#!/usr/bin/env python3
"""
Scrape additional articles from expanded article list.
Uses Playwright in headless mode with saved browser state.
"""

import json
import logging
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

BASE_URL = "https://news.web.nhk/news/easy"
REQUEST_DELAY = 1.5  # seconds between requests
STATE_DIR = Path("data/scrapers/.browser_state")


def fetch_article(page, news_id: str) -> str | None:
    """Fetch a single article's rendered HTML."""
    url = f"{BASE_URL}/{news_id}/{news_id}.html"
    try:
        response = page.goto(url, timeout=30000)
        if response and response.status == 404:
            return None
        # Wait for article content
        try:
            page.wait_for_selector("article", timeout=10000)
            time.sleep(0.5)
        except Exception:
            pass
        html = page.content()
        # Check if it has actual content (ruby tags)
        if "<rt>" in html:
            return html
        return None
    except Exception as e:
        logger.debug(f"Error fetching {news_id}: {e}")
        return None


def save_article(news_id: str, html: str, output_dir: Path):
    """Save article HTML and metadata."""
    article_dir = output_dir / news_id
    article_dir.mkdir(parents=True, exist_ok=True)
    (article_dir / "article.html").write_text(html, encoding="utf-8")
    (article_dir / "metadata.json").write_text(
        json.dumps({"news_id": news_id}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def main(target_total: int = 1500):
    project_dir = Path(__file__).parent.parent
    expanded_path = project_dir / "data" / "scrapers" / "expanded_articles.json"
    output_dir = project_dir / "data" / "raw"

    output_dir.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Load expanded article list
    with open(expanded_path) as f:
        all_articles = json.load(f)

    # Check already downloaded
    existing = set()
    for d in output_dir.iterdir():
        if d.is_dir() and (d / "article.html").exists():
            html = (d / "article.html").read_text(encoding="utf-8")
            if "<rt>" in html:
                existing.add(d.name)

    logger.info(f"Already downloaded: {len(existing)}")
    logger.info(f"Target total: {target_total}")

    if len(existing) >= target_total:
        logger.info("Target already met!")
        return

    need = target_total - len(existing)
    logger.info(f"Need to download: {need}")

    # Filter to undownloaded articles
    to_scrape = [a for a in all_articles if a["news_id"] not in existing]
    logger.info(f"Candidates to try: {len(to_scrape)}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Load browser state if exists
        state_file = STATE_DIR / "state.json"
        if state_file.exists():
            context = browser.new_context(
                locale="ja-JP",
                storage_state=str(state_file),
            )
        else:
            context = browser.new_context(locale="ja-JP")

        page = context.new_page()

        # First visit main page to ensure session
        logger.info("Initializing session...")
        try:
            page.goto(BASE_URL, timeout=60000)
            time.sleep(3)
            context.storage_state(path=str(state_file))
        except Exception as e:
            logger.warning(f"Could not init session: {e}")

        success = 0
        tried = 0
        not_found = 0
        errors = 0

        for article in to_scrape:
            if success >= need:
                break

            tried += 1
            news_id = article["news_id"]

            html = fetch_article(page, news_id)

            if html:
                save_article(news_id, html, output_dir)
                success += 1
                if success % 10 == 0:
                    logger.info(f"Progress: {success}/{need} downloaded ({tried} tried, {not_found} 404s)")
            else:
                not_found += 1

            # Rate limiting
            time.sleep(REQUEST_DELAY)

            # Save state periodically
            if tried % 50 == 0:
                context.storage_state(path=str(state_file))

        browser.close()

    total = len(existing) + success
    logger.info(f"Done: {success} new, {not_found} not found, {total} total")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=1500)
    args = parser.parse_args()
    main(args.target)
