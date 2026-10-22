#!/usr/bin/env python3
"""SpanReader v1 diagnostics: character pooling, position heads, matching, loss breakdown.

Runs all 5 diagnostics and writes results/span_reader_v1_diagnostics.md.
"""

import json
import sys
from pathlib import Path

import torch
import torch.nn.functional as F
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "methods" / "span_reader_v1"))
from model import SpanReaderModel
from prepare_data import (
    SpanReaderDataset, build_reading_vocab, collate_fn, load_data,
    NUM_TYPES, HIRAGANA_VOCAB, TYPE_NAMES,
)
from transformers import AutoTokenizer

REPO = Path(__file__).parent.parent.parent
DATA_DIR = REPO / "data" / "poneglyph_v1"
MODEL_DIR = REPO / "models" / "span-reader-v1"
OUTPUT = REPO / "results" / "span_reader_v1_diagnostics.md"


def load_model_and_data():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    with open(MODEL_DIR / "model_config.json") as f:
        config = json.load(f)

    splits = load_data(str(DATA_DIR))
    reading_vocab = build_reading_vocab(splits["train"])
    config["reading_vocab_size"] = reading_vocab["vocab_size"]

    tokenizer = AutoTokenizer.from_pretrained(config["encoder_name"])
    model = SpanReaderModel(config).to(device)
    model.load_state_dict(torch.load(MODEL_DIR / "best_model.pt", map_location=device, weights_only=True))
    model.eval()

    val_ds = SpanReaderDataset(
        splits["val"], tokenizer, reading_vocab, max_len=128, num_queries=30
    )

    return model, tokenizer, val_ds, splits, reading_vocab, device


def diagnostic_1_char_pooling(tokenizer, val_ds, splits, lines):
    """Verify character-to-token alignment."""
    lines.append("## Diagnostic 1: Character-to-Token Alignment\n\n")

    issues = 0
    total_chars = 0

    for i in range(min(10, len(splits["val"]))):
        entry = splits["val"][i]
        text = entry["text"]
        tokens = entry.get("tokens", [])

        encoding = tokenizer(
            text, max_length=128, truncation=True, return_offsets_mapping=True
        )
        offsets = encoding["offset_mapping"]
        token_strs = tokenizer.convert_ids_to_tokens(encoding["input_ids"])

        lines.append(f"### Sentence {i}: `{text}`\n\n")

        # Show tokenization
        lines.append("**Tokenization:**\n```\n")
        for t_idx, (tok, (s, e)) in enumerate(zip(token_strs, offsets)):
            if s == e:
                lines.append(f"  Token {t_idx}: {tok} -> chars: none (special)\n")
            else:
                chars = text[s:e]
                lines.append(f"  Token {t_idx}: \"{tok}\" -> chars {s}-{e-1} \"{chars}\"\n")
        lines.append("```\n\n")

        # Build char_to_token map (same logic as dataset)
        num_chars = len(text)
        c2t = [0] * num_chars
        for t_idx, (s, e) in enumerate(offsets):
            if s == e:
                continue
            for pos in range(s, min(e, num_chars)):
                c2t[pos] = t_idx

        lines.append(f"**Char-to-token map:** `{c2t[:num_chars]}`\n\n")

        # Check each gold span
        for tok in tokens[:5]:
            start = tok.get("start", 0)
            end = tok.get("end", start + len(tok.get("surface", "")))
            surface = tok.get("surface", "")

            if start >= num_chars or end > num_chars:
                lines.append(f"- Span `{surface}` ({start}-{end}): **OUT OF BOUNDS** (text len={num_chars})\n")
                issues += 1
                continue

            actual_text = text[start:end]
            token_indices = set(c2t[start:end])

            # Check if the actual text at the position matches the surface
            match = actual_text == surface
            # Check if any char maps to special tokens
            special_mapped = any(c2t[p] == 0 for p in range(start, min(end, num_chars))
                                if offsets[0][0] == offsets[0][1])

            status = "OK" if match else "MISMATCH"
            if not match:
                issues += 1

            lines.append(f"- Span `{surface}` (chars {start}-{end-1}): "
                         f"actual=`{actual_text}` tokens={sorted(token_indices)} "
                         f"**{status}**\n")

            total_chars += end - start

        lines.append("\n")

    verdict = "PASS" if issues == 0 else f"ISSUES FOUND ({issues})"
    lines.append(f"**Verdict:** {verdict} — {issues} issues in {total_chars} total span characters\n\n")
    return issues


def diagnostic_2_position_heads(model, val_ds, device, lines):
    """Analyze what position heads actually predict."""
    lines.append("## Diagnostic 2: Position Head Predictions\n\n")

    diffuse_count = 0
    off_by_one = 0
    correct_spans = 0
    total_gold = 0
    start_gt_end = 0

    for i in range(min(10, len(val_ds))):
        batch = collate_fn([val_ds[i]])
        text = batch["texts"][0]
        num_gold = batch["num_gold"][0]

        input_ids = batch["input_ids"].to(device)
        attn = batch["attention_mask"].to(device)
        c2t = batch["char_to_token"].to(device)
        cm = batch["char_mask"].to(device)

        with torch.no_grad():
            preds = model(input_ids, attn, c2t, cm)

        num_chars = cm[0].sum().int().item()
        exists_prob = torch.sigmoid(preds["exists_logits"][0])
        start_probs = F.softmax(preds["start_logits"][0, :, :num_chars], dim=-1)
        end_probs = F.softmax(preds["end_logits"][0, :, :num_chars], dim=-1)

        lines.append(f"### Sentence {i}: `{text}`\n\n")

        # Gold spans
        gold_spans = []
        for j in range(num_gold):
            gs = batch["gold_start"][0, j].item()
            ge = batch["gold_end"][0, j].item()
            gold_spans.append((gs, ge))
        lines.append(f"**Gold spans:** {gold_spans}\n\n")

        # Top queries by existence prob
        active_queries = [(q, exists_prob[q].item()) for q in range(30)]
        active_queries.sort(key=lambda x: -x[1])

        for q, ep in active_queries[:6]:
            pred_start = start_probs[q].argmax().item()
            pred_end = end_probs[q].argmax().item()
            start_entropy = -(start_probs[q] * (start_probs[q] + 1e-10).log()).sum().item()
            end_entropy = -(end_probs[q] * (end_probs[q] + 1e-10).log()).sum().item()
            max_start_prob = start_probs[q].max().item()
            max_end_prob = end_probs[q].max().item()

            # Top 3 start/end positions
            top_starts = start_probs[q].topk(3)
            top_ends = end_probs[q].topk(3)
            s_str = ", ".join(f"{top_starts.values[k]:.2f}@{top_starts.indices[k]}" for k in range(3))
            e_str = ", ".join(f"{top_ends.values[k]:.2f}@{top_ends.indices[k]}" for k in range(3))

            is_diffuse = max_start_prob < 0.15 or max_end_prob < 0.15
            is_swapped = pred_start > pred_end

            if is_diffuse:
                diffuse_count += 1
            if is_swapped:
                start_gt_end += 1

            pred_text = text[pred_start:pred_end+1] if pred_end < len(text) else "?"

            lines.append(f"- **Q{q}** (exists={ep:.2f}): "
                         f"start=[{s_str}] end=[{e_str}] "
                         f"→ ({pred_start},{pred_end}) `{pred_text}` "
                         f"{'DIFFUSE' if is_diffuse else ''}"
                         f"{'SWAPPED' if is_swapped else ''}\n")

        # Check matches against gold
        for gs, ge in gold_spans:
            total_gold += 1
            matched = False
            for q in range(30):
                if exists_prob[q] > 0.5:
                    ps = start_probs[q].argmax().item()
                    pe = end_probs[q].argmax().item()
                    if ps == gs and pe == ge:
                        correct_spans += 1
                        matched = True
                        break
                    elif abs(ps - gs) <= 1 and abs(pe - ge) <= 1:
                        off_by_one += 1
                        matched = True
                        break

        lines.append("\n")

    lines.append(f"**Summary over {min(10, len(val_ds))} sentences:**\n")
    lines.append(f"- Correct spans: {correct_spans}/{total_gold}\n")
    lines.append(f"- Off-by-one: {off_by_one}/{total_gold}\n")
    lines.append(f"- Diffuse predictions (max_prob < 0.15): {diffuse_count}\n")
    lines.append(f"- Start > End: {start_gt_end}\n\n")

    if diffuse_count > total_gold:
        lines.append("**Diagnosis:** Position heads produce DIFFUSE distributions — "
                      "model hasn't learned to point sharply.\n\n")
    elif off_by_one > correct_spans:
        lines.append("**Diagnosis:** Systematic off-by-one errors — "
                      "char-to-token alignment issue.\n\n")
    elif start_gt_end > total_gold * 0.2:
        lines.append("**Diagnosis:** Start > End frequently — "
                      "basic position logic broken.\n\n")
    else:
        lines.append("**Diagnosis:** Position heads working but imprecise.\n\n")


def diagnostic_3_matching_stability(model, val_ds, device, lines):
    """Analyze Hungarian matching assignments."""
    lines.append("## Diagnostic 3: Hungarian Matching Stability\n\n")

    for i in range(min(5, len(val_ds))):
        batch = collate_fn([val_ds[i]])
        text = batch["texts"][0]
        num_gold = batch["num_gold"][0]

        if num_gold == 0:
            continue

        input_ids = batch["input_ids"].to(device)
        attn = batch["attention_mask"].to(device)
        c2t = batch["char_to_token"].to(device)
        cm = batch["char_mask"].to(device)
        gold = {k: batch[f"gold_{k}"].to(device) for k in ["start", "end", "type", "exists", "reading_idx"]}

        with torch.no_grad():
            _, preds = model(input_ids, attn, c2t, cm, gold_spans=gold)

        # Rebuild cost matrix (same as model._build_cost_matrix)
        b = 0
        K = 30
        start_probs = preds["start_logits"][b].softmax(-1)
        end_probs = preds["end_logits"][b].softmax(-1)
        exist_prob = torch.sigmoid(preds["exists_logits"][b])
        type_probs = preds["type_logits"][b].softmax(-1)

        cost = torch.zeros(K, num_gold, device=device)
        for j in range(num_gold):
            gs = gold["start"][b, j].item()
            ge = gold["end"][b, j].item()
            gt = gold["type"][b, j].item()
            cost[:, j] += 5.0 * (-start_probs[:, gs].log().clamp(min=-10))
            cost[:, j] += 5.0 * (-end_probs[:, ge].log().clamp(min=-10))
            cost[:, j] += 2.0 * (-exist_prob.log().clamp(min=-10))
            cost[:, j] += 1.0 * (-type_probs[:, gt].log().clamp(min=-10))

        pred_idx, gold_idx = linear_sum_assignment(cost.cpu().numpy())

        lines.append(f"### Sentence {i}: `{text[:60]}...`\n\n")
        lines.append(f"Gold spans: {num_gold}\n\n")
        lines.append("| Gold # | Gold Pos | Matched Query | Cost | Query Exists Prob |\n")
        lines.append("|--------|----------|--------------|------|------------------|\n")

        for pi, gi in zip(pred_idx, gold_idx):
            gs = gold["start"][b, gi].item()
            ge = gold["end"][b, gi].item()
            c = cost[pi, gi].item()
            ep = exist_prob[pi].item()
            lines.append(f"| {gi} | ({gs},{ge}) | Q{pi} | {c:.2f} | {ep:.3f} |\n")

        # Unmatched queries with high existence prob
        matched_set = set(pred_idx.tolist())
        high_unmatched = [(q, exist_prob[q].item()) for q in range(K)
                          if q not in matched_set and exist_prob[q] > 0.3]
        if high_unmatched:
            lines.append(f"\nUnmatched queries with exists>0.3: "
                         f"{[(q, f'{p:.2f}') for q, p in high_unmatched]}\n")
        lines.append("\n")


def diagnostic_4_loss_breakdown(model, val_ds, device, lines):
    """Break down loss by component."""
    lines.append("## Diagnostic 4: Loss Component Breakdown\n\n")

    loss_accum = {"exist": 0, "start": 0, "end": 0, "type": 0, "reading": 0, "total": 0}
    n_batches = 0

    from torch.utils.data import DataLoader

    val_loader = DataLoader(val_ds, batch_size=4, shuffle=False, collate_fn=collate_fn)

    model.eval()
    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch["input_ids"].to(device)
            attn = batch["attention_mask"].to(device)
            c2t = batch["char_to_token"].to(device)
            cm = batch["char_mask"].to(device)
            gold = {k: batch[f"gold_{k}"].to(device)
                    for k in ["start", "end", "type", "exists", "reading_idx"]}

            # Get predictions
            char_hidden, _ = model.encode_and_pool(input_ids, attn, c2t, cm)
            query_output = model.decode_queries(char_hidden)

            start_logits = model.start_head(query_output, char_hidden)
            end_logits = model.end_head(query_output, char_hidden)
            exists_logits = model.exists_head(query_output).squeeze(-1)
            type_logits = model.type_head(query_output)
            reading_logits = model.reading_classifier(query_output)

            bs = input_ids.size(0)
            for b in range(bs):
                num_gold = batch["num_gold"][b]
                if num_gold == 0:
                    continue

                # Hungarian matching
                sp = start_logits[b].softmax(-1)
                ep_l = end_logits[b].softmax(-1)
                ex_p = torch.sigmoid(exists_logits[b])
                tp = type_logits[b].softmax(-1)

                cost = torch.zeros(30, num_gold, device=device)
                for j in range(num_gold):
                    gs = gold["start"][b, j].item()
                    ge = gold["end"][b, j].item()
                    gt = gold["type"][b, j].item()
                    cost[:, j] += 5.0 * (-sp[:, gs].log().clamp(min=-10))
                    cost[:, j] += 5.0 * (-ep_l[:, ge].log().clamp(min=-10))
                    cost[:, j] += 2.0 * (-ex_p.log().clamp(min=-10))
                    cost[:, j] += 1.0 * (-tp[:, gt].log().clamp(min=-10))

                pi, gi = linear_sum_assignment(cost.cpu().numpy())
                pi = torch.tensor(pi, device=device, dtype=torch.long)
                gi = torch.tensor(gi, device=device, dtype=torch.long)

                # Individual losses
                target_ex = torch.zeros(30, device=device)
                target_ex[pi] = 1.0
                l_exist = F.binary_cross_entropy_with_logits(exists_logits[b], target_ex).item()

                nc = cm[b].sum().int().item()
                l_start = F.cross_entropy(start_logits[b, pi, :nc], gold["start"][b, gi]).item()
                l_end = F.cross_entropy(end_logits[b, pi, :nc], gold["end"][b, gi]).item()
                l_type = F.cross_entropy(type_logits[b, pi], gold["type"][b, gi]).item()

                rmask = gold["reading_idx"][b, gi] >= 0
                if rmask.any():
                    l_read = F.cross_entropy(
                        reading_logits[b, pi[rmask]],
                        gold["reading_idx"][b, gi[rmask]]
                    ).item()
                else:
                    l_read = 0

                loss_accum["exist"] += l_exist
                loss_accum["start"] += l_start
                loss_accum["end"] += l_end
                loss_accum["type"] += l_type
                loss_accum["reading"] += l_read
                loss_accum["total"] += (2*l_exist + 5*(l_start+l_end) + l_type + 3*l_read)
                n_batches += 1

    lines.append("| Component | Raw Loss | Weighted | % of Total |\n")
    lines.append("|-----------|----------|----------|:-----------:|\n")
    for name, weight in [("exist", 2), ("start", 5), ("end", 5), ("type", 1), ("reading", 3)]:
        raw = loss_accum[name] / max(n_batches, 1)
        weighted = raw * weight
        total = loss_accum["total"] / max(n_batches, 1)
        pct = weighted / total * 100 if total > 0 else 0
        lines.append(f"| {name} | {raw:.3f} | {weighted:.3f} | {pct:.1f}% |\n")
    lines.append(f"| **total** | | **{loss_accum['total']/max(n_batches,1):.3f}** | 100% |\n\n")

    # Determine bottleneck
    start_pct = (loss_accum["start"] * 5) / loss_accum["total"] * 100 if loss_accum["total"] > 0 else 0
    end_pct = (loss_accum["end"] * 5) / loss_accum["total"] * 100 if loss_accum["total"] > 0 else 0
    pos_pct = start_pct + end_pct

    if pos_pct > 60:
        lines.append(f"**Bottleneck:** Position loss dominates at {pos_pct:.0f}% — "
                      f"the model's main struggle is pointing to correct positions.\n\n")
    else:
        lines.append(f"**Position loss: {pos_pct:.0f}% of total.**\n\n")


def diagnostic_5_visualization(model, val_ds, splits, device, lines):
    """Side-by-side BIO visualization of gold vs predicted spans."""
    lines.append("## Diagnostic 5: Prediction Visualization\n\n")

    for i in range(min(10, len(val_ds))):
        entry = splits["val"][i]
        text = entry["text"]
        tokens = entry.get("tokens", [])

        batch = collate_fn([val_ds[i]])
        input_ids = batch["input_ids"].to(device)
        attn = batch["attention_mask"].to(device)
        c2t = batch["char_to_token"].to(device)
        cm = batch["char_mask"].to(device)

        with torch.no_grad():
            preds = model(input_ids, attn, c2t, cm)

        num_chars = min(len(text), cm[0].sum().int().item())

        # Gold BIO
        gold_bio = ["O"] * num_chars
        for tok in tokens:
            s = tok.get("start", 0)
            e = tok.get("end", s + len(tok.get("surface", "")))
            if s < num_chars:
                gold_bio[s] = "B"
            for p in range(s + 1, min(e, num_chars)):
                gold_bio[p] = "I"

        # Pred BIO
        pred_bio = ["O"] * num_chars
        exists_prob = torch.sigmoid(preds["exists_logits"][0])
        start_logits = preds["start_logits"][0, :, :num_chars]
        end_logits = preds["end_logits"][0, :, :num_chars]

        pred_spans = []
        for q in range(30):
            if exists_prob[q] > 0.5:
                ps = start_logits[q].argmax().item()
                pe = end_logits[q].argmax().item()
                if pe < ps:
                    pe = ps
                pred_spans.append((ps, min(pe + 1, num_chars), exists_prob[q].item()))

        pred_spans.sort(key=lambda x: (x[0], -x[2]))
        used = set()
        for ps, pe, _ in pred_spans:
            positions = set(range(ps, pe))
            if not positions & used:
                pred_bio[ps] = "B"
                for p in range(ps + 1, pe):
                    pred_bio[p] = "I"
                used |= positions

        # Format
        lines.append(f"### Sentence {i}: `{text[:60]}`\n\n")
        lines.append("```\n")

        # Character row
        char_str = " ".join(f"{c:2s}" for c in text[:num_chars])
        lines.append(f"Text: {char_str}\n")
        gold_str = " ".join(f"{b:2s}" for b in gold_bio[:num_chars])
        lines.append(f"Gold: {gold_str}\n")
        pred_str = " ".join(f"{b:2s}" for b in pred_bio[:num_chars])
        lines.append(f"Pred: {pred_str}\n")
        lines.append("```\n\n")

        # Summary
        gold_span_set = set()
        for tok in tokens:
            s = tok.get("start", 0)
            e = tok.get("end", s)
            gold_span_set.add((s, e))

        pred_span_set = set()
        for ps, pe, _ in pred_spans:
            if ps < num_chars:
                pred_span_set.add((ps, pe))

        correct = gold_span_set & pred_span_set
        missed = gold_span_set - pred_span_set
        extra = pred_span_set - gold_span_set

        if correct:
            lines.append(f"Correct: {len(correct)} ")
        if missed:
            missed_surfs = []
            for s, e in missed:
                missed_surfs.append(text[s:e] if e <= len(text) else "?")
            lines.append(f"Missed: {missed_surfs} ")
        if extra:
            extra_surfs = []
            for s, e in extra:
                extra_surfs.append(text[s:e] if e <= len(text) else "?")
            lines.append(f"Extra: {extra_surfs}")
        lines.append("\n\n")


def main():
    print("Loading model and data...")
    model, tokenizer, val_ds, splits, reading_vocab, device = load_model_and_data()
    print(f"  Val set: {len(val_ds)} sentences")
    print(f"  Device: {device}")

    lines = ["# SpanReader v1 Diagnostics\n\n"]

    print("Running Diagnostic 1: Character pooling...")
    issues = diagnostic_1_char_pooling(tokenizer, val_ds, splits, lines)

    print("Running Diagnostic 2: Position heads...")
    diagnostic_2_position_heads(model, val_ds, device, lines)

    print("Running Diagnostic 3: Hungarian matching...")
    diagnostic_3_matching_stability(model, val_ds, device, lines)

    print("Running Diagnostic 4: Loss breakdown...")
    diagnostic_4_loss_breakdown(model, val_ds, device, lines)

    print("Running Diagnostic 5: Visualization...")
    diagnostic_5_visualization(model, val_ds, splits, device, lines)

    # Conclusion
    lines.append("## Conclusion: Root Cause & Recommended Fix\n\n")
    lines.append("Based on the diagnostics above, the findings will be summarized here "
                 "after reviewing all evidence.\n")

    with open(OUTPUT, "w") as f:
        f.write("".join(lines))
    print(f"\nDiagnostics saved to {OUTPUT}")


if __name__ == "__main__":
    main()
