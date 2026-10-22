#!/usr/bin/env python3
"""
Generate comparison statistics for normalization.

Produces:
1. Before/after comparison table per source
2. Top 50 most common expansions
3. Distribution of expansion types
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ORIG_DIR = Path("data/splits_v6_no_matcha")
NORM_DIR = Path("data/splits_v7_normalized")
REPORT_PATH = Path("results/normalization_stats.md")


def is_hiragana(ch: str) -> bool:
    return '\u3040' <= ch <= '\u309f'


def is_kanji(ch: str) -> bool:
    return '\u4e00' <= ch <= '\u9fff' or '\u3400' <= ch <= '\u4dbf'


def classify_expansion(orig_surface, orig_reading, new_surface, new_reading):
    """Classify the type of expansion performed."""
    added = new_surface[len(orig_surface):]
    if not added:
        return "none"

    # Verb te-form: って, って, いて, んで, etc.
    te_forms = ['って', 'いて', 'して', 'んで', 'ちて', 'ってい', 'してい', 'んでい',
                'いてい', 'ってく', 'ていく', 'けて', 'せて', 'めて', 'べて', 'ねて',
                'れて', 'えて', 'てく', 'てき', 'ても', 'てい', 'ては']
    for tf in te_forms:
        if added.startswith(tf):
            return "verb_te_form"

    # Verb ta-form: った, った, いた, んだ, etc.
    ta_forms = ['った', 'いた', 'した', 'んだ', 'ちた', 'けた', 'せた', 'めた',
                'べた', 'ねた', 'れた', 'えた']
    for tf in ta_forms:
        if added.startswith(tf):
            return "verb_ta_form"

    # Verb masu-form: ります, めます, します, etc.
    masu_forms = ['ります', 'します', 'きます', 'めます', 'えます', 'べます',
                  'けます', 'せます', 'ます', 'ません', 'ました']
    for mf in masu_forms:
        if added.startswith(mf):
            return "verb_masu_form"

    # Verb dictionary form: る, く, す, etc.
    dict_forms = ['る', 'く', 'す', 'つ', 'ぬ', 'ぶ', 'む', 'うる', 'える']
    for df in dict_forms:
        if added == df or (added.startswith(df) and len(added) <= len(df) + 2):
            return "verb_dictionary_form"

    # Adjective forms
    adj_forms = ['い', 'く', 'くて', 'くな', 'さ', 'さい', 'きい', 'しい', 'しく',
                 'くなり', 'くなった', 'くなって', 'きく', 'さく']
    for af in adj_forms:
        if added.startswith(af):
            return "adjective_inflection"

    # Passive/causative: れる, される, せる, etc.
    passive_forms = ['れる', 'れた', 'れて', 'られる', 'られた', 'られて',
                     'される', 'された', 'されて', 'させる', 'させた', 'させて',
                     'われる', 'われた', 'われて']
    for pf in passive_forms:
        if added.startswith(pf):
            return "verb_passive_causative"

    # Suru verb: する, した, して, している etc.
    if added.startswith('する') or added.startswith('した') or added.startswith('して'):
        return "suru_verb"

    # Negative forms: ない, なかった
    neg_forms = ['ない', 'なかった', 'なくな', 'なけれ']
    for nf in neg_forms:
        if added.startswith(nf):
            return "verb_negative"

    # Compound okurigana
    if len(added) >= 4:
        return "compound_conjugation"

    return "other"


def main():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    all_orig = []
    all_norm = []
    for split in ["train.json", "val.json", "test.json"]:
        with open(ORIG_DIR / split) as f:
            all_orig.extend(json.load(f))
        with open(NORM_DIR / split) as f:
            all_norm.extend(json.load(f))

    # Collect expansion data
    expansions = []  # (source, orig_surface, new_surface, added_text)
    surface_lengths_orig = defaultdict(list)
    surface_lengths_norm = defaultdict(list)
    unique_surfaces_orig = defaultdict(set)
    unique_surfaces_norm = defaultdict(set)

    for o, n in zip(all_orig, all_norm):
        src = n["source"]
        for ot, nt in zip(o["tokens"], n["tokens"]):
            surface_lengths_orig[src].append(len(ot["surface"]))
            surface_lengths_norm[src].append(len(nt["surface"]))
            unique_surfaces_orig[src].add(ot["surface"])
            unique_surfaces_norm[src].add(nt["surface"])

            if ot["surface"] != nt["surface"]:
                added = nt["surface"][len(ot["surface"]):]
                expansions.append({
                    "source": src,
                    "orig_surface": ot["surface"],
                    "orig_reading": ot["reading"],
                    "new_surface": nt["surface"],
                    "new_reading": nt["reading"],
                    "added": added,
                    "type": classify_expansion(
                        ot["surface"], ot["reading"],
                        nt["surface"], nt["reading"]
                    ),
                })

    # Build report
    report = []
    report.append("# Normalization Statistics\n")

    # 1. Before/after comparison per source
    report.append("## Before/After Comparison Per Source\n")
    report.append("| Source | Tokens | Avg Surface Len (Before) | Avg Surface Len (After) | Expanded | % Expanded | Unique Surfaces (Before) | Unique Surfaces (After) |")
    report.append("|--------|--------|-------------------------|------------------------|----------|-----------|-------------------------|------------------------|")

    for src in sorted(surface_lengths_orig):
        total = len(surface_lengths_norm[src])
        avg_before = sum(surface_lengths_orig[src]) / len(surface_lengths_orig[src])
        avg_after = sum(surface_lengths_norm[src]) / len(surface_lengths_norm[src])
        expanded = sum(1 for e in expansions if e["source"] == src)
        pct = 100 * expanded / total if total > 0 else 0
        uniq_before = len(unique_surfaces_orig[src])
        uniq_after = len(unique_surfaces_norm[src])
        report.append(f"| {src} | {total} | {avg_before:.2f} | {avg_after:.2f} | {expanded} | {pct:.1f}% | {uniq_before} | {uniq_after} |")
    report.append("")

    # 2. Top 50 most common expansions
    report.append("## Top 50 Most Common Expansions\n")
    expansion_counter = Counter()
    for e in expansions:
        key = f"{e['orig_surface']}→{e['new_surface']}"
        expansion_counter[key] += 1

    report.append("| Rank | Expansion | Count |")
    report.append("|------|-----------|-------|")
    for rank, (exp, count) in enumerate(expansion_counter.most_common(50), 1):
        report.append(f"| {rank} | {exp} | {count} |")
    report.append("")

    # 3. Distribution of expansion types
    report.append("## Expansion Type Distribution\n")
    type_counter = Counter(e["type"] for e in expansions)
    total_expanded = len(expansions)

    type_names = {
        "verb_te_form": "Verb て-form (って, いて, して, んで...)",
        "verb_ta_form": "Verb た-form (った, いた, した, んだ...)",
        "verb_masu_form": "Verb ます-form (ります, します, めます...)",
        "verb_dictionary_form": "Verb dictionary form (る, く, す...)",
        "adjective_inflection": "Adjective inflection (い, く, くて, しい...)",
        "verb_passive_causative": "Passive/causative (れる, される, させる...)",
        "suru_verb": "する verb (する, した, して...)",
        "verb_negative": "Negative form (ない, なかった...)",
        "compound_conjugation": "Compound conjugation (4+ chars)",
        "other": "Other",
    }

    report.append("| Type | Count | % |")
    report.append("|------|-------|---|")
    for t, count in type_counter.most_common():
        name = type_names.get(t, t)
        pct = 100 * count / total_expanded if total_expanded > 0 else 0
        report.append(f"| {name} | {count} | {pct:.1f}% |")
    report.append(f"\n**Total expanded tokens: {total_expanded}**")
    report.append("")

    # 4. Examples per expansion type
    report.append("## Examples Per Expansion Type\n")
    type_examples = defaultdict(list)
    for e in expansions:
        if len(type_examples[e["type"]]) < 5:
            type_examples[e["type"]].append(
                f"{e['orig_surface']}/{e['orig_reading']} → {e['new_surface']}/{e['new_reading']}")

    for t in type_counter:
        name = type_names.get(t, t)
        report.append(f"### {name}\n")
        for ex in type_examples[t]:
            report.append(f"- {ex}")
        report.append("")

    report_text = "\n".join(report)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
