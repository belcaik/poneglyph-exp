#!/usr/bin/env python3
"""
Batch scraper for NHK Easy News using Playwright.
Renders JavaScript to get proper ruby/furigana annotations.
"""

import argparse
import json
import logging
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# NHK Easy News article base URL
BASE_URL = "https://news.web.nhk/news/easy"

# Rate limiting
REQUEST_DELAY = 2.0  # seconds between requests

# Browser state storage
STATE_DIR = Path(__file__).parent / ".browser_state"


def fetch_article(page, news_id: str) -> str | None:
    """Fetch a single article's rendered HTML."""
    url = f"{BASE_URL}/{news_id}/{news_id}.html"
    try:
        page.goto(url, timeout=60000)
        # Wait for article content to render
        try:
            page.wait_for_selector("article", timeout=30000)
            time.sleep(1)  # Extra time for ruby rendering
        except Exception:
            logger.warning(f"Article element not found for {news_id}")
        return page.content()
    except Exception as e:
        logger.warning(f"Error fetching {news_id}: {e}")
        return None


def save_article(news_id: str, html: str, output_dir: Path):
    """Save article HTML and metadata."""
    article_dir = output_dir / news_id
    article_dir.mkdir(parents=True, exist_ok=True)

    (article_dir / "article.html").write_text(html, encoding="utf-8")

    metadata = {
        "news_id": news_id,
        "url": f"{BASE_URL}/{news_id}/{news_id}.html"
    }
    (article_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def main(limit: int = 0, headless: bool = True):
    # Paths
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent.parent
    article_list_path = script_dir / "article_list.json"
    output_dir = project_dir / "data" / "raw"

    output_dir.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Load article list
    with open(article_list_path) as f:
        all_articles = json.load(f)

    # Check already downloaded (with valid ruby content)
    existing = set()
    for d in output_dir.iterdir():
        if d.is_dir() and (d / "article.html").exists():
            # Check if it has ruby tags (properly rendered)
            html = (d / "article.html").read_text(encoding="utf-8")
            if "<rt>" in html:
                existing.add(d.name)

    # Filter to articles we need
    to_scrape = [a for a in all_articles if a["news_id"] not in existing]

    # Apply limit if specified
    if limit > 0:
        to_scrape = to_scrape[:limit]

    logger.info(f"Total target: {len(all_articles)}")
    logger.info(f"Already downloaded (with ruby): {len(existing)}")
    logger.info(f"To scrape: {len(to_scrape)}")

    if not to_scrape:
        logger.info("Nothing to scrape!")
        return

    # Launch Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)

        # Try to load existing browser state
        state_file = STATE_DIR / "state.json"
        if state_file.exists():
            logger.info("Loading saved browser state...")
            context = browser.new_context(
                locale="ja-JP",
                storage_state=str(state_file),
            )
        else:
            logger.info("Creating new browser context...")
            context = browser.new_context(locale="ja-JP")

        page = context.new_page()

        success_count = 0
        batch_size = 50

        for batch_num, i in enumerate(range(0, len(to_scrape), batch_size)):
            batch = to_scrape[i:i + batch_size]
            logger.info(f"\nBatch {batch_num + 1}/{(len(to_scrape) + batch_size - 1)//batch_size}")

            for j, article in enumerate(batch):
                news_id = article["news_id"]
                html = fetch_article(page, news_id)

                if html and "<rt>" in html:  # Verify ruby content
                    save_article(news_id, html, output_dir)
                    success_count += 1
                    logger.info(f"  [{j+1}/{len(batch)}] ✓ {news_id}")
                else:
                    logger.warning(f"  [{j+1}/{len(batch)}] ✗ {news_id} (no ruby content)")

                time.sleep(REQUEST_DELAY)

            # Save browser state periodically
            context.storage_state(path=str(state_file))
            logger.info(f"Batch done: {success_count} total successful so far")

            # Pause between batches
            if i + batch_size < len(to_scrape):
                logger.info("Pausing between batches...")
                time.sleep(REQUEST_DELAY * 5)

        browser.close()

    logger.info(f"\nTotal scraped: {success_count}/{len(to_scrape)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch scrape NHK Easy articles with Playwright")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of articles (0 = no limit)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()
    main(limit=args.limit, headless=args.headless)
