//! Baseline furigana annotator using Lindera with IPADIC dictionary.
//!
//! This method tokenizes Japanese text and extracts readings from the dictionary,
//! converting katakana readings to hiragana.

use anyhow::{Context, Result};
use lindera::dictionary::load_dictionary;
use lindera::mode::Mode;
use lindera::segmenter::Segmenter;
use lindera::tokenizer::Tokenizer;
use serde::{Deserialize, Serialize};

/// Token with furigana reading annotation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Token {
    pub surface: String,
    pub reading: String,
    pub start_offset: usize,
    pub end_offset: usize,
    pub confidence: f32,
}

/// Furigana annotator trait (from CLAUDE.md specification).
pub trait FuriganaAnnotator {
    fn annotate(&self, text: &str) -> Result<Vec<Token>>;
    fn name(&self) -> &str;
    fn description(&self) -> &str;
}

/// Baseline annotator using Lindera with IPADIC.
pub struct LinderaAnnotator {
    tokenizer: Tokenizer,
}

impl LinderaAnnotator {
    /// Create a new LinderaAnnotator with embedded IPADIC dictionary.
    pub fn new() -> Result<Self> {
        let dictionary = load_dictionary("embedded://ipadic")
            .context("Failed to load embedded IPADIC dictionary")?;
        let segmenter = Segmenter::new(Mode::Normal, dictionary, None);
        let tokenizer = Tokenizer::new(segmenter);

        Ok(Self { tokenizer })
    }

    /// Convert katakana string to hiragana.
    fn katakana_to_hiragana(text: &str) -> String {
        text.chars()
            .map(|c| {
                // Katakana range: U+30A1 to U+30F6
                // Hiragana range: U+3041 to U+3096
                // Offset: 0x60
                if ('\u{30A1}'..='\u{30F6}').contains(&c) {
                    char::from_u32(c as u32 - 0x60).unwrap_or(c)
                } else if c == '\u{30FC}' {
                    // Long vowel mark (ー) - keep as-is
                    'ー'
                } else {
                    c
                }
            })
            .collect()
    }

    /// Check if text contains any kanji characters.
    fn contains_kanji(text: &str) -> bool {
        text.chars().any(|c| {
            // CJK Unified Ideographs
            ('\u{4E00}'..='\u{9FFF}').contains(&c)
                // CJK Unified Ideographs Extension A
                || ('\u{3400}'..='\u{4DBF}').contains(&c)
                // CJK Compatibility Ideographs
                || ('\u{F900}'..='\u{FAFF}').contains(&c)
        })
    }
}

impl FuriganaAnnotator for LinderaAnnotator {
    fn annotate(&self, text: &str) -> Result<Vec<Token>> {
        let mut tokens = self.tokenizer.tokenize(text)?;
        let mut result = Vec::new();
        let mut offset = 0;

        for token in tokens.iter_mut() {
            let surface = token.surface.to_string();
            let surface_len = surface.chars().count();

            // Get reading from token details
            // IPADIC format: [品詞,品詞細分類1,品詞細分類2,品詞細分類3,活用型,活用形,原形,読み,発音]
            // Reading is at index 7 (if available)
            let details = token.details();
            let reading = if details.len() > 7 && !details[7].is_empty() && details[7] != "*" {
                Self::katakana_to_hiragana(details[7])
            } else {
                // No reading available - use surface form
                surface.clone()
            };

            // Only include tokens that contain kanji (need furigana)
            if Self::contains_kanji(&surface) {
                result.push(Token {
                    surface: surface.clone(),
                    reading,
                    start_offset: offset,
                    end_offset: offset + surface_len,
                    confidence: 1.0, // Dictionary lookup is deterministic
                });
            }

            offset += surface_len;
        }

        Ok(result)
    }

    fn name(&self) -> &str {
        "baseline_lindera"
    }

    fn description(&self) -> &str {
        "Baseline furigana annotator using Lindera with IPADIC dictionary"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_katakana_to_hiragana() {
        assert_eq!(
            LinderaAnnotator::katakana_to_hiragana("ニホンゴ"),
            "にほんご"
        );
        assert_eq!(
            LinderaAnnotator::katakana_to_hiragana("トウキョウ"),
            "とうきょう"
        );
    }

    #[test]
    fn test_contains_kanji() {
        assert!(LinderaAnnotator::contains_kanji("日本語"));
        assert!(LinderaAnnotator::contains_kanji("東京"));
        assert!(!LinderaAnnotator::contains_kanji("ひらがな"));
        assert!(!LinderaAnnotator::contains_kanji("カタカナ"));
        assert!(!LinderaAnnotator::contains_kanji("abc123"));
    }

    #[test]
    fn test_annotate_basic() -> Result<()> {
        let annotator = LinderaAnnotator::new()?;
        let tokens = annotator.annotate("日本語")?;

        assert!(!tokens.is_empty());
        // Should have token for 日本語
        let has_nihongo = tokens.iter().any(|t| t.surface == "日本語");
        assert!(has_nihongo || tokens.iter().any(|t| t.surface.contains("日")));

        Ok(())
    }
}
