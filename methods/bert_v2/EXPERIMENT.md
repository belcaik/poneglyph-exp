# BERT v2: Dictionary-Constrained Reading Classification

## Hypothesis

bert_v1 failed (66.3%) because character-level token classification is fundamentally
mismatched for furigana: variable-length readings can't be aligned to individual characters,
and the label vocabulary explodes combinatorially.

bert_v2 reframes furigana as **disambiguation, not generation**. Most kanji compounds have
only 2-5 valid readings in practice. Instead of generating arbitrary reading strings, we:
1. Use ground truth token spans (no boundary detection needed)
2. Look up candidate readings from a dictionary built from training data
3. Use BERT contextual embeddings to classify among candidates

This should achieve high accuracy because:
- The model only needs to distinguish between a small set of known readings
- BERT excels at contextual disambiguation (cf. WSD tasks)
- Unambiguous spans (1 candidate) are correct by construction
- The dictionary captures 95%+ of surface forms from the training distribution

## Architecture

```
Input: "今日は天気がいい。"  +  span: "今日" (pos 0-2)

                          ┌──────────────────────┐
   "今日は天気がいい。" → │  BERT Tokenizer      │
                          │  (subword tokens)     │
                          └──────────┬───────────┘
                                     ▼
                          ┌──────────────────────┐
                          │  BERT Encoder         │
                          │  (768-dim hidden)     │
                          └──────────┬───────────┘
                                     ▼
                   ┌─────────────────┴─────────────────┐
                   ▼                                   ▼
          ┌────────────────┐                 ┌────────────────┐
          │  Span tokens   │                 │  [CLS] token   │
          │  (mean pool)   │                 │  (global ctx)  │
          └───────┬────────┘                 └───────┬────────┘
                  ▼                                  ▼
          ┌───────────────────────────────────────────┐
          │           Concatenate (1536-dim)           │
          └─────────────────┬─────────────────────────┘
                            ▼
          ┌───────────────────────────────────────────┐
          │     Linear(1536, 768) + GELU + Dropout     │
          └─────────────────┬─────────────────────────┘
                            ▼
          ┌───────────────────────────────────────────┐
          │     Linear(768, vocab_size) → logits       │
          └─────────────────┬─────────────────────────┘
                            ▼
          ┌───────────────────────────────────────────┐
          │  Dictionary mask: non-candidates → -inf    │
          │  candidates("今日") = ["きょう", "こんにち"]│
          └─────────────────┬─────────────────────────┘
                            ▼
                      softmax → "きょう"
```

## Configuration

- Model: tohoku-nlp/bert-base-japanese-v3
- Training data: v6 splits (no MATCHA), classification format
- Parameters: 120.8M total (111.2M BERT + 9.6M classification head)
- Hyperparameters:
  - Batch size: 16
  - Learning rate: 2e-5
  - Max sequence length: 256 tokens
  - Epochs: 10 (with early stopping, patience=3)
  - Warmup: 10% of total steps (linear)
  - Weight decay: 0.01
  - Gradient clipping: 1.0
  - Optimizer: AdamW
  - Scheduler: Linear warmup + decay

## Data Statistics

- Reading dictionary: 13,248 unique surfaces
- Global reading vocabulary: 10,961 entries
- Unambiguous surfaces (1 reading): 95.3%
- Train instances: 86,002
- Val instances: 10,772
- Test instances: 11,001
- OOV in test: 820 (7.5%)

## Results

### Training
- Training time: 157.8 minutes (10 epochs)
- Best validation accuracy: 98.6% (epoch 9)
- All 10 epochs completed (early stopping never triggered)

### Eval Loss Progression
| Epoch | Train Loss | Val Loss | Val Accuracy |
|-------|-----------|----------|--------------|
| 1     | 0.1757    | 0.0754   | 97.4%        |
| 2     | 0.0572    | 0.0594   | 98.2%        |
| 3     | 0.0327    | 0.0571   | 98.4%        |
| 4     | 0.0228    | 0.0695   | 98.5%        |
| 5     | 0.0173    | 0.0664   | 98.4%        |
| 6     | 0.0133    | 0.0737   | 98.5%        |
| 7     | 0.0111    | 0.0791   | 98.5%        |
| 8     | 0.0089    | 0.0820   | 98.5%        |
| 9     | 0.0079    | 0.0834   | **98.6%**    |
| 10    | 0.0067    | 0.0866   | 98.5%        |

Note: Val loss increases while val accuracy improves — classic overfitting with
diminishing returns on the hard cases. The model is becoming more confident on
correctly-classified instances while struggling with the ~1.4% irreducible error.

### Comparable Test Set (1,498 sentences, 12,558 tokens)
- **Overall accuracy: 98.8%**
- Inference speed: 20.6ms mean, 14.6ms p50, 54.9ms p95

### Per-Source Accuracy
| Source | BERT v2 | ByT5 v2 | T5 v7 | T5 v6 | BERT v1 |
|--------|---------|---------|-------|-------|---------|
| nhk | **99.3%** | 89.7% | 89.3% | 88.8% | 86.7% |
| ud_gsd | **98.6%** | 88.3% | 84.5% | 84.3% | 52.2% |
| ud_pud | **98.8%** | 91.3% | 90.1% | 89.2% | 60.9% |
| kahoku | **98.7%** | 87.8% | 87.8% | 88.0% | 89.8% |
| hirogaru | **99.2%** | 91.8% | 89.0% | 90.5% | 87.7% |

### Accuracy by Ambiguity (Val Set, Epoch 9)
| Candidates | Accuracy | Count |
|-----------|----------|-------|
| 1 (unambiguous) | 100.0% | 7,179 |
| 2 | 96.0% | 1,947 |
| 3 | 95.7% | 1,247 |
| 4+ | 93.7% | 399 |

### Error Analysis (146 total errors)
- Wrong reading (model chose incorrectly): 38 (26%)
- OOV surface (not in dictionary): 102 (70%)
- Gold reading not in candidates: 6 (4%)

Top wrong-reading errors are common ambiguous single-kanji:
- 日: 8x (にち vs か) — counter/date ambiguity
- 人: 6x (ひと vs にん) — counter ambiguity
- 本: 3x (ほん vs ぽん) — rendaku ambiguity

## Conclusion

**Hypothesis confirmed.** Reframing furigana as dictionary-constrained disambiguation
dramatically outperforms all seq2seq and token-classification approaches.

### Key findings:

1. **98.8% accuracy** — +9.7pp over ByT5 v2 (89.1%), +12.4pp over T5 v6 (86.4%),
   +32.5pp over BERT v1 (66.3%)

2. **All sources above 98.5%** — eliminates the source-dependent variance seen in
   seq2seq models (e.g. ByT5 ranged 87.8-91.8%)

3. **70% of errors are OOV** — the model's classification is nearly perfect on
   known surfaces. The bottleneck is dictionary coverage, not disambiguation ability.

4. **Fast inference** — 14.6ms p50, well within the <50ms target. BERT encoder is
   efficient since it processes one span per forward pass.

### Important caveat — different task setup

BERT v2 uses **ground truth spans** during evaluation: it's told which kanji substrings
to annotate and only needs to select the correct reading. The seq2seq models (T5, ByT5)
must both **segment and annotate** from raw text. This means:

- BERT v2's 98.8% measures **reading disambiguation accuracy**
- T5/ByT5's 86-89% measures **end-to-end furigana generation accuracy**

These are complementary tasks. For production use, a pipeline approach (morphological
analyzer for segmentation + BERT v2 for disambiguation) could achieve the best of both.

### Implications for Poneglyph

The dictionary-constrained approach is the clear winner for reading disambiguation
when spans are known. For production integration:
- Use a morphological analyzer (MeCab/Sudachi) for span detection
- Use BERT v2 for reading selection on ambiguous spans
- Dictionary coverage can be expanded by adding entries from external sources

## Figures

- `results/figures/bert_v2_accuracy_comparison.png`
- `results/figures/bert_v2_training_loss.png`
- `results/figures/bert_v2_per_source.png`
- `results/figures/bert_v2_candidates_distribution.png`
- `results/figures/bert_v2_ambiguity_accuracy.png`
