#!/usr/bin/env python3
"""
Batch scraper for NHK Easy News articles.
Uses asyncio and aiohttp for efficient parallel scraping.
"""

import asyncio
import json
import logging
import os
from pathlib import Path

import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# NHK Easy News article base URL
BASE_URL = "https://news.web.nhk/news/easy"

# Rate limiting
CONCURRENT_REQUESTS = 3
REQUEST_DELAY = 1.0  # seconds between requests

# Realistic browser headers to avoid 403 blocks
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


async def fetch_article(session: aiohttp.ClientSession, news_id: str) -> tuple[str, str | None]:
    """Fetch a single article's HTML."""
    url = f"{BASE_URL}/{news_id}/{news_id}.html"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                html = await response.text()
                return news_id, html
            else:
                logger.warning(f"Failed {news_id}: HTTP {response.status}")
                return news_id, None
    except Exception as e:
        logger.warning(f"Error fetching {news_id}: {e}")
        return news_id, None


async def save_article(news_id: str, html: str, output_dir: Path):
    """Save article HTML and metadata."""
    article_dir = output_dir / news_id
    article_dir.mkdir(parents=True, exist_ok=True)

    # Save HTML
    (article_dir / "article.html").write_text(html, encoding="utf-8")

    # Save metadata
    metadata = {
        "news_id": news_id,
        "url": f"{BASE_URL}/{news_id}/{news_id}.html"
    }
    (article_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


async def scrape_batch(articles: list[dict], output_dir: Path, semaphore: asyncio.Semaphore):
    """Scrape a batch of articles."""
    async with aiohttp.ClientSession(headers=BROWSER_HEADERS) as session:
        success_count = 0
        for i, article in enumerate(articles):
            async with semaphore:
                news_id = article["news_id"]
                news_id, html = await fetch_article(session, news_id)
                if html:
                    await save_article(news_id, html, output_dir)
                    success_count += 1
                    logger.info(f"  [{i+1}/{len(articles)}] ✓ {news_id}")
                else:
                    logger.warning(f"  [{i+1}/{len(articles)}] ✗ {news_id}")
                # Rate limit between requests
                await asyncio.sleep(REQUEST_DELAY)
        return success_count


async def main(limit: int = 0):
    # Paths
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent.parent
    article_list_path = script_dir / "article_list.json"
    output_dir = project_dir / "data" / "raw"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load article list
    with open(article_list_path) as f:
        all_articles = json.load(f)

    # Check already downloaded
    existing = set()
    for d in output_dir.iterdir():
        if d.is_dir() and (d / "article.html").exists():
            existing.add(d.name)

    # Filter to articles we need
    to_scrape = [a for a in all_articles if a["news_id"] not in existing]

    # Apply limit if specified
    if limit > 0:
        to_scrape = to_scrape[:limit]

    logger.info(f"Total target: {len(all_articles)}")
    logger.info(f"Already downloaded: {len(existing)}")
    logger.info(f"To scrape: {len(to_scrape)}")

    if not to_scrape:
        logger.info("Nothing to scrape!")
        return

    # Scrape with rate limiting
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    batch_size = 50
    total_success = 0

    for i in range(0, len(to_scrape), batch_size):
        batch = to_scrape[i:i + batch_size]
        logger.info(f"Scraping batch {i//batch_size + 1}/{(len(to_scrape) + batch_size - 1)//batch_size}")

        success = await scrape_batch(batch, output_dir, semaphore)
        total_success += success

        logger.info(f"Batch done: {success}/{len(batch)} succeeded")
        await asyncio.sleep(REQUEST_DELAY * 10)  # Pause between batches

    logger.info(f"Total scraped: {total_success}/{len(to_scrape)}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Batch scrape NHK Easy articles")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of articles to scrape (0 = no limit)")
    args = parser.parse_args()
    asyncio.run(main(limit=args.limit))
