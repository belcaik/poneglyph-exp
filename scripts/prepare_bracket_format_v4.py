#!/usr/bin/env python3
"""
Prepare training data in bracket annotation format for T5 v4.

Converts sentence-segmented data to bracket annotation format:
  Input:  "読み: {original_text}"
  Output: "{text_with_brackets}" where kanji have [reading] annotations

Uses data/splits_v4/ (segmented data) as input.
"""

import json
from pathlib import Path


def contains_kanji(text: str) -> bool:
    """Check if text contains kanji characters."""
    for char in text:
        code = ord(char)
        if (0x4E00 <= code <= 0x9FFF or
            0x3400 <= code <= 0x4DBF or
            0xF900 <= code <= 0xFAFF):
            return True
    return False


def create_bracket_annotation(text: str, tokens: list[dict]) -> str:
    """
    Create bracket-annotated text from original text and token list.

    Args:
        text: Original Japanese text
        tokens: List of {surface, reading} dicts

    Returns:
        Text with bracket annotations: kanji[reading]
    """
    # Sort tokens by their position in text
    annotated_positions = set()
    annotations = []  # (start, end, surface, reading)

    for token in tokens:
        surface = token["surface"]
        reading = token["reading"]

        # Only annotate if surface contains kanji
        if not contains_kanji(surface):
            continue

        # Find position of this surface in text
        search_start = 0
        while True:
            pos = text.find(surface, search_start)
            if pos == -1:
                break

            # Check if this position overlaps with already annotated
            token_range = set(range(pos, pos + len(surface)))
            if not token_range & annotated_positions:
                # No overlap, use this position
                annotations.append((pos, pos + len(surface), surface, reading))
                annotated_positions.update(token_range)
                break

            # Overlap found, search further
            search_start = pos + 1

    # Sort annotations by position (reverse order for replacement)
    annotations.sort(key=lambda x: x[0], reverse=True)

    # Apply annotations from end to start (to preserve positions)
    result = text
    for start, end, surface, reading in annotations:
        result = result[:start] + f"{surface}[{reading}]" + result[end:]

    return result


def convert_split(input_path: Path, output_path: Path) -> dict:
    """
    Convert a data split to bracket format.

    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSON file

    Returns:
        Statistics about conversion
    """
    with open(input_path) as f:
        sentences = json.load(f)

    converted = []
    stats = {
        "total": len(sentences),
        "converted": 0,
        "skipped_no_tokens": 0,
        "skipped_no_kanji": 0,
        "by_source": {},
    }

    for sentence in sentences:
        text = sentence["text"]
        tokens = sentence.get("tokens", [])
        source = sentence.get("source", "unknown")

        # Initialize source stats
        if source not in stats["by_source"]:
            stats["by_source"][source] = {"total": 0, "converted": 0}
        stats["by_source"][source]["total"] += 1

        # Skip if no tokens
        if not tokens:
            stats["skipped_no_tokens"] += 1
            continue

        # Skip if text has no kanji
        if not contains_kanji(text):
            stats["skipped_no_kanji"] += 1
            continue

        # Create bracket annotation
        bracket_text = create_bracket_annotation(text, tokens)

        # Verify at least one annotation was added
        if "[" not in bracket_text:
            stats["skipped_no_kanji"] += 1
            continue

        converted.append({
            "input": f"読み: {text}",
            "output": bracket_text,
            "source": source,
            "article_id": sentence.get("article_id", ""),
        })
        stats["converted"] += 1
        stats["by_source"][source]["converted"] += 1

    # Save converted data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)

    return stats


def main():
    project_root = Path(__file__).parent.parent
    splits_dir = project_root / "data" / "splits_v4"
    output_dir = project_root / "data" / "bracket_format_v4"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Converting v4 data to bracket annotation format...")
    print("=" * 60)
    print(f"Input:  {splits_dir}")
    print(f"Output: {output_dir}")

    total_stats = {
        "total": 0,
        "converted": 0,
    }

    for split in ["train", "val", "test"]:
        input_path = splits_dir / f"{split}.json"
        output_path = output_dir / f"{split}.json"

        if not input_path.exists():
            print(f"\nSkipping {split}: {input_path} not found")
            continue

        stats = convert_split(input_path, output_path)

        total_stats["total"] += stats["total"]
        total_stats["converted"] += stats["converted"]

        print(f"\n{split.upper()} split:")
        print(f"  Total items:        {stats['total']}")
        print(f"  Converted:          {stats['converted']}")
        print(f"  Skipped (no tokens): {stats['skipped_no_tokens']}")
        print(f"  Skipped (no kanji):  {stats['skipped_no_kanji']}")

        print(f"  By source:")
        for source, src_stats in sorted(stats["by_source"].items()):
            print(f"    {source}: {src_stats['converted']}/{src_stats['total']}")

    # Show examples
    print("\n" + "=" * 60)
    print("EXAMPLES")
    print("=" * 60)

    test_output = output_dir / "test.json"
    if test_output.exists():
        with open(test_output) as f:
            examples = json.load(f)[:5]

        for i, ex in enumerate(examples, 1):
            print(f"\nExample {i} ({ex.get('source', 'unknown')}):")
            print(f"  Input:  {ex['input'][:70]}...")
            print(f"  Output: {ex['output'][:70]}...")

    print("\n" + "=" * 60)
    print("Data preparation complete!")
    print(f"Total items: {total_stats['total']}")
    print(f"Total converted: {total_stats['converted']}")
    print(f"Output directory: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
