#!/usr/bin/env python3
"""
MATCHA Easy Japanese Parser

Parses HTML from MATCHA Easy Japanese to extract furigana annotations.
Uses standard <ruby> + <rt> tags.

Usage:
    python parse_matcha.py --input data/raw/matcha/ --output data/processed/matcha/
"""

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup

from ruby_parser import extract_ruby_tokens, has_kanji, get_sentence_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def extract_article_content(html: str) -> dict:
    """
    Extract article content and furigana from MATCHA HTML.

    Returns dict with title, date, sentences with tokens.
    """
    soup = BeautifulSoup(html, 'lxml')

    result = {
        'title': '',
        'date': '',
        'sentences': [],
    }

    # Extract title (h1 or h2)
    title_el = soup.find('h1') or soup.find('h2')
    if title_el:
        result['title'] = title_el.get_text(strip=True)

    # Extract date (MATCHA format: "更新日 : 2023.10.31")
    date_text = soup.find(string=re.compile(r'更新日'))
    if date_text:
        date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', str(date_text.parent.get_text()))
        if date_match:
            result['date'] = date_match.group(1).replace('.', '-')

    # Find paragraphs with ruby content
    # MATCHA articles have varied structure, so search broadly
    for p in soup.find_all(['p', 'div', 'span']):
        # Skip if no ruby tags
        if not p.find('ruby'):
            continue

        # Skip very short elements
        text = get_sentence_text(p)
        if not text or len(text) < 10:
            continue

        # Skip if this element is nested inside another with ruby
        # (to avoid duplicate extraction)
        parent_with_ruby = p.find_parent(lambda t: t.find('ruby') and t != p)
        if parent_with_ruby and parent_with_ruby.name in ['p', 'div']:
            continue

        tokens = extract_ruby_tokens(p)

        if tokens:
            result['sentences'].append({
                'text': text,
                'tokens': tokens,
            })

    # Deduplicate sentences (same text may appear multiple times)
    seen_texts = set()
    unique_sentences = []
    for sentence in result['sentences']:
        if sentence['text'] not in seen_texts:
            seen_texts.add(sentence['text'])
            unique_sentences.append(sentence)
    result['sentences'] = unique_sentences

    return result


def parse_article(html_path: Path, metadata_path: Path) -> Optional[dict]:
    """Parse a single article."""
    try:
        html = html_path.read_text(encoding='utf-8')
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))

        content = extract_article_content(html)

        return {
            'source': 'matcha',
            'article_id': metadata.get('article_id', ''),
            'url': metadata.get('url', ''),
            'title': content['title'] or metadata.get('title', ''),
            'date': content['date'] or metadata.get('date', ''),
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
    total_sentences = 0

    for article_dir in sorted(input_dir.iterdir()):
        if not article_dir.is_dir():
            continue

        html_path = article_dir / 'article.html'
        metadata_path = article_dir / 'metadata.json'

        if not html_path.exists() or not metadata_path.exists():
            continue

        article = parse_article(html_path, metadata_path)
        if article and article['sentences']:
            output_path = output_dir / f"{article_dir.name}.json"
            output_path.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            success += 1
            total_sentences += len(article['sentences'])
            logger.info(f"Parsed: {article_dir.name} ({len(article['sentences'])} sentences)")
        else:
            errors += 1
            logger.warning(f"No content: {article_dir.name}")

    logger.info(f"Done: {success} parsed, {errors} errors, {total_sentences} total sentences")
    return success


def show_examples(output_dir: Path, num_examples: int = 5):
    """Show example parsed sentences with tokens."""
    print("\n" + "=" * 60)
    print("EXAMPLE SENTENCES WITH FURIGANA TOKENS (MATCHA)")
    print("=" * 60 + "\n")

    files = sorted(output_dir.glob("*.json"))[:10]
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

            print(f"Source: matcha/{data.get('article_id', 'unknown')}")
            text_preview = sentence['text'][:80] + ('...' if len(sentence['text']) > 80 else '')
            print(f"Text: {text_preview}")
            print("Tokens:")
            for token in tokens[:8]:
                print(f"  - {token['surface']} -> {token['reading']}")
            print()
            examples_shown += 1

    if examples_shown == 0:
        print("No sentences with furigana tokens found.")


def main():
    parser = argparse.ArgumentParser(description="Parse MATCHA Easy Japanese HTML")
    parser.add_argument("--input", type=Path, default=Path("data/raw/matcha"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/matcha"))
    parser.add_argument("--examples", type=int, default=5)
    args = parser.parse_args()

    logger.info(f"Parsing MATCHA articles from {args.input}")
    count = parse_all_articles(args.input, args.output)

    if count > 0:
        show_examples(args.output, args.examples)


if __name__ == "__main__":
    main()
