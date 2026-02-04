#!/usr/bin/env python3
"""
Train ByT5 v1 with bracket annotation format on sentence-segmented dataset.

ByT5 operates at byte-level (no subword tokenization), which should better handle:
- Mixed scripts (numbers + kanji like 2人目)
- Arbitrary character combinations
- Annotation style variation

Format (same as T5 v4):
  Input:  "読み: 土地の値段"
  Output: "土地[とち]の値段[ねだん]"

Key differences from T5 v4:
- Byte-level tokenization (~3.8x longer sequences)
- max_length: 768 (vs 128 for T5 v4)
- batch_size: 2 with gradient_accumulation_steps: 4 (effective batch = 8)

Usage:
    python -m methods.byt5_v1.train \
        --model sonoisa/byt5-small-japanese \
        --train data/bracket_format_v4/train.json \
        --val data/bracket_format_v4/val.json \
        --output models/byt5-furigana-v1 \
        --epochs 10
"""

import argparse
import json
import time
from pathlib import Path

import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
    EarlyStoppingCallback,
)


class BracketFuriganaDataset(Dataset):
    """Dataset for bracket annotation format with ByT5."""

    def __init__(self, data_path: Path, tokenizer, max_length: int = 768):
        with open(data_path) as f:
            self.data = json.load(f)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        # Tokenize input (byte-level)
        inputs = self.tokenizer(
            item["input"],
            max_length=self.max_length,
            truncation=True,
            padding=False,
            return_tensors=None,
        )

        # Tokenize output (target)
        targets = self.tokenizer(
            item["output"],
            max_length=self.max_length,
            truncation=True,
            padding=False,
            return_tensors=None,
        )

        return {
            "input_ids": torch.tensor(inputs["input_ids"]),
            "attention_mask": torch.tensor(inputs["attention_mask"]),
            "labels": torch.tensor(targets["input_ids"]),
        }


def main():
    parser = argparse.ArgumentParser(description="Train ByT5 v1 with bracket format")
    parser.add_argument("--model", type=str, default="sonoisa/byt5-small-japanese",
                        help="Base model name")
    parser.add_argument("--train", type=Path, required=True,
                        help="Training data (bracket format)")
    parser.add_argument("--val", type=Path, required=True,
                        help="Validation data (bracket format)")
    parser.add_argument("--output", type=Path, required=True,
                        help="Output directory for model")
    parser.add_argument("--epochs", type=int, default=10,
                        help="Number of training epochs (default: 10)")
    parser.add_argument("--batch-size", type=int, default=2,
                        help="Batch size (default: 2 for byte-level)")
    parser.add_argument("--gradient-accumulation", type=int, default=4,
                        help="Gradient accumulation steps (default: 4)")
    parser.add_argument("--lr", type=float, default=3e-4,
                        help="Learning rate")
    parser.add_argument("--max-length", type=int, default=768,
                        help="Maximum sequence length (default: 768 for byte-level)")
    parser.add_argument("--early-stopping-patience", type=int, default=3,
                        help="Early stopping patience (epochs without improvement)")
    args = parser.parse_args()

    print("=" * 60)
    print("ByT5 v1 Training - Byte-Level Furigana Annotation")
    print("=" * 60)
    print(f"Base model: {args.model}")
    print(f"Train data: {args.train}")
    print(f"Val data:   {args.val}")
    print(f"Output:     {args.output}")
    print(f"Epochs:     {args.epochs}")
    print(f"Batch size: {args.batch_size} (x{args.gradient_accumulation} accum = {args.batch_size * args.gradient_accumulation} effective)")
    print(f"LR:         {args.lr}")
    print(f"Max length: {args.max_length}")
    print(f"Early stopping patience: {args.early_stopping_patience}")

    # Load tokenizer and model
    print("\nLoading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model)

    # Print model info
    num_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {num_params:,}")

    # Create datasets
    print("Creating datasets...")
    train_dataset = BracketFuriganaDataset(args.train, tokenizer, args.max_length)
    val_dataset = BracketFuriganaDataset(args.val, tokenizer, args.max_length)
    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples:   {len(val_dataset)}")

    # Show example
    print("\nExample from training data:")
    with open(args.train) as f:
        examples = json.load(f)[:1]
    for ex in examples:
        print(f"  Input:  {ex['input'][:60]}...")
        print(f"  Output: {ex['output'][:60]}...")
        # Show byte lengths
        input_bytes = len(tokenizer(ex['input'], return_tensors=None)['input_ids'])
        output_bytes = len(tokenizer(ex['output'], return_tensors=None)['input_ids'])
        print(f"  Input bytes: {input_bytes}, Output bytes: {output_bytes}")

    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(args.output),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        warmup_steps=200,  # More warmup for longer sequences
        weight_decay=0.01,
        logging_dir=str(args.output / "logs"),
        logging_steps=100,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        predict_with_generate=True,
        generation_max_length=args.max_length,
        learning_rate=args.lr,
        # Disable fp16 to avoid NaN issues
        fp16=False,
        # Save only best checkpoint to save disk space
        save_total_limit=2,
    )

    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        label_pad_token_id=-100,
    )

    # Trainer with early stopping callback
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
        data_collator=data_collator,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=args.early_stopping_patience)],
    )

    # Train with timing
    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60)

    start_time = time.time()
    trainer.train()
    training_time = time.time() - start_time

    # Save final model
    print("\nSaving model...")
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))

    # Prepare training log
    training_log = {
        "version": "byt5_v1",
        "base_model": args.model,
        "config": {
            "epochs_requested": args.epochs,
            "batch_size": args.batch_size,
            "gradient_accumulation_steps": args.gradient_accumulation,
            "effective_batch_size": args.batch_size * args.gradient_accumulation,
            "learning_rate": args.lr,
            "max_length": args.max_length,
            "early_stopping_patience": args.early_stopping_patience,
        },
        "data": {
            "train_samples": len(train_dataset),
            "val_samples": len(val_dataset),
        },
        "model_info": {
            "parameters": num_params,
            "vocab_size": tokenizer.vocab_size,
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

    # Save training log to methods directory
    log_path = Path("methods/byt5_v1/training_log.json")
    with open(log_path, "w") as f:
        json.dump(training_log, f, indent=2)
    print(f"Training log saved to: {log_path}")

    # Also save to results directory
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    results_log_path = results_dir / "byt5_v1_training_log.json"
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
