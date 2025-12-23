"""
Deduplication logic for matching books across sources.
"""

from typing import List, Dict, Optional, Tuple
from .normalization import (
    normalize_title, normalize_author, 
    normalize_isbn13, normalize_asin, compute_canonical_id
)


def find_matches(new_row: Dict, existing_rows: List[Dict]) -> List[Tuple[int, Dict, float]]:
    """
    Find potential matches for a new row in existing rows.
    Returns list of (index, matched_row, confidence_score) tuples.
    Confidence: 1.0 = exact match, 0.5 = fuzzy match, 0.0 = no match
    
    Fuzzy matching is ONLY applied when ISBN13 and ASIN are both missing.
    False merges are worse than duplicates.
    """
    matches = []
    
    new_canonical_id = compute_canonical_id(new_row)
    new_title = normalize_title(new_row.get('title', ''))
    new_author = normalize_author(new_row.get('author', ''))
    new_isbn13 = normalize_isbn13(new_row.get('isbn13', ''))
    new_asin = normalize_asin(new_row.get('asin', ''))
    
    # Check if we have identifiers - if so, don't use fuzzy matching
    has_identifiers = bool(new_isbn13 or new_asin)
    
    for idx, existing in enumerate(existing_rows):
        existing_canonical_id = compute_canonical_id(existing)
        existing_title = normalize_title(existing.get('title', ''))
        existing_author = normalize_author(existing.get('author', ''))
        existing_isbn13 = normalize_isbn13(existing.get('isbn13', ''))
        existing_asin = normalize_asin(existing.get('asin', ''))
        
        confidence = 0.0
        
        # Exact canonical ID match (highest confidence)
        if new_canonical_id and new_canonical_id == existing_canonical_id:
            confidence = 1.0
            matches.append((idx, existing, confidence))
            continue
        
        # ISBN13 match
        if new_isbn13 and existing_isbn13 and new_isbn13 == existing_isbn13:
            confidence = 0.95
            matches.append((idx, existing, confidence))
            continue
        
        # ASIN match
        if new_asin and existing_asin and new_asin == existing_asin:
            confidence = 0.90
            matches.append((idx, existing, confidence))
            continue
        
        # Title + Author match (exact only if we have identifiers)
        if new_title and new_author and existing_title and existing_author:
            title_match = new_title == existing_title
            author_match = new_author == existing_author
            
            if title_match and author_match:
                confidence = 0.85
                matches.append((idx, existing, confidence))
                continue
            
            # Partial match (title exact, author similar) - only if we have identifiers
            if has_identifiers and title_match:
                # Check if authors are similar (same last name)
                new_last = new_author.split(',')[0].strip() if ',' in new_author else ''
                existing_last = existing_author.split(',')[0].strip() if ',' in existing_author else ''
                if new_last and existing_last and new_last == existing_last:
                    confidence = 0.70
                    matches.append((idx, existing, confidence))
                    continue
        
        # Bounded fuzzy matching (ONLY when ISBN13 and ASIN are both missing)
        # Use aggressive normalization and high threshold (0.92+)
        if not has_identifiers and new_title and new_author and existing_title and existing_author:
            title_similarity = compute_title_similarity(new_title, existing_title)
            author_similarity = compute_author_similarity(new_author, existing_author)
            
            # Require very high similarity on both (0.92+ threshold for safety)
            if title_similarity >= 0.92 and author_similarity >= 0.92:
                # Weighted average
                combined_confidence = (title_similarity * 0.6 + author_similarity * 0.4)
                if combined_confidence >= 0.92:
                    confidence = min(0.85, combined_confidence)  # Cap at 0.85 for fuzzy matches
                    matches.append((idx, existing, confidence))
                    continue
    
    # Sort by confidence (highest first)
    matches.sort(key=lambda x: x[2], reverse=True)
    return matches


def compute_title_similarity(title1: str, title2: str) -> float:
    """
    Compute similarity between two normalized titles (0.0 to 1.0).
    Uses Jaccard similarity (word overlap) with word order consideration.
    """
    norm_title1 = normalize_title(title1)
    norm_title2 = normalize_title(title2)
    
    if not norm_title1 or not norm_title2:
        return 0.0
    
    if norm_title1 == norm_title2:
        return 1.0
    
    words1 = set(norm_title1.split())
    words2 = set(norm_title2.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Jaccard similarity (intersection over union)
    intersection = words1 & words2
    union = words1 | words2
    
    if not union:
        return 0.0
    
    jaccard = len(intersection) / len(union)
    
    # Boost if significant word overlap (most words match)
    if len(intersection) >= min(len(words1), len(words2)) * 0.8:
        jaccard = min(1.0, jaccard * 1.1)
    
    return jaccard


def compute_author_similarity(author1: str, author2: str) -> float:
    """
    Compute similarity between two normalized authors (0.0 to 1.0).
    Prioritizes last name match, then first name.
    """
    norm_author1 = normalize_author(author1)
    norm_author2 = normalize_author(author2)
    
    if not norm_author1 or not norm_author2:
        return 0.0
    
    if norm_author1 == norm_author2:
        return 1.0
    
    # Extract last and first names
    def parse_author(auth):
        if ',' in auth:
            parts = [p.strip() for p in auth.split(',', 1)]
            return (parts[0] if len(parts) > 0 else '', parts[1] if len(parts) > 1 else '')
        else:
            parts = auth.split()
            if len(parts) >= 2:
                return (parts[-1], ' '.join(parts[:-1]))
            return (parts[0] if parts else '', '')
    
    last1, first1 = parse_author(norm_author1)
    last2, first2 = parse_author(norm_author2)
    
    # Last name match is critical
    if last1 and last2:
        if last1 == last2:
            # Same last name - check first name
            if first1 and first2:
                if first1 == first2:
                    return 1.0
                # Check if first names are similar (same initial or substring)
                if first1[0] == first2[0] or first1 in first2 or first2 in first1:
                    return 0.95
                return 0.85  # Same last, different first
            return 0.90  # Same last, no first name to compare
    
    return 0.0


def fuzzy_title_match(title1: str, title2: str, threshold: float = 0.8) -> bool:
    """
    Simple fuzzy title matching using word overlap.
    Returns True if similarity >= threshold.
    """
    similarity = compute_title_similarity(title1, title2)
    return similarity >= threshold

