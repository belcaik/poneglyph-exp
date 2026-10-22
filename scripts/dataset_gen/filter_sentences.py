#!/usr/bin/env python3
"""Filter parsed subtitle lines into high-quality sentences for annotation.

Selects kanji-containing, grammatically complete sentences with diversity
sampling across series. Target: 3000 sentences.
"""

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

TARGET_COUNT = 15000
MIN_LEN = 5
MAX_LEN = 100
SIMILARITY_THRESHOLD = 0.8


def is_kanji(c):
    cp = ord(c)
    return 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF


def kanji_count(text):
    return sum(1 for c in text if is_kanji(c))


def has_kanji(text):
    return any(is_kanji(c) for c in text)


def is_sentence_final(text):
    """Check if text ends with a sentence-final form."""
    text = text.rstrip()
    # Explicit punctuation
    if text and text[-1] in '。？！?!…':
        return True
    # Common verb/copula endings
    endings = [
        'た', 'だ', 'です', 'ます', 'ました', 'ません', 'する', 'なる',
        'ない', 'ある', 'いる', 'れる', 'せる', 'ける', 'げる', 'べる',
        'める', 'ねる', 'てる', 'でる', 'よ', 'ね', 'な', 'さ', 'わ',
        'ぞ', 'かな', 'のか', 'んだ', 'のだ', 'のです', 'んです',
        'だろう', 'でしょう', 'かもしれない', 'ください', 'くれ',
        'なさい', 'ましょう', 'よう', 'たい', 'みたい',
    ]
    for e in sorted(endings, key=len, reverse=True):
        if text.endswith(e):
            return True
    return False


def char_overlap(a, b):
    """Calculate character-level Jaccard similarity."""
    set_a = set(a)
    set_b = set(b)
    if not set_a or not set_b:
        return 0
    return len(set_a & set_b) / len(set_a | set_b)


def is_metadata_or_label(text):
    """Check if line is metadata, speaker label, or structural."""
    # Pure speaker label: just a name in brackets
    if re.match(r'^[「『【〈（\(]?[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]{1,4}[」』】〉）\)]?$', text):
        return True
    # Episode/title markers
    if re.match(r'^(第.+話|#\d+|エピソード|Episode)', text):
        return True
    # Timestamps or structural markers
    if re.match(r'^[\d:]+$', text):
        return True
    return False


def deduplicate(sentences, threshold=SIMILARITY_THRESHOLD):
    """Remove near-duplicate sentences."""
    result = []
    seen_texts = set()
    seen_normalized = set()

    for sent in sentences:
        text = sent["text"]
        # Exact dedup
        if text in seen_texts:
            continue
        # Normalized dedup (ignore punctuation/whitespace)
        normalized = re.sub(r'[。、！？\s　…「」『』（）\(\)]', '', text)
        if normalized in seen_normalized:
            continue
        # Jaccard similarity check against recent entries
        is_dup = False
        for prev in result[-200:]:  # Only check recent for speed
            if char_overlap(text, prev["text"]) > threshold:
                is_dup = True
                break
        if is_dup:
            continue

        seen_texts.add(text)
        seen_normalized.add(normalized)
        result.append(sent)

    return result


def main():
    input_path = Path("data/dataset_gen/parsed_subtitles.json")
    output_path = Path("data/dataset_gen/filtered_sentences.json")

    print("Loading parsed subtitles...")
    with open(input_path) as f:
        episodes = json.load(f)

    # Flatten to individual lines with metadata
    all_lines = []
    for ep in episodes:
        for line in ep["lines"]:
            all_lines.append({
                "series": ep["series"],
                "episode": ep["episode"],
                "text": line["text"],
            })

    print(f"Total lines: {len(all_lines)}")

    # Step 1: Basic filtering
    filtered = []
    reject_counts = Counter()

    for line in all_lines:
        text = line["text"]

        if len(text) < MIN_LEN:
            reject_counts["too_short"] += 1
            continue
        if len(text) > MAX_LEN:
            reject_counts["too_long"] += 1
            continue
        if not has_kanji(text):
            reject_counts["no_kanji"] += 1
            continue
        if is_metadata_or_label(text):
            reject_counts["metadata"] += 1
            continue
        if not is_sentence_final(text):
            reject_counts["not_sentence"] += 1
            continue

        kc = kanji_count(text)
        filtered.append({
            "series": line["series"],
            "episode": line["episode"],
            "text": text,
            "char_count": len(text),
            "kanji_count": kc,
        })

    print(f"\nAfter basic filtering: {len(filtered)}")
    print("Rejection reasons:")
    for reason, count in reject_counts.most_common():
        print(f"  {reason}: {count}")

    # Step 2: Deduplicate
    random.seed(42)
    random.shuffle(filtered)
    deduped = deduplicate(filtered)
    print(f"\nAfter deduplication: {len(deduped)}")

    # Step 3: Per-series stats
    series_counts = Counter(s["series"] for s in deduped)
    print(f"\nPer-series availability:")
    for series, count in series_counts.most_common():
        print(f"  {series}: {count}")

    # Step 4: Diversity sampling
    # Allocate proportionally to available sentences per series, with a floor
    total_available = len(deduped)
    if total_available <= TARGET_COUNT:
        selected = deduped
        print(f"\nAll {len(selected)} sentences selected (below target)")
    else:
        # Group by series
        by_series = defaultdict(list)
        for s in deduped:
            by_series[s["series"]].append(s)

        # Proportional allocation with minimum 20 per series
        n_series = len(by_series)
        min_per_series = min(20, TARGET_COUNT // n_series)
        remaining = TARGET_COUNT - min_per_series * n_series

        allocations = {}
        for series in by_series:
            allocations[series] = min_per_series

        # Distribute remaining proportionally, cap at 20% of target
        max_per_series = TARGET_COUNT // 5
        for series in by_series:
            available = len(by_series[series]) - min_per_series
            denom = total_available - min_per_series * n_series
            proportion = available / denom if denom > 0 else 0
            extra = int(remaining * proportion)
            allocations[series] = min(allocations[series] + extra, max_per_series)

        # Select with length diversity: 1/3 short (<20), 1/3 medium (20-40), 1/3 long (>40)
        selected = []
        for series, sents in by_series.items():
            target = min(allocations.get(series, 0), len(sents))
            short = [s for s in sents if s["char_count"] < 20]
            medium = [s for s in sents if 20 <= s["char_count"] <= 40]
            long_ = [s for s in sents if s["char_count"] > 40]

            per_bucket = target // 3
            remainder = target - per_bucket * 3

            random.shuffle(short)
            random.shuffle(medium)
            random.shuffle(long_)

            chosen = []
            chosen.extend(short[:per_bucket + (1 if remainder > 0 else 0)])
            chosen.extend(medium[:per_bucket + (1 if remainder > 1 else 0)])
            chosen.extend(long_[:per_bucket])

            # Fill any shortfall from the largest bucket
            deficit = target - len(chosen)
            if deficit > 0:
                pool = [s for s in sents if s not in chosen]
                random.shuffle(pool)
                chosen.extend(pool[:deficit])

            selected.extend(chosen[:target])

        random.shuffle(selected)

    # Assign IDs
    for i, s in enumerate(selected, 1):
        s["id"] = i

    print(f"\nFinal selection: {len(selected)} sentences")

    # Final stats
    series_final = Counter(s["series"] for s in selected)
    print(f"\nFinal per-series:")
    for series, count in series_final.most_common():
        print(f"  {series}: {count}")

    kanji_densities = [s["kanji_count"] / s["char_count"] for s in selected]
    avg_density = sum(kanji_densities) / len(kanji_densities)
    avg_len = sum(s["char_count"] for s in selected) / len(selected)
    avg_kanji = sum(s["kanji_count"] for s in selected) / len(selected)
    print(f"\nAvg char count: {avg_len:.1f}")
    print(f"Avg kanji count: {avg_kanji:.1f}")
    print(f"Avg kanji density: {avg_density:.2%}")

    # Save
    with open(output_path, "w") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
