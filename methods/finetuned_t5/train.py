#!/usr/bin/env python3
"""
Fine-tune T5 model for furigana prediction.

This script fine-tunes a Japanese T5 model on NHK Easy News data
to predict furigana readings for Japanese text.

Usage:
    python -m methods.finetuned_t5.train \
        --model sonoisa/t5-base-japanese \
        --train data/splits/train.json \
        --val data/splits/val.json \
        --output models/t5-furigana \
        --epochs 3
"""

import argparse
import json
import os
from pathlib import Path

import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)


def load_examples(data_path: Path) -> list[dict]:
    """Load and preprocess examples from JSON file."""
    examples = []

    with open(data_path) as f:
        sentences = json.load(f)

    for sentence in sentences:
        text = sentence["text"]
        tokens = sentence["tokens"]

        if not tokens:
            continue

        # Create input: the original text with prefix
        input_text = f"読み: {text}"

        # Create output: text with kanji replaced by readings
        output_parts = []
        last_end = 0

        for token in tokens:
            surface = token["surface"]
            reading = token["reading"]

            # Find surface in text starting from last position
            pos = text.find(surface, last_end)
            if pos >= 0:
                # Add any text before this token
                if pos > last_end:
                    between = text[last_end:pos]
                    output_parts.append(between)
                # Add the reading
                output_parts.append(reading)
                last_end = pos + len(surface)

        # Add remaining text
        if last_end < len(text):
            output_parts.append(text[last_end:])

        output_text = "".join(output_parts)

        examples.append({
            "input": input_text,
            "output": output_text,
        })

    return examples


class FuriganaDataset(Dataset):
    """Dataset for furigana prediction task."""

    def __init__(self, examples: list[dict], tokenizer, max_length: int = 128):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.examples = examples

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        example = self.examples[idx]

        # Tokenize input - don't pad here, let the collator handle it
        model_inputs = self.tokenizer(
            example["input"],
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt",
        )

        # Tokenize output (labels) using text_target parameter
        labels = self.tokenizer(
            text_target=example["output"],
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt",
        )

        # Squeeze to remove batch dimension and convert to list for collator
        return {
            "input_ids": model_inputs["input_ids"].squeeze(0),
            "attention_mask": model_inputs["attention_mask"].squeeze(0),
            "labels": labels["input_ids"].squeeze(0),
        }


def main():
    parser = argparse.ArgumentParser(description="Fine-tune T5 for furigana")
    parser.add_argument("--model", default="sonoisa/t5-base-japanese",
                        help="Base model name")
    parser.add_argument("--train", type=Path, required=True,
                        help="Training data JSON")
    parser.add_argument("--val", type=Path, required=True,
                        help="Validation data JSON")
    parser.add_argument("--output", type=Path, required=True,
                        help="Output directory")
    parser.add_argument("--epochs", type=int, default=3,
                        help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=8,
                        help="Batch size")
    parser.add_argument("--lr", type=float, default=5e-5,
                        help="Learning rate")
    parser.add_argument("--max-length", type=int, default=128,
                        help="Max sequence length")
    args = parser.parse_args()

    print(f"Loading model: {args.model}")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model)

    print(f"Loading training data: {args.train}")
    train_examples = load_examples(args.train)
    train_dataset = FuriganaDataset(train_examples, tokenizer, args.max_length)
    print(f"  {len(train_dataset)} examples")

    print(f"Loading validation data: {args.val}")
    val_examples = load_examples(args.val)
    val_dataset = FuriganaDataset(val_examples, tokenizer, args.max_length)
    print(f"  {len(val_dataset)} examples")

    # Show sample
    print("\nSample input/output:")
    sample = train_examples[0]
    print(f"  Input:  {sample['input'][:80]}...")
    print(f"  Output: {sample['output'][:80]}...")

    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(args.output),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        predict_with_generate=True,
        logging_steps=100,
        save_total_limit=2,
        fp16=False,  # Disabled - causes NaN on some GPUs
        report_to="none",
    )

    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        label_pad_token_id=-100,
    )

    # Trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
        data_collator=data_collator,
    )

    print("\nStarting training...")
    trainer.train()

    print(f"\nSaving model to {args.output}")
    trainer.save_model()
    tokenizer.save_pretrained(args.output)

    print("Done!")


if __name__ == "__main__":
    main()
