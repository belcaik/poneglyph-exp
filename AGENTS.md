# AGENTS.md

Furigana benchmark lab: compare methods that predict hiragana readings for kanji spans,
validated automatically against ground truth. The maintainer does not read Japanese, so
every claim about correctness must come from a metric computed against ground truth,
never from eyeballing output.

Original project spec and constraints: [CLAUDE.md](CLAUDE.md).

## Working rules

- Run every script and module from the **repository root**. Most scripts use hardcoded
  relative paths (`data/...`, `models/...`); running elsewhere writes stray copies
  (this produced `data/scrapers/splits/` and `methods/span_reader_v1/data/`).
- Code, comments and docs are in English.
- Network access is limited to `news.web.nhk`; ask before contacting any other domain.
  Scrapers sleep at least 1 s between requests.
- Ask before deleting data files, changing metric definitions in `docs/METRICS.md`,
  or changing the Rust `Token` interface.
- Commits follow Conventional Commits (`feat(span-reader): ...`, `docs: ...`).
- A new method gets its own `methods/<name>/` with an `EXPERIMENT.md` (hypothesis,
  architecture, commands, results) and writes its outputs to `results/<name>_*.json`.
  When it finishes, add it to `docs/MODEL_COMPARISON.md` and `docs/CHANGELOG.md`.

## Data versions

Splits are versioned directories; never edit an existing version, create the next one.
Current versions and what each changed: [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md).

- Compare trained models on `data/splits_v6_no_matcha/test_comparable.json` so numbers
  stay comparable across experiments.
- `data/splits_v7_normalized/` uses the morpheme-complete convention (okurigana
  included in the span); v6 and earlier are stem-only. Never compare scores across the
  two conventions.
- Bracket formats: ByT5 uses `[]`, T5 v7 uses `《》`. `《》` costs ByT5 -4.7pp.

## Gotchas

- `models/`, `data/raw/`, `data/processed/` and `data/dataset_gen/` are gitignored:
  regenerate them, they are not in the clone.
- T5 v4 training writes logs to hardcoded paths under `methods/finetuned_t5_v4/` and
  overwrites them when reused for other data versions.
- `tohoku-nlp/bert-base-japanese-v3` has a slow tokenizer only: no
  `return_offsets_mapping`; compute character offsets manually.
- GPU has ~12 GB: one of T5, BERT or ByT5 at a time, never ByT5 alongside another model.
- Training output is tqdm-buffered: find metrics with `strings <log> | grep eval_loss`.
- JSUT labels are TTS readings (ー, は→わ), unusable as furigana ground truth.
- UD CoNLL-U readings: uninflected tokens use UnidicInfo field[0]; inflected tokens use
  field[4] with ー normalized via field[0].
- Watch disk usage (`df -h`); old checkpoints in `models/` fill the disk quickly.
