# Sudachi Mode C Error Analysis

**Date**: January 2026
**Test Set**: 340 sentences, 2,857 ground truth tokens
**Method**: Sudachi Mode C (SudachiPy with long-unit segmentation)

## Executive Summary

Sudachi Mode C achieves **63.5% token accuracy** on the full test set (1,813/2,857 correct).
Analysis of the 1,044 errors reveals:

| Error Category | Count | % of Errors | Root Cause |
|----------------|-------|-------------|------------|
| Segmentation mismatch | 978 | 93.7% | **Annotation style difference** |
| Reading error | 57 | 5.5% | Context-dependent readings |
| Missing token | 9 | 0.9% | Numeric expressions |

**Critical Finding**: 93.7% of errors are NOT learnable patterns but stem from a fundamental
mismatch between NHK's annotation style (kanji stems only) and Sudachi's tokenization
(full inflected forms).

## 1. Segmentation Mismatches (978 errors, 93.7%)

### 1.1 The Core Problem: Okurigana Boundaries

NHK Easy News annotates only the **kanji portion** of inflected words:
- 言**っ**た → annotates only 言 (い)
- 話**し**ます → annotates only 話 (はな)
- 考**え**る → annotates only 考 (かんが)

Sudachi tokenizes the **full word** including okurigana:
- 言った → 言っ (いっ) as one token
- 話します → 話し (はなし) as one token
- 考える → 考え (かんがえ) as one token

### 1.2 Statistics

| Sub-category | Count | % of Seg Errors |
|--------------|-------|-----------------|
| Single kanji in larger token | 874 | 89.4% |
| Compound word split | 70 | 7.2% |
| Other | 34 | 3.4% |

### 1.3 Top 20 Affected Patterns

| NHK Token | Reading | Sudachi Token | Reading | Count |
|-----------|---------|---------------|---------|-------|
| 言 | い | 言っ | いっ | 33 |
| 話 | はな | 話し | はなし | 31 |
| 言 | い | 言い | いい | 27 |
| 考 | かんが | 考え | かんがえ | 15 |
| 多 | おお | 多く | おおく | 14 |
| 使 | つか | 使う | つかう | 12 |
| 新 | あたら | 新しい | あたらしい | 11 |
| 始 | はじ | 始め | はじめ | 11 |
| 調 | しら | 調べ | しらべ | 9 |
| 高 | たか | 高く | たかく | 9 |
| 使 | つか | 使っ | つかっ | 9 |
| 金 | かね | お金 | おかね | 9 |
| 降 | ふ | 降り | ふり | 9 |
| 上 | あ | 上がり | あがり | 8 |
| 亡 | な | 亡くなっ | なくなっ | 8 |
| 続 | つづ | 続い | つづい | 8 |
| 亡 | な | 亡くなり | なくなり | 8 |
| 今 | いま | 今まで | いままで | 7 |
| 同 | おな | 同じ | おなじ | 7 |
| 大 | おお | 大きい | おおきい | 7 |

### 1.4 Examples

**Example 1: Verb Conjugation**
```
Sentence: 国は、土地をもらった人の税金を計算するために...決めています。
NHK:    決 → き
Sudachi: 決め → きめ
```

**Example 2: Adjective Inflection**
```
Sentence: 特に、東京都や沖縄県、福岡県で値段が大きく上がりました。
NHK:    大 → おお
Sudachi: 大きく → おおきく
```

**Example 3: Verb Te-form**
```
Sentence: この事件で、前川彰司さんが捕まりました。裁判で罪が決まって...
NHK:    言 → い
Sudachi: 言っ → いっ
```

**Example 4: Compound with Prefix**
```
Sentence: 前川さんは...お金も払っていると報道しました。
NHK:    金 → かね
Sudachi: お金 → おかね
```

**Example 5: Compound Split**
```
Sentence: 国は、土地をもらった人の税金を計算するために、毎年、日本中の...
NHK:    日本中 → にっぽんじゅう
Sudachi: 日本 → にっぽん (splits 中 separately)
```

### 1.5 Hypothesis

This is **NOT an error in Sudachi**. It's a fundamental difference in annotation philosophy:

- **NHK's goal**: Help learners understand kanji readings
- **Sudachi's goal**: Morphological analysis for NLP

NHK annotates the minimal kanji reading; Sudachi tokenizes complete morphemes.

---

## 2. Reading Errors (57 errors, 5.5%)

### 2.1 Categories

| Pattern | Count | % of Reading Errors |
|---------|-------|---------------------|
| 日 counter (にち vs か) | 21 | 36.8% |
| 米 ambiguity (こめ vs べい) | 8 | 14.0% |
| 日本人 (にほんじん vs にっぽんじん) | 7 | 12.3% |
| Time units (月, 年) | 3 | 5.3% |
| Voiced/unvoiced variants | 2 | 3.5% |
| Other context-dependent | 16 | 28.1% |

### 2.2 Examples

**Example 1: Day Counter**
```
Sentence: 32万ぐらいの土地を調べました...4年続けて、前の年より上がりました。
Surface: 年
NHK:     とし (year as noun)
Sudachi: ねん (year as counter)
```

**Example 2: Rice vs America**
```
Sentence: 2番目に多かった漢字は、「米」でした。米の価格が高くなって...
Surface: 米
NHK:     こめ (rice)
Sudachi: べい (America/prefix)
```

**Example 3: Japan Reading**
```
Sentence: 日本人は、この結婚を認めていませんでした。
Surface: 日本人
NHK:     にっぽんじん
Sudachi: にほんじん
```

**Example 4: Name Reading**
```
Sentence: 39年前、福井県で中学生の女の子が殺されました...前川彰司さんが...
Surface: 彰司
NHK:     しょうし
Sudachi: しょうじ
```

**Example 5: Counter Reading**
```
Sentence: 自民党は4日、トップの「総裁」を選ぶ選挙を行いました。
Surface: 日
NHK:     か (in 4日 = よっか)
Sudachi: にち
```

### 2.3 Hypothesis

These are **genuinely context-dependent readings** that require:
1. Understanding of semantic context (米 = rice vs America)
2. Knowledge of proper noun readings (names)
3. Counter/date pattern recognition (4日 = よっか)

**These ARE learnable patterns** with sufficient training data or specialized rules.

---

## 3. Missing Tokens (9 errors, 0.9%)

### 3.1 Pattern

All 9 missing tokens involve **numeric expressions** where NHK annotates the number:

| Expression | NHK Reading | Notes |
|------------|-------------|-------|
| 1 | ひと | in 1つ |
| 2 | ふた | in 2つ |
| 3 | みっ | in 3つ |
| 24 | にじゅうよっ | in 24日 |

### 3.2 Examples

**Example 1:**
```
Sentence: 長崎市にある浦上天主堂という教会には2つの鐘がありました。
Missing: 1 → ひと
Sudachi found: 長崎市, 浦上, 天主堂, 教会, 鐘...
```

**Example 2:**
```
Sentence: アメリカの研究所によると、日本の時間で7日、2つの火口が噴火しました。
Missing: 2 → ふた
```

### 3.3 Hypothesis

Sudachi doesn't annotate standalone numerals with readings. NHK does when they're
part of counter expressions. This requires **post-processing rules** for counters.

---

## 4. Conclusions and Recommendations

### 4.1 Error Summary

```
Total Errors: 1,044 (36.5% of tokens)

├── Segmentation (93.7%): ANNOTATION STYLE MISMATCH
│   └── Cannot be fixed by training - requires definition change
│
├── Reading (5.5%): CONTEXT-DEPENDENT
│   └── CAN be improved with ML or rules
│
└── Missing (0.9%): NUMERIC EXPRESSIONS
    └── CAN be fixed with post-processing rules
```

### 4.2 What This Means

| If Goal Is... | Recommendation |
|---------------|----------------|
| Match NHK exactly | Need to **redefine evaluation** to compare only kanji portions |
| Best furigana for learners | Current approach is **actually correct** (full readings are clearer) |
| Production system | **Hybrid approach** - dictionary + rules for edge cases |

### 4.3 Recommended Actions

#### Option A: Redefine Success Metric

Change evaluation to compare only the kanji-portion reading:
- Instead of: `言っ (いっ) vs 言 (い)` → MISMATCH
- Compare: `言 reading = い` in both → MATCH

**Expected accuracy boost**: ~90%+ (eliminating 874 okurigana errors)

#### Option B: Keep Current Metric, Accept Difference

Acknowledge that Sudachi's approach is pedagogically valid:
- `言っ` with reading `いっ` IS correct furigana
- NHK's choice to annotate only `言` is stylistic

#### Option C: Hybrid System for Reading Errors

For the 6.4% genuinely fixable errors:
1. **Counter rules**: 4日→よっか, 1つ→ひとつ, etc.
2. **Context classifier**: 米→こめ/べい based on surrounding text
3. **Proper noun dictionary**: Name readings

### 4.4 Implementation Priority

| Priority | Error Type | Fix | Effort | Impact |
|----------|------------|-----|--------|--------|
| 1 | Numeric counters | Rule-based | Low | +0.9% |
| 2 | Day/month readings | Pattern matching | Low | +2.0% |
| 3 | 米 ambiguity | Context classifier | Medium | +0.3% |
| 4 | Segmentation | Metric change | High | +30%* |

*If metric is changed to compare kanji portions only

---

## 5. Raw Data

### 5.1 Full Error Counts

```
Total GT tokens:     2,857
Correct matches:     1,813 (63.5%)
Errors:              1,044 (36.5%)

Segmentation:          978 (93.7% of errors)
  - Okurigana boundary:  874
  - Compound split:       70
  - Other:                34

Reading:                57 (5.5% of errors)
  - Day counter (日):     21
  - 米 ambiguity:          8
  - 日本人 reading:        7
  - Other:                21

Missing:                 9 (0.9% of errors)
  - All numeric expressions
```

### 5.2 Accuracy by Error Type (if fixed)

| Scenario | Accuracy |
|----------|----------|
| Current | 63.5% |
| + Fix missing numerics | 63.8% |
| + Fix reading errors | 65.5% |
| + Fix okurigana (metric change) | 94.1% |

---

*Analysis generated for thesis: Automatic Furigana Annotation for Japanese Language Learning Applications*
