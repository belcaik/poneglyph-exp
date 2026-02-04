"""
Fine-tuned T5 v4 with bracket annotation format and sentence-segmented dataset.

This version builds on v3's multi-source approach but fixes the data structure issue:
  - All sources now have uniform sentence-level granularity
  - MATCHA/Kahoku data segmented into sentences with token reassignment
  - Token preservation rate: >99.96%

Key difference from v3:
- Data preprocessed with sentence segmentation (scripts/segment_sentences.py)
- Training data: 12,261 sentences (vs 4,358 in v3, +181%)
- All sources now have avg ~50-70 chars (vs v3's MATCHA at 443 chars)
"""

from .annotator import T5V4Annotator

__all__ = ["T5V4Annotator"]
