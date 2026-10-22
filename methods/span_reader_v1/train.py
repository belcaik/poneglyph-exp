#!/usr/bin/env python3
"""Train SpanReader model for furigana annotation."""

import argparse
import json
import sys
import time
from pathlib import Path

# Ensure sibling modules are importable
sys.path.insert(0, str(Path(__file__).parent))

import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

from model import SpanReaderModel
from prepare_data import (
    SpanReaderDataset, build_reading_vocab, collate_fn, load_data,
    NUM_TYPES, HIRAGANA_VOCAB, TYPE_NAMES,
)


def evaluate(model, dataloader, device, reading_vocab):
    """Evaluate model on a dataset split."""
    model.eval()
    total_loss = 0
    total_batches = 0

    # Span detection metrics
    tp = fp = fn = 0
    # Reading accuracy
    reading_correct = reading_total = 0
    # Type accuracy
    type_correct = type_total = 0

    global_readings = reading_vocab["global_readings"]

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            char_to_token = batch["char_to_token"].to(device)
            char_mask = batch["char_mask"].to(device)
            intra_positions = batch["intra_positions"].to(device)

            gold = {
                "start": batch["gold_start"].to(device),
                "end": batch["gold_end"].to(device),
                "type": batch["gold_type"].to(device),
                "exists": batch["gold_exists"].to(device),
                "reading_idx": batch["gold_reading_idx"].to(device),
            }

            loss, preds = model(
                input_ids, attention_mask, char_to_token, char_mask,
                intra_positions=intra_positions, gold_spans=gold
            )
            total_loss += loss.item()
            total_batches += 1

            # Extract predictions
            batch_size = input_ids.size(0)
            for b in range(batch_size):
                num_chars = char_mask[b].sum().int().item()
                exists_prob = torch.sigmoid(preds["exists_logits"][b])

                # Gold spans
                gold_spans = set()
                num_gold = batch["num_gold"][b]
                for j in range(num_gold):
                    gs = batch["gold_start"][b, j].item()
                    ge = batch["gold_end"][b, j].item()
                    gt = batch["gold_type"][b, j].item()
                    gr = batch["gold_reading_idx"][b, j].item()
                    gold_spans.add((gs, ge, gt, gr))

                # Predicted spans
                pred_spans = set()
                for q in range(model.num_queries):
                    if exists_prob[q] > 0.5:
                        ps = preds["start_logits"][b, q, :num_chars].argmax().item()
                        pe = preds["end_logits"][b, q, :num_chars].argmax().item()
                        pt = preds["type_logits"][b, q].argmax().item()
                        pr = preds["reading_logits"][b, q].argmax().item()
                        if pe < ps:
                            pe = ps
                        pred_spans.add((ps, pe, pt, pr))

                # Span F1 (position match only)
                gold_pos = {(s, e) for s, e, _, _ in gold_spans}
                pred_pos = {(s, e) for s, e, _, _ in pred_spans}
                tp += len(gold_pos & pred_pos)
                fp += len(pred_pos - gold_pos)
                fn += len(gold_pos - pred_pos)

                # Reading + type accuracy on matched spans
                for gs, ge, gt, gr in gold_spans:
                    for ps, pe, pt, pr in pred_spans:
                        if gs == ps and ge == pe:
                            type_total += 1
                            if pt == gt:
                                type_correct += 1
                            if gr >= 0:
                                reading_total += 1
                                if pr == gr:
                                    reading_correct += 1
                            break

    avg_loss = total_loss / max(total_batches, 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-8)
    read_acc = reading_correct / max(reading_total, 1)
    type_acc = type_correct / max(type_total, 1)

    return {
        "loss": avg_loss,
        "span_precision": precision,
        "span_recall": recall,
        "span_f1": f1,
        "reading_accuracy": read_acc,
        "type_accuracy": type_acc,
        "tp": tp, "fp": fp, "fn": fn,
        "reading_correct": reading_correct,
        "reading_total": reading_total,
    }


def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Load data
    print("Loading data...")
    splits = load_data(args.data_dir)
    print(f"  Train: {len(splits['train'])}, Val: {len(splits['val'])}, Test: {len(splits['test'])}")

    # Build reading vocabulary
    print("Building reading vocabulary...")
    reading_vocab = build_reading_vocab(splits["train"])
    print(f"  {reading_vocab['vocab_size']} unique readings, "
          f"{len(reading_vocab['surface_candidates'])} unique surfaces")

    # Tokenizer
    print(f"Loading tokenizer: {args.encoder}...")
    tokenizer = AutoTokenizer.from_pretrained(args.encoder)

    # Datasets
    train_ds = SpanReaderDataset(
        splits["train"], tokenizer, reading_vocab,
        max_len=args.max_len, num_queries=args.num_queries
    )
    val_ds = SpanReaderDataset(
        splits["val"], tokenizer, reading_vocab,
        max_len=args.max_len, num_queries=args.num_queries
    )
    test_ds = SpanReaderDataset(
        splits["test"], tokenizer, reading_vocab,
        max_len=args.max_len, num_queries=args.num_queries
    )

    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True,
        collate_fn=collate_fn, num_workers=0
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size, shuffle=False,
        collate_fn=collate_fn, num_workers=0
    )
    test_loader = DataLoader(
        test_ds, batch_size=args.batch_size, shuffle=False,
        collate_fn=collate_fn, num_workers=0
    )

    # Model
    print("Building model...")
    config = {
        "encoder_name": args.encoder,
        "num_queries": args.num_queries,
        "num_types": NUM_TYPES,
        "d_model": 768,
        "reading_vocab_size": reading_vocab["vocab_size"],
        "hiragana_vocab_size": len(HIRAGANA_VOCAB),
        "lambda_exist": args.lambda_exist,
        "lambda_pos": args.lambda_pos,
        "lambda_type": args.lambda_type,
        "lambda_read_cls": args.lambda_read_cls,
    }
    model = SpanReaderModel(config).to(device)

    # Parameter count
    encoder_params = sum(p.numel() for p in model.encoder.parameters())
    head_params = sum(p.numel() for p in model.parameters()) - encoder_params
    total_params = encoder_params + head_params
    print(f"  Encoder: {encoder_params/1e6:.1f}M params")
    print(f"  Heads: {head_params/1e6:.1f}M params")
    print(f"  Total: {total_params/1e6:.1f}M params")

    # Optimizer with differential LR
    encoder_params_list = list(model.encoder.parameters())
    head_params_list = [p for n, p in model.named_parameters() if not n.startswith("encoder")]
    optimizer = AdamW([
        {"params": encoder_params_list, "lr": args.encoder_lr},
        {"params": head_params_list, "lr": args.head_lr},
    ], weight_decay=0.01)

    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(total_steps * 0.1)
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    # Training loop
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    best_val_f1 = 0
    patience_counter = 0
    training_log = []

    print(f"\nStarting training: {args.epochs} epochs, batch_size={args.batch_size}")
    print(f"  Encoder LR: {args.encoder_lr}, Head LR: {args.head_lr}")
    print(f"  Warmup: {warmup_steps}/{total_steps} steps")

    for epoch in range(1, args.epochs + 1):
        model.train()
        epoch_loss = 0
        epoch_batches = 0
        epoch_start = time.time()

        for batch_idx, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            char_to_token = batch["char_to_token"].to(device)
            char_mask = batch["char_mask"].to(device)
            intra_positions = batch["intra_positions"].to(device)

            gold = {
                "start": batch["gold_start"].to(device),
                "end": batch["gold_end"].to(device),
                "type": batch["gold_type"].to(device),
                "exists": batch["gold_exists"].to(device),
                "reading_idx": batch["gold_reading_idx"].to(device),
            }

            optimizer.zero_grad()
            loss, _ = model(
                input_ids, attention_mask, char_to_token, char_mask,
                intra_positions=intra_positions, gold_spans=gold
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            epoch_loss += loss.item()
            epoch_batches += 1

            if (batch_idx + 1) % 50 == 0:
                avg = epoch_loss / epoch_batches
                print(f"  Epoch {epoch} [{batch_idx+1}/{len(train_loader)}] loss={avg:.4f}")

        epoch_time = time.time() - epoch_start
        train_loss = epoch_loss / max(epoch_batches, 1)

        # Evaluate
        print(f"  Evaluating...")
        val_metrics = evaluate(model, val_loader, device, reading_vocab)

        log_entry = {
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "val_loss": round(val_metrics["loss"], 4),
            "val_span_f1": round(val_metrics["span_f1"], 4),
            "val_span_precision": round(val_metrics["span_precision"], 4),
            "val_span_recall": round(val_metrics["span_recall"], 4),
            "val_reading_accuracy": round(val_metrics["reading_accuracy"], 4),
            "val_type_accuracy": round(val_metrics["type_accuracy"], 4),
            "epoch_time": round(epoch_time, 1),
            "lr_encoder": optimizer.param_groups[0]["lr"],
            "lr_head": optimizer.param_groups[1]["lr"],
        }
        training_log.append(log_entry)

        print(f"  Epoch {epoch}: train_loss={train_loss:.4f}, "
              f"val_loss={val_metrics['loss']:.4f}, "
              f"span_f1={val_metrics['span_f1']:.3f} "
              f"(P={val_metrics['span_precision']:.3f} R={val_metrics['span_recall']:.3f}), "
              f"read_acc={val_metrics['reading_accuracy']:.3f}, "
              f"type_acc={val_metrics['type_accuracy']:.3f}, "
              f"time={epoch_time:.0f}s")

        # Save best
        if val_metrics["span_f1"] > best_val_f1:
            best_val_f1 = val_metrics["span_f1"]
            patience_counter = 0
            torch.save(model.state_dict(), save_dir / "best_model.pt")
            print(f"  New best! span_f1={best_val_f1:.4f}")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"  Early stopping at epoch {epoch} (patience={args.patience})")
                break

        # Save log
        log_path = Path(__file__).parent / "training_log.json"
        with open(log_path, "w") as f:
            json.dump(training_log, f, indent=2)

    # Load best and evaluate on test
    print(f"\nLoading best model (span_f1={best_val_f1:.4f})...")
    model.load_state_dict(torch.load(save_dir / "best_model.pt", weights_only=True))
    test_metrics = evaluate(model, test_loader, device, reading_vocab)

    print(f"\n{'='*60}")
    print(f"TEST RESULTS:")
    print(f"  Span F1: {test_metrics['span_f1']:.3f} "
          f"(P={test_metrics['span_precision']:.3f} R={test_metrics['span_recall']:.3f})")
    print(f"  Reading Accuracy: {test_metrics['reading_accuracy']:.3f}")
    print(f"  Type Accuracy: {test_metrics['type_accuracy']:.3f}")
    print(f"  TP={test_metrics['tp']} FP={test_metrics['fp']} FN={test_metrics['fn']}")

    # Save results
    results = {
        "model": "SpanReader v1",
        "encoder": args.encoder,
        "best_val_span_f1": round(best_val_f1, 4),
        "test": {k: round(v, 4) if isinstance(v, float) else v
                 for k, v in test_metrics.items()},
        "config": config,
        "training_log": training_log,
        "total_params": total_params,
    }
    repo_root = Path(__file__).parent.parent.parent
    results_path = repo_root / "results" / "span_reader_v1_eval.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {results_path}")

    # Save reading vocab
    with open(save_dir / "reading_vocab.json", "w") as f:
        json.dump({
            "global_readings": reading_vocab["global_readings"],
            "surface_candidates": reading_vocab["surface_candidates"],
        }, f, ensure_ascii=False, indent=2)

    # Save config
    with open(save_dir / "model_config.json", "w") as f:
        json.dump(config, f, indent=2)

    # Copy log to results
    with open(repo_root / "results" / "span_reader_v1_training_log.json", "w") as f:
        json.dump(training_log, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/poneglyph_v1")
    parser.add_argument("--save-dir", default="models/span-reader-v1")
    parser.add_argument("--encoder", default="ku-nlp/deberta-v3-base-japanese")
    parser.add_argument("--max-len", type=int, default=256)
    parser.add_argument("--num-queries", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--encoder-lr", type=float, default=1e-5)
    parser.add_argument("--head-lr", type=float, default=5e-5)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--lambda-exist", type=float, default=2.0)
    parser.add_argument("--lambda-pos", type=float, default=5.0)
    parser.add_argument("--lambda-type", type=float, default=1.0)
    parser.add_argument("--lambda-read-cls", type=float, default=3.0)
    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
