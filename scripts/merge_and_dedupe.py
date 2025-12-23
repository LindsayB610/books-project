#!/usr/bin/env python3
"""
Main merge and deduplication script.
Reads from all source files and merges into canonical books.csv.
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe, write_csv_safe, safe_merge
from utils.deduplication import find_matches
from utils.normalization import compute_canonical_id
from utils.work_id import generate_work_id


# Define the canonical schema
CANONICAL_FIELDS = [
    'work_id', 'isbn13', 'asin', 'title', 'author', 'publication_year', 'publisher',
    'language', 'pages', 'genres', 'description', 'formats', 'physical_owned',
    'kindle_owned', 'audiobook_owned', 'goodreads_id', 'goodreads_url',
    'sources', 'date_added', 'date_read', 'date_updated',
    'read_status', 'rating', 'reread', 'reread_count', 'dnf', 'dnf_reason',
    'pacing_rating', 'tone', 'vibe', 'what_i_wanted', 'did_it_deliver',
    'favorite_elements', 'pet_peeves', 'notes', 'anchor_type', 'would_recommend'
]


def load_all_sources(sources_dir: Path) -> List[Dict]:
    """
    Load books from all source files.
    Returns a list of book dictionaries.
    """
    all_books = []
    
    # Goodreads export
    goodreads_file = sources_dir / 'goodreads_export.csv'
    if goodreads_file.exists():
        print(f"Loading Goodreads data from {goodreads_file}...")
        books = read_csv_safe(str(goodreads_file))
        # TODO: Transform Goodreads format to canonical format
        # For now, just add source marker
        for book in books:
            book['sources'] = 'goodreads'
        all_books.extend(books)
        print(f"  Loaded {len(books)} books from Goodreads")
    
    # Kindle library
    kindle_file = sources_dir / 'kindle_library.csv'
    if kindle_file.exists():
        print(f"Loading Kindle data from {kindle_file}...")
        books = read_csv_safe(str(kindle_file))
        for book in books:
            book['sources'] = 'kindle'
        all_books.extend(books)
        print(f"  Loaded {len(books)} books from Kindle")
    
    # TODO: Physical shelf OCR
    # physical_shelf_dir = sources_dir / 'physical_shelf_photos'
    
    return all_books


def normalize_row(row: Dict) -> Dict:
    """
    Normalize a row to canonical format.
    Ensures all canonical fields exist.
    Generates work_id if missing.
    """
    normalized = {}
    for field in CANONICAL_FIELDS:
        normalized[field] = row.get(field)
    
    # Generate work_id if missing
    if not normalized.get('work_id'):
        normalized['work_id'] = generate_work_id(normalized)
    
    # Merge kindle_asin into asin if present (for backward compatibility)
    if not normalized.get('asin') and row.get('kindle_asin'):
        normalized['asin'] = row.get('kindle_asin')
    
    # Set format flags based on formats field
    formats = (normalized.get('formats') or '').lower()
    normalized['kindle_owned'] = '1' if 'kindle' in formats else normalized.get('kindle_owned', '0')
    normalized['physical_owned'] = '1' if 'physical' in formats else normalized.get('physical_owned', '0')
    normalized['audiobook_owned'] = '1' if 'audiobook' in formats else normalized.get('audiobook_owned', '0')
    
    return normalized


def merge_books(existing_books: List[Dict], new_books: List[Dict]) -> Tuple[List[Dict], List[Tuple[Dict, Dict, float, str]]]:
    """
    Merge new books into existing books, deduplicating as we go.
    Returns (merged_books, possible_duplicates) tuple.
    possible_duplicates is a list of (book1, book2, confidence, reason) tuples.
    """
    merged = existing_books.copy()
    possible_duplicates = []
    
    for new_book in new_books:
        normalized_new = normalize_row(new_book)
        
        # Find matches
        matches = find_matches(normalized_new, merged)
        
        if matches:
            # Merge with best match
            best_match, confidence = matches[0]
            if confidence >= 0.70:  # Threshold for auto-merge
                idx = merged.index(best_match)
                merged[idx] = safe_merge(best_match, normalized_new)
                print(f"  Merged: {normalized_new.get('title', 'Unknown')} (confidence: {confidence:.2f})")
            else:
                # Low confidence - add as new but flag for review
                # Also add to possible duplicates list
                normalized_new['notes'] = (normalized_new.get('notes') or '') + f" [LOW_CONFIDENCE_MATCH: {matches[0][0].get('title')}]"
                merged.append(normalized_new)
                print(f"  Added (low confidence): {normalized_new.get('title', 'Unknown')}")
                
                # Record as possible duplicate if confidence is still reasonably high
                if confidence >= 0.75:
                    reason = f"Fuzzy match during merge (confidence: {confidence:.2f})"
                    possible_duplicates.append((best_match, normalized_new, confidence, reason))
        else:
            # No match - add as new book
            merged.append(normalized_new)
            print(f"  Added new: {normalized_new.get('title', 'Unknown')}")
    
    return merged, possible_duplicates


def main():
    """
    Main entry point: load sources, merge, write canonical CSV.
    """
    project_root = Path(__file__).parent.parent
    sources_dir = project_root / 'sources'
    books_csv = project_root / 'books.csv'
    
    print("=" * 60)
    print("Books CSV Merge and Deduplication")
    print("=" * 60)
    
    # Load existing canonical CSV
    print(f"\nLoading existing books.csv...")
    existing_books = read_csv_safe(str(books_csv))
    print(f"  Found {len(existing_books)} existing books")
    
    # Load all source data
    print(f"\nLoading source data from {sources_dir}...")
    if not sources_dir.exists():
        print(f"  Creating sources directory...")
        sources_dir.mkdir()
    
    new_books = load_all_sources(sources_dir)
    
    if not new_books:
        print("\nNo source data found. Please add data to the sources/ directory.")
        print("See README.md for instructions.")
        return
    
    # Merge and deduplicate
    print(f"\nMerging and deduplicating...")
    merged_books, possible_duplicates = merge_books(existing_books, new_books)
    
    # Report possible duplicates
    if possible_duplicates:
        print(f"\n⚠️  Found {len(possible_duplicates)} possible duplicate(s) (confidence >= 0.75):")
        for book1, book2, confidence, reason in possible_duplicates:
            print(f"  • {book1.get('title', 'Unknown')} <-> {book2.get('title', 'Unknown')} ({confidence:.2%})")
        print(f"  Run 'python scripts/find_duplicates.py' for a detailed report.")
    
    # Ensure all rows have all fields and work_ids
    for book in merged_books:
        # Generate work_id if missing
        if not book.get('work_id'):
            book['work_id'] = generate_work_id(book)
        
        # Ensure all fields exist
        for field in CANONICAL_FIELDS:
            if field not in book:
                book[field] = None
    
    # Write canonical CSV
    print(f"\nWriting canonical books.csv...")
    write_csv_safe(str(books_csv), merged_books, CANONICAL_FIELDS)
    print(f"  Wrote {len(merged_books)} books to books.csv")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
    print(f"\nYou can now manually edit books.csv to add your preferences.")
    print(f"Your manual fields will be preserved on the next run.")
    
    if possible_duplicates:
        print(f"\n💡 Tip: Review possible duplicates with: python scripts/find_duplicates.py")


if __name__ == '__main__':
    main()

