#!/usr/bin/env python3
"""
Hirogaru Nihongo Scraper

Downloads articles from Hirogaru Nihongo (hirogaru-nihongo.jp) for furigana benchmarking.
Uses requests + BeautifulSoup (no JavaScript rendering required).

The site is organized by categories (music, anime, cafe, etc.) with articles in each.

Usage:
    python hirogaru.py --limit 50 --output data/raw/hirogaru/

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

# Hirogaru URLs
BASE_URL = "https://hirogaru-nihongo.jp"

# Categories to scrape
CATEGORIES = [
    "hoshi",      # Stars/Night sky
    "outdoor",    # Outdoor
    "budo",       # Martial arts
    "cafe",       # Cafe/Tea
    "sweets",     # Sweets
    "market",     # Supermarket/Market
    "shodo",      # Calligraphy
    "anime",      # Anime/Manga
    "book",       # Books/Library
    "tera-jinja", # Temples/Shrines
    "music",      # Music
    "suizokukan", # Aquarium
]

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
    response = requests.get(url, headers=HEADERS, timeout=30, verify=False)
    response.raise_for_status()
    return response.text


def extract_article_links_from_category(html: str, category: str) -> list[dict]:
    """Extract article links from a category page."""
    soup = BeautifulSoup(html, 'lxml')
    articles = []
    seen_slugs = set()

    # Find links matching /category/article/slug/ pattern
    article_pattern = re.compile(rf"/{category}/article/([^/]+)/?$")

    for link in soup.find_all('a', href=True):
        href = link['href']

        match = article_pattern.search(href)
        if not match:
            continue

        slug = match.group(1)

        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)

        # Get title from link text
        title = link.get_text(strip=True)[:200]

        # Build full URL
        if href.startswith('/'):
            full_url = f"{BASE_URL}{href}"
        elif href.startswith('http'):
            full_url = href
        else:
            full_url = f"{BASE_URL}/{category}/article/{slug}/"

        articles.append({
            'article_id': slug,
            'category': category,
            'title': title,
            'url': full_url,
        })

    return articles


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
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Check already downloaded
    downloaded = get_downloaded_ids(output_dir)
    logger.info(f"Found {len(downloaded)} already downloaded")

    all_articles = []
    seen_ids = set()

    # Iterate through categories to collect article links
    for category in CATEGORIES:
        try:
            # Fetch category article listing page
            category_url = f"{BASE_URL}/{category}/category/article/"
            logger.info(f"Fetching category: {category}")
            html = fetch_page(category_url)
            time.sleep(MIN_REQUEST_INTERVAL)

            articles = extract_article_links_from_category(html, category)
            for article in articles:
                if article['article_id'] not in seen_ids:
                    all_articles.append(article)
                    seen_ids.add(article['article_id'])

            logger.info(f"  Found {len(articles)} articles in {category}")

        except Exception as e:
            logger.warning(f"Failed to fetch category {category}: {e}")

    logger.info(f"Total unique articles found: {len(all_articles)}")

    # Filter already downloaded
    to_fetch = [a for a in all_articles if a['article_id'] not in downloaded][:limit]
    logger.info(f"Will download {len(to_fetch)} new articles")

    success = 0
    errors = 0

    for i, article in enumerate(to_fetch):
        try:
            logger.info(f"[{i+1}/{len(to_fetch)}] Fetching {article['article_id']} ({article['category']})")

            # Fetch article page
            html = fetch_page(article['url'])

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
    parser = argparse.ArgumentParser(description="Scrape Hirogaru Nihongo")
    parser.add_argument("--limit", type=int, default=50, help="Maximum articles to download")
    parser.add_argument("--output", type=Path, default=Path("data/raw/hirogaru"), help="Output directory")
    args = parser.parse_args()

    logger.info(f"Starting Hirogaru scraper: limit={args.limit}, output={args.output}")
    scrape_articles(args.limit, args.output)


if __name__ == "__main__":
    main()
