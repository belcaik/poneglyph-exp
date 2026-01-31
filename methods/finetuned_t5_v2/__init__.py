"""
Fine-tuned T5 v2 with bracket annotation format.

This version uses character-level span prediction:
  Input:  "読み: 土地の値段"
  Output: "土地[とち]の値段[ねだん]"

Unlike v1 which converted to full hiragana, v2 preserves the original text
with inline bracket annotations, making extraction trivial.
"""

from .annotator import T5V2Annotator

__all__ = ["T5V2Annotator"]
