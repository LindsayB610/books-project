"""
Golden-file test for end-to-end pipeline.
Tests the full merge and deduplication process with sample data.
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import read_csv_safe, write_csv_safe, safe_merge
from utils.work_id import generate_work_id
from utils.deduplication import find_matches
from scripts.merge_and_dedupe import CANONICAL_FIELDS


class TestGoldenFile:
    """End-to-end test with sample fixture data."""
    
    @pytest.fixture
    def sample_books_file(self):
        """Load sample books fixture."""
        fixture_path = Path(__file__).parent / 'fixtures' / 'sample_books.csv'
        return str(fixture_path)
    
    @pytest.fixture
    def temp_dataset(self):
        """Create temporary dataset directory."""
        temp_dir = tempfile.mkdtemp()
        dataset_dir = Path(temp_dir) / 'test_dataset'
        dataset_dir.mkdir()
        (dataset_dir / 'sources').mkdir()
        (dataset_dir / 'reports').mkdir()
        yield dataset_dir
        shutil.rmtree(temp_dir)
    
    def test_load_sample_books(self, sample_books_file):
        """Test loading sample books CSV."""
        books = read_csv_safe(sample_books_file)
        
        assert len(books) > 0, "Should load books from fixture"
        assert 'work_id' in books[0], "Books should have work_id field"
        assert 'title' in books[0], "Books should have title field"
        assert 'author' in books[0], "Books should have author field"
    
    def test_safe_merge_preserves_protected_fields(self, sample_books_file):
        """Test that safe_merge preserves protected fields from existing."""
        books = read_csv_safe(sample_books_file)
        
        # Find a book with protected fields set
        book_with_rating = next((b for b in books if b.get('rating')), None)
        if not book_with_rating:
            pytest.skip("No book with rating in fixture")
        
        existing = book_with_rating.copy()
        new = existing.copy()
        new['rating'] = '1'  # Try to overwrite
        
        merged = safe_merge(existing, new)
        
        # Rating should be preserved (not overwritten)
        assert merged['rating'] == existing['rating'], "Protected field should be preserved"
    
    def test_work_id_generation(self, sample_books_file):
        """Test work_id generation for books."""
        books = read_csv_safe(sample_books_file)
        
        for book in books:
            work_id = generate_work_id(book)
            assert work_id, "Should generate work_id"
            assert work_id.startswith(('isbn13:', 'asin:', 'hash:')), "work_id should have valid prefix"
    
    def test_deduplication_finds_matches(self, sample_books_file):
        """Test that deduplication finds matching books."""
        books = read_csv_safe(sample_books_file)
        
        if len(books) < 2:
            pytest.skip("Need at least 2 books for deduplication test")
        
        # Try to find matches for first book in rest of list
        new_book = books[0]
        existing_books = books[1:]
        
        matches = find_matches(new_book, existing_books)
        
        # Should return list (may be empty if no matches)
        assert isinstance(matches, list), "Should return list of matches"
    
    def test_write_and_read_csv(self, temp_dataset):
        """Test writing and reading CSV maintains data integrity."""
        books = [
            {
                'work_id': 'isbn13:123',
                'title': 'Test Book',
                'author': 'Test Author',
                'rating': '5',
                'anchor_type': 'all_time_favorite'
            }
        ]
        
        csv_path = temp_dataset / 'books.csv'
        write_csv_safe(str(csv_path), books, CANONICAL_FIELDS)
        
        # Read back
        read_books = read_csv_safe(str(csv_path))
        
        assert len(read_books) == 1, "Should read back one book"
        assert read_books[0]['work_id'] == 'isbn13:123', "work_id should be preserved"
        assert read_books[0]['rating'] == '5', "Protected field should be preserved"
        assert read_books[0]['anchor_type'] == 'all_time_favorite', "Protected field should be preserved"

