#!/usr/bin/env python3
"""
External metadata enrichment script.
Populates empty genres and description fields using OpenLibrary and Google Books APIs.

Only fills empty fields - never overwrites existing data.
Respects rate limits and includes dry-run mode.
"""

import sys
import json
import re
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe, write_csv_safe, is_manually_set
from utils.normalization import normalize_isbn13

# Canonical fields (for CSV writing)
CANONICAL_FIELDS = [
    'work_id', 'isbn13', 'asin', 'title', 'author', 'publication_year', 'publisher',
    'language', 'pages', 'genres', 'tags', 'description', 'formats', 'physical_owned',
    'kindle_owned', 'audiobook_owned', 'goodreads_id', 'goodreads_url',
    'sources', 'date_added', 'date_read', 'date_updated',
    'read_status', 'rating', 'reread', 'reread_count', 'dnf', 'dnf_reason',
    'pacing_rating', 'tone', 'vibe', 'what_i_wanted', 'did_it_deliver',
    'favorite_elements', 'pet_peeves', 'notes', 'anchor_type', 'would_recommend'
]


def isbn10_to_isbn13(isbn10: str) -> Optional[str]:
    """
    Convert ISBN-10 to ISBN-13.
    Simplified conversion - just adds 978 prefix and calculates check digit.
    """
    if not isbn10 or len(isbn10) != 10:
        return None
    
    # Remove hyphens
    isbn10 = isbn10.replace('-', '').replace(' ', '')
    if len(isbn10) != 10 or not isbn10[:-1].isdigit():
        return None
    
    # Prefix with 978
    isbn13_base = '978' + isbn10[:-1]
    
    # Calculate check digit
    total = 0
    for i, digit in enumerate(isbn13_base):
        multiplier = 1 if i % 2 == 0 else 3
        total += int(digit) * multiplier
    
    check_digit = (10 - (total % 10)) % 10
    return isbn13_base + str(check_digit)


def extract_isbn(book: Dict) -> Optional[str]:
    """
    Extract ISBN13 from book record.
    Returns normalized ISBN13 string or None.
    """
    isbn13 = book.get('isbn13')
    if isbn13:
        normalized = normalize_isbn13(isbn13)
        if normalized:
            return normalized
    
    # If no ISBN13, try converting ISBN10 (if present in other fields)
    # This is a fallback - most books should have ISBN13
    return None


def fetch_openlibrary_data(isbn: str, timeout: int = 10) -> Optional[Dict]:
    """
    Fetch book metadata from OpenLibrary API.
    Returns dict with 'genres' and 'description' keys, or None if not found.
    """
    try:
        # Try ISBN-13 first
        url = f"https://openlibrary.org/isbn/{isbn}.json"
        request = Request(url, headers={'User-Agent': 'Books-CSV-Enrichment/1.0'})
        
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Extract subjects/genres
            subjects = data.get('subjects', [])
            genres_list = []
            for subject in subjects:
                if isinstance(subject, str):
                    # Filter out very generic subjects
                    subject_lower = subject.lower()
                    # Skip overly generic subjects
                    if subject_lower not in ['accessible book', 'protected daisy', 'fiction', 'nonfiction']:
                        genres_list.append(subject)
            
            # Extract description
            description = None
            desc_value = data.get('description')
            if isinstance(desc_value, str):
                description = desc_value
            elif isinstance(desc_value, dict):
                # Can be {"type": "/type/text", "value": "..."}
                description = desc_value.get('value')
            
            # Clean up description (remove HTML tags, limit length)
            if description:
                # Simple HTML tag removal
                description = re.sub(r'<[^>]+>', '', description)
                # Limit length to reasonable size (5000 chars)
                if len(description) > 5000:
                    description = description[:5000].rsplit('.', 1)[0] + '.'
            
            result = {}
            if genres_list:
                # Convert to pipe-delimited format (sorted for consistency)
                result['genres'] = '|'.join(sorted(set(genres_list)))
            if description:
                result['description'] = description.strip()
            
            return result if result else None
            
    except HTTPError as e:
        if e.code == 404:
            # Book not found - this is fine
            return None
        # Other HTTP errors - log but continue
        print(f"  Warning: OpenLibrary HTTP error {e.code} for ISBN {isbn}", file=sys.stderr)
        return None
    except (URLError, json.JSONDecodeError, KeyError, ValueError) as e:
        # Network errors, JSON parsing errors, etc.
        print(f"  Warning: OpenLibrary error for ISBN {isbn}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        # Unexpected errors
        print(f"  Warning: Unexpected error fetching OpenLibrary data for ISBN {isbn}: {e}", file=sys.stderr)
        return None


def fetch_google_books_data(isbn: str, timeout: int = 10) -> Optional[Dict]:
    """
    Fetch book metadata from Google Books API (fallback).
    Returns dict with 'genres' and 'description' keys, or None if not found.
    """
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        request = Request(url, headers={'User-Agent': 'Books-CSV-Enrichment/1.0'})
        
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if not data.get('items'):
                return None
            
            # Get first result
            volume_info = data['items'][0].get('volumeInfo', {})
            
            # Extract categories (genres)
            categories = volume_info.get('categories', [])
            genres_list = []
            for category in categories:
                if isinstance(category, str):
                    category_lower = category.lower()
                    # Filter out generic categories
                    if category_lower not in ['general', 'fiction', 'nonfiction']:
                        genres_list.append(category)
            
            # Extract description
            description = volume_info.get('description')
            if description:
                # Clean up description
                description = re.sub(r'<[^>]+>', '', description)
                if len(description) > 5000:
                    description = description[:5000].rsplit('.', 1)[0] + '.'
            
            result = {}
            if genres_list:
                result['genres'] = '|'.join(sorted(set(genres_list)))
            if description:
                result['description'] = description.strip()
            
            return result if result else None
            
    except (HTTPError, URLError, json.JSONDecodeError, KeyError, ValueError) as e:
        # Silently fail - this is a fallback
        return None
    except Exception as e:
        return None


def enrich_book_metadata(book: Dict, use_google_books: bool = False, rate_limit: float = 0.5) -> Tuple[Dict, Dict]:
    """
    Enrich a single book's metadata from external APIs.
    
    Args:
        book: Book dictionary from CSV
        use_google_books: Whether to try Google Books as fallback
        rate_limit: Seconds to wait between API calls
    
    Returns:
        Tuple of (updated_book_dict, enrichment_stats)
        enrichment_stats has keys: 'genres_added', 'description_added', 'api_calls'
    """
    stats = {'genres_added': False, 'description_added': False, 'api_calls': 0}
    
    # Check if we need to enrich anything
    needs_genres = not is_manually_set(book.get('genres'))
    needs_description = not is_manually_set(book.get('description'))
    
    if not needs_genres and not needs_description:
        return book, stats
    
    # Extract ISBN
    isbn = extract_isbn(book)
    if not isbn:
        # No ISBN available - can't enrich
        return book, stats
    
    metadata = {}
    
    # Try OpenLibrary first
    time.sleep(rate_limit)  # Rate limiting
    ol_metadata = fetch_openlibrary_data(isbn)
    stats['api_calls'] += 1
    
    if ol_metadata:
        metadata.update(ol_metadata)
    
    # If OpenLibrary didn't have what we need, try Google Books
    if use_google_books:
        still_needs_genres = needs_genres and not metadata.get('genres')
        still_needs_description = needs_description and not metadata.get('description')
        
        if still_needs_genres or still_needs_description:
            time.sleep(rate_limit)
            google_metadata = fetch_google_books_data(isbn)
            stats['api_calls'] += 1
            
            if google_metadata:
                # Merge Google Books data into metadata (only if we still need it)
                if still_needs_genres and google_metadata.get('genres'):
                    metadata['genres'] = google_metadata['genres']
                if still_needs_description and google_metadata.get('description'):
                    metadata['description'] = google_metadata['description']
    
    # Apply metadata to book (only fill empty fields)
    updated_book = book.copy()
    if metadata:
        if needs_genres and metadata.get('genres'):
            updated_book['genres'] = metadata['genres']
            stats['genres_added'] = True
        
        if needs_description and metadata.get('description'):
            updated_book['description'] = metadata['description']
            stats['description_added'] = True
    
    return updated_book, stats


def enrich_dataset(
    dataset_path: Path,
    dry_run: bool = False,
    fields: Optional[List[str]] = None,
    use_google_books: bool = False,
    rate_limit: float = 0.5,
    max_books: Optional[int] = None
) -> Dict:
    """
    Enrich metadata for all books in a dataset.
    
    Args:
        dataset_path: Path to dataset directory
        dry_run: If True, don't write changes, just report
        fields: List of fields to enrich ('genres', 'description'), or None for all
        use_google_books: Whether to use Google Books as fallback
        rate_limit: Seconds to wait between API calls
        max_books: Maximum number of books to process (for testing)
    
    Returns:
        Dictionary with statistics about enrichment
    """
    books_csv = dataset_path / 'books.csv'
    
    if not books_csv.exists():
        print(f"Error: books.csv not found at {books_csv}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Reading books from {books_csv}...")
    books = read_csv_safe(str(books_csv))
    print(f"Loaded {len(books)} books")
    
    # Determine which fields to enrich
    enrich_genres = fields is None or 'genres' in fields
    enrich_description = fields is None or 'description' in fields
    
    if not enrich_genres and not enrich_description:
        print("Error: No valid fields specified for enrichment", file=sys.stderr)
        sys.exit(1)
    
    # Filter books that need enrichment
    books_to_enrich = []
    for book in books:
        has_isbn = bool(extract_isbn(book))
        needs_enrichment = (
            (enrich_genres and not is_manually_set(book.get('genres'))) or
            (enrich_description and not is_manually_set(book.get('description')))
        )
        if has_isbn and needs_enrichment:
            books_to_enrich.append(book)
    
    print(f"\nBooks needing enrichment: {len(books_to_enrich)} (with ISBN and empty fields)")
    if max_books:
        books_to_enrich = books_to_enrich[:max_books]
        print(f"Limiting to {max_books} books for this run")
    
    if not books_to_enrich:
        print("No books need enrichment (all fields already filled or no ISBNs available)")
        return {
            'total_books': len(books),
            'enriched': 0,
            'genres_added': 0,
            'descriptions_added': 0,
            'api_calls': 0,
            'errors': 0
        }
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be written\n")
    
    # Enrich books
    enriched_count = 0
    genres_added = 0
    descriptions_added = 0
    total_api_calls = 0
    errors = 0
    
    for i, book in enumerate(books_to_enrich, 1):
        title = book.get('title', 'Unknown')
        author = book.get('author', 'Unknown')
        isbn = extract_isbn(book)
        
        print(f"[{i}/{len(books_to_enrich)}] Enriching: {title} by {author} (ISBN: {isbn})")
        
        try:
            updated_book, stats = enrich_book_metadata(
                book,
                use_google_books=use_google_books,
                rate_limit=rate_limit
            )
            
            total_api_calls += stats['api_calls']
            
            if stats['genres_added'] or stats['description_added']:
                enriched_count += 1
                if stats['genres_added']:
                    genres_added += 1
                    print(f"  ✅ Added genres: {updated_book.get('genres', '')[:100]}")
                if stats['description_added']:
                    descriptions_added += 1
                    desc_preview = updated_book.get('description', '')[:100]
                    print(f"  ✅ Added description: {desc_preview}...")
                
                # Update book in list
                book_idx = books.index(book)
                books[book_idx] = updated_book
            else:
                print(f"  ⚠️  No metadata found")
        except Exception as e:
            errors += 1
            print(f"  ❌ Error: {e}", file=sys.stderr)
    
    # Write updated CSV
    if not dry_run and enriched_count > 0:
        print(f"\nWriting updated books.csv...")
        write_csv_safe(str(books_csv), books, CANONICAL_FIELDS)
        print(f"✅ Updated {books_csv}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("Enrichment Summary")
    print("=" * 80)
    print(f"Total books in dataset: {len(books)}")
    print(f"Books processed: {len(books_to_enrich)}")
    print(f"Books enriched: {enriched_count}")
    print(f"  - Genres added: {genres_added}")
    print(f"  - Descriptions added: {descriptions_added}")
    print(f"API calls made: {total_api_calls}")
    print(f"Errors: {errors}")
    if dry_run:
        print("\n🔍 This was a DRY RUN - no changes were written")
    
    return {
        'total_books': len(books),
        'enriched': enriched_count,
        'genres_added': genres_added,
        'descriptions_added': descriptions_added,
        'api_calls': total_api_calls,
        'errors': errors
    }


def main():
    parser = argparse.ArgumentParser(
        description='Enrich book metadata from external APIs (OpenLibrary, Google Books)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be enriched
  python scripts/enrich_metadata.py --dataset datasets/lindsay --dry-run
  
  # Actually enrich (genres and descriptions)
  python scripts/enrich_metadata.py --dataset datasets/lindsay
  
  # Enrich only genres
  python scripts/enrich_metadata.py --dataset datasets/lindsay --fields genres
  
  # Use Google Books as fallback
  python scripts/enrich_metadata.py --dataset datasets/lindsay --use-google-books
  
  # Slower rate limiting (1 second between requests)
  python scripts/enrich_metadata.py --dataset datasets/lindsay --rate-limit 1.0
        """
    )
    
    parser.add_argument(
        '--dataset',
        type=str,
        default='datasets/default',
        help='Path to dataset directory (default: datasets/default)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be enriched without making changes'
    )
    
    parser.add_argument(
        '--fields',
        type=str,
        help='Comma-separated list of fields to enrich (genres,description). Default: both'
    )
    
    parser.add_argument(
        '--use-google-books',
        action='store_true',
        help='Use Google Books API as fallback (OpenLibrary is tried first)'
    )
    
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=0.5,
        help='Seconds to wait between API calls (default: 0.5)'
    )
    
    parser.add_argument(
        '--max-books',
        type=int,
        help='Maximum number of books to process (for testing)'
    )
    
    args = parser.parse_args()
    
    # Parse dataset path
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"Error: Dataset directory not found: {dataset_path}", file=sys.stderr)
        sys.exit(1)
    
    # Parse fields
    fields = None
    if args.fields:
        fields = [f.strip() for f in args.fields.split(',')]
        valid_fields = {'genres', 'description'}
        invalid = [f for f in fields if f not in valid_fields]
        if invalid:
            print(f"Error: Invalid fields: {invalid}. Valid fields are: {', '.join(valid_fields)}", file=sys.stderr)
            sys.exit(1)
    
    # Run enrichment
    enrich_dataset(
        dataset_path=dataset_path,
        dry_run=args.dry_run,
        fields=fields,
        use_google_books=args.use_google_books,
        rate_limit=args.rate_limit,
        max_books=args.max_books
    )


if __name__ == '__main__':
    main()

