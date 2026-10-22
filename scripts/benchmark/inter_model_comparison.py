#!/usr/bin/env python3
"""Generate inter-model comparison showing per-span agreement across all models."""

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


def is_kanji(c):
    code = ord(c)
    return 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF


def build_surface_reading_map(annotations):
    """Build surface -> first_reading map from annotations list."""
    m = {}
    for ann in annotations:
        s = ann.get("surface", "")
        r = normalize_reading(ann.get("reading", ""))
        if s and r and s not in m:
            m[s] = r
    return m


def main():
    data_dir = Path("data/benchmark")

    with open(data_dir / "sentences_100.json") as f:
        sentences = json.load(f)

    with open(data_dir / "annotations_v7_gt.json") as f:
        gt = json.load(f)

    # Load all available models
    model_files = {
        "claude_v2": "annotations_claude_v2.json",
        "qwen7b": "annotations_qwen7b.json",
        "gemini": "annotations_gemini.json",
    }

    models = {}
    for name, filename in model_files.items():
        filepath = data_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                models[name] = json.load(f)
            print(f"Loaded {name}: {len(models[name])} sentences")

    if not models:
        print("No model annotations found.")
        return

    model_names = sorted(models.keys())
    gt_by_id = {g["id"]: g for g in gt}

    comparison = []

    for sent in sentences:
        sent_id = sent["id"]
        text = sent["text"]
        source = sent["source"]

        # Build reading maps for all models + GT
        gt_sent = gt_by_id.get(sent_id, {})
        gt_map = build_surface_reading_map(gt_sent.get("annotations", []))

        model_maps = {}
        for name in model_names:
            ms = next((m for m in models[name] if m["id"] == sent_id), None)
            if ms and not ms.get("parse_failure"):
                model_maps[name] = build_surface_reading_map(ms.get("annotations", []))
            else:
                model_maps[name] = {}

        # Collect all surfaces from all sources
        all_surfaces = set(gt_map.keys())
        for name in model_names:
            all_surfaces.update(model_maps[name].keys())

        # Filter to kanji-containing surfaces only
        all_surfaces = {s for s in all_surfaces if any(is_kanji(c) for c in s)}

        spans = []
        for surface in sorted(all_surfaces, key=lambda s: text.find(s) if text.find(s) >= 0 else 9999):
            span_info = {"surface": surface}

            # Get each model's reading
            readings = {}
            for name in model_names:
                r = model_maps[name].get(surface, "")
                span_info[f"{name}_reading"] = r if r else None
                if r:
                    readings[name] = r

            span_info["v7_gt_reading"] = gt_map.get(surface, None)

            # Count agreement among LLMs
            if readings:
                reading_counts = defaultdict(list)
                for name, r in readings.items():
                    reading_counts[r].append(name)
                most_common = max(reading_counts.values(), key=len)
                total_models = len(model_names)
                agreeing = len(most_common)
                span_info["agreement"] = f"{agreeing}/{total_models} LLMs agree"
                span_info["consensus_reading"] = max(reading_counts, key=lambda r: len(reading_counts[r]))
            else:
                span_info["agreement"] = "0 LLMs annotated"
                span_info["consensus_reading"] = None

            # Check GT vs LLM agreement
            gt_reading = gt_map.get(surface)
            if gt_reading and readings:
                gt_matches = sum(1 for r in readings.values()
                                if r == gt_reading or gt_reading in r or r in gt_reading)
                span_info["gt_matches_llms"] = gt_matches > 0
            else:
                span_info["gt_matches_llms"] = None

            spans.append(span_info)

        if spans:
            comparison.append({
                "sentence_id": sent_id,
                "source": source,
                "text": text,
                "spans": spans
            })

    # Save
    output_path = data_dir / "inter_model_comparison.json"
    with open(output_path, "w") as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)

    # Summary stats
    total_spans = sum(len(s["spans"]) for s in comparison)
    agreement_counts = defaultdict(int)
    for sent in comparison:
        for span in sent["spans"]:
            agreement_counts[span["agreement"]] += 1

    print(f"\nTotal annotatable spans: {total_spans}")
    print("Agreement distribution:")
    for k in sorted(agreement_counts.keys()):
        print(f"  {k}: {agreement_counts[k]}")

    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
