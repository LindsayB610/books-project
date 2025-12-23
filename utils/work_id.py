"""
Work ID generation and management utilities.
Generates stable, persistent IDs for books.
"""

import hashlib
import uuid
from typing import Dict, Optional


def generate_work_id(book: Dict, existing_work_id: Optional[str] = None) -> str:
    """
    Generate or preserve a stable work_id for a book.
    
    If existing_work_id is provided, preserve it.
    Otherwise, generate a stable ID based on identifiers or title+author.
    
    Priority:
    1. Preserve existing work_id if present
    2. Use ISBN13 if available
    3. Use ASIN if available
    4. Hash of normalized title+author as fallback
    """
    # Preserve existing work_id if present
    if existing_work_id and existing_work_id.strip():
        return existing_work_id.strip()
    
    # Try to use existing work_id from book dict
    if book.get('work_id') and book.get('work_id').strip():
        return book.get('work_id').strip()
    
    # Generate stable ID based on identifiers
    isbn13 = book.get('isbn13', '').strip()
    if isbn13:
        # Normalize ISBN13 (remove hyphens)
        isbn_clean = isbn13.replace('-', '').replace(' ', '')
        if len(isbn_clean) == 13 and isbn_clean.isdigit():
            return f"isbn13:{isbn_clean}"
    
    asin = book.get('asin', '').strip()
    if asin:
        # ASINs are typically 10 characters
        asin_clean = asin.upper().strip()
        if len(asin_clean) == 10:
            return f"asin:{asin_clean}"
    
    # Fallback: hash of title+author
    title = book.get('title', '').strip()
    author = book.get('author', '').strip()
    
    if title and author:
        # Normalize for stability
        from .normalization import normalize_title, normalize_author
        norm_title = normalize_title(title)
        norm_author = normalize_author(author)
        combined = f"{norm_title}|{norm_author}"
        
        # Generate deterministic hash
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()[:16]  # Use first 16 chars for readability
        return f"hash:{hash_hex}"
    
    # Last resort: UUID (not stable, but better than nothing)
    return f"uuid:{uuid.uuid4().hex[:16]}"

