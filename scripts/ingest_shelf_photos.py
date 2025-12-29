#!/usr/bin/env python3
"""
Physical shelf photo ingestion script.
Extracts book titles and authors from photos of bookshelves using OCR.

This script:
1. Accepts image file(s) of bookshelves
2. Uses OCR to extract text from images
3. Parses titles and authors from the extracted text
4. Creates canonical entries and marks physical_owned=1
5. Integrates with merge pipeline to add to books.csv
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: OCR dependencies not installed. Install with: pip install pillow pytesseract", file=sys.stderr)

from utils.csv_utils import read_csv_safe, write_csv_safe
from utils.normalization import normalize_title, normalize_author

# Canonical fields
CANONICAL_FIELDS = [
    'work_id', 'isbn13', 'asin', 'title', 'author', 'publication_year', 'publisher',
    'language', 'pages', 'genres', 'tags', 'description', 'formats', 'physical_owned',
    'kindle_owned', 'audiobook_owned', 'goodreads_id', 'goodreads_url',
    'sources', 'date_added', 'date_read', 'date_updated',
    'read_status', 'rating', 'reread', 'reread_count', 'dnf', 'dnf_reason',
    'pacing_rating', 'tone', 'vibe', 'what_i_wanted', 'did_it_deliver',
    'favorite_elements', 'pet_peeves', 'notes', 'anchor_type', 'would_recommend'
]


def extract_text_from_image(image_path: Path) -> str:
    """
    Extract text from an image using OCR.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Extracted text as string
    """
    if not OCR_AVAILABLE:
        raise RuntimeError("OCR dependencies not installed. Install with: pip install pillow pytesseract")
    
    try:
        image = Image.open(image_path)
        # Use pytesseract to extract text
        # Configure for better book spine reading (vertical text, single column)
        text = pytesseract.image_to_string(
            image,
            config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,;:!?()-[]"\'' 
        )
        return text
    except Exception as e:
        raise RuntimeError(f"Error extracting text from image {image_path}: {e}")


def parse_books_from_text(text: str) -> List[Dict[str, str]]:
    """
    Parse book titles and authors from OCR-extracted text.
    
    This is a heuristic approach - book spines vary widely in format.
    Attempts to identify title/author patterns.
    
    Args:
        text: Raw OCR text from image
    
    Returns:
        List of dicts with 'title' and 'author' keys (may be incomplete)
    """
    books = []
    
    # Split into lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Common patterns for book spines:
    # - "Title by Author"
    # - "Title - Author"
    # - "Title\nAuthor" (on separate lines)
    # - Just "Title" (author may be on next line or missing)
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip very short lines (likely OCR noise)
        if len(line) < 3:
            i += 1
            continue
        
        # Pattern: "Title by Author"
        if ' by ' in line.lower():
            parts = re.split(r'\s+by\s+', line, flags=re.IGNORECASE)
            if len(parts) == 2:
                title = parts[0].strip()
                author = parts[1].strip()
                if title and author:
                    books.append({'title': title, 'author': author})
                    i += 1
                    continue
        
        # Pattern: "Title - Author" or "Title – Author"
        if ' - ' in line or ' – ' in line:
            parts = re.split(r'\s+[-–]\s+', line)
            if len(parts) == 2:
                title = parts[0].strip()
                author = parts[1].strip()
                if title and author:
                    books.append({'title': title, 'author': author})
                    i += 1
                    continue
        
        # Pattern: Title on one line, Author on next line
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            # Heuristic: if current line is longer and next line looks like an author (proper case, shorter)
            if len(line) > len(next_line) and next_line and line[0].isupper():
                # Check if next line looks like author name (proper case, not too long)
                if next_line[0].isupper() and len(next_line.split()) <= 4:
                    books.append({'title': line, 'author': next_line})
                    i += 2
                    continue
        
        # Fallback: treat line as title only (author missing)
        # Only if line looks reasonable (not too short, has some structure)
        if len(line) > 5 and ' ' in line:
            books.append({'title': line, 'author': None})
        
        i += 1
    
    return books


def create_canonical_entry(parsed_book: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    """
    Create a canonical book entry from parsed OCR data.
    
    Args:
        parsed_book: Dict with 'title' and optionally 'author'
    
    Returns:
        Canonical book entry dict
    """
    from datetime import datetime
    
    canonical = {}
    
    # Identifiers (will be empty from OCR)
    canonical['work_id'] = None  # Will be generated by merge pipeline
    canonical['isbn13'] = None
    canonical['asin'] = None
    
    # Title and author (from OCR)
    canonical['title'] = parsed_book.get('title')
    canonical['author'] = parsed_book.get('author')
    
    # Metadata (empty - OCR doesn't provide this)
    canonical['publication_year'] = None
    canonical['publisher'] = None
    canonical['language'] = None
    canonical['pages'] = None
    canonical['genres'] = None
    canonical['tags'] = None
    canonical['description'] = None
    
    # Formats and ownership
    canonical['formats'] = 'physical'
    canonical['physical_owned'] = '1'  # Key: mark as physically owned
    canonical['kindle_owned'] = '0'
    canonical['audiobook_owned'] = '0'
    
    # Source provenance
    canonical['goodreads_id'] = None
    canonical['goodreads_url'] = None
    canonical['sources'] = 'shelves'
    
    # Dates
    canonical['date_added'] = datetime.now().strftime('%Y-%m-%d')
    canonical['date_read'] = None
    canonical['date_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    # Status and preferences (empty - user can fill later)
    canonical['read_status'] = None
    canonical['rating'] = None
    canonical['reread'] = '0'
    canonical['reread_count'] = '0'
    canonical['dnf'] = '0'
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


def process_shelf_photos(
    image_paths: List[Path],
    dataset_path: Path,
    dry_run: bool = False
) -> Dict:
    """
    Process shelf photos and create canonical entries.
    
    Args:
        image_paths: List of image file paths
        dataset_path: Path to dataset directory
        dry_run: If True, don't write changes, just report
    
    Returns:
        Dictionary with statistics
    """
    if not OCR_AVAILABLE:
        print("Error: OCR dependencies not installed.", file=sys.stderr)
        print("Install with: pip install pillow pytesseract", file=sys.stderr)
        print("Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract", file=sys.stderr)
        sys.exit(1)
    
    sources_dir = dataset_path / 'sources'
    sources_dir.mkdir(parents=True, exist_ok=True)
    
    all_books = []
    
    print(f"Processing {len(image_paths)} image(s)...")
    
    for image_path in image_paths:
        if not image_path.exists():
            print(f"Warning: Image not found: {image_path}", file=sys.stderr)
            continue
        
        print(f"\nProcessing: {image_path.name}")
        print("  Extracting text with OCR...")
        
        try:
            text = extract_text_from_image(image_path)
            print(f"  Extracted {len(text)} characters")
            
            # Parse books from text
            print("  Parsing titles and authors...")
            parsed_books = parse_books_from_text(text)
            print(f"  Found {len(parsed_books)} potential books")
            
            # Create canonical entries
            for parsed_book in parsed_books:
                canonical = create_canonical_entry(parsed_book)
                all_books.append(canonical)
                
                title = canonical.get('title', 'Unknown')
                author = canonical.get('author', 'Unknown')
                print(f"    - {title} by {author}")
        
        except Exception as e:
            print(f"  Error processing {image_path.name}: {e}", file=sys.stderr)
            continue
    
    if not all_books:
        print("\nNo books found in images.")
        return {
            'images_processed': len(image_paths),
            'books_found': 0,
            'books_created': 0
        }
    
    # Write to canonical source file
    output_file = sources_dir / 'shelves_canonical.csv'
    
    if dry_run:
        print(f"\n🔍 DRY RUN MODE - Would write {len(all_books)} books to {output_file}")
    else:
        print(f"\nWriting {len(all_books)} books to {output_file}...")
        write_csv_safe(str(output_file), all_books, CANONICAL_FIELDS)
        print(f"✅ Wrote {output_file}")
        print(f"\nNext step: Run merge pipeline to add these books to books.csv:")
        print(f"  python scripts/merge_and_dedupe.py --dataset {dataset_path}")
    
    return {
        'images_processed': len(image_paths),
        'books_found': len(all_books),
        'books_created': len(all_books) if not dry_run else 0
    }


def main():
    parser = argparse.ArgumentParser(
        description='Extract books from shelf photos using OCR',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single image (dry run)
  python scripts/ingest_shelf_photos.py --dataset datasets/lindsay --dry-run photo1.jpg
  
  # Process multiple images
  python scripts/ingest_shelf_photos.py --dataset datasets/lindsay shelf1.jpg shelf2.jpg
  
  # Process all images in a directory
  python scripts/ingest_shelf_photos.py --dataset datasets/lindsay shelves/*.jpg

Note: Requires Tesseract OCR to be installed:
  - macOS: brew install tesseract
  - Linux: sudo apt-get install tesseract-ocr
  - Windows: Download from https://github.com/tesseract-ocr/tesseract

Also requires Python packages:
  pip install pillow pytesseract
        """
    )
    
    parser.add_argument(
        'images',
        nargs='+',
        type=str,
        help='Image file(s) to process (JPEG, PNG, etc.)'
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
        help='Show what would be created without writing files'
    )
    
    args = parser.parse_args()
    
    # Convert image paths to Path objects
    image_paths = [Path(img) for img in args.images]
    dataset_path = Path(args.dataset)
    
    if not dataset_path.exists():
        print(f"Error: Dataset directory not found: {dataset_path}", file=sys.stderr)
        sys.exit(1)
    
    # Process images
    stats = process_shelf_photos(
        image_paths=image_paths,
        dataset_path=dataset_path,
        dry_run=args.dry_run
    )
    
    # Print summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Images processed: {stats['images_processed']}")
    print(f"Books found: {stats['books_found']}")
    if args.dry_run:
        print(f"Books that would be created: {stats['books_created']}")
        print("\n🔍 This was a DRY RUN - no files were written")
    else:
        print(f"Books created: {stats['books_created']}")


if __name__ == '__main__':
    main()

