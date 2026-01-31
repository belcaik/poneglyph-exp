# Fine-tuned T5 Furigana Annotator

Sequence-to-sequence furigana annotator using a fine-tuned Japanese T5 model.

## Approach

Fine-tune a Japanese T5 model to convert text with kanji to text with readings:
- **Input**: `読み: 東京都で地震がありました`
- **Output**: `とうきょうとでじしんがありました`

The model learns NHK's annotation style from training data, potentially handling:
- Compound word boundaries (能登半島地震 → のとはんとうじしん)
- Counter/date readings (7月 → がつ, 4日 → よっか)
- Context-dependent readings

### Why This Approach

Dictionary-based methods (Lindera, Sudachi) are limited by their segmentation rules.
A seq2seq model can learn the exact annotation patterns from ground truth data,
potentially achieving better alignment with NHK Easy News annotations.

## Training Details

| Parameter | Value |
|-----------|-------|
| Base model | `sonoisa/t5-base-japanese` (220M params) |
| Training set | 1,616 sentences |
| Validation set | 328 sentences |
| Epochs | 5 |
| Batch size | 8 |
| Learning rate | 3e-4 |
| Training time | ~5 minutes (CPU) |

### Training Loss Curve

| Epoch | Train Loss | Eval Loss |
|-------|------------|-----------|
| 1.0   | 1.28       | 0.81      |
| 2.0   | 0.62       | 0.47      |
| 3.0   | 0.41       | 0.41      |
| 4.0   | 0.31       | 0.39      |
| 5.0   | 0.25       | 0.39      |

Best checkpoint: epoch 4 (eval_loss=0.389)

## Results

| Metric | Value |
|--------|-------|
| Token extraction accuracy | **61.8%** (1,766/2,857) |
| Reading presence accuracy | **~87%** |

**Note**: The model generates correct readings ~87% of the time (readings appear in output),
but extracting individual kanji-reading token pairs from seq2seq output is challenging.
The 61.8% token accuracy reflects extraction limitations, not model quality.

### Comparison

| Method | Accuracy |
|--------|----------|
| Lindera baseline | 62.7% |
| **Sudachi Mode C** | **74.7%** |
| Fine-tuned T5 | 61.8% |

## Usage

### Training

```bash
python -m methods.finetuned_t5.train \
    --model sonoisa/t5-base-japanese \
    --train data/splits/train.json \
    --val data/splits/val.json \
    --output models/t5-furigana \
    --epochs 5 \
    --batch-size 8 \
    --lr 3e-4
```

### Inference

```python
from methods.finetuned_t5 import T5Annotator

annotator = T5Annotator("models/t5-furigana")
tokens = annotator.annotate("東京都で地震がありました")
for t in tokens:
    print(f"{t['surface']} → {t['reading']}")
```

### CLI Evaluation

```bash
python -m methods.finetuned_t5 \
    --model models/t5-furigana \
    --input data/splits/test.json \
    --compare
```

## Dependencies

```bash
pip install transformers torch sentencepiece protobuf
```

## Limitations Discovered

1. **Token extraction bottleneck**: Seq2seq output is continuous text; aligning it back
   to individual kanji spans requires heuristic parsing that loses accuracy.

2. **Training data size**: 1,616 sentences may be insufficient for learning all
   reading patterns. Counter/date readings still have errors.

3. **fp16 instability**: Had to disable mixed precision training due to NaN gradients
   on some GPU configurations.

4. **Inference speed**: ~100ms per sentence vs <1ms for dictionary methods.

## Future Improvements

- Use character-level alignment (like CTC) for better token extraction
- Train on larger dataset (target: 10,000+ sentences)
- Try ByT5 for better handling of rare characters
- Ensemble with dictionary method for reliability
