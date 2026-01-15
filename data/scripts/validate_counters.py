#!/usr/bin/env python
"""
Counter Word Benchmark Dataset Validator

Validates the counter word benchmark dataset against authoritative patterns
and ensures data quality for accurate evaluation.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


# Authoritative irregular patterns for each counter type
KNOWN_IRREGULARS = {
    "人": {
        "1人": "ひとり",
        "2人": "ふたり",
    },
    "日": {
        # Highly irregular date readings (1-10)
        "1日": "ついたち",
        "2日": "ふつか",
        "3日": "みっか",
        "4日": "よっか",
        "5日": "いつか",
        "6日": "むいか",
        "7日": "なのか",
        "8日": "ようか",
        "9日": "ここのか",
        "10日": "とおか",
        # Other irregular dates
        "14日": "じゅうよっか",
        "20日": "はつか",
        "24日": "にじゅうよっか",
    },
    "本": {
        # Sound changes with 本
        "1本": "いっぽん",
        "3本": "さんぼん",
        "6本": "ろっぽん",
        "8本": "はっぽん",
        "10本": "じゅっぽん",
    },
    "匹": {
        # Sound changes with 匹
        "1匹": "いっぴき",
        "3匹": "さんびき",
        "6匹": "ろっぴき",
        "8匹": "はっぴき",
        "10匹": "じゅっぴき",
    },
    "個": {
        # Sound changes with 個
        "1個": "いっこ",
        "6個": "ろっこ",
        "8個": "はっこ",
        "10個": "じゅっこ",
    },
    "回": {
        # Sound changes with 回
        "1回": "いっかい",
        "6回": "ろっかい",
        "8回": "はっかい",
        "10回": "じゅっかい",
    },
    "階": {
        # Sound changes with 階
        "1階": "いっかい",
        "6階": "ろっかい",
        "8階": "はっかい",
        "10階": "じゅっかい",
    },
    "枚": {
        # 枚 has regular readings, no critical irregulars
    },
    "歳": {
        # Highly irregular
        "1歳": "いっさい",
        "8歳": "はっさい",
        "10歳": "じゅっさい",
        "20歳": "はたち",
    },
}

# Required counter types
REQUIRED_COUNTER_TYPES = {"人", "日", "本", "匹", "個", "回", "階", "枚", "歳"}

# Required fields for each test case
REQUIRED_FIELDS = {"text", "reading", "counter_type", "irregularity_type", "error_category"}

# Valid values for enum fields
VALID_IRREGULARITY_TYPES = {"regular", "irregular", "highly_irregular", "sound_change"}
VALID_ERROR_CATEGORIES = {
    "wrong_special_reading",
    "missing_sound_change",
    "context_disambiguation",
    "regular_pattern",
    "compound_form",
}


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class CounterValidator:
    """Validates counter word benchmark dataset"""

    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        self.data = None
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_dataset(self) -> None:
        """Load and parse YAML dataset"""
        if not self.dataset_path.exists():
            raise ValidationError(f"Dataset file not found: {self.dataset_path}")

        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                self.data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML format: {e}")

        if not isinstance(self.data, dict):
            raise ValidationError("Dataset must be a YAML dictionary")

        if 'test_cases' not in self.data:
            raise ValidationError("Dataset must contain 'test_cases' key")

    def validate_structure(self) -> None:
        """Validate basic dataset structure"""
        test_cases = self.data.get('test_cases', [])

        if not isinstance(test_cases, list):
            raise ValidationError("'test_cases' must be a list")

        if len(test_cases) == 0:
            raise ValidationError("Dataset contains no test cases")

        print(f"✓ Dataset structure valid")
        print(f"✓ Found {len(test_cases)} test cases")

    def validate_test_case_fields(self) -> None:
        """Validate that all test cases have required fields"""
        test_cases = self.data.get('test_cases', [])

        for idx, test_case in enumerate(test_cases, 1):
            if not isinstance(test_case, dict):
                self.errors.append(f"Test case {idx}: Not a dictionary")
                continue

            # Check required fields
            missing_fields = REQUIRED_FIELDS - set(test_case.keys())
            if missing_fields:
                self.errors.append(
                    f"Test case {idx} ({test_case.get('text', 'unknown')}): "
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

            # Validate field types and values
            if 'text' in test_case and not isinstance(test_case['text'], str):
                self.errors.append(f"Test case {idx}: 'text' must be a string")

            if 'reading' in test_case and not isinstance(test_case['reading'], str):
                self.errors.append(f"Test case {idx}: 'reading' must be a string")

            if 'counter_type' in test_case:
                if test_case['counter_type'] not in REQUIRED_COUNTER_TYPES:
                    self.errors.append(
                        f"Test case {idx} ({test_case.get('text', 'unknown')}): "
                        f"Invalid counter_type '{test_case['counter_type']}'"
                    )

            if 'irregularity_type' in test_case:
                if test_case['irregularity_type'] not in VALID_IRREGULARITY_TYPES:
                    self.errors.append(
                        f"Test case {idx} ({test_case.get('text', 'unknown')}): "
                        f"Invalid irregularity_type '{test_case['irregularity_type']}'"
                    )

            if 'error_category' in test_case:
                if test_case['error_category'] not in VALID_ERROR_CATEGORIES:
                    self.errors.append(
                        f"Test case {idx} ({test_case.get('text', 'unknown')}): "
                        f"Invalid error_category '{test_case['error_category']}'"
                    )

        if not self.errors:
            print(f"✓ All test cases have required fields")

    def validate_counter_coverage(self) -> None:
        """Validate that all required counter types are covered"""
        test_cases = self.data.get('test_cases', [])
        counter_types_found = {tc.get('counter_type') for tc in test_cases}

        missing_types = REQUIRED_COUNTER_TYPES - counter_types_found
        if missing_types:
            self.errors.append(
                f"Missing required counter types: {', '.join(sorted(missing_types))}"
            )
        else:
            print(f"✓ All 9 required counter types present")

        # Count test cases per type
        counter_counts: Dict[str, int] = {}
        for tc in test_cases:
            ct = tc.get('counter_type')
            if ct:
                counter_counts[ct] = counter_counts.get(ct, 0) + 1

        print("\n  Counter type distribution:")
        for counter_type in sorted(REQUIRED_COUNTER_TYPES):
            count = counter_counts.get(counter_type, 0)
            status = "✓" if count >= 30 else "✗"
            print(f"    {status} {counter_type}: {count} test cases")
            if count < 30:
                self.warnings.append(
                    f"Counter type '{counter_type}' has only {count} test cases (recommended: 30+)"
                )

    def validate_reading_format(self) -> None:
        """Validate that all readings are in hiragana format"""
        test_cases = self.data.get('test_cases', [])

        # Hiragana Unicode range: U+3040 to U+309F
        hiragana_pattern = re.compile(r'^[\u3040-\u309F]+$')

        for idx, test_case in enumerate(test_cases, 1):
            reading = test_case.get('reading', '')
            if not reading:
                continue

            if not hiragana_pattern.match(reading):
                self.errors.append(
                    f"Test case {idx} ({test_case.get('text', 'unknown')}): "
                    f"Reading '{reading}' contains non-hiragana characters"
                )

        if not self.errors:
            print(f"✓ All readings are in hiragana format")

    def validate_irregular_patterns(self) -> None:
        """Validate readings against known irregular patterns"""
        test_cases = self.data.get('test_cases', [])

        verified_count = 0
        for idx, test_case in enumerate(test_cases, 1):
            text = test_case.get('text', '')
            reading = test_case.get('reading', '')
            counter_type = test_case.get('counter_type', '')

            if not all([text, reading, counter_type]):
                continue

            # Check if this is a known irregular pattern
            if counter_type in KNOWN_IRREGULARS:
                expected_reading = KNOWN_IRREGULARS[counter_type].get(text)
                if expected_reading:
                    verified_count += 1
                    if reading != expected_reading:
                        self.errors.append(
                            f"Test case {idx} ({text}): "
                            f"Incorrect reading '{reading}' (expected '{expected_reading}')"
                        )

        if not self.errors:
            print(f"✓ All irregular patterns validated")
            print(f"  Verified {verified_count} known irregular readings against authoritative sources")

    def validate_minimum_test_cases(self, minimum: int = 300) -> None:
        """Validate that dataset has minimum number of test cases"""
        test_cases = self.data.get('test_cases', [])
        count = len(test_cases)

        if count < minimum:
            self.errors.append(
                f"Dataset has only {count} test cases (required: {minimum}+)"
            )
        else:
            print(f"✓ Dataset has {count} test cases (requirement: {minimum}+ met)")

    def validate_all(self, check_structure_only: bool = False) -> bool:
        """Run all validations"""
        try:
            self.load_dataset()
            print(f"Validating: {self.dataset_path}")
            print()

            # Basic structure validation
            self.validate_structure()

            if check_structure_only:
                print("\n✓ Structure validation complete")
                return True

            # Detailed validations
            self.validate_test_case_fields()
            self.validate_counter_coverage()
            self.validate_reading_format()
            self.validate_irregular_patterns()
            self.validate_minimum_test_cases()

            # Report results
            print()
            if self.errors:
                print("=" * 60)
                print("VALIDATION FAILED")
                print("=" * 60)
                for error in self.errors:
                    print(f"✗ ERROR: {error}")
                return False

            if self.warnings:
                print("=" * 60)
                print("VALIDATION PASSED WITH WARNINGS")
                print("=" * 60)
                for warning in self.warnings:
                    print(f"⚠ WARNING: {warning}")
                print()

            print("=" * 60)
            print("✓ ALL VALIDATION CHECKS PASSED")
            print("=" * 60)
            return True

        except ValidationError as e:
            print(f"\n✗ VALIDATION ERROR: {e}")
            return False
        except Exception as e:
            print(f"\n✗ UNEXPECTED ERROR: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Validate counter word benchmark dataset"
    )
    parser.add_argument(
        '--dataset',
        default='data/counter_benchmark.yaml',
        help='Path to dataset file (default: data/counter_benchmark.yaml)'
    )
    parser.add_argument(
        '--check-structure',
        action='store_true',
        help='Only check basic structure (skip detailed validations)'
    )

    args = parser.parse_args()

    validator = CounterValidator(args.dataset)
    success = validator.validate_all(check_structure_only=args.check_structure)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
