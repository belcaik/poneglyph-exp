"""
Sudachi Mode C Furigana Annotator.

Uses SudachiPy with Mode C (long unit segmentation) to annotate
Japanese text with furigana readings.
"""

from .annotator import SudachiModeC, katakana_to_hiragana, contains_kanji

__all__ = ["SudachiModeC", "katakana_to_hiragana", "contains_kanji"]
