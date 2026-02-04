# T5 v4 Segmentation Report: Data Structure Fix

## Executive Summary

T5 v4 validates the hypothesis that **data structure mismatch** was the primary cause of poor performance on MATCHA and Kahoku sources in v3. By implementing sentence-level segmentation, we achieved:

- **MATCHA: 32.5% → 60.8%** (+28.3 percentage points, nearly doubled)
- **Kahoku: 60.2% → 71.9%** (+11.7 percentage points)
- **NHK: 82.1% → 84.2%** (+2.1 percentage points)
- **Hirogaru: 80.8% → 82.7%** (+1.9 percentage points)

## Problem Analysis

### v3 Data Structure Issue

| Source | v3 Avg Chars | v3 Data Type | v3 Accuracy |
|--------|--------------|--------------|-------------|
| NHK | 48.5 | Sentence | 82.1% |
| Hirogaru | 63.8 | Sentence | 80.8% |
| Kahoku | 145.0 | Paragraph | 60.2% |
| MATCHA | 443.6 | Article | 32.5% |

The model was trained with `max_length=128` tokens, causing:
1. Long MATCHA articles were truncated, missing most ground truth tokens
2. Model learned to annotate partial text, not complete sentences
3. Validation loss didn't reflect actual annotation quality

### v4 Solution: Sentence Segmentation

Split all data on Japanese sentence boundaries (。！？) while preserving token assignments:

| Source | v4 Avg Chars | v4 Data Type | v4 Accuracy |
|--------|--------------|--------------|-------------|
| NHK | ~48 | Sentence | 84.2% |
| Hirogaru | ~64 | Sentence | 82.7% |
| Kahoku | ~39 | Sentence | 71.9% |
| MATCHA | ~70 | Sentence | 60.8% |

## Dataset Statistics

### Data Expansion from Segmentation

| Split | v3 Items | v4 Items | Growth | Token Preservation |
|-------|----------|----------|--------|-------------------|
| Train | 4,358 | 12,261 | +181% | 99.98% |
| Val | 906 | 2,685 | +196% | 99.96% |
| Test | 957 | 2,755 | +188% | 100.00% |

### Test Set Distribution

| Source | Sentences | Tokens | % of Total |
|--------|-----------|--------|------------|
| MATCHA | 2,161 | 12,650 | 72.6% |
| NHK | 333 | 2,934 | 16.8% |
| Kahoku | 183 | 938 | 5.4% |
| Hirogaru | 78 | 902 | 5.2% |

## Training Results

### Configuration

| Parameter | Value |
|-----------|-------|
| Base Model | sonoisa/t5-base-japanese |
| Train Samples | 11,593 |
| Val Samples | 2,535 |
| Epochs (requested) | 10 |
| Epochs (completed) | 6 (early stopping) |
| Batch Size | 8 |
| Learning Rate | 3e-4 |
| Early Stopping Patience | 3 |
| Training Time | 53.5 minutes |

### Validation Loss by Epoch

| Epoch | Eval Loss | Status |
|-------|-----------|--------|
| 1 | 0.196 | - |
| 2 | 0.160 | Improving |
| 3 | **0.147** | **Best** |
| 4 | 0.159 | Overfitting starts |
| 5 | 0.170 | Patience 1 |
| 6 | 0.184 | Patience 3 → Stop |

Best checkpoint: epoch 3 (checkpoint-4350)

## Evaluation Results

### Full Test Set (2,755 sentences, 17,424 tokens)

| Source | Correct | Total | Accuracy | vs v3 |
|--------|---------|-------|----------|-------|
| NHK | 2,469 | 2,934 | **84.2%** | +2.1% |
| Hirogaru | 746 | 902 | **82.7%** | +1.9% |
| Kahoku | 674 | 938 | **71.9%** | +11.7% |
| MATCHA | 7,688 | 12,650 | **60.8%** | +28.3% |
| **Overall** | **11,577** | **17,424** | **66.4%** | - |

### Comparison with All Methods

| Method | Overall | NHK | Notes |
|--------|---------|-----|-------|
| Lindera baseline | - | 62.7% | Dictionary lookup |
| T5 v1 (hiragana) | - | 61.8% | Hiragana output format |
| Sudachi Mode C | - | 63.5% | Morphological analyzer |
| T5 v2 (bracket) | - | 80.4% | NHK-only training |
| T5 v3 (bracket, multi) | 44.9%* | 82.1% | Multi-source, mixed structure |
| **T5 v4 (segmented)** | **66.4%** | **84.2%** | Multi-source, uniform sentences |

*v3 overall estimated on same test distribution

### v3 vs v4 on Same Test Set (Estimated)

| Source | v3 Tokens Correct | v4 Tokens Correct | Improvement |
|--------|-------------------|-------------------|-------------|
| NHK | 2,409 (82.1%) | 2,469 (84.2%) | +60 |
| Hirogaru | 729 (80.8%) | 746 (82.7%) | +17 |
| Kahoku | 565 (60.2%) | 674 (71.9%) | +109 |
| MATCHA | 4,111 (32.5%) | 7,688 (60.8%) | +3,577 |
| **Total** | **7,814 (44.8%)** | **11,577 (66.4%)** | **+3,763** |

**+21.6 percentage point improvement** from sentence segmentation alone.

## Key Findings

### 1. Data Structure > Data Quantity

T5 v3 had 4x more tokens than v2 but only marginal improvement on NHK because:
- The additional tokens were in truncated form (MATCHA articles)
- Model couldn't learn from data it never saw during training

### 2. Segmentation Preserves Information

Token preservation rate >99.96% proves that sentence segmentation:
- Doesn't lose annotation information
- Correctly reassigns tokens to their containing sentences
- Maintains data integrity while fixing structure

### 3. Source-Specific Patterns

MATCHA still underperforms NHK/Hirogaru (60.8% vs 82-84%) due to:
- Different annotation conventions
- Broader vocabulary (travel/tourism domain)
- More proper nouns and place names

### 4. Early Stopping Worked

Model began overfitting at epoch 4. Best performance at epoch 3 with:
- Eval loss: 0.147
- Training time saved: ~40% (6 vs 10 epochs)

## Remaining Challenges

### MATCHA Gap Analysis (60.8% accuracy)

Common error patterns observed:
1. **Merged tokens**: Model outputs `四季富士山[ふじさん]` instead of separate annotations
2. **Number+Counter**: `2時間[じかん]` instead of just `時間[じかん]`
3. **Place names**: Combined readings like `富士吉田市[ふじよしだし]` instead of `富士[ふじ]` + `吉田市[よしだし]`

These suggest MATCHA ground truth uses different tokenization boundaries than NHK.

## Recommendations

### For Production Use

1. **Use T5 v4** for general Japanese text annotation
2. **NHK-style text**: Expect ~84% accuracy
3. **Travel/tourism text**: Expect ~61% accuracy

### For Future Improvement

1. **Normalize tokenization boundaries** across sources before training
2. **Investigate MATCHA annotation patterns** to understand conventions
3. **Consider ensemble approach** using source-specific models

## Files Generated

```
models/t5-furigana-v4/           # Trained model weights
data/splits_v4/                  # Sentence-segmented data
data/bracket_format_v4/          # Training format data
results/t5_v4_training_log.json  # Full training metrics
results/t5_v4_predictions_full.json  # Test predictions
results/t5_v4_segmentation_report.md # This report
```

## Conclusion

T5 v4 validates that **uniform data structure** is critical for multi-source training. Sentence segmentation alone improved overall accuracy from ~44.8% to 66.4%, with MATCHA nearly doubling from 32.5% to 60.8%.

The remaining performance gap between sources (NHK: 84% vs MATCHA: 61%) is likely due to annotation convention differences, not model capacity. Future work should focus on understanding and normalizing these conventions.
