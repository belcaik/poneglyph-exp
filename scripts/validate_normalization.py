#!/usr/bin/env python3
"""
Validate the normalization output in data/splits_v7_normalized/.

Checks:
1. Surface-text consistency (surfaces are substrings at expected positions)
2. Reading-surface length plausibility
3. No overlapping spans
4. Okurigana consistency (surface/reading end with same hiragana)
5. Reading is valid hiragana
6. Source distribution preserved
7. No data loss (token count preserved or increased)
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ORIG_DIR = Path("data/splits_v6_no_matcha")
NORM_DIR = Path("data/splits_v7_normalized")
REPORT_PATH = Path("results/normalization_validation_report.md")


def is_hiragana(ch: str) -> bool:
    return '\u3040' <= ch <= '\u309f'


def is_katakana(ch: str) -> bool:
    return '\u30a0' <= ch <= '\u30ff'


def is_kanji(ch: str) -> bool:
    return '\u4e00' <= ch <= '\u9fff' or '\u3400' <= ch <= '\u4dbf'


def strip_kahoku_parens(text: str) -> str:
    return text.replace('()', '')


def find_token_positions(text: str, tokens: list) -> list:
    """Find (start, end) for each token in text. Sequential matching."""
    positions = []
    search_start = 0
    for tok in tokens:
        surface = tok["surface"]
        idx = text.find(surface, search_start)
        if idx == -1:
            idx = text.find(surface)
        if idx == -1:
            positions.append(None)
            continue
        end = idx + len(surface)
        positions.append((idx, end))
        search_start = end
    return positions


def validate_reading(reading: str) -> list:
    """Check if reading is valid hiragana. Returns list of issue descriptions."""
    issues = []
    for ch in reading:
        if not (is_hiragana(ch) or ch == 'ー'):
            if is_katakana(ch):
                issues.append(f"katakana '{ch}' in reading")
            elif is_kanji(ch):
                issues.append(f"kanji '{ch}' in reading")
            elif ch.isascii() and ch.isalpha():
                issues.append(f"latin '{ch}' in reading")
            elif ch.isdigit():
                issues.append(f"digit '{ch}' in reading")
            else:
                issues.append(f"unexpected char '{ch}' (U+{ord(ch):04X}) in reading")
    return issues


def get_trailing_hiragana(surface: str) -> str:
    """Get trailing hiragana from surface."""
    trail = ""
    for ch in reversed(surface):
        if is_hiragana(ch):
            trail = ch + trail
        else:
            break
    return trail


def main():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load original and normalized data
    orig_data = {}
    norm_data = {}
    for split in ["train.json", "val.json", "test.json"]:
        orig_path = ORIG_DIR / split
        norm_path = NORM_DIR / split
        if orig_path.exists():
            with open(orig_path) as f:
                orig_data[split] = json.load(f)
        if norm_path.exists():
            with open(norm_path) as f:
                norm_data[split] = json.load(f)

    # Aggregate
    all_orig = []
    all_norm = []
    for split in ["train.json", "val.json", "test.json"]:
        if split in orig_data:
            all_orig.extend(orig_data[split])
        if split in norm_data:
            all_norm.extend(norm_data[split])

    # Error tracking
    errors = defaultdict(list)
    error_counts = Counter()
    total_sentences = len(all_norm)
    total_tokens_orig = sum(len(s["tokens"]) for s in all_orig)
    total_tokens_norm = sum(len(s["tokens"]) for s in all_norm)

    # Per-source counts
    orig_source_counts = Counter(s["source"] for s in all_orig)
    norm_source_counts = Counter(s["source"] for s in all_norm)

    # Per-source token counts
    orig_token_by_source = Counter()
    norm_token_by_source = Counter()
    expanded_by_source = Counter()

    for s in all_orig:
        orig_token_by_source[s["source"]] += len(s["tokens"])
    for s in all_norm:
        norm_token_by_source[s["source"]] += len(s["tokens"])

    # Count expanded tokens
    for o, n in zip(all_orig, all_norm):
        src = n["source"]
        for ot, nt in zip(o["tokens"], n["tokens"]):
            if ot["surface"] != nt["surface"]:
                expanded_by_source[src] += 1

    # Validation checks
    for sent_idx, sent in enumerate(all_norm):
        text = sent["text"]
        tokens = sent["tokens"]
        source = sent["source"]
        positions = find_token_positions(text, tokens)

        for tok_idx, tok in enumerate(tokens):
            surface = tok["surface"]
            reading = tok["reading"]
            pos = positions[tok_idx]

            # CHECK 1: Surface-text consistency
            if pos is None:
                error_key = "surface_not_found"
                error_counts[error_key] += 1
                if len(errors[error_key]) < 50:
                    errors[error_key].append(
                        f"[{source}] '{surface}' not found in text: {text[:60]}")
            else:
                start, end = pos
                actual = text[start:end]
                if actual != surface:
                    error_key = "surface_mismatch"
                    error_counts[error_key] += 1
                    if len(errors[error_key]) < 50:
                        errors[error_key].append(
                            f"[{source}] Expected '{surface}' at {start}:{end}, got '{actual}'")

            # CHECK 2: Reading-surface length plausibility
            if len(surface) > 0 and len(reading) > 0:
                ratio = len(reading) / len(surface)
                if ratio > 4.0:
                    error_key = "reading_too_long"
                    error_counts[error_key] += 1
                    if len(errors[error_key]) < 50:
                        errors[error_key].append(
                            f"[{source}] '{surface}'/'{reading}' ratio={ratio:.1f}")
                elif ratio < 0.3:
                    error_key = "reading_too_short"
                    error_counts[error_key] += 1
                    if len(errors[error_key]) < 50:
                        errors[error_key].append(
                            f"[{source}] '{surface}'/'{reading}' ratio={ratio:.1f}")

            # CHECK 4: Okurigana consistency
            surface_trail = get_trailing_hiragana(surface)
            reading_trail = get_trailing_hiragana(reading)
            if surface_trail and reading_trail:
                if not reading.endswith(surface_trail):
                    error_key = "okurigana_mismatch"
                    error_counts[error_key] += 1
                    if len(errors[error_key]) < 50:
                        errors[error_key].append(
                            f"[{source}] surface '{surface}' ends with '{surface_trail}', "
                            f"reading '{reading}' ends with '{reading_trail}'")

            # CHECK 5: Reading is valid hiragana
            reading_issues = validate_reading(reading)
            if reading_issues:
                error_key = "invalid_reading"
                error_counts[error_key] += 1
                if len(errors[error_key]) < 50:
                    errors[error_key].append(
                        f"[{source}] '{surface}'/'{reading}': {'; '.join(reading_issues)}")

        # CHECK 3: No overlapping spans
        valid_positions = [(i, p) for i, p in enumerate(positions) if p is not None]
        valid_positions.sort(key=lambda x: x[1][0])
        for i in range(len(valid_positions) - 1):
            idx_a, (start_a, end_a) = valid_positions[i]
            idx_b, (start_b, end_b) = valid_positions[i + 1]
            if end_a > start_b:
                error_key = "overlapping_spans"
                error_counts[error_key] += 1
                surf_a = tokens[idx_a]["surface"]
                surf_b = tokens[idx_b]["surface"]
                if len(errors[error_key]) < 50:
                    errors[error_key].append(
                        f"[{source}] '{surf_a}' ({start_a}:{end_a}) overlaps "
                        f"'{surf_b}' ({start_b}:{end_b})")

    # CHECK 6: Source distribution preserved
    source_dist_ok = True
    for src in orig_source_counts:
        if orig_source_counts[src] != norm_source_counts.get(src, 0):
            source_dist_ok = False
            error_key = "source_distribution"
            error_counts[error_key] += 1
            errors[error_key].append(
                f"{src}: orig={orig_source_counts[src]}, norm={norm_source_counts.get(src, 0)}")

    # CHECK 7: No data loss
    data_loss = total_tokens_norm < total_tokens_orig

    # Calculate error rate
    total_checks = total_tokens_norm * 4  # approx number of checks per token
    total_errors = sum(error_counts.values())
    error_rate = total_errors / total_tokens_norm if total_tokens_norm > 0 else 0

    # Generate report
    report = []
    report.append("# Normalization Validation Report\n")
    report.append(f"## Summary\n")
    report.append(f"- Total sentences: {total_sentences}")
    report.append(f"- Total tokens (original): {total_tokens_orig}")
    report.append(f"- Total tokens (normalized): {total_tokens_norm}")
    report.append(f"- Token count change: {total_tokens_norm - total_tokens_orig:+d}")
    report.append(f"- Total validation errors: {total_errors}")
    report.append(f"- Error rate: {error_rate:.4f} ({100*error_rate:.2f}%)")
    report.append("")

    # Per-source expansion stats
    report.append("## Tokens Expanded Per Source\n")
    report.append("| Source | Total Tokens | Expanded | % Expanded |")
    report.append("|--------|-------------|----------|-----------|")
    for src in sorted(norm_token_by_source):
        total = norm_token_by_source[src]
        exp = expanded_by_source.get(src, 0)
        pct = 100 * exp / total if total > 0 else 0
        report.append(f"| {src} | {total} | {exp} | {pct:.1f}% |")
    report.append("")

    # Error breakdown
    report.append("## Error Breakdown\n")
    report.append("| Check | Errors |")
    report.append("|-------|--------|")
    check_names = {
        "surface_not_found": "Surface not found in text",
        "surface_mismatch": "Surface mismatch at position",
        "reading_too_long": "Reading >4x surface length",
        "reading_too_short": "Reading <0.3x surface length",
        "overlapping_spans": "Overlapping spans",
        "okurigana_mismatch": "Okurigana mismatch",
        "invalid_reading": "Invalid reading characters",
        "source_distribution": "Source distribution change",
    }
    for key in sorted(error_counts, key=error_counts.get, reverse=True):
        name = check_names.get(key, key)
        report.append(f"| {name} | {error_counts[key]} |")
    if not error_counts:
        report.append("| (none) | 0 |")
    report.append("")

    # Source distribution
    report.append("## Source Distribution\n")
    report.append("| Source | Original | Normalized | Match |")
    report.append("|--------|----------|-----------|-------|")
    for src in sorted(set(list(orig_source_counts) + list(norm_source_counts))):
        o = orig_source_counts.get(src, 0)
        n = norm_source_counts.get(src, 0)
        match = "✓" if o == n else "✗"
        report.append(f"| {src} | {o} | {n} | {match} |")
    report.append("")

    # Error details (max 100)
    report.append("## Flagged Issues (up to 100)\n")
    shown = 0
    for key in sorted(error_counts, key=error_counts.get, reverse=True):
        if shown >= 100:
            remaining = sum(len(v) for v in errors.values()) - shown
            report.append(f"\n... and {remaining} more issues (truncated)")
            break
        name = check_names.get(key, key)
        report.append(f"### {name} ({error_counts[key]} total)\n")
        for detail in errors[key][:20]:
            report.append(f"- {detail}")
            shown += 1
        if error_counts[key] > 20:
            report.append(f"- ... and {error_counts[key] - 20} more")
        report.append("")

    # Overall assessment
    report.append("## Assessment\n")
    if error_rate > 0.01:
        report.append(f"**FAIL**: Error rate {100*error_rate:.2f}% exceeds 1% threshold.")
        report.append("Investigation and fixes needed before proceeding.")
    elif error_rate > 0.005:
        report.append(f"**WARNING**: Error rate {100*error_rate:.2f}% is between 0.5% and 1%.")
        report.append("Review flagged issues but acceptable for training.")
    else:
        report.append(f"**PASS**: Error rate {100*error_rate:.2f}% is below 0.5% threshold.")

    if data_loss:
        report.append(f"\n**WARNING**: Token count decreased from {total_tokens_orig} to {total_tokens_norm}.")
    if not source_dist_ok:
        report.append("\n**WARNING**: Source distribution changed.")

    report_text = "\n".join(report)

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
