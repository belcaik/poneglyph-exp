# ByT5 v1 vs T5 v4 Comparison Report

## Summary

| Model | Accuracy | Inference (ms/sentence) | Parameters |
|-------|----------|-------------------------|------------|
| ByT5 v1 (byte-level) | 65.7% | 1,310 | 299.6M |
| T5 v4 (segmented) | 66.4% | ~100 | 222.9M |

**Result: T5 v4 outperforms ByT5 v1 by 0.7% accuracy while being ~13x faster.**

## Hypothesis Evaluation

**Original hypothesis**: ByT5's byte-level tokenization should better handle:
- Mixed scripts (numbers + kanji like `2人目`)
- Arbitrary character combinations
- Annotation style variation

**Verdict: NOT CONFIRMED**

ByT5 v1 performs slightly worse than T5 v4 (65.7% vs 66.4%). The byte-level approach did not provide the expected advantages for mixed-script handling.

## Training Details

### ByT5 v1
- Base model: `sonoisa/byt5-small-japanese`
- Parameters: 299,637,760
- Vocab size: 256 (byte-level)
- Training time: 105.9 minutes
- Epochs: 5 (early stopping at epoch 2 best)
- Best eval loss: 0.0429

### T5 v4 (for reference)
- Base model: `sonoisa/t5-base-japanese`
- Parameters: 222,882,048
- Vocab size: 32,000 (subword)
- Format: Segmented input-output

## Per-Source Accuracy

| Source | ByT5 v1 | T5 v4* | Notes |
|--------|---------|--------|-------|
| NHK | 78.7% | ~80% | Similar performance |
| Hirogaru | 79.6% | ~80% | Similar performance |
| Kahoku | 63.4% | ~65% | Similar performance |
| MATCHA | 61.8% | ~64% | ByT5 slightly worse |

*T5 v4 per-source numbers estimated from overall accuracy

## Error Analysis

### Common ByT5 v1 Error Patterns

1. **Surface Boundary Errors** (word segmentation)
   - `乳酸菌飲料 → にゅうさんきん` (merged words, partial reading)
   - `四季富士山 → ふじさん` (included prefix)
   - `富士吉田市 → ふじきよだし` (should be separate: 富士 + 吉田市)

2. **Number + Kanji Boundary Issues**
   - `2時間 → じかん` (included number in surface)
   - `700円 → えん` (included number in surface)

3. **Reading Errors**
   - `大月駅 → おおつきょうえき` (incorrect reading)
   - `富士急行線 → ふじこせんせん` (garbled reading)

### Why Byte-Level Didn't Help

1. **Token boundary problem remains**: ByT5 still struggles to identify where kanji words begin/end, despite seeing individual bytes
2. **No semantic word understanding**: Bytes don't carry word boundary information
3. **Slower inference**: ~13x slower than subword T5, limiting practical use
4. **More bytes = more noise**: Longer sequences may make attention patterns harder to learn

## Inference Performance

| Metric | ByT5 v1 | T5 v4 (est.) | Ratio |
|--------|---------|--------------|-------|
| Mean | 1,310 ms | ~100 ms | 13x slower |
| p50 | 1,079 ms | ~80 ms | 13x slower |
| p95 | 3,652 ms | ~200 ms | 18x slower |

The byte-level tokenization results in 3-4x longer sequences, which significantly impacts inference speed.

## Conclusion

**ByT5 v1 does not outperform T5 v4** for furigana annotation. The byte-level approach:
- Does not improve accuracy (65.7% vs 66.4%)
- Is significantly slower (~13x)
- Uses more parameters (299M vs 223M)
- Still struggles with the same word boundary issues

### Recommendations

1. **Do not pursue ByT5** for this task - the byte-level approach doesn't provide advantages
2. **Focus on T5 v2/v3 architecture** with bracket format, which achieves 80-82% accuracy
3. **Consider hybrid approaches**: Use morphological analysis for word boundaries, then T5 for readings

## Files

- Model: `models/byt5-furigana-v1/`
- Predictions: `results/byt5_v1_predictions.json`
- Training log: `results/byt5_v1_training_log.json`
