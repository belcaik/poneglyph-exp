# Model Comparison

## Current Results

All trained models use bracket format (`kanji[reading]`) for seq2seq output.
Accuracy measured on comparable test set (1,498 sentences, no MATCHA).

### Trained Models

| Model | Architecture | Training Data | Accuracy | Notes |
|-------|-------------|---------------|----------|-------|
| T5 v6 | T5 seq2seq | 10,413 (no MATCHA) | **86.4%** | Current best |
| T5 v5 | T5 seq2seq | 18,817 (with MATCHA) | 78.9% | +UD data |
| T5 v4 | T5 seq2seq | 11,593 (with MATCHA) | — | Sentence-segmented |
| T5 v3 | T5 seq2seq | 11,593 (with MATCHA) | — | Multi-source bracket |
| ByT5 v1 | ByT5 seq2seq | 11,593 (with MATCHA) | — | Byte-level, slower |

### Dictionary Baselines (no training)

| Method | Accuracy (NHK test) | Notes |
|--------|---------------------|-------|
| Sudachi Mode C | 74.7% | Dictionary-based, zero-shot |
| Lindera | 62.7% | Dictionary-based, zero-shot |

Note: Baselines were evaluated on NHK-only test set, not directly comparable
to the multi-source comparable test set used for trained models.

## Key Findings

1. **Data quality > data quantity**: Removing 45% of training data (MATCHA) improved
   accuracy by +7.5pp
2. **Sentence segmentation matters**: Splitting articles to sentences improved MATCHA
   accuracy by +28% (v3 to v4)
3. **UD data is high quality**: 100% annotation coverage, adds domain diversity

## Planned Experiments

1. **ByT5 v2**: Retrain on clean v6 data (no MATCHA)
2. **BERT token classification**: Alternative architecture on v6 data
3. **Delimiter change**: Switch from `[]` to a delimiter not found in Japanese text
4. **More high-quality sources**: Expand training data with sources meeting quality checklist
