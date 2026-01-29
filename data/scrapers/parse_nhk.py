#!/usr/bin/env python3
"""
NHK Easy News Parser

Parses rendered HTML from Playwright to extract furigana annotations.
NHK Easy News uses nested divs for furigana (not standard <ruby> tags).

Pattern:
  <div class="...">
    日本語  <-- kanji text (first text node)
    <div class="...">にほんご</div>  <-- reading (nested div)
  </div>

Usage:
    python parse_nhk.py --input ../raw/ --output ../processed/
"""

import argparse
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, NavigableString

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def extract_furigana_tokens(element) -> list[dict]:
    """
    Extract furigana tokens from an element.

    NHK uses a structure like:
    <span/div>
      kanji_text
      <span/div class="ruby">reading</span>
    </span/div>

    Returns list of dicts with {surface, reading, ...}
    """
    tokens = []

    # Find all elements that have a direct text child and a nested div/span with reading
    for parent in element.find_all(True):  # True = any tag
        children = list(parent.children)

        # Look for pattern: text + nested element with reading
        text_parts = []
        reading = None

        for child in children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    text_parts.append(text)
            elif child.name in ('div', 'span') and not child.find(True):
                # Leaf element - potential reading
                reading_text = child.get_text(strip=True)
                if reading_text and is_hiragana(reading_text):
                    reading = reading_text

        # If we have kanji text and a hiragana reading, it's a furigana annotation
        if text_parts and reading:
            surface = ''.join(text_parts)
            # Only if surface contains kanji
            if has_kanji(surface):
                tokens.append({
                    'surface': surface,
                    'reading': reading,
                })

    return tokens


def is_hiragana(text: str) -> bool:
    """Check if text is primarily hiragana."""
    hiragana_count = sum(1 for c in text if '\u3040' <= c <= '\u309f')
    return hiragana_count > len(text) * 0.5


def has_kanji(text: str) -> bool:
    """Check if text contains any kanji."""
    return any('\u4e00' <= c <= '\u9fff' for c in text)


def extract_article_content(html: str) -> dict:
    """
    Extract article content and furigana from HTML.

    Returns dict with title, date, paragraphs with tokens.
    """
    soup = BeautifulSoup(html, 'lxml')

    # Find the article element
    article = soup.find('article')
    if not article:
        logger.warning("No article element found")
        return None

    result = {
        'title': '',
        'date': '',
        'sentences': [],
    }

    # Extract title (h1 or h2)
    title_el = article.find(['h1', 'h2'])
    if title_el:
        result['title'] = title_el.get_text(strip=True)

    # Extract date
    time_el = article.find('time')
    if time_el:
        result['date'] = time_el.get_text(strip=True)

    # Find the main content area
    # In NHK Easy, the article body is usually in paragraphs
    paragraphs = article.find_all('p')

    for p in paragraphs:
        text = p.get_text(strip=True)
        if not text or len(text) < 5:
            continue

        # Extract tokens with furigana from this paragraph
        tokens = extract_tokens_from_paragraph(p)

        if tokens or has_kanji(text):
            result['sentences'].append({
                'text': text,
                'tokens': tokens,
            })

    return result


def extract_tokens_from_paragraph(p) -> list[dict]:
    """
    Extract furigana tokens from a paragraph element.

    NHK Easy HTML structure uses standard <ruby> and <rt> tags:
    <ruby>
      漢字
      <rt>かんじ</rt>
    </ruby>
    """
    tokens = []

    # Find all ruby elements
    ruby_elements = p.find_all('ruby')

    for ruby in ruby_elements:
        # Get the kanji text (direct text content before <rt>)
        surface = ''
        reading = ''

        for child in ruby.children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    surface += text
            elif child.name == 'rt':
                reading = child.get_text(strip=True)

        if surface and reading:
            tokens.append({
                'surface': surface,
                'reading': reading,
            })

    return tokens


def parse_article(html_path: Path, metadata_path: Path) -> Optional[dict]:
    """Parse a single article."""
    try:
        html = html_path.read_text(encoding='utf-8')
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))

        content = extract_article_content(html)
        if not content:
            return None

        return {
            'source': 'nhk_easy',
            'news_id': metadata.get('news_id', ''),
            'url': metadata.get('url', ''),
            'title': content['title'],
            'date': content['date'],
            'sentences': content['sentences'],
        }
    except Exception as e:
        logger.error(f"Error parsing {html_path}: {e}")
        return None


def parse_all_articles(input_dir: Path, output_dir: Path) -> int:
    """Parse all articles in input directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    errors = 0

    for article_dir in sorted(input_dir.iterdir()):
        if not article_dir.is_dir():
            continue

        html_path = article_dir / 'article.html'
        metadata_path = article_dir / 'metadata.json'

        if not html_path.exists() or not metadata_path.exists():
            continue

        article = parse_article(html_path, metadata_path)
        if article:
            output_path = output_dir / f"{article_dir.name}.json"
            output_path.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            success += 1
            logger.info(f"Parsed: {article_dir.name} ({len(article['sentences'])} sentences)")
        else:
            errors += 1

    logger.info(f"Done: {success} parsed, {errors} errors")
    return success


def show_examples(output_dir: Path, num_examples: int = 3):
    """Show example parsed sentences with tokens."""
    print("\n" + "=" * 60)
    print("EXAMPLE SENTENCES WITH FURIGANA TOKENS")
    print("=" * 60 + "\n")

    files = sorted(output_dir.glob("*.json"))[:5]  # Check first 5 files
    examples_shown = 0

    for file_path in files:
        if examples_shown >= num_examples:
            break

        data = json.loads(file_path.read_text(encoding='utf-8'))

        for sentence in data.get('sentences', []):
            if examples_shown >= num_examples:
                break

            tokens = sentence.get('tokens', [])
            if not tokens:
                continue

            print(f"Source: {data.get('news_id', 'unknown')}")
            print(f"Text: {sentence['text'][:100]}...")
            print("Tokens:")
            for token in tokens[:5]:  # Show first 5 tokens
                print(f"  - {token['surface']} → {token['reading']}")
            print()
            examples_shown += 1

    if examples_shown == 0:
        print("No sentences with furigana tokens found.")
        print("This may indicate a parsing issue.")


def main():
    parser = argparse.ArgumentParser(description="Parse NHK Easy News HTML")
    parser.add_argument("--input", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    parser.add_argument("--examples", type=int, default=3)
    args = parser.parse_args()

    logger.info(f"Parsing articles from {args.input}")
    count = parse_all_articles(args.input, args.output)

    if count > 0:
        show_examples(args.output, args.examples)


if __name__ == "__main__":
    main()
