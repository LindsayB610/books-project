"""
API wrapper for recommendation logic.
Reuses scripts/recommend.py functions.
"""

from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.recommend import (
    load_anchor_books,
    extract_preferences,
    find_candidate_books,
    score_book,
    generate_recommendations
)


def get_recommendations(
    books: List[Dict],
    query: Optional[str] = None,
    limit: int = 5,
    filters: Optional[Dict] = None
) -> List[Dict]:
    """
    Generate recommendations for API endpoint.
    
    Args:
        books: List of all books
        query: Natural language query (e.g., "urban fantasy series")
        limit: Maximum number of recommendations
        filters: Optional filters dict with read_status, genres, etc.
    
    Returns:
        List of recommendation dicts with work_id, title, author, why, confidence
    """
    # Apply filters if provided
    filtered_books = books
    if filters:
        filtered_books = _apply_filters(books, filters)
    
    # Generate recommendations using existing logic
    recommendations = generate_recommendations(filtered_books, num_recommendations=limit, query=query)
    
    # Format for API response
    results = []
    for book, score, reasons in recommendations:
        # Combine reasons into "why" string
        why = ". ".join(reasons) if reasons else "Recommended based on anchor books"
        
        results.append({
            'work_id': book.get('work_id'),
            'title': book.get('title'),
            'author': book.get('author'),
            'why': why,
            'confidence': round(score, 2)
        })
    
    return results


def _apply_filters(books: List[Dict], filters: Dict) -> List[Dict]:
    """Apply filters dict to books list."""
    # Import here to avoid circular dependency
    from api.filters import filter_books
    
    read_status = filters.get('read_status')
    genres = filters.get('genres')
    
    # Convert read_status list to single value (use first if list)
    if isinstance(read_status, list):
        read_status = read_status[0] if read_status else None
    
    # Convert genres list to comma-separated string
    if isinstance(genres, list):
        genres = ','.join(genres) if genres else None
    
    return filter_books(
        books,
        read_status=read_status,
        genres=genres
    )

