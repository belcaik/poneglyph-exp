# Fine-tuned T5 v2 - Bracket Annotation Format

Second version of the T5-based furigana annotator using **character-level span prediction** instead of full text conversion.

## Why v2?

T5 v1 achieved only 61.8% accuracy despite generating correct readings ~87% of the time. The analysis (`results/t5_v1_error_analysis.md`) revealed that 73.7% of errors were caused by the **extraction algorithm**, not the model.

### The v1 Problem

```
Input:  国は、土地をもらった人の税金を計算するために...
Output: くには、ちをもらったひとのぜいぜいをけいかくするために...

Problem: How to map "けいさん" back to "計算"?
         When multiple kanji have no separator, extraction fails.
```

### The v2 Solution

```
Input:  読み: 国は、土地をもらった人の税金を計算するために...
Output: 国[くに]は、土地[とち]をもらった人[ひと]の税金[ぜいきん]を計算[けいさん]するために...
```

The model outputs the **original text with inline bracket annotations**, preserving position information.

## Format Comparison

| Aspect | T5 v1 | T5 v2 |
|--------|-------|-------|
| Output format | Full hiragana | Original + brackets |
| Extraction | Anchor-based alignment | Simple regex |
| Position preserved | No | Yes |
| Multiple same kanji | Fails | Works |
| Complexity | High | Low |

## Results

| Method | Accuracy | Notes |
|--------|----------|-------|
| T5 v1 (hiragana) | 61.8% | Extraction bottleneck |
| Sudachi Mode C | 63.5% | Style mismatch |
| **T5 v2 (bracket)** | **TBD%** | Pending evaluation |

## Usage

### Training

```bash
python -m methods.finetuned_t5_v2.train \
    --model sonoisa/t5-base-japanese \
    --train data/bracket_format/train.json \
    --val data/bracket_format/val.json \
    --output models/t5-furigana-v2 \
    --epochs 5
```

### Evaluation

```bash
python -m methods.finetuned_t5_v2 \
    --model models/t5-furigana-v2 \
    --input data/splits/test.json \
    --compare
```

### Data Preparation

The bracket format data is created by:

```bash
python scripts/prepare_bracket_format.py
```

This converts:
```json
{
  "text": "土地の値段",
  "tokens": [
    {"surface": "土地", "reading": "とち"},
    {"surface": "値段", "reading": "ねだん"}
  ]
}
```

To:
```json
{
  "input": "読み: 土地の値段",
  "output": "土地[とち]の値段[ねだん]"
}
```

## Implementation Details

### Bracket Parsing

Extraction uses a simple regex:

```python
pattern = r'([^\[\]]+?)\[([ぁ-んァ-ヶー]+)\]'
```

This matches:
- `土地[とち]` → surface="土地", reading="とち"
- `値段[ねだん]` → surface="値段", reading="ねだん"

### Model Architecture

- Base: sonoisa/t5-base-japanese (220M parameters)
- Task: Seq2Seq with bracket annotation generation
- Training: 5 epochs, batch size 8, lr 3e-4

## Files

```
methods/finetuned_t5_v2/
├── __init__.py      # Module exports
├── __main__.py      # CLI for evaluation
├── annotator.py     # T5V2Annotator class
├── train.py         # Training script
└── README.md        # This file

data/bracket_format/
├── train.json       # 1,616 samples
├── val.json         # 328 samples
└── test.json        # 340 samples
```

## Expected Improvements

The bracket format should eliminate the 73.7% of errors caused by extraction failures in v1. Expected accuracy: **75-85%** (comparable to or better than Sudachi).

Remaining error sources:
- Model reading errors (~10%)
- Segmentation style mismatch with NHK (~5%)
- Edge cases (rare kanji, names) (~5%)
