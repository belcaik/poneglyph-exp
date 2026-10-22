# Span Detector v1: BIO Tagging for Morpheme Boundary Detection

## Hypothesis

BERT v2 achieves 98.8% accuracy on reading classification when given ground-truth spans.
The main bottleneck for a production pipeline is **span detection** — identifying which
character sequences in raw text are annotatable morphemes requiring furigana.

A BERT-based BIO tagger trained on character-level labels from the v7 normalized data
should be able to detect these spans with F1 >= 0.92, enabling an end-to-end pipeline
(span detector + BERT v2 reading classifier) that exceeds ByT5 v2's 89.1% accuracy.

## Key Insight

The task decomposes into two orthogonal subproblems:
1. **Where** are the annotatable morphemes? (span detection — this experiment)
2. **What** is the reading? (reading classification — BERT v2, already solved)

## Architecture

- **Base model**: `tohoku-nlp/bert-base-japanese-v3` (same as BERT v2)
- **Task**: Character-level BIO sequence tagging
- **Labels**: B-SPAN (start of morpheme), I-SPAN (continuation), O (outside)
- **Head**: Linear(768, 3) on each token, with character-to-token alignment
- **Parameters**: 111.2M total (111.2M BERT + 2.3K head)

## Data

- **Source**: `data/splits_v7_normalized/{train,val,test}.json`
- **Conversion**: Each sentence's text is character-level labeled using token surface spans
- **Train**: 10,413 sentences (~86K tokens)
- **Val**: 1,303 sentences (~11K tokens)
- **Test**: 1,304 sentences (~11K tokens)
- **Label distribution**: O=56.5%, B-SPAN=20.0%, I-SPAN=23.5% (surprisingly balanced, 1.3:1 ratio)

## Training

- Epochs: 15 (early stopping on val span F1, patience 5)
- Batch size: 16
- Learning rate: 2e-5 (AdamW, linear warmup 10%, cosine decay)
- Gradient clipping: 1.0
- Max sequence length: 256
- Training time: 26.1 minutes (RTX 3060)
- Best epoch: 10 (span F1 = 0.9744)

## Results

### Span Detection (Stage 1)

| Metric | Target | Achieved |
|--------|--------|----------|
| Span F1 | >= 0.92 | **0.9490** |
| Span precision | >= 0.90 | **0.9494** |
| Span recall | >= 0.90 | **0.9486** |
| Val span F1 | — | **0.9744** |
| Token accuracy | — | 99.0% |

**Per-source span F1:**

| Source | Precision | Recall | F1 | Correct/Gold |
|--------|-----------|--------|----|-------------|
| ud_pud | 0.9755 | 0.9755 | 0.9755 | 876/898 |
| ud_gsd | 0.9541 | 0.9557 | 0.9549 | 6543/6846 |
| nhk | 0.9545 | 0.9475 | 0.9510 | 1949/2057 |
| hirogaru | 0.9076 | 0.9109 | 0.9093 | 501/550 |
| kahoku | 0.8830 | 0.8708 | 0.8768 | 566/650 |

**Span length recall:**

| Length | Recall | Count |
|--------|--------|-------|
| 1 char | 92.8% | 2,927 |
| 2 char | 97.0% | 5,400 |
| 3 char | 93.2% | 1,250 |
| 4 char | 94.2% | 811 |
| 5 char | 92.7% | 452 |
| 6+ char | 81.4% | 161 |

Latency: mean=15.4ms, p50=16.0ms, p95=18.5ms

### End-to-End Pipeline (Stage 1 + Stage 2)

| Metric | Target | Achieved |
|--------|--------|----------|
| Pipeline accuracy | >= 90% | **82.0%** |

**Per-source pipeline accuracy:**

| Source | Accuracy | Matches/Total |
|--------|----------|---------------|
| nhk | 90.5% | 1,862/2,057 |
| ud_pud | 85.1% | 764/898 |
| hirogaru | 84.4% | 464/550 |
| kahoku | 80.6% | 524/650 |
| ud_gsd | 78.9% | 5,402/6,846 |

Pipeline latency: mean=41.5ms, p50=35.5ms, p95=101.2ms

### Error Decomposition

| Error Type | Count | % of Gold |
|------------|-------|-----------|
| Wrong reading (OOV + disambig.) | 1,419 | 12.9% |
| Missed span (FN) | 566 | 5.1% |
| Spurious span (FP) | 556 | 5.1% |

- ~90% of "wrong reading" errors are **OOV** (surface not in reading dictionary, pred = empty)
- ~10% are true disambiguation errors (BERT v2 predicts wrong reading)
- Accuracy ceiling with perfect spans: **87.1%**
- Accuracy ceiling with perfect readings: **94.9%**

### Method Comparison

| Method | Accuracy | Notes |
|--------|----------|-------|
| BERT v2 (GT spans) | 98.8% | Upper bound, oracle spans |
| ByT5 v2 (seq2seq) | 89.1% | Best seq2seq baseline |
| T5 v7 (seq2seq) | 86.6% | Word-piece seq2seq |
| **SpanDet v1 + BERT v2** | **82.0%** | Two-stage pipeline |
| BERT v1 (token class.) | 66.3% | Token classification |

## Analysis

### Hypothesis: PARTIALLY CONFIRMED

1. **Span detection succeeds** — F1=0.949 on test (target was 0.92)
2. **Pipeline falls short** — 82.0% accuracy (target was 90%, ByT5 v2 baseline is 89.1%)

### Root Cause: Surface Mismatch → OOV

The two-stage pipeline introduces an **interface mismatch** between stages:

- The span detector outputs morpheme-complete surfaces (e.g., `確保して`, `訪問しました`)
- The reading dictionary was built from training data's gold annotations
- 12.7% of correctly-detected spans have surfaces not seen in training → OOV → empty prediction
- OOV surfaces are primarily: inflected forms, compounds, proper nouns

This is a fundamental limitation of the dictionary-constrained approach when used with
predicted (rather than oracle) spans. The reading dictionary's coverage depends on exact
surface form matching, and the span detector inevitably produces some novel surface forms.

### Why Seq2seq (ByT5) Avoids This

Seq2seq models generate readings character-by-character directly from the input text.
They don't require an explicit span detection step or a fixed reading dictionary.
This architectural difference means they gracefully handle novel surfaces — they can
generate readings for words never seen in training by generalizing from character patterns.

### Weaknesses by Source

- **kahoku** (F1=0.877): Smallest training representation, highest span detection error
- **hirogaru** (F1=0.909): Educational text with unusual compound boundaries
- **ud_gsd** (78.9% pipeline): Largest test set, most diverse vocabulary → most OOV

## Conclusion

The two-stage decomposition (span detection + reading classification) is architecturally
clean and each stage performs well independently:
- Span detector: F1=0.949 (excellent)
- Reading classifier: 98.6% on in-vocabulary items (excellent)

However, the **interface between stages** creates an OOV bottleneck that limits end-to-end
accuracy to 82%. To close the gap with ByT5 v2 (89.1%), the pipeline would need either:
1. An OOV fallback strategy (e.g., character-level reading generation for unknown surfaces)
2. A much larger reading dictionary (requires more training data diversity)
3. A unified model that doesn't require exact surface matching

**Recommendation**: For production use, ByT5 v2 remains the better choice at 89.1% accuracy.
The two-stage pipeline's 82% is informative but not competitive. The BERT v2 reading
classifier remains the gold standard at 98.8% — the challenge is closing the span detection gap.

## Figures

- `results/figures/fig1_training_curves.png` — Training loss and val span F1 over epochs
- `results/figures/fig2_pipeline_comparison.png` — Pipeline accuracy comparison across methods
- `results/figures/fig3_per_source.png` — Per-source span F1 vs pipeline accuracy
- `results/figures/fig4_error_breakdown.png` — Error type distribution and span length recall
