#!/usr/bin/env python3
"""Annotate filtered sentences with Gemini Flash via CLI.

Processes in batches of 10 sentences. Saves checkpoints every 10 batches.
Supports resume from partial results.
"""

import json
import re
import subprocess
import time
from pathlib import Path

BATCH_SIZE = 10
TIMEOUT = 180  # 3 min per batch
MAX_RETRIES = 3

PROMPT_TEMPLATE = """You are a Japanese furigana annotation system. Follow these rules EXACTLY:

CRITICAL: Every word containing kanji (U+4E00-U+9FFF) MUST be annotated. Missing any kanji is an error. After annotating, scan the text to verify 100% kanji coverage.

CONVENTIONS:
1. COMPOUND NOUNS as single unit: 幼稚園→ようちえん, 東京都→とうきょうと
2. VERB CHAINS include ALL auxiliaries: 食べている→たべている, 書かれていました→かかれていました
3. ADJECTIVES complete form: 大きくなった→おおきくなった
4. PROPER NOUNS always annotated, type="proper_noun": 田中→たなか
5. NUMBERS+COUNTERS as unit: 2人→ふたり, 3時間→さんじかん
6. MIXED kanji+hiragana words: 子ども→こども, お母さん→おかあさん
7. DO NOT annotate: pure hiragana, pure katakana, standalone particles, punctuation

EXAMPLES:
Input: "田中さんは毎日3時間勉強しています。"
Output: {{"1":[{{"surface":"田中","reading":"たなか","type":"proper_noun"}},{{"surface":"毎日","reading":"まいにち","type":"noun"}},{{"surface":"3時間","reading":"さんじかん","type":"counter"}},{{"surface":"勉強しています","reading":"べんきょうしています","type":"verb"}}]}}

Annotate each sentence below. Return a JSON object mapping sentence IDs to annotation arrays. ONLY JSON, no other text.

{sentences_block}"""


def query_gemini(prompt):
    """Call gemini CLI via stdin."""
    try:
        result = subprocess.run(
            ["gemini"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )
        if result.returncode == 0:
            return result.stdout
        # Try -p flag
        result = subprocess.run(
            ["gemini", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )
        return result.stdout if result.returncode == 0 else f"ERROR: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "ERROR: timeout"
    except FileNotFoundError:
        return "ERROR: gemini CLI not found"
    except Exception as e:
        return f"ERROR: {e}"


def extract_json(text):
    """Extract JSON object from response."""
    text = text.strip()
    # Remove markdown fences
    text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()

    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Try to find JSON object
    brace_start = text.find('{')
    if brace_start >= 0:
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[brace_start:i+1])
                    except json.JSONDecodeError:
                        break
    return None


def is_kanji(c):
    cp = ord(c)
    return 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF


def check_kanji_coverage(text, annotations):
    """Check what % of kanji in text are covered by annotations."""
    kanji_positions = {i for i, c in enumerate(text) if is_kanji(c)}
    if not kanji_positions:
        return 100.0

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
            span = set(range(idx, idx + len(surface)))
            if not span & used:
                covered |= span
                used |= span
                break
            pos = idx + 1

    return len(kanji_positions & covered) / len(kanji_positions) * 100


def main():
    data_dir = Path("data/dataset_gen")
    output_path = data_dir / "annotations_gemini.json"
    raw_path = data_dir / "raw_gemini.json"

    with open(data_dir / "filtered_sentences.json") as f:
        sentences = json.load(f)

    # Resume support
    annotations = {}
    raw_outputs = []
    if output_path.exists():
        try:
            with open(output_path) as f:
                existing = json.load(f)
            annotations = {a["id"]: a for a in existing if not a.get("parse_failure")}
            print(f"Resuming: {len(annotations)} existing annotations")
        except Exception:
            pass

    if raw_path.exists():
        try:
            with open(raw_path) as f:
                raw_outputs = json.load(f)
        except Exception:
            pass

    # Check gemini CLI
    try:
        result = subprocess.run(["gemini", "--version"], capture_output=True, text=True, timeout=10)
        print(f"Gemini CLI: {result.stdout.strip()}")
    except Exception as e:
        print(f"ERROR: gemini CLI not available: {e}")
        return

    # Filter to remaining sentences
    remaining = [s for s in sentences if s["id"] not in annotations]
    print(f"Processing {len(remaining)} remaining sentences...")

    # Process in batches
    batches = [remaining[i:i+BATCH_SIZE] for i in range(0, len(remaining), BATCH_SIZE)]
    total_time = 0
    processed = 0

    for batch_idx, batch in enumerate(batches):
        sentences_block = "\n".join(
            f'Sentence {s["id"]}: "{s["text"]}"' for s in batch
        )
        prompt = PROMPT_TEMPLATE.format(sentences_block=sentences_block)

        parsed = None
        for attempt in range(MAX_RETRIES):
            start = time.time()
            raw = query_gemini(prompt)
            elapsed = time.time() - start
            total_time += elapsed

            raw_outputs.append({
                "batch": batch_idx,
                "ids": [s["id"] for s in batch],
                "time_seconds": elapsed,
                "attempt": attempt + 1,
            })

            if raw.startswith("ERROR:"):
                print(f"  Batch {batch_idx} attempt {attempt+1}: {raw[:100]}")
                time.sleep(2)
                continue

            parsed = extract_json(raw)
            if parsed:
                break
            print(f"  Batch {batch_idx} attempt {attempt+1}: JSON parse failed")

        # Process results
        for sent in batch:
            sid = str(sent["id"])
            annots = None
            if parsed:
                annots = parsed.get(sid) or parsed.get(str(sent["id"]))

            if annots and isinstance(annots, list):
                coverage = check_kanji_coverage(sent["text"], annots)
                annotations[sent["id"]] = {
                    "id": sent["id"],
                    "series": sent["series"],
                    "text": sent["text"],
                    "annotations": annots,
                    "kanji_coverage": coverage,
                }
            else:
                annotations[sent["id"]] = {
                    "id": sent["id"],
                    "series": sent["series"],
                    "text": sent["text"],
                    "annotations": [],
                    "parse_failure": True,
                }

        processed += len(batch)

        if (batch_idx + 1) % 10 == 0 or batch_idx == len(batches) - 1:
            success = sum(1 for a in annotations.values() if not a.get("parse_failure"))
            avg = total_time / processed if processed > 0 else 0
            print(f"  Progress: {processed}/{len(remaining)} "
                  f"(success: {success}, avg: {avg:.1f}s/sent)")
            # Checkpoint
            annot_list = sorted(annotations.values(), key=lambda a: a["id"])
            with open(output_path, "w") as f:
                json.dump(annot_list, f, ensure_ascii=False, indent=2)
            with open(raw_path, "w") as f:
                json.dump(raw_outputs, f, ensure_ascii=False, indent=2)

    # Final save
    annot_list = sorted(annotations.values(), key=lambda a: a["id"])
    with open(output_path, "w") as f:
        json.dump(annot_list, f, ensure_ascii=False, indent=2)

    success = sum(1 for a in annot_list if not a.get("parse_failure"))
    print(f"\nDone! {success}/{len(sentences)} successful")
    print(f"Total time: {total_time:.0f}s ({total_time/60:.1f} min)")


if __name__ == "__main__":
    main()
