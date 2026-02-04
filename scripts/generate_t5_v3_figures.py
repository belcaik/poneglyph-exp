#!/usr/bin/env python3
"""
Generate visualization figures for T5 v3 expanded data report.
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Set up plot style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 10

def create_accuracy_progression():
    """Create bar chart of accuracy across all methods."""
    methods = ['Lindera', 'T5 v1\n(hiragana)', 'Sudachi\nMode C', 'T5 v2\n(bracket)', 'T5 v3\n(NHK only)']
    accuracies = [62.7, 61.8, 63.5, 80.4, 82.1]
    colors = ['#a6cee3', '#b2df8a', '#fdbf6f', '#1f78b4', '#33a02c']

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(methods, accuracies, color=colors, edgecolor='black', linewidth=1.2)

    # Add value labels on bars
    for bar, acc in zip(bars, accuracies):
        height = bar.get_height()
        ax.annotate(f'{acc}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold')

    ax.set_ylabel('Accuracy (%)', fontsize=12)
    ax.set_title('Furigana Annotation Method Comparison', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)

    # Add horizontal line at 80%
    ax.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='80% target')
    ax.legend(loc='lower right')

    plt.tight_layout()
    plt.savefig('results/figures/accuracy_progression.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Created: accuracy_progression.png")

def create_training_loss_v3():
    """Create training and eval loss curves for v3."""
    # Load training log
    with open('results/t5_v3_training_log.json') as f:
        log = json.load(f)

    # Extract epoch-level data
    epochs = []
    train_losses = []
    eval_losses = []

    for entry in log['log_history']:
        if 'eval_loss' in entry:
            epochs.append(entry['epoch'])
            eval_losses.append(entry['eval_loss'])
        if 'loss' in entry and 'epoch' in entry:
            # Get the first loss of each epoch for train loss approximation
            epoch_num = int(entry['epoch'])
            if epoch_num not in [int(e) for e in epochs if e == int(e)]:
                train_losses.append(entry['loss'])

    # Get actual epoch numbers for eval losses
    epoch_nums = list(range(1, len(eval_losses) + 1))

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(epoch_nums, eval_losses, 'b-o', linewidth=2, markersize=8, label='Eval Loss')

    # Mark best epoch
    best_epoch = 4
    best_loss = 0.116
    ax.axvline(x=best_epoch, color='green', linestyle='--', alpha=0.7, label=f'Best (epoch {best_epoch})')
    ax.annotate(f'Best: {best_loss}',
                xy=(best_epoch, best_loss),
                xytext=(best_epoch + 0.5, best_loss + 0.01),
                fontsize=10, fontweight='bold')

    # Mark early stopping
    ax.axvline(x=7, color='red', linestyle=':', alpha=0.7, label='Early stopping')

    ax.set_xlabel('Epoch', fontsize=12)
    ax.set_ylabel('Loss', fontsize=12)
    ax.set_title('T5 v3 Training Progress (Eval Loss)', fontsize=14, fontweight='bold')
    ax.set_xlim(0.5, 7.5)
    ax.legend()

    plt.tight_layout()
    plt.savefig('results/figures/training_loss_v3.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Created: training_loss_v3.png")

def create_data_vs_accuracy():
    """Create scatter plot of training tokens vs accuracy."""
    # Data points: v2 and v3
    tokens = [19000, 80000]
    accuracies = [80.4, 82.1]  # Using NHK-only accuracy for v3
    labels = ['T5 v2\n(NHK only)', 'T5 v3\n(Multi-source)']

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.scatter(tokens, accuracies, s=200, c=['#1f78b4', '#33a02c'], edgecolor='black', linewidth=2, zorder=5)
    ax.plot(tokens, accuracies, 'k--', alpha=0.5, zorder=1)

    # Add labels
    for i, (t, a, l) in enumerate(zip(tokens, accuracies, labels)):
        offset = (5000, 0.5) if i == 0 else (-15000, -1.0)
        ax.annotate(f'{l}\n{a}%', xy=(t, a), xytext=(t + offset[0], a + offset[1]),
                    fontsize=11, ha='center',
                    arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5))

    ax.set_xlabel('Training Tokens', fontsize=12)
    ax.set_ylabel('Accuracy (%) - NHK Test Set', fontsize=12)
    ax.set_title('Training Data Size vs Accuracy', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 100000)
    ax.set_ylim(78, 85)

    # Format x-axis as thousands
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000)}K'))

    plt.tight_layout()
    plt.savefig('results/figures/data_vs_accuracy.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Created: data_vs_accuracy.png")

def create_per_source_accuracy():
    """Create grouped bar chart of accuracy per source."""
    sources = ['NHK', 'Hirogaru', 'Kahoku', 'MATCHA']
    accuracies = [82.1, 80.8, 60.2, 32.5]
    data_types = ['Sentence', 'Sentence', 'Paragraph', 'Article']

    colors = ['#2ecc71', '#2ecc71', '#f39c12', '#e74c3c']  # Green for good, orange for moderate, red for poor

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(sources, accuracies, color=colors, edgecolor='black', linewidth=1.2)

    # Add value labels and data type annotations
    for bar, acc, dtype in zip(bars, accuracies, data_types):
        height = bar.get_height()
        ax.annotate(f'{acc}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold')
        ax.annotate(f'({dtype})',
                    xy=(bar.get_x() + bar.get_width() / 2, 5),
                    ha='center', va='bottom',
                    fontsize=9, style='italic', color='gray')

    ax.set_ylabel('Accuracy (%)', fontsize=12)
    ax.set_title('T5 v3 Per-Source Accuracy', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)

    # Add v2 reference line
    ax.axhline(y=80.4, color='blue', linestyle='--', alpha=0.7, label='T5 v2 (80.4%)')
    ax.legend()

    # Add note about data types
    ax.text(0.02, 0.98, 'Data type annotation in parentheses',
            transform=ax.transAxes, fontsize=8, va='top', style='italic', color='gray')

    plt.tight_layout()
    plt.savefig('results/figures/per_source_accuracy.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Created: per_source_accuracy.png")

if __name__ == "__main__":
    import os
    os.chdir('/home/belcaik/Dev/poneglyph-exp')

    create_accuracy_progression()
    create_training_loss_v3()
    create_data_vs_accuracy()
    create_per_source_accuracy()

    print("\nAll figures generated in results/figures/")
