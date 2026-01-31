#!/usr/bin/env python3
"""
Scrape NHK Easy News articles by navigating through the archive.
NHK keeps articles for ~6 months, so we need recent article IDs.
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
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
STATE_DIR = Path("data/scrapers/.browser_state")


def extract_article_ids(page) -> list[str]:
    """Extract article IDs from current page."""
    ids = set()
    links = page.query_selector_all("a")
    for link in links:
        try:
            href = link.get_attribute("href") or ""
            match = re.search(r"/(ne\d+)/", href)
            if match:
                ids.add(match.group(1))
        except Exception:
            pass
    return list(ids)


def main(target: int = 1500):
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Check existing
    existing = set()
    for d in output_dir.iterdir():
        if d.is_dir() and (d / "article.html").exists():
            html = (d / "article.html").read_text(encoding="utf-8")
            if "<rt>" in html:
                existing.add(d.name)

    logger.info(f"Existing articles with ruby: {len(existing)}")
    need = target - len(existing)
    if need <= 0:
        logger.info("Target already met!")
        return

    logger.info(f"Need {need} more articles")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        state_file = STATE_DIR / "state.json"
        if state_file.exists():
            context = browser.new_context(locale="ja-JP", storage_state=str(state_file))
        else:
            context = browser.new_context(locale="ja-JP")

        page = context.new_page()

        # Step 1: Get all available article IDs from main page and "more" pages
        logger.info("Fetching article list from main page...")
        page.goto(BASE_URL, timeout=60000)
        time.sleep(3)

        all_ids = set()

        # Get articles from current page
        ids = extract_article_ids(page)
        all_ids.update(ids)
        logger.info(f"Found {len(ids)} articles on main page")

        # Try to click "load more" multiple times
        for i in range(20):  # Try up to 20 times
            try:
                more_btn = page.get_by_text("もっと見る")
                if more_btn.is_visible(timeout=3000):
                    more_btn.click()
                    time.sleep(2)
                    new_ids = extract_article_ids(page)
                    before = len(all_ids)
                    all_ids.update(new_ids)
                    logger.info(f"Click {i+1}: Found {len(all_ids) - before} new articles, total {len(all_ids)}")
                else:
                    break
            except Exception:
                break

        # Filter to new articles
        to_scrape = [aid for aid in sorted(all_ids, reverse=True) if aid not in existing]
        logger.info(f"New articles to scrape: {len(to_scrape)}")

        if len(to_scrape) < need:
            logger.warning(f"Only {len(to_scrape)} new articles available, but need {need}")
            # Continue with what we have

        success = 0
        for i, news_id in enumerate(to_scrape[:need]):
            url = f"{BASE_URL}/{news_id}/{news_id}.html"
            try:
                page.goto(url, timeout=30000)
                try:
                    page.wait_for_selector("article", timeout=10000)
                    time.sleep(0.5)
                except Exception:
                    pass

                html = page.content()
                if "<rt>" in html:
                    # Save article
                    article_dir = output_dir / news_id
                    article_dir.mkdir(parents=True, exist_ok=True)
                    (article_dir / "article.html").write_text(html, encoding="utf-8")
                    (article_dir / "metadata.json").write_text(
                        json.dumps({"news_id": news_id}, ensure_ascii=False),
                        encoding="utf-8"
                    )
                    success += 1
                    if success % 10 == 0:
                        logger.info(f"Progress: {success}/{need} downloaded")
                else:
                    logger.warning(f"No ruby content: {news_id}")
            except Exception as e:
                logger.warning(f"Error {news_id}: {e}")

            time.sleep(1.5)

            # Save state periodically
            if i % 50 == 0:
                context.storage_state(path=str(state_file))

        browser.close()

    total = len(existing) + success
    logger.info(f"Done: {success} new articles, {total} total")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=1500)
    args = parser.parse_args()
    main(args.target)
