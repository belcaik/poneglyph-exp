# Furigana Lab (poneglyph-exp)

A benchmark lab for **automatic furigana annotation**: given Japanese text, predict the
hiragana reading of every kanji span. It compares dictionary, seq2seq, classification,
span-based and LLM approaches against human-verified ground truth, to pick the method
that ships in the [Poneglyph](docs/poneglyph_conventions.md) learning platform.

```
入力:  日本語の文章を読みます
出力:  日本語《にほんご》の文章《ぶんしょう》を読《よ》みます
```

## Results at a glance

Comparable test set: 1,498 sentences / 12,558 tokens from NHK Easy, Kahoku, Hirogaru,
UD-GSD and UD-PUD. Primary metric is exact-match reading accuracy per token
(see [docs/METRICS.md](docs/METRICS.md)).

| Method | Approach | Accuracy | Notes |
|---|---|---|---|
| BERT v2 | Dictionary-constrained span classification | **98.8%** | Given gold spans: upper bound, not end-to-end |
| Claude v2 (LLM) | Prompted annotation | 97.9% | 100-sentence benchmark, used for data generation |
| Gemini Flash (LLM) | Prompted annotation | 97.2% | 100-sentence benchmark |
| ByT5 v2 | Byte-level seq2seq | 89.1% | Best end-to-end model, ~1.2 s/sentence |
| T5 v6 / v7 | Word-piece seq2seq | 86.4% / 86.6% | Best speed/accuracy trade-off, ~50 ms/sentence |
| SpanDet v1 + BERT v2 | Two-stage pipeline | 82.0% | Limited by out-of-vocabulary spans |
| Sudachi Mode C | Dictionary, zero-shot | 74.7% | NHK-only test set |
| Lindera (Rust) | Dictionary, zero-shot | 62.7% | NHK-only test set, baseline |

Full analysis: [docs/MODEL_COMPARISON.md](docs/MODEL_COMPARISON.md). Experiment history:
[docs/CHANGELOG.md](docs/CHANGELOG.md).

## Repository layout

```
data/          Scrapers, versioned splits, derived training formats, datasets
  scrapers/    NHK Easy, Kahoku, Hirogaru, MATCHA scrapers + ruby/UD parsers
  splits*/     Versioned train/val/test splits (see docs/DATA_PIPELINE.md)
  poneglyph_v1/  LLM-distilled furigana dataset from Japanese subtitles
  benchmark/   LLM benchmark inputs, annotations and comparisons
methods/       One directory per annotation method (Rust crate or Python package)
scripts/       Data preparation, normalization, benchmark and dataset generation
evaluation/    Tokenizer comparison utilities
results/       Evaluation JSON, training logs, markdown reports, figures/
docs/          Conventions, metrics, data sources, comparisons, changelog
models/        Trained weights (gitignored, regenerate by training)
```

## Getting started

Requirements: Python 3.12, Rust (edition 2024), and a CUDA GPU (~12 GB) for training.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium          # only for the Playwright-based scrapers

cargo build --release                # builds the Rust methods (Lindera baseline)
```

### Evaluate a method

Python methods run as modules from the repository root:

```bash
python -m methods.sudachi_mode_c --input data/splits/test.json --limit 10
python -m methods.byt5_v2 --model models/byt5-furigana-v2 \
    --input data/splits_v6_no_matcha/test_comparable.json
```

The Rust baseline:

```bash
cargo run --release -p baseline_lindera -- --input data/splits/test.json
```

Model weights live in `models/` and are not tracked. Train a model with its
`methods/<name>/train.py` before evaluating it. Each method's `EXPERIMENT.md` or
`README.md` has its exact commands and results.

### Rebuild the data

See [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) for scraping, parsing, splitting,
normalization and the training formats derived from each split version.

## Documentation

| Document | Contents |
|---|---|
| [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) | Data flow, split versions, how to regenerate each artifact |
| [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) | Each corpus: size, coverage, quality, quirks |
| [docs/METRICS.md](docs/METRICS.md) | Evaluation metrics definitions |
| [docs/MODEL_COMPARISON.md](docs/MODEL_COMPARISON.md) | Results across all methods, findings, recommendations |
| [docs/poneglyph_conventions.md](docs/poneglyph_conventions.md) | Annotation conventions (what counts as one span) |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Chronological experiment log |
| [AGENTS.md](AGENTS.md) | Guide for coding agents working in this repo |

## Data licensing

The code is released under the [MIT License](LICENSE). Scraped and derived corpora
(NHK Easy, Kahoku, Hirogaru, MATCHA, subtitle sources) remain subject to their original
publishers' terms and are included for research and evaluation only. Universal
Dependencies data follows its treebank licenses (CC BY-SA).
