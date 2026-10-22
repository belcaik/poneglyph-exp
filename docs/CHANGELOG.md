# Changelog

## [LLM benchmark v2 + Poneglyph v1 dataset] - 2026-03

- LLM benchmark on 100 sentences: Claude v2 97.9%, Gemini Flash 97.2%, Claude v1 96.6%,
  Qwen 7B 69.0% reading accuracy. Strict "every kanji must be annotated" prompt removed
  parse failures and reached 100% kanji coverage.
- `data/poneglyph_v1/`: ~14K subtitle sentences annotated by LLMs under
  `docs/poneglyph_conventions.md` (report: `results/dataset_v1_report.md`).

## [SpanReader v1/v2] - 2026-03

- DETR-style span queries over a DeBERTa v3 JP encoder (188.5M params).
- v1 span F1 0.500: chars inside one sub-token pooled to identical vectors.
- v2 span F1 0.869 after intra-token positional encoding and loss rebalancing;
  reading accuracy 51.1%.

## [Span Detector v1] - 2026-02

- BIO span tagger on v7 data: span F1 0.949 (test).
- Pipeline with BERT v2: 82.0% end-to-end, bottlenecked by OOV spans (12.7%).

## [BERT v2] - 2026-02

- Dictionary-constrained reading classification given gold spans: 98.8% (v6),
  98.6% val on v7. 70% of errors are OOV surfaces.

## [v7] - 2026-02

- All sources converted from stem-only to morpheme-complete annotation
  (`data/splits_v7_normalized/`): ~23K tokens expanded with okurigana, 0.31% validation
  error rate.
- `《》` delimiter: neutral for T5 v7 (86.6%), -4.7pp for ByT5 v3 (84.4%).

## [v6] - 2026-02-10

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

## [v5] - 2026-02-09

### Added UD Japanese Gold Data

Integrated UD_Japanese-GSD (8,036 sentences) and UD_Japanese-PUD (996 sentences)
from Universal Dependencies CoNLL-U files.

### Results

| Model | Training Samples | Accuracy (v4 test) |
|-------|------------------|--------------------|
| T5 v4 | 11,593 | 66.4% |
| T5 v5 | 18,817 | 67.6% |

Small improvement on v4 test set, but v5 test accuracy was 78.9% (comparable set).

## [v4] - 2026-02-08

### Sentence Segmentation

Split articles/paragraphs into individual sentences before training.
MATCHA accuracy jumped +28% from this change alone.

### Results

| Model | Training Samples | Eval Loss |
|-------|------------------|-----------|
| T5 v3 (unsegmented) | 11,593 | — |
| T5 v4 (segmented) | 11,593 | 0.147 |
