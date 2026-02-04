"""
T5 v4 Annotator with bracket parsing.

Identical to v3 annotator - the only difference is the trained model weights.
This version uses a model trained on the sentence-segmented multi-source dataset.
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
    Extract kanji-reading pairs from bracket-annotated text.

    Args:
        text: Text with bracket annotations like "土地[とち]の値段[ねだん]"

    Returns:
        List of {surface, reading} dicts
    """
    tokens = []

    # Find all bracket annotations
    # Pattern: [...] where content is hiragana/katakana
    bracket_pattern = r'\[([ぁ-んァ-ヶー]+)\]'

    # Find each bracket and look backwards for the kanji surface
    for match in re.finditer(bracket_pattern, text):
        reading = match.group(1)
        bracket_start = match.start()

        # Look backwards from bracket to find kanji surface
        # The surface is the kanji sequence immediately before the bracket
        surface_end = bracket_start
        surface_start = surface_end

        # Walk backwards to find start of kanji sequence
        while surface_start > 0:
            prev_char = text[surface_start - 1]
            # Stop if we hit another bracket, hiragana, or punctuation
            if prev_char in '[]' or not contains_kanji(prev_char):
                # Check if this character is part of the surface (numbers for counters)
                if prev_char.isdigit():
                    surface_start -= 1
                    continue
                break
            surface_start -= 1

        surface = text[surface_start:surface_end]

        # Only include if surface has content and contains kanji
        if surface and contains_kanji(surface):
            tokens.append({
                "surface": surface,
                "reading": reading,
            })

    return tokens


def remove_brackets(text: str) -> str:
    """Remove bracket annotations, keeping only the surface text."""
    return re.sub(r'\[([^\]]+)\]', '', text)


@dataclass
class Token:
    """Token with furigana reading."""
    surface: str
    reading: str
    start_offset: int = 0
    end_offset: int = 0
    confidence: float = 1.0


class T5V4Annotator:
    """Furigana annotator using fine-tuned T5 v4 with bracket format and segmented dataset."""

    def __init__(self, model_path: str | Path):
        """
        Initialize the T5 v4 annotator.

        Args:
            model_path: Path to fine-tuned model
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
        return "finetuned_t5_v4"

    def description(self) -> str:
        return "Furigana annotator using T5 v4 with bracket format and sentence-segmented dataset"

    def generate_annotated(self, text: str, max_length: int = 256) -> str:
        """
        Generate bracket-annotated text from input.

        Args:
            text: Japanese text to annotate
            max_length: Maximum sequence length

        Returns:
            Text with bracket annotations: kanji[reading]
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
        annotated = self.generate_annotated(text)
        tokens = extract_bracket_annotations(annotated)

        # Add position information by finding each surface in original text
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

                # Check if position already used
                if pos not in used_positions:
                    token["start_offset"] = pos
                    token["end_offset"] = pos + len(surface)
                    token["confidence"] = 0.95
                    used_positions.add(pos)
                    break

                search_start = pos + 1

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
