#!/usr/bin/env python3
"""
Kahoku Easy Japanese Scraper

Downloads articles from Kahoku Easy Japanese (kahoku.news/easyjapanese) for furigana benchmarking.
Uses Playwright because the raw HTML serves parenthetical furigana, but rendered DOM has ruby tags.

Usage:
    python kahoku.py --limit 50 --output data/raw/kahoku/

Requirements:
    pip install playwright
    playwright install chromium
"""

import argparse
import json
import logging
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, Page

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

# Kahoku Easy URLs
BASE_URL = "https://kahoku.news/easyjapanese/"
ARTICLE_URL_PATTERN = re.compile(r"articles/([0-9a-zA-Z]+)\.html$")

# Rate limiting
MIN_REQUEST_INTERVAL = 2.0  # seconds between requests (slightly more conservative)

# Browser state storage
STATE_DIR = Path("data/scrapers/.browser_state")


def extract_article_links(page: Page) -> list[dict]:
    """Extract article links from the current page."""
    articles = []
    seen_ids = set()

    links = page.query_selector_all("a[href*='articles/']")

    for link in links:
        try:
            href = link.get_attribute("href")
            if not href:
                continue

            match = ARTICLE_URL_PATTERN.search(href)
            if not match:
                continue

            article_id = match.group(1)

            if article_id in seen_ids:
                continue
            seen_ids.add(article_id)

            # Get title from link text
            title = link.inner_text()[:200].strip()

            # Build full URL
            if href.startswith('/'):
                full_url = f"https://kahoku.news{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = f"{BASE_URL}{href}"

            articles.append({
                'article_id': article_id,
                'title': title,
                'url': full_url,
            })
        except Exception:
            continue

    logger.info(f"Found {len(articles)} unique article links")
    return articles


def fetch_article_html(page: Page, url: str) -> str:
    """Fetch rendered HTML of an article page."""
    page.goto(url, timeout=60000)
    try:
        # Wait for main content to load
        page.wait_for_selector("main", timeout=30000)
        time.sleep(2)  # Allow ruby tags to render
    except Exception:
        logger.warning(f"Article not fully loaded: {url}")
    return page.content()


def extract_date_from_page(page: Page) -> str:
    """Extract date from the article page."""
    try:
        # Kahoku has dates in format like "2026-01-28 17:00:00"
        date_el = page.query_selector("p:has-text('202')")
        if date_el:
            text = date_el.inner_text()
            match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
            if match:
                return match.group(1)
    except Exception:
        pass
    return ""


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


def scrape_archive_pages(page: Page, max_pages: int = 12) -> list[dict]:
    """Scrape monthly archive pages to get more article links."""
    all_articles = []
    seen_ids = set()

    # Generate archive URLs for recent months
    # Format: index.html?inyear=2026&inmth=01
    from datetime import datetime, timedelta

    current_date = datetime.now()
    months_to_check = []

    for i in range(max_pages):
        date = current_date - timedelta(days=30 * i)
        year = date.year
        month = f"{date.month:02d}"
        months_to_check.append((year, month))

    for year, month in months_to_check:
        try:
            archive_url = f"{BASE_URL}index.html?inyear={year}&inmth={month}"
            logger.info(f"Checking archive: {year}/{month}")
            page.goto(archive_url, timeout=30000)
            time.sleep(1.5)

            articles = extract_article_links(page)
            for article in articles:
                if article['article_id'] not in seen_ids:
                    all_articles.append(article)
                    seen_ids.add(article['article_id'])

        except Exception as e:
            logger.warning(f"Failed to fetch archive {year}/{month}: {e}")

    return all_articles


def scrape_articles(limit: int, output_dir: Path, headless: bool = True) -> int:
    """Main scraper function."""
    output_dir.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Check already downloaded
    downloaded = get_downloaded_ids(output_dir)
    logger.info(f"Found {len(downloaded)} already downloaded")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(locale="ja-JP")
        page = context.new_page()

        # Fetch main listing page
        logger.info(f"Fetching main page: {BASE_URL}")
        page.goto(BASE_URL, timeout=60000)
        time.sleep(2)

        # Get articles from main page
        all_articles = extract_article_links(page)

        # If we need more, check archive pages
        remaining = limit - len([a for a in all_articles if a['article_id'] not in downloaded])
        if remaining > 0:
            logger.info("Checking archive pages for more articles...")
            archive_articles = scrape_archive_pages(page, max_pages=24)
            existing_ids = {a['article_id'] for a in all_articles}
            for article in archive_articles:
                if article['article_id'] not in existing_ids:
                    all_articles.append(article)
                    existing_ids.add(article['article_id'])

        # Filter already downloaded
        to_fetch = [a for a in all_articles if a['article_id'] not in downloaded][:limit]
        logger.info(f"Will download {len(to_fetch)} new articles")

        success = 0
        errors = 0

        for i, article in enumerate(to_fetch):
            try:
                logger.info(f"[{i+1}/{len(to_fetch)}] Fetching {article['article_id']}")

                # Fetch article page
                html = fetch_article_html(page, article['url'])

                # Extract date if not already present
                if not article.get('date'):
                    article['date'] = extract_date_from_page(page)

                # Save to disk
                save_article(article, html, output_dir)
                success += 1

            except Exception as e:
                errors += 1
                logger.error(f"Failed {article['article_id']}: {e}")

            time.sleep(MIN_REQUEST_INTERVAL)

        browser.close()

    total = len(downloaded) + success
    logger.info(f"Done: {success} new, {errors} errors, {total} total")
    return success


def main():
    parser = argparse.ArgumentParser(description="Scrape Kahoku Easy Japanese")
    parser.add_argument("--limit", type=int, default=50, help="Maximum articles to download")
    parser.add_argument("--output", type=Path, default=Path("data/raw/kahoku"), help="Output directory")
    parser.add_argument("--headed", action="store_true", help="Run in headed mode (visible browser)")
    args = parser.parse_args()

    logger.info(f"Starting Kahoku scraper: limit={args.limit}, output={args.output}")
    scrape_articles(args.limit, args.output, headless=not args.headed)


if __name__ == "__main__":
    main()
