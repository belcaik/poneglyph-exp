#!/usr/bin/env python3
"""
Japanese sentence segmentation with token reassignment.

Splits text on Japanese sentence boundaries (。！？) and reassigns
furigana tokens to the appropriate sentences based on character position.

Key invariant: Total token count must be preserved after segmentation.
"""

import re
from dataclasses import dataclass


# Japanese sentence-ending punctuation
SENTENCE_ENDINGS = re.compile(r'([。！？])')

# Patterns to avoid splitting inside
# e.g., don't split 「こんにちは。」 before the closing quote
PROTECTED_PATTERNS = [
    (r'「[^」]*」', 'quoted'),  # Japanese quotes
    (r'『[^』]*』', 'double_quoted'),  # Double quotes
    (r'\([^)]*\)', 'parentheses'),  # Parentheses
    (r'（[^）]*）', 'jp_parentheses'),  # Japanese parentheses
]


@dataclass
class Sentence:
    """A segmented sentence with its tokens."""
    text: str
    start_offset: int
    end_offset: int
    tokens: list


def find_token_positions(text: str, tokens: list) -> list:
    """
    Find the character position of each token in the text.

    Returns a list of (token, start_pos, end_pos) tuples.
    If a token cannot be found, returns (-1, -1) for its position.
    """
    positioned_tokens = []
    search_start = 0

    for token in tokens:
        surface = token.get("surface", "")
        if not surface:
            continue

        # Search for the token surface in the text
        pos = text.find(surface, search_start)
        if pos == -1:
            # Token not found from current position, search from beginning
            pos = text.find(surface)

        if pos != -1:
            positioned_tokens.append({
                **token,
                "_start": pos,
                "_end": pos + len(surface)
            })
            # Move search start to after this token to handle duplicates correctly
            search_start = pos + len(surface)
        else:
            # Token surface not found in text - this can happen with mismatched data
            positioned_tokens.append({
                **token,
                "_start": -1,
                "_end": -1
            })

    return positioned_tokens


def segment_text(text: str) -> list:
    """
    Split Japanese text into sentences on 。！？ boundaries.

    Returns list of (sentence_text, start_offset, end_offset) tuples.
    """
    if not text:
        return []

    # Split on sentence endings but keep the delimiter
    parts = SENTENCE_ENDINGS.split(text)

    sentences = []
    current_pos = 0
    current_sentence = ""
    sentence_start = 0

    for i, part in enumerate(parts):
        if not part:
            continue

        # Check if this part is a sentence ending
        if SENTENCE_ENDINGS.match(part):
            # Add ending to current sentence
            current_sentence += part
            # Complete the sentence
            if current_sentence.strip():
                sentences.append((
                    current_sentence.strip(),
                    sentence_start,
                    current_pos + len(part)
                ))
            current_pos += len(part)
            current_sentence = ""
            sentence_start = current_pos
        else:
            current_sentence += part
            if not current_sentence.strip():
                sentence_start = current_pos
            current_pos += len(part)

    # Handle any remaining text without sentence ending
    if current_sentence.strip():
        sentences.append((
            current_sentence.strip(),
            sentence_start,
            current_pos
        ))

    return sentences


def assign_tokens_to_sentences(sentences: list, positioned_tokens: list) -> list:
    """
    Assign tokens to sentences based on character position overlap.

    Each token is assigned to the sentence whose range contains the token's start position.
    """
    result = []

    for sent_text, sent_start, sent_end in sentences:
        sent_tokens = []
        for token in positioned_tokens:
            token_start = token.get("_start", -1)
            token_end = token.get("_end", -1)

            if token_start == -1:
                # Token position unknown - skip
                continue

            # Check if token falls within this sentence
            if sent_start <= token_start < sent_end:
                # Remove position metadata and add to sentence
                clean_token = {k: v for k, v in token.items() if not k.startswith("_")}
                sent_tokens.append(clean_token)

        result.append(Sentence(
            text=sent_text,
            start_offset=sent_start,
            end_offset=sent_end,
            tokens=sent_tokens
        ))

    return result


def segment_item(item: dict) -> list:
    """
    Segment a single data item into multiple sentence-level items.

    Args:
        item: Dict with 'text', 'tokens', 'source', 'article_id' keys

    Returns:
        List of new items, one per sentence (with reassigned tokens)
    """
    text = item.get("text", "")
    tokens = item.get("tokens", [])
    source = item.get("source", "unknown")
    article_id = item.get("article_id", "")

    # If text is already short (likely a sentence), return as-is
    if len(text) <= 100 and text.count("。") <= 1:
        return [item]

    # Find token positions
    positioned_tokens = find_token_positions(text, tokens)

    # Segment text into sentences
    sentence_boundaries = segment_text(text)

    # If no valid segmentation, return original
    if len(sentence_boundaries) <= 1:
        return [item]

    # Assign tokens to sentences
    sentences = assign_tokens_to_sentences(sentence_boundaries, positioned_tokens)

    # Create new items for each sentence with tokens
    result = []
    for i, sent in enumerate(sentences):
        # Skip empty sentences or sentences without tokens
        if not sent.text.strip():
            continue

        new_item = {
            "source": source,
            "article_id": f"{article_id}_s{i}",
            "text": sent.text,
            "tokens": sent.tokens,
            "_original_article_id": article_id,
            "_sentence_index": i,
        }
        result.append(new_item)

    return result


def validate_token_preservation(original_items: list, segmented_items: list) -> dict:
    """
    Validate that segmentation preserved all tokens.

    Returns dict with validation results.
    """
    original_token_count = sum(len(item.get("tokens", [])) for item in original_items)
    segmented_token_count = sum(len(item.get("tokens", [])) for item in segmented_items)

    # Count tokens by source
    original_by_source = {}
    segmented_by_source = {}

    for item in original_items:
        source = item.get("source", "unknown")
        original_by_source[source] = original_by_source.get(source, 0) + len(item.get("tokens", []))

    for item in segmented_items:
        source = item.get("source", "unknown")
        segmented_by_source[source] = segmented_by_source.get(source, 0) + len(item.get("tokens", []))

    # Calculate lost tokens
    lost_tokens = original_token_count - segmented_token_count
    lost_by_source = {}
    for source in original_by_source:
        orig = original_by_source.get(source, 0)
        seg = segmented_by_source.get(source, 0)
        if orig != seg:
            lost_by_source[source] = orig - seg

    return {
        "original_total": original_token_count,
        "segmented_total": segmented_token_count,
        "lost_tokens": lost_tokens,
        "preservation_rate": segmented_token_count / original_token_count if original_token_count > 0 else 1.0,
        "lost_by_source": lost_by_source,
        "valid": lost_tokens == 0,
    }


if __name__ == "__main__":
    # Test the segmentation
    test_text = "これは最初の文です。二番目の文章があります！三番目の文章？最後の文です。"
    test_tokens = [
        {"surface": "最初", "reading": "さいしょ"},
        {"surface": "文", "reading": "ぶん"},
        {"surface": "二番目", "reading": "にばんめ"},
        {"surface": "文章", "reading": "ぶんしょう"},
        {"surface": "三番目", "reading": "さんばんめ"},
        {"surface": "文章", "reading": "ぶんしょう"},
        {"surface": "最後", "reading": "さいご"},
        {"surface": "文", "reading": "ぶん"},
    ]

    test_item = {
        "source": "test",
        "article_id": "001",
        "text": test_text,
        "tokens": test_tokens,
    }

    print("Original item:")
    print(f"  Text: {test_text}")
    print(f"  Tokens: {len(test_tokens)}")
    print()

    result = segment_item(test_item)

    print(f"Segmented into {len(result)} items:")
    for item in result:
        print(f"  [{item['article_id']}] {item['text']}")
        print(f"    Tokens: {[t['surface'] for t in item['tokens']]}")
    print()

    # Validate
    validation = validate_token_preservation([test_item], result)
    print(f"Validation: {validation}")
