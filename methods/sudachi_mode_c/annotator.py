"""
Sudachi Mode C annotator implementation.
"""

from dataclasses import dataclass
from sudachipy import tokenizer, dictionary


def katakana_to_hiragana(text: str) -> str:
    """Convert katakana to hiragana."""
    result = []
    for char in text:
        code = ord(char)
        # Katakana range: U+30A1 to U+30F6 -> Hiragana: U+3041 to U+3096
        if 0x30A1 <= code <= 0x30F6:
            result.append(chr(code - 0x60))
        else:
            result.append(char)
    return "".join(result)


def contains_kanji(text: str) -> bool:
    """Check if text contains kanji characters."""
    for char in text:
        code = ord(char)
        if (0x4E00 <= code <= 0x9FFF or   # CJK Unified Ideographs
            0x3400 <= code <= 0x4DBF or   # Extension A
            0xF900 <= code <= 0xFAFF):    # Compatibility
            return True
    return False


@dataclass
class Token:
    """Token with furigana reading."""
    surface: str
    reading: str
    start_offset: int = 0
    end_offset: int = 0
    confidence: float = 1.0


class SudachiModeC:
    """Furigana annotator using Sudachi Mode C (long units)."""

    def __init__(self):
        """Initialize the Sudachi tokenizer."""
        self._dict = dictionary.Dictionary()
        self._tokenizer = self._dict.create()

    def name(self) -> str:
        return "sudachi_mode_c"

    def description(self) -> str:
        return "Furigana annotator using Sudachi Mode C (long unit segmentation)"

    def annotate(self, text: str) -> list[dict]:
        """
        Annotate text with furigana readings.

        Args:
            text: Japanese text to annotate

        Returns:
            List of tokens with surface and reading
        """
        tokens = []
        morphemes = self._tokenizer.tokenize(text, tokenizer.Tokenizer.SplitMode.C)
        offset = 0

        for m in morphemes:
            surface = m.surface()
            surface_len = len(surface)

            if contains_kanji(surface):
                reading = katakana_to_hiragana(m.reading_form())
                tokens.append({
                    "surface": surface,
                    "reading": reading,
                    "start_offset": offset,
                    "end_offset": offset + surface_len,
                    "confidence": 1.0
                })

            offset += surface_len

        return tokens

    def annotate_tokens(self, text: str) -> list[Token]:
        """
        Annotate text and return Token dataclass objects.

        Args:
            text: Japanese text to annotate

        Returns:
            List of Token objects
        """
        raw_tokens = self.annotate(text)
        return [Token(**t) for t in raw_tokens]
