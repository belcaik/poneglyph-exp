#!/usr/bin/env python3
"""
Analyze annotation conventions across data sources to understand
stem-only vs morpheme-complete patterns.

Outputs a report showing:
- Per source: % of tokens that are stem-only (kanji surface + trailing okurigana in text)
- Top 30 examples of stem-only tokens per source
- Summary of which sources need normalization
"""

import json
import sys
from collections import defaultdict, Counter
from pathlib import Path

SPLITS_DIR = Path("data/splits_v6_no_matcha")


def is_hiragana(ch: str) -> bool:
    return '\u3040' <= ch <= '\u309f'


def is_katakana(ch: str) -> bool:
    return '\u30a0' <= ch <= '\u30ff'


def is_kanji(ch: str) -> bool:
    return '\u4e00' <= ch <= '\u9fff' or '\u3400' <= ch <= '\u4dbf'


def surface_ends_with_kanji(surface: str) -> bool:
    return len(surface) > 0 and is_kanji(surface[-1])


def surface_has_hiragana(surface: str) -> bool:
    return any(is_hiragana(c) for c in surface)


def get_trailing_hiragana(text: str, end_pos: int) -> str:
    """Get consecutive hiragana characters starting at end_pos."""
    trail = ""
    j = end_pos
    while j < len(text) and is_hiragana(text[j]):
        trail += text[j]
        j += 1
    return trail


def analyze_file(filepath: Path) -> list:
    with open(filepath) as f:
        return json.load(f)


def main():
    # Load all data
    all_data = []
    for split in ["train.json", "val.json", "test.json"]:
        filepath = SPLITS_DIR / split
        if filepath.exists():
            all_data.extend(analyze_file(filepath))

    print(f"Total sentences: {len(all_data)}")
    sources = Counter(d["source"] for d in all_data)
    for s, c in sources.most_common():
        print(f"  {s}: {c}")

    # Per-source analysis
    source_stats = defaultdict(lambda: {
        "total_tokens": 0,
        "kanji_only_surface": 0,  # surface has kanji, no hiragana
        "mixed_surface": 0,       # surface has both kanji and hiragana
        "stem_only_candidates": 0,  # kanji-ending surface + trailing hiragana in text
        "has_parens_in_text": 0,  # kahoku-style () markers
        "examples_stem_only": [],
        "examples_mixed": [],
    })

    for sent in all_data:
        src = sent["source"]
        text = sent["text"]
        pos = 0

        has_parens = "()" in text
        if has_parens:
            source_stats[src]["has_parens_in_text"] += 1

        for tok in sent["tokens"]:
            surface = tok["surface"]
            reading = tok["reading"]
            source_stats[src]["total_tokens"] += 1

            # Find surface position in text
            idx = text.find(surface, pos)
            if idx == -1:
                # Try from beginning (sometimes tokens aren't sequential)
                idx = text.find(surface)
            if idx == -1:
                continue
            end = idx + len(surface)

            has_kan = any(is_kanji(c) for c in surface)
            has_hira = any(is_hiragana(c) for c in surface)

            if has_kan and not has_hira:
                source_stats[src]["kanji_only_surface"] += 1
            elif has_kan and has_hira:
                source_stats[src]["mixed_surface"] += 1
                if len(source_stats[src]["examples_mixed"]) < 30:
                    source_stats[src]["examples_mixed"].append(
                        f"{surface}/{reading}"
                    )

            # Check for stem-only pattern: kanji-ending surface + trailing hiragana
            if surface_ends_with_kanji(surface) and end < len(text):
                next_ch = text[end]
                if is_hiragana(next_ch):
                    trail = get_trailing_hiragana(text, end)
                    source_stats[src]["stem_only_candidates"] += 1
                    if len(source_stats[src]["examples_stem_only"]) < 30:
                        ctx_start = max(0, idx - 3)
                        ctx_end = min(len(text), end + 10)
                        source_stats[src]["examples_stem_only"].append({
                            "surface": surface,
                            "reading": reading,
                            "trailing": trail,
                            "context": text[ctx_start:ctx_end],
                            "expanded": f"{surface}{trail}",
                        })
                # Also check for () marker (kahoku)
                elif next_ch == "(":
                    paren_end = text.find(")", end + 1)
                    if paren_end >= 0 and paren_end == end + 1:
                        # Empty () - kahoku pattern
                        after_paren = paren_end + 1
                        if after_paren < len(text) and is_hiragana(text[after_paren]):
                            trail = get_trailing_hiragana(text, after_paren)
                            source_stats[src]["stem_only_candidates"] += 1
                            if len(source_stats[src]["examples_stem_only"]) < 30:
                                ctx = text[max(0, idx-3):min(len(text), after_paren+10)]
                                source_stats[src]["examples_stem_only"].append({
                                    "surface": surface,
                                    "reading": reading,
                                    "trailing": trail,
                                    "context": ctx,
                                    "expanded": f"{surface}{trail}",
                                })

            pos = max(pos, end)

    # Print report
    print("\n" + "=" * 80)
    print("ANNOTATION CONVENTION ANALYSIS")
    print("=" * 80)

    for src in sorted(source_stats):
        s = source_stats[src]
        print(f"\n--- {src} ---")
        print(f"  Total tokens: {s['total_tokens']}")
        print(f"  Kanji-only surfaces: {s['kanji_only_surface']}")
        print(f"  Mixed kanji+hiragana surfaces: {s['mixed_surface']}")
        print(f"  Stem-only candidates (kanji end + trailing hira): {s['stem_only_candidates']}")
        print(f"  Sentences with () markers: {s['has_parens_in_text']}")

        if s["total_tokens"] > 0:
            stem_pct = 100 * s["stem_only_candidates"] / s["total_tokens"]
            mixed_pct = 100 * s["mixed_surface"] / s["total_tokens"]
            print(f"  Stem-only %: {stem_pct:.1f}%")
            print(f"  Morpheme-complete %: {mixed_pct:.1f}%")

        if s["examples_stem_only"]:
            print(f"\n  Top stem-only examples:")
            for ex in s["examples_stem_only"][:30]:
                print(f"    {ex['surface']}/{ex['reading']} + \"{ex['trailing']}\" "
                      f"-> {ex['expanded']}  (ctx: {ex['context']})")

        if s["examples_mixed"]:
            print(f"\n  Mixed kanji+hiragana surfaces:")
            for ex in s["examples_mixed"][:10]:
                print(f"    {ex}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nSources that need normalization (stem-only convention):")
    for src in sorted(source_stats):
        s = source_stats[src]
        if s["total_tokens"] > 0:
            stem_pct = 100 * s["stem_only_candidates"] / s["total_tokens"]
            mixed_pct = 100 * s["mixed_surface"] / s["total_tokens"]
            annotation = "STEM-ONLY" if mixed_pct < 1 else "MOSTLY STEM-ONLY"
            if mixed_pct > 5:
                annotation = "MIXED"
            print(f"  {src}: {annotation} "
                  f"(stem-candidates: {stem_pct:.1f}%, morpheme-complete: {mixed_pct:.1f}%)")

    print("\nNote: 'stem-only candidates' includes false positives where trailing")
    print("hiragana is actually a particle (は、が、を etc.), not okurigana.")
    print("True stem-only rate for verbs/adjectives is a subset of this number.")
    print("Kahoku uses () markers in text that need special handling.")


if __name__ == "__main__":
    main()
