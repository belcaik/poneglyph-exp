"""
Fine-tuned T5 v3 with bracket annotation format and expanded multi-source dataset.

This version builds on v2's bracket format approach:
  Input:  "読み: 土地の値段"
  Output: "土地[とち]の値段[ねだん]"

Key difference from v2:
- Trained on 4x more data (multi-source: NHK, MATCHA, Kahoku, Hirogaru)
- 10 epochs with early stopping (patience=3) instead of 5 fixed epochs
"""

from .annotator import T5V3Annotator

__all__ = ["T5V3Annotator"]
