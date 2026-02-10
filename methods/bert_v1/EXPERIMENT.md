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
| BERT v1 | token classification | TBD |

## Results

(To be filled after training and evaluation)
