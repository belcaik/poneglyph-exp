#!/usr/bin/env python3
"""
Kahoku Easy Japanese Parser

Parses HTML from Kahoku Easy Japanese to extract furigana annotations.
Uses standard <ruby> + <rt> tags (rendered by Playwright).

Usage:
    python parse_kahoku.py --input data/raw/kahoku/ --output data/processed/kahoku/
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
    Extract article content and furigana from Kahoku HTML.

    Kahoku structure:
    - Title in h2.kiji-title
    - Content in div.kiji-text elements (each div is a paragraph)
    - Ruby tags use <rp> for fallback parentheses
    """
    soup = BeautifulSoup(html, 'lxml')

    result = {
        'title': '',
        'date': '',
        'sentences': [],
    }

    # Extract title (h2 with kiji-title class)
    title_el = soup.find('h2', class_='kiji-title')
    if not title_el:
        title_el = soup.find('h2', class_='news-title') or soup.find('h3') or soup.find('h2')
    if title_el:
        result['title'] = get_sentence_text(title_el)

    # Extract date from article metadata or page
    # Look for date pattern in the page
    page_text = soup.get_text()
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}:\d{2}', page_text)
    if date_match:
        result['date'] = date_match.group(1)

    # Find main content area
    article = soup.find('article')
    if not article:
        article = soup.find('main') or soup

    # Extract content from div.kiji-text elements (Kahoku's specific structure)
    kiji_texts = article.find_all('div', class_='kiji-text')
    for div in kiji_texts:
        text = get_sentence_text(div)
        if not text or len(text) < 10:
            continue

        tokens = extract_ruby_tokens(div)

        if tokens:
            result['sentences'].append({
                'text': text,
                'tokens': tokens,
            })

    # Also check for any other content containers with ruby
    if not result['sentences']:
        # Fallback: look for any element with ruby tags in article
        for el in article.find_all(['p', 'div', 'dd']):
            if not el.find('ruby'):
                continue

            text = get_sentence_text(el)
            if not text or len(text) < 10:
                continue

            # Skip navigation/UI elements
            if re.match(r'^(漢字の読み方|ニュースを聞く|普通のニュースを読む)', text):
                continue

            tokens = extract_ruby_tokens(el)

            if tokens:
                result['sentences'].append({
                    'text': text,
                    'tokens': tokens,
                })

    # Deduplicate sentences
    seen_texts = set()
    unique_sentences = []
    for sentence in result['sentences']:
        text_key = sentence['text'][:100]  # Use first 100 chars as key
        if text_key not in seen_texts:
            seen_texts.add(text_key)
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
            'source': 'kahoku',
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
    print("EXAMPLE SENTENCES WITH FURIGANA TOKENS (KAHOKU)")
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

            print(f"Source: kahoku/{data.get('article_id', 'unknown')}")
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
    parser = argparse.ArgumentParser(description="Parse Kahoku Easy Japanese HTML")
    parser.add_argument("--input", type=Path, default=Path("data/raw/kahoku"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/kahoku"))
    parser.add_argument("--examples", type=int, default=5)
    args = parser.parse_args()

    logger.info(f"Parsing Kahoku articles from {args.input}")
    count = parse_all_articles(args.input, args.output)

    if count > 0:
        show_examples(args.output, args.examples)


if __name__ == "__main__":
    main()
