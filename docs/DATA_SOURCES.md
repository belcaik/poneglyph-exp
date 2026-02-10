# Data Sources for Furigana Training

## Active Sources (used in v6 training)

### NHK News Easy
- **URL**: https://www3.nhk.or.jp/news/easy/
- **Sentences**: ~2,284
- **Annotation coverage**: 99.9%
- **Bracket collisions**: 0
- **Quality**: Excellent
- **Domain**: Simplified news for Japanese learners
- **Notes**: Primary high-quality source, human-annotated ruby tags

### UD Japanese GSD
- **Source**: Universal Dependencies
- **Sentences**: ~8,036
- **Annotation coverage**: 100%
- **Bracket collisions**: 1
- **Quality**: Excellent
- **Domain**: Wikipedia (formal, varied topics)
- **Notes**: Gold-standard linguistic annotations, extracted from UnidicInfo field.
  Uninflected forms use field[0] (orthographic katakana), inflected use field[4]
  (phonetic katakana) with long vowel normalization via field[0].

### UD Japanese PUD
- **Source**: Universal Dependencies (Parallel)
- **Sentences**: ~996
- **Annotation coverage**: 100%
- **Bracket collisions**: 0
- **Quality**: Excellent
- **Domain**: Wikipedia (parallel corpus)
- **Notes**: Smaller but very clean

### Kahoku Easy Japanese
- **URL**: https://kahoku.news/easyjapanese
- **Sentences**: ~1,198
- **Annotation coverage**: ~99% (estimated)
- **Bracket collisions**: 0
- **Quality**: Good
- **Domain**: Regional news simplified
- **Notes**: Good diversity from NHK

### Hirogaru Nihongo
- **URL**: https://hirogaru-nihongo.jp
- **Sentences**: ~506
- **Annotation coverage**: ~99% (estimated)
- **Bracket collisions**: 0
- **Quality**: Good
- **Domain**: Cultural/educational content
- **Notes**: Longer sentences, good variety

## Excluded Sources

### MATCHA Easy Japanese
- **URL**: https://matcha-jp.com/easy
- **Sentences**: ~13,713
- **Annotation coverage**: 66.2%
- **Bracket collisions**: 256
- **Quality**: Poor - DO NOT USE
- **Domain**: Travel/tourism
- **Reason for exclusion**:
  - Only 66.2% of kanji annotated (vs 99-100% for other sources)
  - JavaScript artifacts leaked through parser (`[index]`, etc.)
  - Including this data REDUCED model accuracy by 7.5pp
- **Potential recovery**: Re-scrape with improved parser, filter for >95% coverage

### JSUT Labels
- **Source**: JSUT speech corpus transcriptions
- **Reason for exclusion**: TTS-style readings not suitable for furigana
  - Uses long vowel mark (e.g., okaasan with prolonged vowels)
  - Particle conversions (ha -> wa, he -> e)
  - Would require complex normalization with high risk of errors

## Data Quality Checklist (for new sources)

Before adding a new data source, verify:
1. **Annotation coverage** > 95% (kanji with readings / total kanji)
2. **Zero bracket collisions** (no `[...]` patterns in raw text that aren't furigana)
3. **Consistent reading format** (hiragana, not katakana or romaji)
4. **Okurigana handling** matches our convention (trailing hiragana stripped from both surface and reading)
5. **Sentence segmentation** applied (one sentence per sample, not paragraphs)
