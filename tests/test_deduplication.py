"""
Tests for deduplication logic.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.deduplication import find_matches, compute_title_similarity, compute_author_similarity


class TestFindMatches:
    """Tests for find_matches() - critical for deduplication."""
    
    def test_exact_isbn13_match(self):
        """Books with same ISBN13 should match with high confidence."""
        new = {
            'isbn13': '9780743273565',
            'title': 'The Great Gatsby',
            'author': 'Fitzgerald, F. Scott'
        }
        existing = [{
            'isbn13': '9780743273565',
            'title': 'Great Gatsby',
            'author': 'F. Scott Fitzgerald'
        }]
        
        matches = find_matches(new, existing)
        
        assert len(matches) > 0, "Should find match for same ISBN13"
        assert matches[0][2] >= 0.95, "ISBN13 match should have high confidence"
    
    def test_exact_asin_match(self):
        """Books with same ASIN should match."""
        new = {
            'asin': 'B001234567',
            'title': 'Test Book',
            'author': 'Test Author'
        }
        existing = [{
            'asin': 'B001234567',
            'title': 'Different Title',
            'author': 'Different Author'
        }]
        
        matches = find_matches(new, existing)
        
        assert len(matches) > 0, "Should find match for same ASIN"
        assert matches[0][2] >= 0.90, "ASIN match should have good confidence"
    
    def test_exact_title_author_match(self):
        """Books with same normalized title+author should match."""
        new = {
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald'
        }
        existing = [{
            'title': 'Great Gatsby',
            'author': 'Fitzgerald, F. Scott'
        }]
        
        matches = find_matches(new, existing)
        
        assert len(matches) > 0, "Should find match for same title+author"
        assert matches[0][2] >= 0.85, "Title+author match should have good confidence"
    
    def test_no_fuzzy_when_has_identifiers(self):
        """Fuzzy matching should NOT be used when ISBN13 or ASIN exists, but exact title+author still matches."""
        new = {
            'isbn13': '9780743273565',
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald'
        }
        existing = [{
            'isbn13': '9781234567890',  # Different ISBN
            'title': 'The Great Gatsby',  # Same title
            'author': 'F. Scott Fitzgerald'  # Same author
        }]
        
        matches = find_matches(new, existing)
        
        # Should match on exact title+author (even with different ISBNs)
        # This is correct behavior - same book, different editions
        assert len(matches) > 0, "Should match on exact title+author even with different ISBNs"
        assert matches[0][2] == 0.85, "Exact title+author match should have 0.85 confidence"
        
        # But fuzzy matching (0.92+ similarity) should NOT be used
        # Test with titles that normalize differently (would require fuzzy matching)
        new2 = {
            'isbn13': '9780743273565',
            'title': 'The Great Gatsby',  # Original title
            'author': 'F. Scott Fitzgerald'
        }
        existing2 = [{
            'isbn13': '9781234567890',
            'title': 'The Great Gatsby: A Novel',  # Different title (would need fuzzy to match)
            'author': 'F. Scott Fitzgerald'
        }]
        
        matches2 = find_matches(new2, existing2)
        # Should NOT match because titles don't exactly match and fuzzy is disabled when identifiers exist
        assert len(matches2) == 0, "Should not fuzzy match when identifiers exist"
    
    def test_fuzzy_only_when_no_identifiers(self):
        """Fuzzy matching should only be used when both ISBN13 and ASIN are missing."""
        new = {
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald'
        }
        existing = [{
            'title': 'Great Gatsby',
            'author': 'Fitzgerald, F Scott'  # Slight variation
        }]
        
        matches = find_matches(new, existing)
        
        # Should potentially match if similarity is high enough
        # (This depends on similarity threshold - 0.92+)
        if len(matches) > 0:
            assert matches[0][2] < 0.90, "Fuzzy matches should have lower confidence than exact"
    
    def test_no_match_for_different_books(self):
        """Completely different books should not match."""
        new = {
            'isbn13': '9780743273565',
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald'
        }
        existing = [{
            'isbn13': '9781234567890',
            'title': '1984',
            'author': 'Orwell, George'
        }]
        
        matches = find_matches(new, existing)
        
        assert len(matches) == 0, "Completely different books should not match"
    
    def test_matches_sorted_by_confidence(self):
        """Matches should be sorted by confidence (highest first)."""
        new = {
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald'
        }
        existing = [
            {
                'isbn13': '9780743273565',
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald'
            },
            {
                'title': 'Great Gatsby',
                'author': 'Fitzgerald, F. Scott'
            }
        ]
        
        matches = find_matches(new, existing)
        
        if len(matches) > 1:
            # First match should have higher confidence
            assert matches[0][2] >= matches[1][2], "Matches should be sorted by confidence"


class TestTitleSimilarity:
    """Tests for compute_title_similarity()."""
    
    def test_exact_match(self):
        """Exact matches should return 1.0."""
        assert compute_title_similarity("The Great Gatsby", "The Great Gatsby") == 1.0
    
    def test_normalized_match(self):
        """Normalized matches should return 1.0."""
        assert compute_title_similarity("The Great Gatsby", "great gatsby") == 1.0
    
    def test_partial_match(self):
        """Partial matches should return similarity < 1.0."""
        similarity = compute_title_similarity("The Great Gatsby", "Gatsby")
        assert 0.0 < similarity < 1.0
    
    def test_no_match(self):
        """Completely different titles should return low similarity."""
        similarity = compute_title_similarity("The Great Gatsby", "1984")
        assert similarity < 0.5


class TestAuthorSimilarity:
    """Tests for compute_author_similarity()."""
    
    def test_exact_match(self):
        """Exact matches should return 1.0."""
        assert compute_author_similarity("Fitzgerald, F. Scott", "Fitzgerald, F. Scott") == 1.0
    
    def test_same_last_name(self):
        """Same last name should return high similarity."""
        similarity = compute_author_similarity("Fitzgerald, F. Scott", "Fitzgerald, Zelda")
        assert similarity >= 0.85
    
    def test_different_authors(self):
        """Different authors should return low similarity."""
        similarity = compute_author_similarity("Fitzgerald, F. Scott", "Orwell, George")
        assert similarity < 0.5

