#!/usr/bin/env python3
"""Live training monitor — parses spanreader log and plots metrics in real-time."""
import re
import sys
import time
import matplotlib
matplotlib.use('Agg')  # non-interactive, save to file
import matplotlib.pyplot as plt

LOG_FILE = sys.argv[1] if len(sys.argv) > 1 else "logs/spanreader_v3.log"
REFRESH_SECONDS = 30

def parse_log(path):
    epochs, span_f1s, read_accs, train_losses, val_losses, type_accs = [], [], [], [], [], []
    pattern = re.compile(
        r"Epoch (\d+): train_loss=([\d.]+), val_loss=([\d.]+), "
        r"span_f1=([\d.]+).*read_acc=([\d.]+), type_acc=([\d.]+)"
    )
    with open(path) as f:
        for line in f:
            m = pattern.search(line)
            if m:
                epochs.append(int(m.group(1)))
                train_losses.append(float(m.group(2)))
                val_losses.append(float(m.group(3)))
                span_f1s.append(float(m.group(4)))
                read_accs.append(float(m.group(5)))
                type_accs.append(float(m.group(6)))
    return epochs, train_losses, val_losses, span_f1s, read_accs, type_accs

def plot(epochs, train_losses, val_losses, span_f1s, read_accs, type_accs):
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(f"SpanReader Training — Epoch {epochs[-1] if epochs else 0}", fontsize=14, fontweight='bold')

    # Span F1
    ax = axes[0, 0]
    ax.clear()
    ax.plot(epochs, span_f1s, 'b-o', markersize=4, label='Span F1')
    ax.axhline(y=0.869, color='green', linestyle='--', alpha=0.5, label='v2 test (0.869)')
    ax.axhline(y=0.85, color='orange', linestyle='--', alpha=0.5, label='Target (0.85)')
    ax.set_ylabel('F1 Score')
    ax.set_title('Span Detection F1')
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)

    # Reading Accuracy
    ax = axes[0, 1]
    ax.clear()
    ax.plot(epochs, read_accs, 'r-o', markersize=4, label='Reading Acc')
    ax.axhline(y=0.511, color='green', linestyle='--', alpha=0.5, label='v2 test (0.511)')
    ax.set_ylabel('Accuracy')
    ax.set_title('Reading Accuracy')
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)

    # Loss
    ax = axes[1, 0]
    ax.clear()
    ax.plot(epochs, train_losses, 'b-o', markersize=4, label='Train')
    ax.plot(epochs, val_losses, 'r-o', markersize=4, label='Val')
    ax.set_ylabel('Loss')
    ax.set_xlabel('Epoch')
    ax.set_title('Loss')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Type Accuracy
    ax = axes[1, 1]
    ax.clear()
    ax.plot(epochs, type_accs, 'g-o', markersize=4, label='Type Acc')
    ax.set_ylabel('Accuracy')
    ax.set_xlabel('Epoch')
    ax.set_title('Type Classification Accuracy')
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

OUT_FILE = "logs/training_monitor.png"
print(f"Monitoring {LOG_FILE} — saving to {OUT_FILE} every {REFRESH_SECONDS}s (Ctrl+C to stop)")

while True:
    try:
        data = parse_log(LOG_FILE)
        if data[0]:
            plot(*data)
            plt.savefig(OUT_FILE, dpi=100, bbox_inches='tight')
            plt.close('all')
            print(f"  Updated: epoch {data[0][-1]}, span_f1={data[3][-1]:.3f}, read_acc={data[4][-1]:.3f}")
        else:
            print("  No epochs found yet...")
        time.sleep(REFRESH_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped.")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(REFRESH_SECONDS)
