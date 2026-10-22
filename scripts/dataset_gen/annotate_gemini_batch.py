#!/usr/bin/env python3
"""Annotate a specific batch of sentences with Gemini CLI.

Optimized: 5 sentences per CLI call instead of 10.
Usage: python annotate_gemini_batch.py <input_file> <output_file>
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

BATCH_SIZE = 5  # Sentences per CLI call
TIMEOUT = 180
MAX_RETRIES = 2

PROMPT_TEMPLATE = """You are a Japanese furigana annotation system. CRITICAL: Annotate EVERY kanji-containing word. Return ONLY JSON.

RULES: Compound nouns as single unit. Verb chains include ALL auxiliaries. Proper nouns type="proper_noun". Counters as unit. Mixed kanji+hiragana included. DO NOT annotate pure hiragana/katakana/particles.

Return JSON object mapping sentence IDs to arrays: {{"ID":[{{"surface":"X","reading":"x","type":"Y"}}]}}

{sentences_block}"""


def query_gemini(prompt):
    try:
        result = subprocess.run(
            ["gemini"], input=prompt,
            capture_output=True, text=True, timeout=TIMEOUT
        )
        return result.stdout if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, Exception):
        return ""


def extract_json(text):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    brace_start = text.find('{')
    if brace_start >= 0:
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == '{': depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try: return json.loads(text[brace_start:i+1])
                    except json.JSONDecodeError: break
    return None


def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else "/tmp/dataset_v2_gemini_500.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "data/dataset_gen/annotations_gemini_v2.json"

    with open(input_file) as f:
        sentences = json.load(f)

    # Resume support
    annotations = {}
    output_path = Path(output_file)
    if output_path.exists():
        try:
            with open(output_path) as f:
                for a in json.load(f):
                    if not a.get("parse_failure"):
                        annotations[a["text"]] = a
        except Exception:
            pass

    remaining = [s for s in sentences if s["text"] not in annotations]
    print(f"Total: {len(sentences)}, Already done: {len(annotations)}, Remaining: {len(remaining)}")

    batches = [remaining[i:i+BATCH_SIZE] for i in range(0, len(remaining), BATCH_SIZE)]
    total_time = 0
    processed = 0

    for batch_idx, batch in enumerate(batches):
        sentences_block = "\n".join(f'Sentence {s["id"]}: "{s["text"]}"' for s in batch)
        prompt = PROMPT_TEMPLATE.format(sentences_block=sentences_block)

        parsed = None
        for attempt in range(MAX_RETRIES):
            start = time.time()
            raw = query_gemini(prompt)
            elapsed = time.time() - start
            total_time += elapsed

            if raw:
                parsed = extract_json(raw)
                if parsed:
                    break

        for sent in batch:
            sid = str(sent["id"])
            annots = parsed.get(sid) if parsed else None
            if annots and isinstance(annots, list):
                annotations[sent["text"]] = {
                    "id": sent["id"], "series": sent["series"],
                    "text": sent["text"], "annotations": annots,
                }
            else:
                annotations[sent["text"]] = {
                    "id": sent["id"], "series": sent["series"],
                    "text": sent["text"], "annotations": [], "parse_failure": True,
                }

        processed += len(batch)
        if (batch_idx + 1) % 20 == 0 or batch_idx == len(batches) - 1:
            success = sum(1 for a in annotations.values() if not a.get("parse_failure"))
            print(f"  {processed}/{len(remaining)} ({success} success, {total_time:.0f}s)")
            annot_list = sorted(annotations.values(), key=lambda a: a.get("id", 0))
            with open(output_path, "w") as f:
                json.dump(annot_list, f, ensure_ascii=False, indent=2)

    annot_list = sorted(annotations.values(), key=lambda a: a.get("id", 0))
    with open(output_path, "w") as f:
        json.dump(annot_list, f, ensure_ascii=False, indent=2)

    success = sum(1 for a in annot_list if not a.get("parse_failure"))
    print(f"\nDone! {success}/{len(sentences)} successful ({total_time:.0f}s)")


if __name__ == "__main__":
    main()
