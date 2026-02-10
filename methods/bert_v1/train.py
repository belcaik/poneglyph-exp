#!/usr/bin/env python3
"""
Train BERT v1 for character-level furigana token classification.

Architecture: cl-tohoku/bert-base-japanese-char
Task: Token classification where each character gets a reading label or "O"

Usage:
    python -m methods.bert_v1.train \
        --model cl-tohoku/bert-base-japanese-char \
        --data-dir methods/bert_v1/data \
        --output models/bert-furigana-v1 \
        --epochs 10 --batch-size 16 --lr 2e-5 --patience 3
"""

import argparse
import json
import time
from pathlib import Path

import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
)


class CharLabelDataset(Dataset):
    """Dataset for character-level token classification."""

    def __init__(self, data_path: Path, tokenizer, label_vocab: dict, max_length: int = 512):
        with open(data_path) as f:
            self.data = json.load(f)
        self.tokenizer = tokenizer
        self.label_vocab = label_vocab
        self.max_length = max_length
        self.unk_label_id = 0  # Map unknown labels to O

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        chars = item["chars"]
        labels = item["labels"]

        # Tokenize character by character
        # For cl-tohoku/bert-base-japanese-char, each char becomes one token
        # Sequence: [CLS] char1 char2 ... charN [SEP]
        encoding = self.tokenizer(
            list(chars),
            is_split_into_words=True,
            max_length=self.max_length,
            truncation=True,
            padding=False,
            return_tensors=None,
        )

        # Manual label alignment since non-fast tokenizer doesn't support word_ids()
        # Token layout: [CLS] + char tokens + [SEP]
        # Number of char tokens = len(input_ids) - 2 (for CLS and SEP)
        n_char_tokens = len(encoding["input_ids"]) - 2
        label_ids = [-100]  # [CLS]
        for i in range(n_char_tokens):
            if i < len(labels):
                label = labels[i]
                label_ids.append(self.label_vocab.get(label, self.unk_label_id))
            else:
                label_ids.append(self.unk_label_id)
        label_ids.append(-100)  # [SEP]

        return {
            "input_ids": torch.tensor(encoding["input_ids"]),
            "attention_mask": torch.tensor(encoding["attention_mask"]),
            "labels": torch.tensor(label_ids),
        }


class PaddingCollator:
    """Collate and pad a batch of char-label samples."""

    def __init__(self, tokenizer):
        self.pad_token_id = tokenizer.pad_token_id

    def __call__(self, features):
        max_len = max(len(f["input_ids"]) for f in features)

        batch = {
            "input_ids": [],
            "attention_mask": [],
            "labels": [],
        }

        for f in features:
            pad_len = max_len - len(f["input_ids"])
            batch["input_ids"].append(
                torch.cat([f["input_ids"], torch.full((pad_len,), self.pad_token_id)])
            )
            batch["attention_mask"].append(
                torch.cat([f["attention_mask"], torch.zeros(pad_len, dtype=torch.long)])
            )
            batch["labels"].append(
                torch.cat([f["labels"], torch.full((pad_len,), -100)])
            )

        return {k: torch.stack(v) for k, v in batch.items()}


def main():
    parser = argparse.ArgumentParser(description="Train BERT v1 for furigana token classification")
    parser.add_argument("--model", type=str, default="cl-tohoku/bert-base-japanese-char",
                        help="Base model name")
    parser.add_argument("--data-dir", type=Path, required=True,
                        help="Directory with train.json, val.json, label_vocab.json")
    parser.add_argument("--output", type=Path, required=True,
                        help="Output directory for model")
    parser.add_argument("--epochs", type=int, default=10,
                        help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16,
                        help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-5,
                        help="Learning rate")
    parser.add_argument("--max-length", type=int, default=512,
                        help="Maximum sequence length in characters")
    parser.add_argument("--patience", type=int, default=3,
                        help="Early stopping patience")
    args = parser.parse_args()

    print("=" * 60)
    print("BERT v1 Training - Character-Level Token Classification")
    print("=" * 60)
    print(f"Base model: {args.model}")
    print(f"Data dir:   {args.data_dir}")
    print(f"Output:     {args.output}")
    print(f"Epochs:     {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print(f"LR:         {args.lr}")
    print(f"Max length: {args.max_length}")
    print(f"Patience:   {args.patience}")

    # Load label vocabulary
    with open(args.data_dir / "label_vocab.json") as f:
        label_vocab = json.load(f)
    num_labels = len(label_vocab)
    print(f"\nLabel vocabulary: {num_labels} labels")

    # Load tokenizer and model
    print("Loading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForTokenClassification.from_pretrained(
        args.model,
        num_labels=num_labels,
    )

    num_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {num_params:,}")

    # Create datasets
    print("Creating datasets...")
    train_dataset = CharLabelDataset(args.data_dir / "train.json", tokenizer, label_vocab, args.max_length)
    val_dataset = CharLabelDataset(args.data_dir / "val.json", tokenizer, label_vocab, args.max_length)
    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples:   {len(val_dataset)}")

    # Show example
    print("\nExample from training data:")
    with open(args.data_dir / "train.json") as f:
        examples = json.load(f)[:1]
    for ex in examples:
        print(f"  Text: {ex['text'][:60]}...")
        print(f"  First 10 char→label pairs:")
        for c, l in zip(ex["chars"][:10], ex["labels"][:10]):
            print(f"    '{c}' → {l}")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(args.output),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir=str(args.output / "logs"),
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        learning_rate=args.lr,
        fp16=False,
        save_total_limit=2,
    )

    collator = PaddingCollator(tokenizer)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
        data_collator=collator,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=args.patience)],
    )

    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60)

    start_time = time.time()
    trainer.train()
    training_time = time.time() - start_time

    print("\nSaving model...")
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))

    # Also save label vocab alongside model
    import shutil
    shutil.copy(args.data_dir / "label_vocab.json", args.output / "label_vocab.json")

    training_log = {
        "version": "bert_v1",
        "base_model": args.model,
        "config": {
            "epochs_requested": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.lr,
            "max_length": args.max_length,
            "early_stopping_patience": args.patience,
            "num_labels": num_labels,
        },
        "data": {
            "train_samples": len(train_dataset),
            "val_samples": len(val_dataset),
        },
        "model_info": {
            "parameters": num_params,
        },
        "results": {
            "training_time_seconds": round(training_time, 2),
            "training_time_minutes": round(training_time / 60, 2),
            "epochs_completed": trainer.state.epoch,
            "best_checkpoint": trainer.state.best_model_checkpoint,
            "best_eval_loss": trainer.state.best_metric if trainer.state.best_metric else None,
        },
        "log_history": trainer.state.log_history,
    }

    log_path = Path("methods/bert_v1/training_log.json")
    with open(log_path, "w") as f:
        json.dump(training_log, f, indent=2)
    print(f"Training log saved to: {log_path}")

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    results_log_path = results_dir / "bert_v1_training_log.json"
    with open(results_log_path, "w") as f:
        json.dump(training_log, f, indent=2)
    print(f"Training log also saved to: {results_log_path}")

    print("\n" + "=" * 60)
    print("Training complete!")
    print(f"Model saved to: {args.output}")
    print(f"Training time: {training_time / 60:.1f} minutes")
    print(f"Epochs completed: {trainer.state.epoch}")
    if trainer.state.best_model_checkpoint:
        print(f"Best checkpoint: {trainer.state.best_model_checkpoint}")
    print("=" * 60)


if __name__ == "__main__":
    main()
