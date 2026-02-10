# ByT5 v2: Byte-level T5 on Clean Data

## Hypothesis

ByT5 v1 (65.7%) underperformed T5 v4 (66.4%) on noisy data. With clean data,
ByT5 may perform better due to:
- No subword tokenization errors on rare kanji
- Character-level precision for readings
- Better handling of okurigana boundaries

## Configuration

- Model: sonoisa/byt5-small-japanese (299.6M parameters)
- Training data: v6 splits (10,413 sentences, no MATCHA)
- Bracket format: [] (same as T5 v6 for fair comparison)
- Hyperparameters:
  - Batch size: 1 (x8 gradient accumulation = 8 effective)
  - Learning rate: 3e-4
  - Max sequence length: 768 bytes
  - Epochs: 10 (with early stopping, patience=3)
  - Warmup steps: 200
  - Weight decay: 0.01

## Comparison baseline

| Model | Data | Accuracy |
|-------|------|----------|
| **ByT5 v2** | v6 clean | **89.1%** |
| T5 v6 | v6 clean | 86.4% |
| ByT5 v1 | v4 (with MATCHA) | 65.7% |

## Results

### Training
- Training time: 139 minutes (8 epochs, early stopped at patience=3)
- Best eval loss: 0.0272 (epoch 5)
- Best checkpoint: models/byt5-furigana-v2/checkpoint-6510

### Eval Loss Progression
| Epoch | Eval Loss |
|-------|-----------|
| 1     | 0.0342    |
| 2     | 0.0281    |
| 3     | 0.0288    |
| 4     | 0.0281    |
| 5     | **0.0272** |
| 6     | 0.0291    |
| 7     | 0.0296    |
| 8     | 0.0317    |

### Comparable Test Set (1,498 sentences, 12,558 tokens)
- **Overall accuracy: 89.1%** (+2.7pp over T5 v6, +23.4pp over ByT5 v1)
- Inference speed: 1,232ms mean, 1,053ms p50, 2,581ms p95

### Per-Source Accuracy
| Source | ByT5 v2 | T5 v6 | Delta |
|--------|---------|-------|-------|
| ud_pud | 91.3% | 85.4% | +5.9pp |
| ud_gsd | 88.3% | 84.1% | +4.2pp |
| hirogaru | 91.8% | 89.6% | +2.2pp |
| nhk | 89.7% | 89.3% | +0.4pp |
| kahoku | 87.8% | 86.1% | +1.7pp |

### Analysis

1. **Hypothesis confirmed**: Clean data dramatically improved ByT5 (+23.4pp vs v1)
2. **ByT5 v2 is the new overall best** at 89.1%, beating T5 v6 by 2.7pp
3. **Biggest gains on UD data**: Byte-level tokenization handles complex compounds
   better than word-piece (ud_pud +5.9pp, ud_gsd +4.2pp)
4. **Consistent across sources**: All sources between 87.8-91.8% (narrow range)
5. **Trade-off**: ~24x slower inference than T5 v6 (1.2s vs ~50ms per sentence)

### Conclusion

ByT5 is the superior architecture for furigana when clean training data is available.
The byte-level approach handles character boundaries naturally, avoiding tokenization
artifacts that hurt T5 on complex compounds. However, the 24x inference speed penalty
means T5 v6 remains the practical choice for production use in Poneglyph.
