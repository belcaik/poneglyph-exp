#!/usr/bin/env python3
"""
Reprocess data splits with sentence segmentation.

Applies segmentation to MATCHA and Kahoku sources (which have article/paragraph-level data)
while preserving NHK and Hirogaru data (which are already sentence-level).

Output: data/splits_v4/ with uniformly segmented data.
"""

import json
from pathlib import Path
from collections import defaultdict
import statistics

from segment_sentences import segment_item, validate_token_preservation


# Sources that need segmentation (article/paragraph level)
SOURCES_TO_SEGMENT = {"matcha", "kahoku"}

# Sources already at sentence level - pass through unchanged
SOURCES_PASS_THROUGH = {"nhk", "hirogaru"}


def process_split(input_path: Path, output_path: Path, verbose: bool = True) -> dict:
    """
    Process a single split file with sentence segmentation.

    Returns statistics about the processing.
    """
    with open(input_path) as f:
        data = json.load(f)

    stats = defaultdict(lambda: {
        "original_items": 0,
        "segmented_items": 0,
        "original_tokens": 0,
        "segmented_tokens": 0,
        "skipped_no_tokens": 0,
    })

    output_items = []

    for item in data:
        source = item.get("source", "unknown")
        tokens = item.get("tokens", [])
        original_token_count = len(tokens)

        stats[source]["original_items"] += 1
        stats[source]["original_tokens"] += original_token_count

        if source in SOURCES_TO_SEGMENT:
            # Apply segmentation
            segmented = segment_item(item)

            for seg_item in segmented:
                seg_tokens = seg_item.get("tokens", [])
                if len(seg_tokens) == 0:
                    stats[source]["skipped_no_tokens"] += 1
                    continue

                # Remove internal metadata
                clean_item = {
                    "source": seg_item["source"],
                    "article_id": seg_item["article_id"],
                    "text": seg_item["text"],
                    "tokens": seg_item["tokens"],
                }
                output_items.append(clean_item)
                stats[source]["segmented_items"] += 1
                stats[source]["segmented_tokens"] += len(seg_tokens)

        else:
            # Pass through unchanged (NHK, Hirogaru)
            if original_token_count == 0:
                stats[source]["skipped_no_tokens"] += 1
                continue

            output_items.append(item)
            stats[source]["segmented_items"] += 1
            stats[source]["segmented_tokens"] += original_token_count

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_items, f, ensure_ascii=False, indent=2)

    # Convert stats to regular dict
    stats_dict = {k: dict(v) for k, v in stats.items()}

    if verbose:
        print(f"\nProcessed {input_path.name}:")
        for source, s in sorted(stats_dict.items()):
            orig = s["original_items"]
            seg = s["segmented_items"]
            orig_tok = s["original_tokens"]
            seg_tok = s["segmented_tokens"]
            lost = orig_tok - seg_tok
            pct = 100 * seg_tok / orig_tok if orig_tok > 0 else 100
            print(f"  {source}: {orig} -> {seg} items, {orig_tok} -> {seg_tok} tokens ({pct:.1f}% preserved, {lost} lost)")

    return stats_dict


def analyze_output(output_path: Path) -> dict:
    """Analyze the output file to verify structure uniformity."""
    with open(output_path) as f:
        data = json.load(f)

    source_stats = defaultdict(lambda: {
        "count": 0,
        "char_lengths": [],
        "token_counts": [],
    })

    for item in data:
        source = item.get("source", "unknown")
        text = item.get("text", "")
        tokens = item.get("tokens", [])

        source_stats[source]["count"] += 1
        source_stats[source]["char_lengths"].append(len(text))
        source_stats[source]["token_counts"].append(len(tokens))

    results = {}
    for source, stats in source_stats.items():
        results[source] = {
            "count": stats["count"],
            "avg_chars": statistics.mean(stats["char_lengths"]) if stats["char_lengths"] else 0,
            "max_chars": max(stats["char_lengths"]) if stats["char_lengths"] else 0,
            "avg_tokens": statistics.mean(stats["token_counts"]) if stats["token_counts"] else 0,
            "total_tokens": sum(stats["token_counts"]),
        }

    return results


def main():
    import os
    os.chdir("/home/belcaik/Dev/poneglyph-exp")

    input_dir = Path("data/splits")
    output_dir = Path("data/splits_v4")

    print("=" * 60)
    print("T5 v4 Data Reprocessing with Sentence Segmentation")
    print("=" * 60)
    print(f"\nInput: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"\nSources to segment: {SOURCES_TO_SEGMENT}")
    print(f"Sources pass-through: {SOURCES_PASS_THROUGH}")

    all_stats = {}

    # Process each split
    for split in ["train", "val", "test"]:
        input_path = input_dir / f"{split}.json"
        output_path = output_dir / f"{split}.json"

        if not input_path.exists():
            print(f"\nSkipping {split} (not found)")
            continue

        print(f"\n{'=' * 40}")
        print(f"Processing {split}")
        print("=" * 40)

        stats = process_split(input_path, output_path)
        all_stats[split] = stats

    # Analyze output
    print(f"\n{'=' * 60}")
    print("Output Analysis (Uniformity Check)")
    print("=" * 60)

    for split in ["train", "val", "test"]:
        output_path = output_dir / f"{split}.json"
        if output_path.exists():
            analysis = analyze_output(output_path)
            print(f"\n{split}:")
            print(f"  {'Source':<12} {'Count':>8} {'Avg Chars':>10} {'Max Chars':>10} {'Total Tokens':>12}")
            print(f"  {'-'*12} {'-'*8} {'-'*10} {'-'*10} {'-'*12}")
            total_items = 0
            total_tokens = 0
            for source in sorted(analysis.keys()):
                a = analysis[source]
                print(f"  {source:<12} {a['count']:>8} {a['avg_chars']:>10.1f} {a['max_chars']:>10} {a['total_tokens']:>12}")
                total_items += a["count"]
                total_tokens += a["total_tokens"]
            print(f"  {'TOTAL':<12} {total_items:>8} {'-':>10} {'-':>10} {total_tokens:>12}")

    # Summary report
    print(f"\n{'=' * 60}")
    print("Token Preservation Summary")
    print("=" * 60)

    for split, stats in all_stats.items():
        print(f"\n{split}:")
        total_orig = sum(s["original_tokens"] for s in stats.values())
        total_seg = sum(s["segmented_tokens"] for s in stats.values())
        total_lost = total_orig - total_seg
        pct = 100 * total_seg / total_orig if total_orig > 0 else 100
        print(f"  Original: {total_orig} tokens")
        print(f"  After segmentation: {total_seg} tokens")
        print(f"  Lost: {total_lost} tokens ({100-pct:.2f}%)")
        print(f"  Preservation rate: {pct:.2f}%")

    print("\n" + "=" * 60)
    print("Done! Output written to data/splits_v4/")
    print("=" * 60)


if __name__ == "__main__":
    main()
