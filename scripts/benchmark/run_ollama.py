#!/usr/bin/env python3
"""Step 3a: Run Qwen2.5-7B via Ollama on benchmark sentences."""

import json
import re
import time
from pathlib import Path

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"
MAX_RETRIES = 3


def load_prompt_template():
    with open("data/benchmark/prompt_template.txt") as f:
        return f.read()


def query_ollama(prompt, model=MODEL):
    """Query Ollama API with retry logic."""
    response = requests.post(OLLAMA_URL, json={
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 4096}
    }, timeout=300)
    response.raise_for_status()
    return response.json()["response"]


def extract_json(text):
    """Extract JSON array from LLM response, handling common issues."""
    # Try direct parse first
    text = text.strip()
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try to find JSON array in the response
    match = re.search(r'\[[\s\S]*?\](?=\s*$|\s*```)', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Try with more aggressive extraction
    match = re.search(r'\[[\s\S]*\]', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


def main():
    prompt_template = load_prompt_template()

    with open("data/benchmark/sentences_100.json") as f:
        sentences = json.load(f)

    output_dir = Path("data/benchmark")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check Ollama connectivity
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        print(f"Ollama models available: {models}")
        if not any(MODEL.split(":")[0] in m for m in models):
            print(f"WARNING: {MODEL} not found. Pull it with: ollama pull {MODEL}")
            return
    except Exception as e:
        print(f"ERROR: Cannot connect to Ollama: {e}")
        print("Start Ollama with: ollama serve")
        return

    annotations = []
    raw_outputs = []
    failures = []
    total_time = 0

    # Resume support
    existing_ids = set()
    partial_path = output_dir / "annotations_qwen7b.json"
    if partial_path.exists():
        try:
            with open(partial_path) as f:
                annotations = json.load(f)
            existing_ids = {a["id"] for a in annotations if not a.get("parse_failure")}
            print(f"Resuming: found {len(existing_ids)} existing successful annotations")
        except Exception:
            pass

    raw_path = output_dir / "raw_qwen7b.json"
    if raw_path.exists():
        try:
            with open(raw_path) as f:
                raw_outputs = json.load(f)
        except Exception:
            pass

    remaining = [s for s in sentences if s["id"] not in existing_ids]
    print(f"\nProcessing {len(remaining)} remaining sentences with {MODEL}...")
    for i, sent in enumerate(remaining):
        prompt = prompt_template.replace("{text}", sent["text"])
        parsed = None

        for attempt in range(MAX_RETRIES):
            try:
                start = time.time()
                raw = query_ollama(prompt)
                elapsed = time.time() - start
                total_time += elapsed

                raw_outputs.append({
                    "id": sent["id"],
                    "raw_response": raw,
                    "time_seconds": elapsed,
                    "attempt": attempt + 1
                })

                parsed = extract_json(raw)
                if parsed is not None:
                    break
                print(f"  [{sent['id']}] Attempt {attempt+1}: JSON parse failed, retrying...")
            except Exception as e:
                print(f"  [{sent['id']}] Attempt {attempt+1}: Error: {e}")
                time.sleep(2)

        if parsed is not None:
            annotations.append({
                "id": sent["id"],
                "source": sent["source"],
                "text": sent["text"],
                "annotations": parsed,
                "time_seconds": elapsed
            })
        else:
            failures.append(sent["id"])
            annotations.append({
                "id": sent["id"],
                "source": sent["source"],
                "text": sent["text"],
                "annotations": [],
                "time_seconds": 0,
                "parse_failure": True
            })

        if (i + 1) % 10 == 0:
            success = sum(1 for a in annotations if not a.get("parse_failure"))
            print(f"  Progress: {i+1}/100 (success: {success}, failures: {len(failures)})")
            # Checkpoint
            with open(output_dir / "raw_qwen7b.json", "w") as f:
                json.dump(raw_outputs, f, ensure_ascii=False, indent=2)
            with open(output_dir / "annotations_qwen7b.json", "w") as f:
                json.dump(annotations, f, ensure_ascii=False, indent=2)

    # Save results
    with open(output_dir / "raw_qwen7b.json", "w") as f:
        json.dump(raw_outputs, f, ensure_ascii=False, indent=2)

    with open(output_dir / "annotations_qwen7b.json", "w") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

    success = sum(1 for a in annotations if not a.get("parse_failure"))
    processed = len(remaining)
    avg_time = total_time / processed if processed > 0 else 0
    print(f"\nDone! {success}/{len(sentences)} successful")
    print(f"Failures: {failures}")
    print(f"Average time per sentence: {avg_time:.2f}s")
    print(f"Total time: {total_time:.1f}s")


if __name__ == "__main__":
    main()
