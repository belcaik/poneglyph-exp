#!/usr/bin/env python3
"""Step 6: Generate benchmark results report and figures for all models."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def load_eval_results():
    with open("results/benchmark_eval.json") as f:
        return json.load(f)


def load_coverage_results():
    path = Path("data/benchmark/coverage_validation.json")
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def generate_accuracy_figure(results, output_dir):
    """Bar chart comparing all models on key metrics."""
    model_names = list(results["models"].keys())
    metrics = ["char_coverage_recall", "reading_accuracy", "exact_span_match_pct"]
    metric_labels = ["Char Coverage (Recall)", "Reading Accuracy", "Exact Span Match"]

    x = np.arange(len(model_names))
    width = 0.22
    colors = ["#5bc0de", "#5cb85c", "#f0ad4e"]

    fig, ax = plt.subplots(figsize=(max(10, len(model_names) * 2.5), 6))

    for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
        values = [results["models"][m]["metrics"].get(metric, 0) for m in model_names]
        bars = ax.bar(x + i * width, values, width, label=label, color=colors[i],
                     edgecolor="black", linewidth=0.5)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                   f"{val:.1f}%", ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("Score (%)")
    ax.set_title("LLM Furigana Annotation Benchmark — All Models")
    ax.set_xticks(x + width)
    ax.set_xticklabels([n.upper() for n in model_names], rotation=15)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    ax.set_ylim(0, 115)

    plt.tight_layout()
    plt.savefig(output_dir / "benchmark_accuracy_all_models.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  benchmark_accuracy_all_models.png")


def generate_coverage_figure(coverage_results, output_dir):
    """Kanji coverage per model bar chart."""
    if not coverage_results:
        print("  (skipping coverage figure — no data)")
        return

    model_names = list(coverage_results.keys())
    values = [coverage_results[m]["coverage_pct"] for m in model_names]

    fig, ax = plt.subplots(figsize=(max(8, len(model_names) * 2), 5))
    colors = ["#5cb85c" if v >= 99 else "#d9534f" for v in values]
    bars = ax.bar(range(len(model_names)), values, color=colors, edgecolor="black", linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
               f"{val:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_xticks(range(len(model_names)))
    ax.set_xticklabels([n.upper() for n in model_names], rotation=15)
    ax.set_ylabel("Coverage (%)")
    ax.set_title("Kanji Coverage by Model (target: 100%)")
    ax.set_ylim(0, 110)
    ax.axhline(y=100, color="#333", linestyle="--", alpha=0.5, label="100% target")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "benchmark_coverage_all_models.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  benchmark_coverage_all_models.png")


def generate_per_source_figure(results, output_dir):
    """Per-source comparison chart."""
    model_names = list(results["models"].keys())

    fig, axes = plt.subplots(1, len(model_names),
                            figsize=(5 * len(model_names), 5), squeeze=False)

    for idx, name in enumerate(model_names):
        ax = axes[0][idx]
        per_source = results["models"][name]["per_source"]
        sources = sorted(per_source.keys())

        recall_vals = []
        reading_vals = []
        exact_vals = []

        for source in sources:
            s = per_source[source]
            gt_chars = max(s.get("ov_gt_kanji_chars", 1), 1)
            overlap = s.get("ov_overlap_chars", 0)
            recall_vals.append(overlap / gt_chars * 100)
            checked = max(s.get("ov_reading_spans_checked", 1), 1)
            correct = s.get("ov_reading_spans_correct", 0)
            reading_vals.append(correct / checked * 100)
            gold = max(s.get("gold", 1), 1)
            exact = s.get("exact", 0)
            exact_vals.append(exact / gold * 100)

        x = np.arange(len(sources))
        width = 0.25
        ax.bar(x - width, recall_vals, width, label="Recall", color="#5bc0de")
        ax.bar(x, reading_vals, width, label="Reading Acc.", color="#5cb85c")
        ax.bar(x + width, exact_vals, width, label="Exact Match", color="#f0ad4e")
        ax.set_xticks(x)
        ax.set_xticklabels(sources, rotation=45, fontsize=8)
        ax.set_ylim(0, 110)
        ax.set_title(f"{name.upper()}", fontsize=10)
        ax.legend(fontsize=7)
        ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "benchmark_per_source.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  benchmark_per_source.png")


def generate_agreement_figure(output_dir):
    """Pairwise agreement heatmap between all models."""
    comparison_path = Path("data/benchmark/inter_model_comparison.json")
    if not comparison_path.exists():
        print("  (skipping agreement figure — no comparison data)")
        return

    with open(comparison_path) as f:
        comparison = json.load(f)

    # Collect all model names from the data
    model_names = set()
    for sent in comparison:
        for span in sent["spans"]:
            for key in span:
                if key.endswith("_reading") and key != "v7_gt_reading" and key != "consensus_reading":
                    model_names.add(key.replace("_reading", ""))
    model_names = sorted(model_names)

    if len(model_names) < 2:
        print("  (skipping agreement figure — need at least 2 models)")
        return

    # Add v7_gt
    all_names = model_names + ["v7_gt"]

    # Build pairwise agreement matrix
    n = len(all_names)
    agreement_matrix = np.zeros((n, n))
    pair_counts = np.zeros((n, n))

    for sent in comparison:
        for span in sent["spans"]:
            readings = {}
            for name in model_names:
                r = span.get(f"{name}_reading")
                if r:
                    readings[name] = r
            gt_r = span.get("v7_gt_reading")
            if gt_r:
                readings["v7_gt"] = gt_r

            for i, name_i in enumerate(all_names):
                for j, name_j in enumerate(all_names):
                    if name_i in readings and name_j in readings:
                        pair_counts[i][j] += 1
                        ri = readings[name_i]
                        rj = readings[name_j]
                        if ri == rj or ri in rj or rj in ri:
                            agreement_matrix[i][j] += 1

    # Normalize to percentages
    with np.errstate(divide="ignore", invalid="ignore"):
        agreement_pct = np.where(pair_counts > 0, agreement_matrix / pair_counts * 100, 0)

    fig, ax = plt.subplots(figsize=(max(6, n * 1.5), max(5, n * 1.2)))
    im = ax.imshow(agreement_pct, cmap="RdYlGn", vmin=50, vmax=100, aspect="auto")

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    labels = [name.upper() for name in all_names]
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)

    for i in range(n):
        for j in range(n):
            text = f"{agreement_pct[i][j]:.0f}%"
            color = "white" if agreement_pct[i][j] < 70 else "black"
            ax.text(j, i, text, ha="center", va="center", fontsize=9, color=color)

    ax.set_title("Pairwise Reading Agreement (%)")
    fig.colorbar(im, ax=ax, label="Agreement %")

    plt.tight_layout()
    plt.savefig(output_dir / "benchmark_agreement_matrix.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  benchmark_agreement_matrix.png")


def generate_convention_chart(results, output_dir):
    """Convention adherence comparison."""
    model_names = list(results["models"].keys())
    convention_names = ["verb_chains", "compound_nouns", "proper_nouns",
                        "counters", "no_hiragana_annotation"]
    convention_labels = ["Verb\nChains", "Compound\nNouns", "Proper\nNouns",
                        "Counters", "No Hiragana\nAnnot."]

    fig, ax = plt.subplots(figsize=(max(10, len(model_names) * 2), 6))
    x = np.arange(len(convention_names))
    width = 0.8 / max(len(model_names), 1)
    colors = plt.cm.Set2(np.linspace(0, 1, max(len(model_names), 1)))

    for i, name in enumerate(model_names):
        scores = results["models"][name].get("convention_scores", {})
        values = []
        for conv in convention_names:
            s = scores.get(conv, {"correct": 0, "total": 0})
            if s["total"] > 0:
                values.append(s["correct"] / s["total"] * 100)
            else:
                values.append(0)
        ax.bar(x + i * width, values, width, label=name.upper(),
                     color=colors[i], edgecolor="black", linewidth=0.5)

    ax.set_ylabel("Adherence (%)")
    ax.set_title("Convention Adherence by Model")
    ax.set_xticks(x + width * (len(model_names) - 1) / 2)
    ax.set_xticklabels(convention_labels)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    ax.set_ylim(0, 110)

    plt.tight_layout()
    plt.savefig(output_dir / "benchmark_convention_adherence.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  benchmark_convention_adherence.png")


def generate_report(results, coverage_results, output_path):
    """Generate markdown report with all models."""
    model_names = list(results["models"].keys())

    lines = ["# LLM Furigana Annotation Benchmark Report (v2)\n\n"]

    # Executive summary
    lines.append("## Executive Summary\n\n")
    lines.append("This benchmark evaluates whether LLMs can annotate Japanese text with furigana "
                "following Poneglyph's annotation conventions, and whether their output quality "
                "is sufficient for training data generation.\n\n")
    lines.append(f"**Models tested:** {', '.join(n.upper() for n in model_names)}\n\n")

    best_model = max(model_names,
                    key=lambda m: results["models"][m]["metrics"].get("reading_accuracy", 0))
    best_read = results["models"][best_model]["metrics"]["reading_accuracy"]
    best_recall = results["models"][best_model]["metrics"]["char_coverage_recall"]
    lines.append(f"**Best model: {best_model.upper()}** — {best_read:.1f}% reading accuracy, "
                f"{best_recall:.1f}% character coverage.\n\n")

    # Kanji coverage
    if coverage_results:
        lines.append("## Kanji Coverage\n\n")
        lines.append("Every kanji character in the input must be covered by an annotation. "
                    "Missing kanji = annotation failure.\n\n")
        lines.append("| Model | Kanji Chars | Covered | Coverage |\n")
        lines.append("|-------|:-----------:|:-------:|:--------:|\n")
        for name in model_names:
            if name in coverage_results:
                c = coverage_results[name]
                lines.append(f"| {name.upper()} | {c['total_kanji_chars']} | "
                            f"{c['covered_kanji_chars']} | {c['coverage_pct']:.1f}% |\n")
        lines.append("\n")

    # Accuracy table
    lines.append("## Accuracy Metrics\n\n")
    lines.append("| Model | Char Coverage | Reading Accuracy | Exact Span Match | Parse Failures |\n")
    lines.append("|-------|:------------:|:----------------:|:----------------:|:--------------:|\n")
    for name in model_names:
        m = results["models"][name]["metrics"]
        lines.append(f"| {name.upper()} | {m.get('char_coverage_recall',0):.1f}% | "
                    f"{m.get('reading_accuracy',0):.1f}% | {m.get('exact_span_match_pct',0):.1f}% | "
                    f"{m.get('parse_failure_rate',0):.1f}% |\n")

    lines.append("\n**Metric definitions:**\n")
    lines.append("- **Char Coverage (Recall)**: % of kanji characters annotated by GT that are also covered by the model\n")
    lines.append("- **Reading Accuracy**: Of overlapping spans, % where readings match (allowing for span boundary differences)\n")
    lines.append("- **Exact Span Match**: % of gold tokens with exact surface+reading match in model output\n\n")

    # Per-source breakdown
    lines.append("## Per-Source Breakdown\n\n")
    for name in model_names:
        lines.append(f"### {name.upper()}\n\n")
        lines.append("| Source | Recall | Reading Acc. | Exact Match | Gold Tokens | Model Tokens |\n")
        lines.append("|--------|:------:|:----------:|:-----------:|:-----------:|:------------:|\n")
        per_source = results["models"][name]["per_source"]
        for source in sorted(per_source.keys()):
            s = per_source[source]
            gt_chars = max(s.get("ov_gt_kanji_chars", 1), 1)
            overlap = s.get("ov_overlap_chars", 0)
            recall = overlap / gt_chars * 100
            checked = max(s.get("ov_reading_spans_checked", 1), 1)
            correct = s.get("ov_reading_spans_correct", 0)
            read_acc = correct / checked * 100
            gold = max(s.get("gold", 1), 1)
            exact = s.get("exact", 0)
            exact_pct = exact / gold * 100
            lines.append(f"| {source} | {recall:.1f}% | {read_acc:.1f}% | {exact_pct:.1f}% | "
                        f"{s.get('gold',0)} | {s.get('model',0)} |\n")
        lines.append("\n")

    # Convention adherence
    lines.append("## Convention Adherence\n\n")
    lines.append("| Convention | " + " | ".join(n.upper() for n in model_names) + " |\n")
    lines.append("|------------|" + "|".join([":------:" for _ in model_names]) + "|\n")
    conventions = ["verb_chains", "compound_nouns", "proper_nouns", "counters", "no_hiragana_annotation"]
    conv_labels = ["Verb Chains", "Compound Nouns", "Proper Nouns", "Counters", "No Hiragana Annot."]
    for conv, label in zip(conventions, conv_labels):
        row = f"| {label} |"
        for name in model_names:
            s = results["models"][name].get("convention_scores", {}).get(conv, {"correct": 0, "total": 0})
            if s["total"] > 0:
                pct = s["correct"] / s["total"] * 100
                row += f" {pct:.0f}% ({s['correct']}/{s['total']}) |"
            else:
                row += " N/A |"
        lines.append(row + "\n")

    # Convention difference analysis
    lines.append("\n## Why Exact Match Is Low\n\n")
    lines.append("The v7 ground truth follows a **stem-only** convention, while LLMs were instructed "
                "to follow **Poneglyph conventions** (morpheme-complete). Key differences:\n\n")
    lines.append("| v7 Ground Truth | LLM (Poneglyph) | Convention Rule |\n")
    lines.append("|----------------|-----------------|----------------|\n")
    lines.append("| 活動して | 活動しています | Verb chain: include て+auxiliary |\n")
    lines.append("| 集まって | 集まっています | Verb chain: include ている |\n")
    lines.append("| 午前4時 (1 span) | 午前 + 4時 (2 spans) | Split number+time unit |\n")
    lines.append("| 一番最初 (1 span) | 一番 + 最初 (2 spans) | Don't merge unrelated words |\n")
    lines.append("\nThese are not errors — they are intentional convention differences. "
                "The character-level recall and reading accuracy confirm "
                "the LLM annotations are accurate, just with different span boundaries.\n\n")

    # Recommendation
    lines.append("## Recommendation\n\n")
    if best_read >= 90:
        lines.append(f"**{best_model.upper()} is suitable for generating training data.**\n\n")
        lines.append(f"With {best_read:.1f}% reading accuracy and {best_recall:.1f}% coverage, "
                    f"LLM-generated annotations following Poneglyph conventions are high enough quality "
                    f"to use as training data for smaller models.\n\n")
    else:
        lines.append(f"LLM annotations at {best_read:.1f}% reading accuracy need improvement before "
                    f"use as training data. Consider prompt engineering or larger models.\n\n")

    # Model comparison summary
    lines.append("## Model Comparison Summary\n\n")
    for name in model_names:
        m = results["models"][name]["metrics"]
        lines.append(f"### {name.upper()}\n")
        lines.append(f"- Reading accuracy: {m.get('reading_accuracy',0):.1f}%\n")
        lines.append(f"- Character coverage: {m.get('char_coverage_recall',0):.1f}%\n")
        lines.append(f"- Exact span match: {m.get('exact_span_match_pct',0):.1f}%\n")
        lines.append(f"- Parse failures: {m.get('parse_failure_rate',0):.1f}%\n\n")

    # Figures
    lines.append("## Figures\n\n")
    lines.append("- `results/figures/benchmark_accuracy_all_models.png` — accuracy comparison\n")
    lines.append("- `results/figures/benchmark_coverage_all_models.png` — kanji coverage per model\n")
    lines.append("- `results/figures/benchmark_agreement_matrix.png` — pairwise agreement heatmap\n")
    lines.append("- `results/figures/benchmark_per_source.png` — per-source metrics\n")
    lines.append("- `results/figures/benchmark_convention_adherence.png` — convention compliance\n")

    with open(output_path, "w") as f:
        f.write("".join(lines))
    print(f"Report saved to {output_path}")


def main():
    output_dir = Path("results/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading evaluation results...")
    results = load_eval_results()
    coverage_results = load_coverage_results()

    print("Generating figures...")
    generate_accuracy_figure(results, output_dir)
    generate_coverage_figure(coverage_results, output_dir)
    generate_per_source_figure(results, output_dir)
    generate_agreement_figure(output_dir)
    generate_convention_chart(results, output_dir)

    print("\nGenerating report...")
    generate_report(results, coverage_results, Path("results/benchmark_report.md"))

    print("\nDone!")


if __name__ == "__main__":
    main()
