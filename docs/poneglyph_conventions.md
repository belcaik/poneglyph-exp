# Poneglyph Annotation Conventions v1.0

## Purpose
This document defines how Japanese text should be annotated with furigana for the Poneglyph learning platform. These conventions prioritize **learner comprehension** over linguistic decomposition. The goal is that a learner sees complete conceptual units with their readings, and can explore sub-components via the UI.

## Core Principle
**Annotate conceptual units, not morphological atoms.** If a sequence of characters forms a single concept or action in context, it is one span with one reading.

---

## 1. Compound Nouns (複合名詞)

**Rule: Annotate as a single span when the compound represents a single concept.**

| Text | Annotation | Reasoning |
|------|-----------|-----------|
| 幼稚園 | 幼稚園→ようちえん | Single concept: kindergarten |
| 東京都 | 東京都→とうきょうと | Single concept: Tokyo Metropolis |
| 図書館 | 図書館→としょかん | Single concept: library |
| 北海道 | 北海道→ほっかいどう | Single concept: Hokkaido |
| 運動会 | 運動会→うんどうかい | Single concept: sports day |
| 携帯電話 | 携帯電話→けいたいでんわ | Single concept: mobile phone |

**Exception:** If the compound is used in a context where its components are being contrasted or individually referenced, annotate separately. Example: 「東京と京都の"都"は同じ漢字です」→ here 都 is discussed as its own concept.

## 2. Verb Chains (動詞の連結)

**Rule: Annotate the complete verb phrase including auxiliaries as a single span.**

| Text | Annotation | Reasoning |
|------|-----------|-----------|
| 食べている | 食べている→たべている | Complete action: is eating |
| 読んでしまった | 読んでしまった→よんでしまった | Complete action: ended up reading |
| 走っていく | 走っていく→はしっていく | Complete action: go running off |
| 書かれている | 書かれている→かかれている | Complete action: is written |
| 食べさせられた | 食べさせられた→たべさせられた | Complete action: was made to eat |
| 話してくれました | 話してくれました→はなしてくれました | Complete action: told (me) kindly |
| 見えなくなっていた | 見えなくなっていた→みえなくなっていた | Complete action: had become invisible |
| 飲みたくなかった | 飲みたくなかった→のみたくなかった | Complete action: didn't want to drink |

**This includes:**
- て-form + auxiliary (いる、ある、しまう、くる、いく、みる、おく、くれる、もらう、あげる)
- Passive (られる)、causative (させる)、causative-passive (させられる)
- Potential (られる/える)
- たい-form (飲みたい)
- ない-form and its inflections (食べなかった)
- ます-form and its inflections (食べました、食べません)
- Compound verbs (取り出す、見つかる、引っ越す)
- Chains of the above (食べさせられてしまいました)

**What is NOT included in the verb span:**
- Sentence-final particles: よ、ね、な、か、かな
- Conjunctive particles that connect clauses: が、けど、から、ので、のに、し
- The topic/subject marker: は、が (when functioning as subject marker after a nominalized verb)

## 3. い-Adjectives (い形容詞)

**Rule: Annotate the complete inflected form.**

| Text | Annotation |
|------|-----------|
| 大きい | 大きい→おおきい |
| 大きく | 大きく→おおきく |
| 大きくない | 大きくない→おおきくない |
| 大きかった | 大きかった→おおきかった |
| 大きくなった | 大きくなった→おおきくなった |
| 新しくなっている | 新しくなっている→あたらしくなっている |

## 4. な-Adjectives and Nouns with Copula

**Rule: Include だ/な/で/に when directly attached, but NOT です/でした (polite copula).**

| Text | Annotation |
|------|-----------|
| 静かな | 静かな→しずかな |
| 静かに | 静かに→しずかに |
| 静かだ | 静かだ→しずかだ |
| 静かです | 静か→しずか (です is separate polite copula) |
| 問題なんじゃない | 問題→もんだい (なんじゃない is colloquial copula phrase) |

## 5. Proper Nouns (固有名詞)

**Rule: Always annotate. Flag as proper noun for distinct UI treatment.**

| Text | Annotation | Type |
|------|-----------|------|
| 田中 | 田中→たなか | person_name |
| 東京 | 東京→とうきょう | place_name |
| 北海道 | 北海道→ほっかいどう | place_name |
| 安倍 | 安倍→あべ | person_name |
| 鈴木一朗 | 鈴木一朗→すずきいちろう | person_name |

**Note:** Proper noun readings may be non-standard (名乗り読み). The annotation should reflect the actual reading of the name, not the standard kanji reading.

## 6. Numbers and Counters (数詞・助数詞)

**Rule: Annotate the number + counter as a single unit when they form a combined reading.**

| Text | Annotation | Reasoning |
|------|-----------|-----------|
| 2人 | 2人→ふたり | Combined reading (not にじん) |
| 3人 | 3人→さんにん | Combined reading |
| 1日 | 1日→ついたち or いちにち | Context-dependent |
| 20日 | 20日→はつか | Special counter reading |
| 何人 | 何人→なんにん | Interrogative + counter |
| 1つ | 1つ→ひとつ | Native number + counter |

**When the number is Arabic and the counter is standard, only annotate the counter portion if it has kanji:**
| Text | Annotation |
|------|-----------|
| 100個 | 100個→ひゃっこ |
| 5時間 | 5時間→ごじかん |

## 7. Mixed Kanji-Hiragana Words

**Rule: Annotate the complete word including the hiragana portion.**

| Text | Annotation |
|------|-----------|
| 子ども | 子ども→こども |
| お母さん | お母さん→おかあさん |
| お父さん | お父さん→おとうさん |
| 一つ | 一つ→ひとつ |
| 取り扱い | 取り扱い→とりあつかい |

## 8. Hiragana-Only Words

**Rule: Do NOT annotate.** Words written entirely in hiragana already show their reading.

Exception: Words where the hiragana spelling might confuse a learner about pronunciation (rare).

## 9. Katakana Words

**Rule: Do NOT annotate.** Katakana is already phonetic.

Exception: Unusual katakana compounds where reading might not be obvious (rare, handle case by case).

## 10. Particles and Grammatical Markers

**Rule: Do NOT annotate standalone particles.**

は、が、を、に、で、と、も、の、へ、や、か、から、まで、より、etc. are never annotated as separate spans. They may be included within a verb/adjective span when part of the inflected form.

## 11. What NOT to Annotate

- Pure hiragana text
- Pure katakana text
- Arabic numbers without kanji counters
- Latin characters / romaji
- Punctuation
- Particles (standalone)

## 12. Output Format

Each annotation is a tuple:
```json
{
  "surface": "食べている",
  "reading": "たべている",
  "start": 5,
  "end": 10,
  "type": "verb"  // noun, verb, adjective, proper_noun, counter, compound_noun
}
```

The `type` field enables UI differentiation (e.g., proper nouns in different color).

---

## Guiding Philosophy

When in doubt, ask: **"If a student sees this span with its furigana, will they understand the complete concept?"**

- If yes → the span is correctly sized
- If no (they only see part of the concept) → expand the span
- If the span is too large (contains multiple unrelated concepts) → split it
