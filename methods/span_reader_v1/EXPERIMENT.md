# SpanReader v1: Unified Span Query Model for Furigana

## Hypothesis

A DETR-inspired span query architecture can jointly perform span detection and reading assignment in a single forward pass, eliminating the two-stage pipeline mismatch that limited SpanDet v1 + BERT v2 (82.0% e2e).

## Architecture

- **Encoder:** ku-nlp/deberta-v3-base-japanese (159.9M params)
- **Span Query Decoder:** 2 transformer decoder layers, K=30 learned queries
- **Position Heads:** Pointer attention (start + end) over character positions
- **Existence Head:** Binary classifier per query
- **Type Head:** 7-class classifier (noun, verb, adj, proper_noun, counter, adverb, other)
- **Reading Classifier:** Linear over 8,463-reading vocabulary with dictionary masking
- **Micro-Decoder:** 2-layer transformer for OOV generation (not activated in v1)
- **Total:** 188.5M parameters (159.9M encoder + 28.6M heads)

## Training

- **Data:** poneglyph_v1 (7,562 train / 798 val / 791 test) — LLM-generated annotations
- **Optimizer:** AdamW, encoder LR=1e-5, head LR=5e-5, weight_decay=0.01
- **Schedule:** Linear warmup 10%, cosine decay
- **Batch size:** 4, max_len=128
- **Epochs:** 20 (no early stopping triggered)
- **Loss:** Hungarian matching + BCE(existence) + CE(start/end/type/reading)
- **Loss weights:** λ_exist=2.0, λ_pos=5.0, λ_type=1.0, λ_read=3.0
- **GPU:** RTX 3060 12GB, ~6.4GB VRAM, ~5 min/epoch

## Results

### Test Set

| Metric | Value |
|--------|-------|
| Span F1 | **0.500** (P=0.519, R=0.483) |
| Reading Accuracy | 57.8% (on matched spans) |
| Type Accuracy | 95.0% (on matched spans) |
| TP / FP / FN | 914 / 847 / 980 |

### Training Progression

| Epoch | Train Loss | Val Span F1 | Val Read Acc |
|-------|-----------|-------------|-------------|
| 1 | 36.94 | 0.241 | 0.049 |
| 5 | 23.74 | 0.427 | 0.262 |
| 10 | 16.25 | 0.454 | 0.453 |
| 15 | 11.08 | 0.458 | 0.546 |
| 20 | 8.78 | 0.461 | 0.579 |

### Comparison with Previous Methods

| Method | Span F1 | Reading Acc | E2E Acc | Notes |
|--------|---------|-------------|---------|-------|
| SpanDet v1 (BIO) | 0.949 | 98.6% (GT) | 82.0% | Two-stage, OOV bottleneck |
| BERT v2 (GT spans) | — | 98.8% | — | Needs ground truth spans |
| ByT5 v2 (seq2seq) | — | — | 89.1% | Slow (1.2s/sent) |
| T5 v6 (seq2seq) | — | — | 86.4% | Moderate speed |
| **SpanReader v1** | **0.500** | **57.8%** | **~29%** | Novel architecture, v1 data |

Note: Previous models trained on v7 data (curated ground truth from NHK/UD). SpanReader trained on poneglyph_v1 (LLM-generated, noisier). Not directly comparable.

## Analysis

### What Worked
1. **Type classification is excellent** (95.0%) — the query embeddings learn to distinguish span types
2. **Loss decreases monotonically** — the model is learning, not diverging
3. **Architecture is functional** — DETR-style span queries work for this task
4. **DeBERTa v3 fits on GPU** with batch_size=4, max_len=128

### What Didn't Work
1. **Span detection F1 = 0.50 is too low** — below the 0.85 minimum viable target
2. **Reading accuracy capped at 58%** — limited by poor span detection
3. **No early stopping** — F1 plateaued at ~0.46 but never triggered patience=5

### Root Cause Analysis

1. **Data quality is the primary bottleneck:**
   - poneglyph_v1 was annotated by LLMs (Claude subagents) without human verification
   - LLM annotations have inconsistent span boundaries (e.g., sometimes "お前" is one span, sometimes "前" alone)
   - Some sentences contain Chinese text (mislabeled subtitles) with nonsensical readings
   - Only 1.1% of annotations have dual-model consensus ("high" confidence)

2. **CharPooling loses alignment information:**
   - DeBERTa tokenizes "今日は" as ["今日", "は"] — only 2 tokens for 3 characters
   - Gathering a single token representation for each character via char_to_token is lossy
   - Better approach: use offset_mapping to scatter token representations across character positions with interpolation

3. **Hungarian matching is expensive:**
   - Per-sample matching with scipy on GPU→CPU transfer each batch
   - Cost matrix may over-weight position vs existence, making the model conservative

4. **K=30 queries for avg 2.4 spans/sentence:**
   - Most queries learn to predict "no span" — imbalanced existence classification
   - May benefit from focal loss or fewer queries (K=10)

## v2: CharPooling Fix + Loss Rebalancing

### Root Cause (from diagnostics)
The v1 model systematically predicted end boundaries 1 char too short. When DeBERTa tokenizes multi-char sequences into single tokens (e.g., `ない` → 1 token), all characters within that token receive **identical** representations from CharPooling. The end position head cannot distinguish between chars that share a token.

### Fixes Applied
1. **Intra-token positional encoding** — Each character gets a learned position embedding based on its index within its token (0th, 1st, 2nd...). Now な (pos=0) and い (pos=1) within token "ない" have different representations.
2. **Loss rebalancing** — λ_pos: 5→10, λ_type: 1→0.5, λ_read: 3→1. Prioritize position learning.
3. **Lower learning rates** — encoder: 5e-6 (was 1e-5), heads: 3e-5 (was 5e-5).

### v2 Training Config
- 30 epochs, batch_size=4, max_len=128, patience=8
- Same poneglyph_v1 data (7,562 train)

### v2 Results

| Metric | v1 | v2 | Change |
|--------|:---:|:---:|:------:|
| **Span F1** | 0.500 | **0.869** | **+0.369** |
| Span Precision | 0.519 | 0.887 | +0.368 |
| Span Recall | 0.483 | 0.852 | +0.369 |
| Reading Accuracy | 0.578 | 0.511 | -0.067 |
| Type Accuracy | 0.950 | 0.955 | +0.005 |
| TP / FP / FN | 914/847/980 | **1614/206/280** | |
| Best val F1 | 0.462 | **0.827** | +0.365 |

### Key Insight
The intra-token positional encoding was the critical fix. **Span F1 nearly doubled** from 0.50 to 0.87 — the model already understood WHAT was a span (95% type accuracy) but couldn't point to WHERE it ended. Giving each character within a token a unique positional embedding resolved the ambiguity.

Reading accuracy dropped slightly (0.578 → 0.511) because λ_read was reduced from 3.0 to 1.0 to prioritize position learning. This is recoverable with staged training.

### Updated Comparison

| Method | Span F1 | Reading Acc | Notes |
|--------|---------|-------------|-------|
| SpanDet v1 (BIO) | 0.949 | 98.6% (GT) | Two-stage, v7 curated data |
| **SpanReader v2** | **0.869** | **51.1%** | Unified, poneglyph_v1 data |
| SpanReader v1 | 0.500 | 57.8% | Broken CharPooling |

### Next Steps
1. **Staged training**: freeze reading head epochs 1-15, then unfreeze with λ_read=3.0
2. **More training data**: annotate remaining 5,800 sentences from poneglyph_v1 filter pool
3. **Dictionary masking**: apply surface→candidate mask from BERT v2 to reduce reading vocab
4. **Train on v7 data** for direct comparison with BIO tagger

## Files

- `model.py` — SpanReaderModel with all components (CharPooling v2 with intra-token pos)
- `prepare_data.py` — Dataset, vocabulary, collation (includes intra_positions)
- `train.py` — Training loop with Hungarian matching
- `training_log.json` — Per-epoch metrics (v2 run)
- `models/span-reader-v1/` — v1 checkpoint (broken CharPooling)
- `models/span-reader-v2/` — v2 checkpoint (fixed CharPooling)

## Files

- `model.py` — SpanReaderModel with all components
- `prepare_data.py` — Dataset, vocabulary, collation
- `train.py` — Training loop with Hungarian matching
- `training_log.json` — Per-epoch metrics
- `models/span-reader-v1/` — Best model checkpoint + config + reading vocab
