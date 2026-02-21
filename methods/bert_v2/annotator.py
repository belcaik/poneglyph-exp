"""
BERT v2 Annotator - Dictionary-constrained reading classification for furigana.

Uses tohoku-nlp/bert-base-japanese-v3 to classify the correct reading for each
kanji span from a set of dictionary candidates. The model uses contextual
embeddings to disambiguate readings when multiple candidates exist.
"""

import json
from pathlib import Path

import torch
from transformers import AutoTokenizer

from .train import BertReadingClassifier, find_span_tokens


def contains_kanji(text: str) -> bool:
    """Check if text contains kanji characters."""
    for char in text:
        code = ord(char)
        if (0x4E00 <= code <= 0x9FFF or
            0x3400 <= code <= 0x4DBF or
            0xF900 <= code <= 0xFAFF):
            return True
    return False


class BertV2Annotator:
    """Furigana annotator using BERT v2 dictionary-constrained reading classification."""

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path) if isinstance(model_path, str) else model_path

        print(f"Loading BERT v2 model from {model_path}")

        # Load model config
        with open(self.model_path / "model_config.json") as f:
            self.model_config = json.load(f)

        # Load reading dictionary and vocabulary
        with open(self.model_path / "reading_dict.json") as f:
            self.reading_dict = json.load(f)
        with open(self.model_path / "reading_vocab.json") as f:
            self.reading_vocab = json.load(f)

        # Reverse vocab: index -> reading
        self.index_to_reading = {v: k for k, v in self.reading_vocab.items()}

        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        self.model = BertReadingClassifier(
            self.model_config["base_model"],
            self.model_config["reading_vocab_size"],
        )

        state_dict = torch.load(self.model_path / "model.pt", map_location="cpu", weights_only=True)
        self.model.load_state_dict(state_dict)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def name(self) -> str:
        return "bert_v2"

    def description(self) -> str:
        return "Furigana annotator using BERT v2 dictionary-constrained reading classification"

    def predict_reading(self, text: str, surface: str, span_start: int, span_end: int) -> str:
        """
        Predict the reading for a single kanji span within a sentence.

        Args:
            text: Full sentence text
            surface: The kanji surface form to classify
            span_start: Character offset start in text
            span_end: Character offset end in text

        Returns:
            Predicted reading (hiragana string)
        """
        # Look up candidates
        if surface in self.reading_dict:
            candidates = self.reading_dict[surface]
        else:
            # OOV — no dictionary entry, return empty
            return ""

        if len(candidates) == 1:
            # Unambiguous — return the only candidate
            return candidates[0]

        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=256,
            truncation=True,
            padding=False,
            return_tensors=None,
        )

        # Find span token indices using manual alignment
        span_token_indices = find_span_tokens(
            self.tokenizer, encoding["input_ids"], text, span_start, span_end
        )

        if not span_token_indices:
            # Fallback: return most common reading (first in sorted list)
            return candidates[0]

        # Build candidate mask
        vocab_size = len(self.reading_vocab)
        candidate_mask = torch.zeros(1, vocab_size, dtype=torch.float)
        for reading in candidates:
            if reading in self.reading_vocab:
                candidate_mask[0, self.reading_vocab[reading]] = 1.0

        # Prepare tensors
        input_ids = torch.tensor([encoding["input_ids"]])
        attention_mask = torch.tensor([encoding["attention_mask"]])
        span_indices_tensor = torch.tensor([span_token_indices], dtype=torch.long)
        span_masks_tensor = torch.ones(1, len(span_token_indices), dtype=torch.float)

        # Move to device
        input_ids = input_ids.to(self.device)
        attention_mask = attention_mask.to(self.device)
        span_indices_tensor = span_indices_tensor.to(self.device)
        span_masks_tensor = span_masks_tensor.to(self.device)
        candidate_mask = candidate_mask.to(self.device)

        with torch.no_grad():
            logits = self.model(
                input_ids, attention_mask,
                span_indices_tensor, span_masks_tensor,
                candidate_mask,
            )

        pred_idx = logits.argmax(dim=-1).item()
        return self.index_to_reading.get(pred_idx, candidates[0])

    def annotate(self, text: str) -> list[dict]:
        """
        Annotate text with furigana readings using dictionary scan.

        Greedy longest-match from left to right.
        """
        return self.annotate_by_dict_scan(text)

    def annotate_by_dict_scan(self, text: str) -> list[dict]:
        """
        Annotate by scanning text for known dictionary surfaces.

        Greedy longest-match from left to right.
        """
        tokens = []
        i = 0
        used_positions = set()

        while i < len(text):
            best_match = None
            best_len = 0

            # Try all possible substrings starting at position i
            for j in range(min(i + 8, len(text)), i, -1):  # Max 8 chars
                substr = text[i:j]
                if contains_kanji(substr) and substr in self.reading_dict:
                    if j - i > best_len:
                        best_match = substr
                        best_len = j - i
                        break  # Longest match found (iterating from long to short)

            if best_match and i not in used_positions:
                reading = self.predict_reading(text, best_match, i, i + best_len)
                if reading:
                    tokens.append({
                        "surface": best_match,
                        "reading": reading,
                    })
                for pos in range(i, i + best_len):
                    used_positions.add(pos)
                i += best_len
            else:
                i += 1

        return tokens

    def annotate_with_spans(self, text: str, ground_truth_tokens: list[dict]) -> list[dict]:
        """
        Annotate using provided ground truth token spans for evaluation.

        This is the primary evaluation method — it uses the same spans
        as ground truth and only needs to predict the reading.
        """
        tokens = []
        used_positions = set()

        for gt_token in ground_truth_tokens:
            surface = gt_token["surface"]
            if not contains_kanji(surface):
                continue

            # Find the span in text (avoiding reuse)
            search_start = 0
            span_start = -1
            while True:
                pos = text.find(surface, search_start)
                if pos == -1:
                    break
                if pos not in used_positions:
                    span_start = pos
                    break
                search_start = pos + 1

            if span_start == -1:
                continue

            span_end = span_start + len(surface)
            for p in range(span_start, span_end):
                used_positions.add(p)

            reading = self.predict_reading(text, surface, span_start, span_end)
            tokens.append({
                "surface": surface,
                "reading": reading,
            })

        return tokens
