#!/usr/bin/env python3
"""
Prepare character-level token classification data for BERT v1.

Converts sentence-level furigana data (text + tokens) to character-level format
where each character gets a label:
- "O" for non-annotated characters (hiragana, katakana, punctuation, etc.)
- A reading portion for kanji characters within annotated spans

For multi-kanji compounds, the reading is split evenly across kanji characters:
  今日→きょう: 今→"きょ", 日→"う" (2 kanji, 3 reading chars)

Usage:
    python methods/bert_v1/prepare_data.py
"""

import json
from collections import Counter
from pathlib import Path


def is_kanji(char: str) -> bool:
    """Check if a character is kanji."""
    code = ord(char)
    return (0x4E00 <= code <= 0x9FFF or
            0x3400 <= code <= 0x4DBF or
            0xF900 <= code <= 0xFAFF)


def align_reading(surface: str, reading: str) -> list[str]:
    """
    Split reading evenly across surface characters.

    For surfaces with N characters and readings with R chars:
    - Each character gets floor(R/N) reading chars
    - First (R % N) characters get one extra char

    Examples:
        align_reading("今日", "きょう") → ["きょ", "う"]
        align_reading("東京", "とうきょう") → ["とうき", "ょう"]  (if 5 chars / 2)
        align_reading("食", "た") → ["た"]
    """
    n = len(surface)
    r = len(reading)

    if n == 0 or r == 0:
        return [""] * n

    per_char = r // n
    remainder = r % n

    result = []
    pos = 0
    for i in range(n):
        length = per_char + (1 if i < remainder else 0)
        result.append(reading[pos:pos + length])
        pos += length

    return result


def find_token_spans(text: str, tokens: list[dict]) -> list[tuple[int, int, str]]:
    """
    Find character positions for each annotated token in text.

    Returns list of (start, end, reading) tuples sorted by start position.
    """
    spans = []
    used_positions = set()

    for token in tokens:
        surface = token["surface"]
        reading = token["reading"]
        search_start = 0

        while True:
            pos = text.find(surface, search_start)
            if pos == -1:
                break

            if pos not in used_positions:
                spans.append((pos, pos + len(surface), reading))
                used_positions.add(pos)
                break

            search_start = pos + 1

    spans.sort(key=lambda x: x[0])
    return spans


def sentence_to_char_labels(text: str, tokens: list[dict]) -> dict:
    """
    Convert a sentence with token annotations to character-level labels.

    Returns:
        {"chars": ["今", "日", "は", ...], "labels": ["きょ", "う", "O", ...]}
    """
    spans = find_token_spans(text, tokens)

    chars = list(text)
    labels = ["O"] * len(chars)

    for start, end, reading in spans:
        surface = text[start:end]
        aligned = align_reading(surface, reading)

        for i, label in enumerate(aligned):
            if start + i < len(labels):
                labels[start + i] = label

    return {"chars": chars, "labels": labels}


def build_label_vocab(samples: list[dict]) -> dict:
    """
    Build label vocabulary from training samples.

    Returns:
        {"O": 0, "reading1": 1, "reading2": 2, ...}
    """
    label_counts = Counter()
    for sample in samples:
        for label in sample["labels"]:
            label_counts[label] += 1

    # O always gets index 0
    vocab = {"O": 0}
    for label, _ in label_counts.most_common():
        if label != "O" and label not in vocab:
            vocab[label] = len(vocab)

    return vocab


def convert_split(input_path: Path, output_path: Path, split_name: str) -> list[dict]:
    """Convert a split file to character-level format."""
    with open(input_path) as f:
        sentences = json.load(f)

    samples = []
    skipped = 0

    for sentence in sentences:
        text = sentence["text"]
        tokens = sentence["tokens"]

        if not tokens:
            skipped += 1
            continue

        char_data = sentence_to_char_labels(text, tokens)
        char_data["source"] = sentence.get("source", "unknown")
        char_data["article_id"] = sentence.get("article_id", "")
        char_data["text"] = text
        char_data["tokens"] = tokens
        samples.append(char_data)

    with open(output_path, "w") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)

    n_labels = sum(1 for s in samples for l in s["labels"] if l != "O")
    n_chars = sum(len(s["chars"]) for s in samples)
    print(f"  {split_name}: {len(samples)} sentences, {n_chars} chars, {n_labels} annotated chars, {skipped} skipped")

    return samples


def main():
    data_dir = Path("methods/bert_v1/data")
    data_dir.mkdir(parents=True, exist_ok=True)

    print("Preparing character-level token classification data for BERT v1")
    print("=" * 60)

    # Convert train split
    train_samples = convert_split(
        Path("data/splits_v6_no_matcha/train.json"),
        data_dir / "train.json",
        "train",
    )

    # Convert val split
    convert_split(
        Path("data/splits_v6_no_matcha/val.json"),
        data_dir / "val.json",
        "val",
    )

    # Convert comparable test split (same as T5 v6 evaluation)
    convert_split(
        Path("data/splits_v6_no_matcha/test_comparable.json"),
        data_dir / "test.json",
        "test (comparable)",
    )

    # Build label vocabulary from training data only
    print("\nBuilding label vocabulary from training data...")
    label_vocab = build_label_vocab(train_samples)
    print(f"  Unique labels: {len(label_vocab)} (including O)")

    # Show most common labels
    label_counts = Counter()
    for sample in train_samples:
        for label in sample["labels"]:
            if label != "O":
                label_counts[label] += 1

    print(f"  Top 20 labels:")
    for label, count in label_counts.most_common(20):
        print(f"    {label}: {count}")

    vocab_path = data_dir / "label_vocab.json"
    with open(vocab_path, "w") as f:
        json.dump(label_vocab, f, ensure_ascii=False, indent=2)
    print(f"\nLabel vocabulary saved to: {vocab_path}")

    # Show example
    print("\nExample conversion:")
    ex = train_samples[0]
    print(f"  Text: {ex['text'][:60]}...")
    print(f"  Chars/Labels (first 20):")
    for c, l in zip(ex["chars"][:20], ex["labels"][:20]):
        print(f"    '{c}' → {l}")

    print("\nData preparation complete!")


if __name__ == "__main__":
    main()
