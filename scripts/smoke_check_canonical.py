#!/usr/bin/env python3
"""
Smoke-check script for canonical CSV output.
Performs CSV-safe validation checks using column names (not positional).
"""

import csv
import re
import sys
import itertools
from collections import Counter
from pathlib import Path
from typing import Tuple
import argparse


def check_read_status(filepath: Path) -> Tuple[bool, str]:
    """Check read_status values are valid."""
    c = Counter()
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = (row.get('read_status') or '').strip()
            c[status] += 1
    
    valid_statuses = {'read', 'reading', 'want_to_read', 'unread', 'dnf', ''}
    invalid = [s for s in c.keys() if s and s not in valid_statuses]
    
    if invalid:
        return False, f"❌ Invalid read_status values: {invalid}\n   Counts: {dict(c)}"
    return True, f"✅ read_status values: {dict(c)}"


def check_genres_empty(filepath: Path) -> Tuple[bool, str]:
    """Check genres is empty (reserved for future enrichment)."""
    vals = set()
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            genre = (row.get('genres') or '').strip()
            if genre:
                vals.add(genre)
    
    if vals:
        return False, f"❌ genres should be empty, found: {vals}"
    return True, "✅ genres is empty (reserved for external enrichment)"


def check_tags_format(filepath: Path) -> Tuple[bool, str]:
    """Check tags are pipe-delimited and lowercased."""
    tags = []
    bad_tags = []
    
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in itertools.islice(reader, 200):  # Check first 200 rows
            tag_str = (row.get('tags') or '').strip()
            if tag_str:
                tags.append(tag_str)
                # Check for commas or uppercase
                if ',' in tag_str or re.search(r'[A-Z]', tag_str):
                    bad_tags.append(tag_str)
    
    sample = tags[:10] if tags else []
    
    if bad_tags:
        return False, f"❌ Bad tags found: {bad_tags[:10]}\n   Sample tags: {sample}"
    return True, f"✅ Tags are pipe-delimited and lowercased\n   Sample: {sample[:5]}"


def check_date_read_empty(filepath: Path) -> Tuple[bool, str]:
    """Check date_read is empty (not populated)."""
    c = Counter()
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = (row.get('date_read') or '').strip()
            c[date] += 1
    
    non_empty = {k: v for k, v in c.items() if k}
    
    if non_empty:
        return False, f"❌ date_read should be empty, found: {dict(list(non_empty.items())[:5])}"
    return True, f"✅ date_read is empty (not populated)\n   Counts: {dict(list(c.items())[:3])}"


def check_header(filepath: Path) -> Tuple[bool, str]:
    """Check header includes expected columns."""
    expected_cols = {'work_id', 'isbn13', 'asin', 'title', 'author', 'genres', 'tags', 
                     'read_status', 'date_read', 'date_updated'}
    
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        actual_cols = set(reader.fieldnames or [])
    
    missing = expected_cols - actual_cols
    if missing:
        return False, f"❌ Missing expected columns: {missing}"
    
    if 'tags' not in actual_cols:
        return False, "❌ Missing 'tags' column"
    
    return True, f"✅ Header includes expected columns (including 'tags')\n   Total columns: {len(actual_cols)}"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Smoke-check canonical CSV output')
    parser.add_argument('--dataset', type=str, default='datasets/default',
                       help='Dataset root directory (default: datasets/default)')
    parser.add_argument('--csv', type=str, help='Path to canonical CSV (overrides --dataset)')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    if args.csv:
        canonical_csv = Path(args.csv)
    else:
        dataset_root = project_root / args.dataset
        canonical_csv = dataset_root / 'sources' / 'goodreads_canonical.csv'
    
    if not canonical_csv.exists():
        print(f"Error: {canonical_csv} not found.")
        print("Please run ingest_goodreads.py first.")
        sys.exit(1)
    
    print(f"Smoke-checking: {canonical_csv}")
    print("=" * 60)
    print()
    
    checks = [
        ("Header", check_header),
        ("Read Status", check_read_status),
        ("Genres Empty", check_genres_empty),
        ("Tags Format", check_tags_format),
        ("Date Read Empty", check_date_read_empty),
    ]
    
    all_passed = True
    for name, check_func in checks:
        passed, message = check_func(canonical_csv)
        print(f"{name}:")
        print(f"  {message}")
        print()
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All checks passed!")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Review the output above.")
        sys.exit(1)


if __name__ == '__main__':
    main()

