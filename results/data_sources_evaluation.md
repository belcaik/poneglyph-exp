# Alternative Data Sources Evaluation

**Date:** 2026-01-31
**Purpose:** Evaluate alternative furigana data sources for the Poneglyph benchmark project

## Executive Summary

| Source | Quality | Quantity | Format Compatibility | Legal Status | Recommendation |
|--------|---------|----------|---------------------|--------------|----------------|
| Kaggle/NDL Huriganacorpus | Medium | 16.5M entries | Needs conversion | CC-BY-4.0 | **Primary supplement** |
| YomujP | High (educational) | ~300+ articles | Needs scraping | Restricted | Not recommended |
| Wayback Machine/NHK | High | Unknown | Same as NHK | Public archive | Worth investigating |
| Animelon | Medium | Large | Custom format | Legal gray area | Not recommended |
| NHKore (GitHub) | High | "Tons" | JSON/CSV with furigana | LGPL-3.0 | **Secondary supplement** |

**Recommendation:** Use **NDL Huriganacorpus (Kaggle)** as primary supplement to NHK Easy data. It provides massive scale with government-verified furigana. Additionally, investigate **NHKore** project for pre-scraped NHK Easy articles.

---

## 1. Kaggle: Huriganacorpus Shosi Dataset

**URL:** https://www.kaggle.com/datasets/iamleonie/huriganacorpus-shosi-dataset

### Overview
This is a post-processed version of the National Diet Library of Japan's (NDL) official furigana corpus, containing book and magazine titles with their readings.

### Data Details
- **Size:** 16.5 million entries (~750 MB compressed)
- **Format:** ZIP containing structured data with `Japanese_text` and `Yomigana` columns
- **Source:** [NDL Lab huriganacorpus-ndlbib](https://github.com/ndl-lab/huriganacorpus-ndlbib)
- **License:** CC-BY-4.0
- **Last Updated:** 2025-01-03 (Version 4)

### Data Format (Original NDL)
Tab-separated text files (TSV, UTF-8):
```
line_number  full_input_text  full_reading  token1  reading1  type1  token2  reading2  type2  ...
```

Types include: kanji, hiragana, symbols

### Quality Assessment

**Strengths:**
- Official government data from Japan's National Diet Library
- Verified furigana annotations created using professional cataloging standards
- Massive scale (16.5M entries provides excellent coverage)
- Multiple morphological dictionaries used (MeCab IPA, NEologd, UniDic, Sudachi)
- Well-documented methodology

**Weaknesses:**
- Contains **book/magazine titles only** (not sentences)
- May include old character forms (旧字体) that display incorrectly
- Readings may differ from modern kana conventions
- Kaggle version is post-processed by a third party (Leonie, German developer)
- No peer review by Japanese speakers mentioned for the Kaggle version

**Compatibility with Our Format:**
```json
// Our format (NHK-style):
{"surface": "日本語", "reading": "にほんご", "start": 0, "end": 3}

// NDL format (needs conversion):
日本語\tにほんご\tkanji
```

Conversion required but straightforward. However, **titles are not sentences** - this affects evaluation methodology.

### Verdict: RECOMMENDED as supplement

The NDL data is high-quality and massive, but it's titles, not natural sentences. Best used for:
- Dictionary validation
- Coverage testing
- Edge case discovery
- Supplementary training data (if ML approaches are used)

---

## 2. YomujP (日本語多読道場)

**URL:** https://yomujp.com

### Overview
Educational reading platform for Japanese language learners, organized by JLPT levels (N1-N6).

### Data Details
- **Content:** Educational articles, stories, cultural content
- **Quantity:** ~300+ articles across levels (N1: 103, N2-N6 varying amounts)
- **Furigana:** Yes - has furigana ON/OFF toggle (premium feature)
- **Structure:** WordPress-based site with categorized content

### robots.txt Analysis
```
User-agent: *
Disallow: /wp-admin/
Allow: /wp-admin/admin-ajax.php
Sitemap: https://yomujp.com/sitemap.xml
```

Technically allows scraping of content pages, but...

### Legal/Ethical Issues

**Critical Problem:** The site explicitly states in its terms:
> "許可なく転載することを禁じます" (Reproduction without permission prohibited)

**Additional concerns:**
- Premium membership model (YJM メンバー限定 content)
- Paywall for certain features
- Commercial educational business

### Quality Assessment

**Strengths:**
- High-quality educational content
- JLPT-level organization would be useful for difficulty stratification
- Verified furigana (educational focus)

**Weaknesses:**
- Explicit prohibition on reproduction
- Limited quantity (~300 articles)
- Premium content restrictions
- Would require scraping against stated terms

### Verdict: NOT RECOMMENDED

Despite high quality, the explicit terms against reproduction make this source ethically problematic. The limited quantity also doesn't justify the legal risk.

---

## 3. Wayback Machine / Archived NHK Easy

**URL:** https://web.archive.org/web/*/https://www3.nhk.or.jp/news/easy/*

### Overview
The Internet Archive's Wayback Machine may contain historical snapshots of NHK Easy News articles.

### Research Findings

**Unable to directly verify** due to web.archive.org access limitations, but:

- NHK NEWS WEB EASY service started in **February 2013**
- NHK does not maintain historical archives of articles
- Third-party tools like NHKore have scraped and preserved articles

### Potential Benefits
- Would preserve articles that are no longer available on live site
- Same format/quality as current NHK Easy (ruby tags preserved if archived correctly)
- Public archive access is generally legal for research

### Challenges
- Unknown how many articles are archived
- Unknown if ruby tags are preserved in archived HTML
- Would need to verify archive coverage
- Complex scraping (each snapshot is a separate URL)

### Verdict: WORTH INVESTIGATING

If current NHK Easy scraping is blocked or insufficient, the Wayback Machine could be a valuable fallback. Recommend manual investigation of archive.org to determine coverage before investing in a scraper.

---

## 4. Animelon

**URL:** https://animelon.com

### Overview
Anime streaming site with Japanese subtitles designed for language learning.

### Data Details
- **Content:** Anime episodes with multi-format subtitles
- **Subtitle Options:** English, Japanese, Romaji, Hiragana, Katakana
- **Furigana:** Partial (hiragana subtitles alongside kanji subtitles, not inline furigana)

### Legal Status

**Animelon's Disclaimer:**
> "Animelon is a non-profit, educational entity. We do not intend to claim ownership of any anime content on this site nor do we monetize them. All anime content on this website belongs to the studios who created them."

They claim fair use under section 107 of the Copyright Act of 1976.

**Reality:**
- Site operates in a legal gray area
- WaniKani community describes it as "doesn't look very legal"
- No official API or data access
- Third-party tools exist for subtitle extraction (animelon-subtitle-downloader)

### Quality Assessment

**Strengths:**
- Large volume of content
- Natural conversational Japanese (unlike news)
- Multiple reading formats available

**Weaknesses:**
- Not true inline furigana (separate subtitle tracks)
- Legal uncertainty
- No official data access
- Subtitle quality varies
- Would require reverse-engineering their format

### Verdict: NOT RECOMMENDED

The legal gray area of the source content, combined with lack of official data access and non-standard furigana format, makes this unsuitable for a benchmark project. The ethical concerns outweigh the benefits.

---

## 5. NHKore (GitHub Project)

**URL:** https://github.com/esotericpig/nhkore

### Overview
A CLI scraper that extracts word frequency data from NHK News Web Easy, with pre-scraped article archives.

### Data Details
- **Content:** Scraped NHK Easy News articles
- **Format:** CSV, HTML, JSON, YAML exports
- **Furigana:** Yes - extracts kanji with kana from ruby tags
- **License:** LGPL-3.0
- **Status:** Actively maintained (361 commits)

### Available Data
- Pre-scraped data available in releases (nhkore-core.zip)
- "Tons of articles scraped" (exact count not specified)
- Word frequency lists with readings

### Quality Assessment

**Strengths:**
- Same source as our target (NHK Easy)
- Pre-scraped data saves time
- Multiple export formats
- Open source and actively maintained
- Already extracts furigana from ruby tags

**Weaknesses:**
- Unknown total article count
- May not have all historical articles
- Would need format conversion
- Focused on word frequency, not sentence-level annotations

### Verdict: RECOMMENDED as secondary source

This could significantly accelerate data collection. The pre-scraped NHK data is essentially what we're building anyway. Recommend downloading and evaluating the nhkore-core.zip release.

---

## 6. NHK Easier (nhkeasier.com)

**URL:** https://nhkeasier.com

### Overview
Third-party site that aggregates NHK Easy News with enhanced features.

### Features
- Furigana display options (all, hover, none)
- EDICT dictionary integration
- RSS feed available
- EPUB downloads
- Audio downloads

### Data Access
- RSS feed provides structured access
- Not explicitly designed for bulk data extraction
- Disclaimer: "Not affiliated with NHK"

### Verdict: USEFUL FOR REFERENCE

Could potentially use RSS feed for article discovery, but primary scraping should still target NHK directly. Not a data source itself, but a useful tool.

---

## Recommendations

### Primary Strategy
1. **Continue with NHK Easy News scraping** as the primary source (highest quality, verified furigana, natural sentences)

2. **Download and evaluate NDL Huriganacorpus** from Kaggle
   - Provides massive coverage for dictionary validation
   - Government-verified furigana
   - CC-BY-4.0 license is permissive
   - Format conversion is straightforward

3. **Download and evaluate NHKore data**
   - Pre-scraped NHK Easy articles
   - Could bootstrap our dataset quickly
   - Same source quality as direct scraping

### Secondary Strategy (if primary sources insufficient)
4. **Investigate Wayback Machine** for historical NHK Easy articles
   - Manual check of archive coverage first
   - Only pursue if significant coverage exists

### Explicitly NOT Recommended
- **YomujP**: Explicit reproduction prohibition
- **Animelon**: Legal gray area, non-standard format

---

## Action Items

1. [ ] Download Kaggle Huriganacorpus dataset
2. [ ] Analyze NDL data format and sample quality
3. [ ] Download NHKore nhkore-core.zip release
4. [ ] Evaluate NHKore data compatibility with our format
5. [ ] Manual check of Wayback Machine for NHK Easy coverage
6. [ ] Update scraper to optionally use NHKore data as input

---

## Sources

- [Kaggle Huriganacorpus Dataset](https://www.kaggle.com/datasets/iamleonie/huriganacorpus-shosi-dataset)
- [NDL Lab huriganacorpus-ndlbib](https://github.com/ndl-lab/huriganacorpus-ndlbib)
- [NDL Lab huriganacorpus-aozora](https://github.com/ndl-lab/huriganacorpus-aozora)
- [YomujP](https://yomujp.com)
- [NHKore GitHub](https://github.com/esotericpig/nhkore)
- [NHK Easier](https://nhkeasier.com/about/)
- [Animelon About](https://animelon.com/about)
- [yt-dlp Animelon Issue](https://github.com/yt-dlp/yt-dlp/issues/4641)
- [WaniKani Community Discussion](https://community.wanikani.com/t/legal-anime-with-japanese-subtitles/46868)
