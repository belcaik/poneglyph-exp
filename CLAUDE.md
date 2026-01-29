# CLAUDE.md - Furigana Lab

## Project Purpose
Isolated benchmark repository to compare different furigana (Japanese reading annotation) methods.
Goal: Determine the best approach for the Poneglyph project before integration.

## Critical Context
- **The developer does not read Japanese** - all validation must be automated against ground truth
- **Ground truth source**: NHK Easy News (has verified furigana in HTML ruby tags)
- **Success metric**: Accuracy > Implementation Complexity > Latency > Memory

## Priority Order for Implementation
1. Data pipeline (scraper + parser) - WITHOUT THIS, NOTHING ELSE WORKS
2. Baseline method (Lindera + dictionary lookup)
3. Evaluation framework
4. Alternative methods (only after baseline is working)

## Constraints
- All code in English (comments included)
- Python for scrapers and evaluation (faster iteration)
- Rust for annotation methods (production parity with Poneglyph)
- No external paid APIs (everything must run locally)
- Target: Can leave running overnight with checkpoints

## Data Pipeline Specifications

### NHK Easy News Scraper
- Source: https://news.web.nhk/news/easy/
- JSON endpoint: https://news.web.nhk/news/easy/news-list.json
- Extract: Article text with ruby annotations
```json
{
  "source": "nhk_easy",
  "url": "https://...",
  "date": "2025-01-28",
  "sentences": [
    {
      "text": "日本語の文章",
      "tokens": [
        {"surface": "日本語", "reading": "にほんご", "start": 0, "end": 3},
        {"surface": "の", "reading": "の", "start": 3, "end": 4},
        {"surface": "文章", "reading": "ぶんしょう", "start": 4, "end": 6}
      ]
    }
  ]
}
```

### Validation Rules
- Skip sentences without any kanji (no furigana needed)
- Skip sentences with parsing errors (log them for review)
- Minimum 1000 sentences for meaningful evaluation

## Method Interface (Rust)
Each method must implement:
```rust
pub trait FuriganaAnnotator {
    fn annotate(&self, text: &str) -> Result<Vec<Token>, AnnotationError>;
    fn name(&self) -> &str;
    fn description(&self) -> &str;
}

pub struct Token {
    pub surface: String,      // Original text
    pub reading: String,      // Hiragana reading
    pub start_offset: usize,
    pub end_offset: usize,
    pub confidence: f32,      // 0.0 - 1.0
}
```

## Evaluation Metrics
1. **Accuracy**: Exact match of reading per token (primary metric)
2. **Partial Accuracy**: Character-level match for partial credit
3. **Latency**: p50, p95, p99 per sentence
4. **Memory**: Peak RSS during processing
5. **Error Categories**: 
   - numeric_counters (2人 → ふたり)
   - date_expressions (3日 → みっか)
   - irregular_readings (今日 → きょう)
   - proper_nouns (context-dependent)
   - unknown_words (not in dictionary)

## Autonomous Work Guidelines

### Safe to do without confirmation:
- Scraping NHK Easy (public educational content) - domain: news.web.nhk
- Creating/modifying files in this repository
- Running benchmarks
- Installing dependencies via cargo/pip
- Git commits with descriptive messages

### Requires confirmation before proceeding:
- Any network requests to domains other than news.web.nhk
- Deleting data files
- Changing the evaluation metrics definition
- Modifying the Token interface (breaking change)

### Checkpointing
After completing each major milestone, create a checkpoint:
```bash
git add -A
git commit -m "CHECKPOINT: [description of what was completed]"
```

Milestones that require checkpoints:
1. Scraper working and first 100 articles downloaded
2. Parser extracting tokens correctly (validated on 10 random samples)
3. Baseline method implemented and passing basic tests
4. Evaluation framework producing comparison reports
5. Each additional method implemented

## Known Edge Cases to Test
These are common failure modes in furigana systems:

| Input | Expected | Category | Notes |
|-------|----------|----------|-------|
| 2人 | ふたり | numeric_counter | Not "にひと" |
| 3日 | みっか | date_counter | Not "さんにち" |
| 今日 | きょう | ateji | Not "こんにち" |
| 明日 | あした | ateji | Could also be "あす" |
| 大人 | おとな | irregular | Not "だいじん" |
| 一人 | ひとり | numeric_counter | Not "いちにん" |
| 二十歳 | はたち | special | Not "にじゅっさい" |
| 行った | いった | verb_conjugation | Could be "おこなった" |

## Directory-Specific Instructions

### /data/scrapers/
- Use requests + BeautifulSoup for scraping
- Respect rate limits: 1 request per second minimum
- Save raw HTML before parsing (for debugging)
- Log all errors to scraper.log

### /methods/
- Each method in its own directory with Cargo.toml
- Include a README.md explaining the approach
- Include unit tests for basic functionality

### /evaluation/
- Generate markdown reports in /results/
- Include visualizations (accuracy by category, latency distribution)
- Error analysis should categorize failures

## Commands Reference
```bash
# Scrape NHK Easy articles
python data/scrapers/nhk_easy.py --num-articles 500 --output data/raw/

# Parse raw HTML to structured JSON
python data/scrapers/parse_nhk.py --input data/raw/ --output data/processed/

# Split into train/val/test
python scripts/split_data.py --input data/processed/ --output data/splits/

# Run baseline method
cargo run --release -p baseline_lindera -- --input data/splits/test.json

# Evaluate all methods
python evaluation/compare.py --methods baseline_lindera,hybrid_fallback --output results/

# Generate report
python scripts/generate_report.py --results results/ --output results/report.md
```

## Success Criteria for This Repository
The benchmark is complete when:
1. [ ] At least 1000 test sentences from NHK Easy
2. [ ] Baseline method (Lindera) implemented and evaluated
3. [ ] At least one alternative method implemented
4. [ ] Comparison report generated with clear recommendation
5. [ ] Error analysis identifying which categories need improvement
6. [ ] All code documented and reproducible

## Notes for Overnight Runs
If running autonomously:
1. Start with `claude --dangerously-skip-permissions` only if you trust the CLAUDE.md constraints
2. Better: Use `claude` normally and queue specific tasks
3. Check git log in the morning to see what was accomplished
4. Review any files in /results/ for findings