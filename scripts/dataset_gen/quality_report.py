#!/usr/bin/env python3
"""Generate dataset quality report and figures for poneglyph_v1."""

import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def is_kanji(c):
    cp = ord(c)
    return 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF


def load_splits():
    base = Path("data/poneglyph_v1")
    splits = {}
    for name in ["train", "val", "test"]:
        with open(base / f"{name}.json") as f:
            splits[name] = json.load(f)
    return splits


def generate_source_figure(splits, output_dir):
    """Source distribution across splits."""
    sources = Counter()
    for split in splits.values():
        for e in split:
            sources[e["source"]] += 1

    names = sorted(sources.keys(), key=lambda x: -sources[x])
    values = [sources[n] for n in names]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.barh(range(len(names)), values, color="#5bc0de", edgecolor="black", linewidth=0.5)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel("Sentences")
    ax.set_title("Dataset v1: Source Distribution")
    ax.invert_yaxis()
    for i, v in enumerate(values):
        ax.text(v + 5, i, str(v), va="center", fontsize=8)
    plt.tight_layout()
    plt.savefig(output_dir / "dataset_v1_source_distribution.png", dpi=150)
    plt.close()


def generate_confidence_figure(splits, output_dir):
    """Confidence breakdown pie chart."""
    conf_counts = Counter()
    for split in splits.values():
        for e in split:
            conf_counts[e.get("confidence", "unknown")] += 1

    labels = list(conf_counts.keys())
    sizes = [conf_counts[l] for l in labels]
    colors = {"high": "#5cb85c", "medium": "#f0ad4e", "low": "#d9534f", "unknown": "#999"}
    cs = [colors.get(l, "#999") for l in labels]

    fig, ax = plt.subplots(figsize=(7, 7))
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                       colors=cs, startangle=90)
    ax.set_title("Annotation Confidence Distribution")
    plt.tight_layout()
    plt.savefig(output_dir / "dataset_v1_confidence_breakdown.png", dpi=150)
    plt.close()


def generate_type_figure(splits, output_dir):
    """Token type distribution."""
    type_counts = Counter()
    for split in splits.values():
        for e in split:
            for t in e.get("tokens", []):
                type_counts[t.get("type", "unknown")] += 1

    names = sorted(type_counts.keys(), key=lambda x: -type_counts[x])[:15]
    values = [type_counts[n] for n in names]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(range(len(names)), values, color="#5cb85c", edgecolor="black", linewidth=0.5)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Count")
    ax.set_title("Token Type Distribution")
    plt.tight_layout()
    plt.savefig(output_dir / "dataset_v1_type_distribution.png", dpi=150)
    plt.close()


def generate_report(splits, output_path):
    """Generate markdown report."""
    all_data = []
    for split in splits.values():
        all_data.extend(split)

    total = len(all_data)
    total_tokens = sum(len(e.get("tokens", [])) for e in all_data)
    unique_surfaces = set()
    unique_readings = set()
    surface_counter = Counter()
    type_counter = Counter()
    confidence_counter = Counter()

    for e in all_data:
        confidence_counter[e.get("confidence", "unknown")] += 1
        for t in e.get("tokens", []):
            unique_surfaces.add(t.get("surface", ""))
            unique_readings.add(t.get("reading", ""))
            surface_counter[t.get("surface", "")] += 1
            type_counter[t.get("type", "unknown")] += 1

    # Per-source stats
    source_counts = Counter(e["source"] for e in all_data)
    source_kanji = defaultdict(list)
    for e in all_data:
        kc = sum(1 for c in e["text"] if is_kanji(c))
        source_kanji[e["source"]].append(kc / len(e["text"]) if e["text"] else 0)

    lines = [
        "# Poneglyph v1 Dataset Quality Report\n\n",
        "## Volume\n\n",
        f"| Split | Sentences | Tokens | Unique Surfaces | Unique Readings |\n",
        f"|-------|:---------:|:------:|:---------------:|:---------------:|\n",
    ]

    for name in ["train", "val", "test"]:
        split = splits[name]
        toks = sum(len(e.get("tokens", [])) for e in split)
        surfs = len(set(t.get("surface", "") for e in split for t in e.get("tokens", [])))
        reads = len(set(t.get("reading", "") for e in split for t in e.get("tokens", [])))
        lines.append(f"| {name} | {len(split)} | {toks} | {surfs} | {reads} |\n")

    lines.append(f"| **total** | **{total}** | **{total_tokens}** | "
                 f"**{len(unique_surfaces)}** | **{len(unique_readings)}** |\n\n")

    # Source distribution
    lines.append("## Source Distribution\n\n")
    lines.append("| Source | Sentences | Avg Kanji Density |\n")
    lines.append("|--------|:---------:|:-----------------:|\n")
    for source, count in source_counts.most_common():
        density = sum(source_kanji[source]) / len(source_kanji[source]) if source_kanji[source] else 0
        lines.append(f"| {source} | {count} | {density:.1%} |\n")

    # Annotation quality
    lines.append("\n## Annotation Quality\n\n")
    lines.append("| Confidence | Count | % |\n")
    lines.append("|------------|:-----:|:--:|\n")
    for conf, count in confidence_counter.most_common():
        pct = count / total * 100
        lines.append(f"| {conf} | {count} | {pct:.1f}% |\n")

    # Token types
    lines.append("\n## Token Type Distribution\n\n")
    lines.append("| Type | Count | % |\n")
    lines.append("|------|:-----:|:--:|\n")
    for t, count in type_counter.most_common(15):
        pct = count / total_tokens * 100
        lines.append(f"| {t} | {count} | {pct:.1f}% |\n")

    # Top surfaces
    lines.append("\n## Top 50 Most Frequent Annotated Surfaces\n\n")
    lines.append("| Rank | Surface | Count |\n")
    lines.append("|:----:|---------|:-----:|\n")
    for i, (surface, count) in enumerate(surface_counter.most_common(50), 1):
        lines.append(f"| {i} | {surface} | {count} |\n")

    # Verb chains (top 20)
    verb_surfaces = Counter()
    for e in all_data:
        for t in e.get("tokens", []):
            if t.get("type") == "verb" and len(t.get("surface", "")) >= 3:
                verb_surfaces[t["surface"]] += 1

    lines.append("\n## Top 20 Verb Chains (Poneglyph Convention)\n\n")
    lines.append("| Verb Chain | Reading | Count |\n")
    lines.append("|------------|---------|:-----:|\n")
    # Need to pair surfaces with readings
    verb_pairs = Counter()
    for e in all_data:
        for t in e.get("tokens", []):
            if t.get("type") == "verb" and len(t.get("surface", "")) >= 3:
                verb_pairs[(t["surface"], t.get("reading", ""))] += 1
    for (surface, reading), count in verb_pairs.most_common(20):
        lines.append(f"| {surface} | {reading} | {count} |\n")

    # Sample annotations
    lines.append("\n## Sample Annotations (10 examples)\n\n")
    import random
    random.seed(42)
    samples = random.sample(all_data, min(10, len(all_data)))
    for e in samples:
        lines.append(f"**{e['source']}** ({e['episode']}): `{e['text']}`\n\n")
        if e.get("tokens"):
            lines.append("| Surface | Reading | Type |\n")
            lines.append("|---------|---------|------|\n")
            for t in e["tokens"]:
                lines.append(f"| {t.get('surface','')} | {t.get('reading','')} | {t.get('type','')} |\n")
        lines.append("\n")

    # Figures
    lines.append("## Figures\n\n")
    lines.append("- `results/figures/dataset_v1_source_distribution.png`\n")
    lines.append("- `results/figures/dataset_v1_confidence_breakdown.png`\n")
    lines.append("- `results/figures/dataset_v1_type_distribution.png`\n")

    with open(output_path, "w") as f:
        f.write("".join(lines))
    print(f"Report saved to {output_path}")


def main():
    output_dir = Path("results/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading dataset splits...")
    splits = load_splits()
    total = sum(len(s) for s in splits.values())
    print(f"Total: {total} sentences")

    print("Generating figures...")
    generate_source_figure(splits, output_dir)
    generate_confidence_figure(splits, output_dir)
    generate_type_figure(splits, output_dir)

    print("Generating report...")
    generate_report(splits, Path("results/dataset_v1_report.md"))
    print("Done!")


if __name__ == "__main__":
    main()
