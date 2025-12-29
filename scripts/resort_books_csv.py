#!/usr/bin/env python3
"""
Utility script to re-sort books.csv by author, then title.
Useful if the CSV gets out of order for any reason.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe, write_csv_safe
from scripts.merge_and_dedupe import CANONICAL_FIELDS


def main():
    """
    Re-sort books.csv by author, then title.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Re-sort books.csv by author, then title')
    parser.add_argument('--dataset', type=str, default='datasets/default',
                       help='Dataset root directory (default: datasets/default)')
    
    args = parser.parse_args()
    
    dataset_path = Path(args.dataset)
    books_csv = dataset_path / 'books.csv'
    
    if not books_csv.exists():
        print(f"Error: {books_csv} does not exist")
        sys.exit(1)
    
    print(f"Reading {books_csv}...")
    books = read_csv_safe(str(books_csv))
    print(f"  Found {len(books)} books")
    
    # Verify current sort status
    authors = [(b.get('author') or '').lower() for b in books]
    is_sorted = authors == sorted(authors)
    
    if is_sorted:
        print("✅ CSV is already sorted correctly")
        return
    
    print("⚠️  CSV is not sorted. Re-sorting...")
    
    # Re-sort using write_csv_safe (which always sorts)
    write_csv_safe(str(books_csv), books, CANONICAL_FIELDS)
    
    print(f"✅ Re-sorted {len(books)} books by author, then title")
    print(f"   Saved to {books_csv}")


if __name__ == '__main__':
    main()

