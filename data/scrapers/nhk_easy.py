#!/usr/bin/env python3
"""
NHK Easy News Scraper

Downloads articles from NHK Easy News (news.web.nhk) for furigana benchmarking.
Uses Playwright in headed mode for reliable consent handling.
Browser state is persisted between runs.

Usage:
    python nhk_easy.py --num-articles 50 --output ../raw/

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

# NHK Easy News URLs
BASE_URL = "https://news.web.nhk/news/easy/"

# Browser state storage
STATE_DIR = Path("data/scrapers/.browser_state")

# Rate limiting
MIN_REQUEST_INTERVAL = 1.5  # seconds between page loads


def extract_articles_from_page(page: Page) -> list[dict]:
    """Extract article links from the rendered main page."""
    articles = []

    # Get all links that might be article links
    links = page.query_selector_all("a")

    for link in links:
        try:
            href = link.get_attribute("href")
            if not href:
                continue

            # Match article URLs like /news/easy/ne2026012911522/...
            match = re.search(r"/news/easy/(ne\d+)/", href)
            if not match:
                continue

            news_id = match.group(1)

            # Get text content as title
            title = link.inner_text()[:100]  # Limit length

            articles.append(
                {
                    "news_id": news_id,
                    "title": title.strip(),
                    "date": "",
                    "url": f"{BASE_URL}{news_id}/{news_id}.html",
                }
            )
        except Exception:
            continue

    # Deduplicate
    seen = set()
    unique = []
    for a in articles:
        if a["news_id"] not in seen:
            seen.add(a["news_id"])
            unique.append(a)

    logger.info(f"Found {len(unique)} unique articles")
    return unique


def fetch_article_html(page: Page, url: str) -> str:
    """Fetch rendered HTML of an article page."""
    page.goto(url, timeout=60000)
    try:
        page.wait_for_selector("article", timeout=30000)
        time.sleep(2)
    except Exception:
        logger.warning(f"Article not fully loaded: {url}")
    return page.content()


def save_article(article: dict, html: str, output_dir: Path) -> None:
    """Save article to disk."""
    article_dir = output_dir / article["news_id"]
    article_dir.mkdir(parents=True, exist_ok=True)

    (article_dir / "article.html").write_text(html, encoding="utf-8")
    (article_dir / "metadata.json").write_text(
        json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def scrape_articles(num_articles: int, output_dir: Path, headless: bool = False) -> int:
    """Main scraper function."""
    output_dir.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Check already downloaded
    downloaded = set()
    if output_dir.exists():
        for d in output_dir.iterdir():
            if d.is_dir() and (d / "article.html").exists():
                downloaded.add(d.name)
    logger.info(f"Found {len(downloaded)} already downloaded")

    with sync_playwright() as p:
        # Launch browser in headed mode for consent handling
        browser = p.chromium.launch(headless=headless)

        # Try to load existing browser state, or create new context
        state_file = STATE_DIR / "state.json"
        if state_file.exists():
            logger.info("Loading saved browser state...")
            context = browser.new_context(
                locale="ja-JP",
                storage_state=str(state_file),
            )
        else:
            logger.info("Creating new browser context (first run)...")
            context = browser.new_context(locale="ja-JP")

        page = context.new_page()

        # Visit main page
        logger.info("Loading main page...")
        page.goto(BASE_URL, timeout=120000)

        # Wait for page to load
        logger.info("Waiting for page to load...")
        logger.info(">>> If consent dialog appears, please click 'I understand' <<<")
        time.sleep(5)

        # Wait for articles to appear (user may need to accept consent)
        max_wait = 60  # seconds
        start = time.time()
        articles = []

        while time.time() - start < max_wait:
            articles = extract_articles_from_page(page)
            if articles:
                logger.info(f"Found {len(articles)} articles")
                break
            logger.info("Waiting for articles to appear...")
            time.sleep(3)

        if not articles:
            logger.warning("No articles found after waiting. Saving debug screenshot.")
            page.screenshot(path="debug_page.png")
            # Try clicking "load more"
            try:
                more = page.get_by_text("もっと見る")
                if more.is_visible(timeout=3000):
                    more.click()
                    time.sleep(5)
                    articles = extract_articles_from_page(page)
            except Exception:
                pass

        # Save browser state for next run
        logger.info("Saving browser state...")
        context.storage_state(path=str(state_file))

        # Filter already downloaded
        to_fetch = [a for a in articles if a["news_id"] not in downloaded][:num_articles]
        logger.info(f"Will download {len(to_fetch)} new articles")

        success = 0
        errors = 0

        for i, article in enumerate(to_fetch):
            try:
                logger.info(f"[{i+1}/{len(to_fetch)}] {article['news_id']}")
                html = fetch_article_html(page, article["url"])
                save_article(article, html, output_dir)
                success += 1
            except Exception as e:
                errors += 1
                logger.error(f"Failed {article['news_id']}: {e}")

            time.sleep(MIN_REQUEST_INTERVAL)

        browser.close()

    total = len(downloaded) + success
    logger.info(f"Done: {success} new, {errors} errors, {total} total")
    return total


def main():
    parser = argparse.ArgumentParser(description="Scrape NHK Easy News")
    parser.add_argument("--num-articles", type=int, default=50)
    parser.add_argument("--output", type=Path, default=Path("data/raw"))
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()

    logger.info(f"Starting: {args.num_articles} articles -> {args.output}")
    scrape_articles(args.num_articles, args.output, headless=args.headless)


if __name__ == "__main__":
    main()
