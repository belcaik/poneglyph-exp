#!/usr/bin/env python3
"""
Normalize furigana annotations from stem-only to morpheme-complete convention.

Version 2: Conservative expansion with auxiliary boundary detection.

Key changes from v1:
- Te/de form is the natural expansion boundary (stop BEFORE auxiliaries)
- AUXILIARY_AFTER_TE patterns are hard stops (ている, てしまう, てくる, etc.)
- NEVER_ABSORB patterns block expansion (かもしれない, たり, etc.)
- CHANGE_OF_STATE patterns are boundaries (なくなる, にくい, やすい)
- Adjective く-form + なる detection (大きくなる → stop at 大きく)
- Ta-form stops: り (listing), ら (conditional)
- Limited compound verb continuations (replace broad VERB_CONTINUATION_PATTERNS)
- Length-based flagging: ≤3 auto-expand, 4-5 expand+log, >5 truncate+log
- Target: surfaces >6 chars < 3%
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

INPUT_DIR = Path("data/splits_v6_no_matcha")
OUTPUT_DIR = Path("data/splits_v7_normalized")
DECISIONS_FILE = Path("data/normalization_decisions.json")


def is_hiragana(ch: str) -> bool:
    return '\u3040' <= ch <= '\u309f'


def is_kanji(ch: str) -> bool:
    return '\u4e00' <= ch <= '\u9fff' or '\u3400' <= ch <= '\u4dbf'


def surface_ends_with_kanji(surface: str) -> bool:
    return len(surface) > 0 and is_kanji(surface[-1])


def strip_kahoku_parens(text: str) -> str:
    return text.replace('()', '')


# --- Boundary patterns ---

PARTICLE_CHARS = set('はがをにでとのもやへかし')

NEVER_ABSORB = sorted([
    'かもしれない', 'かもしれません',
    'なければならない', 'なければなりません', 'なければいけない',
    'なければ', 'なくても',
    'ことができる', 'ことができます',
    'ことがある', 'ことがあります',
    'ことにする', 'ことにした', 'ことになる', 'ことになった',
    'ことは', 'ことが', 'ことに', 'ことを', 'ことで', 'ことも', 'こと',
    'ような', 'ように', 'ようだ', 'ようです', 'よう',
    'ための', 'ために', 'ためか', 'ため',
    'ところ', 'ところが', 'ところで',
    'ほどだ', 'ほどの', 'ほどで', 'ほど',
    'まで', 'から', 'より', 'ほか', 'など',
    'それ', 'これ', 'あれ', 'どれ',
    'その', 'この', 'あの', 'どの',
    'うわさ', 'ひと', 'もの', 'まま', 'あと',
    'うち', 'ころ', 'とき', 'ひま', 'ほう',
    'ひじ', 'ひざ', 'ひげ', 'ひも', 'ひふ',
    'たち', 'さん', 'さま', 'くん', 'ちゃん',
    'ごと', 'ずつ',
    'おり', 'はず', 'わけ', 'そう',
    'お',
], key=len, reverse=True)

AUXILIARY_AFTER_TE = sorted([
    'いる', 'いた', 'いない', 'いなかった',
    'います', 'いました', 'いません', 'いませんでした',
    'いたら', 'いたり', 'いれば', 'いても', 'いては',
    'しまう', 'しまった', 'しまい', 'しまって', 'しまえ', 'しまわ',
    'しまいます', 'しまいました',
    'くる', 'きた', 'きて', 'きます', 'きました', 'くれ', 'くれば',
    'みる', 'みた', 'みて', 'みます', 'みました', 'みれば', 'みよう',
    'もらう', 'もらった', 'もらって', 'もらい', 'もらえ', 'もらえる',
    'もらいます', 'もらいました',
    'あげる', 'あげた', 'あげて', 'あげます',
    'おく', 'おいた', 'おいて', 'おきます', 'おきました',
    'ほしい', 'ほしかった', 'ほしく',
], key=len, reverse=True)

# Change-of-state patterns — always stop before these
CHANGE_OF_STATE = sorted([
    'なくなる', 'なくなった', 'なくなって', 'なくなり',
    'なくなります', 'なくなりました',
    'にくい', 'にくく', 'にくかった',
    'やすい', 'やすく', 'やすかった',
    'すぎる', 'すぎた', 'すぎて', 'すぎます',
    'はじめる', 'はじめた', 'はじめて', 'はじめます',
    'つづける', 'つづけた', 'つづけて',
    'おわる', 'おわった', 'おわって',
    'なおす', 'なおした', 'なおして',
    # きる auxiliary (potential: 載せきれない, 食べきれません)
    'きれる', 'きれない', 'きれません', 'きれた', 'きれて', 'きれ',
], key=len, reverse=True)

# Adjective く-form suffixes that precede なる (change-of-state)
# When okurigana ends with one of these + く, treat following なる as boundary
# Examples: 大き→く→なる, 強→く→なる, 近→く→なる, 美し→く→なる
ADJ_KU_ENDINGS = frozenset(['く', 'きく', 'しく', 'さく'])

# なる patterns that stop after adjective く-form
NARU_PATTERNS = sorted([
    'なって', 'なった', 'なる', 'なり', 'なります', 'なりました', 'ない',
], key=len, reverse=True)

TE_FORMS_2 = frozenset([
    'って', 'いて', 'して', 'んで', 'けて', 'せて',
    'めて', 'べて', 'ねて', 'れて', 'えて', 'ちて',
])

TA_FORMS_2 = frozenset([
    'った', 'いた', 'した', 'んだ', 'けた', 'せた',
    'めた', 'べた', 'ねた', 'れた', 'えた',
])

TA_FORM_STOPS = ['り', 'ら']

COMPOUND_CONTINUATIONS = {
    'が': [r'^がる', r'^がり', r'^がった', r'^がって', r'^がります', r'^がりました', r'^がれ'],
    'か': [r'^かる', r'^かり', r'^かった', r'^かって', r'^かります', r'^かりました',
           r'^かせる', r'^かせた', r'^かせて', r'^かせられ'],
    'と': [r'^とる', r'^とり', r'^とった', r'^とって', r'^とめ', r'^とめる',
           r'^とば', r'^とび', r'^とぶ', r'^とし', r'^とお', r'^とけ', r'^とく'],
    'の': [r'^のぼ', r'^のこ', r'^のせ', r'^のべ', r'^のび', r'^のむ', r'^のま',
           r'^のみ', r'^のり', r'^のぞ'],
    'に': [r'^にく', r'^にん'],
    'で': [r'^でき'],
}

SHI_OKURIGANA_PATTERNS = [
    r'^しい', r'^しく', r'^しさ', r'^しかった',
    r'^し$',
    r'^した($|[はがをにでとのもやへか。、！？「」])',
    r'^して($|[はがをにでとのもやへか。、！？「」]|も)',
    r'^します', r'^しました', r'^しません',
    r'^する',
    r'^してい', r'^してし', r'^してく', r'^してみ', r'^してお', r'^してほ', r'^してあ', r'^してもら',
]


def starts_with_never_absorb(text: str) -> bool:
    for pattern in NEVER_ABSORB:
        if text.startswith(pattern):
            return True
    return False


def starts_with_change_of_state(text: str) -> bool:
    for pattern in CHANGE_OF_STATE:
        if text.startswith(pattern):
            return True
    return False


def is_adj_ku_naru_boundary(trailing: str, end: int) -> bool:
    """Check if position `end` is right after an adjective く-form and
    the remaining text starts with a なる pattern (change-of-state).

    Examples: 大き+く+なる → stop at く. 強+く+なった → stop at く.
    Does NOT fire for compound verbs like 亡+くなる where くなる is one word.
    Distinguishing rule: if okurigana is ONLY く (single char) and the full
    trailing is a known compound pattern (くなる, くなり, etc.), it's a
    compound verb and we should NOT stop. If oku has multi-char adj suffix
    (きく, しく, さく), it's definitely an adjective.
    """
    if end < 1 or trailing[end-1] != 'く':
        return False

    rest = trailing[end:]
    if not any(rest.startswith(p) for p in NARU_PATTERNS):
        return False

    oku_so_far = trailing[:end]

    # Multi-char adjective suffixes: always treat as change-of-state
    for suffix in ADJ_KU_ENDINGS:
        if len(suffix) > 1 and oku_so_far.endswith(suffix):
            return True

    # Single く: ambiguous — compound verb (亡くなる) vs adjective (強くなる)
    # Heuristic: if trailing く is preceded by nothing (oku is just く),
    # then it might be a compound verb. We treat this as NOT a boundary
    # and let the length-based logging capture it for review.
    if oku_so_far == 'く':
        return False

    # Otherwise (く preceded by other okurigana like り, etc.): treat as adj boundary
    return True


def starts_with_auxiliary(text: str) -> bool:
    for pattern in AUXILIARY_AFTER_TE:
        if text.startswith(pattern):
            return True
    return False


def is_at_te_form_boundary(trailing: str, end: int) -> bool:
    if end >= 2 and trailing[end-2:end] in TE_FORMS_2:
        return True
    if end >= 1 and trailing[end-1] == 'て':
        if end < 2 or trailing[end-2] not in 'っいしんけせめべねれえち':
            return True
    if end >= 2 and trailing[end-2:end] == 'んで':
        return True
    return False


def is_at_ta_form_boundary(trailing: str, end: int) -> bool:
    if end >= 2 and trailing[end-2:end] in TA_FORMS_2:
        return True
    if end >= 1 and trailing[end-1] == 'た':
        if end < 2 or trailing[end-2] not in 'っいしんけせめべねれえ':
            return True
    return False


def is_shi_okurigana(rest: str) -> bool:
    return any(re.match(p, rest) for p in SHI_OKURIGANA_PATTERNS)


def get_shi_okurigana_length(rest: str) -> int:
    best = 0
    for p in SHI_OKURIGANA_PATTERNS:
        m = re.match(p, rest)
        if m:
            match_len = len(m.group(0))
            if p.startswith(r'^してい') or p.startswith(r'^してし') or \
               p.startswith(r'^してく') or p.startswith(r'^してみ') or \
               p.startswith(r'^してお') or p.startswith(r'^してほ') or \
               p.startswith(r'^してあ') or p.startswith(r'^してもら'):
                match_len = 2  # Just して
            if match_len > best:
                best = match_len
    return max(best, 1)


def check_compound_continuation(ch: str, rest: str) -> int:
    if ch not in COMPOUND_CONTINUATIONS:
        return 0
    best = 0
    for pattern in COMPOUND_CONTINUATIONS[ch]:
        m = re.match(pattern, rest)
        if m and len(m.group(0)) > best:
            best = len(m.group(0))
    return best


def find_okurigana_end(trailing: str, max_len: int) -> tuple:
    """Find conservative okurigana boundary in trailing hiragana.
    Returns (end_position, used_compound_continuation)."""
    end = 0
    used_compound = False
    while end < len(trailing) and end < max_len:
        ch = trailing[end]
        if not is_hiragana(ch):
            break

        rest = trailing[end:]

        if starts_with_never_absorb(rest):
            break
        if starts_with_change_of_state(rest):
            break
        if is_adj_ku_naru_boundary(trailing, end):
            break
        # Detect くなる compound verb pattern (亡くなる, 無くなる, etc.)
        # If oku so far is just く and rest starts with なる pattern → compound
        if end >= 1 and trailing[end-1] == 'く' and trailing[:end] == 'く':
            if any(rest.startswith(p) for p in NARU_PATTERNS):
                used_compound = True

        if is_at_te_form_boundary(trailing, end):
            if starts_with_auxiliary(rest):
                break

        if is_at_ta_form_boundary(trailing, end):
            if any(rest.startswith(s) for s in TA_FORM_STOPS):
                break

        if ch in PARTICLE_CHARS:
            if ch == 'し' and is_shi_okurigana(rest):
                shi_len = get_shi_okurigana_length(rest)
                end += shi_len
                if end >= 2 and trailing[end-2:end] == 'して':
                    if end < len(trailing) and end < max_len:
                        if starts_with_auxiliary(trailing[end:]):
                            break
                continue

            comp_len = check_compound_continuation(ch, rest)
            if comp_len > 0:
                end += comp_len
                used_compound = True
                continue

            if ch == 'で' and end > 0 and trailing[end-1] == 'ん':
                end += 1
                continue

            break

        end += 1

        # ず is always word-final (negative connective: 知らず)
        if end >= 1 and trailing[end-1] == 'ず':
            break

        # きな/さな: prenominal adjective forms (大きな, 小さな)
        # Always followed by a noun — stop scanning
        if end >= 2 and trailing[end-2:end] in ('きな', 'さな'):
            break

    return end, used_compound


def find_truncation_boundary(okurigana: str) -> Optional[int]:
    """Find a safe truncation point for over-long okurigana."""
    best = None
    for i in range(min(5, len(okurigana) - 1)):
        if i + 2 <= len(okurigana):
            segment = okurigana[i:i+2]
            if segment in TE_FORMS_2 | TA_FORMS_2:
                boundary = i + 2
                if boundary < len(okurigana):
                    best = boundary

    if best is not None:
        return best

    basic_ends = set('るいくすつぬぶむ')
    last_basic = None
    for i in range(min(5, len(okurigana))):
        if okurigana[i] in basic_ends:
            last_basic = i + 1
    if last_basic is not None and last_basic < len(okurigana):
        return last_basic

    return None


def determine_okurigana(surface, reading, trailing, next_token_start, current_end,
                        sentence, decisions):
    """Determine okurigana to append. Returns okurigana string or None."""
    if not trailing:
        return None

    max_len = len(trailing)
    if next_token_start is not None:
        space = next_token_start - current_end
        if space <= 0:
            return None
        max_len = min(max_len, space)
    if max_len <= 0:
        return None

    if starts_with_never_absorb(trailing[:max_len]):
        return None

    first_ch = trailing[0]
    is_compound = False

    # Non-particle first → scan for okurigana
    if first_ch not in PARTICLE_CHARS:
        end, has_compound = find_okurigana_end(trailing, max_len)
        if end <= 0:
            return None
        okurigana = trailing[:end]
        if has_compound:
            is_compound = True

    # し first → check patterns
    elif first_ch == 'し':
        rest = trailing[:max_len]
        if is_shi_okurigana(rest):
            shi_len = get_shi_okurigana_length(rest)
            total = min(shi_len, max_len)
            if total >= 2 and trailing[:total].endswith('て'):
                if total < max_len and starts_with_auxiliary(trailing[total:]):
                    pass
            okurigana = trailing[:total]
        else:
            return None

    # Other particle first → check compound verb continuation
    else:
        comp_len = check_compound_continuation(first_ch, trailing[:max_len])
        if comp_len > 0:
            is_compound = True
            remaining = trailing[comp_len:]
            remaining_max = max_len - comp_len
            if remaining_max > 0 and remaining:
                extra, _ = find_okurigana_end(remaining, remaining_max)
                okurigana = trailing[:comp_len + extra]
            else:
                okurigana = trailing[:comp_len]
        else:
            return None

    # --- Length-based decision logging ---
    if len(okurigana) <= 3:
        return okurigana

    elif len(okurigana) <= 5:
        decisions.append({
            "sentence": sentence.get("text", "")[:100],
            "source": sentence.get("source", ""),
            "original_surface": surface,
            "original_reading": reading,
            "context_after": trailing[:25],
            "decision": "expand",
            "new_surface": surface + okurigana,
            "okurigana": okurigana,
            "length": len(okurigana),
            "reasoning": f"Medium okurigana ({len(okurigana)} chars), auto-expanded",
        })
        return okurigana

    else:
        # Compound verb continuations: don't truncate, just log
        if is_compound:
            decisions.append({
                "sentence": sentence.get("text", "")[:100],
                "source": sentence.get("source", ""),
                "original_surface": surface,
                "original_reading": reading,
                "context_after": trailing[:30],
                "decision": "expand_compound",
                "new_surface": surface + okurigana,
                "okurigana": okurigana,
                "length": len(okurigana),
                "reasoning": f"Compound verb ({len(okurigana)} chars), kept full expansion",
            })
            return okurigana

        boundary = find_truncation_boundary(okurigana)
        if boundary is not None and boundary < len(okurigana):
            truncated = okurigana[:boundary]
            decisions.append({
                "sentence": sentence.get("text", "")[:100],
                "source": sentence.get("source", ""),
                "original_surface": surface,
                "original_reading": reading,
                "context_after": trailing[:30],
                "decision": "truncate",
                "new_surface": surface + truncated,
                "would_have_been": surface + okurigana,
                "okurigana": truncated,
                "original_okurigana": okurigana,
                "length": len(truncated),
                "original_length": len(okurigana),
                "reasoning": (f"Over-expansion ({len(okurigana)} chars '{okurigana}'), "
                              f"truncated to {len(truncated)} chars '{truncated}'"),
            })
            return truncated
        else:
            decisions.append({
                "sentence": sentence.get("text", "")[:100],
                "source": sentence.get("source", ""),
                "original_surface": surface,
                "original_reading": reading,
                "context_after": trailing[:30],
                "decision": "expand_uncertain",
                "new_surface": surface + okurigana,
                "okurigana": okurigana,
                "length": len(okurigana),
                "reasoning": f"Long okurigana ({len(okurigana)} chars), no clear truncation boundary",
            })
            return okurigana


def find_token_positions(clean_text, tokens):
    positions = []
    search_start = 0
    for tok in tokens:
        surface = tok["surface"]
        idx = clean_text.find(surface, search_start)
        if idx == -1:
            idx = clean_text.find(surface)
        if idx == -1:
            positions.append(None)
            continue
        end = idx + len(surface)
        positions.append((idx, end))
        search_start = end
    return positions


def expand_token(tok, tok_pos, next_tok_pos, clean_text, sentence, decisions):
    surface = tok["surface"]
    reading = tok["reading"]

    if tok_pos is None:
        return tok
    start, end = tok_pos

    if not surface_ends_with_kanji(surface):
        return tok
    if end >= len(clean_text) or not is_hiragana(clean_text[end]):
        return tok

    trail_end = end
    while trail_end < len(clean_text) and is_hiragana(clean_text[trail_end]):
        trail_end += 1
    trailing = clean_text[end:trail_end]
    if not trailing:
        return tok

    next_start = next_tok_pos[0] if next_tok_pos else None
    okurigana = determine_okurigana(
        surface, reading, trailing, next_start, end, sentence, decisions)
    if not okurigana:
        return tok

    new_surface = surface + okurigana
    new_reading = reading + okurigana

    expected = clean_text[start:start + len(new_surface)]
    if expected != new_surface:
        decisions.append({
            "sentence": sentence.get("text", "")[:100],
            "source": sentence.get("source", ""),
            "original_surface": surface,
            "original_reading": reading,
            "context_after": trailing[:20],
            "decision": "skip_mismatch",
            "new_surface": new_surface,
            "reasoning": f"Expansion '{new_surface}' doesn't match text '{expected}'",
        })
        return tok

    return {"surface": new_surface, "reading": new_reading}


def normalize_sentence(sentence, decisions):
    clean_text = strip_kahoku_parens(sentence["text"])
    tokens = sentence["tokens"]
    positions = find_token_positions(clean_text, tokens)

    new_tokens = []
    for i, tok in enumerate(tokens):
        tok_pos = positions[i]
        next_pos = None
        for j in range(i + 1, len(tokens)):
            if positions[j] is not None:
                next_pos = positions[j]
                break
        new_tokens.append(expand_token(tok, tok_pos, next_pos, clean_text, sentence, decisions))

    return {
        "source": sentence["source"],
        "text": clean_text,
        "tokens": new_tokens,
        "normalized": True,
    }


def normalize_file(input_path, decisions):
    with open(input_path) as f:
        data = json.load(f)
    results = []
    for i, sent in enumerate(data):
        if i % 1000 == 0 and i > 0:
            print(f"  Processed {i}/{len(data)} sentences...", file=sys.stderr)
        results.append(normalize_sentence(sent, decisions))
    return results


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    decisions = []
    all_data = []

    for split in ["train.json", "val.json", "test.json"]:
        input_path = INPUT_DIR / split
        if not input_path.exists():
            print(f"Warning: {input_path} not found, skipping", file=sys.stderr)
            continue
        print(f"Processing {split}...", file=sys.stderr)
        normalized = normalize_file(input_path, decisions)
        all_data.extend(normalized)
        output_path = OUTPUT_DIR / split
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(normalized, f, ensure_ascii=False, indent=2)
        print(f"  Wrote {len(normalized)} sentences to {output_path}", file=sys.stderr)

    all_path = OUTPUT_DIR / "all.json"
    with open(all_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(all_data)} sentences to {all_path}", file=sys.stderr)

    with open(DECISIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(decisions, f, ensure_ascii=False, indent=2)
    print(f"Logged {len(decisions)} decisions to {DECISIONS_FILE}", file=sys.stderr)

    expanded_by_source = Counter()
    total_by_source = Counter()
    for sent in all_data:
        src = sent["source"]
        for tok in sent["tokens"]:
            total_by_source[src] += 1
            if (any(is_kanji(c) for c in tok["surface"]) and
                    any(is_hiragana(c) for c in tok["surface"])):
                expanded_by_source[src] += 1

    print("\n=== Normalization Summary ===", file=sys.stderr)
    for src in sorted(total_by_source):
        total = total_by_source[src]
        expanded = expanded_by_source[src]
        pct = 100 * expanded / total if total > 0 else 0
        print(f"  {src}: {expanded}/{total} tokens morpheme-complete ({pct:.1f}%)",
              file=sys.stderr)

    decision_types = Counter(d["decision"] for d in decisions)
    print(f"\n=== Decision Summary ({len(decisions)} total) ===", file=sys.stderr)
    for dtype, count in decision_types.most_common():
        print(f"  {dtype}: {count}", file=sys.stderr)


if __name__ == "__main__":
    main()
