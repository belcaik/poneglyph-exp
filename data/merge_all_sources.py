#!/usr/bin/env python3
"""
Merge existing training splits with new UD source data.

Preserves existing split assignments for nhk/matcha/kahoku/hirogaru.
Adds new sources (ud_gsd, ud_pud) with 80/10/10 train/val/test split.

Usage:
    python data/merge_all_sources.py
    python data/merge_all_sources.py --output data/splits_v5
"""

import argparse
import json
import random
from collections import Counter
from pathlib import Path


def load_existing_splits(splits_dir: Path) -> dict[str, list[dict]]:
    """Load existing train/val/test splits."""
    splits = {}
    for name in ['train', 'val', 'test']:
        path = splits_dir / f'{name}.json'
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                splits[name] = json.load(f)
        else:
            splits[name] = []
    return splits


def load_new_source(filepath: Path) -> list[dict]:
    """Load processed sentences from a new source."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def split_new_source(
    sentences: list[dict],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
) -> dict[str, list[dict]]:
    """Split new source sentences into train/val/test (default 80/10/10)."""
    random.shuffle(sentences)
    n = len(sentences)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    return {
        'train': sentences[:train_end],
        'val': sentences[train_end:val_end],
        'test': sentences[val_end:],
    }


def print_summary_table(splits: dict[str, list[dict]]):
    """Print a summary table of sentences by source and split."""
    # Gather all sources
    all_sources = set()
    for name, data in splits.items():
        for s in data:
            all_sources.add(s.get('source', 'unknown'))

    sources = sorted(all_sources)

    # Count per source per split
    counts = {}
    for source in sources:
        counts[source] = {}
        for split_name in ['train', 'val', 'test']:
            counts[source][split_name] = sum(
                1 for s in splits[split_name]
                if s.get('source') == source
            )
        counts[source]['total'] = sum(counts[source].values())

    # Print table
    print(f"\n{'Source':<12} {'Train':>8} {'Val':>8} {'Test':>8} {'Total':>8}")
    print("-" * 48)
    for source in sources:
        c = counts[source]
        print(f"{source:<12} {c['train']:>8,} {c['val']:>8,} {c['test']:>8,} {c['total']:>8,}")

    # Totals
    print("-" * 48)
    totals = {
        split: sum(counts[s][split] for s in sources)
        for split in ['train', 'val', 'test', 'total']
    }
    print(f"{'TOTAL':<12} {totals['train']:>8,} {totals['val']:>8,} {totals['test']:>8,} {totals['total']:>8,}")


def main():
    parser = argparse.ArgumentParser(description='Merge all data sources into splits')
    parser.add_argument(
        '--existing-splits', type=Path, default=Path('data/splits'),
        help='Directory with existing train/val/test splits',
    )
    parser.add_argument(
        '--output', type=Path, default=Path('data/splits'),
        help='Output directory for merged splits (default: overwrite existing)',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Print statistics without writing files',
    )
    args = parser.parse_args()

    random.seed(42)

    print("=" * 60)
    print("Merge All Sources into Training Splits")
    print("=" * 60)

    # Load existing splits
    print(f"\nLoading existing splits from {args.existing_splits}...")
    existing = load_existing_splits(args.existing_splits)
    for name, data in existing.items():
        sources = Counter(s.get('source') for s in data)
        print(f"  {name}: {len(data)} sentences — {dict(sorted(sources.items()))}")

    # Track existing sources so we don't re-add them
    existing_sources = set()
    for data in existing.values():
        for s in data:
            existing_sources.add(s.get('source'))
    print(f"\nExisting sources (preserved): {sorted(existing_sources)}")

    # Load new sources
    new_sources = {}
    processed_dir = Path('data/processed')

    for source_name in ['ud_gsd', 'ud_pud']:
        filepath = processed_dir / source_name / 'sentences.json'
        if filepath.exists():
            sentences = load_new_source(filepath)
            if source_name not in existing_sources:
                new_sources[source_name] = sentences
                print(f"  New source: {source_name} — {len(sentences)} sentences")
            else:
                print(f"  Skipping {source_name}: already in existing splits")
        else:
            print(f"  Not found: {filepath}")

    if not new_sources:
        print("\nNo new sources to add.")
        return

    # Split new sources and merge
    merged = {name: list(data) for name, data in existing.items()}

    for source_name, sentences in new_sources.items():
        source_splits = split_new_source(sentences)
        for split_name in ['train', 'val', 'test']:
            merged[split_name].extend(source_splits[split_name])
            print(f"  Added {len(source_splits[split_name])} {source_name} "
                  f"sentences to {split_name}")

    # Shuffle each split
    for split_name in merged:
        random.shuffle(merged[split_name])

    # Print summary
    print("\n" + "=" * 60)
    print("MERGED DATASET SUMMARY")
    print("=" * 60)
    print_summary_table(merged)

    # Compute token statistics
    print("\n" + "=" * 60)
    print("TOKEN STATISTICS BY SOURCE")
    print("=" * 60)
    all_sentences = merged['train'] + merged['val'] + merged['test']
    source_stats = {}
    for s in all_sentences:
        src = s.get('source', 'unknown')
        if src not in source_stats:
            source_stats[src] = {'n': 0, 'tokens': 0, 'chars': 0}
        source_stats[src]['n'] += 1
        source_stats[src]['tokens'] += len(s.get('tokens', []))
        source_stats[src]['chars'] += len(s.get('text', ''))

    print(f"\n{'Source':<12} {'Sentences':>10} {'Tokens':>10} {'Avg Tok/Sent':>14} {'Avg Chars':>10}")
    print("-" * 60)
    for src in sorted(source_stats):
        st = source_stats[src]
        avg_tok = st['tokens'] / st['n'] if st['n'] else 0
        avg_chr = st['chars'] / st['n'] if st['n'] else 0
        print(f"{src:<12} {st['n']:>10,} {st['tokens']:>10,} {avg_tok:>14.1f} {avg_chr:>10.1f}")

    if args.dry_run:
        print("\n(dry run — no files written)")
        return

    # Save merged splits
    args.output.mkdir(parents=True, exist_ok=True)

    for split_name, data in merged.items():
        output_path = args.output / f'{split_name}.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n  Saved {split_name}: {len(data)} sentences → {output_path}")

    # Also save combined all.json
    all_data = merged['train'] + merged['val'] + merged['test']
    all_path = args.output / 'all.json'
    with open(all_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"  Saved all: {len(all_data)} sentences → {all_path}")

    print(f"\n✓ Merge complete! Total sentences: {len(all_data)}")


if __name__ == '__main__':
    main()
