#!/usr/bin/env python3
"""Assemble final poneglyph_v1 dataset from consensus annotations.

Splits by episode (not sentence) to avoid data leakage.
Ensures proportional series representation across splits.
"""

import json
import random
from collections import defaultdict
from pathlib import Path


def main():
    data_dir = Path("data/dataset_gen")
    output_dir = Path("data/poneglyph_v1")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load consensus data (accepted + flagged, both have tokens)
    accepted = []
    flagged = []

    with open(data_dir / "consensus_accepted.json") as f:
        accepted = json.load(f)
    with open(data_dir / "consensus_flagged.json") as f:
        flagged = json.load(f)

    all_entries = accepted + flagged
    print(f"Total entries: {len(all_entries)} ({len(accepted)} clean + {len(flagged)} resolved)")

    # Assign annotation method
    for entry in all_entries:
        has_consensus = any(t.get("confidence") == "consensus" for t in entry.get("tokens", []))
        has_claude = any(t.get("confidence") in ("claude_only", "claude_default") for t in entry.get("tokens", []))
        if has_consensus and not has_claude:
            entry["annotation_method"] = "llm_consensus"
            entry["confidence"] = "high"
        elif has_consensus:
            entry["annotation_method"] = "llm_consensus"
            entry["confidence"] = "medium"
        else:
            entry["annotation_method"] = "claude_only"
            entry["confidence"] = "medium"

    # Generate compact IDs
    series_prefixes = {}
    for entry in all_entries:
        s = entry["series"]
        if s not in series_prefixes:
            # Create short prefix
            parts = s.split("_")
            prefix = "".join(p[0] for p in parts[:3])
            series_prefixes[s] = prefix

    for entry in all_entries:
        prefix = series_prefixes[entry["series"]]
        ep = entry.get("episode", "E00").lower()
        entry["id"] = f"{prefix}_{ep}_{entry['id']:04d}"

    # Group by (series, episode) for splitting
    by_episode = defaultdict(list)
    for entry in all_entries:
        key = (entry["series"], entry.get("episode", "E00"))
        by_episode[key].append(entry)

    # Split episodes: strict 80/10/10 by series
    # Pool all episodes, shuffle, then assign globally to hit target ratio
    by_series = defaultdict(list)
    for key in by_episode:
        by_series[key[0]].append(key)

    random.seed(42)

    # Collect all episode keys with their sentence counts
    all_episode_keys = []
    for series, episode_keys in by_series.items():
        random.shuffle(episode_keys)
        all_episode_keys.extend(episode_keys)

    total_sents = sum(len(by_episode[k]) for k in all_episode_keys)
    target_val = int(total_sents * 0.10)
    target_test = int(total_sents * 0.10)

    # Assign per-series: for series with many episodes, split proportionally.
    # For series with few episodes (1-3), put all in train to avoid skewing.
    train_entries = []
    val_entries = []
    test_entries = []

    for series, episode_keys in by_series.items():
        random.shuffle(episode_keys)
        n = len(episode_keys)

        if n <= 2:
            # Too few episodes to split — all go to train
            for key in episode_keys:
                train_entries.extend(by_episode[key])
        else:
            # Proportional split: round to nearest integer
            n_test = max(1, round(n * 0.10))
            n_val = max(1, round(n * 0.10))
            # But cap so we don't take more than 30% for val+test
            if n_test + n_val > n * 0.3:
                n_test = 1
                n_val = 1
            n_train = n - n_test - n_val

            test_eps = episode_keys[:n_test]
            val_eps = episode_keys[n_test:n_test + n_val]
            train_eps = episode_keys[n_test + n_val:]

            for key in train_eps:
                train_entries.extend(by_episode[key])
            for key in val_eps:
                val_entries.extend(by_episode[key])
            for key in test_eps:
                test_entries.extend(by_episode[key])

    # Remove internal fields before saving
    def clean_entry(entry):
        return {
            "id": entry["id"],
            "source": entry["series"],
            "episode": entry.get("episode", "E00"),
            "text": entry["text"],
            "tokens": entry.get("tokens", []),
            "annotation_method": entry.get("annotation_method", "claude_only"),
            "confidence": entry.get("confidence", "medium"),
        }

    train = [clean_entry(e) for e in train_entries]
    val = [clean_entry(e) for e in val_entries]
    test = [clean_entry(e) for e in test_entries]

    # Save
    for split, data in [("train", train), ("val", val), ("test", test)]:
        with open(output_dir / f"{split}.json", "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # Metadata
    metadata = {
        "name": "poneglyph_v1",
        "description": "LLM-annotated furigana dataset from Japanese subtitle sources",
        "annotation_conventions": "Poneglyph (compound nouns, verb chains, proper nouns)",
        "sources": list(set(e["source"] for e in train + val + test)),
        "splits": {
            "train": len(train),
            "val": len(val),
            "test": len(test),
            "total": len(train) + len(val) + len(test),
        },
        "annotation_models": ["claude_opus_4", "gemini_flash"],
        "consensus_method": "Accept when both agree; default to Claude for disagreements",
    }
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\nDataset assembled:")
    print(f"  Train: {len(train)} sentences")
    print(f"  Val:   {len(val)} sentences")
    print(f"  Test:  {len(test)} sentences")
    print(f"  Total: {len(train) + len(val) + len(test)} sentences")
    print(f"\nSaved to {output_dir}/")

    # Per-series distribution
    print(f"\nPer-series in train/val/test:")
    series_counts = defaultdict(lambda: [0, 0, 0])
    for e in train:
        series_counts[e["source"]][0] += 1
    for e in val:
        series_counts[e["source"]][1] += 1
    for e in test:
        series_counts[e["source"]][2] += 1
    for s in sorted(series_counts):
        c = series_counts[s]
        print(f"  {s}: {c[0]}/{c[1]}/{c[2]}")


if __name__ == "__main__":
    main()
