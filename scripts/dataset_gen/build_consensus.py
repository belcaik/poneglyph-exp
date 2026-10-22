#!/usr/bin/env python3
"""Build consensus dataset from Claude and Gemini annotations.

Compares span-by-span, accepts agreements, flags disagreements,
and resolves using Claude as default (higher benchmark accuracy).
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def normalize_reading(reading):
    """Normalize reading: katakana to hiragana, strip whitespace."""
    if not reading:
        return ""
    result = []
    for c in reading.strip():
        cp = ord(c)
        if 0x30A1 <= cp <= 0x30F6:
            result.append(chr(cp - 0x60))
        else:
            result.append(c)
    return "".join(result)


def is_kanji(c):
    cp = ord(c)
    return 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF


def build_span_map(text, annotations):
    """Build surface -> (reading, type) map, handling duplicate surfaces."""
    spans = []
    used = set()
    for ann in annotations:
        surface = ann.get("surface", "")
        reading = normalize_reading(ann.get("reading", ""))
        ann_type = ann.get("type", "unknown")
        if not surface or not reading:
            continue

        # Find position in text
        pos = 0
        while pos < len(text):
            idx = text.find(surface, pos)
            if idx == -1:
                break
            span_range = set(range(idx, idx + len(surface)))
            if not span_range & used:
                used |= span_range
                spans.append({
                    "surface": surface,
                    "reading": reading,
                    "type": ann_type,
                    "start": idx,
                    "end": idx + len(surface),
                })
                break
            pos = idx + 1

    return spans


def find_best_overlap(claude_span, gemini_spans):
    """Find the Gemini span with the most character overlap with a Claude span."""
    best = None
    best_overlap = 0
    c_range = set(range(claude_span["start"], claude_span["end"]))

    for g_span in gemini_spans:
        g_range = set(range(g_span["start"], g_span["end"]))
        overlap = len(c_range & g_range)
        if overlap > best_overlap:
            best_overlap = overlap
            best = g_span

    return best, best_overlap


def main():
    data_dir = Path("data/dataset_gen")

    with open(data_dir / "filtered_sentences.json") as f:
        sentences = json.load(f)

    # Load annotations
    claude_annots = {}
    gemini_annots = {}

    claude_path = data_dir / "annotations_claude.json"
    gemini_path = data_dir / "annotations_gemini.json"

    if claude_path.exists():
        with open(claude_path) as f:
            for a in json.load(f):
                if not a.get("parse_failure"):
                    claude_annots[a["id"]] = a
        print(f"Claude: {len(claude_annots)} successful annotations")

    if gemini_path.exists():
        with open(gemini_path) as f:
            for a in json.load(f):
                if not a.get("parse_failure"):
                    gemini_annots[a["id"]] = a
        print(f"Gemini: {len(gemini_annots)} successful annotations")

    if not claude_annots:
        print("ERROR: No Claude annotations found")
        return

    # Build consensus
    accepted = []
    flagged = []
    stats = Counter()

    for sent in sentences:
        sid = sent["id"]
        text = sent["text"]

        c_data = claude_annots.get(sid)
        g_data = gemini_annots.get(sid)

        if not c_data:
            stats["claude_missing"] += 1
            continue

        c_spans = build_span_map(text, c_data.get("annotations", []))
        g_spans = build_span_map(text, g_data.get("annotations", [])) if g_data else []

        tokens = []
        disagreements = []
        g_used = set()

        for c_span in c_spans:
            # Skip if no kanji in span
            if not any(is_kanji(c) for c in c_span["surface"]):
                continue

            g_match, overlap = find_best_overlap(c_span, [g for i, g in enumerate(g_spans) if i not in g_used])

            if g_match and overlap > 0:
                g_idx = next(i for i, g in enumerate(g_spans) if g is g_match)
                g_used.add(g_idx)

                if c_span["surface"] == g_match["surface"] and c_span["reading"] == g_match["reading"]:
                    # Full agreement
                    stats["full_agreement"] += 1
                    tokens.append({
                        "surface": c_span["surface"],
                        "reading": c_span["reading"],
                        "start": c_span["start"],
                        "end": c_span["end"],
                        "type": c_span["type"],
                        "confidence": "consensus",
                    })
                elif c_span["surface"] == g_match["surface"]:
                    # Same surface, different reading
                    stats["reading_diff"] += 1
                    tokens.append({
                        "surface": c_span["surface"],
                        "reading": c_span["reading"],  # Default to Claude
                        "start": c_span["start"],
                        "end": c_span["end"],
                        "type": c_span["type"],
                        "confidence": "claude_default",
                    })
                    disagreements.append({
                        "claude_surface": c_span["surface"],
                        "claude_reading": c_span["reading"],
                        "gemini_surface": g_match["surface"],
                        "gemini_reading": g_match["reading"],
                        "type": "reading_diff",
                        "resolution": "claude",
                    })
                else:
                    # Different segmentation
                    stats["segmentation_diff"] += 1
                    # Use Claude's segmentation (follows Poneglyph conventions)
                    tokens.append({
                        "surface": c_span["surface"],
                        "reading": c_span["reading"],
                        "start": c_span["start"],
                        "end": c_span["end"],
                        "type": c_span["type"],
                        "confidence": "claude_default",
                    })
                    disagreements.append({
                        "claude_surface": c_span["surface"],
                        "claude_reading": c_span["reading"],
                        "gemini_surface": g_match["surface"],
                        "gemini_reading": g_match["reading"],
                        "type": "segmentation_diff",
                        "resolution": "claude",
                    })
            else:
                # Claude only
                stats["claude_only"] += 1
                tokens.append({
                    "surface": c_span["surface"],
                    "reading": c_span["reading"],
                    "start": c_span["start"],
                    "end": c_span["end"],
                    "type": c_span["type"],
                    "confidence": "claude_only",
                })

        # Check for Gemini-only spans
        for i, g_span in enumerate(g_spans):
            if i not in g_used and any(is_kanji(c) for c in g_span["surface"]):
                stats["gemini_only"] += 1
                disagreements.append({
                    "gemini_surface": g_span["surface"],
                    "gemini_reading": g_span["reading"],
                    "type": "gemini_only",
                    "resolution": "excluded",
                })

        # Sort tokens by position
        tokens.sort(key=lambda t: t["start"])

        entry = {
            "id": sid,
            "series": sent["series"],
            "episode": sent["episode"],
            "text": text,
            "tokens": tokens,
        }

        if disagreements:
            flagged.append({**entry, "disagreements": disagreements})
        else:
            accepted.append(entry)

    # Also accept flagged with resolutions (they have tokens already)
    all_resolved = accepted + flagged

    total_spans = sum(stats.values())
    agreement_rate = stats["full_agreement"] / total_spans if total_spans > 0 else 0

    consensus_stats = {
        "total_sentences": len(all_resolved),
        "total_spans": total_spans,
        "full_agreement": stats["full_agreement"],
        "reading_diff": stats["reading_diff"],
        "segmentation_diff": stats["segmentation_diff"],
        "claude_only": stats["claude_only"],
        "gemini_only": stats["gemini_only"],
        "claude_missing": stats["claude_missing"],
        "agreement_rate": round(agreement_rate, 4),
        "accepted_clean": len(accepted),
        "flagged_with_resolution": len(flagged),
    }

    # Save
    with open(data_dir / "consensus_accepted.json", "w") as f:
        json.dump(accepted, f, ensure_ascii=False, indent=2)

    with open(data_dir / "consensus_flagged.json", "w") as f:
        json.dump(flagged, f, ensure_ascii=False, indent=2)

    with open(data_dir / "consensus_stats.json", "w") as f:
        json.dump(consensus_stats, f, ensure_ascii=False, indent=2)

    # Resolution log
    resolutions = []
    for entry in flagged:
        for d in entry.get("disagreements", []):
            resolutions.append({
                "sentence_id": entry["id"],
                "text": entry["text"][:50],
                **d,
            })
    with open(data_dir / "resolution_log.json", "w") as f:
        json.dump(resolutions, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Consensus Results:")
    print(f"  Total sentences: {consensus_stats['total_sentences']}")
    print(f"  Total spans: {total_spans}")
    print(f"  Full agreement: {stats['full_agreement']} ({agreement_rate:.1%})")
    print(f"  Reading diff: {stats['reading_diff']}")
    print(f"  Segmentation diff: {stats['segmentation_diff']}")
    print(f"  Claude only: {stats['claude_only']}")
    print(f"  Gemini only: {stats['gemini_only']}")
    print(f"  Clean accepted: {len(accepted)}")
    print(f"  Flagged (resolved): {len(flagged)}")
    print(f"\nSaved to data/dataset_gen/consensus_*.json")


if __name__ == "__main__":
    main()
