# Normalization Validation Report

## Summary

- Total sentences: 13020
- Total tokens (original): 107835
- Total tokens (normalized): 107835
- Token count change: +0
- Total validation errors: 338
- Error rate: 0.0031 (0.31%)

## Tokens Expanded Per Source

| Source | Total Tokens | Expanded | % Expanded |
|--------|-------------|----------|-----------|
| hirogaru | 5269 | 2081 | 39.5% |
| kahoku | 6206 | 2118 | 34.1% |
| nhk | 19444 | 6530 | 33.6% |
| ud_gsd | 67812 | 16857 | 24.9% |
| ud_pud | 9104 | 2573 | 28.3% |

## Error Breakdown

| Check | Errors |
|-------|--------|
| Okurigana mismatch | 332 |
| Invalid reading characters | 4 |
| Reading >4x surface length | 2 |

## Source Distribution

| Source | Original | Normalized | Match |
|--------|----------|-----------|-------|
| hirogaru | 506 | 506 | ✓ |
| kahoku | 1198 | 1198 | ✓ |
| nhk | 2284 | 2284 | ✓ |
| ud_gsd | 8036 | 8036 | ✓ |
| ud_pud | 996 | 996 | ✓ |

## Flagged Issues (up to 100)

### Okurigana mismatch (332 total)

- [ud_gsd] surface '設け' ends with 'け', reading 'もうける' ends with 'もうける'
- [ud_gsd] surface '書きとめよう' ends with 'きとめよう', reading 'かきとめる' ends with 'かきとめる'
- [ud_gsd] surface '生じ' ends with 'じ', reading 'しょうずる' ends with 'しょうずる'
- [ud_gsd] surface '多かっ' ends with 'かっ', reading 'おおい' ends with 'おおい'
- [ud_gsd] surface '通じ' ends with 'じ', reading 'つうずる' ends with 'つうずる'
- [ud_gsd] surface '称さ' ends with 'さ', reading 'しょうする' ends with 'しょうする'
- [ud_gsd] surface '称し' ends with 'し', reading 'しょうする' ends with 'しょうする'
- [ud_gsd] surface '言い立て' ends with 'て', reading 'いいたてる' ends with 'いいたてる'
- [ud_gsd] surface '近づ' ends with 'づ', reading 'ちかず' ends with 'ちかず'
- [hirogaru] surface '習ったものと' ends with 'ったものと', reading 'なら' ends with 'なら'
- [ud_gsd] surface '聞い' ends with 'い', reading 'きく' ends with 'きく'
- [ud_gsd] surface '報じ' ends with 'じ', reading 'ほうずる' ends with 'ほうずる'
- [ud_gsd] surface '言い' ends with 'い', reading 'いう' ends with 'いう'
- [ud_gsd] surface '言い' ends with 'い', reading 'いう' ends with 'いう'
- [ud_gsd] surface '引い' ends with 'い', reading 'ひく' ends with 'ひく'
- [ud_gsd] surface '守ろう' ends with 'ろう', reading 'まもる' ends with 'まもる'
- [ud_gsd] surface '多かっ' ends with 'かっ', reading 'おおい' ends with 'おおい'
- [ud_gsd] surface '名づ' ends with 'づ', reading 'なず' ends with 'なず'
- [ud_gsd] surface '有し' ends with 'し', reading 'ゆうする' ends with 'ゆうする'
- [ud_gsd] surface '響い' ends with 'い', reading 'ひびく' ends with 'ひびく'
- ... and 312 more

### Invalid reading characters (4 total)

- [kahoku] '１'/'ワン': katakana 'ワ' in reading; katakana 'ン' in reading
- [kahoku] '平昌'/'ピョンチャン': katakana 'ピ' in reading; katakana 'ョ' in reading; katakana 'ン' in reading; katakana 'チ' in reading; katakana 'ャ' in reading; katakana 'ン' in reading
- [nhk] 'timelesz'/'タイムレス': katakana 'タ' in reading; katakana 'イ' in reading; katakana 'ム' in reading; katakana 'レ' in reading; katakana 'ス' in reading
- [hirogaru] '毎年'/'まいとし、': unexpected char '、' (U+3001) in reading

### Reading >4x surface length (2 total)

- [ud_gsd] '界'/'そさえてぃ' ratio=5.0
- [ud_gsd] '詔'/'みことのり' ratio=5.0

## Assessment

**PASS**: Error rate 0.31% is below 0.5% threshold.