#!/usr/bin/env python3
"""
Validation script for books.csv.
Checks data quality and flags issues.
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe
from utils.normalization import normalize_title, normalize_author, normalize_isbn13, normalize_asin


class ValidationResult:
    """Container for validation results."""
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
    
    def add_error(self, message: str, book: Dict = None):
        """Add an error message."""
        if book:
            title = book.get('title', 'Unknown')
            author = book.get('author', 'Unknown')
            self.errors.append(f"{message} | Book: {title} by {author}")
        else:
            self.errors.append(message)
    
    def add_warning(self, message: str, book: Dict = None):
        """Add a warning message."""
        if book:
            title = book.get('title', 'Unknown')
            author = book.get('author', 'Unknown')
            self.warnings.append(f"{message} | Book: {title} by {author}")
        else:
            self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add an info message."""
        self.info.append(message)
    
    def print_report(self):
        """Print validation report."""
        print("=" * 60)
        print("Validation Report")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        else:
            print("\n✅ No errors found")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        else:
            print("\n✅ No warnings")
        
        if self.info:
            print(f"\nℹ️  INFO ({len(self.info)}):")
            for info in self.info:
                print(f"  • {info}")
        
        print("\n" + "=" * 60)
        
        # Summary
        total_issues = len(self.errors) + len(self.warnings)
        if total_issues == 0:
            print("✅ Validation passed! Your books.csv looks good.")
        else:
            print(f"Found {total_issues} issue(s) ({len(self.errors)} errors, {len(self.warnings)} warnings)")


def validate_required_fields(books: List[Dict], result: ValidationResult):
    """Check that required fields are present."""
    required_fields = ['title', 'author']
    
    for book in books:
        for field in required_fields:
            if not book.get(field) or not book.get(field).strip():
                result.add_error(f"Missing required field: {field}", book)


def validate_identifiers(books: List[Dict], result: ValidationResult):
    """Validate identifier formats."""
    for book in books:
        isbn13 = book.get('isbn13')
        if isbn13:
            normalized = normalize_isbn13(isbn13)
            if not normalized:
                result.add_warning(f"Invalid ISBN13 format: {isbn13}", book)
        
        asin = book.get('asin')
        if asin:
            normalized = normalize_asin(asin)
            if not normalized:
                result.add_warning(f"Invalid ASIN format: {asin}", book)


def validate_ratings(books: List[Dict], result: ValidationResult):
    """Validate rating values."""
    for book in books:
        rating = book.get('rating')
        if rating:
            try:
                rating_val = float(rating)
                if rating_val < 1.0 or rating_val > 5.0:
                    result.add_error(f"Rating out of range (1-5): {rating_val}", book)
                # Check if it's a valid half-step
                if rating_val * 2 != int(rating_val * 2):
                    result.add_warning(f"Rating not a valid step (should be .0 or .5): {rating_val}", book)
            except (ValueError, TypeError):
                result.add_error(f"Invalid rating format: {rating}", book)


def validate_anchor_books(books: List[Dict], result: ValidationResult):
    """Check anchor books have sufficient data."""
    anchor_types = ['all_time_favorite', 'recent_hit', 'recent_miss', 'dnf']
    anchor_books = [b for b in books if b.get('anchor_type') in anchor_types]
    
    result.add_info(f"Found {len(anchor_books)} anchor books")
    
    for book in anchor_books:
        anchor_type = book.get('anchor_type')
        
        # All anchor books should have a rating
        if not book.get('rating'):
            result.add_warning(f"Anchor book ({anchor_type}) missing rating", book)
        
        # All-time favorites should have more data
        if anchor_type == 'all_time_favorite':
            if not book.get('favorite_elements'):
                result.add_warning("All-time favorite missing favorite_elements", book)
            if not book.get('tone') and not book.get('vibe'):
                result.add_warning("All-time favorite missing tone/vibe", book)
        
        # Recent misses should have pet_peeves or dnf_reason
        if anchor_type == 'recent_miss':
            if not book.get('pet_peeves') and not book.get('dnf_reason'):
                result.add_warning("Recent miss missing pet_peeves or dnf_reason", book)


def validate_dates(books: List[Dict], result: ValidationResult):
    """Validate date formats."""
    for book in books:
        date_fields = ['date_added', 'date_read', 'date_updated']
        for field in date_fields:
            date_val = book.get(field)
            if date_val:
                # Check format (YYYY-MM-DD or YYYY-MM)
                parts = date_val.split('-')
                if len(parts) not in [2, 3]:
                    result.add_warning(f"Date format may be invalid: {date_val} (expected YYYY-MM-DD)", book)
                elif len(parts) == 3:
                    try:
                        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                        if month < 1 or month > 12 or day < 1 or day > 31:
                            result.add_warning(f"Date values out of range: {date_val}", book)
                    except ValueError:
                        result.add_warning(f"Date contains non-numeric values: {date_val}", book)


def validate_duplicates(books: List[Dict], result: ValidationResult):
    """Check for potential duplicates (same ISBN/ASIN)."""
    isbn_map = defaultdict(list)
    asin_map = defaultdict(list)
    
    for idx, book in enumerate(books):
        isbn13 = normalize_isbn13(book.get('isbn13', ''))
        if isbn13:
            isbn_map[isbn13].append((idx, book))
        
        asin = normalize_asin(book.get('asin', ''))
        if asin:
            asin_map[asin].append((idx, book))
    
    # Check ISBN duplicates
    for isbn, entries in isbn_map.items():
        if len(entries) > 1:
            titles = [e[1].get('title', 'Unknown') for e in entries]
            result.add_error(f"Duplicate ISBN13 {isbn} found in {len(entries)} books: {', '.join(titles)}")
    
    # Check ASIN duplicates
    for asin, entries in asin_map.items():
        if len(entries) > 1:
            titles = [e[1].get('title', 'Unknown') for e in entries]
            result.add_warning(f"Duplicate ASIN {asin} found in {len(entries)} books: {', '.join(titles)}")


def validate_format_consistency(books: List[Dict], result: ValidationResult):
    """Check format flags are consistent with formats field."""
    for book in books:
        formats = (book.get('formats') or '').lower()
        kindle_owned = book.get('kindle_owned', '0')
        physical_owned = book.get('physical_owned', '0')
        audiobook_owned = book.get('audiobook_owned', '0')
        
        if 'kindle' in formats and kindle_owned != '1':
            result.add_warning("formats contains 'kindle' but kindle_owned is not 1", book)
        if 'physical' in formats and physical_owned != '1':
            result.add_warning("formats contains 'physical' but physical_owned is not 1", book)
        if 'audiobook' in formats and audiobook_owned != '1':
            result.add_warning("formats contains 'audiobook' but audiobook_owned is not 1", book)


def validate_all(books: List[Dict]) -> ValidationResult:
    """Run all validation checks."""
    result = ValidationResult()
    
    if not books:
        result.add_error("No books found in CSV")
        return result
    
    result.add_info(f"Validating {len(books)} books")
    
    validate_required_fields(books, result)
    validate_identifiers(books, result)
    validate_ratings(books, result)
    validate_dates(books, result)
    validate_duplicates(books, result)
    validate_format_consistency(books, result)
    validate_anchor_books(books, result)
    
    return result


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    books_csv = project_root / 'books.csv'
    
    if not books_csv.exists():
        print(f"Error: {books_csv} not found.")
        print("Please run merge_and_dedupe.py first to create books.csv")
        return
    
    print(f"Loading {books_csv}...")
    books = read_csv_safe(str(books_csv))
    
    print(f"Validating {len(books)} books...\n")
    result = validate_all(books)
    result.print_report()
    
    # Exit with error code if there are errors
    if result.errors:
        sys.exit(1)


if __name__ == '__main__':
    main()

