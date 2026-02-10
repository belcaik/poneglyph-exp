"""
BERT v1 Annotator - Character-level token classification for furigana.

Uses cl-tohoku/bert-base-japanese-char to classify each character:
- "O" for non-annotated characters
- A reading portion for annotated kanji characters

Predictions are reconstructed into surface[reading] pairs for evaluation.
"""

import json
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification


def contains_kanji(text: str) -> bool:
    """Check if text contains kanji characters."""
    for char in text:
        code = ord(char)
        if (0x4E00 <= code <= 0x9FFF or
            0x3400 <= code <= 0x4DBF or
            0xF900 <= code <= 0xFAFF):
            return True
    return False


class BertV1Annotator:
    """Furigana annotator using BERT v1 character-level token classification."""

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path) if isinstance(model_path, str) else model_path

        print(f"Loading BERT v1 model from {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForTokenClassification.from_pretrained(model_path)

        # Load label vocabulary
        vocab_path = self.model_path / "label_vocab.json"
        with open(vocab_path) as f:
            self.label_vocab = json.load(f)

        # Create reverse mapping: id -> label
        self.id_to_label = {v: k for k, v in self.label_vocab.items()}

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def name(self) -> str:
        return "bert_v1"

    def description(self) -> str:
        return "Furigana annotator using BERT v1 character-level token classification"

    def predict_char_labels(self, text: str) -> list[tuple[str, str]]:
        """
        Predict labels for each character in text.

        Returns:
            List of (char, label) tuples
        """
        chars = list(text)

        encoding = self.tokenizer(
            chars,
            is_split_into_words=True,
            max_length=512,
            truncation=True,
            padding=False,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**encoding)

        predictions = outputs.logits.argmax(dim=-1)[0].cpu().tolist()

        # Manual alignment: [CLS] char1 char2 ... charN [SEP]
        # Skip CLS (index 0) and SEP (last index), map middle tokens to chars
        n_char_tokens = len(predictions) - 2
        char_labels = ["O"] * len(chars)
        for i in range(min(n_char_tokens, len(chars))):
            label_id = predictions[i + 1]  # +1 to skip [CLS]
            char_labels[i] = self.id_to_label.get(label_id, "O")

        return list(zip(chars, char_labels))

    def annotate(self, text: str) -> list[dict]:
        """
        Annotate text with furigana readings.

        Returns:
            List of {surface, reading} dicts
        """
        char_labels = self.predict_char_labels(text)
        return self._reconstruct_tokens(char_labels)

    def _reconstruct_tokens(self, char_labels: list[tuple[str, str]]) -> list[dict]:
        """
        Reconstruct surface[reading] pairs from character-level predictions.

        Consecutive non-O characters are merged into a single token.
        """
        tokens = []
        i = 0

        while i < len(char_labels):
            char, label = char_labels[i]

            if label != "O":
                # Start of annotated span
                surface = char
                reading = label
                i += 1

                # Continue while we have consecutive non-O labels
                while i < len(char_labels) and char_labels[i][1] != "O":
                    surface += char_labels[i][0]
                    reading += char_labels[i][1]
                    i += 1

                # Only include if surface contains kanji
                if contains_kanji(surface):
                    tokens.append({
                        "surface": surface,
                        "reading": reading,
                    })
            else:
                i += 1

        return tokens
