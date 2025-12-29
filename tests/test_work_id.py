"""
Tests for work_id generation.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.work_id import generate_work_id


class TestGenerateWorkID:
    """Tests for generate_work_id() - critical for stable identifiers."""
    
    def test_preserve_existing_work_id(self):
        """Existing work_id should always be preserved."""
        book = {
            'title': 'Test Book',
            'author': 'Test Author'
        }
        existing_id = 'isbn13:9780743273565'
        
        result = generate_work_id(book, existing_work_id=existing_id)
        
        assert result == existing_id, "Existing work_id should be preserved"
    
    def test_use_isbn13_when_available(self):
        """ISBN13 should be used to generate work_id."""
        book = {
            'isbn13': '978-0-7432-7356-5',
            'title': 'Test Book',
            'author': 'Test Author'
        }
        
        result = generate_work_id(book)
        
        assert result.startswith('isbn13:')
        assert '9780743273565' in result  # Hyphens removed
    
    def test_use_asin_when_no_isbn13(self):
        """ASIN should be used when ISBN13 not available."""
        book = {
            'asin': 'B001234567',
            'title': 'Test Book',
            'author': 'Test Author'
        }
        
        result = generate_work_id(book)
        
        assert result.startswith('asin:')
        assert 'B001234567' in result
    
    def test_fallback_to_hash(self):
        """Hash should be used when no identifiers."""
        book = {
            'title': 'Test Book',
            'author': 'Test Author'
        }
        
        result = generate_work_id(book)
        
        assert result.startswith('hash:')
        assert len(result) > 5  # Should have hash value
    
    def test_hash_stability(self):
        """Hash should be stable for same title+author."""
        book1 = {
            'title': 'Test Book',
            'author': 'Test Author'
        }
        book2 = {
            'title': 'Test Book',
            'author': 'Test Author'
        }
        
        result1 = generate_work_id(book1)
        result2 = generate_work_id(book2)
        
        assert result1 == result2, "Hash should be stable for same input"
    
    def test_priority_order(self):
        """Priority should be: existing > ISBN13 > ASIN > hash."""
        # Test ISBN13 takes priority over ASIN
        book = {
            'isbn13': '9780743273565',
            'asin': 'B001234567',
            'title': 'Test Book',
            'author': 'Test Author'
        }
        
        result = generate_work_id(book)
        
        assert result.startswith('isbn13:'), "ISBN13 should take priority over ASIN"
    
    def test_work_id_from_book_dict(self):
        """work_id from book dict should be used if present."""
        book = {
            'work_id': 'isbn13:9780743273565',
            'title': 'Test Book',
            'author': 'Test Author'
        }
        
        result = generate_work_id(book)
        
        assert result == 'isbn13:9780743273565', "work_id from book dict should be used"

