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

### Delimiter Migration: [] → 《》

| Model | Delimiter | Accuracy | Delta | Inference (ms/sent) |
|-------|-----------|----------|-------|---------------------|
| T5 v7 | 《》 | 86.6% | +0.2pp | 669 |
| T5 v6 | [] | 86.4% | baseline | ~50 |
| ByT5 v3 | 《》 | 84.4% | **-4.7pp** | 1,520 |
| ByT5 v2 | [] | 89.1% | baseline | 1,232 |

**Result**: 《》 is neutral for T5 (word-piece) but harmful for ByT5 (byte-level).
See "Finding #5" below.

#### Per-Source: Delimiter Impact

| Source | T5 v7 (《》) | T5 v6 ([]) | ByT5 v3 (《》) | ByT5 v2 ([]) |
|--------|-------------|-----------|---------------|-------------|
| hirogaru | 89.0% | 89.6% | 83.9% | 91.8% |
| kahoku | 87.8% | 86.1% | 84.1% | 87.8% |
| nhk | 89.3% | 89.3% | 85.7% | 89.7% |
| ud_gsd | 84.5% | 84.1% | 83.6% | 88.3% |
| ud_pud | 90.1% | 85.4% | 87.1% | 91.3% |

### Dictionary Baselines (no training)

| Method | Accuracy (NHK test) | Notes |
|--------|---------------------|-------|
| Sudachi Mode C | 74.7% | Dictionary-based, zero-shot |
| Lindera | 62.7% | Dictionary-based, zero-shot |

Note: Baselines were evaluated on NHK-only test set, not directly comparable
to the multi-source comparable test set used for trained models.

## Phase 2: Span-Based and LLM Methods (v7 data)

### BERT v2: Dictionary-Constrained Disambiguation

BERT encoder + span mean pool + [CLS] → linear head with softmax masked to the
readings the dictionary allows for that surface.

| Variant | Data | Accuracy | Notes |
|---|---|---|---|
| BERT v2 | v6 | **98.8%** | All sources 98.5-99.3% |
| BERT v2 | v7 normalized | 98.6% (val) | Reading vocab 18,636 |

**Caveat**: receives gold spans (told which characters to annotate), so it is an upper
bound for the reading step, not an end-to-end score. 70% of its errors are surfaces
missing from the dictionary (OOV).

### Two-Stage Pipeline: Span Detector v1 + BERT v2

| Stage | Metric | Value |
|---|---|---|
| Span detection (BIO tagger) | F1 test / val | 0.949 / 0.974 |
| End-to-end pipeline | Accuracy | 82.0% |

Errors: wrong reading 12.9%, missed span 5.1%, spurious span 5.1%. 12.7% of detected
spans are not in the reading dictionary (inflections, compounds, proper nouns), which
caps the pipeline below ByT5 v2. Seq2seq models avoid this by generating readings.

### SpanReader: Unified Span Query Model

DeBERTa v3 JP encoder + DETR-style learned span queries + hybrid reading head (188.5M
params), trained on `data/poneglyph_v1`.

| Version | Span F1 | Reading Acc | Fix |
|---|---|---|---|
| v1 | 0.500 | 57.8% | CharPooling gave identical vectors to chars in one sub-token |
| v2 | 0.869 | 51.1% | Intra-token positional encoding; loss weights λ_pos=10, λ_type=0.5, λ_read=1 |

Reading accuracy dropped with the lower λ_read; staged training should recover it.
Diagnostics: `results/span_reader_v1_diagnostics.md`.

### LLM Benchmark v2 (100 test sentences, v7 ground truth)

| Model | Reading Acc | Exact Span Match | Kanji Coverage | Parse Fail |
|---|---|---|---|---|
| Claude v2 | **97.9%** | 66.9% | 100% | 0% |
| Gemini Flash | 97.2% | 61.1% | 100% | 0% |
| Claude v1 | 96.6% | 51.4% | 89.4% | 7% |
| Qwen 7B (local) | 69.0% | 34.5% | 88.9% | 11% |

Low exact span match reflects the convention gap (ground truth is morpheme-level,
Poneglyph conventions annotate conceptual units), not wrong readings. Claude v2 and
Gemini Flash are good enough to generate training data, which produced
`data/poneglyph_v1`. Full report: `results/benchmark_report.md`.

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

### 5. 《》 delimiter hurts byte-level models

Changing delimiters from `[]` to `《》` had opposite effects on different architectures:

- **T5 v7**: 86.6% (+0.2pp) — neutral. Word-piece tokenizer handles 《》 as single tokens.
- **ByT5 v3**: 84.4% (-4.7pp) — significant regression. Each 《》 is 3 bytes in UTF-8
  (vs 1 byte for `[]`), making the delimiter pattern harder for byte-level models to learn.
  All sources dropped uniformly (3.7-7.9pp), indicating a systematic issue rather than
  source-specific noise.

Despite ByT5 v3 having a lower eval_loss (0.0244 vs 0.0272), accuracy dropped —
suggesting the loss metric doesn't fully capture delimiter generation quality at byte-level.

**Conclusion**: Keep `[]` delimiters for ByT5. If avoiding bracket collisions is needed,
use `[]` for ByT5 and `《》` for T5, or use `[]` universally with collision escaping.

## Recommendations

1. **For production (Poneglyph)**: T5 v6/v7 offers the best accuracy/speed trade-off.
   ByT5 v2 is 24x slower at inference, which may be prohibitive for real-time use.
2. **For offline batch processing**: ByT5 v2 (with `[]`) achieves the highest accuracy at 89.1%.
3. **Do not use BERT token classification** for furigana — the architecture is a poor fit.
4. **Keep `[]` delimiters for ByT5**: The 《》 migration costs -4.7pp for byte-level models.
   T5 is unaffected, so delimiter choice only matters for ByT5.
5. **Next experiments**:
   - More high-quality training sources to push past 90%
   - Distillation: Train a smaller/faster model using ByT5 v2 predictions
   - Longer ByT5 training with 《》 to see if accuracy gap closes with more epochs
6. **Readings given spans are nearly solved** (BERT v2, 98.8%). The open problem is span
   detection plus OOV surfaces: a reading step that can generate outside the dictionary
   is needed before a span pipeline beats seq2seq.
7. **For training data generation**: Claude v2 or Gemini Flash (≥97% reading accuracy,
   100% kanji coverage). Local Qwen 7B is not usable.
