# Sudachi Mode C Furigana Annotator

Furigana annotator using SudachiPy with Mode C (long unit segmentation).

## Approach

Mode C keeps compound words together, improving alignment with NHK Easy News ground truth annotations.

**Mode differences:**
- Mode A (short): 東京 + 都, 自民 + 党
- Mode C (long): 東京都, 自民党 (matches NHK)

## Results (10 test sentences)

| Method | Accuracy | Improvement |
|--------|----------|-------------|
| Lindera/Mode A | 62.7% | baseline |
| **Mode C** | **74.7%** | **+12.0%** |

## Usage

```python
from methods.sudachi_mode_c import SudachiModeC

annotator = SudachiModeC()
tokens = annotator.annotate("東京都で地震がありました")
for t in tokens:
    print(f"{t['surface']} → {t['reading']}")
```

CLI:
```bash
python -m methods.sudachi_mode_c --input data/splits/test.json --limit 10
```

## Dependencies

```bash
pip install sudachipy sudachidict_core
```

## Limitations

- Still splits some semantic compounds (日本中)
- Verb conjugation boundaries differ from NHK
- Rust implementation pending (sudachi.rs has no public API yet)
