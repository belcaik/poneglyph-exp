#!/usr/bin/env python3
"""
Parse UD_Japanese CoNLL-U files (GSD and PUD) and extract furigana annotations.

Reads UnidicInfo from the MISC field to get readings:
    field[0] = Lemma reading (katakana, orthographic - correct vowels, no ー)
    field[2] = Surface form
    field[3] = Dictionary/lemma form
    field[4] = Surface reading (katakana, phonetic - may use ー for long vowels)

Strategy for reading extraction:
- Uninflected tokens (surface == lemma): use field[0] directly (orthographic)
- Inflected tokens (surface != lemma): use field[4], normalize ー using field[0]

After getting the full-token reading, strip okurigana (trailing hiragana) from both
surface and reading to match the existing project format where only kanji spans
are annotated (e.g., 持っ→もっ becomes 持→も).

Usage:
    python data/scrapers/parse_ud_conllu.py --source ud_gsd --input data/raw/ud_gsd --output data/processed/ud_gsd/sentences.json
    python data/scrapers/parse_ud_conllu.py --source ud_pud --input data/raw/ud_pud --output data/processed/ud_pud/sentences.json
"""

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path


def contains_kanji(text: str) -> bool:
    """Check if text contains at least one CJK Unified Ideograph."""
    for char in text:
        cp = ord(char)
        if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
            return True
    return False


def is_hiragana_char(char: str) -> bool:
    """Check if a single character is hiragana."""
    cp = ord(char)
    return 0x3041 <= cp <= 0x309F


def katakana_to_hiragana(text: str) -> str:
    """Convert katakana to hiragana. Leaves ー and other chars unchanged."""
    result = []
    for char in text:
        cp = ord(char)
        if 0x30A1 <= cp <= 0x30F6:  # Katakana ァ-ヶ
            result.append(chr(cp - 0x60))
        else:
            result.append(char)
    return ''.join(result)


def normalize_long_vowels(phonetic_kata: str, orthographic_kata: str) -> str:
    """
    Replace ー in the phonetic reading with the correct vowel from the
    orthographic reading.

    Examples:
        phonetic=ゲンドー, ortho=ゲンドウ → ゲンドウ
        phonetic=イコー,   ortho=イコウ   → イコウ
        phonetic=ダイトーリョー, ortho=ダイトウリョウ → ダイトウリョウ
    """
    if 'ー' not in phonetic_kata:
        return phonetic_kata

    # If orthographic has no ー and lengths match, do positional replacement
    if 'ー' not in orthographic_kata and len(phonetic_kata) == len(orthographic_kata):
        result = []
        for p_char, o_char in zip(phonetic_kata, orthographic_kata):
            if p_char == 'ー':
                result.append(o_char)
            else:
                result.append(p_char)
        return ''.join(result)

    # If orthographic has no ー but lengths differ, use orthographic directly
    if 'ー' not in orthographic_kata:
        return orthographic_kata

    # Both have ー — shouldn't happen but return phonetic as-is
    return phonetic_kata


def strip_okurigana(surface: str, reading_hira: str) -> tuple[str, str]:
    """
    Strip trailing okurigana (hiragana) from surface and corresponding
    characters from the reading.

    Examples:
        ("持っ", "もっ")     → ("持", "も")
        ("行き", "いき")     → ("行", "い")
        ("浮かす", "うかす") → ("浮", "う")
        ("反則", "はんそく") → ("反則", "はんそく")  # no okurigana
        ("大きい", "おおきい") → ("大", "おお")
    """
    s = list(surface)
    r = list(reading_hira)

    while s and r and is_hiragana_char(s[-1]) and s[-1] == r[-1]:
        s.pop()
        r.pop()

    result_surface = ''.join(s)
    result_reading = ''.join(r)

    if not result_surface or not contains_kanji(result_surface):
        return surface, reading_hira

    return result_surface, result_reading


def parse_unidic_info(misc: str) -> dict | None:
    """
    Extract reading info from UnidicInfo in the MISC field.

    Returns dict with lemma_reading_kata, surface_form, lemma_form,
    surface_reading_kata. Or None if UnidicInfo not found / malformed.
    """
    for part in misc.split('|'):
        if part.startswith('UnidicInfo='):
            fields = part[len('UnidicInfo='):].split(',')
            if len(fields) >= 5 and fields[0] and fields[4]:
                return {
                    'lemma_reading_kata': fields[0],
                    'surface_form': fields[2] if len(fields) > 2 else '',
                    'lemma_form': fields[3] if len(fields) > 3 else '',
                    'surface_reading_kata': fields[4],
                }
    return None


def get_reading_hiragana(form: str, lemma: str, unidic: dict) -> str | None:
    """
    Get the correct hiragana reading for a surface form.

    - If form == lemma (uninflected): use lemma_reading (field[0], orthographic)
    - If form != lemma (inflected): use surface_reading (field[4]), normalize ー
    """
    if form == lemma:
        reading_kata = unidic['lemma_reading_kata']
    else:
        reading_kata = normalize_long_vowels(
            unidic['surface_reading_kata'],
            unidic['lemma_reading_kata']
        )

    return katakana_to_hiragana(reading_kata)


def validate_reading(reading: str) -> bool:
    """Check that reading contains only hiragana characters."""
    for char in reading:
        if not is_hiragana_char(char):
            return False
    return len(reading) > 0


def parse_conllu_file(filepath: Path, source_name: str) -> tuple[list[dict], Counter]:
    """Parse a CoNLL-U file and extract sentences with furigana annotations."""
    sentences = []
    stats = Counter()

    current_text = None
    current_sent_id = None
    current_tokens = []

    def flush_sentence():
        nonlocal current_text, current_sent_id, current_tokens

        if current_text is None:
            current_tokens = []
            return

        stats['total_sentences'] += 1

        furigana_tokens = []
        for tok in current_tokens:
            form = tok['form']
            reading = tok['reading']

            if not contains_kanji(form):
                stats['tokens_skipped_no_kanji'] += 1
                continue

            if reading is None:
                stats['tokens_skipped_no_reading'] += 1
                continue

            # Strip okurigana
            kanji_surface, kanji_reading = strip_okurigana(form, reading)

            if not validate_reading(kanji_reading):
                stats['tokens_skipped_invalid_reading'] += 1
                continue

            if not contains_kanji(kanji_surface):
                stats['tokens_skipped_no_kanji_after_strip'] += 1
                continue

            furigana_tokens.append({
                'surface': kanji_surface,
                'reading': kanji_reading,
            })
            stats['tokens_extracted'] += 1

        if furigana_tokens:
            stats['sentences_with_kanji'] += 1
            sentences.append({
                'source': source_name,
                'article_id': current_sent_id or '',
                'text': current_text,
                'tokens': furigana_tokens,
            })
        else:
            stats['sentences_skipped_no_kanji'] += 1

        current_text = None
        current_sent_id = None
        current_tokens = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')

            if line.startswith('# sent_id = '):
                flush_sentence()
                current_sent_id = line[12:]
            elif line.startswith('# text = '):
                current_text = line[9:]
            elif not line:
                flush_sentence()
            elif line.startswith('#'):
                continue
            elif '\t' in line:
                parts = line.split('\t')
                if len(parts) < 10:
                    continue

                token_id = parts[0]
                if '-' in token_id or '.' in token_id:
                    continue

                form = parts[1]
                lemma = parts[2]
                misc = parts[9]

                unidic = parse_unidic_info(misc)
                if unidic is None:
                    current_tokens.append({'form': form, 'reading': None})
                    continue

                reading = get_reading_hiragana(form, lemma, unidic)
                current_tokens.append({'form': form, 'reading': reading})

    flush_sentence()
    return sentences, stats


def bracket_format_test(sentences: list[dict]):
    """Test bracket format conversion on 5 sample sentences."""
    print("\n" + "=" * 60)
    print("BRACKET FORMAT INTEGRATION TEST")
    print("=" * 60)

    sample = random.sample(sentences, min(5, len(sentences)))
    for sent in sample:
        text = sent['text']
        tokens = sent['tokens']

        annotated_positions = set()
        annotations = []

        for token in tokens:
            surface = token['surface']
            reading = token['reading']
            if not contains_kanji(surface):
                continue

            search_start = 0
            while True:
                pos = text.find(surface, search_start)
                if pos == -1:
                    break
                token_range = set(range(pos, pos + len(surface)))
                if not token_range & annotated_positions:
                    annotations.append((pos, pos + len(surface), surface, reading))
                    annotated_positions.update(token_range)
                    break
                search_start = pos + 1

        annotations.sort(key=lambda x: x[0], reverse=True)
        result = text
        for start, end, surface, reading in annotations:
            result = result[:start] + f"{surface}[{reading}]" + result[end:]

        print(f"\n  Input:  読み: {text[:70]}{'...' if len(text)>70 else ''}")
        print(f"  Output: {result[:80]}{'...' if len(result)>80 else ''}")


def main():
    parser = argparse.ArgumentParser(
        description='Parse UD_Japanese CoNLL-U files for furigana annotations'
    )
    parser.add_argument('--source', required=True, help='Source name (ud_gsd or ud_pud)')
    parser.add_argument('--input', type=Path, required=True, help='Directory with .conllu files')
    parser.add_argument('--output', type=Path, required=True, help='Output JSON file path')
    args = parser.parse_args()

    random.seed(42)

    print("=" * 60)
    print(f"UD Japanese CoNLL-U Parser — {args.source}")
    print("=" * 60)
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")

    conllu_files = sorted(args.input.glob('*.conllu'))
    if not conllu_files:
        print(f"ERROR: No .conllu files found in {args.input}")
        sys.exit(1)
    print(f"Found {len(conllu_files)} file(s): {', '.join(f.name for f in conllu_files)}")

    all_sentences = []
    total_stats = Counter()

    for filepath in conllu_files:
        print(f"\nProcessing: {filepath.name}")
        sentences, stats = parse_conllu_file(filepath, args.source)
        all_sentences.extend(sentences)
        for key, val in stats.items():
            total_stats[key] += val
        print(f"  Sentences: {stats['total_sentences']} total, "
              f"{stats['sentences_with_kanji']} with kanji")
        print(f"  Tokens extracted: {stats['tokens_extracted']}")

    # Statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print(f"Total sentences parsed:       {total_stats['total_sentences']}")
    print(f"Sentences with kanji:         {total_stats['sentences_with_kanji']}")
    print(f"Sentences skipped (no kanji): {total_stats['sentences_skipped_no_kanji']}")
    print(f"Total tokens extracted:       {total_stats['tokens_extracted']}")
    print(f"Tokens skipped (no kanji):    {total_stats['tokens_skipped_no_kanji']}")
    print(f"Tokens skipped (no reading):  {total_stats['tokens_skipped_no_reading']}")
    print(f"Tokens skipped (invalid):     {total_stats['tokens_skipped_invalid_reading']}")
    print(f"Tokens skipped (strip):       {total_stats['tokens_skipped_no_kanji_after_strip']}")

    if all_sentences:
        avg_tokens = sum(len(s['tokens']) for s in all_sentences) / len(all_sentences)
        avg_text_len = sum(len(s['text']) for s in all_sentences) / len(all_sentences)
        print(f"\nAvg tokens per sentence:      {avg_tokens:.1f}")
        print(f"Avg text length (chars):      {avg_text_len:.1f}")

    # Validation
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)
    invalid_count = 0
    for sent in all_sentences:
        for tok in sent['tokens']:
            if not validate_reading(tok['reading']):
                invalid_count += 1
                if invalid_count <= 10:
                    print(f"  INVALID: {tok['surface']} → {tok['reading']}")
    if invalid_count == 0:
        print("  All readings validated: pure hiragana ✓")
    else:
        print(f"  WARNING: {invalid_count} invalid readings found")

    no_kanji_count = sum(
        1 for s in all_sentences for t in s['tokens']
        if not contains_kanji(t['surface'])
    )
    if no_kanji_count == 0:
        print("  All surfaces contain kanji ✓")
    else:
        print(f"  WARNING: {no_kanji_count} surfaces without kanji")

    # Save output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(all_sentences, f, ensure_ascii=False, indent=2)
    print(f"\nOutput saved to: {args.output}")
    print(f"Total sentences: {len(all_sentences)}")

    # Quality report — 10 random sentences
    print("\n" + "=" * 60)
    print(f"SAMPLE SENTENCES ({args.source})")
    print("=" * 60)
    sample = random.sample(all_sentences, min(10, len(all_sentences)))
    for sent in sample:
        text_display = sent['text'][:70] + ('...' if len(sent['text']) > 70 else '')
        print(f"\n  [{sent['article_id']}]")
        print(f"  Text: {text_display}")
        tokens_str = ', '.join(
            f"{t['surface']}→{t['reading']}" for t in sent['tokens'][:6]
        )
        if len(sent['tokens']) > 6:
            tokens_str += f", ... (+{len(sent['tokens'])-6} more)"
        print(f"  Tokens: {tokens_str}")

    # 20 random tokens
    print("\n" + "=" * 60)
    print("RANDOM TOKEN SAMPLES")
    print("=" * 60)
    all_tokens = [(t['surface'], t['reading']) for s in all_sentences for t in s['tokens']]
    for surface, reading in random.sample(all_tokens, min(20, len(all_tokens))):
        print(f"  {surface} → {reading}")

    # Bracket format test
    bracket_format_test(all_sentences)

    print(f"\n✓ {args.source} parsing complete!")


if __name__ == '__main__':
    main()
