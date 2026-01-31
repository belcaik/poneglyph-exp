"""
T5 Annotator for furigana prediction.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


def contains_kanji(text: str) -> bool:
    """Check if text contains kanji characters."""
    for char in text:
        code = ord(char)
        if (0x4E00 <= code <= 0x9FFF or
            0x3400 <= code <= 0x4DBF or
            0xF900 <= code <= 0xFAFF):
            return True
    return False


def is_hiragana(char: str) -> bool:
    """Check if character is hiragana."""
    code = ord(char)
    return 0x3040 <= code <= 0x309F


def extract_kanji_reading_pairs(original: str, converted: str) -> list[dict]:
    """
    Extract kanji-reading pairs by comparing original and converted text.

    Uses anchor-based alignment: finds non-kanji characters that appear in both
    texts and uses them as anchors to determine reading boundaries.
    """
    tokens = []

    # Find all kanji sequences and their positions in original
    kanji_spans = []
    i = 0
    while i < len(original):
        if contains_kanji(original[i]):
            start = i
            while i < len(original) and contains_kanji(original[i]):
                i += 1
            kanji_spans.append((start, i, original[start:i]))
        else:
            i += 1

    if not kanji_spans:
        return tokens

    # For each kanji span, find corresponding reading by looking at anchors
    for idx, (start, end, kanji) in enumerate(kanji_spans):
        # Find left anchor (non-kanji text before this kanji in original)
        left_anchor = ""
        if start > 0:
            anchor_start = start - 1
            while anchor_start > 0 and not contains_kanji(original[anchor_start - 1]):
                anchor_start -= 1
            left_anchor = original[anchor_start:start]

        # Find right anchor (non-kanji text after this kanji in original)
        right_anchor = ""
        if end < len(original):
            anchor_end = end
            while anchor_end < len(original) and not contains_kanji(original[anchor_end]):
                anchor_end += 1
            right_anchor = original[end:anchor_end]

        # Find the reading in converted text using anchors
        reading_start = 0
        reading_end = len(converted)

        # Use left anchor to find start position
        if left_anchor:
            left_pos = converted.find(left_anchor)
            if left_pos >= 0:
                reading_start = left_pos + len(left_anchor)

        # Use right anchor to find end position
        if right_anchor:
            right_pos = converted.find(right_anchor, reading_start)
            if right_pos >= 0:
                reading_end = right_pos

        reading = converted[reading_start:reading_end]

        # Clean up: only take hiragana characters from the reading
        clean_reading = ""
        for c in reading:
            if is_hiragana(c):
                clean_reading += c

        if clean_reading:
            tokens.append({
                "surface": kanji,
                "reading": clean_reading,
                "start_offset": start,
                "end_offset": end,
                "confidence": 0.9
            })

    return tokens


@dataclass
class Token:
    """Token with furigana reading."""
    surface: str
    reading: str
    start_offset: int = 0
    end_offset: int = 0
    confidence: float = 1.0


class T5Annotator:
    """Furigana annotator using fine-tuned T5."""

    def __init__(self, model_path: str | Path):
        """
        Initialize the T5 annotator.

        Args:
            model_path: Path to fine-tuned model or HuggingFace model name
        """
        self.model_path = Path(model_path) if isinstance(model_path, str) else model_path

        print(f"Loading model from {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

        # Move to GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def name(self) -> str:
        return "finetuned_t5"

    def description(self) -> str:
        return "Furigana annotator using fine-tuned Japanese T5"

    def convert_to_readings(self, text: str, max_length: int = 128) -> str:
        """
        Convert text to readings using the T5 model.

        Args:
            text: Japanese text to convert
            max_length: Maximum sequence length

        Returns:
            Text with kanji replaced by readings
        """
        input_text = f"読み: {text}"

        inputs = self.tokenizer(
            input_text,
            max_length=max_length,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=4,
                early_stopping=True,
            )

        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return result

    def annotate(self, text: str) -> list[dict]:
        """
        Annotate text with furigana readings.

        Args:
            text: Japanese text to annotate

        Returns:
            List of tokens with surface and reading
        """
        converted = self.convert_to_readings(text)
        tokens = extract_kanji_reading_pairs(text, converted)
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
