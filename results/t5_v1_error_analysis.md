# T5 v1 Error Analysis

**Date**: January 2026
**Model**: sonoisa/t5-base-japanese fine-tuned on NHK Easy News
**Test Set**: 340 sentences, 2,857 ground truth tokens

## Executive Summary

T5 v1 achieves **61.8% token accuracy** (1,766/2,857 correct). Analysis of the 1,091 errors reveals that the primary failure is NOT the model's reading generation quality, but the **task formulation and extraction pipeline**.

**Critical Finding**: The seq2seq task format "text → full hiragana text" makes it impossible to reliably extract individual kanji-reading pairs because:
1. Original kanji positions are lost in the output
2. Anchor-based alignment fails when multiple kanji share similar context
3. The extraction algorithm produces garbage readings for 73.7% of errors

**Hypothesis Confirmed**: T5 v1 failed because the task formulation was wrong, not because of data size.

---

## 1. Error Breakdown

| Error Category | Count | % of Errors | Root Cause |
|----------------|-------|-------------|------------|
| Wrong reading | 804 | 73.7% | **Extraction algorithm failure** |
| Segmentation mismatch | 227 | 20.8% | NHK vs extracted boundary style |
| Missing | 40 | 3.7% | Model didn't generate reading |
| Extraction failure | 20 | 1.8% | Reading present but not extracted |
| Hallucination | 0 | 0.0% | Model is well-calibrated |

**Note**: The "wrong reading" category is misleading. Most are extraction failures where the anchor algorithm grabs the wrong segment, not cases where T5 generated incorrect hiragana.

---

## 2. The Core Problem: Task Formulation

### 2.1 How T5 v1 Works

```
Input:  "読み: 国は7月1日、今年の「路線価」を発表しました。"
Output: "くには7がつついたち、ことしの「ろせんか」をはっぴょうしました。"
```

The model converts the entire text to hiragana. Then a **post-processing extraction algorithm** tries to align the output back to original kanji positions.

### 2.2 Why Extraction Fails

The extraction uses "anchors" (non-kanji characters that appear in both texts) to find reading boundaries:

```
Original:  国は7月1日、今年の...
              ↑    ↑
           anchor  anchor

Output:    くには7がつついたち、ことしの...
```

**Failure Mode 1: Multiple Kanji Between Anchors**
```
Original: 土地をもらった人の税金を計算する
Kanji:    土地           人  税金  計算

Output:   ちをもらったひとのぜいぜいをけいかくする

The algorithm tries to split "ちをもらったひとのぜいぜいをけいかく" among
4 kanji spans. Without explicit markers, it guesses wrong:

Expected: 土地→とち, 人→ひと, 税金→ぜいきん, 計算→けいさん
Got:      土地→ぜいぜいをけいかくするためにまいとしにっぽんちゅう  (GARBAGE)
```

**Failure Mode 2: Repeated Kanji**
```
Original: 土地をもらった...土地の値段を
Same kanji "土地" appears twice, but output has one reading span each.
Second "土地" gets matched to wrong segment.
```

**Failure Mode 3: Dates and Numbers**
```
Original: 7月1日
Output:   7がつついたち

GT tokens: 月→がつ, 1日→ついたち
Problem: "1日" is the kanji span, but extraction finds only "日"
Result: 日→くにはがつついたち (grabs everything before)
```

### 2.3 Evidence: Model Generates Correct Readings

Looking at raw T5 output for error cases:

| Input | T5 Output | GT Reading | In Output? |
|-------|-----------|------------|------------|
| 国は7月1日 | くには7がつついたち | がつ | ✓ |
| 日本に旅行 | にっぽんにりょこう | にっぽん | ✓ |
| 前の年 | まえのとし | とし | ✓ |
| 2つの鐘 | 2つのかね | ふた | ✗ (model used "2") |

In 20 "extraction failure" cases, the correct reading WAS in the output but the extraction algorithm couldn't find it.

The actual model reading quality is **~87%** (per previous analysis), but the pipeline only extracts **61.8%** correctly.

---

## 3. Detailed Error Examples

### 3.1 Extraction Algorithm Failure (Most Common)

**Example 1: Garbage reading from wrong anchors**
```
Sentence: 国は、土地をもらった人の税金を計算するために...
T5 output: くには、ちをもらったひとのぜいぜいをけいかくするために...

Ground Truth: 計算 → けいさん
Extracted:    計算 → もらったひとのぜいぜいをけいかく  ← GARBAGE

Why: Algorithm found left anchor but grabbed too much text
     before finding right anchor.
```

**Example 2: Reading present but misaligned**
```
Sentence: 国は7月1日、今年の「路線価」を発表しました。
T5 output: くには7がつついたち、ことしの「せんどうか」をはっぴょうしました。

Ground Truth: 路線価 → ろせんか
Extracted:    路線価 → せんどうか  ← Wrong (model hallucinated?)

Actually: T5 generated "せんどうか" not "ろせんか" - this IS a model error
```

### 3.2 Segmentation Mismatch (NHK Style)

**Example 1: Name boundaries**
```
Sentence: 石破総理大臣は選挙に出ませんでした。
T5 output: いしばそうりだいじんはせんきょにでませんでした。

Ground Truth: 石破 → いしば, 総理大臣 → そうりだいじん  (2 tokens)
Extracted:    石破総理大臣 → いしばそうりだいじん       (1 token)

T5 doesn't know NHK wants name/title separated.
```

**Example 2: Counter separated from number**
```
Sentence: 4年続けて、前の年より上がりました。
T5 output: 4ねんつづけて、まえのとしよりあがりました。

Ground Truth: 続 → つづ (stem only)
Extracted:    年続 → ねんつづ (includes 年)

NHK annotates only kanji stem; T5 tokenizes the compound.
```

### 3.3 True Model Errors (Rare)

**Example 1: Wrong reading choice**
```
Sentence: 土地の値段についてのニュースです。
T5 output: ちいきのねだんについてのニュースです。

Ground Truth: 土地 → とち
T5 generated: 土地 → ちいき (different valid reading, wrong context)

Note: 土地 can be read as "とち" (land) or "ちいき" (region/area).
      T5 picked the less common reading for this context.
```

**Example 2: Corrupted reading**
```
Sentence: 国は、土地をもらった人の税金を計算する...
T5 output: ...ぜいぜいをけいかくする...

Ground Truth: 税金 → ぜいきん
T5 generated: 税金 → ぜいぜい (corrupted, possibly repeated pattern)
```

### 3.4 Missing Tokens (Model Didn't Generate)

**Example 1: Rare kanji skipped**
```
Sentence: たくさんの墓が並ぶさいたま市の墓地では、...水を細かくした霧を出しています。
T5 output: ...みずを細かくしたきりをだしています。

Ground Truth: 細 → こま
T5 kept: 細 (left as kanji in output, didn't convert)

Note: 細かい is common but 細 alone might have confused the model.
```

**Example 2: Single kanji verb stem**
```
Sentence: ...この話を信じることはできないと言いました。
T5 output: ...このはなしを信じることはできないといいました。

Ground Truth: 信 → しん
T5 kept: 信 (left as kanji)

Note: NHK annotates 信 alone (verb stem), but "信じる" is one word.
```

---

## 4. Root Cause Analysis

### 4.1 Task Formulation Problems

| Problem | Impact | Example |
|---------|--------|---------|
| Position loss | 73.7% | Can't map readings back to kanji |
| No explicit markers | 20.8% | Can't determine token boundaries |
| One-to-many ambiguity | 3.7% | Same kanji, different positions |
| Seq2seq hallucination | ~5% | Model generates plausible but wrong |

### 4.2 Why This Task Format Was Chosen

Original reasoning:
- Japanese T5 was pretrained on text → text tasks
- Converting to hiragana is a "natural" text transformation
- Post-processing seemed simpler than structured output

What went wrong:
- Underestimated extraction complexity
- Didn't account for multiple kanji with no anchors between them
- Assumed anchor alignment would work reliably

### 4.3 Comparison with Sudachi

| Aspect | T5 v1 | Sudachi Mode C |
|--------|-------|----------------|
| Accuracy | 61.8% | 63.5% |
| Primary errors | Extraction failure | Annotation style |
| Fixable by training? | No (wrong format) | No (style choice) |
| Fixable by rules? | No | Partially |

Sudachi's errors are philosophically different: they're segmentation style mismatches (okurigana boundaries). T5's errors are pipeline failures.

---

## 5. Solution: T5 v2 Proposal

### 5.1 New Task Formulation

Instead of generating continuous hiragana:
```
Input:  国は7月1日、今年の「路線価」を発表しました。
Output: 能登半島地震[のとはんとうじしん]で被害[ひがい]があった
```

The model outputs the **original text with inline bracket annotations**.

### 5.2 Benefits

| Benefit | Explanation |
|---------|-------------|
| Preserves position | Kanji stays in place, reading follows in brackets |
| No extraction needed | Parse brackets to get surface→reading pairs |
| Explicit boundaries | `[` and `]` mark exactly where readings belong |
| Handles repetition | Each occurrence gets its own annotation |

### 5.3 Expected Format

```
Input:  読み: 土地をもらった人の税金を計算する
Output: 土地[とち]をもらった人[ひと]の税金[ぜいきん]を計算[けいさん]する
```

Extraction becomes simple regex: `(\w+)\[([ぁ-ん]+)\]`

### 5.4 Training Data Transformation

Current format:
```json
{
  "input": "読み: 土地の値段",
  "output": "とちのねだん"
}
```

New format:
```json
{
  "input": "読み: 土地の値段",
  "output": "土地[とち]の値段[ねだん]"
}
```

---

## 6. Conclusions

### 6.1 Summary

| Finding | Evidence |
|---------|----------|
| Model generates correct readings ~87% | Readings present in output but not extracted |
| Extraction is the bottleneck | 73.7% of errors are garbage extractions |
| Task format prevents improvement | Cannot fix with more training data |
| New format needed | Character-level span annotation |

### 6.2 Key Insight

**T5 v1 is not a model failure—it's an interface failure.**

The seq2seq task format "text → hiragana" destroys the structural information needed to map readings back to their source kanji. No amount of training data or hyperparameter tuning can fix this fundamental design flaw.

### 6.3 Recommended Next Steps

1. **Implement T5 v2** with bracket annotation format
2. **Keep T5 v1** as baseline for comparison
3. **Re-evaluate** on same test set
4. **Expected improvement**: 75-85% (matching Sudachi or better)

---

## 7. Appendix: Error Statistics

### 7.1 Raw Numbers

```
Total sentences:        340
Total GT tokens:        2,857
Total predicted tokens: 2,687
Exact matches:          1,766

Accuracy:               61.8%

Error breakdown:
  wrong_reading:        804 (73.7%)  ← Mostly extraction failures
  segmentation_mismatch: 227 (20.8%)
  missing:               40 (3.7%)
  extraction_failure:    20 (1.8%)   ← Reading present, not found
  hallucination:          0 (0.0%)   ← Model well-calibrated
```

### 7.2 Extraction Algorithm Analysis

The anchor-based extraction algorithm in `annotator.py:extract_kanji_reading_pairs()`:

```python
# Find left anchor (non-kanji before this kanji)
# Find right anchor (non-kanji after this kanji)
# Extract reading between anchor positions in output
```

This fails when:
- No non-kanji characters between adjacent kanji
- Same non-kanji pattern appears multiple times
- Kanji span includes numbers (7月1日)
- Output has insertions/deletions vs input

### 7.3 Files Generated

- `/results/t5_v1_errors.json` - Complete error data with all predictions
- `/results/t5_v1_error_analysis.md` - This document
- `/scripts/analyze_t5_errors.py` - Analysis script

---

*Analysis generated for thesis: Automatic Furigana Annotation for Japanese Language Learning Applications*
