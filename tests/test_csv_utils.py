"""
Tests for CSV utilities, focusing on safe_merge() and protected fields.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.csv_utils import safe_merge, union_pipe, is_manually_set, PROTECTED_FIELDS


class TestSafeMerge:
    """Tests for safe_merge() - critical for data safety."""
    
    def test_protected_field_preserved_when_existing_has_value(self):
        """Protected fields should NEVER be overwritten if existing has value."""
        existing = {
            'work_id': 'isbn13:123',
            'title': 'Existing Book',
            'rating': '5',
            'notes': 'My favorite book',
            'anchor_type': 'all_time_favorite'
        }
        new = {
            'work_id': 'isbn13:123',
            'title': 'Existing Book',
            'rating': '3',  # Different value - should be ignored
            'notes': 'Different notes',  # Should be ignored
            'anchor_type': 'recent_hit'  # Should be ignored
        }
        
        merged = safe_merge(existing, new)
        
        assert merged['rating'] == '5', "Protected field 'rating' should be preserved"
        assert merged['notes'] == 'My favorite book', "Protected field 'notes' should be preserved"
        assert merged['anchor_type'] == 'all_time_favorite', "Protected field 'anchor_type' should be preserved"
    
    def test_protected_field_updated_when_existing_empty(self):
        """Protected fields can be filled if existing is empty."""
        existing = {
            'work_id': 'isbn13:123',
            'title': 'Book',
            'rating': '',  # Empty
            'notes': None,  # None
            'anchor_type': ''  # Empty
        }
        new = {
            'work_id': 'isbn13:123',
            'title': 'Book',
            'rating': '4',
            'notes': 'Great book',
            'anchor_type': 'recent_hit'
        }
        
        merged = safe_merge(existing, new)
        
        assert merged['rating'] == '4', "Protected field should be filled when existing is empty"
        assert merged['notes'] == 'Great book', "Protected field should be filled when existing is empty"
        assert merged['anchor_type'] == 'recent_hit', "Protected field should be filled when existing is empty"
    
    def test_work_id_always_preserved_from_existing(self):
        """work_id from existing should always be preserved."""
        existing = {
            'work_id': 'isbn13:123',
            'title': 'Book'
        }
        new = {
            'work_id': 'isbn13:456',  # Different work_id
            'title': 'Book'
        }
        
        merged = safe_merge(existing, new)
        
        assert merged['work_id'] == 'isbn13:123', "work_id should always be preserved from existing"
    
    def test_work_id_set_from_new_when_existing_empty(self):
        """work_id can be set from new if existing doesn't have it."""
        existing = {
            'title': 'Book'
        }
        new = {
            'work_id': 'isbn13:123',
            'title': 'Book'
        }
        
        merged = safe_merge(existing, new)
        
        assert merged['work_id'] == 'isbn13:123', "work_id should be set from new when existing is empty"
    
    def test_pipe_delimited_fields_union(self):
        """Pipe-delimited fields (formats, sources, tags) should be unioned."""
        existing = {
            'title': 'Book',
            'formats': 'kindle|physical',
            'sources': 'goodreads',
            'tags': 'fantasy|fiction'
        }
        new = {
            'title': 'Book',
            'formats': 'kindle|audiobook',  # Adds audiobook
            'sources': 'kindle',  # Adds kindle
            'tags': 'fantasy|mystery'  # Adds mystery, keeps fantasy
        }
        
        merged = safe_merge(existing, new)
        
        # Formats should be unioned and sorted
        assert 'kindle' in merged['formats']
        assert 'physical' in merged['formats']
        assert 'audiobook' in merged['formats']
        assert merged['formats'].count('|') == 2  # Three items, two pipes
        
        # Sources should be unioned
        assert 'goodreads' in merged['sources']
        assert 'kindle' in merged['sources']
        
        # Tags should be unioned
        assert 'fantasy' in merged['tags']
        assert 'fiction' in merged['tags']
        assert 'mystery' in merged['tags']
    
    def test_safe_fields_updated_when_existing_empty(self):
        """Safe fields (non-protected) can be updated if existing is empty."""
        existing = {
            'title': 'Book',
            'publication_year': '',
            'publisher': None
        }
        new = {
            'title': 'Book',
            'publication_year': '2020',
            'publisher': 'Test Publisher'
        }
        
        merged = safe_merge(existing, new)
        
        assert merged['publication_year'] == '2020', "Safe field should be updated when existing is empty"
        assert merged['publisher'] == 'Test Publisher', "Safe field should be updated when existing is empty"
    
    def test_safe_fields_preserved_when_both_exist(self):
        """Safe fields prefer existing value when both exist."""
        existing = {
            'title': 'Book',
            'publication_year': '2020',
            'publisher': 'Existing Publisher'
        }
        new = {
            'title': 'Book',
            'publication_year': '2021',
            'publisher': 'New Publisher'
        }
        
        merged = safe_merge(existing, new)
        
        assert merged['publication_year'] == '2020', "Safe field should prefer existing when both exist"
        assert merged['publisher'] == 'Existing Publisher', "Safe field should prefer existing when both exist"
    
    def test_all_protected_fields_listed(self):
        """Verify all expected protected fields are in PROTECTED_FIELDS set."""
        expected_protected = {
            'work_id', 'rating', 'reread', 'reread_count', 'dnf', 'dnf_reason',
            'pacing_rating', 'tone', 'vibe', 'what_i_wanted', 'did_it_deliver',
            'favorite_elements', 'pet_peeves', 'notes', 'anchor_type',
            'read_status', 'would_recommend'
        }
        
        assert expected_protected.issubset(PROTECTED_FIELDS), "All expected protected fields should be in PROTECTED_FIELDS"


class TestUnionPipe:
    """Tests for union_pipe() function."""
    
    def test_union_two_pipe_delimited_strings(self):
        """Union two pipe-delimited strings."""
        result = union_pipe('kindle|physical', 'kindle|audiobook')
        
        assert 'kindle' in result
        assert 'physical' in result
        assert 'audiobook' in result
        assert result.count('|') == 2  # Three items
    
    def test_union_sorted_output(self):
        """Union result should be sorted."""
        result = union_pipe('zebra|alpha', 'beta|zebra')
        
        # Should be sorted: alpha, beta, zebra
        parts = result.split('|')
        assert parts == sorted(parts), "Union result should be sorted"
    
    def test_union_with_none(self):
        """Union handles None values."""
        result = union_pipe(None, 'kindle|physical')
        assert result == 'kindle|physical'
        
        result = union_pipe('kindle|physical', None)
        assert result == 'kindle|physical'
        
        result = union_pipe(None, None)
        assert result is None
    
    def test_union_with_empty_strings(self):
        """Union handles empty strings."""
        result = union_pipe('', 'kindle|physical')
        assert result == 'kindle|physical'
        
        result = union_pipe('kindle|physical', '')
        assert result == 'kindle|physical'
        
        result = union_pipe('', '')
        assert result is None


class TestIsManuallySet:
    """Tests for is_manually_set() function."""
    
    def test_manually_set_with_value(self):
        """Value is manually set if it has content."""
        assert is_manually_set('5') is True
        assert is_manually_set('test') is True
        assert is_manually_set('  test  ') is True  # After strip
    
    def test_not_manually_set_when_empty(self):
        """Empty or None values are not manually set."""
        assert is_manually_set('') is False
        assert is_manually_set(None) is False
        assert is_manually_set('   ') is False  # Only whitespace

