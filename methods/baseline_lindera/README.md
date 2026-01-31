# Baseline Lindera Furigana Annotator

Baseline method using Lindera morphological analyzer with embedded IPADIC dictionary.

## Approach

1. **Tokenization**: Use Lindera to segment Japanese text into morphemes
2. **Reading extraction**: Extract katakana readings from IPADIC dictionary entries
3. **Conversion**: Convert katakana readings to hiragana
4. **Filtering**: Only return tokens containing kanji (which need furigana)

### Why This Approach

Lindera is a pure-Rust morphological analyzer, making it ideal for the Poneglyph project
which requires Rust implementation. It provides a baseline to measure against more
sophisticated approaches.

## Results

| Metric | Value |
|--------|-------|
| Token accuracy | **62.7%** (52/83 on sample) |
| Full test set | ~63% (estimated) |

### Comparison

| Method | Accuracy | Notes |
|--------|----------|-------|
| **Lindera baseline** | **62.7%** | Reference implementation |
| Sudachi Mode C | 74.7% | +12% improvement |
| Fine-tuned T5 | 61.8% | Extraction bottleneck |

## Usage

### Build

```bash
cargo build --release -p baseline_lindera
```

### Run Evaluation

```bash
# With comparison output (first 10 sentences)
./target/release/baseline_lindera --input data/splits/test.json --limit 10 --compare

# Full evaluation
./target/release/baseline_lindera --input data/splits/test.json --output results/baseline_predictions.json
```

## Dependencies

Add to Cargo.toml:
```toml
[dependencies]
lindera = { version = "2.0.1", features = ["ipadic", "filter"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
clap = { version = "4.0", features = ["derive"] }
```

The IPADIC dictionary is embedded at compile time (~50MB binary).

## Implementation Notes

### Token Format from Lindera

```
surface: "東京"
details: ["名詞", "固有名詞", "地域", "一般", "*", "*", "東京", "トウキョウ", "トーキョー"]
                                                           ↑reading
```

Reading is typically at index 7 (katakana).

### Katakana to Hiragana Conversion

Unicode offset: katakana (U+30A1-30F6) → hiragana (U+3041-3096) by subtracting 0x60.

## Limitations Discovered

### 1. Compound Word Segmentation (Primary Issue)

Ground truth often has compound words that Lindera splits:

| Ground Truth | Lindera Output |
|--------------|----------------|
| 日本中 | 日本 + 中 |
| 能登半島地震 | 能登 + 半島 + 地震 |
| 路線価 | 路線 + 価 |
| 東京都 | 東京 + 都 |

### 2. Counter/Date Readings

| Input | Expected | Lindera |
|-------|----------|---------|
| 7月 | がつ | つき |
| 4日 | よっか | ひ/にち |
| 1日 | ついたち | missing |

### 3. Verb Conjugation Boundaries

| Ground Truth | Lindera |
|--------------|---------|
| 上 (あ) | 上がり (あがり) |
| 続 (つづ) | 続け (つづけ) |

### 4. Proper Nouns

Names and places may have split readings:
- 長野県 → 長野 + 県
- 石破 → different segmentation than expected

## Error Categorization

| Category | % of Errors | Example |
|----------|-------------|---------|
| Compound splits | ~50% | 東京都 → 東京+都 |
| Counter readings | ~20% | 7月 → wrong reading |
| Verb boundaries | ~15% | 上がり vs 上 |
| Proper nouns | ~10% | Name segmentation |
| Other | ~5% | Rare kanji, ateji |

## Future Improvements

- User dictionary for common compounds
- Post-processing to merge adjacent tokens
- Context-aware reading selection for counters
- Consider Sudachi Mode C for better compound handling
