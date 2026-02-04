# T5 v4 Data Audit Report

## Executive Summary

This audit documents the data structure inconsistency discovered during T5 v3 evaluation.
**Key finding**: MATCHA data contains full articles (avg ~400+ chars), not sentences (~50 chars).
This mismatch caused artificially low accuracy (32.5%) due to token truncation.

## Data Structure by Source

### Test Set Analysis

| Source | Items | Avg Chars | Max Chars | Avg Tokens | Avg Periods | Data Type |
|--------|-------|-----------|-----------|------------|-------------|-----------|
| hirogaru | 78 | 63.8 | 145 | 11.6 | 2.6 | Sentence |
| kahoku | 49 | 145.0 | 319 | 19.1 | 3.7 | Paragraph |
| matcha | 497 | 443.6 | 8831 | 25.5 | 6.3 | Article |
| nhk | 333 | 48.5 | 168 | 8.8 | 1.6 | Sentence |

### Items Exceeding Single-Sentence Length

| Source | Items | >150 chars | % | >300 chars | % | Multiple 。 | % |
|--------|-------|------------|---|------------|---|------------|---|
| hirogaru | 78 | 0 | 0.0% | 0 | 0.0% | 67 | 85.9% |
| kahoku | 49 | 22 | 44.9% | 1 | 2.0% | 45 | 91.8% |
| matcha | 497 | 105 | 21.1% | 45 | 9.1% | 114 | 22.9% |
| nhk | 333 | 1 | 0.3% | 0 | 0.0% | 147 | 44.1% |

## Detailed Per-Source Analysis

### HIROGARU

**Classification**: Sentence

| Metric | Value |
|--------|-------|
| Item count | 78 |
| Character length (avg) | 63.8 |
| Character length (median) | 62.5 |
| Character length (max) | 145 |
| Character length (stdev) | 29.1 |
| Tokens (avg) | 11.6 |
| Tokens (total) | 902 |
| Japanese periods (avg) | 2.6 |
| Items >150 chars | 0 (0.0%) |
| Items with multiple sentences | 67 (85.9%) |

**Period count distribution:**

| Periods | Count |
|---------|-------|
| 1 | 11 |
| 2 | 29 |
| 3 | 25 |
| 4 | 9 |
| 5 | 2 |
| 6 | 2 |

### KAHOKU

**Classification**: Paragraph

| Metric | Value |
|--------|-------|
| Item count | 49 |
| Character length (avg) | 145.0 |
| Character length (median) | 140.0 |
| Character length (max) | 319 |
| Character length (stdev) | 66.2 |
| Tokens (avg) | 19.1 |
| Tokens (total) | 938 |
| Japanese periods (avg) | 3.7 |
| Items >150 chars | 22 (44.9%) |
| Items with multiple sentences | 45 (91.8%) |

**Period count distribution:**

| Periods | Count |
|---------|-------|
| 0 | 3 |
| 1 | 1 |
| 2 | 7 |
| 3 | 13 |
| 4 | 10 |
| 5 | 8 |
| 6 | 4 |
| 7 | 2 |
| 8 | 1 |

### MATCHA

**Classification**: Article

| Metric | Value |
|--------|-------|
| Item count | 497 |
| Character length (avg) | 443.6 |
| Character length (median) | 40.0 |
| Character length (max) | 8831 |
| Character length (stdev) | 1358.7 |
| Tokens (avg) | 25.5 |
| Tokens (total) | 12650 |
| Japanese periods (avg) | 6.3 |
| Items >150 chars | 105 (21.1%) |
| Items with multiple sentences | 114 (22.9%) |

**Period count distribution:**

| Periods | Count |
|---------|-------|
| 0 | 218 |
| 1 | 165 |
| 2 | 33 |
| 3 | 31 |
| 4 | 4 |
| 6 | 1 |
| 11 | 1 |
| 12 | 1 |
| 19 | 1 |
| 22 | 1 |
| ... | (truncated, 41 unique values) |

### NHK

**Classification**: Sentence

| Metric | Value |
|--------|-------|
| Item count | 333 |
| Character length (avg) | 48.5 |
| Character length (median) | 45.0 |
| Character length (max) | 168 |
| Character length (stdev) | 24.5 |
| Tokens (avg) | 8.8 |
| Tokens (total) | 2934 |
| Japanese periods (avg) | 1.6 |
| Items >150 chars | 1 (0.3%) |
| Items with multiple sentences | 147 (44.1%) |

**Period count distribution:**

| Periods | Count |
|---------|-------|
| 0 | 1 |
| 1 | 185 |
| 2 | 114 |
| 3 | 25 |
| 4 | 6 |
| 5 | 1 |
| 6 | 1 |

## Training Data Analysis

| Source | Items | Avg Chars | Total Tokens | Data Type |
|--------|-------|-----------|--------------|-----------|
| hirogaru | 352 | 61.4 | 3572 | Sentence |
| kahoku | 242 | 134.6 | 4416 | Paragraph |
| matcha | 2151 | 476.0 | 58967 | Article |
| nhk | 1613 | 46.9 | 13671 | Sentence |
| **TOTAL** | **4358** | - | **80626** | - |

## Impact on T5 v3 Accuracy

The data structure mismatch explains the T5 v3 accuracy discrepancy:

| Source | Accuracy | Avg Chars | Issue |
|--------|----------|-----------|-------|
| NHK | 82.1% | ~48 | None - proper sentence data |
| Hirogaru | 80.8% | ~64 | None - proper sentence data |
| Kahoku | 60.2% | ~145 | Partial - paragraph level |
| MATCHA | 32.5% | ~444 | Severe - article level, token truncation |

**Root cause**: T5 model uses `max_length=256` tokens. MATCHA articles exceed this,
causing truncation. The model correctly annotates visible text but cannot predict
tokens beyond the context window.

## Recommendations for v4

1. **Implement sentence segmentation** for MATCHA and Kahoku sources
2. **Split on Japanese sentence boundaries**: 。！？
3. **Reassign tokens** to segmented sentences (preserve total count)
4. **Verify uniform structure** before training (all items <100 chars avg)
5. **Rebuild splits** with consistent sentence-level granularity

## Segmentation Rules

```python
SENTENCE_ENDINGS = ['。', '！', '？']
# Split text at these boundaries
# Assign tokens to sentences based on character position
# Handle edge cases: quotes, parentheses, inline readings
```

---

*Generated by scripts/analyze_data_structure.py*