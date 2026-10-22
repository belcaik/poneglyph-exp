#!/usr/bin/env python3
"""Step 4: Evaluate and compare all model annotations against v7 ground truth.

Uses both exact-match and overlap-based evaluation to handle convention differences
between v7 GT (stem-only) and Poneglyph conventions (morpheme-complete).
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def contains_kanji(text):
    return any(0x4E00 <= ord(c) <= 0x9FFF or 0x3400 <= ord(c) <= 0x4DBF for c in text)


def normalize_reading(reading):
    """Normalize reading for comparison."""
    if not reading:
        return ""
    reading = reading.strip()
    result = []
    for c in reading:
        code = ord(c)
        if 0x30A1 <= code <= 0x30F6:
            result.append(chr(code - 0x60))
        else:
            result.append(c)
    return "".join(result)


def load_annotations(filepath):
    with open(filepath) as f:
        return json.load(f)


def find_token_positions(text, tokens):
    """Find character positions for each token in the text.
    Returns list of (start, end, surface, reading) tuples.
    """
    positions = []
    used = set()

    for token in tokens:
        surface = token.get("surface", "")
        reading = normalize_reading(token.get("reading", ""))
        if not surface:
            continue

        # Find the surface in text, avoiding already-used positions
        pos = 0
        while pos < len(text):
            idx = text.find(surface, pos)
            if idx == -1:
                break
            if not any(p in used for p in range(idx, idx + len(surface))):
                for p in range(idx, idx + len(surface)):
                    used.add(p)
                positions.append((idx, idx + len(surface), surface, reading))
                break
            pos = idx + 1

    return positions


def build_char_reading_map(text, positions):
    """Build a map from character position to reading character.

    For a token at positions [3,4,5] with surface "食べて" and reading "たべて",
    maps: {3: 'た', 4: 'べ', 5: 'て'}
    """
    char_map = {}
    for start, end, surface, reading in positions:
        surface_len = end - start
        reading_len = len(reading)

        # For simple 1:1 character mapping (same length)
        if surface_len == reading_len:
            for i in range(surface_len):
                char_map[start + i] = reading[i]
        else:
            # Store the full reading for each character position
            for i in range(surface_len):
                char_map[start + i] = (reading, i, surface_len)

    return char_map


def evaluate_overlap(model_annots, gt_annots, text):
    """Evaluate model vs GT using position-based overlap.

    Returns:
        kanji_positions_gt: set of char positions that GT annotated (kanji only)
        kanji_positions_model: set of char positions that model annotated (kanji only)
        overlap: positions annotated by both
        reading_matches: positions where both annotated and readings agree
    """
    gt_positions = find_token_positions(text, gt_annots)
    model_positions = find_token_positions(text, model_annots)

    # For kanji-containing tokens only, track which characters are annotated
    gt_kanji_chars = set()
    model_kanji_chars = set()

    gt_span_map = {}  # char_pos -> (surface, reading) of the span containing it
    model_span_map = {}

    for start, end, surface, reading in gt_positions:
        if contains_kanji(surface):
            for p in range(start, end):
                gt_kanji_chars.add(p)
                gt_span_map[p] = (surface, reading, start, end)

    for start, end, surface, reading in model_positions:
        if contains_kanji(surface):
            for p in range(start, end):
                model_kanji_chars.add(p)
                model_span_map[p] = (surface, reading, start, end)

    overlap = gt_kanji_chars & model_kanji_chars
    model_extra = model_kanji_chars - gt_kanji_chars
    gt_only = gt_kanji_chars - model_kanji_chars

    # For overlapping positions, check reading agreement at the span level
    reading_correct = 0
    reading_total = 0

    # Group overlapping chars by GT spans
    gt_spans_checked = set()
    for p in overlap:
        gt_surface, gt_reading, gt_start, gt_end = gt_span_map[p]
        span_key = (gt_start, gt_end)
        if span_key in gt_spans_checked:
            continue
        gt_spans_checked.add(span_key)

        # Find all model spans that overlap with this GT span
        model_surfaces = set()
        model_readings = []
        for gp in range(gt_start, gt_end):
            if gp in model_span_map:
                ms, mr, ms_start, ms_end = model_span_map[gp]
                model_surfaces.add((ms_start, ms_end, ms, mr))

        reading_total += 1

        if not model_surfaces:
            continue

        # Check if model reading contains the GT reading (or vice versa)
        combined_model_reading = ""
        for ms_start, ms_end, ms, mr in sorted(model_surfaces):
            combined_model_reading += mr

        # Various matching strategies:
        # 1. Exact match (GT reading == model reading)
        if gt_reading == combined_model_reading:
            reading_correct += 1
        # 2. GT reading is contained in model reading (model has larger span)
        elif gt_reading in combined_model_reading:
            reading_correct += 1
        # 3. Model reading is contained in GT reading (model has smaller span)
        elif combined_model_reading in gt_reading:
            reading_correct += 1
        # 4. Single model span that starts with GT reading
        elif len(model_surfaces) == 1:
            _, _, ms, mr = list(model_surfaces)[0]
            if mr.startswith(gt_reading) or gt_reading.startswith(mr):
                reading_correct += 1

    return {
        "gt_kanji_chars": len(gt_kanji_chars),
        "model_kanji_chars": len(model_kanji_chars),
        "overlap_chars": len(overlap),
        "model_extra_chars": len(model_extra),
        "gt_only_chars": len(gt_only),
        "reading_spans_checked": reading_total,
        "reading_spans_correct": reading_correct,
    }


def evaluate_model_full(model_annotations, gt_annotations):
    """Full evaluation with both exact-match and overlap metrics."""
    results = {
        "total_gold_tokens": 0,
        "total_model_tokens": 0,
        "exact_matches": 0,
        "overlap": defaultdict(int),
        "per_source": defaultdict(lambda: defaultdict(int)),
        "parse_failures": 0,
        "examples_gt_only": [],
        "examples_model_extra": [],
        "examples_reading_diff": [],
    }

    for gt_sent in gt_annotations:
        sent_id = gt_sent["id"]
        source = gt_sent["source"]
        text = gt_sent["text"]

        model_sent = None
        for ms in model_annotations:
            if ms["id"] == sent_id:
                model_sent = ms
                break

        gt_tokens = gt_sent["annotations"]
        results["total_gold_tokens"] += len(gt_tokens)
        results["per_source"][source]["gold"] += len(gt_tokens)

        if model_sent is None or model_sent.get("parse_failure"):
            results["parse_failures"] += 1
            continue

        model_tokens = model_sent.get("annotations", [])
        results["total_model_tokens"] += len(model_tokens)
        results["per_source"][source]["model"] += len(model_tokens)

        # Exact surface+reading match
        gt_set = Counter()
        model_set = Counter()
        for t in gt_tokens:
            key = (t.get("surface", ""), normalize_reading(t.get("reading", "")))
            gt_set[key] += 1
        for t in model_tokens:
            key = (t.get("surface", ""), normalize_reading(t.get("reading", "")))
            model_set[key] += 1

        for key in gt_set:
            matches = min(gt_set[key], model_set.get(key, 0))
            results["exact_matches"] += matches
            results["per_source"][source]["exact"] += matches

        # Overlap-based evaluation
        ov = evaluate_overlap(model_tokens, gt_tokens, text)
        for k, v in ov.items():
            results["overlap"][k] += v
            results["per_source"][source][f"ov_{k}"] += v

        # Collect examples of differences (for first few sentences)
        if len(results["examples_gt_only"]) < 20:
            gt_pos = find_token_positions(text, gt_tokens)
            model_pos = find_token_positions(text, model_tokens)
            gt_surfaces = {s for _, _, s, _ in gt_pos}
            model_surfaces = {s for _, _, s, _ in model_pos}

            for s in gt_surfaces - model_surfaces:
                if contains_kanji(s):
                    reading = next((r for _, _, sf, r in gt_pos if sf == s), "")
                    results["examples_gt_only"].append({
                        "sent_id": sent_id, "source": source,
                        "surface": s, "reading": reading
                    })

            for s in model_surfaces - gt_surfaces:
                if contains_kanji(s):
                    reading = next((r for _, _, sf, r in model_pos if sf == s), "")
                    results["examples_model_extra"].append({
                        "sent_id": sent_id, "source": source,
                        "surface": s, "reading": reading
                    })

    # Compute metrics
    total_gold = results["total_gold_tokens"]
    ov = results["overlap"]
    metrics = {
        "exact_span_match_pct": results["exact_matches"] / total_gold * 100 if total_gold > 0 else 0,
        "char_coverage_recall": ov["overlap_chars"] / ov["gt_kanji_chars"] * 100 if ov["gt_kanji_chars"] > 0 else 0,
        "char_coverage_precision": ov["overlap_chars"] / ov["model_kanji_chars"] * 100 if ov["model_kanji_chars"] > 0 else 0,
        "reading_accuracy": ov["reading_spans_correct"] / ov["reading_spans_checked"] * 100 if ov["reading_spans_checked"] > 0 else 0,
        "parse_failure_rate": results["parse_failures"] / len(gt_annotations) * 100 if gt_annotations else 0,
        "model_extra_chars": ov["model_extra_chars"],
        "gt_only_chars": ov["gt_only_chars"],
    }
    results["metrics"] = metrics

    return results


def evaluate_convention_adherence(model_annotations):
    """Check how well the model follows Poneglyph conventions."""
    scores = {
        "verb_chains": {"total": 0, "correct": 0},
        "compound_nouns": {"total": 0, "correct": 0},
        "proper_nouns": {"total": 0, "correct": 0},
        "counters": {"total": 0, "correct": 0},
        "no_hiragana_annotation": {"total": 0, "correct": 0},
    }

    for sent in model_annotations:
        annotations = sent.get("annotations", [])

        for ann in annotations:
            surface = ann.get("surface", "")
            ann_type = ann.get("type", "")

            # Verb chains
            if ann_type == "verb" or (contains_kanji(surface) and
                any(surface.endswith(p) for p in ["ている", "ていた", "ていました", "てしまった",
                    "させた", "られた", "ました", "ません"])):
                scores["verb_chains"]["total"] += 1
                if len(surface) >= 3 and contains_kanji(surface):
                    scores["verb_chains"]["correct"] += 1

            # Compound nouns
            if ann_type in ("noun", "compound_noun"):
                kanji_count = sum(1 for c in surface if 0x4E00 <= ord(c) <= 0x9FFF)
                if kanji_count >= 3:
                    scores["compound_nouns"]["total"] += 1
                    scores["compound_nouns"]["correct"] += 1

            # Proper nouns
            if ann_type == "proper_noun":
                scores["proper_nouns"]["total"] += 1
                scores["proper_nouns"]["correct"] += 1

            # Pure hiragana check
            if surface and all(0x3040 <= ord(c) <= 0x309F for c in surface):
                scores["no_hiragana_annotation"]["total"] += 1
            elif surface:
                scores["no_hiragana_annotation"]["total"] += 1
                scores["no_hiragana_annotation"]["correct"] += 1

            # Counters
            if ann_type == "counter" or re.match(r'^[０-９\d]+[一-龯]', surface):
                scores["counters"]["total"] += 1
                scores["counters"]["correct"] += 1

    return scores


def main():
    data_dir = Path("data/benchmark")
    gt = load_annotations(data_dir / "annotations_v7_gt.json")

    models = {}
    for name, filename in [("claude_v2", "annotations_claude_v2.json"),
                            ("qwen7b", "annotations_qwen7b.json"),
                            ("gemini", "annotations_gemini.json"),
                            ("claude_v1", "annotations_claude.json")]:
        filepath = data_dir / filename
        if filepath.exists():
            models[name] = load_annotations(filepath)
            print(f"Loaded {name}: {len(models[name])} sentences")
        else:
            print(f"Skipping {name}: {filepath} not found")

    if not models:
        print("No model annotations found.")
        return

    results = {}
    print("\n" + "=" * 70)
    print("BENCHMARK EVALUATION")
    print("=" * 70)

    for name, annots in models.items():
        print(f"\n--- {name.upper()} ---")
        result = evaluate_model_full(annots, gt)
        results[name] = result

        m = result["metrics"]
        print(f"  Exact span match:       {m['exact_span_match_pct']:.1f}%")
        print(f"  Char coverage (recall):  {m['char_coverage_recall']:.1f}%")
        print(f"  Char coverage (precis.): {m['char_coverage_precision']:.1f}%")
        print(f"  Reading accuracy:        {m['reading_accuracy']:.1f}%")
        print(f"  Parse failure rate:      {m['parse_failure_rate']:.1f}%")
        print(f"  Model extra chars:       {m['model_extra_chars']}")
        print(f"  GT-only chars:           {m['gt_only_chars']}")
        print(f"  Gold tokens: {result['total_gold_tokens']}, Model tokens: {result['total_model_tokens']}")

        print(f"\n  Per-source:")
        for source in sorted(result["per_source"].keys()):
            s = result["per_source"][source]
            recall = s.get("ov_overlap_chars", 0) / s.get("ov_gt_kanji_chars", 1) * 100
            read_acc = s.get("ov_reading_spans_correct", 0) / max(s.get("ov_reading_spans_checked", 1), 1) * 100
            exact_pct = s.get("exact", 0) / max(s.get("gold", 1), 1) * 100
            print(f"    {source}: recall={recall:.1f}%, reading_acc={read_acc:.1f}%, exact={exact_pct:.1f}% "
                  f"(gold={s.get('gold',0)}, model={s.get('model',0)})")

        # Convention adherence
        conv = evaluate_convention_adherence(annots)
        print(f"\n  Convention adherence:")
        for rule, counts in conv.items():
            if counts["total"] > 0:
                pct = counts["correct"] / counts["total"] * 100
                print(f"    {rule}: {pct:.0f}% ({counts['correct']}/{counts['total']})")
        results[name]["convention_scores"] = conv

        # Show example differences
        if result["examples_gt_only"]:
            print(f"\n  Examples: GT annotated but model didn't (first 10):")
            for ex in result["examples_gt_only"][:10]:
                print(f"    [{ex['source']}] {ex['surface']} → {ex['reading']}")

        if result["examples_model_extra"]:
            print(f"\n  Examples: Model annotated but GT didn't (first 10):")
            for ex in result["examples_model_extra"][:10]:
                print(f"    [{ex['source']}] {ex['surface']} → {ex['reading']}")

    # Save results
    output = {"models": {}}
    for name in models:
        r = results[name]
        output["models"][name] = {
            "metrics": r["metrics"],
            "total_gold_tokens": r["total_gold_tokens"],
            "total_model_tokens": r["total_model_tokens"],
            "exact_matches": r["exact_matches"],
            "parse_failures": r["parse_failures"],
            "overlap": dict(r["overlap"]),
            "per_source": {k: dict(v) for k, v in r["per_source"].items()},
            "convention_scores": {k: dict(v) for k, v in r["convention_scores"].items()},
        }

    output_path = Path("results/benchmark_eval.json")
    with open(output_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
