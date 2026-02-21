"""
CLI for BERT v2 annotator evaluation.

Usage:
    python -m methods.bert_v2 --model models/bert-furigana-v2 --input data/splits_v6_no_matcha/test_comparable.json
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np

from .annotator import BertV2Annotator


def calculate_accuracy(ground_truth: list[dict], predicted: list[dict]) -> tuple[int, int]:
    """Calculate exact match accuracy."""
    matches = 0
    for gt in ground_truth:
        for pred in predicted:
            if gt["surface"] == pred["surface"] and gt["reading"] == pred["reading"]:
                matches += 1
                break
    return matches, len(ground_truth)


def main():
    parser = argparse.ArgumentParser(description="BERT v2 Furigana Annotator")
    parser.add_argument("--model", type=Path, required=True,
                        help="Path to fine-tuned model")
    parser.add_argument("--input", type=Path, required=True,
                        help="Input JSON file (original format with tokens)")
    parser.add_argument("--output", type=Path, help="Output JSON file")
    parser.add_argument("--limit", type=int, default=0, help="Limit sentences (0=all)")
    parser.add_argument("--compare", action="store_true", help="Show comparison")
    parser.add_argument("--use-gt-spans", action="store_true", default=True,
                        help="Use ground truth spans for evaluation (default: True)")
    args = parser.parse_args()

    with open(args.input) as f:
        sentences = json.load(f)

    limit = args.limit if args.limit > 0 else len(sentences)
    sentences = sentences[:limit]

    print(f"Loaded {len(sentences)} sentences from {args.input}")

    annotator = BertV2Annotator(args.model)
    print(f"Annotator: {annotator.name()}")
    print(f"Using ground truth spans: {args.use_gt_spans}")

    total_gt = 0
    total_matches = 0
    predictions = []
    inference_times = []
    source_stats = {}

    # Error analysis
    error_categories = {
        "wrong_reading": [],        # Reading in dict but model picked wrong one
        "oov_surface": [],          # Surface not in dictionary
        "gold_not_in_dict": [],     # Gold reading not among dictionary candidates
    }

    for i, sentence in enumerate(sentences):
        text = sentence["text"]
        gt_tokens = sentence["tokens"]

        start_time = time.time()
        if args.use_gt_spans:
            pred_tokens = annotator.annotate_with_spans(text, gt_tokens)
        else:
            pred_tokens = annotator.annotate(text)
        inference_time = (time.time() - start_time) * 1000
        inference_times.append(inference_time)

        matches, gt_count = calculate_accuracy(gt_tokens, pred_tokens)
        total_gt += gt_count
        total_matches += matches

        source = sentence.get("source", "unknown")
        if source not in source_stats:
            source_stats[source] = {"matches": 0, "total": 0, "sentences": 0}
        source_stats[source]["matches"] += matches
        source_stats[source]["total"] += gt_count
        source_stats[source]["sentences"] += 1

        # Error analysis: find which ground truth tokens were missed
        for gt in gt_tokens:
            found = any(
                p["surface"] == gt["surface"] and p["reading"] == gt["reading"]
                for p in pred_tokens
            )
            if not found:
                # Find what was predicted for this surface
                pred_reading = None
                for p in pred_tokens:
                    if p["surface"] == gt["surface"]:
                        pred_reading = p["reading"]
                        break

                surface = gt["surface"]
                if surface not in annotator.reading_dict:
                    error_categories["oov_surface"].append({
                        "surface": surface,
                        "gold_reading": gt["reading"],
                        "text": text[:80],
                    })
                elif gt["reading"] not in annotator.reading_dict.get(surface, []):
                    error_categories["gold_not_in_dict"].append({
                        "surface": surface,
                        "gold_reading": gt["reading"],
                        "candidates": annotator.reading_dict.get(surface, []),
                        "predicted": pred_reading,
                        "text": text[:80],
                    })
                else:
                    error_categories["wrong_reading"].append({
                        "surface": surface,
                        "gold_reading": gt["reading"],
                        "predicted": pred_reading,
                        "candidates": annotator.reading_dict.get(surface, []),
                        "text": text[:80],
                    })

        if args.compare and i < 10:
            display_text = text[:50] + "..." if len(text) > 50 else text
            print(f"\n{'─' * 60}")
            print(f"Sentence {i+1}: {display_text}")

            print(f"\nGround Truth ({len(gt_tokens)}):")
            for t in gt_tokens:
                print(f"  {t['surface']} → {t['reading']}")
            print(f"\nPredicted ({len(pred_tokens)}) [{matches}/{gt_count}]:")
            for t in pred_tokens:
                status = "✓" if any(
                    g["surface"] == t["surface"] and g["reading"] == t["reading"]
                    for g in gt_tokens
                ) else "✗"
                print(f"  {t['surface']} → {t['reading']} {status}")

        predictions.append({
            "text": text,
            "source": source,
            "ground_truth": gt_tokens,
            "predicted": pred_tokens,
            "matches": matches,
            "total": gt_count,
            "inference_time_ms": inference_time,
        })

    inference_times = np.array(inference_times)

    accuracy = total_matches / total_gt * 100 if total_gt > 0 else 0
    print(f"\n{'=' * 60}")
    print("SUMMARY - BERT v2 (Dictionary-Constrained Reading Classification)")
    print(f"{'=' * 60}")
    print(f"Sentences: {len(sentences)}")
    print(f"Ground truth tokens: {total_gt}")
    print(f"Exact matches: {total_matches}")
    print(f"Accuracy: {accuracy:.1f}%")

    print(f"\nInference timing (ms/sentence):")
    print(f"  Mean: {inference_times.mean():.1f}")
    print(f"  p50:  {np.percentile(inference_times, 50):.1f}")
    print(f"  p95:  {np.percentile(inference_times, 95):.1f}")

    print(f"\nPer-source accuracy:")
    for source, stats in sorted(source_stats.items()):
        src_acc = stats["matches"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {source}: {src_acc:.1f}% ({stats['matches']}/{stats['total']} tokens, {stats['sentences']} sentences)")

    # Error analysis summary
    total_errors = total_gt - total_matches
    print(f"\nError Analysis ({total_errors} errors):")
    print(f"  Wrong reading (model chose incorrectly): {len(error_categories['wrong_reading'])}")
    print(f"  OOV surface (not in dictionary):         {len(error_categories['oov_surface'])}")
    print(f"  Gold not in candidates:                  {len(error_categories['gold_not_in_dict'])}")

    # Top 20 most common wrong reading errors
    from collections import Counter
    wrong_surface_counts = Counter(
        e["surface"] for e in error_categories["wrong_reading"]
    )
    if wrong_surface_counts:
        print(f"\n  Top 20 most common wrong reading errors:")
        for surface, count in wrong_surface_counts.most_common(20):
            # Find an example
            example = next(
                e for e in error_categories["wrong_reading"] if e["surface"] == surface
            )
            print(f"    {surface}: {count}x (gold={example['gold_reading']}, "
                  f"pred={example['predicted']}, candidates={example['candidates']})")

    print(f"\nComparison (comparable test set):")
    print(f"  ByT5 v2 (byte seq2seq):     89.1%")
    print(f"  T5 v7 (seq2seq):            86.6%")
    print(f"  T5 v6 (seq2seq):            86.4%")
    print(f"  BERT v2 (dict constrained): {accuracy:.1f}%")
    print(f"  BERT v1 (token cls):        66.3%")

    if args.output:
        output_data = {
            "summary": {
                "sentences": len(sentences),
                "total_tokens": total_gt,
                "matches": total_matches,
                "accuracy": round(accuracy, 1),
                "inference_ms_mean": round(float(inference_times.mean()), 1),
                "inference_ms_p50": round(float(np.percentile(inference_times, 50)), 1),
                "inference_ms_p95": round(float(np.percentile(inference_times, 95)), 1),
            },
            "per_source": {
                source: {
                    "accuracy": round(stats["matches"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
                    "matches": stats["matches"],
                    "total": stats["total"],
                    "sentences": stats["sentences"],
                }
                for source, stats in source_stats.items()
            },
            "error_analysis": {
                "wrong_reading": len(error_categories["wrong_reading"]),
                "oov_surface": len(error_categories["oov_surface"]),
                "gold_not_in_dict": len(error_categories["gold_not_in_dict"]),
                "top_wrong_readings": [
                    {
                        "surface": surface,
                        "count": count,
                        "gold": next(e["gold_reading"] for e in error_categories["wrong_reading"] if e["surface"] == surface),
                        "predicted": next(e["predicted"] for e in error_categories["wrong_reading"] if e["surface"] == surface),
                    }
                    for surface, count in wrong_surface_counts.most_common(20)
                ] if wrong_surface_counts else [],
            },
            "predictions": predictions,
        }
        with open(args.output, "w") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
