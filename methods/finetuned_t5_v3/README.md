# Fine-tuned T5 v3 - Expanded Multi-Source Dataset

Third version of the T5-based furigana annotator. Uses the **same bracket annotation format as v2**, but trained on an **expanded multi-source dataset** (4x more training data).

## What Changed from v2?

| Aspect | T5 v2 | T5 v3 |
|--------|-------|-------|
| Architecture | sonoisa/t5-base-japanese | Same |
| Format | Bracket `kanji[reading]` | Same |
| Training data | NHK-only (1,616 sentences) | Multi-source (4,358 sentences) |
| Training tokens | ~19,000 | ~80,000 |
| Data sources | 1 (NHK Easy) | 4 (NHK, MATCHA, Kahoku, Hirogaru) |
| Epochs | 5 (fixed) | 10 (with early stopping) |
| Early stopping | None | patience=3 |

## Hypothesis

Increasing training data from 4 sources (NHK + MATCHA + Kahoku + Hirogaru) should improve accuracy by:
1. Exposing the model to more vocabulary
2. Learning reading patterns from diverse contexts
3. Reducing overfitting to NHK-specific annotation style

## Dataset Comparison

### T5 v2 (NHK-only)
- 500 NHK Easy articles
- 1,616 training sentences
- ~19,000 tokens
- Single annotation style

### T5 v3 (Multi-source)
- 801 articles from 4 sources:
  - NHK Easy: 500 articles
  - MATCHA: 141 articles (tourism/regional)
  - Kahoku: 50 articles (news)
  - Hirogaru: 110 articles (educational)
- 4,358 training sentences (+169%)
- ~80,000 tokens (+324%)
- Multiple annotation styles

## Results

See `results/t5_v3_expanded_data_report.md` for detailed comparison.

| Method | Accuracy | Notes |
|--------|----------|-------|
| Lindera baseline | 62.7% | Dictionary lookup |
| T5 v1 (hiragana) | 61.8% | Extraction bottleneck |
| Sudachi Mode C | 63.5% | Dictionary + morphology |
| T5 v2 (NHK-only) | 80.4% | Bracket format, 5 epochs |
| **T5 v3 (NHK test)** | **82.1%** | **4x data, early stopping, +1.7%** |

## Usage

### Training

```bash
# First, regenerate bracket format data from expanded splits
python scripts/prepare_bracket_format.py

# Then train T5 v3
python -m methods.finetuned_t5_v3.train \
    --model sonoisa/t5-base-japanese \
    --train data/bracket_format/train.json \
    --val data/bracket_format/val.json \
    --output models/t5-furigana-v3 \
    --epochs 10
```

### Evaluation

```bash
python -m methods.finetuned_t5_v3 \
    --model models/t5-furigana-v3 \
    --input data/splits/test.json \
    --output results/t5_v3_predictions.json \
    --compare
```

## Training Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Base model | sonoisa/t5-base-japanese | Same as v2 |
| Epochs | 10 | More data supports longer training |
| Early stopping | patience=3 | Stop if eval_loss doesn't improve |
| Batch size | 8 | Same as v2 |
| Learning rate | 3e-4 | Same as v2 |
| Warmup steps | 100 | Same as v2 |

## Files

```
methods/finetuned_t5_v3/
├── __init__.py      # Module exports
├── __main__.py      # CLI for evaluation (with per-source accuracy)
├── annotator.py     # T5V3Annotator class (same logic as v2)
├── train.py         # Training script (with early stopping)
└── README.md        # This file

models/t5-furigana-v3/   # Trained model weights
results/
├── t5_v3_training_log.json        # Training metrics
├── t5_v3_predictions.json         # Test predictions
└── t5_v3_expanded_data_report.md  # Full comparison report
```

## Actual Outcomes

| Source | Accuracy | Notes |
|--------|----------|-------|
| NHK (sentence-level) | **82.1%** | +1.7% over v2, improved |
| Hirogaru (sentence-level) | 80.8% | Good generalization |
| Kahoku (paragraph-level) | 60.2% | Partial truncation issues |
| MATCHA (article-level) | 32.5% | Data structure mismatch |

**Key finding**: Accuracy on sentence-level data improved (80.4% → 82.1%). The low MATCHA accuracy is due to article-level data (avg 443 chars) being evaluated in a sentence-level pipeline (max 256 tokens). See `results/t5_v3_expanded_data_report.md` for full analysis.

## Reproduction

To reproduce this experiment from scratch:

```bash
# 1. Ensure expanded splits exist
ls -la data/splits/train.json  # Should be ~8.8M with 4,358 sentences

# 2. Regenerate bracket format data
python scripts/prepare_bracket_format.py

# 3. Verify bracket data
python -c "import json; d=json.load(open('data/bracket_format/train.json')); print(f'Train samples: {len(d)}')"

# 4. Train model
python -m methods.finetuned_t5_v3.train \
    --model sonoisa/t5-base-japanese \
    --train data/bracket_format/train.json \
    --val data/bracket_format/val.json \
    --output models/t5-furigana-v3 \
    --epochs 10

# 5. Evaluate
python -m methods.finetuned_t5_v3 \
    --model models/t5-furigana-v3 \
    --input data/splits/test.json \
    --output results/t5_v3_predictions.json
```
