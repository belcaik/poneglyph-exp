#!/usr/bin/env python3
"""Assemble Claude subagent batch results into annotations_claude.json.

Reads /tmp/dataset_claude_batch_*.json files produced by subagents,
validates kanji coverage, and assembles into standard format.
"""

import json
import re
from pathlib import Path


def is_kanji(c):
    cp = ord(c)
    return 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF


def extract_json_from_file(filepath):
    """Extract JSON object from a file that may contain non-JSON text."""
    with open(filepath) as f:
        content = f.read().strip()

    # Remove markdown fences
    content = re.sub(r'^```(?:json)?\s*\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n?```\s*$', '', content, flags=re.MULTILINE)
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Find JSON object
    brace_start = content.find('{')
    if brace_start >= 0:
        depth = 0
        for i in range(brace_start, len(content)):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(content[brace_start:i+1])
                    except json.JSONDecodeError:
                        break
    return None


def check_kanji_coverage(text, annotations):
    """Return coverage percentage."""
    kanji_positions = {i for i, c in enumerate(text) if is_kanji(c)}
    if not kanji_positions:
        return 100.0

    covered = set()
    used = set()
    for ann in annotations:
        surface = ann.get("surface", "")
        if not surface:
            continue
        pos = 0
        while pos < len(text):
            idx = text.find(surface, pos)
            if idx == -1:
                break
            span = set(range(idx, idx + len(surface)))
            if not span & used:
                covered |= span
                used |= span
                break
            pos = idx + 1

    return len(kanji_positions & covered) / len(kanji_positions) * 100


def main():
    data_dir = Path("data/dataset_gen")

    with open(data_dir / "filtered_sentences.json") as f:
        sentences = json.load(f)

    sent_by_id = {s["id"]: s for s in sentences}

    # Find all batch result files
    batch_files = sorted(Path("/tmp").glob("dataset_claude_batch_*.json"))
    print(f"Found {len(batch_files)} batch files")

    all_results = {}
    for bf in batch_files:
        try:
            data = extract_json_from_file(bf)
            if data and isinstance(data, dict):
                all_results.update(data)
                print(f"  {bf.name}: {len(data)} entries")
            else:
                print(f"  {bf.name}: FAILED to parse")
        except Exception as e:
            print(f"  {bf.name}: ERROR: {e}")

    print(f"\nTotal entries loaded: {len(all_results)}")

    # Assemble
    annotations = []
    coverage_issues = 0

    for sent in sentences:
        sid = sent["id"]
        text = sent["text"]

        annots = all_results.get(str(sid)) or all_results.get(sid)

        if annots and isinstance(annots, list):
            valid = [a for a in annots if isinstance(a, dict) and "surface" in a and "reading" in a]
            coverage = check_kanji_coverage(text, valid)
            if coverage < 100:
                coverage_issues += 1

            annotations.append({
                "id": sid,
                "series": sent["series"],
                "text": text,
                "annotations": valid,
                "kanji_coverage": coverage,
            })
        else:
            annotations.append({
                "id": sid,
                "series": sent["series"],
                "text": text,
                "annotations": [],
                "parse_failure": True,
            })

    output_path = data_dir / "annotations_claude.json"
    with open(output_path, "w") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

    success = sum(1 for a in annotations if not a.get("parse_failure"))
    avg_coverage = sum(a.get("kanji_coverage", 0) for a in annotations) / len(annotations)

    print(f"\nAssembled {success}/{len(sentences)} annotations")
    print(f"Average kanji coverage: {avg_coverage:.1f}%")
    print(f"Coverage issues (<100%): {coverage_issues}")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
