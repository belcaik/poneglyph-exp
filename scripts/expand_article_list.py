#!/usr/bin/env python3
"""
Expand article list by generating article IDs from date patterns.

NHK Easy News article IDs follow pattern: neYYYYMMDDNNNNN
where YYYYMMDD is the date and NNNNN is a sequential number.

This script generates plausible article IDs for the past year.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path


def generate_article_ids(start_date: datetime, end_date: datetime) -> list[str]:
    """Generate plausible article IDs for a date range."""
    ids = []
    current = start_date

    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        # Generate IDs with common sequential patterns
        # NHK typically has 3-6 articles per day
        for seq in range(11000, 11700, 50):  # Sample various sequence numbers
            news_id = f"ne{date_str}{seq}"
            ids.append(news_id)
        current += timedelta(days=1)

    return ids


def main():
    script_dir = Path(__file__).parent.parent / "data" / "scrapers"
    all_articles_path = script_dir / "all_articles.json"
    output_path = script_dir / "expanded_articles.json"

    # Load existing articles
    existing = set()
    if all_articles_path.exists():
        with open(all_articles_path) as f:
            articles = json.load(f)
            for a in articles:
                existing.add(a["news_id"])
        print(f"Existing articles: {len(existing)}")

    # Generate new IDs for past 2 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years back

    new_ids = generate_article_ids(start_date, end_date)
    print(f"Generated {len(new_ids)} potential IDs")

    # Combine with existing
    all_ids = existing | set(new_ids)
    print(f"Total unique IDs: {len(all_ids)}")

    # Create article list
    articles = []
    for news_id in sorted(all_ids, reverse=True):  # Newest first
        articles.append({
            "news_id": news_id,
            "url": f"https://news.web.nhk/news/easy/{news_id}/{news_id}.html"
        })

    # Save expanded list
    with open(output_path, "w") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(articles)} articles to {output_path}")


if __name__ == "__main__":
    main()
