"""
Filtering and search logic for books API.
"""

from typing import List, Dict, Optional, Set
import re


def filter_books(
    books: List[Dict],
    read_status: Optional[str] = None,
    genres: Optional[str] = None,
    tone: Optional[str] = None,
    vibe: Optional[str] = None,
    anchor_type: Optional[str] = None,
    has_rating: Optional[bool] = None
) -> List[Dict]:
    """
    Filter books based on query parameters.
    
    Args:
        books: List of book dictionaries
        read_status: Filter by read_status (exact match)
        genres: Comma-separated list of genres/tags (any match)
        tone: Filter by tone (exact match, case-insensitive)
        vibe: Filter by vibe (exact match, case-insensitive)
        anchor_type: Filter by anchor_type (exact match)
        has_rating: If True, only books with ratings
    
    Returns:
        Filtered list of books
    """
    filtered = books
    
    # Filter by read_status
    if read_status:
        filtered = [b for b in filtered if (b.get('read_status') or '').strip().lower() == read_status.lower()]
    
    # Filter by genres/tags (any match)
    if genres:
        genre_list = [g.strip().lower() for g in genres.split(',') if g.strip()]
        if genre_list:
            filtered = [b for b in filtered if _matches_genres(b, genre_list)]
    
    # Filter by tone (exact match, case-insensitive)
    if tone:
        tone_lower = tone.lower()
        filtered = [b for b in filtered if (b.get('tone') or '').strip().lower() == tone_lower]
    
    # Filter by vibe (exact match, case-insensitive)
    if vibe:
        vibe_lower = vibe.lower()
        filtered = [b for b in filtered if (b.get('vibe') or '').strip().lower() == vibe_lower]
    
    # Filter by anchor_type
    if anchor_type:
        filtered = [b for b in filtered if (b.get('anchor_type') or '').strip() == anchor_type]
    
    # Filter by has_rating
    if has_rating is not None:
        if has_rating:
            filtered = [b for b in filtered if _has_rating(b)]
        else:
            filtered = [b for b in filtered if not _has_rating(b)]
    
    return filtered


def _matches_genres(book: Dict, genre_list: List[str]) -> bool:
    """Check if book matches any of the genres/tags in genre_list."""
    # Check tags (preferred)
    tags_str = (book.get('tags') or '').strip().lower()
    if tags_str:
        book_tags = {t.strip() for t in tags_str.split('|') if t.strip()}
        if any(genre in book_tags for genre in genre_list):
            return True
    
    # Check genres (fallback)
    genres_str = (book.get('genres') or '').strip().lower()
    if genres_str:
        book_genres = {g.strip() for g in genres_str.split('|') if g.strip()}
        if any(genre in book_genres for genre in genre_list):
            return True
    
    return False


def _has_rating(book: Dict) -> bool:
    """Check if book has a rating."""
    rating = book.get('rating', '').strip()
    if not rating:
        return False
    try:
        float(rating)
        return True
    except (ValueError, TypeError):
        return False


def sort_books(books: List[Dict], sort_by: str = "author", order: str = "asc") -> List[Dict]:
    """
    Sort books by specified field.
    
    Args:
        books: List of book dictionaries
        sort_by: Field to sort by (title, author, date_read, rating)
        order: Sort order (asc, desc)
    
    Returns:
        Sorted list of books
    """
    reverse = order.lower() == "desc"
    
    def sort_key(book: Dict):
        if sort_by == "title":
            return (book.get('title') or '').lower()
        elif sort_by == "author":
            return (book.get('author') or '').lower()
        elif sort_by == "date_read":
            date_str = (book.get('date_read') or '').strip()
            # Return empty string for sorting (will sort to end)
            return date_str if date_str else ''
        elif sort_by == "rating":
            rating_str = (book.get('rating') or '').strip()
            try:
                return float(rating_str) if rating_str else 0.0
            except (ValueError, TypeError):
                return 0.0
        else:
            return ''
    
    return sorted(books, key=sort_key, reverse=reverse)


def paginate_books(books: List[Dict], limit: int = 50, offset: int = 0) -> List[Dict]:
    """
    Paginate books list.
    
    Args:
        books: List of book dictionaries
        limit: Maximum number of results
        offset: Number of results to skip
    
    Returns:
        Paginated list of books
    """
    # Clamp limit to reasonable max
    limit = min(limit, 500)
    offset = max(offset, 0)
    
    return books[offset:offset + limit]


def search_books(
    books: List[Dict],
    query: str,
    fields: Optional[List[str]] = None,
    limit: int = 20
) -> List[Dict]:
    """
    Search books by query string.
    
    Args:
        books: List of book dictionaries
        query: Search query string
        fields: Fields to search (default: ['title', 'author'])
        limit: Maximum number of results
    
    Returns:
        List of matching books with match_field and match_score
    """
    if not query or not query.strip():
        return []
    
    if fields is None:
        fields = ['title', 'author']
    
    query_lower = query.strip().lower()
    results = []
    
    for book in books:
        match_field = None
        match_score = 0.0
        
        # Search in specified fields
        for field in fields:
            field_value = (book.get(field) or '').strip()
            if not field_value:
                continue
            
            field_lower = field_value.lower()
            
            # Exact match (highest score)
            if field_lower == query_lower:
                match_score = 1.0
                match_field = field
                break
            
            # Starts with query (high score)
            elif field_lower.startswith(query_lower):
                match_score = 0.8
                match_field = field
            
            # Contains query (medium score)
            elif query_lower in field_lower:
                if match_score < 0.6:
                    match_score = 0.6
                    match_field = field
        
        if match_field:
            # Add match metadata to book dict (temporary, for response)
            result = book.copy()
            result['match_field'] = match_field
            result['match_score'] = match_score
            results.append(result)
    
    # Sort by match score (highest first)
    results.sort(key=lambda x: x.get('match_score', 0.0), reverse=True)
    
    # Limit results
    return results[:limit]

