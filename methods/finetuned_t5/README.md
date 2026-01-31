# Fine-tuned T5 Furigana Annotator

Sequence-to-sequence furigana annotator using a fine-tuned Japanese T5 model.

## Approach

Fine-tune a Japanese T5 model to predict readings directly from text:
- Input: `読み: 東京都で地震がありました`
- Output: `とうきょうと で じしん が ありました`

The model learns NHK's exact annotation style from training data, handling:
- Compound word boundaries
- Counter/date readings
- Context-dependent readings

## Model Options

1. `sonoisa/t5-base-japanese` - 220M params, good general Japanese
2. `sonoisa/byt5-small-japanese` - Byte-level, handles rare kanji

## Training

```bash
python -m methods.finetuned_t5.train \
    --model sonoisa/t5-base-japanese \
    --train data/splits/train.json \
    --val data/splits/val.json \
    --output models/t5-furigana
```

## Inference

```python
from methods.finetuned_t5 import T5Annotator

annotator = T5Annotator("models/t5-furigana")
tokens = annotator.annotate("東京都で地震がありました")
```

## Results

Target: >80% accuracy (vs Sudachi Mode C 74.7%)

## Dependencies

```bash
pip install transformers torch datasets
```
