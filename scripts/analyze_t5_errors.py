#!/usr/bin/env python3
"""
T5 v1 Error Analysis Script.

Analyzes errors from fine-tuned T5 model to understand failure modes.
Categorizes errors as:
- Segmentation mismatch: T5 extracted wrong surface/boundaries
- Wrong reading: Correct surface, wrong hiragana reading
- Hallucination: T5 invented tokens not in ground truth
- Missing: Ground truth token not found in prediction
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from methods.finetuned_t5.annotator import T5Annotator


def analyze_errors(test_path: Path, model_path: Path, output_path: Path):
    """Run T5 on test set and categorize all errors."""

    # Load test data
    with open(test_path) as f:
        sentences = json.load(f)

    print(f"Loaded {len(sentences)} test sentences")

    # Initialize annotator
    annotator = T5Annotator(model_path)

    # Error categories
    errors = {
        "segmentation_mismatch": [],  # Wrong surface extracted
        "wrong_reading": [],          # Right surface, wrong reading
        "hallucination": [],          # Invented token not in GT
        "missing": [],                # GT token not found at all
        "extraction_failure": [],     # Anchor alignment failed
    }

    # Statistics
    stats = {
        "total_sentences": len(sentences),
        "total_gt_tokens": 0,
        "total_pred_tokens": 0,
        "exact_matches": 0,
    }

    # Detailed predictions for analysis
    all_predictions = []

    for i, sentence in enumerate(sentences):
        text = sentence["text"]
        gt_tokens = sentence["tokens"]

        # Get T5 raw output
        raw_output = annotator.convert_to_readings(text)

        # Get extracted tokens
        pred_tokens = annotator.annotate(text)

        stats["total_gt_tokens"] += len(gt_tokens)
        stats["total_pred_tokens"] += len(pred_tokens)

        # Track matches for this sentence
        gt_matched = set()
        pred_matched = set()

        sentence_errors = []

        # Check each ground truth token
        for gt_idx, gt in enumerate(gt_tokens):
            gt_surface = gt["surface"]
            gt_reading = gt["reading"]

            matched = False
            partial_match = None

            for pred_idx, pred in enumerate(pred_tokens):
                pred_surface = pred["surface"]
                pred_reading = pred["reading"]

                # Exact match
                if gt_surface == pred_surface and gt_reading == pred_reading:
                    matched = True
                    gt_matched.add(gt_idx)
                    pred_matched.add(pred_idx)
                    stats["exact_matches"] += 1
                    break

                # Surface match but wrong reading
                if gt_surface == pred_surface and gt_reading != pred_reading:
                    partial_match = ("wrong_reading", pred)

                # Partial surface overlap (segmentation issue)
                if (gt_surface in pred_surface or pred_surface in gt_surface) and \
                   gt_surface != pred_surface:
                    if partial_match is None:
                        partial_match = ("segmentation_mismatch", pred)

            if not matched:
                if partial_match:
                    error_type, pred = partial_match
                    error_entry = {
                        "sentence_idx": i,
                        "text": text,
                        "raw_output": raw_output,
                        "gt_surface": gt_surface,
                        "gt_reading": gt_reading,
                        "pred_surface": pred["surface"],
                        "pred_reading": pred["reading"],
                    }
                    errors[error_type].append(error_entry)
                    sentence_errors.append((error_type, gt_surface, gt_reading))
                else:
                    # Token not found at all
                    # Check if reading is in raw output (extraction failure vs generation failure)
                    if gt_reading in raw_output:
                        error_type = "extraction_failure"
                    else:
                        error_type = "missing"

                    error_entry = {
                        "sentence_idx": i,
                        "text": text,
                        "raw_output": raw_output,
                        "gt_surface": gt_surface,
                        "gt_reading": gt_reading,
                        "reading_in_output": gt_reading in raw_output,
                    }
                    errors[error_type].append(error_entry)
                    sentence_errors.append((error_type, gt_surface, gt_reading))

        # Check for hallucinations
        for pred_idx, pred in enumerate(pred_tokens):
            if pred_idx not in pred_matched:
                # Check if this is a subset/superset of any GT
                is_partial = False
                for gt in gt_tokens:
                    if pred["surface"] in gt["surface"] or gt["surface"] in pred["surface"]:
                        is_partial = True
                        break

                if not is_partial and pred["surface"] not in text:
                    # True hallucination - surface not in original text
                    errors["hallucination"].append({
                        "sentence_idx": i,
                        "text": text,
                        "raw_output": raw_output,
                        "pred_surface": pred["surface"],
                        "pred_reading": pred["reading"],
                    })

        all_predictions.append({
            "idx": i,
            "text": text,
            "raw_output": raw_output,
            "gt_tokens": gt_tokens,
            "pred_tokens": pred_tokens,
            "errors": sentence_errors,
        })

    # Generate analysis
    analysis = {
        "statistics": stats,
        "error_counts": {k: len(v) for k, v in errors.items()},
        "accuracy": stats["exact_matches"] / stats["total_gt_tokens"] * 100,
        "examples": {k: v[:10] for k, v in errors.items()},  # First 10 of each
    }

    # Save detailed output
    with open(output_path, "w") as f:
        json.dump({
            "analysis": analysis,
            "all_predictions": all_predictions,
        }, f, ensure_ascii=False, indent=2)

    print(f"\nSaved detailed analysis to {output_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("T5 v1 ERROR ANALYSIS SUMMARY")
    print("=" * 70)

    print(f"\nTotal sentences: {stats['total_sentences']}")
    print(f"Total GT tokens: {stats['total_gt_tokens']}")
    print(f"Total predicted tokens: {stats['total_pred_tokens']}")
    print(f"Exact matches: {stats['exact_matches']}")
    print(f"Accuracy: {analysis['accuracy']:.1f}%")

    total_errors = sum(len(v) for v in errors.values())
    print(f"\nTotal errors: {total_errors}")
    print("\nError breakdown:")
    for error_type, error_list in sorted(errors.items(), key=lambda x: -len(x[1])):
        pct = len(error_list) / total_errors * 100 if total_errors > 0 else 0
        print(f"  {error_type}: {len(error_list)} ({pct:.1f}%)")

    # Show examples
    print("\n" + "=" * 70)
    print("EXAMPLE ERRORS BY CATEGORY")
    print("=" * 70)

    for error_type in ["extraction_failure", "segmentation_mismatch", "wrong_reading", "missing", "hallucination"]:
        if errors[error_type]:
            print(f"\n### {error_type.upper()} ({len(errors[error_type])} total)")
            print("-" * 50)
            for ex in errors[error_type][:5]:
                text_display = ex.get("text", "")[:60] + "..."
                print(f"\nSentence: {text_display}")
                print(f"T5 output: {ex.get('raw_output', '')[:70]}...")
                if "gt_surface" in ex:
                    print(f"Expected: {ex['gt_surface']} → {ex['gt_reading']}")
                if "pred_surface" in ex:
                    print(f"Got:      {ex['pred_surface']} → {ex['pred_reading']}")
                if "reading_in_output" in ex:
                    print(f"Reading '{ex['gt_reading']}' in output: {ex['reading_in_output']}")

    return analysis, errors


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent

    test_path = project_root / "data" / "splits" / "test.json"
    model_path = project_root / "models" / "t5-furigana"
    output_path = project_root / "results" / "t5_v1_errors.json"

    analyze_errors(test_path, model_path, output_path)
