# Fine-tuned T5 v4 - Sentence-Segmented Multi-Source Dataset

Fourth version of the T5-based furigana annotator. Uses the **same bracket annotation format as v2/v3**, but trained on a **sentence-segmented multi-source dataset**.

## What Changed from v3?

| Aspect | T5 v3 | T5 v4 |
|--------|-------|-------|
| Architecture | sonoisa/t5-base-japanese | Same |
| Format | Bracket `kanji[reading]` | Same |
| Training sentences | 4,358 | 12,261 (+181%) |
| Data structure | Mixed (sentence/paragraph/article) | **Uniform (sentence-level)** |
| MATCHA avg chars | 443.6 | ~70 |
| Kahoku avg chars | 145.0 | ~39 |
| Epochs | 10 (early stopping) | Same |

## Motivation

T5 v3 achieved only 32.5% on MATCHA and 60.2% on Kahoku due to a **data structure mismatch**:
- MATCHA items were full articles (avg 443 chars, max 8831 chars)
- Kahoku items were paragraphs (avg 145 chars)
- Model truncated inputs at 256 tokens, missing most ground truth tokens

See `results/v4_data_audit.md` for detailed analysis.

## Solution: Sentence Segmentation

T5 v4 preprocesses all data with `scripts/segment_sentences.py`:

1. **Split text on Japanese sentence boundaries**: 。！？
2. **Reassign tokens** to sentences based on character position
3. **Preserve total token count** (>99.96% preservation rate)
4. **Result**: All sources now have uniform ~50-70 char average

### Before (v3)
| Source | Avg Chars | Data Type |
|--------|-----------|-----------|
| NHK | 48 | Sentence |
| Hirogaru | 64 | Sentence |
| Kahoku | 145 | Paragraph |
| MATCHA | 444 | Article |

### After (v4)
| Source | Avg Chars | Data Type |
|--------|-----------|-----------|
| NHK | 48 | Sentence |
| Hirogaru | 64 | Sentence |
| Kahoku | 39 | Sentence |
| MATCHA | 70 | Sentence |

## Dataset Statistics

| Split | v3 Items | v4 Items | v3 Tokens | v4 Tokens | Preservation |
|-------|----------|----------|-----------|-----------|--------------|
| Train | 4,358 | 12,261 | 80,626 | 80,606 | 99.98% |
| Val | 906 | 2,685 | 17,635 | 17,628 | 99.96% |
| Test | 957 | 2,755 | 17,424 | 17,424 | 100.00% |

## Results

T5 v4 validates the data structure hypothesis:

| Source | v3 Accuracy | v4 Accuracy | Change |
|--------|-------------|-------------|--------|
| NHK | 82.1% | **84.2%** | +2.1% |
| Hirogaru | 80.8% | **82.7%** | +1.9% |
| Kahoku | 60.2% | **71.9%** | +11.7% |
| MATCHA | 32.5% | **60.8%** | +28.3% |
| **Overall** | **~44.9%** | **66.4%** | **+21.5%** |

**Key achievement**: MATCHA nearly doubled from 32.5% to 60.8% through sentence segmentation alone.

### Training Details

- **Epochs**: 6/10 (early stopping triggered)
- **Best checkpoint**: Epoch 3 (eval_loss: 0.147)
- **Training time**: 53.5 minutes

## Usage

### Prepare Data

```bash
# 1. Run sentence segmentation (if not already done)
python scripts/reprocess_with_segmentation.py

# 2. Prepare bracket format from v4 splits
python scripts/prepare_bracket_format_v4.py
```

### Training

```bash
python -m methods.finetuned_t5_v4.train \
    --model sonoisa/t5-base-japanese \
    --train data/bracket_format_v4/train.json \
    --val data/bracket_format_v4/val.json \
    --output models/t5-furigana-v4 \
    --epochs 10
```

### Evaluation

```bash
python -m methods.finetuned_t5_v4 \
    --model models/t5-furigana-v4 \
    --input data/splits_v4/test.json \
    --output results/t5_v4_predictions.json
```

## Files

```
methods/finetuned_t5_v4/
├── __init__.py      # Module exports
├── __main__.py      # CLI for evaluation
├── annotator.py     # T5V4Annotator class
├── train.py         # Training script
└── README.md        # This file

data/splits_v4/           # Sentence-segmented data
├── train.json
├── val.json
├── test.json
└── all.json

models/t5-furigana-v4/    # Trained model weights

results/
├── v4_data_audit.md              # Data structure analysis
├── t5_v4_training_log.json       # Training metrics
├── t5_v4_predictions.json        # Test predictions
└── t5_v4_segmentation_report.md  # Full comparison report
```

## Key Finding: Data Quality > Data Quantity

T5 v3 had 4x more tokens than v2 but only +1.7% improvement on NHK. The real problem wasn't data quantity but **data structure mismatch**.

T5 v4 validates that properly segmented data enables the model to fully utilize multi-source training data.
