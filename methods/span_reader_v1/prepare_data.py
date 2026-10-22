"""Data preparation for SpanReader training.

Loads poneglyph_v1 dataset, tokenizes with DeBERTa, builds character-to-token
alignment, reading vocabulary, and creates PyTorch datasets.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

import torch
from torch.utils.data import Dataset


# Type label mapping
TYPE_LABELS = {
    "noun": 0, "verb": 1, "adjective": 2, "proper_noun": 3,
    "counter": 4, "adverb": 5, "other": 6,
}
TYPE_NAMES = {v: k for k, v in TYPE_LABELS.items()}
NUM_TYPES = len(TYPE_LABELS)

# Hiragana vocabulary for micro-decoder
HIRAGANA_CHARS = list(
    "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞ"
    "ただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽ"
    "まみむめもゃやゅゆょよらりるれろゎわゐゑをんゔ"
)
HIRAGANA_SPECIAL = ["<SOS>", "<EOS>", "<PAD>"]
HIRAGANA_VOCAB = HIRAGANA_SPECIAL + HIRAGANA_CHARS
HIRAGANA_TO_IDX = {c: i for i, c in enumerate(HIRAGANA_VOCAB)}
SOS_IDX = 0
EOS_IDX = 1
PAD_IDX = 2


def build_reading_vocab(data):
    """Build reading vocabulary from training data."""
    surface_to_readings = defaultdict(Counter)
    all_readings = Counter()

    for entry in data:
        for token in entry.get("tokens", []):
            surface = token.get("surface", "")
            reading = token.get("reading", "")
            if surface and reading:
                surface_to_readings[surface][reading] += 1
                all_readings[reading] += 1

    # Global reading list (sorted by frequency)
    global_readings = [r for r, _ in all_readings.most_common()]
    reading_to_idx = {r: i for i, r in enumerate(global_readings)}

    # Surface -> candidate reading indices
    surface_candidates = {}
    for surface, readings in surface_to_readings.items():
        candidates = [reading_to_idx[r] for r in readings]
        surface_candidates[surface] = candidates

    return {
        "global_readings": global_readings,
        "reading_to_idx": reading_to_idx,
        "surface_candidates": surface_candidates,
        "vocab_size": len(global_readings),
    }


def reading_to_hiragana_ids(reading, max_len=20):
    """Convert reading string to hiragana token IDs for micro-decoder."""
    ids = [SOS_IDX]
    for c in reading[:max_len - 2]:
        ids.append(HIRAGANA_TO_IDX.get(c, PAD_IDX))
    ids.append(EOS_IDX)
    # Pad
    while len(ids) < max_len:
        ids.append(PAD_IDX)
    return ids


def build_char_to_token_map(text, tokenizer, encoding):
    """Build character-to-token index mapping using offset_mapping."""
    offsets = encoding.get("offset_mapping", [])
    num_chars = len(text)
    char_to_token = [0] * num_chars

    for token_idx, (start, end) in enumerate(offsets):
        if start == end:
            continue  # special token
        for char_pos in range(start, min(end, num_chars)):
            char_to_token[char_pos] = token_idx

    return char_to_token


class SpanReaderDataset(Dataset):
    """Dataset for SpanReader training."""

    def __init__(self, data, tokenizer, reading_vocab, max_len=256,
                 num_queries=30, max_reading_len=20):
        self.data = data
        self.tokenizer = tokenizer
        self.reading_vocab = reading_vocab
        self.max_len = max_len
        self.num_queries = num_queries
        self.max_reading_len = max_reading_len
        self.reading_to_idx = reading_vocab["reading_to_idx"]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        entry = self.data[idx]
        text = entry["text"]
        tokens = entry.get("tokens", [])

        # Tokenize
        encoding = self.tokenizer(
            text, max_length=self.max_len, truncation=True,
            padding="max_length", return_tensors="pt",
            return_offsets_mapping=True
        )

        input_ids = encoding["input_ids"].squeeze(0)
        attention_mask = encoding["attention_mask"].squeeze(0)
        offset_mapping = encoding["offset_mapping"].squeeze(0)

        # Build char-to-token map
        num_chars = len(text)
        char_to_token = torch.zeros(self.max_len, dtype=torch.long)
        char_mask = torch.zeros(self.max_len, dtype=torch.float)

        for token_idx, (start, end) in enumerate(offset_mapping.tolist()):
            if start == end:
                continue
            for pos in range(int(start), min(int(end), num_chars)):
                if pos < self.max_len:
                    char_to_token[pos] = token_idx
                    char_mask[pos] = 1.0

        # Build gold spans (pad to num_queries)
        K = self.num_queries
        gold_start = torch.zeros(K, dtype=torch.long)
        gold_end = torch.zeros(K, dtype=torch.long)
        gold_type = torch.zeros(K, dtype=torch.long)
        gold_exists = torch.zeros(K, dtype=torch.float)
        gold_reading_idx = torch.full((K,), -1, dtype=torch.long)

        for i, token in enumerate(tokens[:K]):
            start = token.get("start", 0)
            end = token.get("end", start + len(token.get("surface", "")))
            surface = token.get("surface", "")
            reading = token.get("reading", "")
            span_type = token.get("type", "other")

            gold_start[i] = min(start, self.max_len - 1)
            gold_end[i] = min(max(end - 1, start), self.max_len - 1)  # inclusive
            gold_type[i] = TYPE_LABELS.get(span_type, TYPE_LABELS["other"])
            gold_exists[i] = 1.0

            # Reading index (for classification path)
            if reading in self.reading_to_idx:
                gold_reading_idx[i] = self.reading_to_idx[reading]

        # Precompute intra-token positions for CharPooling v2
        intra_positions = torch.zeros(self.max_len, dtype=torch.long)
        prev_tok = -1
        count = 0
        for pos in range(min(num_chars, self.max_len)):
            tok_idx = char_to_token[pos].item()
            if tok_idx != prev_tok:
                count = 0
                prev_tok = tok_idx
            intra_positions[pos] = min(count, 7)
            count += 1

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "char_to_token": char_to_token,
            "char_mask": char_mask,
            "intra_positions": intra_positions,
            "gold_start": gold_start,
            "gold_end": gold_end,
            "gold_type": gold_type,
            "gold_exists": gold_exists,
            "gold_reading_idx": gold_reading_idx,
            "text": text,
            "num_gold": min(len(tokens), K),
        }


def collate_fn(batch):
    """Collate function for DataLoader."""
    result = {}
    for key in ["input_ids", "attention_mask", "char_to_token", "char_mask",
                 "intra_positions",
                 "gold_start", "gold_end", "gold_type", "gold_exists",
                 "gold_reading_idx"]:
        result[key] = torch.stack([b[key] for b in batch])

    result["texts"] = [b["text"] for b in batch]
    result["num_gold"] = [b["num_gold"] for b in batch]
    return result


def load_data(data_dir="data/poneglyph_v1"):
    """Load dataset splits."""
    base = Path(data_dir)
    splits = {}
    for name in ["train", "val", "test"]:
        with open(base / f"{name}.json") as f:
            splits[name] = json.load(f)
    return splits
