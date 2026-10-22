#!/usr/bin/env python3
"""Incremental dataset scaling pipeline.

Tracks progress, discovers new files, parses, filters, and prepares
for annotation — all resumable and incremental.
"""

import hashlib
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_subtitles import (
    parse_subtitle_file, clean_text, contains_japanese,
    is_mostly_english, guess_episode
)
from filter_sentences import (
    has_kanji, kanji_count, is_sentence_final, is_metadata_or_label,
    char_overlap, MIN_LEN, MAX_LEN
)

KITSUNEKKO = Path("/home/belcaik/kitsunekko/subtitles")
DATA_DIR = Path("data/dataset_gen")
PROGRESS_FILE = DATA_DIR / "progress.json"
CATEGORIES = ["drama_tv", "anime_tv", "drama_movie", "anime_movie", "unsorted"]
SUB_EXTENSIONS = {".srt", ".ass", ".ssa", ".vtt"}


def text_hash(text):
    return hashlib.md5(text.encode()).hexdigest()[:16]


def make_short_name(dirname):
    name = dirname.lower()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    parts = name.split('_')
    return '_'.join(parts[:4])


# ──────────────────────────────────────────────────────────────
# Step 1: Bootstrap progress.json
# ──────────────────────────────────────────────────────────────

def bootstrap_progress():
    """Build progress.json from existing data."""
    progress = {"parsed_files": {}, "annotated_texts": set(), "stats": {}}

    # Load existing parsed subtitles
    parsed_path = DATA_DIR / "parsed_subtitles.json"
    if parsed_path.exists():
        with open(parsed_path) as f:
            episodes = json.load(f)
        for ep in episodes:
            sf = ep.get("source_file", "")
            if sf:
                progress["parsed_files"][sf] = {
                    "lines": len(ep.get("lines", [])),
                    "series": ep.get("series", ""),
                }
        print(f"  Parsed files: {len(progress['parsed_files'])}")

    # Load existing annotations (text-based dedup)
    for annot_file in ["annotations_claude.json"]:
        path = DATA_DIR / annot_file
        if path.exists():
            with open(path) as f:
                for a in json.load(f):
                    if not a.get("parse_failure") and a.get("annotations"):
                        progress["annotated_texts"].add(a["text"])
    print(f"  Annotated texts: {len(progress['annotated_texts'])}")

    # Also check assembled dataset
    for split in ["train", "val", "test"]:
        path = Path("data/poneglyph_v1") / f"{split}.json"
        if path.exists():
            with open(path) as f:
                for e in json.load(f):
                    progress["annotated_texts"].add(e["text"])

    print(f"  Total unique annotated: {len(progress['annotated_texts'])}")
    return progress


# ──────────────────────────────────────────────────────────────
# Step 2: Discover unparsed files
# ──────────────────────────────────────────────────────────────

def discover_new_files(progress):
    """Find all subtitle files not yet parsed."""
    parsed_set = set(progress["parsed_files"].keys())
    new_files = []

    for category in CATEGORIES:
        cat_dir = KITSUNEKKO / category
        if not cat_dir.exists():
            continue
        for series_dir in sorted(cat_dir.iterdir()):
            if not series_dir.is_dir():
                continue
            for sf in series_dir.rglob("*"):
                if sf.suffix.lower() in SUB_EXTENSIONS and str(sf) not in parsed_set:
                    new_files.append({
                        "path": str(sf),
                        "category": category,
                        "series": series_dir.name,
                    })

    # Group by series
    by_series = defaultdict(list)
    for f in new_files:
        by_series[f["series"]].append(f)

    print(f"  New files: {len(new_files)} from {len(by_series)} series")
    return new_files


# ──────────────────────────────────────────────────────────────
# Step 3: Parse new files
# ──────────────────────────────────────────────────────────────

def parse_new_files(new_files, progress, batch_size=200):
    """Parse new subtitle files in batches, save progress."""
    parsed_path = DATA_DIR / "parsed_subtitles.json"
    existing = []
    if parsed_path.exists():
        with open(parsed_path) as f:
            existing = json.load(f)

    total_new_lines = 0
    processed = 0

    for i in range(0, len(new_files), batch_size):
        batch = new_files[i:i + batch_size]
        batch_episodes = []

        for finfo in batch:
            sf = Path(finfo["path"])
            lines = parse_subtitle_file(sf)
            if not lines:
                progress["parsed_files"][str(sf)] = {"lines": 0, "series": ""}
                continue

            short_name = make_short_name(finfo["series"])
            ep = guess_episode(sf.name)

            batch_episodes.append({
                "series": short_name,
                "series_full": finfo["series"],
                "episode": ep,
                "source_file": str(sf),
                "lines": lines,
            })
            progress["parsed_files"][str(sf)] = {
                "lines": len(lines),
                "series": short_name,
            }
            total_new_lines += len(lines)

        existing.extend(batch_episodes)
        processed += len(batch)

        # Save checkpoint
        with open(parsed_path, "w") as f:
            json.dump(existing, f, ensure_ascii=False)

        print(f"  Parsed {processed}/{len(new_files)} files, "
              f"{total_new_lines} new lines, {len(existing)} total episodes")

    return total_new_lines


# ──────────────────────────────────────────────────────────────
# Step 4: Filter new sentences
# ──────────────────────────────────────────────────────────────

def filter_new_sentences(progress, target=20000):
    """Filter sentences from parsed data, excluding already-annotated ones."""
    parsed_path = DATA_DIR / "parsed_subtitles.json"
    with open(parsed_path) as f:
        episodes = json.load(f)

    annotated_texts = progress["annotated_texts"]
    existing_count = len(annotated_texts)

    # Flatten all lines
    all_lines = []
    for ep in episodes:
        for line in ep.get("lines", []):
            all_lines.append({
                "series": ep["series"],
                "episode": ep.get("episode", "E00"),
                "text": line["text"],
            })

    print(f"  Total lines: {len(all_lines)}")

    # Basic filtering
    filtered = []
    for line in all_lines:
        text = line["text"]
        if text in annotated_texts:
            continue
        if len(text) < MIN_LEN or len(text) > MAX_LEN:
            continue
        if not has_kanji(text):
            continue
        if is_metadata_or_label(text):
            continue
        if not is_sentence_final(text):
            continue
        filtered.append({
            "series": line["series"],
            "episode": line["episode"],
            "text": text,
            "char_count": len(text),
            "kanji_count": kanji_count(text),
        })

    print(f"  After basic filter (excl. already annotated): {len(filtered)}")

    # Dedup by normalized text
    seen = set()
    deduped = []
    for s in filtered:
        norm = re.sub(r'[。、！？\s　…「」『』（）\(\)]', '', s["text"])
        if norm not in seen:
            seen.add(norm)
            deduped.append(s)

    print(f"  After dedup: {len(deduped)}")

    # Cap per series at 15%
    needed = max(0, target - existing_count)
    max_per_series = int(needed * 0.15) if needed > 0 else 500

    import random
    random.seed(42)
    random.shuffle(deduped)

    by_series = defaultdict(list)
    for s in deduped:
        by_series[s["series"]].append(s)

    selected = []
    for series, sents in by_series.items():
        selected.extend(sents[:max_per_series])

    random.shuffle(selected)
    selected = selected[:needed]

    # Assign IDs
    start_id = existing_count + 1
    for i, s in enumerate(selected):
        s["id"] = start_id + i

    output_path = DATA_DIR / "new_filtered_sentences.json"
    with open(output_path, "w") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)

    print(f"  Selected {len(selected)} new sentences for annotation")
    print(f"  Target: {target}, existing: {existing_count}, needed: {needed}")

    # Series distribution
    series_counts = Counter(s["series"] for s in selected)
    print(f"  Top 10 new series:")
    for s, c in series_counts.most_common(10):
        print(f"    {s}: {c}")

    return selected


# ──────────────────────────────────────────────────────────────
# Step 5: Prepare annotation batches
# ──────────────────────────────────────────────────────────────

def prepare_annotation_batches(sentences, batch_size=50):
    """Write batch files for Claude subagent annotation."""
    n_batches = (len(sentences) + batch_size - 1) // batch_size
    for i in range(n_batches):
        batch = sentences[i * batch_size:(i + 1) * batch_size]
        with open(f"/tmp/dataset_inc_input_{i}.json", "w") as f:
            json.dump(batch, f, ensure_ascii=False)
    print(f"  Wrote {n_batches} batch files to /tmp/dataset_inc_input_*.json")
    return n_batches


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("INCREMENTAL DATASET PIPELINE")
    print("=" * 60)

    # Step 1: Bootstrap
    print("\n[Step 1] Bootstrapping progress from existing data...")
    progress = bootstrap_progress()

    # Step 2: Discover
    print("\n[Step 2] Discovering unparsed subtitle files...")
    new_files = discover_new_files(progress)

    if not new_files:
        print("  No new files to parse!")
    else:
        # Step 3: Parse
        print(f"\n[Step 3] Parsing {len(new_files)} new files...")
        new_lines = parse_new_files(new_files, progress, batch_size=200)
        print(f"  Done! {new_lines} new lines extracted")

    # Step 4: Filter
    print("\n[Step 4] Filtering new sentences...")
    new_sentences = filter_new_sentences(progress, target=20000)

    if not new_sentences:
        print("  No new sentences to annotate!")
        return

    # Step 5: Prepare batches
    print(f"\n[Step 5] Preparing {len(new_sentences)} sentences for annotation...")
    n_batches = prepare_annotation_batches(new_sentences, batch_size=50)

    # Save progress
    save_progress = {
        "stats": {
            "total_files_parsed": len(progress["parsed_files"]),
            "total_annotated": len(progress["annotated_texts"]),
            "new_sentences_for_annotation": len(new_sentences),
            "annotation_batches": n_batches,
            "last_updated": datetime.now().isoformat(),
        }
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(save_progress, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"READY FOR ANNOTATION")
    print(f"  Existing annotated: {len(progress['annotated_texts'])}")
    print(f"  New to annotate: {len(new_sentences)}")
    print(f"  Batches: {n_batches} (50 sentences each)")
    print(f"  After annotation: ~{len(progress['annotated_texts']) + len(new_sentences)} total")
    print(f"\nLaunch Claude subagents for batches 0-{n_batches-1}:")
    print(f"  Input: /tmp/dataset_inc_input_{{0..{n_batches-1}}}.json")
    print(f"  Output: /tmp/dataset_inc_batch_{{0..{n_batches-1}}}.json")
    print(f"  Prompt: /tmp/dataset_claude_prompt.txt")


if __name__ == "__main__":
    main()
