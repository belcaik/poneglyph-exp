#!/usr/bin/env python3
"""Fast dataset expansion — parse, filter, and prepare in one pass.

Avoids the huge parsed_subtitles.json bottleneck by streaming through
subtitle files and directly filtering to annotation-ready sentences.
"""

import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_subtitles import parse_subtitle_file, guess_episode
from filter_sentences import has_kanji, kanji_count, is_sentence_final, is_metadata_or_label

KITSUNEKKO = Path("/home/belcaik/kitsunekko/subtitles")
REPO_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "dataset_gen"
CATEGORIES = ["drama_tv", "anime_tv", "drama_movie", "anime_movie"]
SUB_EXTENSIONS = {".srt", ".ass", ".ssa", ".vtt"}
MIN_LEN = 5
MAX_LEN = 100


def make_short_name(dirname):
    name = dirname.lower()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return '_'.join(name.split('_')[:4])


def load_existing_texts():
    """Load all already-annotated text strings for dedup."""
    texts = set()
    for f in ["annotations_claude.json"]:
        path = DATA_DIR / f
        if path.exists():
            with open(path) as fp:
                for a in json.load(fp):
                    if a.get("annotations"):
                        texts.add(a["text"])
    for split in ["train", "val", "test"]:
        path = REPO_ROOT / "data" / "poneglyph_v1" / f"{split}.json"
        if path.exists():
            with open(path) as fp:
                for e in json.load(fp):
                    texts.add(e["text"])
    return texts


def get_already_parsed_files():
    """Get set of file paths already in parsed_subtitles.json."""
    path = DATA_DIR / "parsed_subtitles.json"
    parsed = set()
    if path.exists():
        try:
            with open(path) as f:
                for ep in json.load(f):
                    sf = ep.get("source_file", "")
                    if sf:
                        parsed.add(sf)
        except (json.JSONDecodeError, MemoryError):
            print("  Warning: parsed_subtitles.json is corrupt, ignoring")
    return parsed


def main():
    print("=" * 60)
    print("FAST DATASET EXPANSION")
    print("=" * 60)

    # Load existing state
    print("\n[1] Loading existing annotations...")
    existing_texts = load_existing_texts()
    print(f"  {len(existing_texts)} existing annotated texts")

    already_parsed = get_already_parsed_files()
    print(f"  {len(already_parsed)} files already parsed")

    # Discover ALL subtitle files
    print("\n[2] Discovering subtitle files...")
    all_files = []
    for category in CATEGORIES:
        cat_dir = KITSUNEKKO / category
        if not cat_dir.exists():
            continue
        for series_dir in sorted(cat_dir.iterdir()):
            if not series_dir.is_dir():
                continue
            for sf in series_dir.rglob("*"):
                if sf.suffix.lower() in SUB_EXTENSIONS:
                    if str(sf) not in already_parsed:
                        all_files.append({
                            "path": sf,
                            "category": category,
                            "series_dir": series_dir.name,
                        })

    print(f"  {len(all_files)} new files to process")

    # Shuffle for diversity — don't process alphabetically
    import random
    random.seed(42)
    random.shuffle(all_files)

    # Stream-process: parse → filter → collect
    # No intermediate JSON dump — keep only filtered sentences in memory
    print("\n[3] Parsing and filtering (streaming)...")
    new_sentences = []
    seen_normalized = set()
    series_counts = Counter()
    files_processed = 0
    files_with_content = 0
    total_lines = 0
    target_new = max(0, 20000 - len(existing_texts))
    max_per_series = min(300, int(target_new * 0.03))  # 3% cap = ~330 per series for 11K

    for finfo in all_files:
        sf = finfo["path"]
        series_name = make_short_name(finfo["series_dir"])
        episode = guess_episode(sf.name)

        lines = parse_subtitle_file(sf)
        files_processed += 1

        if not lines:
            continue

        files_with_content += 1
        total_lines += len(lines)

        for line in lines:
            text = line["text"]

            # Quick filters
            if text in existing_texts:
                continue
            if len(text) < MIN_LEN or len(text) > MAX_LEN:
                continue
            if not has_kanji(text):
                continue
            if is_metadata_or_label(text):
                continue
            if not is_sentence_final(text):
                continue

            # Dedup
            norm = re.sub(r'[。、！？\s　…「」『』（）\(\)]', '', text)
            if norm in seen_normalized:
                continue
            seen_normalized.add(norm)

            # Series cap
            if series_counts[series_name] >= max_per_series:
                continue

            series_counts[series_name] += 1
            new_sentences.append({
                "series": series_name,
                "episode": episode,
                "text": text,
                "char_count": len(text),
                "kanji_count": kanji_count(text),
            })

        # Progress
        if files_processed % 1000 == 0:
            print(f"  {files_processed}/{len(all_files)} files, "
                  f"{len(new_sentences)} new sentences, "
                  f"{total_lines} total lines")

        # Stop if we have enough
        if len(new_sentences) >= target_new:
            print(f"  Reached target of {target_new} new sentences!")
            break

    print(f"\n  Files processed: {files_processed}")
    print(f"  Files with content: {files_with_content}")
    print(f"  Total lines parsed: {total_lines}")
    print(f"  New sentences: {len(new_sentences)}")
    print(f"  Series: {len(series_counts)}")

    # Assign IDs
    start_id = len(existing_texts) + 1
    for i, s in enumerate(new_sentences):
        s["id"] = start_id + i

    # Save
    output = DATA_DIR / "new_filtered_sentences.json"
    with open(output, "w") as f:
        json.dump(new_sentences, f, ensure_ascii=False, indent=2)

    # Prepare annotation batches
    print(f"\n[4] Preparing annotation batches...")
    batch_size = 50
    n_batches = (len(new_sentences) + batch_size - 1) // batch_size
    for i in range(n_batches):
        batch = new_sentences[i * batch_size:(i + 1) * batch_size]
        with open(f"/tmp/dataset_inc_input_{i}.json", "w") as f:
            json.dump(batch, f, ensure_ascii=False)

    print(f"  {n_batches} batch files written")

    # Save progress
    progress = {
        "existing_annotated": len(existing_texts),
        "new_sentences": len(new_sentences),
        "files_processed": files_processed,
        "total_files": len(all_files),
        "annotation_batches": n_batches,
        "top_series": dict(series_counts.most_common(20)),
    }
    with open(DATA_DIR / "progress.json", "w") as f:
        json.dump(progress, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"READY FOR ANNOTATION")
    print(f"  Existing: {len(existing_texts)}")
    print(f"  New: {len(new_sentences)}")
    print(f"  Target total: {len(existing_texts) + len(new_sentences)}")
    print(f"  Batches: {n_batches}")
    print(f"\n  Top 10 new series:")
    for s, c in series_counts.most_common(10):
        print(f"    {s}: {c}")


if __name__ == "__main__":
    main()
