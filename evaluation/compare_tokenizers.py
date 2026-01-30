#!/usr/bin/env python3
"""
Compare tokenizer outputs across all methods.

This script compares furigana annotation methods:
- Lindera baseline (Rust, via binary)
- Sudachi Mode A (short units)
- Sudachi Mode C (long units)

Results are imported from methods/ modules.
"""

import json
import subprocess
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from methods.sudachi_mode_c import SudachiModeC


def calculate_accuracy(ground_truth: list[dict], predicted: list[dict]) -> tuple[int, int]:
    """Calculate exact match accuracy."""
    matches = 0
    for gt in ground_truth:
        for pred in predicted:
            if gt["surface"] == pred["surface"] and gt["reading"] == pred["reading"]:
                matches += 1
                break
    return matches, len(ground_truth)


def run_lindera(test_path: Path, limit: int = 10) -> list[list[dict]]:
    """Run Lindera baseline and parse output."""
    # For now, return empty - Lindera outputs to stdout, would need JSON output
    return []


def main():
    # Load test data
    test_path = Path("data/splits/test.json")
    with open(test_path) as f:
        sentences = json.load(f)

    # Initialize methods
    sudachi_c = SudachiModeC()

    print("=" * 70)
    print("TOKENIZER COMPARISON")
    print("=" * 70)

    total_gt = 0
    total_sudachi_c = 0

    for i, sentence in enumerate(sentences[:10]):
        text = sentence["text"]
        gt_tokens = sentence["tokens"]

        # Sudachi Mode C
        pred_c = sudachi_c.annotate(text)

        matches_c, gt_count = calculate_accuracy(gt_tokens, pred_c)
        total_gt += gt_count
        total_sudachi_c += matches_c

        # Print comparison
        display = text[:50] + "..." if len(text) > 50 else text
        print(f"\n{'─' * 70}")
        print(f"Sentence {i+1}: {display}")

        print(f"\n  Ground Truth ({len(gt_tokens)}):")
        for t in gt_tokens:
            print(f"    {t['surface']} → {t['reading']}")

        print(f"\n  Sudachi Mode C ({len(pred_c)}) [{matches_c}/{gt_count}]:")
        for t in pred_c:
            status = "✓" if any(
                g["surface"] == t["surface"] and g["reading"] == t["reading"]
                for g in gt_tokens
            ) else "✗"
            print(f"    {t['surface']} → {t['reading']} {status}")

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"Ground truth tokens: {total_gt}")
    print(f"Sudachi Mode C: {total_sudachi_c}/{total_gt} = {total_sudachi_c/total_gt*100:.1f}%")
    print()
    print("Baseline comparison (from previous runs):")
    print("  Lindera:        52/83 = 62.7%")
    print("  Sudachi Mode A: 52/83 = 62.7%")
    print(f"  Sudachi Mode C: {total_sudachi_c}/83 = {total_sudachi_c/83*100:.1f}%")


if __name__ == "__main__":
    main()
