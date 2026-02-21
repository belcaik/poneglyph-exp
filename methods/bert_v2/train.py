#!/usr/bin/env python3
"""
Train BERT v2 for dictionary-constrained reading classification.

Architecture: tohoku-nlp/bert-base-japanese-v3
Task: For each kanji span, classify the correct reading among dictionary candidates.
      Uses a global reading vocabulary with dictionary-masked softmax.

Usage:
    python -m methods.bert_v2.train \
        --model tohoku-nlp/bert-base-japanese-v3 \
        --data-dir data/bert_v2_classification \
        --dict-path data/bert_v2_reading_dict.json \
        --output models/bert-furigana-v2 \
        --epochs 10 --batch-size 16 --lr 2e-5 --patience 3
"""

import argparse
import json
import time
import unicodedata
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup

import numpy as np


def find_span_tokens(tokenizer, input_ids, text, span_start, span_end):
    """Find token indices overlapping with character span [span_start, span_end).

    Handles slow tokenizers (no offset_mapping) by manually aligning
    token strings to original text positions, accounting for NFKC normalization.
    """
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    char_pos = 0
    result = []

    for tok_idx, token in enumerate(tokens):
        if token in ("[CLS]", "[SEP]", "[PAD]"):
            continue

        if token == "[UNK]":
            tok_start = char_pos
            # Look ahead to find where the next real token starts
            next_piece = None
            for future_tok in tokens[tok_idx + 1:]:
                if future_tok in ("[CLS]", "[SEP]", "[PAD]", "[UNK]"):
                    continue
                next_piece = future_tok[2:] if future_tok.startswith("##") else future_tok
                break
            if next_piece is not None:
                # Scan forward in text until we find the next piece
                scan_pos = char_pos + 1
                while scan_pos < len(text):
                    norm_remaining = unicodedata.normalize("NFKC", text[scan_pos:scan_pos + len(next_piece)])
                    if norm_remaining == next_piece:
                        break
                    scan_pos += 1
                char_pos = scan_pos
            else:
                char_pos += 1
            tok_end = char_pos
            if tok_start < span_end and tok_end > span_start:
                result.append(tok_idx)
            continue

        piece = token[2:] if token.startswith("##") else token
        tok_start = char_pos

        # Match piece against original text, handling NFKC normalization
        matched = 0
        consumed_chars = 0
        while matched < len(piece) and char_pos + consumed_chars < len(text):
            orig_char = text[char_pos + consumed_chars]
            norm_char = unicodedata.normalize("NFKC", orig_char)
            if piece[matched:matched + len(norm_char)] == norm_char:
                matched += len(norm_char)
                consumed_chars += 1
            else:
                # Mismatch — advance both pointers
                consumed_chars += 1
                matched += 1

        if consumed_chars == 0:
            consumed_chars = 1  # Safety: always advance at least one char

        char_pos += consumed_chars
        tok_end = char_pos

        if tok_start < span_end and tok_end > span_start:
            result.append(tok_idx)

    return result if result else [0]  # Fallback to CLS if nothing found


class ReadingClassificationDataset(Dataset):
    """Dataset for dictionary-constrained reading classification.

    Each item represents a single kanji span within a sentence, with
    candidate readings from the dictionary and a gold label index.
    """

    def __init__(self, data_path: Path, tokenizer, reading_vocab: dict, max_length: int = 256):
        with open(data_path) as f:
            self.data = json.load(f)
        self.tokenizer = tokenizer
        self.reading_vocab = reading_vocab
        self.max_length = max_length
        self.vocab_size = len(reading_vocab)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        text = item["text"]
        span_start = item["span_start"]
        span_end = item["span_end"]
        candidates = item["candidates"]
        gold_index = item["gold_index"]
        gold_reading = item["gold_reading"]

        # Tokenize the full sentence (no offset_mapping — slow tokenizer)
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            truncation=True,
            padding=False,
            return_tensors=None,
        )

        # Find which subword tokens overlap with the kanji span
        span_token_indices = find_span_tokens(
            self.tokenizer, encoding["input_ids"], text, span_start, span_end
        )

        # Build candidate mask over the global reading vocabulary
        # candidate_mask[i] = 1 if reading_vocab index i is a valid candidate
        candidate_mask = torch.zeros(self.vocab_size, dtype=torch.float)
        candidate_vocab_indices = []
        for reading in candidates:
            if reading in self.reading_vocab:
                vid = self.reading_vocab[reading]
                candidate_mask[vid] = 1.0
                candidate_vocab_indices.append(vid)
            else:
                # Reading not in global vocab — use <UNK>
                candidate_mask[0] = 1.0
                candidate_vocab_indices.append(0)

        # Gold label is the global vocab index of the correct reading
        if gold_reading in self.reading_vocab:
            gold_label = self.reading_vocab[gold_reading]
        else:
            gold_label = 0  # <UNK>

        return {
            "input_ids": torch.tensor(encoding["input_ids"]),
            "attention_mask": torch.tensor(encoding["attention_mask"]),
            "span_token_indices": span_token_indices,  # Variable length, collated below
            "candidate_mask": candidate_mask,
            "gold_label": gold_label,
        }


def collate_fn(batch):
    """Custom collate that pads input_ids and handles variable-length span indices."""
    max_len = max(len(item["input_ids"]) for item in batch)

    input_ids = []
    attention_mask = []
    candidate_masks = []
    gold_labels = []

    # For span indices, we need to store them and create a span attention mask
    max_span_len = max(len(item["span_token_indices"]) for item in batch)
    max_span_len = max(max_span_len, 1)  # At least 1 to avoid empty tensors
    span_indices = []
    span_masks = []

    pad_token_id = 0  # Standard BERT pad

    for item in batch:
        # Pad input_ids and attention_mask
        pad_len = max_len - len(item["input_ids"])
        input_ids.append(
            torch.cat([item["input_ids"], torch.full((pad_len,), pad_token_id)])
        )
        attention_mask.append(
            torch.cat([item["attention_mask"], torch.zeros(pad_len, dtype=torch.long)])
        )

        # Pad span indices
        indices = item["span_token_indices"]
        span_pad_len = max_span_len - len(indices)
        span_indices.append(
            torch.tensor(indices + [0] * span_pad_len, dtype=torch.long)
        )
        span_masks.append(
            torch.tensor([1.0] * len(indices) + [0.0] * span_pad_len)
        )

        candidate_masks.append(item["candidate_mask"])
        gold_labels.append(item["gold_label"])

    return {
        "input_ids": torch.stack(input_ids),
        "attention_mask": torch.stack(attention_mask),
        "span_indices": torch.stack(span_indices),
        "span_masks": torch.stack(span_masks),
        "candidate_masks": torch.stack(candidate_masks),
        "gold_labels": torch.tensor(gold_labels, dtype=torch.long),
    }


class BertReadingClassifier(nn.Module):
    """BERT-based model for dictionary-constrained reading classification.

    Architecture:
        Input sentence -> BERT encoder -> hidden states
        For each kanji span:
            1. Mean pool subword tokens overlapping the span
            2. Concatenate with [CLS] token (global context)
            3. Project through linear layer -> logits over global reading vocabulary
            4. Apply dictionary mask (set non-candidate logits to -inf)
            5. CrossEntropyLoss on masked logits
    """

    def __init__(self, bert_model_name: str, reading_vocab_size: int):
        super().__init__()
        self.bert = AutoModel.from_pretrained(bert_model_name)
        hidden_size = self.bert.config.hidden_size  # 768 for bert-base

        # Classification head: [span_repr; cls_repr] -> reading logits
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, reading_vocab_size),
        )

    def forward(self, input_ids, attention_mask, span_indices, span_masks, candidate_masks=None):
        """
        Args:
            input_ids: (batch, seq_len)
            attention_mask: (batch, seq_len)
            span_indices: (batch, max_span_len) - indices into the token sequence
            span_masks: (batch, max_span_len) - 1 for real span tokens, 0 for padding
            candidate_masks: (batch, vocab_size) - 1 for valid candidates, 0 otherwise

        Returns:
            logits: (batch, vocab_size) - masked logits over reading vocabulary
        """
        # BERT forward pass
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        hidden_states = outputs.last_hidden_state  # (batch, seq_len, hidden)

        # Extract [CLS] representation
        cls_repr = hidden_states[:, 0, :]  # (batch, hidden)

        # Mean pool over span tokens
        batch_size = hidden_states.size(0)
        hidden_size = hidden_states.size(2)

        # Gather span token hidden states
        # span_indices: (batch, max_span_len) -> expand to (batch, max_span_len, hidden)
        expanded_indices = span_indices.unsqueeze(-1).expand(-1, -1, hidden_size)
        span_hidden = torch.gather(hidden_states, 1, expanded_indices)  # (batch, max_span_len, hidden)

        # Masked mean pool
        span_masks_expanded = span_masks.unsqueeze(-1)  # (batch, max_span_len, 1)
        span_sum = (span_hidden * span_masks_expanded).sum(dim=1)  # (batch, hidden)
        span_count = span_masks.sum(dim=1, keepdim=True).clamp(min=1)  # (batch, 1)
        span_repr = span_sum / span_count  # (batch, hidden)

        # Concatenate [CLS] and span representation
        combined = torch.cat([span_repr, cls_repr], dim=-1)  # (batch, hidden*2)

        # Classification head
        logits = self.classifier(combined)  # (batch, vocab_size)

        # Apply dictionary mask: set non-candidate logits to -inf
        if candidate_masks is not None:
            logits = logits.masked_fill(candidate_masks == 0, float("-inf"))

        return logits


def evaluate(model, dataloader, device):
    """Evaluate model on a dataset. Returns loss, accuracy, and per-ambiguity stats."""
    model.eval()
    criterion = nn.CrossEntropyLoss()

    total_loss = 0
    total_correct = 0
    total_samples = 0

    # Track accuracy by number of candidates
    ambiguity_stats = {
        "1": {"correct": 0, "total": 0},
        "2": {"correct": 0, "total": 0},
        "3": {"correct": 0, "total": 0},
        "4+": {"correct": 0, "total": 0},
    }

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            span_indices = batch["span_indices"].to(device)
            span_masks = batch["span_masks"].to(device)
            candidate_masks = batch["candidate_masks"].to(device)
            gold_labels = batch["gold_labels"].to(device)

            logits = model(input_ids, attention_mask, span_indices, span_masks, candidate_masks)
            loss = criterion(logits, gold_labels)

            total_loss += loss.item() * input_ids.size(0)
            predictions = logits.argmax(dim=-1)
            correct = (predictions == gold_labels)
            total_correct += correct.sum().item()
            total_samples += input_ids.size(0)

            # Per-ambiguity stats
            n_candidates = candidate_masks.sum(dim=-1).long()  # (batch,)
            for i in range(input_ids.size(0)):
                nc = n_candidates[i].item()
                if nc == 1:
                    key = "1"
                elif nc == 2:
                    key = "2"
                elif nc == 3:
                    key = "3"
                else:
                    key = "4+"
                ambiguity_stats[key]["total"] += 1
                if correct[i].item():
                    ambiguity_stats[key]["correct"] += 1

    avg_loss = total_loss / total_samples if total_samples > 0 else 0
    accuracy = total_correct / total_samples * 100 if total_samples > 0 else 0

    return avg_loss, accuracy, ambiguity_stats


def main():
    parser = argparse.ArgumentParser(description="Train BERT v2 for reading classification")
    parser.add_argument("--model", type=str, default="tohoku-nlp/bert-base-japanese-v3",
                        help="Base model name")
    parser.add_argument("--data-dir", type=Path, default=Path("data/bert_v2_classification"),
                        help="Directory with train.json, val.json, reading_vocab.json")
    parser.add_argument("--dict-path", type=Path, default=Path("data/bert_v2_reading_dict.json"),
                        help="Path to reading dictionary")
    parser.add_argument("--output", type=Path, default=Path("models/bert-furigana-v2"),
                        help="Output directory for model")
    parser.add_argument("--epochs", type=int, default=10,
                        help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16,
                        help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-5,
                        help="Learning rate")
    parser.add_argument("--max-length", type=int, default=256,
                        help="Maximum sequence length in tokens")
    parser.add_argument("--patience", type=int, default=3,
                        help="Early stopping patience")
    parser.add_argument("--gradient-clip", type=float, default=1.0,
                        help="Gradient clipping max norm")
    args = parser.parse_args()

    print("=" * 60)
    print("BERT v2 Training - Dictionary-Constrained Reading Classification")
    print("=" * 60)
    print(f"Base model: {args.model}")
    print(f"Data dir:   {args.data_dir}")
    print(f"Dict path:  {args.dict_path}")
    print(f"Output:     {args.output}")
    print(f"Epochs:     {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print(f"LR:         {args.lr}")
    print(f"Max length: {args.max_length}")
    print(f"Patience:   {args.patience}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device:     {device}")

    # Load reading vocabulary
    vocab_path = args.data_dir / "reading_vocab.json"
    with open(vocab_path) as f:
        reading_vocab = json.load(f)
    vocab_size = len(reading_vocab)
    print(f"\nReading vocabulary: {vocab_size} entries")

    # Load reading dictionary (for saving alongside model)
    with open(args.dict_path) as f:
        reading_dict = json.load(f)

    # Load tokenizer
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    # Create datasets
    print("Creating datasets...")
    train_dataset = ReadingClassificationDataset(
        args.data_dir / "train.json", tokenizer, reading_vocab, args.max_length
    )
    val_dataset = ReadingClassificationDataset(
        args.data_dir / "val.json", tokenizer, reading_vocab, args.max_length
    )
    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples:   {len(val_dataset)}")

    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True,
        collate_fn=collate_fn, num_workers=0, pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size, shuffle=False,
        collate_fn=collate_fn, num_workers=0, pin_memory=True,
    )

    # Create model
    print("Creating model...")
    model = BertReadingClassifier(args.model, vocab_size)
    model.to(device)

    num_params = sum(p.numel() for p in model.parameters())
    bert_params = sum(p.numel() for p in model.bert.parameters())
    head_params = sum(p.numel() for p in model.classifier.parameters())
    print(f"Total parameters:      {num_params:,}")
    print(f"  BERT encoder:        {bert_params:,}")
    print(f"  Classification head: {head_params:,}")

    # Optimizer and scheduler
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.lr, weight_decay=0.01
    )

    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(total_steps * 0.1)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )

    criterion = nn.CrossEntropyLoss()

    print(f"\nTotal training steps: {total_steps}")
    print(f"Warmup steps: {warmup_steps}")

    # Training loop
    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60)

    best_val_accuracy = 0.0
    patience_counter = 0
    log_history = []
    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()
        model.train()
        epoch_loss = 0
        epoch_correct = 0
        epoch_total = 0

        for step, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            span_indices = batch["span_indices"].to(device)
            span_masks = batch["span_masks"].to(device)
            candidate_masks = batch["candidate_masks"].to(device)
            gold_labels = batch["gold_labels"].to(device)

            optimizer.zero_grad()
            logits = model(input_ids, attention_mask, span_indices, span_masks, candidate_masks)
            loss = criterion(logits, gold_labels)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), args.gradient_clip)
            optimizer.step()
            scheduler.step()

            epoch_loss += loss.item() * input_ids.size(0)
            predictions = logits.argmax(dim=-1)
            epoch_correct += (predictions == gold_labels).sum().item()
            epoch_total += input_ids.size(0)

            if (step + 1) % 50 == 0:
                running_acc = epoch_correct / epoch_total * 100
                print(f"  Epoch {epoch} Step {step+1}/{len(train_loader)} "
                      f"Loss: {loss.item():.4f} Acc: {running_acc:.1f}%")

        train_loss = epoch_loss / epoch_total
        train_accuracy = epoch_correct / epoch_total * 100
        epoch_time = time.time() - epoch_start

        # Evaluate
        val_loss, val_accuracy, ambiguity_stats = evaluate(model, val_loader, device)

        epoch_log = {
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "train_accuracy": round(train_accuracy, 1),
            "eval_loss": round(val_loss, 4),
            "eval_accuracy": round(val_accuracy, 1),
            "ambiguity_stats": {
                k: {
                    "accuracy": round(v["correct"] / v["total"] * 100, 1) if v["total"] > 0 else 0,
                    "correct": v["correct"],
                    "total": v["total"],
                }
                for k, v in ambiguity_stats.items()
            },
            "epoch_time_seconds": round(epoch_time, 1),
            "learning_rate": scheduler.get_last_lr()[0],
        }
        log_history.append(epoch_log)

        print(f"\nEpoch {epoch}/{args.epochs}:")
        print(f"  Train Loss: {train_loss:.4f}  Train Acc: {train_accuracy:.1f}%")
        print(f"  Val Loss:   {val_loss:.4f}  Val Acc:   {val_accuracy:.1f}%")
        print(f"  Time: {epoch_time:.1f}s")
        print(f"  Val accuracy by ambiguity:")
        for k, v in ambiguity_stats.items():
            acc = v["correct"] / v["total"] * 100 if v["total"] > 0 else 0
            print(f"    {k} candidates: {acc:.1f}% ({v['correct']}/{v['total']})")

        # Early stopping on val accuracy
        if val_accuracy > best_val_accuracy:
            best_val_accuracy = val_accuracy
            patience_counter = 0

            # Save best model
            args.output.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), args.output / "model.pt")
            tokenizer.save_pretrained(str(args.output))

            # Save reading vocab and dict alongside model
            import shutil
            shutil.copy(vocab_path, args.output / "reading_vocab.json")
            shutil.copy(args.dict_path, args.output / "reading_dict.json")

            # Save model config
            model_config = {
                "base_model": args.model,
                "reading_vocab_size": vocab_size,
                "hidden_size": model.bert.config.hidden_size,
            }
            with open(args.output / "model_config.json", "w") as f:
                json.dump(model_config, f, indent=2)

            print(f"  -> New best! Saved to {args.output}")
        else:
            patience_counter += 1
            print(f"  -> No improvement (patience {patience_counter}/{args.patience})")
            if patience_counter >= args.patience:
                print(f"\nEarly stopping at epoch {epoch}")
                break

    training_time = time.time() - start_time

    # Save training log
    training_log = {
        "version": "bert_v2",
        "base_model": args.model,
        "config": {
            "epochs_requested": args.epochs,
            "epochs_completed": epoch,
            "batch_size": args.batch_size,
            "learning_rate": args.lr,
            "max_length": args.max_length,
            "early_stopping_patience": args.patience,
            "gradient_clip": args.gradient_clip,
            "reading_vocab_size": vocab_size,
        },
        "data": {
            "train_samples": len(train_dataset),
            "val_samples": len(val_dataset),
        },
        "model_info": {
            "parameters": num_params,
            "bert_parameters": bert_params,
            "head_parameters": head_params,
        },
        "results": {
            "training_time_seconds": round(training_time, 2),
            "training_time_minutes": round(training_time / 60, 2),
            "best_val_accuracy": round(best_val_accuracy, 1),
            "best_epoch": epoch - patience_counter if patience_counter >= args.patience else epoch,
        },
        "log_history": log_history,
    }

    # Save to both method dir and results dir
    log_path = Path("methods/bert_v2/training_log.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(training_log, f, indent=2)
    print(f"\nTraining log saved to: {log_path}")

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    results_log_path = results_dir / "bert_v2_training_log.json"
    with open(results_log_path, "w") as f:
        json.dump(training_log, f, indent=2)
    print(f"Training log also saved to: {results_log_path}")

    print("\n" + "=" * 60)
    print("Training complete!")
    print(f"Model saved to: {args.output}")
    print(f"Training time: {training_time / 60:.1f} minutes")
    print(f"Best validation accuracy: {best_val_accuracy:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
