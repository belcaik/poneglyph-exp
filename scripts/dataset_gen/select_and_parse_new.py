#!/usr/bin/env python3
"""Select diverse new series and parse their subtitles.

Strategy: pick ~150 series across categories, targeting modern,
dialogue-heavy shows. Parse and append to existing data.
"""

import json
import os
import random
import re
import sys
from pathlib import Path

# Import the parser from our existing script
sys.path.insert(0, str(Path(__file__).parent))
from parse_subtitles import (
    parse_subtitle_file, clean_text, contains_japanese,
    is_mostly_english, guess_episode
)

KITSUNEKKO = Path("/home/belcaik/kitsunekko/subtitles")


def make_short_name(dirname):
    """Create a short series name from directory name."""
    name = dirname.lower()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    # Truncate to reasonable length
    parts = name.split('_')
    if len(parts) > 4:
        parts = parts[:4]
    return '_'.join(parts)


def process_series(category, dirname):
    """Process all subtitle files for one series."""
    series_dir = KITSUNEKKO / category / dirname
    if not series_dir.exists():
        return []

    sub_files = []
    for ext in ('*.srt', '*.ass', '*.ssa', '*.vtt'):
        sub_files.extend(series_dir.glob(ext))
        sub_files.extend(series_dir.glob(f'*/{ext}'))

    sub_files = sorted(set(sub_files))
    short_name = make_short_name(dirname)

    episodes = {}
    for sf in sub_files:
        ep = guess_episode(sf.name)
        lines = parse_subtitle_file(sf)
        if not lines:
            continue
        if ep in episodes:
            if len(lines) > len(episodes[ep]["lines"]):
                episodes[ep] = {"file": str(sf), "lines": lines}
        else:
            episodes[ep] = {"file": str(sf), "lines": lines}

    results = []
    for ep in sorted(episodes.keys()):
        data = episodes[ep]
        results.append({
            "series": short_name,
            "series_full": dirname,
            "episode": ep,
            "source_file": data["file"],
            "lines": data["lines"]
        })

    return results


def main():
    # Load discovered series
    with open("data/dataset_gen/discovered_series.json") as f:
        all_discovered = json.load(f)

    # Load existing parsed data
    existing_path = Path("data/dataset_gen/parsed_subtitles.json")
    with open(existing_path) as f:
        existing_data = json.load(f)

    existing_series = {ep["series_full"] for ep in existing_data}
    print(f"Already parsed: {len(existing_series)} series, {len(existing_data)} episodes")

    # Filter to new series only
    new_series = [d for d in all_discovered if d["name"] not in existing_series]
    print(f"New series available: {len(new_series)}")

    # Selection strategy: pick diverse, dialogue-heavy shows
    # Prefer drama_tv (most natural dialogue), then anime_tv
    # Prefer medium-sized series (10-200 files — enough content, not too much noise)
    # Avoid massive long-runners (One Piece, Naruto) — too much action dialogue
    candidates = []
    for d in new_series:
        files = d["files"]
        est = d["est_lines"]
        # Skip too small (< 3 files) or too large (> 500 files)
        if files < 3 or files > 500:
            continue
        # Skip if estimated lines per file is very low (likely not Japanese)
        avg = est / files if files > 0 else 0
        if avg < 20:
            continue
        candidates.append(d)

    print(f"Candidates after size filter: {len(candidates)}")

    # Separate by category and select proportionally
    by_cat = {}
    for d in candidates:
        cat = d["category"]
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(d)

    # Target: ~150 new series
    # drama_tv: 60, anime_tv: 50, drama_movie: 25, anime_movie: 15
    targets = {
        "drama_tv": 60,
        "anime_tv": 50,
        "drama_movie": 25,
        "anime_movie": 15,
    }

    random.seed(42)
    selected = []
    for cat, target in targets.items():
        pool = by_cat.get(cat, [])
        # Sort by estimated lines (moderate first — not too huge, not too tiny)
        pool.sort(key=lambda d: abs(d["est_lines"] - 5000))
        # Take top candidates
        chosen = pool[:target]
        selected.extend(chosen)
        print(f"  {cat}: selected {len(chosen)}/{len(pool)} available")

    print(f"\nTotal new series to parse: {len(selected)}")

    # Parse all selected series
    new_episodes = []
    stats = {}

    for i, d in enumerate(selected):
        cat = d["category"]
        name = d["name"]
        print(f"  [{i+1}/{len(selected)}] {cat}/{name}...", end=" ", flush=True)

        episodes = process_series(cat, name)
        total_lines = sum(len(ep["lines"]) for ep in episodes)
        short = make_short_name(name)
        stats[short] = {"episodes": len(episodes), "lines": total_lines}
        print(f"{len(episodes)} eps, {total_lines} lines")
        new_episodes.extend(episodes)

    # Merge with existing
    all_episodes = existing_data + new_episodes

    # Save
    with open(existing_path, "w") as f:
        json.dump(all_episodes, f, ensure_ascii=False, indent=2)

    total_eps = len(all_episodes)
    total_lines = sum(len(ep["lines"]) for ep in all_episodes)
    new_lines = sum(len(ep["lines"]) for ep in new_episodes)
    all_series = set(ep["series"] for ep in all_episodes)

    print(f"\n{'='*60}")
    print(f"New: {len(new_episodes)} episodes, {new_lines:,} lines from {len(selected)} series")
    print(f"Total: {total_eps} episodes, {total_lines:,} lines from {len(all_series)} series")
    print(f"Saved to {existing_path}")

    # Show top new series by line count
    print(f"\nTop 20 new series:")
    for name, s in sorted(stats.items(), key=lambda x: -x[1]["lines"])[:20]:
        print(f"  {name}: {s['episodes']} eps, {s['lines']:,} lines")


if __name__ == "__main__":
    main()
