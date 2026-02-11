# T5 v7: Angle-Bracket 《》 Delimiter

## Hypothesis

Changing the delimiter from `[]` to `《》` should not affect accuracy since both
are unambiguous markers. The benefit is eliminating potential collisions with
Japanese text that uses square brackets (e.g. `[注]`, `[1]`).

## Configuration

- Model: sonoisa/t5-base-japanese (222M parameters)
- Training data: v7 bracket format (10,411 sentences, from v6 splits minus 2 《》 collisions)
- Delimiter: 《》 (angle brackets)
- Hyperparameters: same as T5 v6 (batch=8, lr=3e-4, epochs=10, patience=3)

## Training

- Training time: 49.3 minutes
- Early stopped at epoch 9 (best at epoch 6, patience=3)

| Epoch | Eval Loss |
|-------|-----------|
| 1 | 0.3305 |
| 2 | 0.2390 |
| 3 | 0.1741 |
| 4 | 0.1501 |
| 5 | 0.1425 |
| **6** | **0.1377** |
| 7 | 0.1386 |
| 8 | 0.1410 |
| 9 | 0.1436 |

## Results

**Accuracy: 86.6%** (vs T5 v6: 86.4% — virtually identical, +0.2pp)

| Model | Delimiter | Accuracy |
|-------|-----------|----------|
| **T5 v7** | **《》** | **86.6%** |
| T5 v6 | [] | 86.4% |

### Per-Source Accuracy

| Source | T5 v7 (《》) | T5 v6 ([]) | Delta |
|--------|-------------|-----------|-------|
| hirogaru | 89.0% | 89.6% | -0.6pp |
| kahoku | 87.8% | 86.1% | +1.7pp |
| nhk | 89.3% | 89.3% | 0.0pp |
| ud_gsd | 84.5% | 84.1% | +0.4pp |
| ud_pud | 90.1% | 85.4% | +4.7pp |

### Inference

- Mean: 668.8 ms/sentence
- p50: 590.1 ms
- p95: 1,399.6 ms

## Conclusion

Hypothesis confirmed. The 《》 delimiter has no meaningful impact on T5 accuracy.
The word-piece tokenizer treats 《》 as single tokens, making the delimiter change
transparent to the model.
