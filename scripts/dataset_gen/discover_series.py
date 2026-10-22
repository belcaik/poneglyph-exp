#!/usr/bin/env python3
"""Discover all kitsunekko series with Japanese subtitle files.

Scans all categories, checks for .srt/.ass/.vtt files containing Japanese text,
reports available series with file counts and estimated line counts.
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

KITSUNEKKO = Path("/home/belcaik/kitsunekko/subtitles")
CATEGORIES = ["drama_tv", "anime_tv", "drama_movie", "anime_movie"]

# Already parsed series (full dir names)
ALREADY_PARSED = {
    "Terrace House. Boys & Girls in the City",
    "Terrace House. Boys × Girls Next Door",
    "Terrace House. Aloha State",
    "Terrace House Opening New Doors",
    "Nigeru wa Haji da ga Yaku ni Tatsu",
    "Shinya Shokudou",
    "Shinya Shokudou. Tokyo Stories",
    "Unnatural",
    "Hanzawa Naoki",
    "Barakamon",
    "Shirokuma Cafe",
    "Nichijou",
    "Non Non Biyori",
    "Non Non Biyori. Nonstop",
    "Non Non Biyori. Repeat",
    "Hyouka",
    "Gin no Saji",
    "Gin no Saji 2",
    "Yuru Camp△",
    "Yuru Camp△ SEASON 2",
    "Yuru Camp△ SEASON 3",
    "K-ON!",
    "K-ON!!",
    "Flying Witch",
}


def has_japanese(filepath, sample_lines=30):
    """Quick check if a file contains Japanese characters."""
    try:
        for encoding in ['utf-8-sig', 'utf-8', 'shift_jis', 'euc-jp', 'cp932']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    sample = f.read(8000)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            return False

        jp_chars = sum(1 for c in sample if 0x3040 <= ord(c) <= 0x309F or
                       0x30A0 <= ord(c) <= 0x30FF or
                       0x4E00 <= ord(c) <= 0x9FFF)
        en_chars = sum(1 for c in sample if c.isascii() and c.isalpha())

        # Must have meaningful Japanese content
        return jp_chars > 20 and jp_chars > en_chars * 0.3
    except Exception:
        return False


def count_subtitle_lines(filepath):
    """Estimate number of subtitle lines in a file."""
    try:
        ext = filepath.suffix.lower()
        for encoding in ['utf-8-sig', 'utf-8', 'shift_jis', 'euc-jp', 'cp932']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            return 0

        if ext == '.srt':
            return len(re.findall(r'\d{2}:\d{2}:\d{2}', content)) // 2
        elif ext in ('.ass', '.ssa'):
            return content.count('Dialogue:')
        elif ext == '.vtt':
            return len(re.findall(r'\d{2}:\d{2}:\d{2}', content)) // 2
        return 0
    except Exception:
        return 0


def scan_series(category, series_name):
    """Scan a series directory for Japanese subtitle files."""
    series_dir = KITSUNEKKO / category / series_name

    sub_files = []
    for ext in ('*.srt', '*.ass', '*.ssa', '*.vtt'):
        sub_files.extend(series_dir.glob(ext))
        sub_files.extend(series_dir.glob(f'*/{ext}'))

    if not sub_files:
        return None

    # Quick check: does the first file contain Japanese?
    jp_files = []
    for sf in sub_files[:3]:  # Check first 3 files
        if has_japanese(sf):
            jp_files.append(sf)

    if not jp_files:
        return None

    # Count total files and estimate lines
    total_files = len(sub_files)
    est_lines = sum(count_subtitle_lines(sf) for sf in sub_files[:5])
    avg_lines_per_file = est_lines / min(5, len(sub_files))
    est_total_lines = int(avg_lines_per_file * total_files)

    return {
        "category": category,
        "name": series_name,
        "files": total_files,
        "est_lines": est_total_lines,
    }


def main():
    output_path = Path("data/dataset_gen/discovered_series.json")

    discovered = []
    total_scanned = 0

    for category in CATEGORIES:
        cat_dir = KITSUNEKKO / category
        if not cat_dir.exists():
            continue

        series_list = sorted(os.listdir(cat_dir))
        print(f"\nScanning {category}: {len(series_list)} series...")

        for i, series_name in enumerate(series_list):
            if series_name in ALREADY_PARSED:
                continue

            series_path = cat_dir / series_name
            if not series_path.is_dir():
                continue

            total_scanned += 1
            result = scan_series(category, series_name)
            if result:
                discovered.append(result)

            if (i + 1) % 500 == 0:
                print(f"  {i+1}/{len(series_list)} scanned, {len(discovered)} with JP subs so far")

        print(f"  Done: {len([d for d in discovered if d['category'] == category])} JP series found")

    # Sort by estimated lines (largest first)
    discovered.sort(key=lambda x: -x["est_lines"])

    # Save
    with open(output_path, "w") as f:
        json.dump(discovered, f, ensure_ascii=False, indent=2)

    total_est_lines = sum(d["est_lines"] for d in discovered)
    print(f"\n{'='*60}")
    print(f"Scanned: {total_scanned} series")
    print(f"Found: {len(discovered)} series with Japanese subtitles")
    print(f"Estimated total lines: {total_est_lines:,}")
    print(f"\nTop 30 by estimated lines:")
    for d in discovered[:30]:
        print(f"  {d['category']}/{d['name']}: ~{d['est_lines']:,} lines ({d['files']} files)")
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
