#!/usr/bin/env python3
"""Step 5: Generate human review file for disagreement cases."""

import json
from collections import defaultdict
from pathlib import Path


def normalize_reading(reading):
    if not reading:
        return ""
    reading = reading.strip()
    result = []
    for c in reading:
        code = ord(c)
        if 0x30A1 <= code <= 0x30F6:
            result.append(chr(code - 0x60))
        else:
            result.append(c)
    return "".join(result)


def build_surface_reading_map(annotations):
    """Build surface -> [readings] map."""
    m = defaultdict(list)
    for ann in annotations:
        s = ann.get("surface", "")
        r = normalize_reading(ann.get("reading", ""))
        if s and r:
            m[s].append(r)
    return dict(m)


def main():
    data_dir = Path("data/benchmark")

    with open(data_dir / "sentences_100.json") as f:
        sentences = json.load(f)

    with open(data_dir / "annotations_v7_gt.json") as f:
        gt = json.load(f)

    # Load available models
    models = {}
    for name, filename in [("claude_v2", "annotations_claude_v2.json"),
                            ("qwen7b", "annotations_qwen7b.json"),
                            ("gemini", "annotations_gemini.json")]:
        filepath = data_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                models[name] = json.load(f)

    model_names = sorted(models.keys())
    if not model_names:
        print("No model annotations found.")
        return

    # Build per-sentence comparison
    md_lines = ["# Benchmark Human Review\n"]
    md_lines.append(f"Models compared: {', '.join(model_names)} vs v7 GT\n\n")

    tsv_lines = ["sent_id\tsource\tsurface\t" + "\t".join(model_names) + "\tv7_gt\tdisagreement_type\n"]

    disagreement_count = 0
    total_tokens_reviewed = 0

    for sent in sentences:
        sent_id = sent["id"]
        text = sent["text"]
        source = sent["source"]

        # Get GT annotations
        gt_sent = next((g for g in gt if g["id"] == sent_id), None)
        if not gt_sent:
            continue

        gt_map = build_surface_reading_map(gt_sent["annotations"])

        # Get model annotations
        model_maps = {}
        for name in model_names:
            ms = next((m for m in models[name] if m["id"] == sent_id), None)
            if ms and not ms.get("parse_failure"):
                model_maps[name] = build_surface_reading_map(ms.get("annotations", []))
            else:
                model_maps[name] = {}

        # Collect all surfaces mentioned by anyone
        all_surfaces = set()
        for s in gt_map:
            all_surfaces.add(s)
        for name in model_names:
            for s in model_maps[name]:
                all_surfaces.add(s)

        # Find disagreements for this sentence
        sent_disagreements = []
        for surface in sorted(all_surfaces):
            gt_readings = gt_map.get(surface, [])
            model_readings = {}
            for name in model_names:
                model_readings[name] = model_maps[name].get(surface, [])

            # Check if there's any disagreement
            all_readings = set()
            if gt_readings:
                all_readings.update(gt_readings)
            for name in model_names:
                if model_readings[name]:
                    all_readings.update(model_readings[name])

            if len(all_readings) <= 1 and all(bool(model_readings[n]) == bool(gt_readings) for n in model_names):
                continue  # Full agreement, skip

            # Determine disagreement type
            model_present = [name for name in model_names if model_readings[name]]
            gt_present = bool(gt_readings)

            if not gt_present and model_present:
                dtype = "model_extra"
            elif gt_present and not model_present:
                dtype = "model_missing"
            elif gt_present and model_present:
                # Check reading disagreement
                gt_r = gt_readings[0] if gt_readings else ""
                model_r = {name: model_readings[name][0] if model_readings[name] else "" for name in model_names}
                if any(model_r[n] != gt_r for n in model_names if model_r[n]):
                    dtype = "reading_diff"
                else:
                    dtype = "coverage_diff"
            else:
                continue

            sent_disagreements.append({
                "surface": surface,
                "gt_readings": gt_readings,
                "model_readings": model_readings,
                "dtype": dtype,
            })

            total_tokens_reviewed += 1

            # TSV line
            model_cols = []
            for name in model_names:
                r = ", ".join(model_readings[name]) if model_readings[name] else "—"
                model_cols.append(r)
            gt_col = ", ".join(gt_readings) if gt_readings else "—"
            tsv_lines.append(f"{sent_id}\t{source}\t{surface}\t" +
                           "\t".join(model_cols) + f"\t{gt_col}\t{dtype}\n")

        if sent_disagreements:
            disagreement_count += len(sent_disagreements)
            md_lines.append(f"## Sentence {sent_id} ({source})\n")
            md_lines.append(f'"{text}"\n\n')

            # Table header
            header = "| Surface |"
            separator = "|---------|"
            for name in model_names:
                header += f" {name} |"
                separator += "---------|"
            header += " v7 GT | Type |"
            separator += "-------|------|"
            md_lines.append(header + "\n")
            md_lines.append(separator + "\n")

            for d in sent_disagreements:
                row = f"| {d['surface']} |"
                for name in model_names:
                    r = ", ".join(d["model_readings"][name]) if d["model_readings"][name] else "—"
                    row += f" {r} |"
                gt_r = ", ".join(d["gt_readings"]) if d["gt_readings"] else "—"
                row += f" {gt_r} | {d['dtype']} |"
                md_lines.append(row + "\n")

            md_lines.append("\n")

    # Write markdown
    with open(data_dir / "human_review.md", "w") as f:
        f.write("".join(md_lines))

    # Write TSV
    with open(data_dir / "disagreements.tsv", "w") as f:
        f.writelines(tsv_lines)

    print(f"Found {disagreement_count} disagreements across {total_tokens_reviewed} token comparisons")
    print(f"Written to:")
    print(f"  {data_dir / 'human_review.md'}")
    print(f"  {data_dir / 'disagreements.tsv'}")


if __name__ == "__main__":
    main()
