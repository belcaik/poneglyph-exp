# ByT5 v3: Angle-Bracket 《》 Delimiter

## Hypothesis

Changing the delimiter from `[]` to `《》` should not affect accuracy. The byte-level
model may handle the 3-byte 《》 characters slightly differently than 1-byte `[]`, but
the semantic task is identical.

## Configuration

- Model: sonoisa/byt5-small-japanese (299.6M parameters)
- Training data: v7 bracket format (10,411 sentences, 《》 delimiter)
- Hyperparameters: same as ByT5 v2
  - Batch size: 1 (x8 gradient accumulation = 8 effective)
  - Learning rate: 3e-4
  - Max sequence length: 768 bytes
  - Epochs: 10 (with early stopping, patience=3)

## Training

- Training time: 85.5 minutes
- Early stopped at epoch 5 (best at epoch 2, patience=3)
- Converged much faster than v2 (best at epoch 2 vs epoch 5)

| Epoch | Eval Loss |
|-------|-----------|
| 1 | 0.0300 |
| **2** | **0.0244** |
| 3 | 0.0247 |
| 4 | 0.0252 |
| 5 | 0.0247 |

## Results

**Accuracy: 84.4%** — significant regression of -4.7pp vs ByT5 v2 (89.1%).

| Model | Delimiter | Accuracy | Eval Loss |
|-------|-----------|----------|-----------|
| ByT5 v2 | [] | **89.1%** | 0.0272 |
| **ByT5 v3** | **《》** | **84.4%** | **0.0244** |

### Per-Source Accuracy

| Source | ByT5 v3 (《》) | ByT5 v2 ([]) | Delta |
|--------|---------------|-------------|-------|
| hirogaru | 83.9% | 91.8% | -7.9pp |
| kahoku | 84.1% | 87.8% | -3.7pp |
| nhk | 85.7% | 89.7% | -4.0pp |
| ud_gsd | 83.6% | 88.3% | -4.7pp |
| ud_pud | 87.1% | 91.3% | -4.2pp |

### Inference

- Mean: 1,520.1 ms/sentence
- p50: 1,319.8 ms
- p95: 3,158.7 ms

## Analysis

### Why did accuracy drop despite lower eval_loss?

1. **Byte-level delimiter complexity**: 《 and 》 are 3 bytes each (E3 80 8A, E3 80 8B)
   vs `[` and `]` which are 1 byte each. The model must learn to generate a 3-byte
   sequence as a delimiter, increasing the chance of generation errors.

2. **Eval loss doesn't capture delimiter precision**: The byte-level loss can be low
   because the model gets most bytes right, but delimiter generation errors cascade
   (a wrong byte in 《 corrupts the entire annotation).

3. **All sources dropped uniformly** (3.7-7.9pp), indicating a systematic delimiter
   issue rather than source-specific noise.

4. **Faster convergence is misleading**: Best at epoch 2 (vs v2's epoch 5) suggests
   the model plateaued early — potentially unable to fully learn the 3-byte delimiter.

## Conclusion

**Hypothesis rejected.** The 《》 delimiter significantly hurts byte-level model accuracy.
For ByT5, `[]` should be preferred. For T5 (word-piece), the delimiter change is neutral
(86.6% vs 86.4%).
