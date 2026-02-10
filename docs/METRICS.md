# Evaluation Metrics

## Primary Metric: Token-level Accuracy

For each kanji token in the test set:
- Compare predicted reading (hiragana) to ground truth
- Exact string match required (no partial credit)
- Accuracy = correct predictions / total ground truth tokens

This measures whether the model correctly annotates each kanji with its reading.

## Secondary Metrics

### Per-Source Accuracy
Break down accuracy by data source to identify:
- Which domains the model handles well
- Which domains need more training data
- Whether a source is helping or hurting overall performance

### Annotation Coverage (for data sources)
```
coverage = (kanji with readings) / (total kanji in text)
```
Sources with <95% coverage should be excluded or cleaned.
This metric caught MATCHA's 66.2% coverage issue.

### Bracket Collision Rate (for data sources)
```
collisions = sentences containing [...] patterns that aren't furigana annotations
```
Must be zero for clean training data.

## Test Sets

### Comparable Test Set (v6, primary)
Used for comparing models trained on different data compositions.
1,498 sentences from v5 test set excluding MATCHA:
- NHK: 333 sentences
- Kahoku: 183 sentences
- UD GSD: 804 sentences
- UD PUD: 100 sentences
- Hirogaru: 78 sentences
- Total ground truth tokens: 12,558

### v6 Test Set
1,304 sentences from stratified 80/10/10 split of non-MATCHA data:
- NHK: 229 sentences
- Kahoku: 120 sentences
- UD GSD: 804 sentences
- UD PUD: 100 sentences
- Hirogaru: 51 sentences

### Legacy v4 Test Set
Used for backward compatibility with older model results.
Contains MATCHA sentences, so not suitable for v6 comparisons.

## Error Categories

Known failure modes in furigana systems:

| Category | Example | Expected | Common Error |
|----------|---------|----------|--------------|
| Numeric counters | 2人 | ふたり | にひと |
| Date expressions | 3日 | みっか | さんにち |
| Ateji (irregular) | 今日 | きょう | こんにち |
| Verb conjugation | 行った | いった | おこなった |
| Proper nouns | 伊達 | だて | context-dependent |
| Rare readings | 辛うじて | かろうじて | つらうじて |
