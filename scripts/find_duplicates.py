#!/usr/bin/env python3
"""
Find and report possible duplicates in books.csv.
Uses fuzzy matching with high thresholds to identify potential duplicates.
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe
from utils.deduplication import find_matches, compute_title_similarity, compute_author_similarity
from utils.normalization import normalize_title, normalize_author, normalize_isbn13, normalize_asin


def find_possible_duplicates(books: List[Dict], confidence_threshold: float = 0.75) -> List[Tuple[Dict, Dict, float, str]]:
    """
    Find possible duplicates using fuzzy matching.
    Returns list of (book1, book2, confidence, reason) tuples.
    Only reports matches above confidence_threshold.
    """
    duplicates = []
    seen_pairs = set()
    
    for i, book1 in enumerate(books):
        # Compare with all other books
        for j, book2 in enumerate(books[i+1:], start=i+1):
            # Skip if already compared
            pair_key = tuple(sorted([i, j]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            
            # Check for exact identifier matches first
            isbn1 = normalize_isbn13(book1.get('isbn13', ''))
            isbn2 = normalize_isbn13(book2.get('isbn13', ''))
            asin1 = normalize_asin(book1.get('asin', ''))
            asin2 = normalize_asin(book2.get('asin', ''))
            
            confidence = 0.0
            reason = ""
            
            # Exact ISBN match
            if isbn1 and isbn2 and isbn1 == isbn2:
                confidence = 1.0
                reason = f"Same ISBN13: {isbn1}"
            
            # Exact ASIN match
            elif asin1 and asin2 and asin1 == asin2:
                confidence = 0.95
                reason = f"Same ASIN: {asin1}"
            
            # Fuzzy title + author match (high threshold)
            else:
                title1 = normalize_title(book1.get('title', ''))
                title2 = normalize_title(book2.get('title', ''))
                author1 = normalize_author(book1.get('author', ''))
                author2 = normalize_author(book2.get('author', ''))
                
                if title1 and title2 and author1 and author2:
                    title_sim = compute_title_similarity(title1, title2)
                    author_sim = compute_author_similarity(author1, author2)
                    
                    # Require both to be high (0.85+ for possible duplicate)
                    if title_sim >= 0.85 and author_sim >= 0.85:
                        confidence = (title_sim * 0.6 + author_sim * 0.4)
                        reason = f"Fuzzy match: title similarity {title_sim:.2f}, author similarity {author_sim:.2f}"
            
            if confidence >= confidence_threshold:
                duplicates.append((book1, book2, confidence, reason))
    
    # Sort by confidence (highest first)
    duplicates.sort(key=lambda x: x[2], reverse=True)
    return duplicates


def print_duplicate_report(duplicates: List[Tuple[Dict, Dict, float, str]]):
    """Print a formatted duplicate report."""
    if not duplicates:
        print("✅ No possible duplicates found!")
        return
    
    print("=" * 80)
    print(f"Possible Duplicates Found: {len(duplicates)}")
    print("=" * 80)
    print()
    
    for idx, (book1, book2, confidence, reason) in enumerate(duplicates, 1):
        title1 = book1.get('title', 'Unknown')
        author1 = book1.get('author', 'Unknown')
        isbn1 = book1.get('isbn13', 'N/A')
        asin1 = book1.get('asin', 'N/A')
        
        title2 = book2.get('title', 'Unknown')
        author2 = book2.get('author', 'Unknown')
        isbn2 = book2.get('isbn13', 'N/A')
        asin2 = book2.get('asin', 'N/A')
        
        print(f"Duplicate #{idx} (Confidence: {confidence:.2%})")
        print(f"  Reason: {reason}")
        print(f"  Book 1: {title1} by {author1}")
        print(f"          ISBN13: {isbn1}, ASIN: {asin1}")
        print(f"  Book 2: {title2} by {author2}")
        print(f"          ISBN13: {isbn2}, ASIN: {asin2}")
        print()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Find possible duplicate books in books.csv')
    parser.add_argument('--dataset', type=str, default='datasets/default',
                       help='Dataset root directory (default: datasets/default)')
    parser.add_argument('--csv', type=str, help='Path to books.csv (overrides --dataset)')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    if args.csv:
        books_csv = Path(args.csv)
    else:
        dataset_root = project_root / args.dataset
        books_csv = dataset_root / 'books.csv'
    
    if not books_csv.exists():
        print(f"Error: {books_csv} not found.")
        print("Please run merge_and_dedupe.py first to create books.csv")
        return
    
    print(f"Loading {books_csv}...")
    books = read_csv_safe(str(books_csv))
    
    if len(books) < 2:
        print("Not enough books to check for duplicates.")
        return
    
    print(f"Checking {len(books)} books for possible duplicates...\n")
    
    # Find duplicates with high threshold (0.75+)
    duplicates = find_possible_duplicates(books, confidence_threshold=0.75)
    
    print_duplicate_report(duplicates)
    
    if duplicates:
        print("\n💡 Tip: Review these potential duplicates and merge manually if needed.")
        print("   The merge script will handle exact matches automatically.")


if __name__ == '__main__':
    main()

