"""
Span Detector v1 Annotator - BIO-based morpheme boundary detection.

Detects which character sequences in raw text are annotatable morphemes
that need furigana. Used as Stage 1 in the two-stage pipeline:
    Stage 1: Span Detector (this) -> detected morpheme boundaries
    Stage 2: BERT v2 Reading Classifier -> readings for each span
"""

import json
import unicodedata
from pathlib import Path

import torch
from transformers import AutoTokenizer

from .train import BertSpanDetector, LABEL_B, LABEL_I, LABEL_O, NUM_LABELS


def align_token_predictions_to_chars(tokenizer, input_ids: list[int], text: str,
                                     token_preds: list[int]) -> list[int]:
    """Convert token-level BIO predictions back to character-level labels.

    For each subword token, assign its predicted label to all characters it covers.
    """
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    char_labels = [LABEL_O] * len(text)
    char_pos = 0
    tok_pred_idx = 0

    for tok_idx, token in enumerate(tokens):
        if token in ("[CLS]", "[SEP]", "[PAD]"):
            continue

        # Get prediction for this token
        pred = token_preds[tok_pred_idx] if tok_pred_idx < len(token_preds) else LABEL_O
        tok_pred_idx += 1

        if token == "[UNK]":
            if char_pos < len(text):
                char_labels[char_pos] = pred
                char_pos += 1
            continue

        piece = token[2:] if token.startswith("##") else token
        tok_start = char_pos

        # Match piece against text with NFKC normalization
        matched = 0
        consumed_chars = 0
        while matched < len(piece) and char_pos + consumed_chars < len(text):
            orig_char = text[char_pos + consumed_chars]
            norm_char = unicodedata.normalize("NFKC", orig_char)
            if piece[matched:matched + len(norm_char)] == norm_char:
                matched += len(norm_char)
                consumed_chars += 1
            else:
                consumed_chars += 1
                matched += 1

        if consumed_chars == 0:
            consumed_chars = 1

        # Assign prediction to all covered characters
        for i in range(char_pos, min(char_pos + consumed_chars, len(text))):
            if i == tok_start and pred == LABEL_B:
                char_labels[i] = LABEL_B
            elif pred == LABEL_B and i > tok_start:
                char_labels[i] = LABEL_I
            elif pred == LABEL_I:
                char_labels[i] = LABEL_I
            # else: keep O

        char_pos += consumed_chars

    return char_labels


def extract_spans_from_labels(text: str, char_labels: list[int]) -> list[dict]:
    """Extract spans from character-level BIO labels.

    Returns list of {"surface": str, "start": int, "end": int}.
    """
    spans = []
    i = 0
    while i < len(char_labels):
        if char_labels[i] == LABEL_B:
            start = i
            i += 1
            while i < len(char_labels) and char_labels[i] == LABEL_I:
                i += 1
            surface = text[start:i]
            spans.append({"surface": surface, "start": start, "end": i})
        else:
            i += 1
    return spans


class SpanDetectorAnnotator:
    """Annotator that detects morpheme spans in raw text using BIO tagging."""

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path) if isinstance(model_path, str) else model_path

        print(f"Loading Span Detector v1 from {model_path}")

        # Load model config
        with open(self.model_path / "model_config.json") as f:
            self.model_config = json.load(f)

        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        self.model = BertSpanDetector(
            self.model_config["base_model"],
            self.model_config.get("num_labels", NUM_LABELS),
        )

        state_dict = torch.load(self.model_path / "model.pt", map_location="cpu", weights_only=True)
        self.model.load_state_dict(state_dict)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def detect_spans(self, text: str) -> list[dict]:
        """Detect annotatable morpheme spans in text.

        Returns list of {"surface": str, "start": int, "end": int}.
        """
        if not text:
            return []

        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=256,
            truncation=True,
            padding=False,
            return_tensors=None,
        )

        input_ids = encoding["input_ids"]
        attention_mask = encoding["attention_mask"]

        input_ids_t = torch.tensor([input_ids], dtype=torch.long).to(self.device)
        attention_mask_t = torch.tensor([attention_mask], dtype=torch.long).to(self.device)

        with torch.no_grad():
            logits, _ = self.model(input_ids_t, attention_mask_t)
            token_preds = logits.argmax(dim=-1)[0].cpu().tolist()

        # Filter to only non-special token predictions
        tokens = self.tokenizer.convert_ids_to_tokens(input_ids)
        filtered_preds = []
        for tok, pred in zip(tokens, token_preds):
            if tok not in ("[CLS]", "[SEP]", "[PAD]"):
                filtered_preds.append(pred)

        # Convert token-level predictions to character-level labels
        char_labels = align_token_predictions_to_chars(
            self.tokenizer, input_ids, text, filtered_preds
        )

        # Extract spans
        return extract_spans_from_labels(text, char_labels)
