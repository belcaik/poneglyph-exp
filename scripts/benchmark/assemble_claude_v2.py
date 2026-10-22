#!/usr/bin/env python3
"""Assemble Claude v2 subagent batch results into annotations_claude_v2.json.

Reads /tmp/benchmark_result_*.json files (one per batch of 10 sentences),
validates each result, and assembles into the standard annotation format.
"""

import json
import re
from pathlib import Path


def is_kanji(c):
    code = ord(c)
    return 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF


def extract_json_from_text(text):
    """Extract JSON from text that may contain markdown or explanations."""
    text = text.strip()
    # Remove markdown fences
    text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find a JSON object
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


def check_kanji_coverage(text, annotations):
    """Check what percentage of kanji chars in text are covered by annotations."""
    kanji_positions = {i for i, c in enumerate(text) if is_kanji(c)}
    if not kanji_positions:
        return 100.0, []

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

    uncovered = [text[i] for i in sorted(kanji_positions - covered)]
    coverage = len(kanji_positions & covered) / len(kanji_positions) * 100
    return coverage, uncovered


def main():
    data_dir = Path("data/benchmark")

    with open(data_dir / "sentences_100.json") as f:
        sentences = json.load(f)

    sent_by_id = {s["id"]: s for s in sentences}

    # Load batch results
    all_results = {}
    for batch_idx in range(10):
        result_path = Path(f"/tmp/benchmark_result_{batch_idx}.json")
        if result_path.exists():
            try:
                with open(result_path) as f:
                    content = f.read()
                batch_data = extract_json_from_text(content)
                if batch_data and isinstance(batch_data, dict):
                    all_results.update(batch_data)
                    print(f"Batch {batch_idx}: loaded {len(batch_data)} sentences")
                else:
                    print(f"Batch {batch_idx}: FAILED to parse JSON")
            except Exception as e:
                print(f"Batch {batch_idx}: ERROR reading file: {e}")
        else:
            print(f"Batch {batch_idx}: MISSING ({result_path})")

    print(f"\nTotal sentence results loaded: {len(all_results)}")

    # Assemble annotations
    annotations = []
    coverage_issues = []

    for sent in sentences:
        sent_id = sent["id"]
        text = sent["text"]

        # Try both string and int keys
        annots = all_results.get(str(sent_id)) or all_results.get(sent_id)

        if annots and isinstance(annots, list):
            # Validate: check if annotations are well-formed
            valid_annots = []
            for ann in annots:
                if isinstance(ann, dict) and "surface" in ann and "reading" in ann:
                    valid_annots.append(ann)

            coverage, uncovered = check_kanji_coverage(text, valid_annots)

            annotations.append({
                "id": sent_id,
                "source": sent["source"],
                "text": text,
                "annotations": valid_annots,
                "time_seconds": 0,
                "kanji_coverage": coverage
            })

            if uncovered:
                coverage_issues.append({
                    "id": sent_id,
                    "coverage": coverage,
                    "uncovered_kanji": uncovered
                })
        else:
            annotations.append({
                "id": sent_id,
                "source": sent["source"],
                "text": text,
                "annotations": [],
                "parse_failure": True,
                "time_seconds": 0,
                "kanji_coverage": 0
            })
            coverage_issues.append({
                "id": sent_id,
                "coverage": 0,
                "uncovered_kanji": ["PARSE_FAILURE"]
            })

    # Save
    output_path = data_dir / "annotations_claude_v2.json"
    with open(output_path, "w") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

    success = sum(1 for a in annotations if not a.get("parse_failure"))
    avg_coverage = sum(a.get("kanji_coverage", 0) for a in annotations) / len(annotations)

    print(f"\nAssembled {success}/{len(sentences)} Claude v2 annotations")
    print(f"Average kanji coverage: {avg_coverage:.1f}%")

    if coverage_issues:
        print(f"\nCoverage issues in {len(coverage_issues)} sentences:")
        for issue in coverage_issues[:20]:
            chars = "".join(issue["uncovered_kanji"][:10])
            print(f"  sent {issue['id']}: {issue['coverage']:.0f}% — uncovered: {chars}")

    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
