//! CLI for baseline Lindera furigana annotator.
//!
//! Usage:
//!   cargo run --release -p baseline_lindera -- --input data/splits/test.json

use anyhow::{Context, Result};
use baseline_lindera::{FuriganaAnnotator, LinderaAnnotator};
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "baseline_lindera")]
#[command(about = "Baseline furigana annotator using Lindera")]
struct Args {
    /// Input JSON file with test sentences
    #[arg(short, long)]
    input: PathBuf,

    /// Output JSON file for predictions (optional)
    #[arg(short, long)]
    output: Option<PathBuf>,

    /// Number of sentences to process (0 = all)
    #[arg(short, long, default_value = "0")]
    limit: usize,

    /// Show comparison with ground truth
    #[arg(long)]
    compare: bool,
}

/// Ground truth token from NHK data.
#[derive(Debug, Deserialize)]
struct GroundTruthToken {
    surface: String,
    reading: String,
}

/// Sentence from the test data.
#[derive(Debug, Deserialize)]
struct Sentence {
    text: String,
    tokens: Vec<GroundTruthToken>,
}

/// Output prediction for a sentence.
#[derive(Debug, Serialize)]
struct Prediction {
    text: String,
    ground_truth: Vec<TokenOutput>,
    predicted: Vec<TokenOutput>,
}

#[derive(Debug, Serialize)]
struct TokenOutput {
    surface: String,
    reading: String,
}

fn main() -> Result<()> {
    let args = Args::parse();

    // Load test data
    let data = fs::read_to_string(&args.input)
        .with_context(|| format!("Failed to read input file: {:?}", args.input))?;
    let sentences: Vec<Sentence> =
        serde_json::from_str(&data).context("Failed to parse input JSON")?;

    println!("Loaded {} sentences from {:?}", sentences.len(), args.input);

    // Initialize annotator
    println!("Initializing Lindera annotator...");
    let annotator = LinderaAnnotator::new()?;
    println!("Annotator ready: {}", annotator.name());

    // Process sentences
    let limit = if args.limit > 0 {
        args.limit.min(sentences.len())
    } else {
        sentences.len()
    };

    let mut predictions = Vec::new();
    let mut total_gt_tokens = 0;
    let mut total_pred_tokens = 0;
    let mut exact_matches = 0;

    println!("\nProcessing {} sentences...\n", limit);

    for (i, sentence) in sentences.iter().take(limit).enumerate() {
        let pred_tokens = annotator.annotate(&sentence.text)?;

        // Compare with ground truth
        let gt_tokens: Vec<TokenOutput> = sentence
            .tokens
            .iter()
            .map(|t| TokenOutput {
                surface: t.surface.clone(),
                reading: t.reading.clone(),
            })
            .collect();

        let pred_output: Vec<TokenOutput> = pred_tokens
            .iter()
            .map(|t| TokenOutput {
                surface: t.surface.clone(),
                reading: t.reading.clone(),
            })
            .collect();

        // Count matches
        total_gt_tokens += gt_tokens.len();
        total_pred_tokens += pred_output.len();

        for gt in &gt_tokens {
            if pred_output
                .iter()
                .any(|p| p.surface == gt.surface && p.reading == gt.reading)
            {
                exact_matches += 1;
            }
        }

        if args.compare && i < 10 {
            println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            // Truncate at char boundary
            let display_text: String = sentence.text.chars().take(50).collect();
            println!("Sentence {}: {}...", i + 1, display_text);
            println!("\nGround Truth:");
            for t in &gt_tokens {
                println!("  {} → {}", t.surface, t.reading);
            }
            println!("\nPredicted:");
            for t in &pred_output {
                let match_status = if gt_tokens
                    .iter()
                    .any(|g| g.surface == t.surface && g.reading == t.reading)
                {
                    "✓"
                } else if gt_tokens.iter().any(|g| g.surface == t.surface) {
                    "✗ (wrong reading)"
                } else {
                    "? (extra)"
                };
                println!("  {} → {} {}", t.surface, t.reading, match_status);
            }
            println!();
        }

        predictions.push(Prediction {
            text: sentence.text.clone(),
            ground_truth: gt_tokens,
            predicted: pred_output,
        });
    }

    // Summary statistics
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("SUMMARY");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("Sentences processed: {}", limit);
    println!("Ground truth tokens: {}", total_gt_tokens);
    println!("Predicted tokens:    {}", total_pred_tokens);
    println!("Exact matches:       {}", exact_matches);
    if total_gt_tokens > 0 {
        let accuracy = exact_matches as f64 / total_gt_tokens as f64 * 100.0;
        println!("Token accuracy:      {:.1}%", accuracy);
    }

    // Save output if requested
    if let Some(output_path) = args.output {
        let output_json = serde_json::to_string_pretty(&predictions)?;
        fs::write(&output_path, output_json)?;
        println!("\nPredictions saved to {:?}", output_path);
    }

    Ok(())
}
