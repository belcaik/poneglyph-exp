#!/usr/bin/env python3
"""
Split parsed NHK Easy articles into train/val/test sets.
Also displays statistics about the dataset.
"""

import argparse
import json
import random
from collections import Counter
from pathlib import Path


def load_processed_articles(input_dir: Path) -> list[dict]:
    """Load all processed articles."""
    articles = []
    for f in sorted(input_dir.glob("*.json")):
        articles.append(json.loads(f.read_text(encoding="utf-8")))
    return articles


def split_data(articles: list[dict], train_ratio: float = 0.7, val_ratio: float = 0.15):
    """Split articles into train/val/test sets."""
    random.seed(42)  # Reproducibility
    random.shuffle(articles)

    n = len(articles)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    return {
        "train": articles[:train_end],
        "val": articles[train_end:val_end],
        "test": articles[val_end:],
    }


def compute_statistics(articles: list[dict]) -> dict:
    """Compute statistics for a set of articles."""
    total_sentences = 0
    sentences_with_tokens = 0
    total_tokens = 0
    tokens_per_sentence = []

    for article in articles:
        for sentence in article.get("sentences", []):
            total_sentences += 1
            tokens = sentence.get("tokens", [])
            if tokens:
                sentences_with_tokens += 1
                total_tokens += len(tokens)
                tokens_per_sentence.append(len(tokens))

    return {
        "num_articles": len(articles),
        "total_sentences": total_sentences,
        "sentences_with_tokens": sentences_with_tokens,
        "total_tokens": total_tokens,
        "avg_sentences_per_article": total_sentences / len(articles) if articles else 0,
        "avg_tokens_per_sentence": total_tokens / sentences_with_tokens if sentences_with_tokens else 0,
        "tokens_per_sentence_distribution": {
            "min": min(tokens_per_sentence) if tokens_per_sentence else 0,
            "max": max(tokens_per_sentence) if tokens_per_sentence else 0,
            "median": sorted(tokens_per_sentence)[len(tokens_per_sentence)//2] if tokens_per_sentence else 0,
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Split data into train/val/test")
    parser.add_argument("--input", type=Path, default=Path("data/processed"))
    parser.add_argument("--output", type=Path, default=Path("data/splits"))
    args = parser.parse_args()

    # Load articles
    articles = load_processed_articles(args.input)
    print(f"\nLoaded {len(articles)} articles from {args.input}")

    # Compute overall statistics
    overall_stats = compute_statistics(articles)

    print("\n" + "="*60)
    print("DATASET STATISTICS")
    print("="*60)
    print(f"\nTotal articles: {overall_stats['num_articles']}")
    print(f"Total sentences: {overall_stats['total_sentences']}")
    print(f"Sentences with furigana tokens: {overall_stats['sentences_with_tokens']}")
    print(f"Total furigana tokens: {overall_stats['total_tokens']}")
    print(f"\nAverage sentences per article: {overall_stats['avg_sentences_per_article']:.1f}")
    print(f"Average tokens per sentence: {overall_stats['avg_tokens_per_sentence']:.1f}")
    print(f"\nTokens per sentence distribution:")
    print(f"  Min: {overall_stats['tokens_per_sentence_distribution']['min']}")
    print(f"  Max: {overall_stats['tokens_per_sentence_distribution']['max']}")
    print(f"  Median: {overall_stats['tokens_per_sentence_distribution']['median']}")

    # Split data
    splits = split_data(articles)

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Save splits
    print("\n" + "="*60)
    print("DATA SPLITS")
    print("="*60)

    for split_name, split_data_list in splits.items():
        # Flatten to sentences for training
        sentences = []
        for article in split_data_list:
            for sentence in article.get("sentences", []):
                if sentence.get("tokens"):  # Only sentences with tokens
                    sentences.append({
                        "source": article.get("source", "nhk_easy"),
                        "news_id": article.get("news_id", ""),
                        "text": sentence.get("text", ""),
                        "tokens": sentence.get("tokens", []),
                    })

        # Save
        output_path = args.output / f"{split_name}.json"
        output_path.write_text(
            json.dumps(sentences, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        stats = compute_statistics(split_data_list)
        print(f"\n{split_name.upper()}:")
        print(f"  Articles: {stats['num_articles']}")
        print(f"  Sentences (with tokens): {len(sentences)}")
        print(f"  Total tokens: {sum(len(s['tokens']) for s in sentences)}")
        print(f"  Saved to: {output_path}")

    # Also save a combined file with all sentences
    all_sentences = []
    for article in articles:
        for sentence in article.get("sentences", []):
            if sentence.get("tokens"):
                all_sentences.append({
                    "source": article.get("source", "nhk_easy"),
                    "news_id": article.get("news_id", ""),
                    "text": sentence.get("text", ""),
                    "tokens": sentence.get("tokens", []),
                })

    all_path = args.output / "all.json"
    all_path.write_text(
        json.dumps(all_sentences, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\nAll sentences: {len(all_sentences)} -> {all_path}")

    print("\n" + "="*60)
    print("SAMPLE TOKENS (first 10 unique)")
    print("="*60 + "\n")

    seen_tokens = set()
    for sentence in all_sentences[:50]:
        for token in sentence.get("tokens", []):
            key = (token.get("surface"), token.get("reading"))
            if key not in seen_tokens:
                seen_tokens.add(key)
                print(f"  {token['surface']} → {token['reading']}")
            if len(seen_tokens) >= 10:
                break
        if len(seen_tokens) >= 10:
            break

    print(f"\n✓ Data split complete!")


if __name__ == "__main__":
    main()
