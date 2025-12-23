"""
Normalization utilities for titles, authors, and identifiers.
"""

import re
from typing import Optional


def normalize_title(title: str) -> str:
    """
    Normalize a book title for matching.
    - Lowercase
    - Remove punctuation
    - Normalize whitespace
    - Remove common prefixes (the, a, an)
    """
    if not title:
        return ""
    
    # Lowercase
    normalized = title.lower().strip()
    
    # Remove punctuation (keep alphanumeric and spaces)
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Remove common prefixes
    prefixes = ['the ', 'a ', 'an ']
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
    
    return normalized


def normalize_author(author: str) -> str:
    """
    Normalize author name to "Last, First" format.
    Handles various input formats.
    """
    if not author:
        return ""
    
    # Remove extra whitespace
    author = ' '.join(author.split())
    
    # If already in "Last, First" format, normalize case
    if ',' in author:
        parts = [p.strip() for p in author.split(',', 1)]
        if len(parts) == 2:
            return f"{parts[0].title()}, {parts[1].title()}"
        return parts[0].title()
    
    # Try "First Last" format
    parts = author.split()
    if len(parts) >= 2:
        # Assume last word(s) is last name
        last_name = parts[-1]
        first_name = ' '.join(parts[:-1])
        return f"{last_name.title()}, {first_name.title()}"
    
    # Single name - return as is
    return author.title()


def normalize_isbn13(isbn: str) -> Optional[str]:
    """
    Normalize ISBN-13: remove hyphens/spaces, validate format.
    Returns None if invalid.
    """
    if not isbn:
        return None
    
    # Remove hyphens and spaces
    cleaned = re.sub(r'[-\s]', '', str(isbn))
    
    # Should be 13 digits
    if len(cleaned) == 13 and cleaned.isdigit():
        return cleaned
    
    # Try converting ISBN-10 to ISBN-13 (basic check)
    if len(cleaned) == 10 and cleaned.isdigit():
        # This is a simplified check - full conversion is more complex
        # For now, return None and let it be handled elsewhere
        return None
    
    return None


def normalize_asin(asin: str) -> Optional[str]:
    """
    Normalize ASIN: uppercase, strip whitespace.
    ASINs are 10 characters (alphanumeric).
    """
    if not asin:
        return None
    
    cleaned = str(asin).strip().upper()
    
    # ASINs are typically 10 characters
    if len(cleaned) == 10:
        return cleaned
    
    return None


def compute_canonical_id(row: dict) -> str:
    """
    Compute a stable canonical ID for a book.
    Priority: isbn13 > asin > hash(title+author)
    """
    # Try ISBN13 first
    isbn13 = normalize_isbn13(row.get('isbn13', ''))
    if isbn13:
        return f"isbn13:{isbn13}"
    
    # Try ASIN
    asin = normalize_asin(row.get('asin', ''))
    if asin:
        return f"asin:{asin}"
    
    # Fallback: hash of normalized title + author
    title = normalize_title(row.get('title', ''))
    author = normalize_author(row.get('author', ''))
    combined = f"{title}|{author}"
    
    # Simple hash (for stability, we'll use a deterministic approach)
    import hashlib
    hash_obj = hashlib.md5(combined.encode('utf-8'))
    return f"hash:{hash_obj.hexdigest()[:12]}"

