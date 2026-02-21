#!/usr/bin/env python3
"""
Prepare data for BERT v2 dictionary-constrained reading classification.

1. Build a surface -> set(readings) dictionary from training data
2. Build a global reading vocabulary
3. Transform each sentence into classification instances

Usage:
    python -m methods.bert_v2.prepare_data \
        --data-dir data/splits_v6_no_matcha \
        --output-dir data/bert_v2_classification \
        --dict-path data/bert_v2_reading_dict.json
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def contains_kanji(text: str) -> bool:
    """Check if text contains kanji characters."""
    for char in text:
        code = ord(char)
        if (0x4E00 <= code <= 0x9FFF or
            0x3400 <= code <= 0x4DBF or
            0xF900 <= code <= 0xFAFF):
            return True
    return False


def build_reading_dict(train_path: Path, val_path: Path) -> dict[str, list[str]]:
    """
    Build surface -> list(readings) dictionary from training and validation data.

    Includes val set to avoid OOV during validation.
    Returns sorted reading lists for deterministic ordering.
    """
    surface_readings = defaultdict(set)

    for path in [train_path, val_path]:
        with open(path) as f:
            sentences = json.load(f)
        for sentence in sentences:
            for token in sentence["tokens"]:
                surface = token["surface"]
                reading = token["reading"]
                if contains_kanji(surface):
                    surface_readings[surface].add(reading)

    # Sort readings for deterministic ordering
    return {surface: sorted(readings) for surface, readings in surface_readings.items()}


def build_reading_vocab(reading_dict: dict[str, list[str]]) -> dict[str, int]:
    """
    Build a global reading vocabulary from all unique readings in the dictionary.

    Index 0 is reserved for <UNK>.
    """
    all_readings = set()
    for readings in reading_dict.values():
        all_readings.update(readings)

    vocab = {"<UNK>": 0}
    for i, reading in enumerate(sorted(all_readings), start=1):
        vocab[reading] = i

    return vocab


def convert_split(
    data_path: Path,
    reading_dict: dict[str, list[str]],
    reading_vocab: dict[str, int],
) -> list[dict]:
    """
    Convert a data split into classification instances.

    For each sentence, extract kanji spans and look up candidate readings.
    """
    with open(data_path) as f:
        sentences = json.load(f)

    instances = []
    stats = Counter()

    for sentence in sentences:
        text = sentence["text"]
        source = sentence.get("source", "unknown")

        for token in sentence["tokens"]:
            surface = token["surface"]
            reading = token["reading"]

            if not contains_kanji(surface):
                continue

            # Find span position in text
            span_start = text.find(surface)
            if span_start == -1:
                stats["span_not_found"] += 1
                continue
            span_end = span_start + len(surface)

            # Look up candidates from dictionary
            if surface in reading_dict:
                candidates = reading_dict[surface]
                if reading in candidates:
                    gold_index = candidates.index(reading)
                    stats["in_dict"] += 1
                else:
                    # Gold reading not in dictionary (unseen in train+val)
                    candidates = candidates + [reading]
                    gold_index = len(candidates) - 1
                    stats["gold_not_in_candidates"] += 1
            else:
                # Surface not in dictionary at all (OOV)
                candidates = [reading]
                gold_index = 0
                stats["oov_surface"] += 1

            # Track ambiguity stats
            n_candidates = len(candidates)
            if n_candidates == 1:
                stats["unambiguous"] += 1
            else:
                stats[f"ambiguous_{min(n_candidates, 5)}+"] += 1
                stats["ambiguous_total"] += 1

            instance = {
                "text": text,
                "surface": surface,
                "span_start": span_start,
                "span_end": span_end,
                "candidates": candidates,
                "gold_reading": reading,
                "gold_index": gold_index,
                "source": source,
            }
            instances.append(instance)

    return instances, stats


def log_dict_statistics(reading_dict: dict[str, list[str]]):
    """Log statistics about the reading dictionary."""
    total_surfaces = len(reading_dict)
    candidate_counts = Counter()
    for surface, readings in reading_dict.items():
        candidate_counts[len(readings)] += 1

    total_readings = sum(len(r) for r in reading_dict.values())
    avg_candidates = total_readings / total_surfaces if total_surfaces > 0 else 0

    print(f"\nReading Dictionary Statistics:")
    print(f"  Total unique surfaces: {total_surfaces}")
    print(f"  Total unique surface-reading pairs: {total_readings}")
    print(f"  Average candidates per surface: {avg_candidates:.2f}")
    print(f"\n  Candidate count distribution:")
    for count in sorted(candidate_counts.keys()):
        n = candidate_counts[count]
        pct = n / total_surfaces * 100
        print(f"    {count} reading(s): {n} surfaces ({pct:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Prepare BERT v2 classification data")
    parser.add_argument("--data-dir", type=Path, default=Path("data/splits_v6_no_matcha"),
                        help="Directory with train.json, val.json, test.json")
    parser.add_argument("--output-dir", type=Path, default=Path("data/bert_v2_classification"),
                        help="Output directory for classification data")
    parser.add_argument("--dict-path", type=Path, default=Path("data/bert_v2_reading_dict.json"),
                        help="Output path for reading dictionary")
    args = parser.parse_args()

    print("=" * 60)
    print("BERT v2 Data Preparation")
    print("=" * 60)

    # Step 1: Build reading dictionary from train + val
    print("\nBuilding reading dictionary from train + val...")
    reading_dict = build_reading_dict(
        args.data_dir / "train.json",
        args.data_dir / "val.json",
    )

    log_dict_statistics(reading_dict)

    # Save dictionary
    args.dict_path.parent.mkdir(parents=True, exist_ok=True)
    with open(args.dict_path, "w") as f:
        json.dump(reading_dict, f, ensure_ascii=False, indent=2)
    print(f"\nSaved reading dictionary to {args.dict_path}")

    # Step 2: Build global reading vocabulary
    reading_vocab = build_reading_vocab(reading_dict)
    print(f"\nGlobal reading vocabulary: {len(reading_vocab)} entries (including <UNK>)")

    # Save reading vocabulary
    args.output_dir.mkdir(parents=True, exist_ok=True)
    vocab_path = args.output_dir / "reading_vocab.json"
    with open(vocab_path, "w") as f:
        json.dump(reading_vocab, f, ensure_ascii=False, indent=2)
    print(f"Saved reading vocabulary to {vocab_path}")

    # Step 3: Convert each split
    for split in ["train", "val", "test"]:
        split_path = args.data_dir / f"{split}.json"
        if not split_path.exists():
            print(f"\nSkipping {split} (file not found)")
            continue

        print(f"\nConverting {split}...")
        instances, stats = convert_split(split_path, reading_dict, reading_vocab)

        output_path = args.output_dir / f"{split}.json"
        with open(output_path, "w") as f:
            json.dump(instances, f, ensure_ascii=False, indent=2)

        print(f"  Instances: {len(instances)}")
        print(f"  Stats: {dict(stats)}")
        print(f"  Saved to {output_path}")

    # Also convert test_comparable if it exists
    comparable_path = args.data_dir / "test_comparable.json"
    if comparable_path.exists():
        print(f"\nConverting test_comparable...")
        instances, stats = convert_split(comparable_path, reading_dict, reading_vocab)
        output_path = args.output_dir / "test_comparable.json"
        with open(output_path, "w") as f:
            json.dump(instances, f, ensure_ascii=False, indent=2)
        print(f"  Instances: {len(instances)}")
        print(f"  Saved to {output_path}")

    print(f"\n{'=' * 60}")
    print("Data preparation complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
