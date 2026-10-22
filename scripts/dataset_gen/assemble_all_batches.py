#!/usr/bin/env python3
"""Assemble ALL Claude batch results (v1 + v2) into annotations_claude.json.

Reads both /tmp/dataset_claude_batch_*.json (v1) and
/tmp/dataset_v2_batch_*.json (v2) files, deduplicates by text,
and builds the combined annotation file.
"""

import json
import re
from pathlib import Path


def is_kanji(c):
    cp = ord(c)
    return 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF


def extract_json_from_file(filepath):
    with open(filepath) as f:
        content = f.read().strip()
    content = re.sub(r'^```(?:json)?\s*\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n?```\s*$', '', content, flags=re.MULTILINE)
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    brace_start = content.find('{')
    if brace_start >= 0:
        depth = 0
        for i in range(brace_start, len(content)):
            if content[i] == '{': depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    try: return json.loads(content[brace_start:i+1])
                    except json.JSONDecodeError: break
    return None


def check_kanji_coverage(text, annotations):
    kanji_positions = {i for i, c in enumerate(text) if is_kanji(c)}
    if not kanji_positions:
        return 100.0
    covered = set()
    used = set()
    for ann in annotations:
        surface = ann.get("surface", "")
        if not surface: continue
        pos = 0
        while pos < len(text):
            idx = text.find(surface, pos)
            if idx == -1: break
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

    # Load ALL batch files from both v1 and v2
    all_results = {}

    # V1 batches (dataset_claude_batch_*)
    for bf in sorted(Path("/tmp").glob("dataset_claude_batch_*.json")):
        try:
            data = extract_json_from_file(bf)
            if data and isinstance(data, dict):
                all_results.update(data)
        except Exception:
            pass

    # V2 batches (dataset_v2_batch_*)
    for bf in sorted(Path("/tmp").glob("dataset_v2_batch_*.json")):
        try:
            data = extract_json_from_file(bf)
            if data and isinstance(data, dict):
                all_results.update(data)
        except Exception:
            pass

    print(f"Total batch entries loaded: {len(all_results)}")

    # Also load existing annotations_claude.json for text-based matching
    text_to_annots = {}
    existing_path = data_dir / "annotations_claude.json"
    if existing_path.exists():
        try:
            with open(existing_path) as f:
                for a in json.load(f):
                    if not a.get("parse_failure") and a.get("annotations"):
                        text_to_annots[a["text"]] = a["annotations"]
        except Exception:
            pass
    print(f"Existing text-matched annotations: {len(text_to_annots)}")

    # Assemble
    annotations = []
    success = 0
    failures = 0

    for sent in sentences:
        sid = sent["id"]
        text = sent["text"]

        # Try ID-based match first (both string and int)
        annots = all_results.get(str(sid)) or all_results.get(sid)

        # Fall back to text-based match from old annotations
        if not annots and text in text_to_annots:
            annots = text_to_annots[text]

        if annots and isinstance(annots, list):
            valid = [a for a in annots if isinstance(a, dict) and "surface" in a and "reading" in a]
            coverage = check_kanji_coverage(text, valid)
            annotations.append({
                "id": sid,
                "series": sent["series"],
                "text": text,
                "annotations": valid,
                "kanji_coverage": coverage,
            })
            success += 1
        else:
            annotations.append({
                "id": sid,
                "series": sent["series"],
                "text": text,
                "annotations": [],
                "parse_failure": True,
            })
            failures += 1

    output_path = data_dir / "annotations_claude.json"
    with open(output_path, "w") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

    avg_coverage = sum(a.get("kanji_coverage", 0) for a in annotations if not a.get("parse_failure")) / max(success, 1)

    print(f"\nAssembled: {success}/{len(sentences)} successful ({failures} failures)")
    print(f"Average kanji coverage: {avg_coverage:.1f}%")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
