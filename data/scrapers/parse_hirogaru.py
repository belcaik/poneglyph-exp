#!/usr/bin/env python3
"""
Hirogaru Nihongo Parser

Parses HTML from Hirogaru Nihongo to extract furigana annotations.
Uses standard <ruby> + <rt> tags.

Content is organized as Q&A format articles about Japanese culture.

Usage:
    python parse_hirogaru.py --input data/raw/hirogaru/ --output data/processed/hirogaru/
"""

import argparse
import json
import logging
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
    Extract article content and furigana from Hirogaru HTML.

    Hirogaru structure:
    - Title in h2 heading
    - Content in p and dd elements (Q&A format with audio definitions)
    - Ruby toggle exists but ruby tags are always in DOM
    """
    soup = BeautifulSoup(html, 'lxml')

    result = {
        'title': '',
        'date': '',
        'sentences': [],
    }

    # Extract title (h2 in the main content area)
    # Skip the site title "ひろがる" which is in h1
    title_el = soup.find('h2')
    if title_el:
        result['title'] = get_sentence_text(title_el)

    # Hirogaru doesn't show article dates prominently
    # Leave date empty

    # Find elements with ruby content
    # Content is in paragraphs (questions) and dd elements (answers/audio transcripts)
    for el in soup.find_all(['p', 'dd', 'figcaption']):
        # Skip elements without ruby
        if not el.find('ruby'):
            continue

        text = get_sentence_text(el)
        if not text or len(text) < 10:
            continue

        # Skip UI/navigation elements
        if any(skip in text for skip in ['Copyright', 'RUBY', 'JAPANESE', 'ENGLISH']):
            continue

        tokens = extract_ruby_tokens(el)

        if tokens:
            result['sentences'].append({
                'text': text,
                'tokens': tokens,
            })

    # Also check for content in specific content divs
    # Hirogaru uses various containers for article content
    content_containers = soup.find_all('div', class_=lambda x: x and ('content' in x.lower() or 'article' in x.lower()))
    for container in content_containers:
        for el in container.find_all(['p', 'dd', 'span']):
            if not el.find('ruby'):
                continue

            text = get_sentence_text(el)
            if not text or len(text) < 10:
                continue

            # Check if already added
            existing_texts = {s['text'] for s in result['sentences']}
            if text in existing_texts:
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
        text_key = sentence['text'][:100]
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
            'source': 'hirogaru',
            'article_id': metadata.get('article_id', ''),
            'category': metadata.get('category', ''),
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
    print("EXAMPLE SENTENCES WITH FURIGANA TOKENS (HIROGARU)")
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

            print(f"Source: hirogaru/{data.get('article_id', 'unknown')} ({data.get('category', '')})")
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
    parser = argparse.ArgumentParser(description="Parse Hirogaru Nihongo HTML")
    parser.add_argument("--input", type=Path, default=Path("data/raw/hirogaru"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/hirogaru"))
    parser.add_argument("--examples", type=int, default=5)
    args = parser.parse_args()

    logger.info(f"Parsing Hirogaru articles from {args.input}")
    count = parse_all_articles(args.input, args.output)

    if count > 0:
        show_examples(args.output, args.examples)


if __name__ == "__main__":
    main()
