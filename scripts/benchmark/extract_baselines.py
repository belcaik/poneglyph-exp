#!/usr/bin/env python3
"""Step 3d: Extract baseline annotations for the 100 benchmark sentences.

Extracts:
- v7 ground truth annotations (already in the sentences file)
- ByT5 v2 predictions (if model is available)
"""

import json
from pathlib import Path


def extract_v7_ground_truth(sentences):
    """Extract v7 ground truth from the benchmark sentences."""
    annotations = []
    for sent in sentences:
        # v7_tokens are already in the sentences file
        tokens = sent["v7_tokens"]
        # Convert to annotation format (add type field)
        annots = []
        for token in tokens:
            annot = {
                "surface": token["surface"],
                "reading": token["reading"],
                "type": "unknown"  # v7 doesn't have type annotations
            }
            annots.append(annot)

        annotations.append({
            "id": sent["id"],
            "source": sent["source"],
            "text": sent["text"],
            "annotations": annots,
            "time_seconds": 0  # ground truth, no inference time
        })
    return annotations


def main():
    with open("data/benchmark/sentences_100.json") as f:
        sentences = json.load(f)

    output_dir = Path("data/benchmark")

    # v7 ground truth
    v7_annotations = extract_v7_ground_truth(sentences)
    with open(output_dir / "annotations_v7_gt.json", "w") as f:
        json.dump(v7_annotations, f, ensure_ascii=False, indent=2)
    print(f"v7 ground truth: {len(v7_annotations)} sentences")

    total_tokens = sum(len(a["annotations"]) for a in v7_annotations)
    print(f"  Total tokens: {total_tokens}")
    print(f"  Avg tokens/sentence: {total_tokens/len(v7_annotations):.1f}")

    # Check for ByT5 v2 predictions
    byt5_model_dir = Path("models/byt5-furigana-v2")
    if byt5_model_dir.exists():
        print("\nByT5 v2 model found — inference would need to be run separately")
        print("(seq2seq model outputs need bracket parsing, not direct JSON)")
    else:
        print("\nByT5 v2 model not found at models/byt5-furigana-v2 — skipping")

    # Check for any existing comparable results
    for result_file in Path("results").glob("*comparable*.json"):
        print(f"\nFound existing results: {result_file}")


if __name__ == "__main__":
    main()
