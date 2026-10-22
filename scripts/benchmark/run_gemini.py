#!/usr/bin/env python3
"""Step 3c: Run Gemini Flash via CLI on benchmark sentences."""

import json
import re
import subprocess
import time
from pathlib import Path


MAX_RETRIES = 3


def load_prompt_template():
    with open("data/benchmark/prompt_template.txt") as f:
        return f.read()


def query_gemini(prompt):
    """Query Gemini via CLI."""
    result = subprocess.run(
        ["gemini", "-p", prompt],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        raise RuntimeError(f"gemini CLI error: {result.stderr}")
    return result.stdout


def extract_json(text):
    """Extract JSON array from LLM response."""
    text = text.strip()

    # Remove markdown code fences
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()

    # Try direct parse
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try to find JSON array
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

    # Resume support: check for existing partial results
    existing_annotations = []
    existing_raw = []
    existing_ids = set()
    partial_path = output_dir / "annotations_gemini.json"
    if partial_path.exists():
        try:
            with open(partial_path) as f:
                existing_annotations = json.load(f)
            existing_ids = {a["id"] for a in existing_annotations if not a.get("parse_failure")}
            print(f"Resuming: found {len(existing_ids)} existing successful annotations")
        except Exception:
            pass

    raw_path = output_dir / "raw_gemini.json"
    if raw_path.exists():
        try:
            with open(raw_path) as f:
                existing_raw = json.load(f)
        except Exception:
            pass

    # Check gemini CLI
    try:
        result = subprocess.run(["gemini", "--version"], capture_output=True, text=True, timeout=10)
        print(f"Gemini CLI: {result.stdout.strip()}")
    except FileNotFoundError:
        print("ERROR: gemini CLI not found. Install it first.")
        return
    except Exception as e:
        print(f"Gemini CLI check: {e}")

    annotations = list(existing_annotations)
    raw_outputs = list(existing_raw)
    failures = []
    total_time = 0
    processed = 0

    remaining = [s for s in sentences if s["id"] not in existing_ids]
    print(f"\nProcessing {len(remaining)} remaining sentences with Gemini Flash...")

    for i, sent in enumerate(remaining):
        prompt = prompt_template.replace("{text}", sent["text"])
        parsed = None
        elapsed = 0

        for attempt in range(MAX_RETRIES):
            try:
                start = time.time()
                raw = query_gemini(prompt)
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
            except subprocess.TimeoutExpired:
                print(f"  [{sent['id']}] Attempt {attempt+1}: Timeout (300s)")
            except Exception as e:
                print(f"  [{sent['id']}] Attempt {attempt+1}: Error: {e}")
                time.sleep(1)

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

        processed += 1
        if processed % 10 == 0:
            success = sum(1 for a in annotations if not a.get("parse_failure"))
            print(f"  Progress: {processed}/{len(remaining)} (total success: {success})")
            # Save checkpoint
            with open(output_dir / "raw_gemini.json", "w") as f:
                json.dump(raw_outputs, f, ensure_ascii=False, indent=2)
            with open(output_dir / "annotations_gemini.json", "w") as f:
                json.dump(annotations, f, ensure_ascii=False, indent=2)

    # Final save
    with open(output_dir / "raw_gemini.json", "w") as f:
        json.dump(raw_outputs, f, ensure_ascii=False, indent=2)

    with open(output_dir / "annotations_gemini.json", "w") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

    success = sum(1 for a in annotations if not a.get("parse_failure"))
    avg_time = total_time / processed if processed > 0 else 0
    print(f"\nDone! {success}/{len(sentences)} successful")
    print(f"Failures: {failures}")
    print(f"Average time per sentence: {avg_time:.2f}s")
    print(f"Total time: {total_time:.1f}s")


if __name__ == "__main__":
    main()
