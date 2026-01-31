"""
Fine-tuned T5 Furigana Annotator.

Uses a fine-tuned Japanese T5 model to predict furigana readings
for Japanese text.
"""

from .annotator import T5Annotator

__all__ = ["T5Annotator"]
