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

# Region listing pages (all 47 prefectures + popular sub-regions)
REGION_PAGES = [
    # Hokkaido
    "https://matcha-jp.com/easy/list?region=101",  # 北海道
    # Tohoku
    "https://matcha-jp.com/easy/list?region=102",  # 青森県
    "https://matcha-jp.com/easy/list?region=103",  # 岩手県
    "https://matcha-jp.com/easy/list?region=104",  # 宮城県
    "https://matcha-jp.com/easy/list?region=105",  # 秋田県
    "https://matcha-jp.com/easy/list?region=106",  # 山形県
    "https://matcha-jp.com/easy/list?region=107",  # 福島県
    # Kanto
    "https://matcha-jp.com/easy/list?region=108",  # 茨城県
    "https://matcha-jp.com/easy/list?region=109",  # 栃木県
    "https://matcha-jp.com/easy/list?region=110",  # 群馬県
    "https://matcha-jp.com/easy/list?region=111",  # 埼玉県
    "https://matcha-jp.com/easy/list?region=112",  # 千葉県
    "https://matcha-jp.com/easy/list?region=113",  # 東京都
    "https://matcha-jp.com/easy/list?region=114",  # 神奈川県
    # Chubu
    "https://matcha-jp.com/easy/list?region=115",  # 新潟県
    "https://matcha-jp.com/easy/list?region=116",  # 富山県
    "https://matcha-jp.com/easy/list?region=117",  # 石川県
    "https://matcha-jp.com/easy/list?region=118",  # 福井県
    "https://matcha-jp.com/easy/list?region=119",  # 山梨県
    "https://matcha-jp.com/easy/list?region=120",  # 長野県
    "https://matcha-jp.com/easy/list?region=121",  # 岐阜県
    "https://matcha-jp.com/easy/list?region=122",  # 静岡県
    "https://matcha-jp.com/easy/list?region=123",  # 愛知県
    "https://matcha-jp.com/easy/list?region=124",  # 三重県
    # Kinki
    "https://matcha-jp.com/easy/list?region=125",  # 滋賀県
    "https://matcha-jp.com/easy/list?region=126",  # 京都府
    "https://matcha-jp.com/easy/list?region=127",  # 大阪府
    "https://matcha-jp.com/easy/list?region=128",  # 兵庫県
    "https://matcha-jp.com/easy/list?region=129",  # 奈良県
    "https://matcha-jp.com/easy/list?region=130",  # 和歌山県
    # Chugoku
    "https://matcha-jp.com/easy/list?region=131",  # 鳥取県
    "https://matcha-jp.com/easy/list?region=132",  # 島根県
    "https://matcha-jp.com/easy/list?region=133",  # 岡山県
    "https://matcha-jp.com/easy/list?region=134",  # 広島県
    "https://matcha-jp.com/easy/list?region=135",  # 山口県
    # Shikoku
    "https://matcha-jp.com/easy/list?region=136",  # 徳島県
    "https://matcha-jp.com/easy/list?region=137",  # 香川県
    "https://matcha-jp.com/easy/list?region=138",  # 愛媛県
    "https://matcha-jp.com/easy/list?region=139",  # 高知県
    # Kyushu
    "https://matcha-jp.com/easy/list?region=140",  # 福岡県
    "https://matcha-jp.com/easy/list?region=141",  # 佐賀県
    "https://matcha-jp.com/easy/list?region=142",  # 長崎県
    "https://matcha-jp.com/easy/list?region=143",  # 熊本県
    "https://matcha-jp.com/easy/list?region=144",  # 大分県
    "https://matcha-jp.com/easy/list?region=145",  # 宮崎県
    "https://matcha-jp.com/easy/list?region=146",  # 鹿児島県
    # Okinawa
    "https://matcha-jp.com/easy/list?region=147",  # 沖縄県
    # Sub-regions (popular areas within prefectures)
    "https://matcha-jp.com/easy/list?region=223",  # 上野・浅草・秋葉原
    "https://matcha-jp.com/easy/list?region=249",  # 横浜
    "https://matcha-jp.com/easy/list?region=325",  # 神戸
]

# Category listing pages
CATEGORY_PAGES = [
    # Main categories
    "https://matcha-jp.com/easy/list?category=1",    # 食 (FOOD)
    "https://matcha-jp.com/easy/list?category=36",   # 宿泊 (STAY)
    "https://matcha-jp.com/easy/list?category=69",   # 観光 (THINGS TO DO)
    "https://matcha-jp.com/easy/list?category=101",  # 文化・カルチャー
    # Travel tips
    "https://matcha-jp.com/easy/list?category=53",   # 交通
    "https://matcha-jp.com/easy/list?category=82",   # 天気・四季
    "https://matcha-jp.com/easy/list?category=83",   # 災害
    "https://matcha-jp.com/easy/list?category=115",  # 長期滞在
    "https://matcha-jp.com/easy/list?category=116",  # 役に立つ情報
    # Food subcategories
    "https://matcha-jp.com/easy/list?category=5",    # ハラル
    "https://matcha-jp.com/easy/list?category=12",   # 居酒屋
    "https://matcha-jp.com/easy/list?category=16",   # ヴィーガン・ベジタリアン
    "https://matcha-jp.com/easy/list?category=17",   # カフェ
    "https://matcha-jp.com/easy/list?category=87",   # バー
    "https://matcha-jp.com/easy/list?category=88",   # 日本酒
    "https://matcha-jp.com/easy/list?category=89",   # 焼酎
    "https://matcha-jp.com/easy/list?category=90",   # スイーツ
    "https://matcha-jp.com/easy/list?category=91",   # 和食
]

# Combined list of all listing pages to scrape
ALL_LISTING_PAGES = REGION_PAGES + CATEGORY_PAGES


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

    # Collect articles from all listing pages
    all_articles = []
    existing_ids = set()

    # Fetch main listing page first
    logger.info(f"Fetching main page: {BASE_URL}")
    try:
        listing_html = fetch_page(BASE_URL)
        main_articles = extract_article_links(listing_html)
        for article in main_articles:
            if article['article_id'] not in existing_ids:
                all_articles.append(article)
                existing_ids.add(article['article_id'])
        time.sleep(MIN_REQUEST_INTERVAL)
    except Exception as e:
        logger.warning(f"Failed to fetch main page: {e}")

    # Crawl all region and category listing pages
    total_pages = len(ALL_LISTING_PAGES)
    logger.info(f"Crawling {total_pages} listing pages (50 regions + 18 categories)...")

    for i, page_url in enumerate(ALL_LISTING_PAGES, 1):
        try:
            logger.info(f"Fetching listing page {i}/{total_pages}: {page_url}")
            extra_html = fetch_page(page_url)
            extra_articles = extract_article_links(extra_html)

            # Add new articles (deduplication via existing_ids set)
            new_count = 0
            for article in extra_articles:
                if article['article_id'] not in existing_ids:
                    all_articles.append(article)
                    existing_ids.add(article['article_id'])
                    new_count += 1

            if new_count > 0:
                logger.info(f"  -> Added {new_count} new articles (total: {len(all_articles)})")

            # Note: MATCHA listing pages do not appear to support pagination
            # (no ?page=N parameter observed in the HTML). Each listing page
            # shows all articles for that region/category.

            time.sleep(MIN_REQUEST_INTERVAL)
        except Exception as e:
            logger.warning(f"Failed to fetch {page_url}: {e}")

    # Log total unique articles found before applying limit
    logger.info(f"Total unique articles found: {len(all_articles)}")

    # Filter already downloaded
    to_fetch = [a for a in all_articles if a['article_id'] not in downloaded][:limit]
    logger.info(f"Will download {len(to_fetch)} new articles (limit={limit})")

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
