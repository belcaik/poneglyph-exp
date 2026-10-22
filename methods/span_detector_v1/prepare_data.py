#!/usr/bin/env python3
"""
Prepare character-level BIO data for span detection.

Converts v7 normalized sentences into character-level BIO tags:
- B-SPAN: First character of an annotatable morpheme
- I-SPAN: Continuation character of an annotatable morpheme
- O: Outside any annotatable morpheme

Usage:
    python -m methods.span_detector_v1.prepare_data \
        --data-dir data/splits_v7_normalized \
        --output-dir data/span_detector_v1
"""

import argparse
import json
from collections import Counter
from pathlib import Path


LABEL_MAP = {"O": 0, "B-SPAN": 1, "I-SPAN": 2}
LABEL_NAMES = {v: k for k, v in LABEL_MAP.items()}


def contains_kanji(text: str) -> bool:
    """Check if text contains kanji characters."""
    for char in text:
        code = ord(char)
        if (0x4E00 <= code <= 0x9FFF or
            0x3400 <= code <= 0x4DBF or
            0xF900 <= code <= 0xFAFF):
            return True
    return False


def sentence_to_bio(sentence: dict) -> dict | None:
    """Convert a sentence with token annotations to character-level BIO labels.

    Returns None if the sentence has no annotatable spans (all hiragana/katakana).
    """
    text = sentence["text"]
    tokens = sentence["tokens"]
    source = sentence.get("source", "unknown")

    # Initialize all characters as O
    char_labels = [0] * len(text)  # 0 = O

    spans_found = 0
    used_positions = set()

    for token in tokens:
        surface = token["surface"]

        # Only label spans containing kanji
        if not contains_kanji(surface):
            continue

        # Find surface position in text, avoiding reuse
        search_start = 0
        span_start = -1
        while search_start < len(text):
            pos = text.find(surface, search_start)
            if pos == -1:
                break
            # Check no overlap with already-used positions
            if not any(p in used_positions for p in range(pos, pos + len(surface))):
                span_start = pos
                break
            search_start = pos + 1

        if span_start == -1:
            continue

        span_end = span_start + len(surface)

        # Mark positions as used
        for p in range(span_start, span_end):
            used_positions.add(p)

        # Assign BIO labels
        char_labels[span_start] = 1  # B-SPAN
        for i in range(span_start + 1, span_end):
            char_labels[i] = 2  # I-SPAN

        spans_found += 1

    if spans_found == 0:
        return None

    return {
        "text": text,
        "char_labels": char_labels,
        "source": source,
        "num_spans": spans_found,
    }


def convert_split(data_path: Path) -> tuple[list[dict], Counter]:
    """Convert an entire data split to BIO format."""
    with open(data_path) as f:
        sentences = json.load(f)

    results = []
    stats = Counter()

    for sentence in sentences:
        bio = sentence_to_bio(sentence)
        if bio is None:
            stats["skipped_no_spans"] += 1
            continue

        results.append(bio)
        stats["sentences"] += 1
        stats["total_chars"] += len(bio["text"])
        stats["total_spans"] += bio["num_spans"]

        for label in bio["char_labels"]:
            stats[LABEL_NAMES[label]] += 1

    return results, stats


def main():
    parser = argparse.ArgumentParser(description="Prepare BIO data for span detection")
    parser.add_argument("--data-dir", type=Path, default=Path("data/splits_v7_normalized"),
                        help="Directory with train.json, val.json, test.json")
    parser.add_argument("--output-dir", type=Path, default=Path("data/span_detector_v1"),
                        help="Output directory for BIO data")
    args = parser.parse_args()

    print("=" * 60)
    print("Span Detector v1 - BIO Data Preparation")
    print("=" * 60)
    print(f"Data dir:   {args.data_dir}")
    print(f"Output dir: {args.output_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    all_stats = Counter()

    for split in ["train", "val", "test"]:
        split_path = args.data_dir / f"{split}.json"
        if not split_path.exists():
            print(f"\nSkipping {split} (file not found)")
            continue

        print(f"\nConverting {split}...")
        data, stats = convert_split(split_path)

        output_path = args.output_dir / f"{split}.json"
        with open(output_path, "w") as f:
            json.dump(data, f, ensure_ascii=False)

        print(f"  Sentences: {stats['sentences']} (skipped {stats.get('skipped_no_spans', 0)})")
        print(f"  Total chars: {stats['total_chars']}")
        print(f"  Total spans: {stats['total_spans']}")
        print(f"  Label distribution:")
        total_labels = stats["O"] + stats["B-SPAN"] + stats["I-SPAN"]
        for label_name in ["O", "B-SPAN", "I-SPAN"]:
            count = stats.get(label_name, 0)
            pct = count / total_labels * 100 if total_labels > 0 else 0
            print(f"    {label_name}: {count:>8} ({pct:.1f}%)")

        all_stats += stats

    # Save label map
    with open(args.output_dir / "label_map.json", "w") as f:
        json.dump(LABEL_MAP, f, indent=2)

    # Print overall summary
    print(f"\n{'=' * 60}")
    print("Overall Summary")
    print(f"{'=' * 60}")
    print(f"Total sentences: {all_stats['sentences']}")
    print(f"Total chars:     {all_stats['total_chars']}")
    print(f"Total spans:     {all_stats['total_spans']}")
    total_labels = all_stats["O"] + all_stats["B-SPAN"] + all_stats["I-SPAN"]
    print(f"\nLabel distribution:")
    for label_name in ["O", "B-SPAN", "I-SPAN"]:
        count = all_stats.get(label_name, 0)
        pct = count / total_labels * 100 if total_labels > 0 else 0
        print(f"  {label_name}: {count:>8} ({pct:.1f}%)")

    # Class imbalance ratio
    b_count = all_stats.get("B-SPAN", 0)
    i_count = all_stats.get("I-SPAN", 0)
    o_count = all_stats.get("O", 0)
    bi_count = b_count + i_count
    print(f"\nImbalance ratio O:(B+I) = {o_count / bi_count:.1f}:1" if bi_count > 0 else "")
    print(f"Avg span length: {(b_count + i_count) / b_count:.2f} chars" if b_count > 0 else "")
    print(f"\nData preparation complete!")


if __name__ == "__main__":
    main()
