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
| T5 v6 | v6 clean | 86.4% |
| ByT5 v1 | v4 (with MATCHA) | 65.7% |
| ByT5 v2 | v6 clean | TBD |

## Results

(To be filled after training and evaluation)
