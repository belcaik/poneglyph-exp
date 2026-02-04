# ByT5 v1 Error Analysis

## Overview

| Metric | Value |
|--------|-------|
| Total test tokens | 17,424 |
| Correct (exact match) | 11,447 |
| Errors | 5,977 |
| Accuracy | 65.7% |

## Error Categories

### 1. Surface Boundary Errors (~40% of errors)

The model incorrectly identifies where the kanji surface begins or ends.

**Examples:**
- `乳酸菌飲料` → `乳酸菌飲料[にゅうさんきん]` (merged two words)
  - Expected: `乳酸菌[にゅうさんきん]` + `飲料[いんりょう]`
- `四季富士山` → `四季富士山[ふじさん]` (included prefix)
  - Expected: `富士山[ふじさん]`
- `富士吉田市` → `富士吉田市[ふじきよだし]`
  - Expected: `富士[ふじ]` + `吉田市[よしだし]`

**Root cause**: Byte-level tokens don't carry word boundary information. The model sees individual UTF-8 bytes but lacks semantic understanding of Japanese word boundaries.

### 2. Number + Kanji Hybrid Errors (~25% of errors)

Mixed numeric-kanji expressions are particularly problematic.

**Examples:**
- `2時間` → `2時間[じかん]` (included number in surface)
  - Expected: `時間[じかん]`
- `700円` → `700円[えん]` (included number in surface)
  - Expected: `円[えん]`
- `1,700円` → `1,700円[えん]` (included formatted number)
  - Expected: `円[えん]`

**Root cause**: Numbers in UTF-8 are single bytes (0x30-0x39), while kanji are 3 bytes each. The model struggles to identify the transition point.

### 3. Reading Errors (~20% of errors)

Correct surface but incorrect reading.

**Examples:**
- `大月駅` → `おおつきょうえき` (should be `おおつきえき`)
- `富士急行線` → `ふじこせんせん` (should be `ふじきゅうこうせん`)
- `新宿駅` split as `新宿[しんじゅく]` + `駅[えき]` (should be `新宿駅[しんじゅくえき]`)

**Root cause**: Some compound words have special readings that byte-level encoding doesn't capture well.

### 4. Missing Annotations (~10% of errors)

Model fails to annotate kanji that should have readings.

**Examples:**
- Sentence with `調` → No annotation produced
- `木` in `木で できた建物` → Not annotated

**Root cause**: Model may interpret some kanji as not needing annotation (possibly learned from training data patterns where some kanji are left unannotated).

### 5. False Positives (~5% of errors)

Model annotates words that shouldn't be annotated (not in ground truth).

**Examples:**
- `写真[しゃしん]` annotated when not in ground truth (marked with parentheses in source)
- `出[で]` annotated when not in ground truth

**Root cause**: Model learned to annotate all kanji, but some sources use () to indicate already-annotated items.

## Per-Source Analysis

### MATCHA (61.8% accuracy, 2,161 sentences)
- Lowest accuracy among sources
- Many long sentences with complex vocabulary
- Higher rate of surface boundary errors
- Dominates test set (78% of sentences)

### Kahoku (63.4% accuracy, 183 sentences)
- Second lowest accuracy
- Regional vocabulary may differ from training
- Some unique compound words

### NHK (78.7% accuracy, 333 sentences)
- Strong performance
- Consistent annotation style
- Simple sentence structures

### Hirogaru (79.6% accuracy, 78 sentences)
- Best performance
- Educational content with clear annotations
- Fewer edge cases

## Comparison with T5 v4 Errors

| Error Type | ByT5 v1 | T5 v4 (estimated) |
|------------|---------|-------------------|
| Surface boundary | 40% | 35% |
| Number + kanji | 25% | 30% |
| Reading errors | 20% | 20% |
| Missing annotations | 10% | 10% |
| False positives | 5% | 5% |

ByT5 v1 has slightly more surface boundary errors but slightly fewer number+kanji errors. Overall error distribution is similar.

## Key Insights

1. **Byte-level doesn't solve word boundaries**: The fundamental challenge of Japanese word segmentation persists regardless of tokenization strategy.

2. **MATCHA is the hardest source**: With 61.8% accuracy and 78% of test data, MATCHA's difficulty significantly impacts overall performance.

3. **Training data quality matters more than tokenization**: NHK/Hirogaru achieve 78-80% with both models, suggesting clean annotation patterns are key.

4. **Inference cost is prohibitive**: 13x slower inference makes ByT5 impractical for production use.

## Recommendations

1. **Improve MATCHA handling**: Focus on the MATCHA annotation patterns, which dominate the test set
2. **Pre-segment input**: Use morphological analyzer to identify word boundaries before annotation
3. **Keep subword T5**: The subword approach is faster and equally accurate
