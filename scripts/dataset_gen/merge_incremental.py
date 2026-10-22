#!/usr/bin/env python3
"""Merge incremental annotations with existing dataset and rebuild poneglyph_v1.

Combines:
1. Existing annotations from data/dataset_gen/annotations_claude.json
2. Existing v1/v2 batch results from /tmp/dataset_claude_batch_*.json and /tmp/dataset_v2_batch_*.json
3. New incremental batch results from /tmp/dataset_inc_batch_*.json
4. Existing poneglyph_v1 dataset entries

Deduplicates by text, assembles into train/val/test splits.
"""

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
DATA_DIR = REPO / "data" / "dataset_gen"
OUTPUT_DIR = REPO / "data" / "poneglyph_v1"


def is_kanji(c):
    cp = ord(c)
    return 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF


def extract_json(filepath):
    content = filepath.read_text().strip()
    content = re.sub(r'^```(?:json)?\s*\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n?```\s*$', '', content, flags=re.MULTILINE)
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        brace = content.find('{')
        if brace >= 0:
            depth = 0
            for i in range(brace, len(content)):
                if content[i] == '{': depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        try: return json.loads(content[brace:i+1])
                        except: break
    return None


def load_all_annotations():
    """Load ALL annotation sources into a text→annotations map."""
    text_to_annot = {}
    loaded_sources = Counter()

    # 1. Existing annotations_claude.json
    annot_path = DATA_DIR / "annotations_claude.json"
    if annot_path.exists():
        for a in json.load(open(annot_path)):
            if a.get("annotations") and not a.get("parse_failure"):
                text_to_annot[a["text"]] = {
                    "annotations": a["annotations"],
                    "series": a.get("series", "unknown"),
                    "episode": a.get("episode", "E00"),
                }
                loaded_sources["annotations_claude"] += 1

    # 2. Existing dataset entries
    for split in ["train", "val", "test"]:
        path = OUTPUT_DIR / f"{split}.json"
        if path.exists():
            for e in json.load(open(path)):
                if e.get("tokens") and e["text"] not in text_to_annot:
                    text_to_annot[e["text"]] = {
                        "annotations": e["tokens"],
                        "series": e.get("source", "unknown"),
                        "episode": e.get("episode", "E00"),
                    }
                    loaded_sources[f"existing_{split}"] += 1

    # 3. All batch files from /tmp
    for pattern in ["dataset_claude_batch_*.json", "dataset_v2_batch_*.json",
                     "dataset_inc_batch_*.json"]:
        for bf in sorted(Path("/tmp").glob(pattern)):
            try:
                data = extract_json(bf)
                if not data or not isinstance(data, dict):
                    continue
                for sid, annots in data.items():
                    if isinstance(annots, list) and annots:
                        # We need to find the text for this ID — check filtered sentences
                        loaded_sources[pattern.split("_")[1]] += 1
            except Exception:
                continue

    print(f"  Sources: {dict(loaded_sources)}")
    print(f"  Total unique texts: {len(text_to_annot)}")
    return text_to_annot


def load_filtered_sentences():
    """Load all filtered sentence files to get text→metadata mapping."""
    sentences = {}

    # Original filtered
    path = DATA_DIR / "filtered_sentences.json"
    if path.exists():
        for s in json.load(open(path)):
            sentences[s["text"]] = {
                "series": s.get("series", "unknown"),
                "episode": s.get("episode", "E00"),
            }

    # New incremental filtered
    path = DATA_DIR / "new_filtered_sentences.json"
    if path.exists():
        for s in json.load(open(path)):
            sentences[s["text"]] = {
                "series": s.get("series", "unknown"),
                "episode": s.get("episode", "E00"),
            }

    return sentences


def load_incremental_batches():
    """Load incremental batch annotations, matched against filtered sentences."""
    filtered = load_filtered_sentences()
    text_to_annot = {}

    # Build id→text mapping from new_filtered_sentences.json
    id_to_text = {}
    path = DATA_DIR / "new_filtered_sentences.json"
    if path.exists():
        for s in json.load(open(path)):
            id_to_text[str(s["id"])] = s["text"]
            id_to_text[s["id"]] = s["text"]

    # Also from filtered_sentences.json
    path = DATA_DIR / "filtered_sentences.json"
    if path.exists():
        for s in json.load(open(path)):
            id_to_text[str(s["id"])] = s["text"]
            id_to_text[s["id"]] = s["text"]

    # Load all batch files
    for pattern in ["dataset_inc_batch_*.json", "dataset_claude_batch_*.json",
                     "dataset_v2_batch_*.json"]:
        for bf in sorted(Path("/tmp").glob(pattern)):
            try:
                data = extract_json(bf)
                if not data or not isinstance(data, dict):
                    continue
                for sid, annots in data.items():
                    if not isinstance(annots, list) or not annots:
                        continue
                    # Find the text for this ID
                    text = id_to_text.get(sid) or id_to_text.get(int(sid) if sid.isdigit() else sid)
                    if text and text not in text_to_annot:
                        meta = filtered.get(text, {"series": "unknown", "episode": "E00"})
                        text_to_annot[text] = {
                            "annotations": annots,
                            "series": meta["series"],
                            "episode": meta["episode"],
                        }
            except Exception:
                continue

    return text_to_annot


def main():
    print("=" * 60)
    print("MERGE AND REBUILD DATASET")
    print("=" * 60)

    # Load all annotation sources
    print("\n[1] Loading existing annotations...")
    existing = load_all_annotations()

    print("\n[2] Loading incremental batch annotations...")
    incremental = load_incremental_batches()

    # Merge (incremental overrides existing for same text)
    print("\n[3] Merging...")
    merged = {**existing, **incremental}
    # Also add existing entries not in incremental
    for text, data in existing.items():
        if text not in merged:
            merged[text] = data

    print(f"  Existing: {len(existing)}")
    print(f"  Incremental: {len(incremental)}")
    print(f"  Merged (deduped): {len(merged)}")

    # Build dataset entries
    # First: preserve ALL existing dataset entries as-is (they already have correct tokens)
    entries = []
    existing_texts = set()
    for split in ["train", "val", "test"]:
        path = OUTPUT_DIR / f"{split}.json"
        if path.exists():
            for e in json.load(open(path)):
                if e["text"] not in existing_texts:
                    entries.append(e)
                    existing_texts.add(e["text"])

    print(f"  Preserved existing: {len(entries)}")

    # Second: add NEW entries from incremental annotations
    new_count = 0
    for text, data in merged.items():
        if text in existing_texts:
            continue  # Already in dataset

        annots = data["annotations"]
        valid = [a for a in annots if isinstance(a, dict) and "surface" in a and "reading" in a]
        if not valid:
            continue

        # Build tokens with positions
        tokens = []
        used_positions = set()
        for a in valid:
            surface = a.get("surface", "")
            if not surface:
                continue
            pos = 0
            while pos < len(text):
                idx = text.find(surface, pos)
                if idx == -1:
                    break
                span = set(range(idx, idx + len(surface)))
                if not span & used_positions:
                    used_positions |= span
                    tokens.append({
                        "surface": surface,
                        "reading": a.get("reading", ""),
                        "start": idx,
                        "end": idx + len(surface),
                        "type": a.get("type", "noun"),
                        "confidence": a.get("confidence", "claude_only"),
                    })
                    break
                pos = idx + 1

        if not tokens:
            continue

        entries.append({
            "source": data["series"],
            "episode": data["episode"],
            "text": text,
            "tokens": tokens,
            "annotation_method": "claude_only",
            "confidence": "medium",
        })
        new_count += 1

    print(f"  New entries added: {new_count}")

    print(f"  Valid entries: {len(entries)}")

    # Split 80/10/10 by episode
    print("\n[4] Splitting 80/10/10 by episode...")
    random.seed(42)

    by_episode = defaultdict(list)
    for e in entries:
        key = (e["source"], e["episode"])
        by_episode[key].append(e)

    by_series = defaultdict(list)
    for key in by_episode:
        by_series[key[0]].append(key)

    train, val, test = [], [], []
    for series, episode_keys in by_series.items():
        random.shuffle(episode_keys)
        n = len(episode_keys)
        if n <= 2:
            for key in episode_keys:
                train.extend(by_episode[key])
        else:
            n_test = max(1, round(n * 0.10))
            n_val = max(1, round(n * 0.10))
            if n_test + n_val > n * 0.3:
                n_test = n_val = 1

            for key in episode_keys[:n_test]:
                test.extend(by_episode[key])
            for key in episode_keys[n_test:n_test + n_val]:
                val.extend(by_episode[key])
            for key in episode_keys[n_test + n_val:]:
                train.extend(by_episode[key])

    # Assign IDs
    for i, e in enumerate(train, 1):
        prefix = ''.join(w[0] for w in e["source"].split("_")[:3])
        e["id"] = f"{prefix}_{e['episode'].lower()}_{i:05d}"
    for i, e in enumerate(val, 1):
        prefix = ''.join(w[0] for w in e["source"].split("_")[:3])
        e["id"] = f"{prefix}_{e['episode'].lower()}_{i:05d}"
    for i, e in enumerate(test, 1):
        prefix = ''.join(w[0] for w in e["source"].split("_")[:3])
        e["id"] = f"{prefix}_{e['episode'].lower()}_{i:05d}"

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in [("train", train), ("val", val), ("test", test)]:
        with open(OUTPUT_DIR / f"{name}.json", "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    total = len(train) + len(val) + len(test)
    total_tokens = sum(len(e["tokens"]) for e in train + val + test)
    n_series = len(set(e["source"] for e in train + val + test))

    metadata = {
        "name": "poneglyph_v1",
        "splits": {"train": len(train), "val": len(val), "test": len(test), "total": total},
        "total_tokens": total_tokens,
        "num_series": n_series,
    }
    with open(OUTPUT_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"DATASET REBUILT")
    print(f"  Train: {len(train)} ({len(train)/total*100:.1f}%)")
    print(f"  Val:   {len(val)} ({len(val)/total*100:.1f}%)")
    print(f"  Test:  {len(test)} ({len(test)/total*100:.1f}%)")
    print(f"  Total: {total}")
    print(f"  Tokens: {total_tokens}")
    print(f"  Series: {n_series}")


if __name__ == "__main__":
    main()
