#!/usr/bin/env python3
"""
Goodreads export ingestion script.
Transforms Goodreads CSV export into canonical format.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe, write_csv_safe
from utils.normalization import normalize_isbn13


def map_goodreads_to_canonical(goodreads_row: dict) -> dict:
    """
    Map Goodreads export fields to canonical format.
    
    Maps strictly according to specification:
    - Exclusive Shelf ONLY for read_status (no inference from rating/Bookshelves)
    - Read Count → reread_count (int, default 0)
    - Owned Copies → physical_owned (1 if > 0, else 0)
    - Bookshelves → genres (comma to pipe-delimited)
    - All other fields per specification
    """
    canonical = {}
    
    # work_id - leave blank, let merge_and_dedupe assign/preserve
    canonical['work_id'] = None
    
    # Identifiers
    # isbn13 <- ISBN13 (fallback to ISBN if ISBN13 missing)
    # Normalize using normalize_isbn13; if normalization fails, set to None (do NOT keep dirty raw values)
    isbn13_raw = goodreads_row.get('ISBN13', '').strip() or goodreads_row.get('ISBN', '').strip()
    if isbn13_raw:
        normalized = normalize_isbn13(isbn13_raw)
        canonical['isbn13'] = normalized if normalized else None  # Only use if normalization succeeds
    else:
        canonical['isbn13'] = None
    
    canonical['asin'] = None  # Goodreads doesn't have ASIN
    
    # Basic info
    canonical['title'] = goodreads_row.get('Title', '').strip() or None
    canonical['author'] = goodreads_row.get('Author', '').strip() or None
    
    # Metadata
    # publication_year <- Year Published (fallback to Original Publication Year)
    canonical['publication_year'] = (
        goodreads_row.get('Year Published', '').strip() or 
        goodreads_row.get('Original Publication Year', '').strip() or 
        None
    )
    canonical['publisher'] = goodreads_row.get('Publisher', '').strip() or None
    canonical['language'] = None  # Goodreads doesn't have language
    canonical['pages'] = goodreads_row.get('Number of Pages', '').strip() or None
    
    # genres = None (reserved for external genre enrichment)
    canonical['genres'] = None
    
    # tags <- Bookshelves (user shelves/labels; convert comma-separated to pipe-delimited, lowercased)
    bookshelves = goodreads_row.get('Bookshelves', '').strip()
    if bookshelves:
        # Convert comma-separated to pipe-delimited, lowercase tags
        tags = [tag.strip().lower() for tag in bookshelves.split(',') if tag.strip()]
        canonical['tags'] = '|'.join(tags) if tags else None
    else:
        canonical['tags'] = None
    
    canonical['description'] = None  # Goodreads export doesn't include description
    
    # Formats
    canonical['formats'] = None
    
    # Ownership
    # physical_owned <- 1 if Owned Copies > 0 else 0 (if parse fails, set to None)
    owned_copies = goodreads_row.get('Owned Copies', '').strip()
    if owned_copies:
        try:
            owned_count = int(owned_copies)
            canonical['physical_owned'] = '1' if owned_count > 0 else '0'
        except (ValueError, TypeError):
            canonical['physical_owned'] = None  # Set to None if parse fails
    else:
        canonical['physical_owned'] = '0'
    
    canonical['kindle_owned'] = '0'
    canonical['audiobook_owned'] = '0'
    
    # Source provenance
    # goodreads_id <- Book Id
    canonical['goodreads_id'] = goodreads_row.get('Book Id', '').strip() or None
    # goodreads_url <- https://www.goodreads.com/book/show/{goodreads_id}
    canonical['goodreads_url'] = (
        f"https://www.goodreads.com/book/show/{canonical['goodreads_id']}" 
        if canonical['goodreads_id'] else None
    )
    canonical['sources'] = 'goodreads'
    
    # Dates
    # date_added <- Date Added (normalize to YYYY-MM-DD)
    # Accept %Y/%m/%d, %Y-%m-%d, and if encountered %Y/%m or %Y-%m leave as-is
    date_added = goodreads_row.get('Date Added', '').strip()
    if date_added:
        try:
            if '/' in date_added:
                # Try full date first
                try:
                    dt = datetime.strptime(date_added, '%Y/%m/%d')
                    canonical['date_added'] = dt.strftime('%Y-%m-%d')
                except ValueError:
                    # Try year/month only
                    try:
                        dt = datetime.strptime(date_added, '%Y/%m')
                        canonical['date_added'] = dt.strftime('%Y-%m')
                    except ValueError:
                        canonical['date_added'] = date_added
            else:
                # Try full date first
                try:
                    dt = datetime.strptime(date_added, '%Y-%m-%d')
                    canonical['date_added'] = dt.strftime('%Y-%m-%d')
                except ValueError:
                    # Try year/month only
                    try:
                        dt = datetime.strptime(date_added, '%Y-%m')
                        canonical['date_added'] = dt.strftime('%Y-%m')
                    except ValueError:
                        canonical['date_added'] = date_added
        except:
            canonical['date_added'] = date_added
    else:
        canonical['date_added'] = None
    
    # date_read - Do not populate from Goodreads anymore. Leave it None.
    canonical['date_read'] = None
    
    # date_updated <- today
    canonical['date_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    # read_status - Use Exclusive Shelf as the ONLY source
    # read -> read, currently-reading -> reading, to-read -> want_to_read
    # Do NOT infer from rating or Bookshelves
    exclusive_shelf = goodreads_row.get('Exclusive Shelf', '').strip().lower()
    if exclusive_shelf == 'read':
        canonical['read_status'] = 'read'
    elif exclusive_shelf == 'currently-reading':
        canonical['read_status'] = 'reading'
    elif exclusive_shelf == 'to-read':
        canonical['read_status'] = 'want_to_read'
    else:
        canonical['read_status'] = None
    
    # rating <- My Rating (allow blank)
    rating = goodreads_row.get('My Rating', '').strip()
    if rating and rating.isdigit():
        canonical['rating'] = rating
    else:
        canonical['rating'] = None
    
    # reread_count <- Read Count (int, default 0)
    # reread <- 1 if reread_count > 1 else 0
    read_count = goodreads_row.get('Read Count', '').strip()
    if read_count:
        try:
            count = int(read_count)
            canonical['reread_count'] = str(count)
            canonical['reread'] = '1' if count > 1 else '0'
        except (ValueError, TypeError):
            canonical['reread_count'] = '0'
            canonical['reread'] = '0'
    else:
        canonical['reread_count'] = '0'
        canonical['reread'] = '0'
    
    # dnf fields
    canonical['dnf'] = None
    canonical['dnf_reason'] = None
    
    # Preference fields (leave empty)
    canonical['pacing_rating'] = None
    canonical['tone'] = None
    canonical['vibe'] = None
    canonical['what_i_wanted'] = None
    canonical['did_it_deliver'] = None
    canonical['favorite_elements'] = None
    canonical['pet_peeves'] = None
    
    # notes <- My Review + Private Notes (append with labels)
    my_review = goodreads_row.get('My Review', '').strip()
    private_notes = goodreads_row.get('Private Notes', '').strip()
    
    if my_review and private_notes:
        canonical['notes'] = f"My Review: {my_review}\n\nPrivate Notes: {private_notes}"
    elif my_review:
        canonical['notes'] = f"My Review: {my_review}"
    elif private_notes:
        canonical['notes'] = f"Private Notes: {private_notes}"
    else:
        canonical['notes'] = None
    
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
    
    if not goodreads_rows:
        print("No books found in export.")
        return
    
    print(f"Converting to canonical format...")
    canonical_rows = [map_goodreads_to_canonical(row) for row in goodreads_rows]
    
    # Use full canonical schema
    CANONICAL_FIELDS = [
        'work_id', 'isbn13', 'asin', 'title', 'author', 'publication_year', 'publisher',
        'language', 'pages', 'genres', 'description', 'formats', 'physical_owned',
        'kindle_owned', 'audiobook_owned', 'goodreads_id', 'goodreads_url',
        'sources', 'date_added', 'date_read', 'date_updated',
        'read_status', 'rating', 'reread', 'reread_count', 'dnf', 'dnf_reason',
        'pacing_rating', 'tone', 'vibe', 'what_i_wanted', 'did_it_deliver',
        'favorite_elements', 'pet_peeves', 'notes', 'anchor_type', 'would_recommend'
    ]
    
    # Ensure all rows have all fields
    for row in canonical_rows:
        for field in CANONICAL_FIELDS:
            if field not in row:
                row[field] = None
    
    print(f"Writing canonical format to {output_file}...")
    write_csv_safe(str(output_file), canonical_rows, CANONICAL_FIELDS)
    print(f"  Wrote {len(canonical_rows)} books")
    
    # Preview first 3 rows (non-sensitive fields only)
    print("\n" + "=" * 80)
    print("Preview of first 3 mapped rows:")
    print("=" * 80)
    for idx, row in enumerate(canonical_rows[:3], 1):
        print(f"\nRow {idx}:")
        print(f"  Title: {row.get('title', 'N/A')}")
        print(f"  Author: {row.get('author', 'N/A')}")
        print(f"  ISBN13: {row.get('isbn13', 'N/A')}")
        print(f"  Read Status: {row.get('read_status', 'N/A')}")
        print(f"  Rating: {row.get('rating', 'N/A')}")
        print(f"  Reread Count: {row.get('reread_count', 'N/A')}")
        print(f"  Physical Owned: {row.get('physical_owned', 'N/A')}")
        print(f"  Tags: {row.get('tags', 'N/A')}")
        print(f"  Genres: {row.get('genres', 'N/A')}")
        print(f"  Goodreads ID: {row.get('goodreads_id', 'N/A')}")
    
    print("\nDone! You can now run merge_and_dedupe.py to merge this into books.csv")


if __name__ == '__main__':
    main()
