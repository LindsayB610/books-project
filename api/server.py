"""
FastAPI server for Books CSV Builder + Recommender.
Provides read-only REST API endpoints.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from pydantic import BaseModel
import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.cache import BooksCache
from api.filters import filter_books, sort_books, paginate_books, search_books
from api.recommendations import get_recommendations

# Initialize FastAPI app
app = FastAPI(
    title="Books CSV Builder + Recommender API",
    description="Read-only API for browsing, filtering, searching, and getting book recommendations",
    version="1.0.0"
)

# Configure CORS
# Allow requests from the same domain and localhost for development
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "https://bookshelf.lindsaybrunner.com,http://localhost:3000,http://localhost:5173,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize cache (default dataset)
# Can be configured via BOOKS_DATASET environment variable
# Defaults to "datasets/default" if not set
import os
DEFAULT_DATASET = os.getenv("BOOKS_DATASET", "datasets/default")
cache = BooksCache(DEFAULT_DATASET)


# Request/Response models
class RecommendationRequest(BaseModel):
    query: Optional[str] = None
    limit: int = 5
    filters: Optional[Dict] = None


# Helper function to normalize empty strings to None for JSON
def normalize_for_json(book: Dict) -> Dict:
    """Convert empty strings to None for cleaner JSON responses."""
    normalized = {}
    for key, value in book.items():
        if value == '' or value is None:
            normalized[key] = None
        else:
            normalized[key] = value
    return normalized


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Books CSV Builder + Recommender API",
        "version": "1.0.0",
        "endpoints": {
            "books": "/api/books",
            "book_detail": "/api/books/{work_id}",
            "search": "/api/books/search",
            "recommendations": "/api/recommendations",
            "filters": "/api/filters/options",
            "stats": "/api/stats"
        }
    }


@app.get("/api/books")
async def list_books(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    read_status: Optional[str] = None,
    genres: Optional[str] = None,
    tone: Optional[str] = None,
    vibe: Optional[str] = None,
    anchor_type: Optional[str] = None,
    has_rating: Optional[bool] = None,
    sort: str = Query("author", regex="^(title|author|date_read|rating)$"),
    order: str = Query("asc", regex="^(asc|desc)$")
):
    """
    List books with filtering, sorting, and pagination.
    """
    books = cache.get_books()
    
    # Apply filters
    filtered = filter_books(
        books,
        read_status=read_status,
        genres=genres,
        tone=tone,
        vibe=vibe,
        anchor_type=anchor_type,
        has_rating=has_rating
    )
    
    # Sort
    sorted_books = sort_books(filtered, sort_by=sort, order=order)
    
    # Paginate
    paginated = paginate_books(sorted_books, limit=limit, offset=offset)
    
    # Normalize for JSON
    normalized = [normalize_for_json(book) for book in paginated]
    
    return {
        "books": normalized,
        "total": len(sorted_books),
        "limit": limit,
        "offset": offset
    }


@app.get("/api/books/{work_id}")
async def get_book(work_id: str):
    """
    Get a single book by work_id.
    """
    books = cache.get_books()
    
    # Find book by work_id
    book = next((b for b in books if b.get('work_id') == work_id), None)
    
    if not book:
        raise HTTPException(status_code=404, detail=f"Book with work_id '{work_id}' not found")
    
    return normalize_for_json(book)


@app.get("/api/books/search")
async def search_books_endpoint(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    fields: Optional[str] = Query(None, description="Comma-separated fields to search (title,author,notes)")
):
    """
    Search books by query string.
    """
    if not q or not q.strip():
        return {
            "query": q,
            "results": [],
            "total": 0
        }
    
    books = cache.get_books()
    
    # Parse fields
    search_fields = None
    if fields:
        search_fields = [f.strip() for f in fields.split(',') if f.strip()]
    
    # Search
    results = search_books(books, q, fields=search_fields, limit=limit)
    
    # Remove temporary match metadata for response (or keep it, it's useful)
    # Actually, let's keep match_field and match_score as they're useful
    
    normalized = [normalize_for_json(book) for book in results]
    
    return {
        "query": q,
        "results": normalized,
        "total": len(results)
    }


@app.post("/api/recommendations")
async def recommendations(request: RecommendationRequest):
    """
    Get book recommendations based on natural language query and anchor books.
    """
    books = cache.get_books()
    
    recommendations = get_recommendations(
        books,
        query=request.query,
        limit=request.limit,
        filters=request.filters
    )
    
    return recommendations


@app.get("/api/filters/options")
async def get_filter_options():
    """
    Get available filter options for UI dropdowns.
    """
    books = cache.get_books()
    
    # Extract unique values
    read_statuses = set()
    anchor_types = set()
    genres = set()
    tones = set()
    vibes = set()
    
    for book in books:
        # Read statuses
        rs = (book.get('read_status') or '').strip()
        if rs:
            read_statuses.add(rs)
        
        # Anchor types
        at = (book.get('anchor_type') or '').strip()
        if at:
            anchor_types.add(at)
        
        # Genres/tags (pipe-delimited)
        tags_str = (book.get('tags') or '').strip()
        if tags_str:
            for tag in tags_str.split('|'):
                tag_clean = tag.strip()
                if tag_clean:
                    genres.add(tag_clean.lower())
        
        genres_str = (book.get('genres') or '').strip()
        if genres_str:
            for genre in genres_str.split('|'):
                genre_clean = genre.strip()
                if genre_clean:
                    genres.add(genre_clean.lower())
        
        # Tones
        tone = (book.get('tone') or '').strip()
        if tone:
            tones.add(tone)
        
        # Vibes
        vibe = (book.get('vibe') or '').strip()
        if vibe:
            vibes.add(vibe)
    
    return {
        "read_statuses": sorted(list(read_statuses)),
        "anchor_types": sorted(list(anchor_types)),
        "genres": sorted(list(genres)),
        "tones": sorted(list(tones)),
        "vibes": sorted(list(vibes))
    }


@app.get("/api/stats")
async def get_stats():
    """
    Get library statistics.
    """
    books = cache.get_books()
    
    total_books = len(books)
    
    # Count by read_status
    read_status_counts = {}
    for book in books:
        rs = (book.get('read_status') or '').strip() or 'unknown'
        read_status_counts[rs] = read_status_counts.get(rs, 0) + 1
    
    # Count with ratings
    with_ratings = sum(1 for b in books if (b.get('rating') or '').strip())
    
    # Count anchor books
    anchor_books = sum(1 for b in books if (b.get('anchor_type') or '').strip())
    
    # Count by genre (top genres)
    genre_counts = {}
    for book in books:
        tags_str = (book.get('tags') or '').strip()
        if tags_str:
            for tag in tags_str.split('|'):
                tag_clean = tag.strip().lower()
                if tag_clean:
                    genre_counts[tag_clean] = genre_counts.get(tag_clean, 0) + 1
        
        genres_str = (book.get('genres') or '').strip()
        if genres_str:
            for genre in genres_str.split('|'):
                genre_clean = genre.strip().lower()
                if genre_clean:
                    genre_counts[genre_clean] = genre_counts.get(genre_clean, 0) + 1
    
    # Get top 10 genres
    top_genres = dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    return {
        "total_books": total_books,
        "read": read_status_counts.get('read', 0),
        "unread": read_status_counts.get('unread', 0),
        "reading": read_status_counts.get('reading', 0),
        "want_to_read": read_status_counts.get('want_to_read', 0),
        "dnf": read_status_counts.get('dnf', 0),
        "with_ratings": with_ratings,
        "anchor_books": anchor_books,
        "by_genre": top_genres
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

