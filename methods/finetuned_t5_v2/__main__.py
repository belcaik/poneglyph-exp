"""
CLI for T5 v2 annotator evaluation.

Usage:
    python -m methods.finetuned_t5_v2 --model models/t5-furigana-v2 --input data/splits/test.json
"""

import argparse
import json
from pathlib import Path

from .annotator import T5V2Annotator


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
    parser = argparse.ArgumentParser(description="T5 v2 Furigana Annotator")
    parser.add_argument("--model", type=Path, required=True,
                        help="Path to fine-tuned model")
    parser.add_argument("--input", type=Path, required=True,
                        help="Input JSON file (original format with tokens)")
    parser.add_argument("--output", type=Path, help="Output JSON file")
    parser.add_argument("--limit", type=int, default=0, help="Limit sentences (0=all)")
    parser.add_argument("--compare", action="store_true", help="Show comparison")
    args = parser.parse_args()

    # Load data
    with open(args.input) as f:
        sentences = json.load(f)

    limit = args.limit if args.limit > 0 else len(sentences)
    sentences = sentences[:limit]

    print(f"Loaded {len(sentences)} sentences from {args.input}")

    # Initialize annotator
    annotator = T5V2Annotator(args.model)
    print(f"Annotator: {annotator.name()}")

    total_gt = 0
    total_matches = 0
    predictions = []

    for i, sentence in enumerate(sentences):
        text = sentence["text"]
        gt_tokens = sentence["tokens"]
        pred_tokens = annotator.annotate(text)

        matches, gt_count = calculate_accuracy(gt_tokens, pred_tokens)
        total_gt += gt_count
        total_matches += matches

        if args.compare and i < 10:
            display_text = text[:50] + "..." if len(text) > 50 else text
            print(f"\n{'─' * 60}")
            print(f"Sentence {i+1}: {display_text}")

            # Show model output
            annotated = annotator.generate_annotated(text)
            print(f"T5 v2 output: {annotated[:70]}...")

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
            "ground_truth": gt_tokens,
            "predicted": pred_tokens
        })

    # Summary
    accuracy = total_matches / total_gt * 100 if total_gt > 0 else 0
    print(f"\n{'=' * 60}")
    print("SUMMARY - T5 v2 (Bracket Format)")
    print(f"{'=' * 60}")
    print(f"Sentences: {len(sentences)}")
    print(f"Ground truth tokens: {total_gt}")
    print(f"Exact matches: {total_matches}")
    print(f"Accuracy: {accuracy:.1f}%")

    # Comparison with other methods
    print(f"\nComparison:")
    print(f"  T5 v1 (hiragana):     61.8%")
    print(f"  Sudachi Mode C:       63.5%")
    print(f"  T5 v2 (bracket):      {accuracy:.1f}%")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
