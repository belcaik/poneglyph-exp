# Baseline Lindera Furigana Annotator

Baseline method using Lindera morphological analyzer with embedded IPADIC dictionary.

## Approach

1. **Tokenization**: Use Lindera to segment Japanese text into tokens
2. **Reading extraction**: Extract katakana readings from IPADIC dictionary entries
3. **Conversion**: Convert katakana readings to hiragana
4. **Filtering**: Only return tokens containing kanji (which need furigana)

## Usage

```bash
# Build
cargo build --release -p baseline_lindera

# Run with comparison against ground truth
./target/release/baseline_lindera --input data/splits/test.json --limit 10 --compare

# Run full evaluation
./target/release/baseline_lindera --input data/splits/test.json --output results/baseline_predictions.json
```

## Results (10 sentence sample)

- Token accuracy: **62.7%** (52/83 exact matches)

## Known Limitations

1. **Compound word segmentation**: Ground truth often has compound words (日本中, 能登半島地震) that Lindera splits into components
2. **Date/counter readings**: "7月" becomes "つき" instead of "がつ", "4日" misses "よっか" reading
3. **Verb conjugation boundaries**: "上がり" vs "上" differ in how much of the verb is included
4. **Proper nouns**: Place names like "長野県" get split into "長野"+"県"

## Dependencies

- lindera 2.0.1 with embedded IPADIC dictionary
- serde, serde_json for JSON handling
- clap for CLI argument parsing
