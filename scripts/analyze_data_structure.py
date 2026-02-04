#!/usr/bin/env python3
"""
Analyze data structure across all sources to document the v3 data quality issue.
Outputs a comprehensive audit report for T5 v4 planning.
"""

import json
from pathlib import Path
from collections import defaultdict
import statistics


def count_japanese_periods(text: str) -> int:
    """Count Japanese sentence-ending punctuation."""
    return text.count("。") + text.count("！") + text.count("？")


def analyze_split(filepath: Path) -> dict:
    """Analyze a single data split file."""
    with open(filepath) as f:
        data = json.load(f)

    source_stats = defaultdict(lambda: {
        "count": 0,
        "char_lengths": [],
        "token_counts": [],
        "period_counts": [],
        "items_over_150_chars": 0,
        "items_over_300_chars": 0,
        "items_with_multiple_sentences": 0,
    })

    for item in data:
        source = item.get("source", "unknown")
        text = item.get("text", "")
        tokens = item.get("tokens", [])

        char_len = len(text)
        token_count = len(tokens)
        period_count = count_japanese_periods(text)

        stats = source_stats[source]
        stats["count"] += 1
        stats["char_lengths"].append(char_len)
        stats["token_counts"].append(token_count)
        stats["period_counts"].append(period_count)

        if char_len > 150:
            stats["items_over_150_chars"] += 1
        if char_len > 300:
            stats["items_over_300_chars"] += 1
        if period_count > 1:
            stats["items_with_multiple_sentences"] += 1

    # Compute summary statistics
    results = {}
    for source, stats in source_stats.items():
        char_lengths = stats["char_lengths"]
        token_counts = stats["token_counts"]
        period_counts = stats["period_counts"]

        results[source] = {
            "count": stats["count"],
            "char_length": {
                "min": min(char_lengths),
                "max": max(char_lengths),
                "avg": statistics.mean(char_lengths),
                "median": statistics.median(char_lengths),
                "stdev": statistics.stdev(char_lengths) if len(char_lengths) > 1 else 0,
            },
            "token_count": {
                "min": min(token_counts),
                "max": max(token_counts),
                "avg": statistics.mean(token_counts),
                "median": statistics.median(token_counts),
                "total": sum(token_counts),
            },
            "period_count": {
                "min": min(period_counts),
                "max": max(period_counts),
                "avg": statistics.mean(period_counts),
                "distribution": dict(sorted(
                    {p: period_counts.count(p) for p in set(period_counts)}.items()
                )),
            },
            "items_over_150_chars": stats["items_over_150_chars"],
            "items_over_300_chars": stats["items_over_300_chars"],
            "items_with_multiple_sentences": stats["items_with_multiple_sentences"],
            "pct_over_150": 100 * stats["items_over_150_chars"] / stats["count"],
            "pct_multiple_sentences": 100 * stats["items_with_multiple_sentences"] / stats["count"],
        }

    return results


def classify_data_type(avg_chars: float, pct_over_150: float, avg_periods: float) -> str:
    """Classify data as sentence, paragraph, or article level."""
    if avg_chars < 80 and pct_over_150 < 20:
        return "Sentence"
    elif avg_chars < 200 and pct_over_150 < 60:
        return "Paragraph"
    else:
        return "Article"


def generate_report(splits_dir: Path, output_path: Path):
    """Generate comprehensive data audit report."""
    # Analyze all splits
    results = {}
    for split in ["train", "val", "test"]:
        filepath = splits_dir / f"{split}.json"
        if filepath.exists():
            results[split] = analyze_split(filepath)

    # Generate markdown report
    lines = [
        "# T5 v4 Data Audit Report",
        "",
        "## Executive Summary",
        "",
        "This audit documents the data structure inconsistency discovered during T5 v3 evaluation.",
        "**Key finding**: MATCHA data contains full articles (avg ~400+ chars), not sentences (~50 chars).",
        "This mismatch caused artificially low accuracy (32.5%) due to token truncation.",
        "",
        "## Data Structure by Source",
        "",
    ]

    # Create summary table across all splits
    all_sources = set()
    for split_results in results.values():
        all_sources.update(split_results.keys())

    # Use test split for detailed analysis (representative)
    test_results = results.get("test", {})

    lines.extend([
        "### Test Set Analysis",
        "",
        "| Source | Items | Avg Chars | Max Chars | Avg Tokens | Avg Periods | Data Type |",
        "|--------|-------|-----------|-----------|------------|-------------|-----------|",
    ])

    for source in sorted(test_results.keys()):
        stats = test_results[source]
        avg_chars = stats["char_length"]["avg"]
        max_chars = stats["char_length"]["max"]
        avg_tokens = stats["token_count"]["avg"]
        avg_periods = stats["period_count"]["avg"]
        pct_over_150 = stats["pct_over_150"]
        data_type = classify_data_type(avg_chars, pct_over_150, avg_periods)

        lines.append(
            f"| {source} | {stats['count']} | {avg_chars:.1f} | {max_chars} | "
            f"{avg_tokens:.1f} | {avg_periods:.1f} | {data_type} |"
        )

    lines.extend([
        "",
        "### Items Exceeding Single-Sentence Length",
        "",
        "| Source | Items | >150 chars | % | >300 chars | % | Multiple 。 | % |",
        "|--------|-------|------------|---|------------|---|------------|---|",
    ])

    for source in sorted(test_results.keys()):
        stats = test_results[source]
        count = stats["count"]
        over_150 = stats["items_over_150_chars"]
        over_300 = stats["items_over_300_chars"]
        multi_sent = stats["items_with_multiple_sentences"]

        lines.append(
            f"| {source} | {count} | {over_150} | {100*over_150/count:.1f}% | "
            f"{over_300} | {100*over_300/count:.1f}% | {multi_sent} | {100*multi_sent/count:.1f}% |"
        )

    lines.extend([
        "",
        "## Detailed Per-Source Analysis",
        "",
    ])

    for source in sorted(test_results.keys()):
        stats = test_results[source]
        lines.extend([
            f"### {source.upper()}",
            "",
            f"**Classification**: {classify_data_type(stats['char_length']['avg'], stats['pct_over_150'], stats['period_count']['avg'])}",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Item count | {stats['count']} |",
            f"| Character length (avg) | {stats['char_length']['avg']:.1f} |",
            f"| Character length (median) | {stats['char_length']['median']:.1f} |",
            f"| Character length (max) | {stats['char_length']['max']} |",
            f"| Character length (stdev) | {stats['char_length']['stdev']:.1f} |",
            f"| Tokens (avg) | {stats['token_count']['avg']:.1f} |",
            f"| Tokens (total) | {stats['token_count']['total']} |",
            f"| Japanese periods (avg) | {stats['period_count']['avg']:.1f} |",
            f"| Items >150 chars | {stats['items_over_150_chars']} ({stats['pct_over_150']:.1f}%) |",
            f"| Items with multiple sentences | {stats['items_with_multiple_sentences']} ({stats['pct_multiple_sentences']:.1f}%) |",
            "",
        ])

        # Period distribution
        period_dist = stats["period_count"]["distribution"]
        if len(period_dist) > 1:
            lines.extend([
                "**Period count distribution:**",
                "",
                "| Periods | Count |",
                "|---------|-------|",
            ])
            for periods, count in list(period_dist.items())[:10]:
                lines.append(f"| {periods} | {count} |")
            if len(period_dist) > 10:
                lines.append(f"| ... | (truncated, {len(period_dist)} unique values) |")
            lines.append("")

    # Training data analysis
    lines.extend([
        "## Training Data Analysis",
        "",
    ])

    train_results = results.get("train", {})
    if train_results:
        lines.extend([
            "| Source | Items | Avg Chars | Total Tokens | Data Type |",
            "|--------|-------|-----------|--------------|-----------|",
        ])

        total_items = 0
        total_tokens = 0
        for source in sorted(train_results.keys()):
            stats = train_results[source]
            data_type = classify_data_type(
                stats["char_length"]["avg"],
                stats["pct_over_150"],
                stats["period_count"]["avg"]
            )
            total_items += stats["count"]
            total_tokens += stats["token_count"]["total"]
            lines.append(
                f"| {source} | {stats['count']} | {stats['char_length']['avg']:.1f} | "
                f"{stats['token_count']['total']} | {data_type} |"
            )
        lines.append(f"| **TOTAL** | **{total_items}** | - | **{total_tokens}** | - |")

    lines.extend([
        "",
        "## Impact on T5 v3 Accuracy",
        "",
        "The data structure mismatch explains the T5 v3 accuracy discrepancy:",
        "",
        "| Source | Accuracy | Avg Chars | Issue |",
        "|--------|----------|-----------|-------|",
        "| NHK | 82.1% | ~48 | None - proper sentence data |",
        "| Hirogaru | 80.8% | ~64 | None - proper sentence data |",
        "| Kahoku | 60.2% | ~145 | Partial - paragraph level |",
        "| MATCHA | 32.5% | ~444 | Severe - article level, token truncation |",
        "",
        "**Root cause**: T5 model uses `max_length=256` tokens. MATCHA articles exceed this,",
        "causing truncation. The model correctly annotates visible text but cannot predict",
        "tokens beyond the context window.",
        "",
        "## Recommendations for v4",
        "",
        "1. **Implement sentence segmentation** for MATCHA and Kahoku sources",
        "2. **Split on Japanese sentence boundaries**: 。！？",
        "3. **Reassign tokens** to segmented sentences (preserve total count)",
        "4. **Verify uniform structure** before training (all items <100 chars avg)",
        "5. **Rebuild splits** with consistent sentence-level granularity",
        "",
        "## Segmentation Rules",
        "",
        "```python",
        "SENTENCE_ENDINGS = ['。', '！', '？']",
        "# Split text at these boundaries",
        "# Assign tokens to sentences based on character position",
        "# Handle edge cases: quotes, parentheses, inline readings",
        "```",
        "",
        "---",
        "",
        "*Generated by scripts/analyze_data_structure.py*",
    ])

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Report written to: {output_path}")

    # Also save raw JSON for programmatic access
    json_path = output_path.with_suffix(".json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Raw data written to: {json_path}")


if __name__ == "__main__":
    import os
    os.chdir("/home/belcaik/Dev/poneglyph-exp")

    generate_report(
        splits_dir=Path("data/splits"),
        output_path=Path("results/v4_data_audit.md")
    )
