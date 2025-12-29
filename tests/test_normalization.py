"""
Tests for normalization utilities.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.normalization import (
    normalize_title, normalize_author,
    normalize_isbn13, normalize_asin,
    compute_canonical_id
)


class TestNormalizeTitle:
    """Tests for normalize_title()."""
    
    def test_lowercase(self):
        """Title should be lowercased."""
        assert normalize_title("The Great Gatsby") == "great gatsby"
    
    def test_remove_punctuation(self):
        """Punctuation should be removed."""
        assert normalize_title("Harry Potter & The Philosopher's Stone") == "harry potter the philosophers stone"
        assert normalize_title("1984") == "1984"  # Numbers preserved
    
    def test_remove_common_prefixes(self):
        """Common prefixes (the, a, an) should be removed."""
        assert normalize_title("The Great Gatsby") == "great gatsby"
        assert normalize_title("A Tale of Two Cities") == "tale of two cities"
        assert normalize_title("An American Tragedy") == "american tragedy"
    
    def test_normalize_whitespace(self):
        """Multiple spaces should be normalized to single space."""
        assert normalize_title("The   Great    Gatsby") == "great gatsby"
    
    def test_empty_title(self):
        """Empty title should return empty string."""
        assert normalize_title("") == ""
        assert normalize_title("   ") == ""


class TestNormalizeAuthor:
    """Tests for normalize_author()."""
    
    def test_last_first_format(self):
        """Author in 'Last, First' format should be normalized."""
        assert normalize_author("Smith, John") == "Smith, John"
        assert normalize_author("smith, john") == "Smith, John"  # Case normalized
    
    def test_first_last_format(self):
        """Author in 'First Last' format should be converted."""
        assert normalize_author("John Smith") == "Smith, John"
        assert normalize_author("J.K. Rowling") == "Rowling, J.K."
    
    def test_multiple_words(self):
        """Multiple word names should be handled."""
        assert normalize_author("Mary Jane Watson") == "Watson, Mary Jane"
        assert normalize_author("F. Scott Fitzgerald") == "Fitzgerald, F. Scott"
    
    def test_single_name(self):
        """Single name should be returned as-is."""
        assert normalize_author("Madonna") == "Madonna"
    
    def test_empty_author(self):
        """Empty author should return empty string."""
        assert normalize_author("") == ""
        assert normalize_author("   ") == ""


class TestNormalizeISBN13:
    """Tests for normalize_isbn13()."""
    
    def test_valid_isbn13(self):
        """Valid ISBN13 should be normalized (hyphens removed)."""
        assert normalize_isbn13("978-0-7432-7356-5") == "9780743273565"
        assert normalize_isbn13("978 0 7432 7356 5") == "9780743273565"
        assert normalize_isbn13("9780743273565") == "9780743273565"
    
    def test_invalid_isbn13(self):
        """Invalid ISBN13 should return None."""
        assert normalize_isbn13("123") is None  # Too short
        assert normalize_isbn13("978-0-7432-7356-5X") is None  # Contains letter
        assert normalize_isbn13("") is None
        assert normalize_isbn13(None) is None
    
    def test_isbn10_not_converted(self):
        """ISBN10 should return None (not converted)."""
        assert normalize_isbn13("0-7432-7356-5") is None


class TestNormalizeASIN:
    """Tests for normalize_asin()."""
    
    def test_valid_asin(self):
        """Valid ASIN should be uppercased."""
        assert normalize_asin("B001234567") == "B001234567"
        assert normalize_asin("b001234567") == "B001234567"
        assert normalize_asin("  B001234567  ") == "B001234567"
    
    def test_invalid_asin(self):
        """Invalid ASIN should return None."""
        assert normalize_asin("123") is None  # Too short
        assert normalize_asin("B00123456789") is None  # Too long
        assert normalize_asin("") is None
        assert normalize_asin(None) is None


class TestComputeCanonicalID:
    """Tests for compute_canonical_id()."""
    
    def test_priority_isbn13(self):
        """ISBN13 should be used if available."""
        row = {
            'isbn13': '9780743273565',
            'asin': 'B001234567',
            'title': 'Test Book',
            'author': 'Test Author'
        }
        result = compute_canonical_id(row)
        assert result.startswith('isbn13:')
        assert '9780743273565' in result
    
    def test_priority_asin_when_no_isbn13(self):
        """ASIN should be used if ISBN13 not available."""
        row = {
            'asin': 'B001234567',
            'title': 'Test Book',
            'author': 'Test Author'
        }
        result = compute_canonical_id(row)
        assert result.startswith('asin:')
        assert 'B001234567' in result
    
    def test_fallback_to_hash(self):
        """Hash should be used if no identifiers."""
        row = {
            'title': 'Test Book',
            'author': 'Test Author'
        }
        result = compute_canonical_id(row)
        assert result.startswith('hash:')
        assert len(result) > 5  # Should have hash value
    
    def test_hash_stability(self):
        """Hash should be stable for same title+author."""
        row1 = {
            'title': 'Test Book',
            'author': 'Test Author'
        }
        row2 = {
            'title': 'Test Book',
            'author': 'Test Author'
        }
        result1 = compute_canonical_id(row1)
        result2 = compute_canonical_id(row2)
        assert result1 == result2, "Hash should be stable for same input"

