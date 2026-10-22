#!/usr/bin/env python3
"""Parse Claude subagent output files and assemble into annotations_claude.json."""

import json
import re
import sys
from pathlib import Path


def extract_json_from_agent_output(filepath):
    """Parse JSONL agent output and extract the JSON annotation object."""
    with open(filepath) as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Look for assistant messages with content
        if entry.get("type") != "assistant":
            continue

        message = entry.get("message", {})
        content = message.get("content", [])

        for block in content:
            if block.get("type") != "text":
                continue

            text = block["text"]

            # Remove markdown code fences
            text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
            text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
            text = text.strip()

            # Try to parse as JSON
            try:
                result = json.loads(text)
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                # Try to find JSON object in text
                match = re.search(r'\{[\s\S]*\}', text)
                if match:
                    try:
                        return json.loads(match.group())
                    except json.JSONDecodeError:
                        pass

    return None


def main():
    tasks_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None

    if tasks_dir is None:
        # Auto-discover from common locations
        possible = list(Path("/tmp/claude-1000").rglob("tasks"))
        if possible:
            tasks_dir = possible[0]
        else:
            print("Usage: python parse_subagent_outputs.py <tasks_dir>")
            print("  tasks_dir: directory containing agent output files (*.output)")
            return

    # Find all agent output files
    output_files = sorted(tasks_dir.glob("a*.output"))
    print(f"Found {len(output_files)} agent output files in {tasks_dir}")

    # Parse each file
    all_annotations = {}
    for filepath in output_files:
        result = extract_json_from_agent_output(filepath)
        if result:
            all_annotations.update(result)
            ids = sorted(result.keys(), key=lambda x: int(x))
            print(f"  {filepath.name}: sentences {ids[0]}-{ids[-1]} ({len(result)} sentences)")
        else:
            print(f"  {filepath.name}: FAILED to extract JSON")

    print(f"\nTotal annotations extracted: {len(all_annotations)} sentences")

    # Load sentences for metadata
    with open("data/benchmark/sentences_100.json") as f:
        sentences = json.load(f)

    # Assemble into final format
    annotations = []
    for sent in sentences:
        sent_id = str(sent["id"])
        if sent_id in all_annotations:
            annotations.append({
                "id": sent["id"],
                "source": sent["source"],
                "text": sent["text"],
                "annotations": all_annotations[sent_id],
                "time_seconds": 0
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

    success = sum(1 for a in annotations if not a.get("parse_failure"))
    print(f"Successfully matched: {success}/100")

    # Save
    output_path = Path("data/benchmark/annotations_claude.json")
    with open(output_path, "w") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
