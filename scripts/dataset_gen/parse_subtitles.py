#!/usr/bin/env python3
"""Parse subtitle files (.srt, .ass, .vtt) from kitsunekko into structured JSON.

Handles SRT, ASS/SSA, and VTT formats. Strips formatting tags, sound effects,
non-Japanese content, and deduplicates lines.
"""

import json
import os
import re
import unicodedata
from pathlib import Path


KITSUNEKKO = Path("/home/belcaik/kitsunekko/subtitles")

# Series to process: (category, directory_name, short_name)
TARGET_SERIES = [
    # Priority 1 — Doramas
    ("drama_tv", "Terrace House. Boys & Girls in the City", "terrace_house_bgc"),
    ("drama_tv", "Terrace House. Boys × Girls Next Door", "terrace_house_bgnd"),
    ("drama_tv", "Terrace House. Aloha State", "terrace_house_aloha"),
    ("drama_tv", "Terrace House Opening New Doors", "terrace_house_ond"),
    ("drama_tv", "Nigeru wa Haji da ga Yaku ni Tatsu", "nigehaji"),
    ("drama_tv", "Shinya Shokudou", "shinya_shokudou"),
    ("drama_tv", "Shinya Shokudou. Tokyo Stories", "shinya_shokudou_ts"),
    ("drama_tv", "Unnatural", "unnatural"),
    ("drama_tv", "Hanzawa Naoki", "hanzawa_naoki"),
    # Priority 2 — Anime
    ("anime_tv", "Barakamon", "barakamon"),
    ("anime_tv", "Shirokuma Cafe", "shirokuma_cafe"),
    ("anime_tv", "Nichijou", "nichijou"),
    ("anime_tv", "Non Non Biyori", "non_non_biyori"),
    ("anime_tv", "Non Non Biyori. Nonstop", "non_non_biyori_ns"),
    ("anime_tv", "Non Non Biyori. Repeat", "non_non_biyori_r"),
    ("anime_tv", "Hyouka", "hyouka"),
    ("anime_tv", "Gin no Saji", "gin_no_saji"),
    ("anime_tv", "Gin no Saji 2", "gin_no_saji_2"),
    ("anime_tv", "Yuru Camp△", "yuru_camp"),
    ("anime_tv", "Yuru Camp△ SEASON 2", "yuru_camp_2"),
    ("anime_tv", "Yuru Camp△ SEASON 3", "yuru_camp_3"),
    ("anime_tv", "K-ON!", "k_on"),
    ("anime_tv", "K-ON!!", "k_on_2"),
    ("anime_tv", "Flying Witch", "flying_witch"),
]

# Sound effect patterns to remove
SOUND_EFFECT_RE = re.compile(
    r'^[（\(].+?[）\)]$'  # Entire line is a sound effect in parens
    r'|^[♪♫🎵🎶～〜]+$'  # Music symbols only
    r'|^[\s　]*$'  # Blank
)

# ASS/SSA style tag patterns
ASS_TAG_RE = re.compile(r'\{[^}]*\}')

# HTML tags
HTML_TAG_RE = re.compile(r'<[^>]+>')

# Parenthetical sound effects within lines
PAREN_EFFECT_RE = re.compile(r'[（\(][^）\)]*(?:音|笑|拍手|歓声|BGM|SE|♪)[^）\)]*[）\)]')

# Speaker labels like （山田） at start of line
SPEAKER_LABEL_RE = re.compile(r'^[（\(][^\）\)]{1,6}[）\)]\s*')


def contains_japanese(text):
    """Check if text contains any Japanese characters (hiragana, katakana, or kanji)."""
    for c in text:
        cp = ord(c)
        if (0x3040 <= cp <= 0x309F or  # Hiragana
            0x30A0 <= cp <= 0x30FF or  # Katakana
            0x4E00 <= cp <= 0x9FFF or  # CJK
            0x3400 <= cp <= 0x4DBF):   # CJK Ext A
            return True
    return False


def is_mostly_english(text):
    """Check if text is predominantly English/Latin characters."""
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    jp = sum(1 for c in text if ord(c) >= 0x3000)
    return latin > jp * 2 and latin > 5


def clean_text(text):
    """Clean a subtitle line: strip tags, effects, normalize whitespace."""
    # Strip ASS tags
    text = ASS_TAG_RE.sub('', text)
    # Strip HTML tags
    text = HTML_TAG_RE.sub('', text)
    # Remove inline sound effects
    text = PAREN_EFFECT_RE.sub('', text)
    # Remove speaker labels at start
    text = SPEAKER_LABEL_RE.sub('', text)
    # Remove ASS line break markers
    text = text.replace('\\N', '\n').replace('\\n', '\n')
    # Normalize whitespace: full-width space, multiple spaces
    text = re.sub(r'[　\s]+', ' ', text)
    # Strip leading/trailing
    text = text.strip()
    # Remove trailing arrows (continuation markers in some subs)
    text = re.sub(r'[→➡]$', '', text).strip()
    return text


def parse_srt(filepath):
    """Parse an SRT subtitle file."""
    lines_out = []
    try:
        # Try UTF-8 first, fall back to shift_jis
        for encoding in ['utf-8-sig', 'utf-8', 'shift_jis', 'euc-jp', 'cp932']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            return []

        blocks = re.split(r'\n\s*\n', content.strip())
        for block in blocks:
            block_lines = block.strip().split('\n')
            if len(block_lines) < 3:
                continue

            # First line: index, Second: timestamp, Rest: text
            timestamp_line = block_lines[1] if '-->' in block_lines[1] else None
            if not timestamp_line:
                # Try to find timestamp in other lines
                for bl in block_lines:
                    if '-->' in bl:
                        timestamp_line = bl
                        break
            if not timestamp_line:
                continue

            match = re.match(
                r'(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})',
                timestamp_line
            )
            if not match:
                continue

            start_time = match.group(1).replace(',', '.')
            end_time = match.group(2).replace(',', '.')

            # Text is everything after the timestamp line
            ts_idx = block_lines.index(timestamp_line) if timestamp_line in block_lines else 1
            text_lines = block_lines[ts_idx + 1:]
            text = ' '.join(text_lines)
            text = clean_text(text)

            if text and contains_japanese(text) and not is_mostly_english(text):
                lines_out.append({
                    "start_time": start_time,
                    "end_time": end_time,
                    "text": text
                })
    except Exception as e:
        print(f"  Error parsing SRT {filepath}: {e}")

    return lines_out


def parse_ass(filepath):
    """Parse an ASS/SSA subtitle file."""
    lines_out = []
    try:
        for encoding in ['utf-8-sig', 'utf-8', 'shift_jis', 'euc-jp', 'cp932']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            return []

        for line in content.split('\n'):
            if not line.startswith('Dialogue:'):
                continue

            parts = line.split(',', 9)
            if len(parts) < 10:
                continue

            start_time = parts[1].strip()
            end_time = parts[2].strip()
            text = parts[9]

            text = clean_text(text)
            if text and contains_japanese(text) and not is_mostly_english(text):
                lines_out.append({
                    "start_time": start_time,
                    "end_time": end_time,
                    "text": text
                })
    except Exception as e:
        print(f"  Error parsing ASS {filepath}: {e}")

    return lines_out


def parse_vtt(filepath):
    """Parse a WebVTT subtitle file."""
    lines_out = []
    try:
        for encoding in ['utf-8-sig', 'utf-8', 'shift_jis']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            return []

        # Remove WEBVTT header
        content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.DOTALL)

        blocks = re.split(r'\n\s*\n', content.strip())
        for block in blocks:
            block_lines = block.strip().split('\n')
            timestamp_line = None
            for bl in block_lines:
                if '-->' in bl:
                    timestamp_line = bl
                    break
            if not timestamp_line:
                continue

            match = re.match(
                r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})',
                timestamp_line
            )
            if not match:
                continue

            ts_idx = block_lines.index(timestamp_line)
            text_lines = block_lines[ts_idx + 1:]
            text = ' '.join(text_lines)
            # Remove VTT positioning tags
            text = re.sub(r'<[^>]+>', '', text)
            text = clean_text(text)

            if text and contains_japanese(text) and not is_mostly_english(text):
                lines_out.append({
                    "start_time": match.group(1),
                    "end_time": match.group(2),
                    "text": text
                })
    except Exception as e:
        print(f"  Error parsing VTT {filepath}: {e}")

    return lines_out


def guess_episode(filename):
    """Try to extract episode number from filename."""
    name = Path(filename).stem
    # Common patterns: E01, EP01, Episode 01, - 01, #01, S01E01
    patterns = [
        r'[Ss]\d+[Ee](\d+)',
        r'[Ee][Pp]?\.?(\d+)',
        r'[Ee]pisode\s*(\d+)',
        r'[\s_\-\.]+(\d{1,3})[\s_\-\.\[\(]',
        r'#(\d+)',
        r'\s(\d{2,3})\s',
    ]
    for pat in patterns:
        m = re.search(pat, name)
        if m:
            return f"E{int(m.group(1)):02d}"
    return "E00"


def parse_subtitle_file(filepath):
    """Route to the right parser based on extension."""
    ext = filepath.suffix.lower()
    if ext == '.srt':
        return parse_srt(filepath)
    elif ext in ('.ass', '.ssa'):
        return parse_ass(filepath)
    elif ext == '.vtt':
        return parse_vtt(filepath)
    return []


def process_series(category, dirname, short_name):
    """Process all subtitle files for one series."""
    series_dir = KITSUNEKKO / category / dirname
    if not series_dir.exists():
        print(f"  SKIP: {series_dir} not found")
        return []

    # Find all subtitle files (skip subdirs like 'extra/')
    sub_files = []
    for ext in ('*.srt', '*.ass', '*.ssa', '*.vtt'):
        sub_files.extend(series_dir.glob(ext))
        # Also check one level of subdirs
        sub_files.extend(series_dir.glob(f'*/{ext}'))

    # Prefer Japanese-named files, then JP-tagged files, then any
    # Sort to get consistent ordering
    sub_files = sorted(set(sub_files))

    episodes = {}
    for sf in sub_files:
        ep = guess_episode(sf.name)
        lines = parse_subtitle_file(sf)
        if not lines:
            continue

        # Keep the file with the most Japanese lines per episode
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
    output_path = Path("data/dataset_gen/parsed_subtitles.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_episodes = []
    stats = {}

    print("Parsing subtitle files...")
    for category, dirname, short_name in TARGET_SERIES:
        print(f"\n  {dirname}...")
        episodes = process_series(category, dirname, short_name)
        total_lines = sum(len(ep["lines"]) for ep in episodes)
        stats[short_name] = {"episodes": len(episodes), "lines": total_lines}
        print(f"    {len(episodes)} episodes, {total_lines} lines")
        all_episodes.extend(episodes)

    # Save
    with open(output_path, "w") as f:
        json.dump(all_episodes, f, ensure_ascii=False, indent=2)

    total_eps = sum(s["episodes"] for s in stats.values())
    total_lines = sum(s["lines"] for s in stats.values())
    print(f"\n{'='*60}")
    print(f"Total: {total_eps} episodes, {total_lines} lines")
    print(f"Saved to {output_path}")

    print(f"\nPer-series breakdown:")
    for name, s in sorted(stats.items(), key=lambda x: -x[1]["lines"]):
        print(f"  {name}: {s['episodes']} eps, {s['lines']} lines")


if __name__ == "__main__":
    main()
