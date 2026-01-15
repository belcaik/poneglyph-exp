# Japanese furigana annotation: A technical specification for comparative evaluation

Japanese reading annotation presents a deceptively difficult challenge: determining correct furigana for expressions like "2人目" (ふたりめ, "second person") when morphological analyzers systematically produce incorrect readings like "ひとめ." This specification outlines an experimentation repository comparing three approaches—classical Viterbi/dictionary methods, fine-tuned small LLMs, and custom ML models—to solve this problem with measurable accuracy, latency, and resource metrics.

The core technical problem stems from Japanese counter words (助数詞) having **irregular readings** that break standard tokenization. MeCab and similar tools tokenize "2人目" as `2 + 人 + 目`, assigning individual readings (ニ + ニン + メ) rather than recognizing the compound pattern requiring native Japanese numerals (ふたり + め). This specification provides everything needed to build, benchmark, and compare solutions.

---

## Classical Viterbi morphological analyzers: The baseline

The **Viterbi algorithm** finds minimum-cost paths through word lattices using Conditional Random Fields for parameter estimation. MeCab remains the gold standard at **~0.095 seconds per 100 iterations** on typical sentences, with Vibrato (Rust) achieving **1.5-2x faster performance** for large dictionaries like UniDic 3.1.1.

### Primary tools and architecture details

| Analyzer | Language | Repository | Speed | Dictionary Support |
|----------|----------|------------|-------|-------------------|
| **MeCab** | C++ | github.com/taku910/mecab | Fastest (baseline) | IPAdic, UniDic, NEologd |
| **Vibrato** | Rust | github.com/daac-tools/vibrato | 1.5x MeCab | MeCab-compatible, compressed models |
| **lindera** | Rust | github.com/lindera/lindera | Good | IPAdic, UniDic, user dictionaries |
| **Sudachi** | Java/Rust | github.com/WorksApplications/sudachi.rs | ~40x slower than MeCab (Python) | Own dictionary, A/B/C modes |
| **Kagome** | Go | github.com/ikawaha/kagome | Moderate | IPAdic, UniDic, WASM support |

All these analyzers share a fundamental limitation: **dictionary-stored readings don't capture numerical expression irregularities**. The counter word "人" stores reading "ニン" (Sino-Japanese), while native readings (ひとり, ふたり) exist as separate lexical entries that aren't triggered when preceded by Arabic numerals.

### Dictionary systems and their reading data

**IPAdic** (frozen at 2.7.0) stores readings in katakana format: `人,1285,1285,5463,名詞,接尾,助数詞,*,*,*,人,ニン,ニン`. The pronunciation field enables systems to distinguish orthographic reading from actual pronunciation (e.g., は reading ハ, pronunciation ワ).

**UniDic** (actively maintained by NINJAL) provides finer-grained tokenization with a **459 MiB connection matrix** in version 3.1.1. It follows Short Unit Word principles for reproducible annotation but doesn't solve the counter word problem—only shifts where tokenization boundaries fall.

**NEologd** addresses some numerical expressions through exhaustive enumeration: "8月3日" → "ハチガツミッカ" stored as single entries. However, this approach doesn't scale to arbitrary number+counter combinations like "47人目" or "183日目."

### Counter word problem mechanics

Japanese counters follow complex patterns mixing Sino-Japanese (音読み) and native (訓読み) number systems:

| Number + 人 | Correct Reading | MeCab Output | Error Type |
|-------------|-----------------|--------------|------------|
| 1人 | ひとり | いちにん | Wrong numeral system |
| 2人 | ふたり | ににん | Wrong numeral system |
| 3人 | さんにん | さんにん | ✓ Correct |
| 1日 (date) | ついたち | いちにち | Context-dependent |
| 2日 | ふつか | ににち | Irregular pattern |
| 20日 | はつか | にじゅうにち | Highly irregular |

The problem compounds with suffixes: "2人目" requires recognizing that 人 takes native counting when followed by 目, producing ふたりめ rather than the default ににんめ.

### Implementation approach for classical baseline

```rust
// Vibrato-based implementation structure
use vibrato::{Dictionary, Tokenizer};

struct ClassicalFuriganaAnnotator {
    tokenizer: Tokenizer,
    counter_rules: CounterRuleEngine,  // Post-processing layer
    jukujikun_dict: HashMap<String, String>,  // 熟字訓 lookup
}

impl ClassicalFuriganaAnnotator {
    fn annotate(&self, text: &str) -> Vec<(String, String)> {
        let tokens = self.tokenizer.tokenize(text);
        let mut results = Vec::new();
        
        for window in tokens.windows(3) {
            if self.counter_rules.matches(&window) {
                // Apply counter word reading rules
                results.push(self.counter_rules.apply(&window));
            } else if let Some(reading) = self.jukujikun_dict.get(&combined_surface) {
                // Jukujikun override
                results.push((combined_surface, reading.clone()));
            } else {
                // Default tokenizer reading
                results.extend(window.iter().map(|t| (t.surface(), t.reading())));
            }
        }
        results
    }
}
```

The **counter rule engine** must encode approximately **300+ specific patterns** covering 人 (1-10 + tens), 日 (1-31 dates + duration contexts), 本/匹/個/回/階 with their phonological transformations (rendaku, sokuon insertion).

---

## Small LLM fine-tuning: Transformer-based reading prediction

Japanese transformer models enable framing furigana generation as **token classification**: each input character maps to a reading label. The cl-tohoku BERT models trained on CC-100 (74.3GB) provide strong Japanese understanding baselines.

### Recommended models for experimentation

| Model | Parameters | Tokenization | Inference (GPU) | Best For |
|-------|-----------|--------------|-----------------|----------|
| **bert-base-japanese-char-v3** | 110M | Character-level | ~2.2ms batch=1 | Accuracy testing |
| **DistilBERT-base-jp** | 66M | WordPiece+MeCab | ~15ms CPU | Production deployment |
| **deberta-v2-tiny-japanese** | ~30M | SentencePiece | Fast | Mobile/edge |
| **deberta-v2-large-japanese-char-wwm** | 340M | Character-level | GPU required | Maximum accuracy |
| **rinna/japanese-gpt2-xsmall** | 45M | SentencePiece | Lightweight | No MeCab dependency |

**Character-level tokenization** (bert-base-japanese-char-v3) is strongly recommended for reading tasks because it avoids subword alignment problems. Each kanji character directly maps to hiragana output without needing to decompose subwords.

### Fine-tuning architecture

The task frames as **sequence labeling** where each input character predicts its reading character(s):

```python
# Token classification approach
from transformers import AutoModelForTokenClassification, AutoTokenizer

class FuriganaTransformer:
    def __init__(self, model_name="tohoku-nlp/bert-base-japanese-char-v3"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        # Output vocabulary: ~100 hiragana + special tokens
        self.model = AutoModelForTokenClassification.from_pretrained(
            model_name,
            num_labels=len(HIRAGANA_VOCAB)
        )
    
    def predict(self, text: str) -> List[str]:
        inputs = self.tokenizer(text, return_tensors="pt")
        outputs = self.model(**inputs)
        predictions = outputs.logits.argmax(dim=-1)
        return [HIRAGANA_VOCAB[p] for p in predictions[0]]
```

Adding a **CRF layer** on top of BERT captures label transition constraints—valid hiragana sequences—improving accuracy on limited training data by **2-5 percentage points** based on sequence labeling literature.

### Inference optimization pipeline

Real-time subtitle annotation requires **<100ms latency**. The optimization path:

1. **ONNX Export**: `optimum-cli export onnx -m tohoku-nlp/bert-base-japanese-char-v3 --optimize O2`
2. **INT8 Quantization**: 4x size reduction (417MB → ~105MB), 2-3x speedup on CPU with VNNI
3. **Graph Optimization**: Operator fusion, symbolic shape inference
4. **Batch=1 Inference**: Lowest per-request latency for real-time use

Expected latencies after optimization:
- GPU (T4 with TensorRT): **2.2ms** for 128-character input
- CPU (optimized DistilBERT): **15-25ms** for 128-character input
- CPU (BERT-base quantized): **40-70ms** for 128-character input

### Training data requirements

| Complexity | Minimum Examples | Recommended | Expected Accuracy |
|------------|------------------|-------------|-------------------|
| Basic fine-tuning | 5,000-10,000 | 50,000+ | 90-93% |
| Counter word handling | 10,000+ | 100,000+ | 93-96% |
| Production quality | 100,000+ | 500,000+ | 96-98% |

Training configuration for fine-tuning:
```yaml
learning_rate: 2e-5
batch_size: 32
epochs: 5
warmup_ratio: 0.1
weight_decay: 0.01
max_seq_length: 256
fp16: true
```

---

## Custom ML model with embeddings: Architecture specification

A purpose-built model can exploit **Japanese-specific features** unavailable in generic transformers: radical decomposition, position-aware embeddings, and pointer-generator mechanisms for copying unchanged hiragana/katakana.

### Proposed architecture: FuriganaNet

```
┌─────────────────────────────────────────────────────┐
│                  INPUT LAYER                        │
│  Kanji/Kana sequence (batch, seq_len)               │
└─────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────┐
│                EMBEDDING FUSION                     │
│  • Character embedding (256 dim)                    │
│  • Radical embedding (128 dim) - kanji only         │
│  • Script-type embedding (8 dim) - kanji/hira/kata  │
│  • Position encoding (sinusoidal)                   │
│  → Concatenate → Linear → 384 dim                   │
└─────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────┐
│                   ENCODER                           │
│  Option A: BiLSTM (2 layers, 256 units) - 5-10M     │
│  Option B: Transformer (4 layers, 4 heads) - 10-15M │
│  + Residual connections + LayerNorm                 │
└─────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────┐
│                   DECODER                           │
│  • Autoregressive generation (2-4 layers)           │
│  • Pointer-generator for copying                    │
│  • Coverage mechanism for jukujikun                 │
└─────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────┐
│                   OUTPUT                            │
│  • Hiragana vocabulary softmax (~100 tokens)        │
│  • Copy distribution over input                     │
│  • p_gen: probability of generate vs copy           │
└─────────────────────────────────────────────────────┘
```

### Radical embeddings for kanji

Decomposing kanji into radicals (部首) captures morphological patterns. Using **KanjiVG** or **KRADFILE**, 亻 + 中 compose 仲, sharing semantic features with other 亻-component kanji.

```python
class RadicalEmbedding(nn.Module):
    def __init__(self, radical_vocab_size=214, embed_dim=128):
        super().__init__()
        self.radical_embed = nn.Embedding(radical_vocab_size, embed_dim)
        self.reducer = nn.Linear(embed_dim * MAX_RADICALS, embed_dim)
    
    def forward(self, kanji_radicals):
        # kanji_radicals: (batch, seq_len, max_radicals)
        embedded = self.radical_embed(kanji_radicals)  # (B, S, R, E)
        return self.reducer(embedded.flatten(-2))  # (B, S, E)
```

### Pointer-generator for script handling

Japanese text mixes scripts: kanji require reading generation, but **hiragana and katakana should copy unchanged**. The pointer-generator mechanism (See et al., 2017) learns when to generate versus copy:

```python
def pointer_generator_step(self, decoder_hidden, encoder_outputs, input_tokens):
    # Generation probability
    p_gen = torch.sigmoid(
        self.W_h(decoder_hidden) + 
        self.W_s(context_vector) + 
        self.W_x(decoder_input)
    )
    
    # Final distribution
    vocab_dist = self.softmax(self.vocab_proj(decoder_hidden))
    copy_dist = attention_weights  # Distribution over input positions
    
    final_dist = p_gen * vocab_dist + (1 - p_gen) * copy_dist
    return final_dist
```

### Training approach

**Hybrid pipeline** recommended for production:
1. MeCab tokenization for word boundaries and POS tags
2. Dictionary lookup for known words and jukujikun
3. Neural model for unknown/ambiguous cases only
4. Post-processing rules for rendaku (連濁) patterns

This approach focuses neural capacity on hard cases while leveraging existing high-quality dictionaries.

---

## Training data and corpora: A comprehensive catalog

### Primary training sources

**BCCWJ (Balanced Corpus of Contemporary Written Japanese)** provides the gold standard: **104.3 million words** with professional morphological annotation including readings. Access requires registration via NINJAL's Chunagon interface; the DVD edition enables offline training.

**Aozora Bunko** offers **15,500+ public domain literary works** with human-annotated furigana in ruby format. The custom markup `漢字《かんじ》` can be programmatically extracted. This corpus covers classical to modern Japanese but skews literary.

**JMDict** contains **214,000+ dictionary entries** with 314,000+ headword-reading combinations. The **JmdictFurigana project** (github.com/Doublevil/JmdictFurigana) provides character-aligned furigana mappings updated monthly.

| Source | Size | Readings | Access | License |
|--------|------|----------|--------|---------|
| BCCWJ | 104M words | ✓ Professional | NINJAL registration | Research free |
| Aozora Bunko | 15K+ works | ✓ Ruby markup | Direct download | Public domain |
| JMDict | 214K entries | ✓ Dictionary | Free download | CC BY-SA 4.0 |
| NHK News Easy | Thousands of articles | ✓ HTML ruby | Web scraping | Copyright (personal use) |
| KWDLC | 15K sentences | ✓ Morphological | GitHub | Academic |
| CSJ | 7.5M words | ✓ Phonetic | ELRA license | Research |

### Counter word dataset creation

**No existing benchmark specifically targets counter word readings.** The repository must create a dedicated test set:

```yaml
counter_benchmark:
  人_counter:  # 30+ examples
    - {text: "1人", reading: "ひとり", type: "irregular"}
    - {text: "2人", reading: "ふたり", type: "irregular"}
    - {text: "3人", reading: "さんにん", type: "regular"}
    - {text: "2人目", reading: "ふたりめ", type: "compound_irregular"}
    
  日_counter:  # 62 examples (1-31 dates + duration)
    - {text: "1日", reading: "ついたち", context: "date"}
    - {text: "1日", reading: "いちにち", context: "duration"}
    - {text: "2日", reading: "ふつか", type: "irregular"}
    - {text: "20日", reading: "はつか", type: "highly_irregular"}
    
  本_counter:  # 30 examples with sound changes
    - {text: "1本", reading: "いっぽん", change: "h→p"}
    - {text: "3本", reading: "さんぼん", change: "h→b"}
    - {text: "6本", reading: "ろっぽん", change: "h→p"}
```

Total minimum counter benchmark: **~300 examples** covering 人, 日, 本, 匹, 個, 回, 階, 枚, 歳.

---

## Benchmarking methodology: Metrics and measurement

### Accuracy metrics specification

**Character Error Rate (CER)** measures Levenshtein distance at character level:
```
CER = (Substitutions + Deletions + Insertions) / Reference_Length
```

Target: **<5% CER** for production systems. MeCab baseline typically achieves 3-8% CER depending on domain.

**Multiple valid readings** require special handling. 明日 accepts three readings (あした, あす, みょうにち) depending on formality. The evaluation system must implement **acceptable set matching**:

```python
def multi_reading_accuracy(prediction: str, acceptable: List[str]) -> float:
    return 1.0 if prediction in acceptable else 0.0
```

### Counter word evaluation protocol

Dedicated scoring for the **300-example counter benchmark** with weighted error categories:

| Error Type | Weight | Example |
|------------|--------|---------|
| Wrong numeral system | 2.0 | ふたり → ににん |
| Missing sound change | 1.5 | いっぽん → いちほん |
| Context error | 1.5 | ついたち → いちにち |
| Regular reading error | 1.0 | さんにん → さにん |

Report **Counter Word Accuracy (CWA)** separately from overall accuracy to highlight the specific problem addressed.

### Latency measurement protocol

```python
import time
import numpy as np

def benchmark_latency(model, inputs, warmup=10, iterations=1000):
    # Warm-up phase (critical for GPU/JIT)
    for _ in range(warmup):
        _ = model.predict(inputs)
    
    latencies = []
    for _ in range(iterations):
        start = time.perf_counter()
        _ = model.predict(inputs)
        end = time.perf_counter()
        latencies.append((end - start) * 1000)  # ms
    
    return {
        'p50': np.percentile(latencies, 50),
        'p95': np.percentile(latencies, 95),
        'p99': np.percentile(latencies, 99),
        'mean': np.mean(latencies),
        'std': np.std(latencies)
    }
```

Input configurations for benchmarking:
- Lengths: 10, 50, 100, 500 characters
- Batch sizes: 1, 8, 16, 32
- Report both **model-only** and **end-to-end** (including tokenization) latency

### Compute resource measurement

```python
import torch
from torch.profiler import profile, ProfilerActivity

def measure_resources(model, inputs):
    # GPU memory
    torch.cuda.reset_peak_memory_stats()
    _ = model.predict(inputs)
    gpu_peak = torch.cuda.max_memory_allocated() / 1e9  # GB
    
    # CPU profiling
    with profile(activities=[ProfilerActivity.CPU], profile_memory=True) as prof:
        _ = model.predict(inputs)
    cpu_memory = prof.key_averages()[0].self_cpu_memory_usage / 1e9  # GB
    
    return {'gpu_peak_gb': gpu_peak, 'cpu_memory_gb': cpu_memory}
```

### Statistical validity requirements

- **Bootstrap confidence intervals** (1,000 iterations) for all accuracy metrics
- **Sample size**: Minimum 5,000 sentences in test set, 300+ counter examples
- **Stratification**: By text domain, difficulty level, counter word presence
- **Significance testing**: McNemar's test for paired system comparison

---

## Competitor technology analysis: What exists and why it fails

### Language Reactor
Uses external translation services without specialized reading technology. Limited to video content with no evidence of MeCab or morphological analysis integration. Reading accuracy depends entirely on source subtitle quality.

### Yomichan/Yomitan
Pure **dictionary-based lookup** from JMdict with no contextual disambiguation. Shows all possible readings, requiring user selection. Counter words handled only if explicitly enumerated in dictionary entries. **Cannot determine which reading applies** in ambiguous cases.

### Migaku
Uses **MeCab via mecab_controller** with acknowledged limitations: "Mecab is not perfect and sometimes generates incorrect readings. There's nothing that can be done about it." No disambiguation layer or counter word specialization.

### Google Japanese Input (Mozc)
Sophisticated system combining MeCab, **N-gram language models**, and **neural language models** for contextual prediction. However, it solves the reverse problem (kana → kanji input), not reading annotation.

### Critical gap: Counter word handling

Explicit acknowledgment across tools:
> "⚠️ Note that mecab does not handle very well the irregular reading like 二人(ふたり) or 一回(いっかい) and may produce incorrect readings."

This systematic failure creates the opportunity this repository addresses.

---

## Repository structure and experimentation plan

### Proposed directory structure

```
furigana-benchmark/
├── data/
│   ├── counter_benchmark.yaml     # 300+ counter word test cases
│   ├── jukujikun_dict.json        # 熟字訓 special readings
│   ├── test_sentences.jsonl       # 5,000+ evaluation sentences
│   └── scripts/
│       ├── download_bccwj.py
│       ├── parse_aozora.py
│       └── extract_jmdict_furigana.py
│
├── baselines/
│   ├── classical/
│   │   ├── vibrato_annotator.rs   # Rust Vibrato implementation
│   │   ├── counter_rules.rs       # Counter word post-processing
│   │   └── mecab_baseline.py      # Python MeCab wrapper
│   │
│   ├── transformer/
│   │   ├── train_bert_reading.py  # Fine-tuning script
│   │   ├── inference.py           # Optimized inference
│   │   └── export_onnx.py         # ONNX conversion
│   │
│   └── custom_ml/
│       ├── model.py               # FuriganaNet architecture
│       ├── radical_embeddings.py  # Kanji decomposition
│       └── pointer_generator.py   # Copy mechanism
│
├── evaluation/
│   ├── metrics.py                 # CER, WER, CWA implementations
│   ├── benchmark_runner.py        # Automated evaluation pipeline
│   ├── latency_profiler.py        # Timing measurements
│   └── resource_monitor.py        # Memory/GPU tracking
│
├── visualization/
│   ├── accuracy_comparison.py     # Comparative bar charts
│   ├── latency_heatmap.py         # Input length × batch size
│   └── resource_radar.py          # Multi-axis resource comparison
│
└── reports/
    └── template.md                # Standardized reporting format
```

### Comparative graphics specification

**1. Accuracy Comparison Bar Chart**
- X-axis: Three approaches (Classical, Transformer, Custom ML)
- Y-axis: Accuracy percentage
- Grouped bars: Overall accuracy, Counter Word Accuracy, Jukujikun Accuracy
- Error bars: 95% confidence intervals

**2. Latency vs Accuracy Scatter Plot**
- X-axis: p95 latency (ms, log scale)
- Y-axis: Counter Word Accuracy (%)
- Point size: Model parameter count
- Color: Approach category

**3. Resource Radar Chart**
- Axes: GPU Memory, CPU Memory, Latency, Accuracy, Counter Accuracy
- Overlaid polygons for each approach
- Normalized 0-100 scale

**4. Counter Word Confusion Matrix**
- Rows: True readings (ひとり, ふたり, さんにん...)
- Columns: Predicted readings
- Heatmap intensity: Error frequency

### Experiment execution plan

**Phase 1: Data preparation (Week 1-2)**
- Download and process BCCWJ (requires NINJAL registration)
- Parse Aozora Bunko furigana annotations
- Create 300+ counter word benchmark
- Build jukujikun dictionary from JMDict

**Phase 2: Baseline implementation (Week 3-4)**
- Vibrato/MeCab baseline with counter rule post-processing
- Fine-tune bert-base-japanese-char-v3 on reading task
- Implement FuriganaNet architecture with radical embeddings

**Phase 3: Evaluation (Week 5-6)**
- Run all models on test set and counter benchmark
- Measure latency across input configurations
- Profile resource utilization
- Generate comparative visualizations

**Phase 4: Analysis and optimization (Week 7-8)**
- Error analysis on counter word failures
- Ablation studies (CRF layer, radical embeddings, pointer mechanism)
- Quantization and optimization for production deployment

---

## Conclusion: A path toward accurate Japanese reading annotation

The counter word problem exemplifies a broader challenge in Japanese NLP: **rule-based systems lack the flexibility to handle irregular patterns, while neural systems lack the inductive bias to learn them from limited examples**. The most promising approach combines both paradigms.

The classical Viterbi baseline provides **fast, reliable tokenization** with explicit rules for known counter patterns. Transformer models offer **context-dependent disambiguation** but require substantial training data and careful optimization for real-time use. Custom architectures with radical embeddings and pointer-generators may achieve the best accuracy by encoding Japanese-specific linguistic knowledge directly.

This repository will produce concrete, reproducible benchmarks demonstrating which approach—or combination—best solves the "2人目 → ふたりめ" problem and similar reading challenges. Success metrics target **>95% Counter Word Accuracy** with **<100ms p95 latency** for subtitle annotation applications.