# Changelog

## [v6] - 2025-02-10

### Major Finding: Data Quality > Data Quantity

Removing MATCHA dataset (13,713 sentences with 66.2% annotation coverage)
improved model accuracy by 7.5 percentage points despite reducing training
data by 45%.

### Results Summary

| Model | Training Samples | Accuracy | Change |
|-------|------------------|----------|--------|
| T5 v5 (with MATCHA) | 18,817 | 78.9% | baseline |
| T5 v6 (no MATCHA) | 10,413 | 86.4% | +7.5pp |

### Per-Source Improvements

| Source | v5 | v6 | Delta |
|--------|-----|-----|-------|
| Kahoku | 74.5% | 88.0% | +13.5pp |
| UD GSD | 75.4% | 84.3% | +8.9pp |
| UD PUD | 81.7% | 89.2% | +7.5pp |
| Hirogaru | 84.9% | 90.5% | +5.6pp |
| NHK | 85.5% | 88.8% | +3.3pp |

### Root Cause Analysis

MATCHA data had two critical issues:
1. **Low annotation coverage (66.2%)** - Only 2/3 of kanji had furigana annotations,
   teaching the model that partial annotation is acceptable
2. **Bracket collisions (256 sentences)** - JavaScript artifacts like `[index]`
   leaked through the HTML parser, confusing the bracket-based annotation format

### Lessons Learned

1. Always measure annotation coverage before including a data source
2. Validate that delimiter characters (e.g., `[]`) don't appear in source text
3. More data can hurt if quality is poor - the model learns bad patterns

## [v5] - 2025-02-09

### Added UD Japanese Gold Data

Integrated UD_Japanese-GSD (8,036 sentences) and UD_Japanese-PUD (996 sentences)
from Universal Dependencies CoNLL-U files.

### Results

| Model | Training Samples | Accuracy (v4 test) |
|-------|------------------|--------------------|
| T5 v4 | 11,593 | 66.4% |
| T5 v5 | 18,817 | 67.6% |

Small improvement on v4 test set, but v5 test accuracy was 78.9% (comparable set).

## [v4] - 2025-02-08

### Sentence Segmentation

Split articles/paragraphs into individual sentences before training.
MATCHA accuracy jumped +28% from this change alone.

### Results

| Model | Training Samples | Eval Loss |
|-------|------------------|-----------|
| T5 v3 (unsegmented) | 11,593 | — |
| T5 v4 (segmented) | 11,593 | 0.147 |
