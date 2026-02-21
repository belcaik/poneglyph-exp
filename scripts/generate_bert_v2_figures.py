#!/usr/bin/env python3
"""
Generate comparison figures for BERT v2 experiment.

Produces:
1. Accuracy comparison bar chart (all methods)
2. Training and validation loss curves
3. Per-source accuracy breakdown
4. Candidates distribution histogram
5. Accuracy by number of candidates (ambiguity)

Usage:
    python scripts/generate_bert_v2_figures.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


RESULTS_DIR = Path("results")
FIGURES_DIR = RESULTS_DIR / "figures"
DICT_PATH = Path("data/bert_v2_reading_dict.json")


def load_comparable_results():
    """Load accuracy values from existing comparable JSON files."""
    methods = {}

    # Map of filename prefix -> display name
    file_map = {
        "bert_v1": "BERT v1",
        "bert_v2": "BERT v2",
        "t5_v6": "T5 v6",
        "t5_v7": "T5 v7",
        "byt5_v2": "ByT5 v2",
    }

    for prefix, display_name in file_map.items():
        path = RESULTS_DIR / f"{prefix}_comparable.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            methods[display_name] = {
                "accuracy": data["summary"]["accuracy"],
                "per_source": data.get("per_source", {}),
            }

    # Hardcoded values for methods without comparable JSON files
    if "Sudachi" not in methods:
        methods["Sudachi"] = {"accuracy": 74.7, "per_source": {}}
    if "Lindera" not in methods:
        methods["Lindera"] = {"accuracy": 62.7, "per_source": {}}

    return methods


def fig1_accuracy_comparison(methods):
    """Bar chart comparing all methods."""
    # Order by accuracy
    sorted_methods = sorted(methods.items(), key=lambda x: x[1]["accuracy"])
    names = [m[0] for m in sorted_methods]
    accuracies = [m[1]["accuracy"] for m in sorted_methods]

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = []
    for name in names:
        if name == "BERT v2":
            colors.append("#2196F3")  # Blue highlight for BERT v2
        elif name == "ByT5 v2":
            colors.append("#4CAF50")  # Green for current best
        else:
            colors.append("#90A4AE")  # Gray for others

    bars = ax.barh(names, accuracies, color=colors, edgecolor="white", linewidth=0.5)

    # Add value labels
    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{acc:.1f}%", va="center", fontsize=11, fontweight="bold")

    ax.set_xlabel("Token-Level Accuracy (%)", fontsize=12)
    ax.set_title("Furigana Annotation: Method Comparison", fontsize=14, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    path = FIGURES_DIR / "bert_v2_accuracy_comparison.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


def fig2_training_loss(training_log):
    """Training and validation loss curves."""
    epochs = [entry["epoch"] for entry in training_log]
    train_losses = [entry["train_loss"] for entry in training_log]
    val_losses = [entry["eval_loss"] for entry in training_log]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Loss curves
    ax1.plot(epochs, train_losses, "o-", label="Train Loss", color="#2196F3", linewidth=2)
    ax1.plot(epochs, val_losses, "s-", label="Val Loss", color="#FF5722", linewidth=2)
    ax1.set_xlabel("Epoch", fontsize=12)
    ax1.set_ylabel("Loss", fontsize=12)
    ax1.set_title("Training & Validation Loss", fontsize=13, fontweight="bold")
    ax1.legend(fontsize=11)
    ax1.grid(alpha=0.3)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Accuracy curves
    train_accs = [entry["train_accuracy"] for entry in training_log]
    val_accs = [entry["eval_accuracy"] for entry in training_log]
    ax2.plot(epochs, train_accs, "o-", label="Train Accuracy", color="#2196F3", linewidth=2)
    ax2.plot(epochs, val_accs, "s-", label="Val Accuracy", color="#FF5722", linewidth=2)
    ax2.set_xlabel("Epoch", fontsize=12)
    ax2.set_ylabel("Accuracy (%)", fontsize=12)
    ax2.set_title("Training & Validation Accuracy", fontsize=13, fontweight="bold")
    ax2.legend(fontsize=11)
    ax2.grid(alpha=0.3)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    plt.tight_layout()
    path = FIGURES_DIR / "bert_v2_training_loss.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


def fig3_per_source(methods):
    """Per-source accuracy breakdown."""
    sources = ["nhk", "ud_gsd", "ud_pud", "kahoku", "hirogaru"]
    source_labels = ["NHK", "UD GSD", "UD PUD", "Kahoku", "Hirogaru"]

    # Methods to compare
    method_order = ["BERT v2", "ByT5 v2", "T5 v7", "T5 v6", "BERT v1"]
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336"]
    available_methods = [(m, c) for m, c in zip(method_order, colors) if m in methods]

    x = np.arange(len(sources))
    width = 0.15
    n_methods = len(available_methods)

    fig, ax = plt.subplots(figsize=(12, 6))

    for i, (method_name, color) in enumerate(available_methods):
        method_data = methods[method_name]
        accs = []
        for source in sources:
            if source in method_data.get("per_source", {}):
                accs.append(method_data["per_source"][source]["accuracy"])
            else:
                accs.append(0)

        offset = (i - n_methods / 2 + 0.5) * width
        bars = ax.bar(x + offset, accs, width, label=method_name, color=color, alpha=0.85)

    ax.set_xlabel("Data Source", fontsize=12)
    ax.set_ylabel("Accuracy (%)", fontsize=12)
    ax.set_title("Per-Source Accuracy Comparison", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(source_labels, fontsize=11)
    ax.legend(fontsize=10, loc="lower right")
    ax.set_ylim(40, 100)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    path = FIGURES_DIR / "bert_v2_per_source.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


def fig4_candidates_distribution():
    """Histogram of candidate reading counts per surface."""
    if not DICT_PATH.exists():
        print(f"Skipping candidates distribution (dict not found: {DICT_PATH})")
        return

    with open(DICT_PATH) as f:
        reading_dict = json.load(f)

    counts = [len(readings) for readings in reading_dict.values()]
    max_count = max(counts)

    fig, ax = plt.subplots(figsize=(8, 5))

    bins = range(1, min(max_count + 2, 12))  # Cap at 11 for readability
    hist_data = [min(c, 11) for c in counts]  # Group 11+ together

    ax.hist(hist_data, bins=[b - 0.5 for b in range(1, 13)], color="#2196F3",
            edgecolor="white", alpha=0.85, rwidth=0.8)

    ax.set_xlabel("Number of Candidate Readings", fontsize=12)
    ax.set_ylabel("Number of Surfaces", fontsize=12)
    ax.set_title("Reading Dictionary: Candidate Distribution", fontsize=14, fontweight="bold")
    ax.set_xticks(range(1, 12))
    labels = [str(i) for i in range(1, 11)] + ["11+"]
    ax.set_xticklabels(labels)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Annotate key stats
    total = len(counts)
    unambiguous = sum(1 for c in counts if c == 1)
    pct_unambiguous = unambiguous / total * 100
    avg = sum(counts) / total

    stats_text = (
        f"Total surfaces: {total:,}\n"
        f"Unambiguous (1 reading): {unambiguous:,} ({pct_unambiguous:.0f}%)\n"
        f"Average candidates: {avg:.2f}"
    )
    ax.text(0.97, 0.97, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment="top", horizontalalignment="right",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", alpha=0.8))

    plt.tight_layout()
    path = FIGURES_DIR / "bert_v2_candidates_distribution.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


def fig5_ambiguity_accuracy(training_log):
    """Accuracy by number of candidates from the last epoch's validation."""
    # Use the last epoch's ambiguity stats
    last_epoch = training_log[-1]
    ambiguity = last_epoch.get("ambiguity_stats", {})

    if not ambiguity:
        print("Skipping ambiguity accuracy (no ambiguity_stats in training log)")
        return

    categories = ["1", "2", "3", "4+"]
    accuracies = []
    totals = []
    for cat in categories:
        if cat in ambiguity and ambiguity[cat]["total"] > 0:
            accuracies.append(ambiguity[cat]["accuracy"])
            totals.append(ambiguity[cat]["total"])
        else:
            accuracies.append(0)
            totals.append(0)

    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(categories, accuracies, color=["#4CAF50", "#2196F3", "#FF9800", "#F44336"],
                  edgecolor="white", alpha=0.85, width=0.6)

    # Add value labels and sample counts
    for bar, acc, total in zip(bars, accuracies, totals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{acc:.1f}%\n(n={total:,})", ha="center", va="bottom", fontsize=11)

    ax.set_xlabel("Number of Candidate Readings", fontsize=12)
    ax.set_ylabel("Validation Accuracy (%)", fontsize=12)
    ax.set_title("Accuracy vs Reading Ambiguity (Val Set)", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 105)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    path = FIGURES_DIR / "bert_v2_ambiguity_accuracy.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Generating BERT v2 Figures")
    print("=" * 60)

    # Load comparable results
    methods = load_comparable_results()
    print(f"\nLoaded results for: {', '.join(methods.keys())}")

    # Load training log
    training_log_path = RESULTS_DIR / "bert_v2_training_log.json"
    training_log = None
    if training_log_path.exists():
        with open(training_log_path) as f:
            training_log = json.load(f)
        print(f"Loaded training log: {len(training_log.get('log_history', []))} epochs")

    # Generate figures
    print("\nGenerating figures...")

    fig1_accuracy_comparison(methods)

    if training_log and training_log.get("log_history"):
        fig2_training_loss(training_log["log_history"])
    else:
        print("Skipping training loss (no training log found)")

    fig3_per_source(methods)
    fig4_candidates_distribution()

    if training_log and training_log.get("log_history"):
        fig5_ambiguity_accuracy(training_log["log_history"])
    else:
        print("Skipping ambiguity accuracy (no training log found)")

    print(f"\n{'=' * 60}")
    print("Figure generation complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
