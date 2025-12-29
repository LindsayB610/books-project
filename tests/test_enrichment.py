"""
Tests for metadata enrichment script.
Focuses on critical safety logic: never overwrite existing data.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.enrich_metadata import (
    enrich_book_metadata,
    extract_isbn,
    fetch_openlibrary_data,
    fetch_google_books_data
)
from utils.csv_utils import is_manually_set


class TestExtractISBN:
    """Tests for ISBN extraction."""
    
    def test_extract_isbn13_valid(self):
        """Extract valid ISBN13."""
        book = {'isbn13': '9780590353427', 'title': 'Test Book'}
        isbn = extract_isbn(book)
        assert isbn == '9780590353427'
    
    def test_extract_isbn13_normalized(self):
        """Extract and normalize ISBN13 with hyphens."""
        book = {'isbn13': '978-0590353427', 'title': 'Test Book'}
        isbn = extract_isbn(book)
        assert isbn == '9780590353427'
    
    def test_extract_isbn_missing(self):
        """Return None when ISBN13 is missing."""
        book = {'title': 'Test Book', 'author': 'Author'}
        isbn = extract_isbn(book)
        assert isbn is None
    
    def test_extract_isbn_empty(self):
        """Return None when ISBN13 is empty."""
        book = {'isbn13': '', 'title': 'Test Book'}
        isbn = extract_isbn(book)
        assert isbn is None


class TestEnrichBookMetadataSafety:
    """Critical safety tests: never overwrite existing data."""
    
    def test_never_overwrite_existing_genres(self):
        """Never overwrite existing genres field."""
        book = {
            'isbn13': '9780590353427',
            'title': 'Test Book',
            'genres': 'Fantasy|Fiction',  # Already set
            'description': ''  # Empty
        }
        
        # Mock API to return different genres
        with patch('scripts.enrich_metadata.fetch_openlibrary_data') as mock_fetch:
            mock_fetch.return_value = {
                'genres': 'Science Fiction|Adventure',  # Different genres
                'description': 'A test description'
            }
            
            updated_book, stats = enrich_book_metadata(book, rate_limit=0)
            
            # Genres should NOT be overwritten
            assert updated_book['genres'] == 'Fantasy|Fiction'
            assert stats['genres_added'] is False
            
            # Description should be added (was empty)
            assert updated_book['description'] == 'A test description'
            assert stats['description_added'] is True
    
    def test_never_overwrite_existing_description(self):
        """Never overwrite existing description field."""
        book = {
            'isbn13': '9780590353427',
            'title': 'Test Book',
            'genres': '',  # Empty
            'description': 'Existing description'  # Already set
        }
        
        # Mock API to return different description
        with patch('scripts.enrich_metadata.fetch_openlibrary_data') as mock_fetch:
            mock_fetch.return_value = {
                'genres': 'Fantasy',
                'description': 'Different description'  # Different description
            }
            
            updated_book, stats = enrich_book_metadata(book, rate_limit=0)
            
            # Description should NOT be overwritten
            assert updated_book['description'] == 'Existing description'
            assert stats['description_added'] is False
            
            # Genres should be added (was empty)
            assert updated_book['genres'] == 'Fantasy'
            assert stats['genres_added'] is True
    
    def test_fill_empty_genres(self):
        """Can fill empty genres field."""
        book = {
            'isbn13': '9780590353427',
            'title': 'Test Book',
            'genres': '',  # Empty
            'description': ''  # Empty
        }
        
        with patch('scripts.enrich_metadata.fetch_openlibrary_data') as mock_fetch:
            mock_fetch.return_value = {
                'genres': 'Fantasy|Science Fiction',
                'description': 'A test description'
            }
            
            updated_book, stats = enrich_book_metadata(book, rate_limit=0)
            
            # Both should be filled
            assert updated_book['genres'] == 'Fantasy|Science Fiction'
            assert updated_book['description'] == 'A test description'
            assert stats['genres_added'] is True
            assert stats['description_added'] is True
    
    def test_fill_empty_genres_none_value(self):
        """Can fill genres when value is None."""
        book = {
            'isbn13': '9780590353427',
            'title': 'Test Book',
            'genres': None,  # None
            'description': None  # None
        }
        
        with patch('scripts.enrich_metadata.fetch_openlibrary_data') as mock_fetch:
            mock_fetch.return_value = {
                'genres': 'Fantasy',
                'description': 'A test description'
            }
            
            updated_book, stats = enrich_book_metadata(book, rate_limit=0)
            
            # Both should be filled
            assert updated_book['genres'] == 'Fantasy'
            assert updated_book['description'] == 'A test description'
            assert stats['genres_added'] is True
            assert stats['description_added'] is True
    
    def test_no_enrichment_when_both_filled(self):
        """Skip enrichment when both fields are already filled."""
        book = {
            'isbn13': '9780590353427',
            'title': 'Test Book',
            'genres': 'Fantasy',
            'description': 'Existing description'
        }
        
        with patch('scripts.enrich_metadata.fetch_openlibrary_data') as mock_fetch:
            updated_book, stats = enrich_book_metadata(book, rate_limit=0)
            
            # Should not call API at all
            mock_fetch.assert_not_called()
            assert stats['genres_added'] is False
            assert stats['description_added'] is False
            assert stats['api_calls'] == 0
    
    def test_no_enrichment_without_isbn(self):
        """Skip enrichment when ISBN is missing."""
        book = {
            'title': 'Test Book',
            'genres': '',
            'description': ''
        }
        
        with patch('scripts.enrich_metadata.fetch_openlibrary_data') as mock_fetch:
            updated_book, stats = enrich_book_metadata(book, rate_limit=0)
            
            # Should not call API
            mock_fetch.assert_not_called()
            assert stats['api_calls'] == 0
            assert stats['genres_added'] is False
            assert stats['description_added'] is False


class TestEnrichBookMetadataGoogleBooks:
    """Tests for Google Books fallback logic."""
    
    def test_google_books_fallback_when_openlibrary_missing_genres(self):
        """Use Google Books when OpenLibrary doesn't have genres."""
        book = {
            'isbn13': '9780590353427',
            'title': 'Test Book',
            'genres': '',
            'description': ''
        }
        
        with patch('scripts.enrich_metadata.fetch_openlibrary_data') as mock_ol, \
             patch('scripts.enrich_metadata.fetch_google_books_data') as mock_gb:
            
            # OpenLibrary returns only description
            mock_ol.return_value = {
                'description': 'OpenLibrary description'
            }
            
            # Google Books returns genres
            mock_gb.return_value = {
                'genres': 'Fantasy|Fiction'
            }
            
            updated_book, stats = enrich_book_metadata(
                book,
                use_google_books=True,
                rate_limit=0
            )
            
            # Should have both
            assert updated_book['genres'] == 'Fantasy|Fiction'
            assert updated_book['description'] == 'OpenLibrary description'
            assert stats['genres_added'] is True
            assert stats['description_added'] is True
            assert stats['api_calls'] == 2  # Both APIs called
    
    def test_google_books_not_called_when_openlibrary_has_everything(self):
        """Don't call Google Books if OpenLibrary has everything needed."""
        book = {
            'isbn13': '9780590353427',
            'title': 'Test Book',
            'genres': '',
            'description': ''
        }
        
        with patch('scripts.enrich_metadata.fetch_openlibrary_data') as mock_ol, \
             patch('scripts.enrich_metadata.fetch_google_books_data') as mock_gb:
            
            # OpenLibrary returns both
            mock_ol.return_value = {
                'genres': 'Fantasy',
                'description': 'Description'
            }
            
            updated_book, stats = enrich_book_metadata(
                book,
                use_google_books=True,
                rate_limit=0
            )
            
            # Google Books should not be called
            mock_gb.assert_not_called()
            assert stats['api_calls'] == 1  # Only OpenLibrary


class TestEnrichBookMetadataErrorHandling:
    """Tests for error handling."""
    
    def test_handles_api_error_gracefully(self):
        """Handle API errors without crashing (API returns None on error)."""
        book = {
            'isbn13': '9780590353427',
            'title': 'Test Book',
            'genres': '',
            'description': ''
        }
        
        with patch('scripts.enrich_metadata.fetch_openlibrary_data') as mock_fetch:
            # API returns None on error (as per actual implementation)
            mock_fetch.return_value = None
            
            # Should not crash
            updated_book, stats = enrich_book_metadata(book, rate_limit=0)
            
            # Book should be unchanged
            assert updated_book['genres'] == ''
            assert updated_book['description'] == ''
            assert stats['genres_added'] is False
            assert stats['description_added'] is False
    
    def test_handles_api_returns_none(self):
        """Handle when API returns None (book not found)."""
        book = {
            'isbn13': '9780590353427',
            'title': 'Test Book',
            'genres': '',
            'description': ''
        }
        
        with patch('scripts.enrich_metadata.fetch_openlibrary_data') as mock_fetch:
            mock_fetch.return_value = None
            
            updated_book, stats = enrich_book_metadata(book, rate_limit=0)
            
            # Book should be unchanged
            assert updated_book['genres'] == ''
            assert updated_book['description'] == ''
            assert stats['genres_added'] is False
            assert stats['description_added'] is False

