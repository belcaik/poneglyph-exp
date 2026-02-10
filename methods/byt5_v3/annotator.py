"""
ByT5 v3 Annotator with angle-bracket 《》 parsing.

Same architecture as ByT5 v2 but with 《》 delimiters instead of [].
"""

import re
from dataclasses import dataclass
from pathlib import Path

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


def extract_bracket_annotations(text: str) -> list[dict]:
    """
    Extract kanji-reading pairs from angle-bracket-annotated text.

    Args:
        text: Text with angle-bracket annotations like "土地《とち》の値段《ねだん》"

    Returns:
        List of {surface, reading} dicts
    """
    tokens = []

    bracket_pattern = r'《([ぁ-んァ-ヶー]+)》'

    for match in re.finditer(bracket_pattern, text):
        reading = match.group(1)
        bracket_start = match.start()

        surface_end = bracket_start
        surface_start = surface_end

        while surface_start > 0:
            prev_char = text[surface_start - 1]
            if prev_char in '《》' or not contains_kanji(prev_char):
                if prev_char.isdigit():
                    surface_start -= 1
                    continue
                break
            surface_start -= 1

        surface = text[surface_start:surface_end]

        if surface and contains_kanji(surface):
            tokens.append({
                "surface": surface,
                "reading": reading,
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


class ByT5V3Annotator:
    """Furigana annotator using fine-tuned ByT5 v3 with angle-bracket 《》 format."""

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path) if isinstance(model_path, str) else model_path

        print(f"Loading ByT5 v3 model from {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def name(self) -> str:
        return "byt5_v3"

    def description(self) -> str:
        return "Furigana annotator using ByT5 v3 with angle-bracket 《》 format"

    def generate_annotated(self, text: str, max_length: int = 768) -> str:
        """Generate angle-bracket-annotated text from input."""
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
        """Annotate text with furigana readings."""
        annotated = self.generate_annotated(text)
        tokens = extract_bracket_annotations(annotated)

        used_positions = set()
        for token in tokens:
            surface = token["surface"]
            search_start = 0

            while True:
                pos = text.find(surface, search_start)
                if pos == -1:
                    token["start_offset"] = -1
                    token["end_offset"] = -1
                    break

                if pos not in used_positions:
                    token["start_offset"] = pos
                    token["end_offset"] = pos + len(surface)
                    token["confidence"] = 0.95
                    used_positions.add(pos)
                    break

                search_start = pos + 1

        return tokens

    def annotate_tokens(self, text: str) -> list[Token]:
        """Annotate text and return Token dataclass objects."""
        raw_tokens = self.annotate(text)
        return [Token(**t) for t in raw_tokens]
