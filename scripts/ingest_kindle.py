#!/usr/bin/env python3
"""
Kindle library ingestion script.
Reads Kindle library data (CSV or JSON) and converts to canonical format.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe, write_csv_safe


def map_kindle_to_canonical(kindle_row: dict) -> dict:
    """
    Map Kindle library data to canonical format.
    
    Kindle data format may vary. Common fields:
    - Title, Author, ASIN, ISBN, Publication Date, etc.
    """
    canonical = {}
    
    # Identifiers
    canonical['isbn13'] = kindle_row.get('ISBN', '').strip() or kindle_row.get('ISBN13', '').strip() or None
    canonical['asin'] = kindle_row.get('ASIN', '').strip() or None
    canonical['title'] = kindle_row.get('Title', '').strip() or None
    canonical['author'] = kindle_row.get('Author', '').strip() or None
    
    # Metadata
    pub_date = kindle_row.get('Publication Date', '') or kindle_row.get('Year', '')
    if pub_date:
        # Try to extract year
        try:
            year = int(str(pub_date)[:4])
            canonical['publication_year'] = str(year)
        except:
            canonical['publication_year'] = str(pub_date).strip()
    else:
        canonical['publication_year'] = None
    
    canonical['publisher'] = kindle_row.get('Publisher', '').strip() or None
    canonical['pages'] = kindle_row.get('Pages', '').strip() or None
    canonical['genres'] = None  # Kindle doesn't typically have genres
    canonical['description'] = None
    
    # Formats
    canonical['formats'] = 'kindle'
    canonical['physical_owned'] = '0'
    canonical['kindle_owned'] = '1'
    canonical['audiobook_owned'] = '0'
    
    # Source provenance
    canonical['goodreads_id'] = None
    canonical['goodreads_url'] = None
    canonical['sources'] = 'kindle'
    
    # Dates
    canonical['date_added'] = datetime.now().strftime('%Y-%m-%d')
    canonical['date_read'] = None
    canonical['date_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    # Status (Kindle books are typically unread unless we have other info)
    canonical['read_status'] = 'unread'
    
    # Preference fields (not in Kindle data)
    canonical['rating'] = None
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
    canonical['notes'] = None
    canonical['anchor_type'] = None
    canonical['would_recommend'] = None
    
    return canonical


def load_kindle_json(json_file: Path) -> list:
    """
    Load Kindle library from JSON file.
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'books' in data:
        return data['books']
    elif isinstance(data, dict):
        return [data]
    else:
        return []


def main():
    """
    Convert Kindle library to canonical format.
    """
    project_root = Path(__file__).parent.parent
    sources_dir = project_root / 'sources'
    
    # Try CSV first, then JSON
    kindle_csv = sources_dir / 'kindle_library.csv'
    kindle_json = sources_dir / 'kindle_library.json'
    output_file = sources_dir / 'kindle_canonical.csv'
    
    kindle_data = []
    
    if kindle_csv.exists():
        print(f"Reading Kindle library from {kindle_csv}...")
        kindle_data = read_csv_safe(str(kindle_csv))
        print(f"  Found {len(kindle_data)} books")
    elif kindle_json.exists():
        print(f"Reading Kindle library from {kindle_json}...")
        kindle_data = load_kindle_json(kindle_json)
        print(f"  Found {len(kindle_data)} books")
    else:
        print(f"Error: No Kindle library file found.")
        print("Please save your Kindle library as 'kindle_library.csv' or 'kindle_library.json' in the sources/ directory.")
        return
    
    print(f"Converting to canonical format...")
    canonical_rows = [map_kindle_to_canonical(row) for row in kindle_data]
    
    # Define output fields
    output_fields = [
        'isbn13', 'asin', 'title', 'author', 'publication_year', 'publisher',
        'pages', 'formats', 'kindle_owned', 'sources',
        'date_added', 'date_updated', 'read_status'
    ]
    
    print(f"Writing canonical format to {output_file}...")
    write_csv_safe(str(output_file), canonical_rows, output_fields)
    print(f"  Wrote {len(canonical_rows)} books")
    
    print("\nDone! You can now run merge_and_dedupe.py to merge this into books.csv")


if __name__ == '__main__':
    main()

