# BERT v1: Token Classification for Furigana

## Approach

Unlike T5 (seq2seq), BERT uses token classification:
- Each character receives a label
- For kanji: label = hiragana reading portion
- For non-kanji: label = "O" (no annotation)

## Architecture

- Model: cl-tohoku/bert-base-japanese-char (~110M parameters)
- Task: Token classification (each character classified independently)
- Labels: Dynamic vocabulary of reading portions + "O"

## Label Scheme

For multi-kanji compounds, readings are split evenly:
- 今日→きょう: 今→"きょ", 日→"う"
- 東京→とうきょう: 東→"とうき", 京→"ょう"
- 食→た: 食→"た"

## Challenges

1. **Reading alignment**: Multi-character kanji need consistent reading splits
2. **Context dependency**: 今日→きょう vs 今+日→いま+ひ (BERT attention handles this)
3. **Label vocabulary size**: ~2,000-3,000 unique labels from training data
4. **Span reconstruction**: Converting per-char predictions back to compound tokens

## Configuration

- Hyperparameters:
  - Batch size: 16
  - Learning rate: 2e-5
  - Max sequence length: 512 characters
  - Epochs: 10 (with early stopping, patience=3)
  - Warmup steps: 100
  - Weight decay: 0.01

## Comparison baseline

| Model | Architecture | Accuracy |
|-------|-------------|----------|
| T5 v6 | seq2seq | 86.4% |
| ByT5 v2 | byte seq2seq | TBD |
| BERT v1 | token classification | 66.3% |

## Results

### Training
- Training time: 26.2 minutes (10 epochs, no early stopping triggered)
- Best eval loss: 0.2798 (epoch 10)
- 90.7M parameters, 2,821 label classes

### Eval Loss Progression
| Epoch | Eval Loss |
|-------|-----------|
| 1     | 0.8186    |
| 2     | 0.5743    |
| 3     | 0.4796    |
| 4     | 0.3969    |
| 5     | 0.3507    |
| 6     | 0.3186    |
| 7     | 0.2999    |
| 8     | 0.2886    |
| 9     | 0.2822    |
| 10    | 0.2798    |

### Comparable Test Set (1,498 sentences, 12,558 tokens)
- **Overall accuracy: 66.3%**
- Inference speed: 19.7ms mean, 20.2ms p50, 26.1ms p95

### Per-Source Accuracy
| Source | Accuracy | Tokens |
|--------|----------|--------|
| kahoku | 89.8% | 938 |
| hirogaru | 87.7% | 902 |
| nhk | 86.7% | 2,934 |
| ud_pud | 60.9% | 913 |
| ud_gsd | 52.2% | 6,871 |

### Analysis

The token classification approach has structural weaknesses:

1. **Boundary detection failure**: The model merges adjacent kanji into single tokens
   (e.g., 先制+点 → 先制点), causing mismatches with ground truth tokenization
2. **Reading alignment artifacts**: Even-split reading assignment creates unnatural
   sub-readings that don't correspond to real morphemes
3. **UD data struggle**: UD sources have more complex compound words, exposing the
   boundary detection issue (52-61% vs 87-90% on simpler sources)
4. **Architecture mismatch**: Token classification is better suited for tasks with
   fixed label sets; furigana readings are essentially a generation task

### Conclusion

Character-level token classification is fundamentally unsuitable for furigana annotation.
The seq2seq approach (T5) handles compound boundaries and reading generation naturally.
T5 v6 achieves 86.4% vs BERT v1's 66.3% — a 20pp gap that reflects architectural fit.
