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

### Byte-level impact

《 (U+300A) = 3 bytes, 》 (U+300B) = 3 bytes.
Each annotation adds 4 extra bytes vs `[]` (1 byte each).
With ~20 annotations per sentence, this adds ~80 bytes. Max length is 768, no risk.

## Comparison baseline

| Model | Delimiter | Accuracy |
|-------|-----------|----------|
| ByT5 v3 | 《》 | TBD |
| ByT5 v2 | [] | 89.1% |

## Results

TBD — training in progress
