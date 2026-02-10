# T5 v6 Experiment: MATCHA Exclusion

## Hypothesis
MATCHA's low annotation coverage (66.2%) and bracket collisions are introducing
noise that hurts model generalization. Excluding it should improve accuracy
despite reducing training data.

## Dataset composition

### v5 (baseline)
- NHK: ~2,284 sentences
- MATCHA: ~13,713 sentences (EXCLUDED in v6)
- Kahoku: ~1,198 sentences
- Hirogaru: ~506 sentences
- UD GSD: ~8,036 sentences
- UD PUD: ~996 sentences
- Total: ~26,733 sentences

### v6 (this experiment)
- NHK: ~2,284 sentences
- Kahoku: ~1,198 sentences
- Hirogaru: ~506 sentences
- UD GSD: ~8,036 sentences
- UD PUD: ~996 sentences
- Total: ~13,020 sentences (estimated)

## Training

### v5 (baseline)
- Bracket format samples: 18,817 train / 3,439 val
- Best eval loss: 0.132 (epoch 8)
- Training time: ~87.5 min

### v6 (this experiment)
- Bracket format samples: 10,413 train / 1,303 val
- Best eval loss: 0.138 (epoch 6)
- Early stopped at epoch 9 (patience=3)
- Training time: ~54.2 min
- 100% bracket conversion rate (vs 96% for v5 — zero skip rate without MATCHA)

## Evaluation

Comparable test set: 1,498 sentences from v5 test excluding MATCHA.
Both models evaluated on identical test data for fair comparison.

## Results

### Overall accuracy

| Model | Accuracy | Exact Matches | Ground Truth Tokens |
|-------|----------|---------------|---------------------|
| T5 v5 (with MATCHA) | **78.9%** | 9,904 | 12,558 |
| T5 v6 (no MATCHA) | **86.4%** | 10,850 | 12,558 |
| **Delta** | **+7.5pp** | **+946** | — |

### Per-source accuracy

| Source | v5 (with MATCHA) | v6 (no MATCHA) | Delta |
|--------|------------------|----------------|-------|
| hirogaru | 84.9% (766/902) | 90.5% (816/902) | +5.6pp |
| kahoku | 74.5% (699/938) | 88.0% (825/938) | +13.5pp |
| nhk | 85.5% (2510/2934) | 88.8% (2606/2934) | +3.3pp |
| ud_gsd | 75.4% (5183/6871) | 84.3% (5789/6871) | +8.9pp |
| ud_pud | 81.7% (746/913) | 89.2% (814/913) | +7.5pp |
| **Overall** | **78.9%** | **86.4%** | **+7.5pp** |

### Notable observations

1. **Every source improved** — MATCHA noise was dragging down accuracy across ALL domains
2. **Kahoku improved most** (+13.5pp) — newspaper text was most confused by MATCHA patterns
3. **45% less training data, 7.5pp better accuracy** — data quality >> data quantity
4. **Zero bracket collisions** in v6 data (vs 256 from MATCHA's `[index]` JS artifacts in v5)
5. **100% bracket conversion rate** in v6 (vs 96% in v5 — MATCHA had kanji-free sentences)

### Qualitative examples

- 婚活: v5 predicted さんかつ (wrong), v6 predicted こんかつ (correct)
- 辛うじて: v5 predicted つら (wrong), v6 predicted かろ (correct)
- Sentence 10 (17 tokens): v5 got 13/17, v6 got 17/17 (perfect)

## Conclusion

**Hypothesis validated.** MATCHA's low annotation coverage (66.2%) and bracket
collisions were introducing significant noise that hurt model generalization.

### Key findings
- Removing MATCHA improved accuracy by +7.5 percentage points despite losing 45% of training data
- The improvement was universal across all data sources, not just source-specific
- MATCHA's 256 bracket collisions (`[index]` JS artifacts) and 33.8% unannotated kanji
  were teaching the model to skip annotations and produce malformed bracket output

### Recommendations

1. **Never re-add MATCHA** without fixing:
   - Annotation coverage must be >95%
   - All `[...]` patterns must be validated as furigana (content is pure hiragana)

2. **For new data sources**, always check:
   - Annotation coverage (reject if <95%)
   - Delimiter collisions (search for `[` in raw text)
   - Domain diversity (avoid over-representing one style)

3. **Next experiments** to run on clean v6 data:
   - ByT5 v2: Retrain byte-level model without MATCHA noise
   - BERT token classification: Alternative architecture comparison
   - Delimiter change: Switch from `[]` to a delimiter not found in Japanese text
   - Expand with more high-quality sources meeting data quality checklist

### Model accuracy history

| Version | Train Samples | Eval Loss | Accuracy (comparable) | Notes |
|---------|--------------|-----------|----------------------|-------|
| T5 v4 | 11,593 | 0.147 | — | NHK+MATCHA+Kahoku+Hirogaru |
| T5 v5 | 18,817 | 0.132 | 78.9% | +UD data |
| T5 v6 | 10,413 | 0.138 | 86.4% | No MATCHA |
