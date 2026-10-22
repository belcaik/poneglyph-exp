#!/usr/bin/env python3
"""Generate figures for Span Detector v1 experiment."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def load_data():
    with open("results/span_detector_v1_training_log.json") as f:
        training_log = json.load(f)
    with open("results/span_detector_v1_eval.json") as f:
        eval_results = json.load(f)
    return training_log, eval_results


def fig1_training_curves(training_log, output_dir):
    """Training curves: loss and span F1 over epochs."""
    epochs = [e["epoch"] for e in training_log["log_history"]]
    train_loss = [e["train_loss"] for e in training_log["log_history"]]
    eval_loss = [e["eval_loss"] for e in training_log["log_history"]]
    span_f1 = [e["span_f1"] for e in training_log["log_history"]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # Loss
    ax1.plot(epochs, train_loss, "b-o", markersize=4, label="Train loss")
    ax1.plot(epochs, eval_loss, "r-o", markersize=4, label="Val loss")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.set_title("Training & Validation Loss")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale("log")

    # Span F1
    ax2.plot(epochs, span_f1, "g-o", markersize=4, label="Val span F1")
    ax2.axhline(y=0.92, color="gray", linestyle="--", alpha=0.7, label="Target (0.92)")
    best_epoch = training_log["results"]["best_epoch"]
    best_f1 = training_log["results"]["best_val_span_f1"]
    ax2.plot(best_epoch, best_f1, "r*", markersize=15, label=f"Best: {best_f1:.4f} (epoch {best_epoch})")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Span F1")
    ax2.set_title("Validation Span F1")
    ax2.legend(loc="lower right")
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0.92, 0.98)

    plt.tight_layout()
    plt.savefig(output_dir / "fig1_training_curves.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  fig1_training_curves.png")


def fig2_pipeline_comparison(eval_results, output_dir):
    """Bar chart comparing pipeline accuracy across methods."""
    methods = [
        "BERT v1\n(tok. class.)",
        "SpanDet v1\n+ BERT v2",
        "T5 v7\n(seq2seq)",
        "ByT5 v2\n(seq2seq)",
        "BERT v2\n(GT spans)",
    ]
    accuracies = [66.3, 82.0, 86.6, 89.1, 98.8]
    colors = ["#d9534f", "#f0ad4e", "#5bc0de", "#5cb85c", "#337ab7"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(methods, accuracies, color=colors, edgecolor="black", linewidth=0.5)

    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{acc:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=11)

    ax.set_ylabel("Accuracy (%)")
    ax.set_title("End-to-End Pipeline Accuracy Comparison")
    ax.set_ylim(0, 105)
    ax.grid(True, axis="y", alpha=0.3)
    ax.axhline(y=89.1, color="green", linestyle="--", alpha=0.5, label="ByT5 v2 baseline (89.1%)")
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "fig2_pipeline_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  fig2_pipeline_comparison.png")


def fig3_per_source(eval_results, output_dir):
    """Per-source comparison: span F1 and pipeline accuracy."""
    sources = list(eval_results["span_detection"]["per_source"].keys())
    span_f1 = [eval_results["span_detection"]["per_source"][s]["f1"] for s in sources]
    pipeline_acc = [eval_results["pipeline"]["per_source"][s]["accuracy"] / 100 for s in sources]

    x = np.arange(len(sources))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    bars1 = ax.bar(x - width / 2, span_f1, width, label="Span F1", color="#5bc0de", edgecolor="black", linewidth=0.5)
    bars2 = ax.bar(x + width / 2, pipeline_acc, width, label="Pipeline Acc.", color="#f0ad4e", edgecolor="black", linewidth=0.5)

    for bar, val in zip(bars1, span_f1):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                f"{val:.3f}", ha="center", va="bottom", fontsize=9)
    for bar, val in zip(bars2, pipeline_acc):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                f"{val:.3f}", ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("Score")
    ax.set_title("Per-Source: Span Detection F1 vs Pipeline Accuracy")
    ax.set_xticks(x)
    ax.set_xticklabels(sources)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    ax.set_ylim(0.7, 1.05)

    plt.tight_layout()
    plt.savefig(output_dir / "fig3_per_source.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  fig3_per_source.png")


def fig4_error_breakdown(eval_results, output_dir):
    """Pie chart of error types + span length accuracy."""
    error_types = eval_results["pipeline"]["error_types"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Error type pie chart
    labels = ["Wrong reading\n(OOV + disambig.)", "Missed span\n(FN)", "Spurious span\n(FP)"]
    sizes = [error_types["wrong_reading"], error_types["missed_span"], error_types["spurious_span"]]
    colors = ["#d9534f", "#f0ad4e", "#5bc0de"]
    explode = (0.05, 0, 0)
    wedges, texts, autotexts = ax1.pie(
        sizes, labels=labels, colors=colors, explode=explode,
        autopct=lambda p: f"{p:.1f}%\n({int(p*sum(sizes)/100)})",
        startangle=90, textprops={"fontsize": 9}
    )
    ax1.set_title("Error Type Distribution (n=2,541)")

    # Span length accuracy
    span_stats = eval_results["span_detection"]["span_length_stats"]
    lengths = sorted(set(
        [int(k) for k in span_stats["correct"].keys()] +
        [int(k) for k in span_stats["missed"].keys()]
    ))
    correct_counts = [span_stats["correct"].get(str(l), 0) for l in lengths]
    missed_counts = [span_stats["missed"].get(str(l), 0) for l in lengths]
    totals = [c + m for c, m in zip(correct_counts, missed_counts)]
    accuracies = [c / t * 100 if t > 0 else 0 for c, t in zip(correct_counts, totals)]

    bars = ax2.bar([str(l) for l in lengths], accuracies, color="#5cb85c", edgecolor="black", linewidth=0.5)
    for bar, acc, total in zip(bars, accuracies, totals):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{acc:.0f}%\n(n={total})", ha="center", va="bottom", fontsize=8)
    ax2.set_xlabel("Span Length (characters)")
    ax2.set_ylabel("Recall (%)")
    ax2.set_title("Span Detection Recall by Span Length")
    ax2.set_ylim(0, 110)
    ax2.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "fig4_error_breakdown.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  fig4_error_breakdown.png")


def main():
    output_dir = Path("results/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating Span Detector v1 figures...")
    training_log, eval_results = load_data()

    fig1_training_curves(training_log, output_dir)
    fig2_pipeline_comparison(eval_results, output_dir)
    fig3_per_source(eval_results, output_dir)
    fig4_error_breakdown(eval_results, output_dir)

    print(f"\nAll figures saved to {output_dir}/")


if __name__ == "__main__":
    main()
