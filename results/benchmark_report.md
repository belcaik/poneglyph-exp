# LLM Furigana Annotation Benchmark Report (v2)

## Executive Summary

This benchmark evaluates whether LLMs can annotate Japanese text with furigana following Poneglyph's annotation conventions, and whether their output quality is sufficient for training data generation.

**Models tested:** CLAUDE_V2, QWEN7B, GEMINI, CLAUDE_V1

**Best model: CLAUDE_V2** — 97.9% reading accuracy, 97.9% character coverage.

## Kanji Coverage

Every kanji character in the input must be covered by an annotation. Missing kanji = annotation failure.

| Model | Kanji Chars | Covered | Coverage |
|-------|:-----------:|:-------:|:--------:|
| CLAUDE_V2 | 2190 | 2190 | 100.0% |
| QWEN7B | 2190 | 1947 | 88.9% |
| GEMINI | 2190 | 2190 | 100.0% |

## Accuracy Metrics

| Model | Char Coverage | Reading Accuracy | Exact Span Match | Parse Failures |
|-------|:------------:|:----------------:|:----------------:|:--------------:|
| CLAUDE_V2 | 97.9% | 97.9% | 66.9% | 0.0% |
| QWEN7B | 92.9% | 69.0% | 34.5% | 11.0% |
| GEMINI | 97.7% | 97.2% | 61.1% | 0.0% |
| CLAUDE_V1 | 95.9% | 96.6% | 51.4% | 7.0% |

**Metric definitions:**
- **Char Coverage (Recall)**: % of kanji characters annotated by GT that are also covered by the model
- **Reading Accuracy**: Of overlapping spans, % where readings match (allowing for span boundary differences)
- **Exact Span Match**: % of gold tokens with exact surface+reading match in model output

## Per-Source Breakdown

### CLAUDE_V2

| Source | Recall | Reading Acc. | Exact Match | Gold Tokens | Model Tokens |
|--------|:------:|:----------:|:-----------:|:-----------:|:------------:|
| hirogaru | 98.3% | 99.6% | 83.5% | 254 | 250 |
| kahoku | 97.3% | 98.2% | 58.1% | 167 | 142 |
| nhk | 98.0% | 98.9% | 77.7% | 273 | 261 |
| ud_gsd | 97.8% | 97.0% | 54.0% | 404 | 320 |
| ud_pud | 97.8% | 96.5% | 65.0% | 254 | 216 |

### QWEN7B

| Source | Recall | Reading Acc. | Exact Match | Gold Tokens | Model Tokens |
|--------|:------:|:----------:|:-----------:|:-----------:|:------------:|
| hirogaru | 94.7% | 75.1% | 49.6% | 254 | 527 |
| kahoku | 92.1% | 75.8% | 35.3% | 167 | 304 |
| nhk | 95.6% | 73.0% | 44.7% | 273 | 502 |
| ud_gsd | 90.7% | 60.6% | 20.3% | 404 | 532 |
| ud_pud | 91.5% | 67.0% | 30.3% | 254 | 381 |

### GEMINI

| Source | Recall | Reading Acc. | Exact Match | Gold Tokens | Model Tokens |
|--------|:------:|:----------:|:-----------:|:-----------:|:------------:|
| hirogaru | 97.9% | 99.6% | 82.7% | 254 | 249 |
| kahoku | 97.3% | 97.6% | 58.1% | 167 | 142 |
| nhk | 98.0% | 98.9% | 72.9% | 273 | 255 |
| ud_gsd | 97.7% | 95.3% | 45.3% | 404 | 306 |
| ud_pud | 97.6% | 95.7% | 53.9% | 254 | 204 |

### CLAUDE_V1

| Source | Recall | Reading Acc. | Exact Match | Gold Tokens | Model Tokens |
|--------|:------:|:----------:|:-----------:|:-----------:|:------------:|
| hirogaru | 97.6% | 99.2% | 81.5% | 254 | 251 |
| kahoku | 96.4% | 97.5% | 49.1% | 167 | 138 |
| nhk | 95.8% | 98.8% | 65.9% | 273 | 243 |
| ud_gsd | 94.9% | 93.4% | 32.7% | 404 | 250 |
| ud_pud | 95.1% | 95.2% | 37.0% | 254 | 154 |

## Convention Adherence

| Convention | CLAUDE_V2 | QWEN7B | GEMINI | CLAUDE_V1 |
|------------|:------:|:------:|:------:|:------:|
| Verb Chains | 88% (271/307) | 63% (208/331) | 87% (268/307) | 89% (271/303) |
| Compound Nouns | 100% (101/101) | 100% (75/75) | 100% (110/110) | 100% (104/104) |
| Proper Nouns | 100% (109/109) | 100% (139/139) | 100% (124/124) | 100% (118/118) |
| Counters | 100% (74/74) | 100% (58/58) | 100% (75/75) | 100% (69/69) |
| No Hiragana Annot. | 100% (1189/1189) | 60% (1343/2246) | 100% (1156/1156) | 100% (1109/1114) |

## Why Exact Match Is Low

The v7 ground truth follows a **stem-only** convention, while LLMs were instructed to follow **Poneglyph conventions** (morpheme-complete). Key differences:

| v7 Ground Truth | LLM (Poneglyph) | Convention Rule |
|----------------|-----------------|----------------|
| 活動して | 活動しています | Verb chain: include て+auxiliary |
| 集まって | 集まっています | Verb chain: include ている |
| 午前4時 (1 span) | 午前 + 4時 (2 spans) | Split number+time unit |
| 一番最初 (1 span) | 一番 + 最初 (2 spans) | Don't merge unrelated words |

These are not errors — they are intentional convention differences. The character-level recall and reading accuracy confirm the LLM annotations are accurate, just with different span boundaries.

## Recommendation

**CLAUDE_V2 is suitable for generating training data.**

With 97.9% reading accuracy and 97.9% coverage, LLM-generated annotations following Poneglyph conventions are high enough quality to use as training data for smaller models.

## Model Comparison Summary

### CLAUDE_V2
- Reading accuracy: 97.9%
- Character coverage: 97.9%
- Exact span match: 66.9%
- Parse failures: 0.0%

### QWEN7B
- Reading accuracy: 69.0%
- Character coverage: 92.9%
- Exact span match: 34.5%
- Parse failures: 11.0%
- **Note**: Qwen 7B (Q4_K_M) ran on CPU via Ollama (`ollama` package, not `ollama-cuda`), ~127s/sentence avg. The model incorrectly annotates hiragana words and particles (60% no-hiragana adherence), produces significantly more tokens than other models (2246 vs ~1150-1190), and has lower reading accuracy. Install `ollama-cuda` for GPU acceleration.

### GEMINI
- Reading accuracy: 97.2%
- Character coverage: 97.7%
- Exact span match: 61.1%
- Parse failures: 0.0%

### CLAUDE_V1
- Reading accuracy: 96.6%
- Character coverage: 95.9%
- Exact span match: 51.4%
- Parse failures: 7.0%

## Figures

- `results/figures/benchmark_accuracy_all_models.png` — accuracy comparison
- `results/figures/benchmark_coverage_all_models.png` — kanji coverage per model
- `results/figures/benchmark_agreement_matrix.png` — pairwise agreement heatmap
- `results/figures/benchmark_per_source.png` — per-source metrics
- `results/figures/benchmark_convention_adherence.png` — convention compliance
