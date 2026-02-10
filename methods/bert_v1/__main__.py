"""
CLI for BERT v1 annotator evaluation.

Usage:
    python -m methods.bert_v1 --model models/bert-furigana-v1 --input data/splits_v6_no_matcha/test_comparable.json
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np

from .annotator import BertV1Annotator


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
    parser = argparse.ArgumentParser(description="BERT v1 Furigana Annotator")
    parser.add_argument("--model", type=Path, required=True,
                        help="Path to fine-tuned model")
    parser.add_argument("--input", type=Path, required=True,
                        help="Input JSON file (original format with tokens)")
    parser.add_argument("--output", type=Path, help="Output JSON file")
    parser.add_argument("--limit", type=int, default=0, help="Limit sentences (0=all)")
    parser.add_argument("--compare", action="store_true", help="Show comparison")
    args = parser.parse_args()

    with open(args.input) as f:
        sentences = json.load(f)

    limit = args.limit if args.limit > 0 else len(sentences)
    sentences = sentences[:limit]

    print(f"Loaded {len(sentences)} sentences from {args.input}")

    annotator = BertV1Annotator(args.model)
    print(f"Annotator: {annotator.name()}")

    total_gt = 0
    total_matches = 0
    predictions = []
    inference_times = []
    source_stats = {}

    for i, sentence in enumerate(sentences):
        text = sentence["text"]
        gt_tokens = sentence["tokens"]

        start_time = time.time()
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
    print("SUMMARY - BERT v1 (Character-Level Token Classification)")
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

    print(f"\nComparison (comparable test set):")
    print(f"  T5 v6 (seq2seq):      86.4%")
    print(f"  BERT v1 (token cls):  {accuracy:.1f}%")

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
            "predictions": predictions,
        }
        with open(args.output, "w") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
