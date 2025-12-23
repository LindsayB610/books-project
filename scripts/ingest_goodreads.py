#!/usr/bin/env python3
"""
Goodreads export ingestion script.
Transforms Goodreads CSV export into canonical format.
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe, write_csv_safe
from utils.normalization import normalize_isbn13


def map_goodreads_to_canonical(goodreads_row: dict) -> dict:
    """
    Map Goodreads export fields to canonical format.
    
    Typical Goodreads fields:
    - Book Id, Title, Author, Author l-f, Additional Authors, ISBN, ISBN13,
      My Rating, Average Rating, Publisher, Binding, Number of Pages,
      Year Published, Original Publication Year, Date Read, Date Added,
      Bookshelves, My Review, Spoiler, Private Notes
    """
    canonical = {}
    
    # Identifiers - clean ISBN/ISBN13
    isbn13_raw = goodreads_row.get('ISBN13', '').strip() or goodreads_row.get('ISBN', '').strip()
    if isbn13_raw:
        # Clean and normalize ISBN13
        canonical['isbn13'] = normalize_isbn13(isbn13_raw) or isbn13_raw.strip()
    else:
        canonical['isbn13'] = None
    
    canonical['asin'] = None  # Goodreads doesn't have ASIN
    canonical['title'] = goodreads_row.get('Title', '').strip() or None
    canonical['author'] = goodreads_row.get('Author', '').strip() or None
    
    # Metadata
    canonical['publication_year'] = goodreads_row.get('Year Published', '').strip() or None
    canonical['publisher'] = goodreads_row.get('Publisher', '').strip() or None
    canonical['pages'] = goodreads_row.get('Number of Pages', '').strip() or None
    # Bookshelves as tags (don't infer read status from it)
    canonical['genres'] = goodreads_row.get('Bookshelves', '').strip() or None
    canonical['description'] = None  # Goodreads export doesn't include description
    
    # Formats and ownership
    canonical['formats'] = None
    # Ingest Owned Copies → physical_owned
    owned_copies = goodreads_row.get('Owned Copies', '').strip()
    if owned_copies:
        try:
            owned_count = int(owned_copies)
            canonical['physical_owned'] = '1' if owned_count > 0 else '0'
        except (ValueError, TypeError):
            canonical['physical_owned'] = '0'
    else:
        canonical['physical_owned'] = '0'
    
    canonical['kindle_owned'] = '0'
    canonical['audiobook_owned'] = '0'
    
    # Source provenance
    canonical['goodreads_id'] = goodreads_row.get('Book Id', '').strip() or None
    canonical['goodreads_url'] = f"https://www.goodreads.com/book/show/{canonical['goodreads_id']}" if canonical['goodreads_id'] else None
    canonical['sources'] = 'goodreads'
    
    # Dates
    date_added = goodreads_row.get('Date Added', '').strip()
    if date_added:
        # Goodreads format: "YYYY/MM/DD" or "YYYY-MM-DD"
        try:
            # Try to parse and normalize
            if '/' in date_added:
                dt = datetime.strptime(date_added, '%Y/%m/%d')
            else:
                dt = datetime.strptime(date_added, '%Y-%m-%d')
            canonical['date_added'] = dt.strftime('%Y-%m-%d')
        except:
            canonical['date_added'] = date_added
    else:
        canonical['date_added'] = None
    
    date_read = goodreads_row.get('Date Read', '').strip()
    if date_read:
        try:
            if '/' in date_read:
                dt = datetime.strptime(date_read, '%Y/%m/%d')
            else:
                dt = datetime.strptime(date_read, '%Y-%m-%d')
            canonical['date_read'] = dt.strftime('%Y-%m-%d')
        except:
            canonical['date_read'] = date_read
    else:
        canonical['date_read'] = None
    
    canonical['date_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    # Status - map strictly from Exclusive Shelf
    exclusive_shelf = goodreads_row.get('Exclusive Shelf', '').strip().lower()
    if exclusive_shelf == 'read':
        canonical['read_status'] = 'read'
    elif exclusive_shelf == 'currently-reading':
        canonical['read_status'] = 'reading'
    elif exclusive_shelf == 'to-read':
        canonical['read_status'] = 'want_to_read'
    else:
        canonical['read_status'] = None
    
    # Ratings
    rating = goodreads_row.get('My Rating', '').strip()
    if rating and rating.isdigit():
        canonical['rating'] = rating
    else:
        canonical['rating'] = None
    
    # Manual fields (from Goodreads)
    canonical['notes'] = goodreads_row.get('My Review', '').strip() or None
    if canonical['notes']:
        private_notes = goodreads_row.get('Private Notes', '').strip()
        if private_notes:
            canonical['notes'] = f"{canonical['notes']}\n\nPrivate Notes: {private_notes}"
    
    # Reread - ingest Read Count
    read_count = goodreads_row.get('Read Count', '').strip()
    if read_count:
        try:
            count = int(read_count)
            canonical['reread_count'] = str(count)
            canonical['reread'] = '1' if count > 1 else '0'
        except (ValueError, TypeError):
            canonical['reread'] = None
            canonical['reread_count'] = None
    else:
        canonical['reread'] = None
        canonical['reread_count'] = None
    canonical['dnf'] = None
    canonical['dnf_reason'] = None
    canonical['pacing_rating'] = None
    canonical['tone'] = None
    canonical['vibe'] = None
    canonical['what_i_wanted'] = None
    canonical['did_it_deliver'] = None
    canonical['favorite_elements'] = None
    canonical['pet_peeves'] = None
    canonical['anchor_type'] = None
    canonical['would_recommend'] = None
    
    return canonical


def main():
    """
    Convert Goodreads export to canonical format.
    """
    project_root = Path(__file__).parent.parent
    sources_dir = project_root / 'sources'
    goodreads_file = sources_dir / 'goodreads_export.csv'
    output_file = sources_dir / 'goodreads_canonical.csv'
    
    if not goodreads_file.exists():
        print(f"Error: {goodreads_file} not found.")
        print("Please export your Goodreads library and save it as 'goodreads_export.csv' in the sources/ directory.")
        return
    
    print(f"Reading Goodreads export from {goodreads_file}...")
    goodreads_rows = read_csv_safe(str(goodreads_file))
    print(f"  Found {len(goodreads_rows)} books")
    
    print(f"Converting to canonical format...")
    canonical_rows = [map_goodreads_to_canonical(row) for row in goodreads_rows]
    
    # Define output fields (subset of canonical fields)
    output_fields = [
        'isbn13', 'asin', 'title', 'author', 'publication_year', 'publisher',
        'pages', 'genres', 'physical_owned', 'goodreads_id', 'goodreads_url', 'sources',
        'date_added', 'date_read', 'date_updated', 'read_status', 'rating',
        'reread', 'reread_count', 'notes', 'would_recommend'
    ]
    
    print(f"Writing canonical format to {output_file}...")
    write_csv_safe(str(output_file), canonical_rows, output_fields)
    print(f"  Wrote {len(canonical_rows)} books")
    
    print("\nDone! You can now run merge_and_dedupe.py to merge this into books.csv")


if __name__ == '__main__':
    main()

