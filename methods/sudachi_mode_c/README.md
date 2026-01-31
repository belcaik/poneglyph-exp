# Sudachi Mode C Furigana Annotator

Furigana annotator using SudachiPy with Mode C (long unit segmentation).

## Approach

Sudachi offers three segmentation modes:
- **Mode A** (short): Splits aggressively (東京 + 都, 自民 + 党)
- **Mode B** (middle): Balanced segmentation
- **Mode C** (long): Keeps compound words together (東京都, 自民党)

NHK Easy News annotates compound words as single units, making Mode C the best match.

### Why This Approach

After analyzing Lindera baseline errors (62.7% accuracy), the primary issue was
compound word segmentation. Sudachi Mode C directly addresses this by preserving
longer morphological units that match NHK's annotation style.

## Results

| Metric | Value |
|--------|-------|
| Token accuracy | **74.7%** (62/83 on sample) |
| Full test set | ~75% (estimated) |
| Improvement over baseline | **+12.0 percentage points** |

### Comparison

| Method | Accuracy | Notes |
|--------|----------|-------|
| Lindera baseline | 62.7% | Splits compounds |
| **Sudachi Mode C** | **74.7%** | Best performer |
| Fine-tuned T5 | 61.8% | Extraction bottleneck |

### Example Improvements

| Text | Lindera | Sudachi Mode C | Ground Truth |
|------|---------|----------------|--------------|
| 路線価 | 路線 + 価 | 路線価 ✓ | 路線価 |
| 東京都 | 東京 + 都 | 東京都 ✓ | 東京都 |
| 能登半島地震 | 能登 + 半島 + 地震 | 能登半島地震 ✓ | 能登半島地震 |
| 自民党 | 自民 + 党 | 自民党 ✓ | 自民党 |

## Usage

### Python API

```python
from methods.sudachi_mode_c import SudachiModeC

annotator = SudachiModeC()
tokens = annotator.annotate("東京都で地震がありました")
for t in tokens:
    print(f"{t['surface']} → {t['reading']}")
# Output:
# 東京都 → とうきょうと
# 地震 → じしん
```

### CLI Evaluation

```bash
# Run on test set with comparison output
python -m methods.sudachi_mode_c --input data/splits/test.json --limit 10 --compare

# Full evaluation
python -m methods.sudachi_mode_c --input data/splits/test.json --output results/sudachi_predictions.json
```

## Dependencies

```bash
pip install sudachipy sudachidict_core
```

The dictionary downloads automatically on first use (~70MB).

## Implementation Notes

1. **Katakana conversion**: Sudachi returns readings in katakana; we convert to hiragana.
2. **Kanji filtering**: Only tokens containing kanji are returned (non-kanji don't need furigana).
3. **Offset tracking**: Token positions are tracked for alignment with source text.

## Limitations Discovered

1. **Some compounds still split**: "日本中" (にっぽんじゅう) may split as "日本" + "中"
2. **Verb conjugation boundaries**: "上がり" vs "上" differ from NHK's choices
3. **Counter readings**: Some counters like "7月" still need context for correct reading
4. **No Rust implementation**: sudachi.rs exists but lacks public API; Python-only for now

## Error Analysis

Remaining errors (25.3%) fall into categories:

| Category | Example | Issue |
|----------|---------|-------|
| Verb boundaries | 上がり vs 上 | Inflection included/excluded |
| Counters | 7月 → つき vs がつ | Context-dependent |
| Semantic compounds | 日本中 | Split despite semantic unity |
| Proper noun variants | 石破 | Name reading variations |

## Future Improvements

- Custom user dictionary for NHK-specific compounds
- Post-processing rules for counter readings
- Rust port when sudachi.rs API stabilizes
