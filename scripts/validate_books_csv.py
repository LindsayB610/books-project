#!/usr/bin/env python3
"""
Validation script for books.csv.
Scans and reports data quality issues without auto-fixing.
Safe to run before and after merges.
"""

import sys
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe
from utils.normalization import normalize_isbn13, normalize_asin


class ValidationReport:
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
            work_id = book.get('work_id', 'N/A')
            self.errors.append(f"{message} | Book: {title} by {author} (work_id: {work_id})")
        else:
            self.errors.append(message)
    
    def add_warning(self, message: str, book: Dict = None):
        """Add a warning message."""
        if book:
            title = book.get('title', 'Unknown')
            author = book.get('author', 'Unknown')
            work_id = book.get('work_id', 'N/A')
            self.warnings.append(f"{message} | Book: {title} by {author} (work_id: {work_id})")
        else:
            self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add an info message."""
        self.info.append(message)
    
    def print_report(self):
        """Print human-readable validation report."""
        print("=" * 80)
        print("Books CSV Validation Report")
        print("=" * 80)
        
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
        
        print("\n" + "=" * 80)
        
        # Summary
        total_issues = len(self.errors) + len(self.warnings)
        if total_issues == 0:
            print("✅ Validation passed! Your books.csv looks good.")
        else:
            print(f"Found {total_issues} issue(s) ({len(self.errors)} errors, {len(self.warnings)} warnings)")
            print("\n💡 Tip: Review and fix issues manually. This script does not auto-fix.")


def validate_work_ids(books: List[Dict], report: ValidationReport):
    """Check for duplicate work_ids."""
    work_id_map = defaultdict(list)
    
    for idx, book in enumerate(books):
        work_id = book.get('work_id', '').strip()
        if not work_id:
            report.add_error("Missing work_id", book)
        else:
            work_id_map[work_id].append((idx, book))
    
    # Check for duplicates
    for work_id, entries in work_id_map.items():
        if len(entries) > 1:
            titles = [e[1].get('title', 'Unknown') for e in entries]
            report.add_error(f"Duplicate work_id: {work_id} found in {len(entries)} books: {', '.join(titles)}")


def validate_identifiers(books: List[Dict], report: ValidationReport):
    """Check for duplicate ISBN13 or ASIN."""
    isbn_map = defaultdict(list)
    asin_map = defaultdict(list)
    
    for idx, book in enumerate(books):
        isbn13 = book.get('isbn13', '').strip()
        if isbn13:
            normalized = normalize_isbn13(isbn13)
            if not normalized:
                report.add_warning(f"Invalid ISBN13 format: {isbn13}", book)
            else:
                isbn_map[normalized].append((idx, book))
        
        asin = book.get('asin', '').strip()
        if asin:
            normalized = normalize_asin(asin)
            if not normalized:
                report.add_warning(f"Invalid ASIN format: {asin}", book)
            else:
                asin_map[normalized].append((idx, book))
    
    # Check for duplicate ISBN13
    for isbn, entries in isbn_map.items():
        if len(entries) > 1:
            titles = [e[1].get('title', 'Unknown') for e in entries]
            report.add_error(f"Duplicate ISBN13 {isbn} found in {len(entries)} books: {', '.join(titles)}")
    
    # Check for duplicate ASIN
    for asin, entries in asin_map.items():
        if len(entries) > 1:
            titles = [e[1].get('title', 'Unknown') for e in entries]
            report.add_error(f"Duplicate ASIN {asin} found in {len(entries)} books: {', '.join(titles)}")


def validate_required_fields(books: List[Dict], report: ValidationReport):
    """Check that required fields are present."""
    required_fields = ['title', 'author']
    
    for book in books:
        for field in required_fields:
            value = book.get(field, '').strip() if book.get(field) else ''
            if not value:
                report.add_error(f"Missing required field: {field}", book)


def validate_ratings(books: List[Dict], report: ValidationReport):
    """Validate rating values (1-5, allow halves)."""
    for book in books:
        rating = book.get('rating', '').strip()
        if rating:
            try:
                rating_val = float(rating)
                if rating_val < 1.0 or rating_val > 5.0:
                    report.add_error(f"Rating out of range (1-5): {rating_val}", book)
                # Check if it's a valid step (0.0 or 0.5)
                remainder = (rating_val * 2) % 1
                if remainder != 0:
                    report.add_warning(f"Rating not a standard step (should be .0 or .5): {rating_val}", book)
            except (ValueError, TypeError):
                report.add_error(f"Invalid rating format: {rating}", book)


def validate_reread_count(books: List[Dict], report: ValidationReport):
    """Validate reread_count is an integer."""
    for book in books:
        reread_count = book.get('reread_count', '').strip()
        if reread_count:
            try:
                count = int(reread_count)
                if count < 0:
                    report.add_warning(f"reread_count is negative: {count}", book)
            except (ValueError, TypeError):
                report.add_error(f"reread_count must be an integer: {reread_count}", book)


def validate_enums(books: List[Dict], report: ValidationReport):
    """Validate enum fields have valid values."""
    valid_read_status = {'read', 'unread', 'dnf', 'reading', 'want_to_read', ''}
    valid_anchor_type = {'all_time_favorite', 'recent_hit', 'recent_miss', 'dnf', ''}
    valid_boolean_fields = {'0', '1', ''}
    
    for book in books:
        # read_status
        read_status = book.get('read_status', '').strip().lower()
        if read_status and read_status not in valid_read_status:
            report.add_warning(f"Invalid read_status: {read_status} (expected: {', '.join(valid_read_status - {''})})", book)
        
        # anchor_type
        anchor_type = book.get('anchor_type', '').strip().lower()
        if anchor_type and anchor_type not in valid_anchor_type:
            report.add_warning(f"Invalid anchor_type: {anchor_type} (expected: {', '.join(valid_anchor_type - {''})})", book)
        
        # Boolean fields (0/1)
        boolean_fields = ['reread', 'dnf', 'did_it_deliver', 'would_recommend']
        for field in boolean_fields:
            value = book.get(field, '').strip()
            if value and value not in valid_boolean_fields:
                report.add_warning(f"Invalid {field} value: {value} (expected: 0, 1, or empty)", book)


def validate_delimiters(books: List[Dict], report: ValidationReport):
    """Check that pipe-delimited fields don't contain accidental commas."""
    pipe_delimited_fields = ['genres', 'formats', 'sources']
    
    for book in books:
        for field in pipe_delimited_fields:
            value = book.get(field, '').strip()
            if value:
                # Check if it contains commas (which suggests wrong delimiter)
                if ',' in value and '|' not in value:
                    report.add_warning(f"Field {field} contains commas but no pipes - should be pipe-delimited", book)
                # Check for mixed delimiters
                if ',' in value and '|' in value:
                    report.add_warning(f"Field {field} contains both commas and pipes - inconsistent delimiter", book)


def validate_all(books: List[Dict]) -> ValidationReport:
    """Run all validation checks."""
    report = ValidationReport()
    
    if not books:
        report.add_error("No books found in CSV")
        return report
    
    report.add_info(f"Validating {len(books)} books")
    
    validate_work_ids(books, report)
    validate_identifiers(books, report)
    validate_required_fields(books, report)
    validate_ratings(books, report)
    validate_reread_count(books, report)
    validate_enums(books, report)
    validate_delimiters(books, report)
    
    return report


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate books.csv for data quality issues')
    parser.add_argument('--csv', type=str, help='Path to books.csv (default: books.csv in project root)')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    books_csv = Path(args.csv) if args.csv else project_root / 'books.csv'
    
    if not books_csv.exists():
        print(f"Error: {books_csv} not found.")
        print("Please run merge_and_dedupe.py first to create books.csv")
        sys.exit(1)
    
    print(f"Loading {books_csv}...")
    books = read_csv_safe(str(books_csv))
    
    print(f"Validating {len(books)} books...\n")
    report = validate_all(books)
    report.print_report()
    
    # Exit with error code if there are errors
    if report.errors:
        sys.exit(1)


if __name__ == '__main__':
    main()

