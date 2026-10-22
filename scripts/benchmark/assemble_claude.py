#!/usr/bin/env python3
"""Assemble Claude subagent results from batch files into annotations_claude.json."""

import json
import re
from pathlib import Path


def extract_json_from_text(text):
    """Extract JSON object from text that may contain markdown or explanations."""
    text = text.strip()

    # Remove markdown code fences
    text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()

    # Try direct parse
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in text
    # Look for opening brace
    brace_start = text.find('{')
    if brace_start >= 0:
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[brace_start:i+1])
                    except json.JSONDecodeError:
                        break

    return None


def assemble_from_batches(batch_dir, sentences):
    """Assemble annotations from batch result files."""
    annotations = []
    batch_files = sorted(batch_dir.glob("batch_*.json"))

    all_results = {}
    for bf in batch_files:
        with open(bf) as f:
            batch_data = json.load(f)
        all_results.update(batch_data)

    for sent in sentences:
        sent_id = str(sent["id"])
        if sent_id in all_results:
            annots = all_results[sent_id]
            annotations.append({
                "id": sent["id"],
                "source": sent["source"],
                "text": sent["text"],
                "annotations": annots,
                "time_seconds": 0  # subagent, no individual timing
            })
        else:
            annotations.append({
                "id": sent["id"],
                "source": sent["source"],
                "text": sent["text"],
                "annotations": [],
                "parse_failure": True,
                "time_seconds": 0
            })

    return annotations


def main():
    data_dir = Path("data/benchmark")
    batch_dir = data_dir / "claude_batches"

    with open(data_dir / "sentences_100.json") as f:
        sentences = json.load(f)

    if batch_dir.exists():
        annotations = assemble_from_batches(batch_dir, sentences)
    else:
        print(f"No batch directory at {batch_dir}")
        print("Batch files should be created by the subagent orchestrator")
        return

    with open(data_dir / "annotations_claude.json", "w") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

    success = sum(1 for a in annotations if not a.get("parse_failure"))
    print(f"Assembled {success}/{len(sentences)} Claude annotations")
    print(f"Saved to {data_dir / 'annotations_claude.json'}")


if __name__ == "__main__":
    main()
