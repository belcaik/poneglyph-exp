# ByT5 v1 - Byte-Level Furigana Annotator

## Overview

ByT5 v1 is a byte-level T5 model for Japanese furigana annotation. Unlike subword T5 models, ByT5 operates directly on UTF-8 bytes, which was hypothesized to better handle mixed scripts (numbers + kanji).

## Results

| Metric | Value |
|--------|-------|
| **Accuracy** | 65.7% |
| Inference (mean) | 1,310 ms/sentence |
| Parameters | 299.6M |

**Verdict**: ByT5 v1 does not outperform T5 v4 (66.4%) and is ~13x slower.

## Architecture

- **Base model**: `sonoisa/byt5-small-japanese`
- **Tokenization**: Byte-level (vocab size 256)
- **Format**: Bracket annotation (`kanji[reading]`)
- **Input**: `読み: {text}`
- **Output**: `{text with bracket annotations}`

## Training

```bash
python -m methods.byt5_v1.train \
    --model sonoisa/byt5-small-japanese \
    --train data/bracket_format_v4/train.json \
    --val data/bracket_format_v4/val.json \
    --output models/byt5-furigana-v1 \
    --epochs 10 \
    --batch-size 1 \
    --gradient-accumulation 8 \
    --max-length 768
```

### Training Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Batch size | 1 | OOM with batch_size=2 |
| Gradient accumulation | 8 | Effective batch = 8 |
| Learning rate | 3e-4 | |
| Max length | 768 | Covers 96.8% of outputs |
| Early stopping | patience=3 | |
| Training time | 106 minutes | |
| Epochs completed | 5/10 | Early stopping triggered |

## Evaluation

```bash
python -m methods.byt5_v1 \
    --model models/byt5-furigana-v1 \
    --input data/splits_v4/test.json \
    --output results/byt5_v1_predictions.json
```

### Per-Source Accuracy

| Source | Accuracy | Tokens |
|--------|----------|--------|
| Hirogaru | 79.6% | 902 |
| NHK | 78.7% | 2,934 |
| Kahoku | 63.4% | 938 |
| MATCHA | 61.8% | 12,650 |

## Comparison with Other Methods

| Method | Accuracy | Notes |
|--------|----------|-------|
| Lindera baseline | 62.7% | Dictionary lookup |
| Sudachi Mode C | 63.5% | Morphological analysis |
| **ByT5 v1** | **65.7%** | Byte-level T5 |
| T5 v4 (segmented) | 66.4% | Subword T5 |
| T5 v2 (bracket, NHK) | 80.4% | Subword T5, NHK only |
| T5 v3 (bracket, 4x) | 82.1% | Subword T5, expanded |

## Why Byte-Level Didn't Help

1. **Word boundaries remain hard**: Bytes don't carry semantic word boundary information
2. **Longer sequences**: Japanese text = 3 bytes/char = slower inference
3. **Same error patterns**: Surface boundary errors persist despite byte-level view

## Files

- `train.py` - Training script
- `annotator.py` - Inference annotator class
- `__main__.py` - CLI evaluation
- `__init__.py` - Module exports

## Reports

- `results/byt5_v1_vs_t5_v4.md` - Comparison report
- `results/byt5_v1_error_analysis.md` - Error analysis
- `results/byt5_v1_training_log.json` - Training metrics
- `results/byt5_v1_predictions.json` - Test predictions
