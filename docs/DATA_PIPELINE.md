# Data Pipeline

All commands run from the repository root.

```
scrapers ──> data/raw/ ──> parsers ──> data/processed/ ──> split scripts ──> data/splits*/
                                                                   │
                                     derived training formats <────┘
                                     (bracket_format*, bert_v2_*, span_detector_v1, ...)
```

## 1. Scrape

| Source | Script | Output |
|---|---|---|
| NHK Easy | `python data/scrapers/nhk_easy.py --num-articles 500 --output data/raw/` | raw HTML |
| Kahoku | `data/scrapers/kahoku.py` | raw HTML |
| Hirogaru | `data/scrapers/hirogaru.py` | raw HTML |
| MATCHA | `data/scrapers/matcha.py`, `batch_playwright.py` | raw HTML (excluded since v6) |
| UD GSD / PUD | `data/scrapers/parse_ud_conllu.py` | parsed directly from CoNLL-U |

Raw HTML is kept in `data/raw/` (gitignored) so parsers can be re-run without
re-scraping. Corpus details: [DATA_SOURCES.md](DATA_SOURCES.md).

## 2. Parse

Ruby tags become token records:

```json
{"source": "nhk_easy", "text": "土地の値段", "tokens": [{"surface": "土地", "reading": "とち"}]}
```

```bash
python data/scrapers/parse_nhk.py --input data/raw/ --output data/processed/
python scripts/process_all_sources.py       # all sources into data/processed/
python scripts/segment_sentences.py         # article -> sentence segmentation
```

## 3. Split versions

Each version is a new directory with `train.json`, `val.json`, `test.json`, `all.json`.

| Directory | Change | Created by |
|---|---|---|
| `data/splits/` | Original article-level split (NHK + MATCHA + Kahoku + Hirogaru) | `scripts/split_data.py` |
| `data/splits_v4/` | Sentence-segmented | `scripts/reprocess_with_segmentation.py` |
| `data/splits_v5/` | v4 + UD GSD/PUD gold data | `data/merge_all_sources.py` |
| `data/splits_v6_no_matcha/` | v5 minus MATCHA, re-split 80/10/10 stratified; adds `test_comparable.json` | `data/create_splits_no_matcha.py` |
| `data/splits_v7_normalized/` | v6 converted to the morpheme-complete convention (okurigana expansion) | `scripts/normalize_to_morpheme.py` |

v7 normalization is validated by `scripts/validate_normalization.py` (0.31% error rate,
all pre-existing UD issues) and summarized in `results/normalization_*.md`. The
per-token decisions are logged in `data/normalization_decisions.json`.

## 4. Derived training formats

| Directory | Consumer | Created by |
|---|---|---|
| `data/bracket_format*/` | T5 / ByT5 seq2seq (`読み: text` → `kanji[reading]`) | `scripts/prepare_bracket_format*.py` |
| `data/bert_v2_classification/`, `data/bert_v2_reading_dict.json` | BERT v2 on v6 | `python -m methods.bert_v2.prepare_data` |
| `data/bert_v2_v7_classification/`, `data/bert_v2_v7_reading_dict.json` | BERT v2 on v7 | same, with `--data-dir data/splits_v7_normalized` |
| `data/span_detector_v1/` | BIO span detector | `python -m methods.span_detector_v1.prepare_data` |

## 5. Poneglyph v1 dataset (LLM-distilled)

`data/poneglyph_v1/` holds ~14K subtitle sentences annotated by LLMs following
[poneglyph_conventions.md](poneglyph_conventions.md). Pipeline in `scripts/dataset_gen/`:

1. `discover_series.py`, `parse_subtitles.py`: collect and parse subtitle files.
2. `filter_sentences.py`, `select_and_parse_new.py`: keep kanji-bearing sentences.
3. `annotate_gemini*.py`, `assemble_claude_batches.py`: LLM annotation.
4. `build_consensus.py`, `assemble_dataset.py`: merge annotations into splits.
5. `quality_report.py`: writes `results/dataset_v1_report.md`.

Intermediate files go to `data/dataset_gen/` (gitignored, ~0.5 GB).

## 6. LLM benchmark

`scripts/benchmark/` selects 100 test sentences (`select_sentences.py`), runs each
model (`run_gemini.py`, `run_ollama.py`, Claude via `assemble_claude_v2.py`), then
`evaluate.py` and `generate_report.py` produce `results/benchmark_report.md`.
