# Model Comparison

## Current Results

All models evaluated on comparable test set: 1,498 sentences, 12,558 tokens,
5 sources (NHK, kahoku, hirogaru, UD-GSD, UD-PUD), no MATCHA.

### Architecture Comparison (v6 data)

| Model | Architecture | Params | Accuracy | Inference (ms/sent) | Notes |
|-------|-------------|--------|----------|---------------------|-------|
| **ByT5 v2** | Byte-level seq2seq | 300M | **89.1%** | 1,232 | New best |
| T5 v6 | Word-piece seq2seq | 222M | 86.4% | ~50 | Previous best |
| BERT v1 | Token classification | 91M | 66.3% | 20 | Unsuitable |

### Per-Source Accuracy

| Source | ByT5 v2 | T5 v6 | BERT v1 | Tokens |
|--------|---------|-------|---------|--------|
| hirogaru | 91.8% | 89.6% | 87.7% | 902 |
| kahoku | 87.8% | 86.1% | 89.8% | 938 |
| nhk | 89.7% | 89.3% | 86.7% | 2,934 |
| ud_gsd | 88.3% | 84.1% | 52.2% | 6,871 |
| ud_pud | 91.3% | 85.4% | 60.9% | 913 |

### Training History (chronological)

| Model | Training Data | Accuracy | Notes |
|-------|--------------|----------|-------|
| T5 v4 | 11,593 (with MATCHA) | — | Sentence-segmented |
| T5 v5 | 18,817 (with MATCHA) | 78.9% | +UD data |
| T5 v6 | 10,413 (no MATCHA) | 86.4% | MATCHA exclusion validated |
| BERT v1 | 10,413 (no MATCHA) | 66.3% | Token classification approach |
| ByT5 v2 | 10,413 (no MATCHA) | 89.1% | Byte-level, clean data |

### Dictionary Baselines (no training)

| Method | Accuracy (NHK test) | Notes |
|--------|---------------------|-------|
| Sudachi Mode C | 74.7% | Dictionary-based, zero-shot |
| Lindera | 62.7% | Dictionary-based, zero-shot |

Note: Baselines were evaluated on NHK-only test set, not directly comparable
to the multi-source comparable test set used for trained models.

## Key Findings

### 1. Byte-level processing outperforms word-piece for furigana

ByT5 v2 (89.1%) beats T5 v6 (86.4%) by +2.7pp despite being slower. Byte-level
tokenization handles character boundaries more naturally for this task. The gap is
largest on UD data: +4.2pp on ud_gsd, +5.9pp on ud_pud.

### 2. Token classification is fundamentally unsuitable

BERT v1 (66.3%) fails at compound boundary detection — it merges adjacent kanji
into single tokens (e.g., 先制+点 → 先制点). Furigana is a generation task,
not a classification task. The approach works on simple sources (87-90%) but
collapses on complex UD compounds (52-61%).

### 3. Data quality > data quantity

Removing MATCHA (45% of data) improved T5 accuracy by +7.5pp. Every source
improved. Root cause: MATCHA had 66.2% annotation coverage and bracket collisions
from JavaScript artifacts.

### 4. Sentence segmentation matters

Splitting articles to sentences improved MATCHA accuracy by +28% (v3 to v4).

## Architecture Trade-offs

| | ByT5 v2 | T5 v6 | BERT v1 |
|---|---------|-------|---------|
| **Accuracy** | 89.1% | 86.4% | 66.3% |
| **Speed** | ~1.2s/sent | ~50ms/sent | ~20ms/sent |
| **Training** | 139 min | 26 min | 26 min |
| **GPU memory** | ~7 GB | ~3 GB | ~2 GB |
| **Strength** | Best accuracy, handles compounds | Fast, good accuracy | Fastest inference |
| **Weakness** | Very slow inference | Lower on UD data | Poor boundary detection |

## Recommendations

1. **For production (Poneglyph)**: T5 v6 offers the best accuracy/speed trade-off.
   ByT5 v2 is 24x slower at inference, which may be prohibitive for real-time use.
2. **For offline batch processing**: ByT5 v2 achieves the highest accuracy.
3. **Do not use BERT token classification** for furigana — the architecture is a poor fit.
4. **Next experiments**:
   - Delimiter change from `[]` to avoid collisions with Japanese text
   - More high-quality training sources to push past 90%
   - Distillation: Train a smaller/faster model using ByT5 v2 predictions
