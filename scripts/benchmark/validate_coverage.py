#!/usr/bin/env python3
"""Step 5: Validate kanji coverage for all model annotations.

For every model, checks that every kanji character in each input sentence
is covered by at least one annotation span. Reports uncovered kanji.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def is_kanji(c):
    code = ord(c)
    return 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF


def get_kanji_positions(text):
    """Return set of (position, character) for all kanji in text."""
    return {(i, c) for i, c in enumerate(text) if is_kanji(c)}


def get_covered_positions(text, annotations):
    """Return set of character positions covered by annotation spans."""
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
            span_positions = set(range(idx, idx + len(surface)))
            if not span_positions & used:
                covered |= span_positions
                used |= span_positions
                break
            pos = idx + 1

    return covered


def validate_model(sentences, annotations, model_name):
    """Validate kanji coverage for a single model."""
    total_kanji = 0
    covered_kanji = 0
    uncovered_details = []

    annot_by_id = {a["id"]: a for a in annotations}

    for sent in sentences:
        sent_id = sent["id"]
        text = sent["text"]

        kanji_positions = get_kanji_positions(text)
        total_kanji += len(kanji_positions)

        annot = annot_by_id.get(sent_id)
        if not annot or annot.get("parse_failure"):
            uncovered_details.append({
                "sent_id": sent_id,
                "source": sent["source"],
                "uncovered": [{"pos": p, "char": c} for p, c in sorted(kanji_positions)],
                "reason": "parse_failure" if annot else "missing"
            })
            continue

        covered_pos = get_covered_positions(text, annot.get("annotations", []))
        sent_uncovered = []
        for pos, char in sorted(kanji_positions):
            if pos in covered_pos:
                covered_kanji += 1
            else:
                sent_uncovered.append({"pos": pos, "char": char})

        if sent_uncovered:
            uncovered_details.append({
                "sent_id": sent_id,
                "source": sent["source"],
                "uncovered": sent_uncovered
            })

    return {
        "model": model_name,
        "total_kanji_chars": total_kanji,
        "covered_kanji_chars": covered_kanji,
        "coverage_pct": covered_kanji / total_kanji * 100 if total_kanji > 0 else 0,
        "uncovered_sentences": len(uncovered_details),
        "uncovered_details": uncovered_details
    }


def main():
    data_dir = Path("data/benchmark")

    with open(data_dir / "sentences_100.json") as f:
        sentences = json.load(f)

    # Count total kanji in corpus
    total_kanji = sum(len(get_kanji_positions(s["text"])) for s in sentences)
    print(f"Total kanji characters in 100 sentences: {total_kanji}\n")

    models = {}
    for name, filename in [
        ("claude_v2", "annotations_claude_v2.json"),
        ("claude", "annotations_claude.json"),
        ("qwen7b", "annotations_qwen7b.json"),
        ("gemini", "annotations_gemini.json"),
        ("v7_gt", "annotations_v7_gt.json"),
    ]:
        filepath = data_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                models[name] = json.load(f)

    if not models:
        print("No annotation files found.")
        return

    results = {}
    for name, annots in models.items():
        result = validate_model(sentences, annots, name)
        results[name] = result

        status = "PASS" if result["coverage_pct"] >= 99.0 else "FAIL"
        print(f"[{status}] {name}: {result['coverage_pct']:.1f}% coverage "
              f"({result['covered_kanji_chars']}/{result['total_kanji_chars']} kanji chars)")

        if result["uncovered_details"]:
            print(f"  Uncovered in {result['uncovered_sentences']} sentences:")
            for detail in result["uncovered_details"][:10]:
                chars = "".join(u["char"] for u in detail["uncovered"])
                reason = f" ({detail['reason']})" if "reason" in detail else ""
                print(f"    sent {detail['sent_id']} ({detail['source']}): {chars}{reason}")
            if len(result["uncovered_details"]) > 10:
                print(f"    ... and {len(result['uncovered_details']) - 10} more sentences")

    # Save validation report
    output_path = data_dir / "coverage_validation.json"
    with open(output_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nValidation results saved to {output_path}")

    # Return exit code based on whether all models pass
    all_pass = all(r["coverage_pct"] >= 99.0 for r in results.values())
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main() or 0)
