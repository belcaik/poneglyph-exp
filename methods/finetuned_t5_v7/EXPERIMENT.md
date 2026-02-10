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

## Comparison baseline

| Model | Delimiter | Accuracy |
|-------|-----------|----------|
| T5 v7 | 《》 | TBD |
| T5 v6 | [] | 86.4% |

## Results

TBD — training in progress
