#!/usr/bin/env python3
"""
Main merge and deduplication script.
Reads from canonical source files and merges into books.csv.
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe, write_csv_safe, safe_merge
from utils.deduplication import find_matches
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

# Confidence thresholds
AUTO_MERGE_THRESHOLD = 0.92  # High threshold - prefer false negatives
POSSIBLE_DUPLICATE_THRESHOLD = 0.80  # Report possible duplicates above this


def load_all_sources(sources_dir: Path) -> List[Dict]:
    """
    Load books from canonical source files (output of ingest scripts).
    Returns a list of book dictionaries.
    """
    all_books = []
    
    # Goodreads canonical (output of ingest_goodreads.py)
    goodreads_file = sources_dir / 'goodreads_canonical.csv'
    if goodreads_file.exists():
        print(f"Loading Goodreads canonical data from {goodreads_file}...")
        books = read_csv_safe(str(goodreads_file))
        all_books.extend(books)
        print(f"  Loaded {len(books)} books from Goodreads")
    
    # Kindle canonical (output of ingest_kindle.py) - if present
    kindle_file = sources_dir / 'kindle_canonical.csv'
    if kindle_file.exists():
        print(f"Loading Kindle canonical data from {kindle_file}...")
        books = read_csv_safe(str(kindle_file))
        all_books.extend(books)
        print(f"  Loaded {len(books)} books from Kindle")
    
    # TODO: Physical shelf OCR canonical - if present
    
    return all_books


def normalize_row(row: Dict) -> Dict:
    """
    Normalize a row to canonical format.
    Ensures all canonical fields exist.
    Does NOT generate work_id here - that happens only for new rows.
    """
    normalized = {}
    for field in CANONICAL_FIELDS:
        normalized[field] = row.get(field)
    
    # Merge kindle_asin into asin if present (for backward compatibility)
    if not normalized.get('asin') and row.get('kindle_asin'):
        normalized['asin'] = row.get('kindle_asin')
    
    # Set format flags based on formats field
    formats = (normalized.get('formats') or '').lower()
    normalized['kindle_owned'] = '1' if 'kindle' in formats else normalized.get('kindle_owned', '0')
    normalized['physical_owned'] = '1' if 'physical' in formats else normalized.get('physical_owned', '0')
    normalized['audiobook_owned'] = '1' if 'audiobook' in formats else normalized.get('audiobook_owned', '0')
    
    return normalized


def write_possible_duplicates_report(possible_duplicates: List[Tuple[Dict, Dict, float, str]], report_file: Path):
    """
    Write possible duplicates to a CSV report file.
    """
    if not possible_duplicates:
        return
    
    # Create reports directory if needed
    report_file.parent.mkdir(exist_ok=True)
    
    report_rows = []
    for book1, book2, confidence, reason in possible_duplicates:
        report_rows.append({
            'work_id_1': book1.get('work_id', 'N/A'),
            'title_1': book1.get('title', 'Unknown'),
            'author_1': book1.get('author', 'Unknown'),
            'isbn13_1': book1.get('isbn13', 'N/A'),
            'work_id_2': book2.get('work_id', 'N/A'),
            'title_2': book2.get('title', 'Unknown'),
            'author_2': book2.get('author', 'Unknown'),
            'isbn13_2': book2.get('isbn13', 'N/A'),
            'confidence': f"{confidence:.3f}",
            'reason': reason
        })
    
    report_fields = [
        'work_id_1', 'title_1', 'author_1', 'isbn13_1',
        'work_id_2', 'title_2', 'author_2', 'isbn13_2',
        'confidence', 'reason'
    ]
    
    write_csv_safe(str(report_file), report_rows, report_fields)


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
        
        # Find matches (returns indices)
        matches = find_matches(normalized_new, merged)
        
        if matches:
            # Get best match
            best_idx, best_match, confidence = matches[0]
            
            if confidence >= AUTO_MERGE_THRESHOLD:
                # Auto-merge: preserve existing work_id, merge data
                merged[best_idx] = safe_merge(best_match, normalized_new)
                print(f"  Merged: {normalized_new.get('title', 'Unknown')} (confidence: {confidence:.2f})")
            
            elif confidence >= POSSIBLE_DUPLICATE_THRESHOLD:
                # Possible duplicate: do NOT merge, add as new, record in report
                # Generate work_id for the new row (it's truly new)
                if not normalized_new.get('work_id'):
                    normalized_new['work_id'] = generate_work_id(normalized_new)
                
                merged.append(normalized_new)
                print(f"  Added (possible duplicate): {normalized_new.get('title', 'Unknown')} (confidence: {confidence:.2f})")
                
                # Record in possible duplicates report
                reason = f"Possible duplicate match (confidence: {confidence:.2f})"
                possible_duplicates.append((best_match, normalized_new, confidence, reason))
            
            else:
                # Low confidence: add as new, no duplicate record
                # Generate work_id for the new row
                if not normalized_new.get('work_id'):
                    normalized_new['work_id'] = generate_work_id(normalized_new)
                
                merged.append(normalized_new)
                print(f"  Added new: {normalized_new.get('title', 'Unknown')}")
        
        else:
            # No match - add as new book
            # Generate work_id for the new row
            if not normalized_new.get('work_id'):
                normalized_new['work_id'] = generate_work_id(normalized_new)
            
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
    reports_dir = project_root / 'reports'
    duplicates_report = reports_dir / 'possible_duplicates.csv'
    
    print("=" * 60)
    print("Books CSV Merge and Deduplication")
    print("=" * 60)
    
    # Load existing canonical CSV
    print(f"\nLoading existing books.csv...")
    existing_books = read_csv_safe(str(books_csv))
    print(f"  Found {len(existing_books)} existing books")
    
    # Load all canonical source data
    print(f"\nLoading canonical source data from {sources_dir}...")
    if not sources_dir.exists():
        print(f"  Creating sources directory...")
        sources_dir.mkdir()
    
    new_books = load_all_sources(sources_dir)
    
    if not new_books:
        print("\nNo canonical source data found.")
        print("Please run ingest scripts first (e.g., ingest_goodreads.py)")
        print("See README.md for instructions.")
        return
    
    # Merge and deduplicate
    print(f"\nMerging and deduplicating...")
    merged_books, possible_duplicates = merge_books(existing_books, new_books)
    
    # Write possible duplicates report
    if possible_duplicates:
        print(f"\n⚠️  Found {len(possible_duplicates)} possible duplicate(s) (confidence >= {POSSIBLE_DUPLICATE_THRESHOLD:.2f})")
        write_possible_duplicates_report(possible_duplicates, duplicates_report)
        print(f"  Wrote report to {duplicates_report}")
        print(f"  Review manually and merge if appropriate")
    
    # Ensure all rows have all fields
    # Preserve existing work_ids, only generate for rows that don't have one
    for book in merged_books:
        # Only generate work_id if missing (shouldn't happen after merge, but safety check)
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
        print(f"\n💡 Tip: Review possible duplicates in {duplicates_report}")


if __name__ == '__main__':
    main()
