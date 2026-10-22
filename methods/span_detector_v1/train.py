#!/usr/bin/env python3
"""
Train BERT-based BIO tagger for morpheme span detection.

Architecture: tohoku-nlp/bert-base-japanese-v3 + Linear(768, 3) token classification head
Task: For each subword token, predict B-SPAN / I-SPAN / O

Character-level labels are aligned to subword tokens:
- If any character in a token's span is B-SPAN, the token gets B-SPAN
- If any character in a token's span is I-SPAN (and none are B-SPAN), the token gets I-SPAN
- Special tokens ([CLS], [SEP], [PAD]) get label -100 (ignored in loss)

Usage:
    python -m methods.span_detector_v1.train \
        --data-dir data/span_detector_v1 \
        --output models/span-detector-v1 \
        --epochs 15 --batch-size 16 --lr 2e-5 --patience 5
"""

import argparse
import json
import time
import unicodedata
from collections import Counter
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup

# Labels
LABEL_O = 0
LABEL_B = 1
LABEL_I = 2
NUM_LABELS = 3
IGNORE_INDEX = -100


def align_char_labels_to_tokens(tokenizer, input_ids: list[int], text: str,
                                char_labels: list[int]) -> list[int]:
    """Align character-level BIO labels to subword token labels.

    For each subword token, determine which characters it covers,
    then assign the token label based on the characters' labels:
    - If any character is B-SPAN -> token is B-SPAN
    - Else if any character is I-SPAN -> token is I-SPAN
    - Else -> token is O
    - Special tokens -> IGNORE_INDEX (-100)
    """
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    token_labels = []
    char_pos = 0

    for tok_idx, token in enumerate(tokens):
        if token in ("[CLS]", "[SEP]", "[PAD]"):
            token_labels.append(IGNORE_INDEX)
            continue

        if token == "[UNK]":
            # UNK token — consume one character
            if char_pos < len(char_labels):
                token_labels.append(char_labels[char_pos])
                char_pos += 1
            else:
                token_labels.append(IGNORE_INDEX)
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
                consumed_chars += 1
                matched += 1

        if consumed_chars == 0:
            consumed_chars = 1

        # Determine token label from the characters it covers
        char_end = min(char_pos + consumed_chars, len(char_labels))
        covered_labels = char_labels[char_pos:char_end]

        if not covered_labels:
            token_labels.append(LABEL_O)
        elif LABEL_B in covered_labels:
            token_labels.append(LABEL_B)
        elif LABEL_I in covered_labels:
            token_labels.append(LABEL_I)
        else:
            token_labels.append(LABEL_O)

        char_pos += consumed_chars

    return token_labels


class SpanDetectionDataset(Dataset):
    """Dataset for character-level BIO span detection."""

    def __init__(self, data_path: Path, tokenizer, max_length: int = 256):
        with open(data_path) as f:
            self.data = json.load(f)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = item["text"]
        char_labels = item["char_labels"]

        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            truncation=True,
            padding=False,
            return_tensors=None,
        )

        input_ids = encoding["input_ids"]
        attention_mask = encoding["attention_mask"]

        # Align character labels to token labels
        token_labels = align_char_labels_to_tokens(
            self.tokenizer, input_ids, text, char_labels
        )

        # Truncate labels to match input_ids length (in case of mismatch)
        if len(token_labels) > len(input_ids):
            token_labels = token_labels[:len(input_ids)]
        elif len(token_labels) < len(input_ids):
            token_labels.extend([IGNORE_INDEX] * (len(input_ids) - len(token_labels)))

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(token_labels, dtype=torch.long),
        }


def collate_fn(batch):
    """Pad batch to max sequence length."""
    max_len = max(len(item["input_ids"]) for item in batch)

    input_ids = []
    attention_mask = []
    labels = []

    for item in batch:
        pad_len = max_len - len(item["input_ids"])
        input_ids.append(
            torch.cat([item["input_ids"], torch.zeros(pad_len, dtype=torch.long)])
        )
        attention_mask.append(
            torch.cat([item["attention_mask"], torch.zeros(pad_len, dtype=torch.long)])
        )
        labels.append(
            torch.cat([item["labels"], torch.full((pad_len,), IGNORE_INDEX, dtype=torch.long)])
        )

    return {
        "input_ids": torch.stack(input_ids),
        "attention_mask": torch.stack(attention_mask),
        "labels": torch.stack(labels),
    }


class BertSpanDetector(nn.Module):
    """BERT-based BIO tagger for morpheme span detection.

    Architecture:
        Input sentence -> BERT encoder -> hidden states (batch, seq, 768)
        -> Dropout(0.1) -> Linear(768, 3) -> per-token BIO logits
    """

    def __init__(self, bert_model_name: str, num_labels: int = NUM_LABELS):
        super().__init__()
        self.bert = AutoModel.from_pretrained(bert_model_name)
        hidden_size = self.bert.config.hidden_size
        self.dropout = nn.Dropout(0.1)
        self.classifier = nn.Linear(hidden_size, num_labels)
        self.num_labels = num_labels

    def forward(self, input_ids, attention_mask, labels=None):
        """
        Returns:
            logits: (batch, seq_len, num_labels)
            loss: scalar if labels provided
        """
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        hidden_states = outputs.last_hidden_state  # (batch, seq_len, hidden)
        hidden_states = self.dropout(hidden_states)
        logits = self.classifier(hidden_states)  # (batch, seq_len, num_labels)

        loss = None
        if labels is not None:
            loss_fn = nn.CrossEntropyLoss(ignore_index=IGNORE_INDEX)
            # Reshape for cross entropy: (batch*seq, num_labels) vs (batch*seq,)
            loss = loss_fn(logits.view(-1, self.num_labels), labels.view(-1))

        return logits, loss


def compute_span_metrics(all_preds: list[list[int]], all_labels: list[list[int]]) -> dict:
    """Compute span-level precision, recall, F1.

    A span is a contiguous B-SPAN, I-SPAN, I-SPAN, ... sequence.
    A predicted span is correct if it exactly matches a gold span
    (same start position AND same end position).
    """
    def extract_spans(label_seq: list[int]) -> set[tuple[int, int]]:
        spans = set()
        i = 0
        while i < len(label_seq):
            if label_seq[i] == LABEL_B:
                start = i
                i += 1
                while i < len(label_seq) and label_seq[i] == LABEL_I:
                    i += 1
                spans.add((start, i))
            else:
                i += 1
        return spans

    total_pred_spans = 0
    total_gold_spans = 0
    total_correct = 0

    for preds, labels in zip(all_preds, all_labels):
        pred_spans = extract_spans(preds)
        gold_spans = extract_spans(labels)
        total_pred_spans += len(pred_spans)
        total_gold_spans += len(gold_spans)
        total_correct += len(pred_spans & gold_spans)

    precision = total_correct / total_pred_spans if total_pred_spans > 0 else 0
    recall = total_correct / total_gold_spans if total_gold_spans > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "pred_spans": total_pred_spans,
        "gold_spans": total_gold_spans,
        "correct_spans": total_correct,
    }


def evaluate(model, dataloader, device) -> dict:
    """Evaluate model. Returns loss, token-level accuracy, and span-level metrics."""
    model.eval()
    total_loss = 0
    total_correct = 0
    total_tokens = 0

    all_preds = []
    all_labels = []

    label_counts = Counter()
    label_correct = Counter()

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            logits, loss = model(input_ids, attention_mask, labels)
            total_loss += loss.item() * input_ids.size(0)

            predictions = logits.argmax(dim=-1)  # (batch, seq_len)

            # Collect per-sentence predictions and labels (filtered)
            for i in range(input_ids.size(0)):
                mask = labels[i] != IGNORE_INDEX
                valid_preds = predictions[i][mask].cpu().tolist()
                valid_labels = labels[i][mask].cpu().tolist()

                all_preds.append(valid_preds)
                all_labels.append(valid_labels)

                for p, l in zip(valid_preds, valid_labels):
                    label_counts[l] += 1
                    if p == l:
                        label_correct[l] += 1
                        total_correct += 1
                    total_tokens += 1

    avg_loss = total_loss / len(dataloader.dataset)
    token_accuracy = total_correct / total_tokens * 100 if total_tokens > 0 else 0

    # Per-label accuracy
    per_label = {}
    for label_id in [LABEL_O, LABEL_B, LABEL_I]:
        name = ["O", "B-SPAN", "I-SPAN"][label_id]
        total = label_counts.get(label_id, 0)
        correct = label_correct.get(label_id, 0)
        acc = correct / total * 100 if total > 0 else 0
        per_label[name] = {"accuracy": acc, "correct": correct, "total": total}

    # Span-level metrics
    span_metrics = compute_span_metrics(all_preds, all_labels)

    return {
        "loss": avg_loss,
        "token_accuracy": token_accuracy,
        "per_label": per_label,
        "span_metrics": span_metrics,
        "total_tokens": total_tokens,
    }


def main():
    parser = argparse.ArgumentParser(description="Train span detector")
    parser.add_argument("--model", type=str, default="tohoku-nlp/bert-base-japanese-v3",
                        help="Base model name")
    parser.add_argument("--data-dir", type=Path, default=Path("data/span_detector_v1"),
                        help="Directory with BIO data")
    parser.add_argument("--output", type=Path, default=Path("models/span-detector-v1"),
                        help="Output directory for model")
    parser.add_argument("--epochs", type=int, default=15,
                        help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16,
                        help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-5,
                        help="Learning rate")
    parser.add_argument("--max-length", type=int, default=256,
                        help="Maximum sequence length in tokens")
    parser.add_argument("--patience", type=int, default=5,
                        help="Early stopping patience (on val span F1)")
    parser.add_argument("--gradient-clip", type=float, default=1.0,
                        help="Gradient clipping max norm")
    args = parser.parse_args()

    print("=" * 60)
    print("Span Detector v1 - BIO Tagging Training")
    print("=" * 60)
    print(f"Base model: {args.model}")
    print(f"Data dir:   {args.data_dir}")
    print(f"Output:     {args.output}")
    print(f"Epochs:     {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print(f"LR:         {args.lr}")
    print(f"Max length: {args.max_length}")
    print(f"Patience:   {args.patience}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device:     {device}")

    # Load tokenizer
    print("\nLoading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    # Create datasets
    print("Creating datasets...")
    train_dataset = SpanDetectionDataset(
        args.data_dir / "train.json", tokenizer, args.max_length
    )
    val_dataset = SpanDetectionDataset(
        args.data_dir / "val.json", tokenizer, args.max_length
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
    print("\nCreating model...")
    model = BertSpanDetector(args.model, NUM_LABELS)
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

    print(f"\nTotal training steps: {total_steps}")
    print(f"Warmup steps: {warmup_steps}")

    # Training loop
    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60)

    best_val_f1 = 0.0
    patience_counter = 0
    log_history = []
    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()
        model.train()
        epoch_loss = 0
        epoch_steps = 0

        for step, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()
            logits, loss = model(input_ids, attention_mask, labels)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), args.gradient_clip)
            optimizer.step()
            scheduler.step()

            epoch_loss += loss.item()
            epoch_steps += 1

            if (step + 1) % 100 == 0:
                avg = epoch_loss / epoch_steps
                print(f"  Epoch {epoch} Step {step+1}/{len(train_loader)} Loss: {avg:.4f}")

        train_loss = epoch_loss / epoch_steps
        epoch_time = time.time() - epoch_start

        # Evaluate
        val_results = evaluate(model, val_loader, device)

        span = val_results["span_metrics"]
        epoch_log = {
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "eval_loss": round(val_results["loss"], 4),
            "token_accuracy": round(val_results["token_accuracy"], 2),
            "span_precision": round(span["precision"], 4),
            "span_recall": round(span["recall"], 4),
            "span_f1": round(span["f1"], 4),
            "pred_spans": span["pred_spans"],
            "gold_spans": span["gold_spans"],
            "correct_spans": span["correct_spans"],
            "per_label": {k: round(v["accuracy"], 1) for k, v in val_results["per_label"].items()},
            "epoch_time_seconds": round(epoch_time, 1),
            "learning_rate": scheduler.get_last_lr()[0],
        }
        log_history.append(epoch_log)

        print(f"\nEpoch {epoch}/{args.epochs}:")
        print(f"  Train Loss: {train_loss:.4f}")
        print(f"  Val Loss:   {val_results['loss']:.4f}  Token Acc: {val_results['token_accuracy']:.1f}%")
        print(f"  Span P: {span['precision']:.4f}  R: {span['recall']:.4f}  F1: {span['f1']:.4f}")
        print(f"  Spans: {span['correct_spans']}/{span['gold_spans']} correct, "
              f"{span['pred_spans']} predicted")
        print(f"  Per-label accuracy: ", end="")
        for name, info in val_results["per_label"].items():
            print(f"{name}={info['accuracy']:.1f}% ", end="")
        print(f"\n  Time: {epoch_time:.1f}s")

        # Early stopping on span F1
        if span["f1"] > best_val_f1:
            best_val_f1 = span["f1"]
            patience_counter = 0

            # Save best model
            args.output.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), args.output / "model.pt")
            tokenizer.save_pretrained(str(args.output))

            model_config = {
                "base_model": args.model,
                "num_labels": NUM_LABELS,
                "hidden_size": model.bert.config.hidden_size,
            }
            with open(args.output / "model_config.json", "w") as f:
                json.dump(model_config, f, indent=2)

            # Save label map
            with open(args.output / "label_map.json", "w") as f:
                json.dump({"O": LABEL_O, "B-SPAN": LABEL_B, "I-SPAN": LABEL_I}, f, indent=2)

            print(f"  -> New best F1! Saved to {args.output}")
        else:
            patience_counter += 1
            print(f"  -> No improvement (patience {patience_counter}/{args.patience})")
            if patience_counter >= args.patience:
                print(f"\nEarly stopping at epoch {epoch}")
                break

    training_time = time.time() - start_time

    # Save training log
    best_epoch = max(log_history, key=lambda x: x["span_f1"])
    training_log = {
        "version": "span_detector_v1",
        "base_model": args.model,
        "config": {
            "epochs_requested": args.epochs,
            "epochs_completed": epoch,
            "batch_size": args.batch_size,
            "learning_rate": args.lr,
            "max_length": args.max_length,
            "early_stopping_patience": args.patience,
            "gradient_clip": args.gradient_clip,
            "num_labels": NUM_LABELS,
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
            "best_val_span_f1": round(best_val_f1, 4),
            "best_epoch": best_epoch["epoch"],
            "best_epoch_metrics": best_epoch,
        },
        "log_history": log_history,
    }

    log_path = Path("methods/span_detector_v1/training_log.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(training_log, f, indent=2)
    print(f"\nTraining log saved to: {log_path}")

    results_log_path = Path("results/span_detector_v1_training_log.json")
    results_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_log_path, "w") as f:
        json.dump(training_log, f, indent=2)
    print(f"Training log also saved to: {results_log_path}")

    print("\n" + "=" * 60)
    print("Training complete!")
    print(f"Model saved to: {args.output}")
    print(f"Training time: {training_time / 60:.1f} minutes")
    print(f"Best validation span F1: {best_val_f1:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
