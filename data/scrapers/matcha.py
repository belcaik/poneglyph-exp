#!/usr/bin/env python3
"""
MATCHA Easy Japanese Scraper

Downloads articles from MATCHA Easy Japanese (matcha-jp.com/easy) for furigana benchmarking.
Uses requests + BeautifulSoup (no JavaScript rendering required).

Usage:
    python matcha.py --limit 50 --output data/raw/matcha/

Requirements:
    pip install requests beautifulsoup4 lxml
"""

import argparse
import json
import logging
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# MATCHA Easy URLs
BASE_URL = "https://matcha-jp.com/easy"
ARTICLE_URL_PATTERN = re.compile(r"/easy/(\d+)$")

# Rate limiting
MIN_REQUEST_INTERVAL = 1.5  # seconds between requests

# Headers to avoid being blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
}


def fetch_page(url: str) -> str:
    """Fetch a page with rate limiting and error handling."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def extract_article_links(html: str, base_url: str = BASE_URL) -> list[dict]:
    """Extract article links from the listing page."""
    soup = BeautifulSoup(html, 'lxml')
    articles = []
    seen_ids = set()

    for link in soup.find_all('a', href=True):
        href = link['href']

        # Match article URLs like /easy/12673
        match = ARTICLE_URL_PATTERN.search(href)
        if not match:
            continue

        article_id = match.group(1)

        if article_id in seen_ids:
            continue
        seen_ids.add(article_id)

        # Get title from link text
        title = link.get_text(strip=True)[:200]

        # Build full URL
        if href.startswith('/'):
            full_url = f"https://matcha-jp.com{href}"
        elif href.startswith('http'):
            full_url = href
        else:
            full_url = f"{base_url}/{article_id}"

        articles.append({
            'article_id': article_id,
            'title': title,
            'url': full_url,
        })

    logger.info(f"Found {len(articles)} unique article links")
    return articles


def extract_article_metadata(html: str, article_id: str) -> dict:
    """Extract metadata from an article page."""
    soup = BeautifulSoup(html, 'lxml')

    metadata = {
        'article_id': article_id,
        'title': '',
        'date': '',
    }

    # Try to find title
    title_el = soup.find('h1') or soup.find('h2')
    if title_el:
        metadata['title'] = title_el.get_text(strip=True)

    # Try to find date (MATCHA uses format like "更新日 : 2023.10.31")
    date_el = soup.find(string=re.compile(r'更新日'))
    if date_el:
        date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', str(date_el.parent.get_text()))
        if date_match:
            metadata['date'] = date_match.group(1).replace('.', '-')

    # Also check for time element
    time_el = soup.find('time')
    if time_el and not metadata['date']:
        metadata['date'] = time_el.get_text(strip=True)

    return metadata


def save_article(article: dict, html: str, output_dir: Path) -> None:
    """Save article HTML and metadata to disk."""
    article_dir = output_dir / article['article_id']
    article_dir.mkdir(parents=True, exist_ok=True)

    (article_dir / "article.html").write_text(html, encoding="utf-8")
    (article_dir / "metadata.json").write_text(
        json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_downloaded_ids(output_dir: Path) -> set:
    """Get set of already downloaded article IDs."""
    downloaded = set()
    if output_dir.exists():
        for d in output_dir.iterdir():
            if d.is_dir() and (d / "article.html").exists():
                downloaded.add(d.name)
    return downloaded


def scrape_articles(limit: int, output_dir: Path) -> int:
    """Main scraper function."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check already downloaded
    downloaded = get_downloaded_ids(output_dir)
    logger.info(f"Found {len(downloaded)} already downloaded")

    # Fetch main listing page
    logger.info(f"Fetching listing page: {BASE_URL}")
    listing_html = fetch_page(BASE_URL)
    time.sleep(MIN_REQUEST_INTERVAL)

    # Extract article links
    all_articles = extract_article_links(listing_html)

    # Try to get more articles from category/region pages if needed
    if len(all_articles) < limit:
        additional_pages = [
            f"{BASE_URL}/list/region",
            f"{BASE_URL}/list?region=113",  # Tokyo
            f"{BASE_URL}/list?region=126",  # Kyoto
        ]
        for page_url in additional_pages:
            try:
                logger.info(f"Fetching additional page: {page_url}")
                extra_html = fetch_page(page_url)
                extra_articles = extract_article_links(extra_html)

                # Add new articles
                existing_ids = {a['article_id'] for a in all_articles}
                for article in extra_articles:
                    if article['article_id'] not in existing_ids:
                        all_articles.append(article)
                        existing_ids.add(article['article_id'])

                time.sleep(MIN_REQUEST_INTERVAL)
            except Exception as e:
                logger.warning(f"Failed to fetch {page_url}: {e}")

    # Filter already downloaded
    to_fetch = [a for a in all_articles if a['article_id'] not in downloaded][:limit]
    logger.info(f"Will download {len(to_fetch)} new articles")

    success = 0
    errors = 0

    for i, article in enumerate(to_fetch):
        try:
            logger.info(f"[{i+1}/{len(to_fetch)}] Fetching {article['article_id']}")

            # Fetch article page
            html = fetch_page(article['url'])

            # Extract metadata from page
            metadata = extract_article_metadata(html, article['article_id'])
            article.update(metadata)

            # Save to disk
            save_article(article, html, output_dir)
            success += 1

        except Exception as e:
            errors += 1
            logger.error(f"Failed {article['article_id']}: {e}")

        time.sleep(MIN_REQUEST_INTERVAL)

    total = len(downloaded) + success
    logger.info(f"Done: {success} new, {errors} errors, {total} total")
    return success


def main():
    parser = argparse.ArgumentParser(description="Scrape MATCHA Easy Japanese")
    parser.add_argument("--limit", type=int, default=50, help="Maximum articles to download")
    parser.add_argument("--output", type=Path, default=Path("data/raw/matcha"), help="Output directory")
    args = parser.parse_args()

    logger.info(f"Starting MATCHA scraper: limit={args.limit}, output={args.output}")
    scrape_articles(args.limit, args.output)


if __name__ == "__main__":
    main()
