#!/usr/bin/env python3
"""Step 1: Select 100 benchmark sentences from test data.

Selects 20 sentences per source, prioritizing diversity of phenomena:
- Compound nouns
- Verb chains with auxiliaries
- Proper nouns
- Numbers with counters
- Mix of lengths
"""

import json
import re
from pathlib import Path
from collections import Counter


def contains_kanji(text):
    return any(0x4E00 <= ord(c) <= 0x9FFF or 0x3400 <= ord(c) <= 0x4DBF for c in text)


def analyze_phenomena(sentence):
    """Analyze a sentence for interesting phenomena."""
    text = sentence["text"]
    tokens = sentence["tokens"]
    phenomena = set()
    scores = 0

    for token in tokens:
        surface = token["surface"]
        reading = token["reading"]

        # Compound noun: multi-kanji surface >= 3 chars
        kanji_count = sum(1 for c in surface if 0x4E00 <= ord(c) <= 0x9FFF)
        if kanji_count >= 3:
            phenomena.add("compound_noun")
            scores += 2

        # Verb chain: surface contains て/で + more chars, or ends with auxiliary patterns
        verb_patterns = ["ている", "ていた", "ていました", "てしまった", "てしまう",
                         "てくれ", "てもらう", "ていく", "てくる", "てみ",
                         "ている", "れている", "させ", "られ", "たい",
                         "ません", "ました", "なかった", "なくなっ"]
        for pat in verb_patterns:
            if pat in surface and len(surface) > len(pat) + 1 and contains_kanji(surface):
                phenomena.add("verb_chain")
                scores += 2
                break

        # Proper noun heuristic: single/double kanji that looks like a name
        # (hard to detect without context, use surface length and common patterns)
        if re.match(r'^[一-龯]{2,4}$', surface) and reading and len(reading) <= 6:
            # Could be a proper noun — give partial score
            scores += 0.5

        # Number + counter
        if re.match(r'^\d+[一-龯]', surface) or re.match(r'^[一二三四五六七八九十百千万億兆]+[人日月年回個本枚台件]', surface):
            phenomena.add("counter")
            scores += 3  # rarer, more valuable

        # Mixed kanji-hiragana
        has_kanji_char = any(0x4E00 <= ord(c) <= 0x9FFF for c in surface)
        has_hira_char = any(0x3040 <= ord(c) <= 0x309F for c in surface)
        if has_kanji_char and has_hira_char and len(surface) >= 3:
            phenomena.add("mixed_word")
            scores += 1

        # Long verb form (4+ chars with kanji)
        if has_kanji_char and has_hira_char and len(surface) >= 4:
            phenomena.add("long_form")
            scores += 1

    # Length diversity scoring
    text_len = len(text)
    if text_len >= 60:
        phenomena.add("long_sentence")
        scores += 1
    elif text_len <= 15:
        phenomena.add("short_sentence")
        scores += 1

    # Multiple tokens (more complex)
    if len(tokens) >= 5:
        scores += 1
    if len(tokens) >= 8:
        scores += 1

    return phenomena, scores


def select_sentences(test_data, per_source=20):
    """Select benchmark sentences prioritizing phenomenon diversity."""
    # Group by source
    by_source = {}
    for sent in test_data:
        src = sent["source"]
        if src not in by_source:
            by_source[src] = []
        by_source[src].append(sent)

    selected = []
    stats = {}

    for source, sentences in sorted(by_source.items()):
        # Analyze all sentences
        scored = []
        for sent in sentences:
            phenomena, score = analyze_phenomena(sent)
            scored.append((score, phenomena, sent))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Select top N, but ensure length diversity
        chosen = []
        short_count = 0
        long_count = 0
        medium_count = 0

        for score, phenomena, sent in scored:
            if len(chosen) >= per_source:
                break
            text_len = len(sent["text"])

            # Ensure at least some length diversity
            if text_len <= 20:
                if short_count >= 4:
                    continue
                short_count += 1
            elif text_len >= 60:
                if long_count >= 6:
                    continue
                long_count += 1
            else:
                medium_count += 1

            chosen.append(sent)

        # Assign IDs
        for sent in chosen:
            sent_id = len(selected) + 1
            selected.append({
                "id": sent_id,
                "source": source,
                "text": sent["text"],
                "v7_tokens": sent["tokens"]
            })

        # Stats
        all_phenomena = Counter()
        for _, phenomena, _ in scored[:per_source]:
            for p in phenomena:
                all_phenomena[p] += 1
        stats[source] = {
            "total_available": len(sentences),
            "selected": len(chosen),
            "avg_length": sum(len(s["text"]) for s in chosen) / len(chosen) if chosen else 0,
            "avg_tokens": sum(len(s.get("v7_tokens", s.get("tokens", []))) for s in chosen) / len(chosen) if chosen else 0,
            "phenomena": dict(all_phenomena)
        }

    return selected, stats


def main():
    input_path = Path("data/splits_v7_normalized/test.json")
    output_dir = Path("data/benchmark")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "sentences_100.json"

    with open(input_path) as f:
        test_data = json.load(f)

    print(f"Loaded {len(test_data)} test sentences")

    selected, stats = select_sentences(test_data, per_source=20)

    with open(output_path, "w") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)

    print(f"\nSelected {len(selected)} sentences → {output_path}")
    print()

    total_phenomena = Counter()
    for source, s in sorted(stats.items()):
        print(f"  {source}: {s['selected']}/{s['total_available']} "
              f"(avg len={s['avg_length']:.0f}, avg tokens={s['avg_tokens']:.1f})")
        for p, count in sorted(s["phenomena"].items()):
            print(f"    {p}: {count}")
            total_phenomena[p] += count

    print(f"\nOverall phenomena distribution:")
    for p, count in total_phenomena.most_common():
        print(f"  {p}: {count}")

    # Length distribution
    lengths = [len(s["text"]) for s in selected]
    print(f"\nLength distribution:")
    print(f"  min={min(lengths)}, max={max(lengths)}, "
          f"mean={sum(lengths)/len(lengths):.0f}, "
          f"median={sorted(lengths)[len(lengths)//2]}")


if __name__ == "__main__":
    main()
