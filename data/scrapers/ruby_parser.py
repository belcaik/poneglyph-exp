"""
Shared Ruby Parser Utility

Extracts furigana annotations from HTML ruby tags.
All source parsers (NHK, MATCHA, Kahoku, Hirogaru) use this module.

Standard HTML ruby structure:
  <ruby>
    漢字
    <rt>かんじ</rt>
  </ruby>
"""

from bs4 import NavigableString
from bs4.element import Tag


def extract_ruby_tokens(element: Tag) -> list[dict]:
    """
    Extract {surface, reading} pairs from ruby tags in a BeautifulSoup element.

    Args:
        element: BeautifulSoup element to search for ruby tags

    Returns:
        List of dicts with 'surface' (kanji) and 'reading' (hiragana) keys
    """
    tokens = []

    ruby_elements = element.find_all('ruby')

    for ruby in ruby_elements:
        surface = ''
        reading = ''

        for child in ruby.children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    surface += text
            elif child.name == 'rt':
                reading = child.get_text(strip=True)

        if surface and reading:
            tokens.append({
                'surface': surface,
                'reading': reading,
            })

    return tokens


def is_hiragana(text: str) -> bool:
    """Check if text is primarily hiragana (>50%)."""
    if not text:
        return False
    hiragana_count = sum(1 for c in text if '\u3040' <= c <= '\u309f')
    return hiragana_count > len(text) * 0.5


def has_kanji(text: str) -> bool:
    """Check if text contains any kanji characters."""
    return any('\u4e00' <= c <= '\u9fff' for c in text)


def is_katakana(text: str) -> bool:
    """Check if text is primarily katakana (>50%)."""
    if not text:
        return False
    katakana_count = sum(1 for c in text if '\u30a0' <= c <= '\u30ff')
    return katakana_count > len(text) * 0.5


def get_sentence_text(element: Tag) -> str:
    """
    Extract clean sentence text from an element, removing ruby annotations.

    The text returned is the sentence as it would be read, with kanji
    but without the furigana readings visible above them.
    """
    text_parts = []

    for child in element.descendants:
        if isinstance(child, NavigableString):
            # Skip if parent is <rt> (reading annotation)
            if child.parent and child.parent.name == 'rt':
                continue
            text = str(child).strip()
            if text:
                text_parts.append(text)

    # Join and normalize whitespace
    full_text = ''.join(text_parts)
    # Normalize multiple spaces to single space
    full_text = ' '.join(full_text.split())
    return full_text


def extract_sentences_with_tokens(element: Tag, min_length: int = 5) -> list[dict]:
    """
    Extract sentences from an element, each with its text and furigana tokens.

    Args:
        element: BeautifulSoup element to extract sentences from
        min_length: Minimum character length for a valid sentence

    Returns:
        List of dicts with 'text' and 'tokens' keys
    """
    sentences = []

    # Find all paragraph-like elements
    for p in element.find_all(['p', 'dd']):
        text = get_sentence_text(p)

        if not text or len(text) < min_length:
            continue

        tokens = extract_ruby_tokens(p)

        # Include sentence if it has tokens OR contains kanji (potential annotation targets)
        if tokens or has_kanji(text):
            sentences.append({
                'text': text,
                'tokens': tokens,
            })

    return sentences
