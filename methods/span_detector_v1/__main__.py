#!/usr/bin/env python3
"""
Evaluate Span Detector v1 and the two-stage pipeline.

Three evaluation modes:
1. Span-level metrics (precision, recall, F1)
2. End-to-end pipeline (span detector + BERT v2 reading classifier)
3. Error analysis (per-source, span length, error types)

Usage:
    # Span metrics only
    python -m methods.span_detector_v1 \
        --span-model models/span-detector-v1 \
        --input data/splits_v7_normalized/test.json

    # Full pipeline
    python -m methods.span_detector_v1 \
        --span-model models/span-detector-v1 \
        --reading-model models/bert-furigana-v2 \
        --input data/splits_v7_normalized/test.json \
        --pipeline

    # Save results
    python -m methods.span_detector_v1 \
        --span-model models/span-detector-v1 \
        --reading-model models/bert-furigana-v2 \
        --input data/splits_v7_normalized/test.json \
        --pipeline --output results/span_detector_v1_eval.json
"""

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from .annotator import SpanDetectorAnnotator


def contains_kanji(text: str) -> bool:
    for char in text:
        code = ord(char)
        if (0x4E00 <= code <= 0x9FFF or
            0x3400 <= code <= 0x4DBF or
            0xF900 <= code <= 0xFAFF):
            return True
    return False


def extract_gold_spans(sentence: dict) -> list[dict]:
    """Extract gold spans from a v7 normalized sentence."""
    text = sentence["text"]
    tokens = sentence["tokens"]
    spans = []
    used = set()

    for token in tokens:
        surface = token["surface"]
        reading = token["reading"]
        if not contains_kanji(surface):
            continue

        search_start = 0
        while search_start < len(text):
            pos = text.find(surface, search_start)
            if pos == -1:
                break
            if not any(p in used for p in range(pos, pos + len(surface))):
                for p in range(pos, pos + len(surface)):
                    used.add(p)
                spans.append({
                    "surface": surface,
                    "reading": reading,
                    "start": pos,
                    "end": pos + len(surface),
                })
                break
            search_start = pos + 1

    return spans


def compute_span_metrics(pred_spans_list, gold_spans_list):
    """Compute span-level precision, recall, F1 across all sentences."""
    total_pred = 0
    total_gold = 0
    total_correct = 0

    for pred_spans, gold_spans in zip(pred_spans_list, gold_spans_list):
        pred_set = {(s["start"], s["end"]) for s in pred_spans}
        gold_set = {(s["start"], s["end"]) for s in gold_spans}
        total_pred += len(pred_set)
        total_gold += len(gold_set)
        total_correct += len(pred_set & gold_set)

    precision = total_correct / total_pred if total_pred > 0 else 0
    recall = total_correct / total_gold if total_gold > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "pred_spans": total_pred,
        "gold_spans": total_gold,
        "correct_spans": total_correct,
    }


def evaluate_spans(span_detector, sentences):
    """Evaluate span detection on test sentences."""
    all_pred_spans = []
    all_gold_spans = []
    per_source_pred = defaultdict(list)
    per_source_gold = defaultdict(list)

    latencies = []
    span_length_stats = {"correct": Counter(), "missed": Counter(), "spurious": Counter()}

    for sent in sentences:
        text = sent["text"]
        source = sent.get("source", "unknown")
        gold_spans = extract_gold_spans(sent)

        start_t = time.perf_counter()
        pred_spans = span_detector.detect_spans(text)
        latency = (time.perf_counter() - start_t) * 1000
        latencies.append(latency)

        all_pred_spans.append(pred_spans)
        all_gold_spans.append(gold_spans)
        per_source_pred[source].append(pred_spans)
        per_source_gold[source].append(gold_spans)

        # Span length analysis
        pred_set = {(s["start"], s["end"]) for s in pred_spans}
        gold_set = {(s["start"], s["end"]) for s in gold_spans}

        for start, end in pred_set & gold_set:
            span_length_stats["correct"][end - start] += 1
        for start, end in gold_set - pred_set:
            span_length_stats["missed"][end - start] += 1
        for start, end in pred_set - gold_set:
            span_length_stats["spurious"][end - start] += 1

    overall = compute_span_metrics(all_pred_spans, all_gold_spans)

    per_source = {}
    for source in sorted(per_source_pred):
        per_source[source] = compute_span_metrics(
            per_source_pred[source], per_source_gold[source]
        )

    latencies.sort()
    n = len(latencies)
    latency_stats = {
        "mean_ms": round(sum(latencies) / n, 2) if n > 0 else 0,
        "p50_ms": round(latencies[n // 2], 2) if n > 0 else 0,
        "p95_ms": round(latencies[int(n * 0.95)], 2) if n > 0 else 0,
    }

    return {
        "overall": overall,
        "per_source": per_source,
        "latency": latency_stats,
        "span_length_stats": {
            k: dict(sorted(v.items())) for k, v in span_length_stats.items()
        },
        "all_pred_spans": all_pred_spans,
        "all_gold_spans": all_gold_spans,
    }


def evaluate_pipeline(span_detector, reading_annotator, sentences):
    """Evaluate the full two-stage pipeline against ground truth."""
    total_tokens = 0
    total_matches = 0
    per_source_matches = Counter()
    per_source_total = Counter()

    error_types = Counter()
    error_examples = defaultdict(list)

    latencies = []

    for sent in sentences:
        text = sent["text"]
        source = sent.get("source", "unknown")
        gold_spans = extract_gold_spans(sent)

        start_t = time.perf_counter()

        # Stage 1: Detect spans
        pred_spans = span_detector.detect_spans(text)

        # Stage 2: For each detected span, predict reading
        pred_tokens = []
        for span in pred_spans:
            surface = span["surface"]
            reading = reading_annotator.predict_reading(
                text, surface, span["start"], span["end"]
            )
            pred_tokens.append({
                "surface": surface,
                "reading": reading,
                "start": span["start"],
                "end": span["end"],
            })

        latency = (time.perf_counter() - start_t) * 1000
        latencies.append(latency)

        # Match predictions against gold
        gold_map = {(s["start"], s["end"]): s for s in gold_spans}
        pred_map = {(s["start"], s["end"]): s for s in pred_tokens}

        for (start, end), gold in gold_map.items():
            total_tokens += 1
            per_source_total[source] += 1

            if (start, end) in pred_map:
                pred = pred_map[(start, end)]
                if pred["reading"] == gold["reading"]:
                    total_matches += 1
                    per_source_matches[source] += 1
                else:
                    error_types["wrong_reading"] += 1
                    if len(error_examples["wrong_reading"]) < 20:
                        error_examples["wrong_reading"].append({
                            "surface": gold["surface"],
                            "gold": gold["reading"],
                            "pred": pred["reading"],
                            "source": source,
                        })
            else:
                error_types["missed_span"] += 1
                if len(error_examples["missed_span"]) < 20:
                    error_examples["missed_span"].append({
                        "surface": gold["surface"],
                        "gold": gold["reading"],
                        "source": source,
                    })

        # Count spurious spans (predicted but not in gold)
        for (start, end), pred in pred_map.items():
            if (start, end) not in gold_map:
                error_types["spurious_span"] += 1
                if len(error_examples["spurious_span"]) < 20:
                    error_examples["spurious_span"].append({
                        "surface": pred["surface"],
                        "pred_reading": pred.get("reading", ""),
                        "source": source,
                    })

    accuracy = total_matches / total_tokens * 100 if total_tokens > 0 else 0

    per_source_accuracy = {}
    for source in sorted(per_source_total):
        total = per_source_total[source]
        matches = per_source_matches[source]
        per_source_accuracy[source] = {
            "accuracy": round(matches / total * 100, 1) if total > 0 else 0,
            "matches": matches,
            "total": total,
        }

    latencies.sort()
    n = len(latencies)
    latency_stats = {
        "mean_ms": round(sum(latencies) / n, 2) if n > 0 else 0,
        "p50_ms": round(latencies[n // 2], 2) if n > 0 else 0,
        "p95_ms": round(latencies[int(n * 0.95)], 2) if n > 0 else 0,
    }

    return {
        "accuracy": round(accuracy, 1),
        "total_tokens": total_tokens,
        "total_matches": total_matches,
        "per_source": per_source_accuracy,
        "error_types": dict(error_types),
        "error_examples": dict(error_examples),
        "latency": latency_stats,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Span Detector v1")
    parser.add_argument("--span-model", type=Path, default=Path("models/span-detector-v1"),
                        help="Path to span detector model")
    parser.add_argument("--reading-model", type=Path, default=Path("models/bert-furigana-v2"),
                        help="Path to BERT v2 reading classifier")
    parser.add_argument("--input", type=Path, default=Path("data/splits_v7_normalized/test.json"),
                        help="Test data path")
    parser.add_argument("--pipeline", action="store_true",
                        help="Run full pipeline evaluation (requires --reading-model)")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output JSON path for results")
    args = parser.parse_args()

    print("=" * 60)
    print("Span Detector v1 - Evaluation")
    print("=" * 60)

    # Load test data
    with open(args.input) as f:
        sentences = json.load(f)
    print(f"Test sentences: {len(sentences)}")

    # Load span detector
    span_detector = SpanDetectorAnnotator(args.span_model)

    # Evaluate span detection
    print("\n--- Span Detection Metrics ---")
    span_results = evaluate_spans(span_detector, sentences)

    overall = span_results["overall"]
    print(f"\nOverall: P={overall['precision']:.4f} R={overall['recall']:.4f} F1={overall['f1']:.4f}")
    print(f"  Predicted: {overall['pred_spans']} spans")
    print(f"  Gold:      {overall['gold_spans']} spans")
    print(f"  Correct:   {overall['correct_spans']} spans")

    print(f"\nPer-source:")
    for source, metrics in span_results["per_source"].items():
        print(f"  {source}: P={metrics['precision']:.4f} R={metrics['recall']:.4f} "
              f"F1={metrics['f1']:.4f} ({metrics['correct_spans']}/{metrics['gold_spans']})")

    lat = span_results["latency"]
    print(f"\nLatency: mean={lat['mean_ms']:.1f}ms p50={lat['p50_ms']:.1f}ms p95={lat['p95_ms']:.1f}ms")

    # Span length analysis
    print(f"\nSpan length accuracy:")
    for length in sorted(set(
        list(span_results["span_length_stats"]["correct"].keys()) +
        list(span_results["span_length_stats"]["missed"].keys())
    )):
        c = span_results["span_length_stats"]["correct"].get(length, 0)
        m = span_results["span_length_stats"]["missed"].get(length, 0)
        total = c + m
        acc = c / total * 100 if total > 0 else 0
        print(f"  Length {length}: {c}/{total} ({acc:.1f}%)")

    results = {"span_detection": {
        "overall": span_results["overall"],
        "per_source": span_results["per_source"],
        "latency": span_results["latency"],
        "span_length_stats": span_results["span_length_stats"],
    }}

    # Pipeline evaluation
    if args.pipeline:
        print("\n--- Pipeline Evaluation (Span Detector + BERT v2) ---")
        from methods.bert_v2.annotator import BertV2Annotator
        reading_annotator = BertV2Annotator(args.reading_model)

        pipeline_results = evaluate_pipeline(span_detector, reading_annotator, sentences)

        print(f"\nPipeline Accuracy: {pipeline_results['accuracy']:.1f}%")
        print(f"  Matches: {pipeline_results['total_matches']}/{pipeline_results['total_tokens']}")

        print(f"\nPer-source:")
        for source, info in pipeline_results["per_source"].items():
            print(f"  {source}: {info['accuracy']:.1f}% ({info['matches']}/{info['total']})")

        print(f"\nError breakdown:")
        for err_type, count in sorted(pipeline_results["error_types"].items()):
            print(f"  {err_type}: {count}")

        lat = pipeline_results["latency"]
        print(f"\nPipeline latency: mean={lat['mean_ms']:.1f}ms "
              f"p50={lat['p50_ms']:.1f}ms p95={lat['p95_ms']:.1f}ms")

        results["pipeline"] = pipeline_results

    # Save results
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to {args.output}")

    print("\n" + "=" * 60)
    print("Evaluation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
