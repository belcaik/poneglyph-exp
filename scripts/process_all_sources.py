#!/usr/bin/env python3
"""
Process All Sources

Runs all parsers and merges processed data from all sources (NHK, MATCHA, Kahoku, Hirogaru).
Outputs combined data to data/processed/all_sources/.

Usage:
    python scripts/process_all_sources.py
"""

import json
import subprocess
import sys
from pathlib import Path

# Source configurations
SOURCES = {
    "nhk": {
        "parser": "data/scrapers/parse_nhk.py",
        "input": "data/raw",  # NHK uses root raw dir
        "output": "data/processed",  # NHK uses root processed dir
        "id_field": "news_id",
    },
    "matcha": {
        "parser": "data/scrapers/parse_matcha.py",
        "input": "data/raw/matcha",
        "output": "data/processed/matcha",
        "id_field": "article_id",
    },
    "kahoku": {
        "parser": "data/scrapers/parse_kahoku.py",
        "input": "data/raw/kahoku",
        "output": "data/processed/kahoku",
        "id_field": "article_id",
    },
    "hirogaru": {
        "parser": "data/scrapers/parse_hirogaru.py",
        "input": "data/raw/hirogaru",
        "output": "data/processed/hirogaru",
        "id_field": "article_id",
    },
}


def run_parser(source_name: str, config: dict) -> bool:
    """Run a parser for a source."""
    parser_path = Path(config["parser"])
    if not parser_path.exists():
        print(f"  Parser not found: {parser_path}")
        return False

    input_dir = Path(config["input"])
    if not input_dir.exists():
        print(f"  Input directory not found: {input_dir}")
        return False

    cmd = [
        sys.executable,
        str(parser_path),
        "--input", str(input_dir),
        "--output", str(config["output"]),
        "--examples", "0",  # Don't show examples when batch processing
    ]

    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  Error: {result.stderr}")
        return False

    return True


def count_processed(output_dir: Path) -> tuple[int, int]:
    """Count articles and sentences in a processed directory."""
    articles = 0
    sentences = 0

    for f in output_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            articles += 1
            sentences += len(data.get("sentences", []))
        except Exception:
            pass

    return articles, sentences


def merge_all_sources(output_dir: Path) -> dict:
    """Merge all processed sources into a combined directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {}
    all_articles = []

    for source_name, config in SOURCES.items():
        source_output = Path(config["output"])
        if not source_output.exists():
            print(f"  Skipping {source_name}: no processed data")
            continue

        articles = 0
        sentences = 0

        for f in source_output.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))

                # Normalize the article structure
                article = {
                    "source": source_name,
                    "article_id": data.get(config["id_field"], data.get("article_id", data.get("news_id", f.stem))),
                    "url": data.get("url", ""),
                    "title": data.get("title", ""),
                    "date": data.get("date", ""),
                    "sentences": data.get("sentences", []),
                }

                all_articles.append(article)
                articles += 1
                sentences += len(article["sentences"])

            except Exception as e:
                print(f"  Warning: Failed to load {f}: {e}")

        stats[source_name] = {"articles": articles, "sentences": sentences}

    # Save merged data
    merged_path = output_dir / "all_articles.json"
    merged_path.write_text(
        json.dumps(all_articles, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Also save individual files for compatibility
    for article in all_articles:
        article_path = output_dir / f"{article['source']}_{article['article_id']}.json"
        article_path.write_text(
            json.dumps(article, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    return stats


def main():
    print("=" * 60)
    print("PROCESSING ALL SOURCES")
    print("=" * 60)

    # Run parsers for each source
    print("\n1. Running parsers...")
    for source_name, config in SOURCES.items():
        print(f"\n[{source_name.upper()}]")
        input_dir = Path(config["input"])
        if input_dir.exists() and any(input_dir.iterdir()):
            run_parser(source_name, config)
        else:
            print(f"  No raw data found at {input_dir}")

    # Merge all sources
    print("\n" + "=" * 60)
    print("2. Merging all sources...")
    print("=" * 60)

    all_sources_dir = Path("data/processed/all_sources")
    stats = merge_all_sources(all_sources_dir)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_articles = 0
    total_sentences = 0

    print(f"\n{'Source':<15} {'Articles':>10} {'Sentences':>12}")
    print("-" * 40)

    for source_name, source_stats in stats.items():
        articles = source_stats["articles"]
        sentences = source_stats["sentences"]
        total_articles += articles
        total_sentences += sentences
        print(f"{source_name:<15} {articles:>10} {sentences:>12}")

    print("-" * 40)
    print(f"{'TOTAL':<15} {total_articles:>10} {total_sentences:>12}")

    print(f"\nMerged data saved to: {all_sources_dir}")
    print(f"  - all_articles.json ({total_articles} articles)")
    print(f"  - Individual article files")

    # Check for format inconsistencies
    print("\n" + "=" * 60)
    print("FORMAT CHECK")
    print("=" * 60)

    issues = []
    all_articles_path = all_sources_dir / "all_articles.json"
    if all_articles_path.exists():
        articles = json.loads(all_articles_path.read_text(encoding="utf-8"))
        for article in articles:
            if not article.get("source"):
                issues.append(f"Missing source: {article.get('article_id')}")
            if not article.get("sentences"):
                issues.append(f"No sentences: {article.get('source')}/{article.get('article_id')}")
            for sent in article.get("sentences", []):
                if not sent.get("tokens"):
                    issues.append(f"Sentence without tokens in {article.get('source')}/{article.get('article_id')}")
                    break

    if issues:
        print(f"\nFound {len(issues)} issues:")
        for issue in issues[:10]:
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")
    else:
        print("\nNo format issues found!")

    print("\nDone!")


if __name__ == "__main__":
    main()
