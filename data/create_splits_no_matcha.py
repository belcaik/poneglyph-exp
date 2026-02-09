#!/usr/bin/env python3
"""
Create training splits excluding MATCHA source data.

Loads v5 splits, filters out all MATCHA sentences, re-splits the remaining
data (80/10/10) stratified by source with a fixed random seed.

Also creates a comparable test set from v5 (v5 test minus MATCHA) for
fair cross-version evaluation.

Usage:
    python data/create_splits_no_matcha.py
"""

import json
import random
from collections import Counter
from pathlib import Path


EXCLUDED_SOURCES = {"matcha"}


def load_all_sentences(splits_dir: Path) -> list[dict]:
    """Load all sentences from train/val/test splits."""
    sentences = []
    for name in ["train", "val", "test"]:
        path = splits_dir / f"{name}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                sentences.extend(json.load(f))
    return sentences


def stratified_split(
    sentences: list[dict],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
) -> dict[str, list[dict]]:
    """Split sentences into train/val/test, stratified by source."""
    by_source: dict[str, list[dict]] = {}
    for s in sentences:
        src = s.get("source", "unknown")
        by_source.setdefault(src, []).append(s)

    splits = {"train": [], "val": [], "test": []}

    for source, source_sents in sorted(by_source.items()):
        random.shuffle(source_sents)
        n = len(source_sents)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        splits["train"].extend(source_sents[:train_end])
        splits["val"].extend(source_sents[train_end:val_end])
        splits["test"].extend(source_sents[val_end:])

    for split_name in splits:
        random.shuffle(splits[split_name])

    return splits


def print_table(splits: dict[str, list[dict]]):
    """Print a formatted statistics table."""
    all_sources = set()
    for data in splits.values():
        for s in data:
            all_sources.add(s.get("source", "unknown"))
    sources = sorted(all_sources)

    counts = {}
    for source in sources:
        counts[source] = {}
        for split_name in ["train", "val", "test"]:
            counts[source][split_name] = sum(
                1 for s in splits[split_name] if s.get("source") == source
            )
        counts[source]["total"] = sum(counts[source][k] for k in ["train", "val", "test"])

    print(f"\n{'Source':<12} {'Train':>8} {'Val':>8} {'Test':>8} {'Total':>8}")
    print("-" * 48)
    for source in sources:
        c = counts[source]
        print(f"{source:<12} {c['train']:>8,} {c['val']:>8,} {c['test']:>8,} {c['total']:>8,}")
    print("-" * 48)
    totals = {
        k: sum(counts[s][k] for s in sources)
        for k in ["train", "val", "test", "total"]
    }
    print(f"{'TOTAL':<12} {totals['train']:>8,} {totals['val']:>8,} {totals['test']:>8,} {totals['total']:>8,}")


def check_no_overlap(splits: dict[str, list[dict]]):
    """Verify no sentence text appears in multiple splits."""
    split_texts = {}
    for split_name, data in splits.items():
        split_texts[split_name] = set(s["text"] for s in data)

    names = list(split_texts.keys())
    overlaps = 0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            common = split_texts[names[i]] & split_texts[names[j]]
            if common:
                overlaps += len(common)
                print(f"  WARNING: {len(common)} overlapping texts between {names[i]} and {names[j]}")
    if overlaps == 0:
        print("  No overlapping texts between splits")
    return overlaps


def main():
    random.seed(42)

    v5_dir = Path("data/splits_v5")
    output_dir = Path("data/splits_v6_no_matcha")

    print("=" * 60)
    print("Create Splits Excluding MATCHA")
    print("=" * 60)

    # Load all v5 data
    print(f"\nLoading from {v5_dir}...")
    all_sentences = load_all_sentences(v5_dir)
    source_counts = Counter(s.get("source") for s in all_sentences)
    print(f"  Total v5 sentences: {len(all_sentences)}")
    for src, count in sorted(source_counts.items()):
        excluded = " (EXCLUDED)" if src in EXCLUDED_SOURCES else ""
        print(f"    {src}: {count}{excluded}")

    # Filter out excluded sources
    filtered = [s for s in all_sentences if s.get("source") not in EXCLUDED_SOURCES]
    print(f"\n  After excluding {EXCLUDED_SOURCES}: {len(filtered)} sentences")

    # Create stratified splits
    print("\nCreating stratified splits (80/10/10)...")
    splits = stratified_split(filtered)

    print("\n" + "=" * 60)
    print("V6 SPLIT STATISTICS")
    print("=" * 60)
    print_table(splits)

    # Verify quality
    print("\n" + "=" * 60)
    print("SPLIT QUALITY CHECKS")
    print("=" * 60)

    print("\n1. Overlap check:")
    check_no_overlap(splits)

    print("\n2. All sources in all splits:")
    for split_name, data in splits.items():
        sources = sorted(set(s.get("source") for s in data))
        print(f"  {split_name}: {sources}")

    print("\n3. Sample sentences (5 per source from train):")
    by_source_train = {}
    for s in splits["train"]:
        src = s.get("source", "unknown")
        by_source_train.setdefault(src, []).append(s)

    for src in sorted(by_source_train):
        print(f"\n  [{src}]")
        sample = random.sample(by_source_train[src], min(5, len(by_source_train[src])))
        for sent in sample:
            text = sent["text"][:70]
            n_tok = len(sent.get("tokens", []))
            print(f"    ({n_tok} tok) {text}{'...' if len(sent['text']) > 70 else ''}")

    # Save splits
    output_dir.mkdir(parents=True, exist_ok=True)
    for split_name, data in splits.items():
        path = output_dir / f"{split_name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n  Saved {split_name}: {len(data)} sentences -> {path}")

    # Save all.json
    all_data = splits["train"] + splits["val"] + splits["test"]
    all_path = output_dir / "all.json"
    with open(all_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"  Saved all: {len(all_data)} sentences -> {all_path}")

    # Create comparable test set (v5 test minus MATCHA)
    print("\n" + "=" * 60)
    print("COMPARABLE TEST SET")
    print("=" * 60)

    v5_test_path = v5_dir / "test.json"
    with open(v5_test_path, "r", encoding="utf-8") as f:
        v5_test = json.load(f)

    comparable_test = [s for s in v5_test if s.get("source") not in EXCLUDED_SOURCES]
    comparable_path = output_dir / "test_comparable.json"
    with open(comparable_path, "w", encoding="utf-8") as f:
        json.dump(comparable_test, f, ensure_ascii=False, indent=2)

    print(f"  v5 test total: {len(v5_test)}")
    print(f"  v5 test minus MATCHA: {len(comparable_test)}")
    comp_sources = Counter(s.get("source") for s in comparable_test)
    for src, count in sorted(comp_sources.items()):
        print(f"    {src}: {count}")
    print(f"  Saved -> {comparable_path}")

    print(f"\nDone!")


if __name__ == "__main__":
    main()
