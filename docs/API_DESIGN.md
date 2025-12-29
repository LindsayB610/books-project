# API Design Proposal: Future Frontend Support

## Overview

This document proposes a minimal, read-only API layer that sits on top of `books.csv` to support a future frontend. The API will enable browsing, filtering, searching, and natural-language recommendation queries without changing the core ingestion/merge pipeline.

## Design Principles

1. **Read-only**: API never writes to `books.csv` directly
2. **Stateless**: Each request reads fresh from `books.csv`
3. **Minimal dependencies**: Start with standard library, add only if needed
4. **Future-proof**: Structure allows evolution without breaking changes
5. **CSV-first**: No database required; `books.csv` remains source of truth

## Proposed API Structure

### Location in Repo

```
books-project/
├── api/                          # New directory
│   ├── __init__.py
│   ├── server.py                 # Simple HTTP server (Flask/FastAPI or stdlib)
│   ├── handlers.py               # Request handlers
│   ├── filters.py                # Filtering/search logic
│   └── recommendations.py        # Query-based recommendation logic
├── books.csv                     # Unchanged
├── scripts/                      # Unchanged
└── utils/                        # Unchanged
```

### Technology Choice

**Option A: Standard Library Only**
- Use `http.server` from stdlib
- Pros: Zero dependencies, simple
- Cons: More boilerplate, limited features

**Option B: Minimal Framework (Flask)**
- Single dependency: `flask`
- Pros: Clean routing, easy to extend
- Cons: Adds dependency

**Option C: FastAPI (Preferred for Implementation)**
- Single dependency: `fastapi` (+ `uvicorn` for server)
- Pros: Better typing support, automatic schema validation, OpenAPI docs
- Cons: Slightly larger dependency footprint

**Recommendation**: 
- For documentation/planning: Flask is fine as the "single dependency" example
- For actual implementation: Prefer FastAPI for better typing + schema validation
- Can start with Flask and migrate to FastAPI if needed

## Proposed API Endpoints

### 1. List Books (with filtering)

```
GET /api/books
```

**Query Parameters:**
- `limit` (int, default: 50, max: 500): Number of results
- `offset` (int, default: 0): Pagination offset
- `read_status` (string): Filter by `read`, `unread`, `reading`, `want_to_read`, `dnf`
- `genres` (string, comma-separated): Filter by genres/tags (e.g., `fantasy,fiction`)
- `tone` (string): Filter by tone (exact match)
- `vibe` (string): Filter by vibe (exact match)
- `anchor_type` (string): Filter by `all_time_favorite`, `recent_hit`, `recent_miss`, `dnf`
- `has_rating` (bool): Only books with ratings
- `sort` (string): `title`, `author`, `date_read`, `rating` (default: `author`)
- `order` (string): `asc`, `desc` (default: `asc`)

**Response:**
```json
{
  "books": [
    {
      "work_id": "isbn13:9781501139239",
      "title": "The Seven Husbands of Evelyn Hugo",
      "author": "Taylor Jenkins Reid",
      "isbn13": "9781501139239",
      "read_status": "read",
      "rating": "5",
      "genres": "favorites|historical-fiction|romance",
      "tone": "warm",
      "vibe": "glamorous Hollywood drama",
      "anchor_type": "all_time_favorite",
      "date_read": "2023-02-15"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### 2. Get Single Book

```
GET /api/books/{work_id}
```

**Response:**
```json
{
  "work_id": "isbn13:9781501139239",
  "title": "The Seven Husbands of Evelyn Hugo",
  "author": "Taylor Jenkins Reid",
  // ... all fields from books.csv
}
```

### 3. Search Books

```
GET /api/books/search?q={query}
```

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (int, default: 20): Number of results
- `fields` (string, comma-separated): Which fields to search (`title`, `author`, `notes`, default: `title,author`)

**Response:**
```json
{
  "query": "evelyn hugo",
  "results": [
    {
      "work_id": "isbn13:9781501139239",
      "title": "The Seven Husbands of Evelyn Hugo",
      "author": "Taylor Jenkins Reid",
      "match_field": "title",
      "match_score": 1.0
    }
  ],
  "total": 1
}
```

### 4. Query-Based Recommendations

```
POST /api/recommendations
```

**Request Body:**
```json
{
  "query": "urban fantasy series",
  "limit": 5,
  "filters": {
    "read_status": ["unread", "want_to_read"],
    "genres": ["fantasy"]
  }
}
```

**Response:**
```json
[
  {
    "work_id": "isbn13:9780451461032",
    "title": "Storm Front",
    "author": "Jim Butcher",
    "why": "Matches favorite tags: urban-fantasy|fantasy. Query keywords match: urban, fantasy",
    "confidence": 0.85
  },
  {
    "work_id": "isbn13:9780316127259",
    "title": "Dead Until Dark",
    "author": "Charlaine Harris",
    "why": "Matches favorite tags: urban-fantasy|mystery. Series starter book",
    "confidence": 0.78
  }
]
```

**Implementation Note**: This endpoint would:
1. Parse natural language query (extract keywords: "urban fantasy", "series")
2. Apply optional filters (read_status, genres, etc.)
3. Use existing `recommend.py` logic with query parameters
4. Return simple array of recommendations with work_id, title, author, why, and confidence

### 5. Get Filter Options (for UI dropdowns)

```
GET /api/filters/options
```

**Response:**
```json
{
  "read_statuses": ["read", "unread", "reading", "want_to_read", "dnf"],
  "anchor_types": ["all_time_favorite", "recent_hit", "recent_miss", "dnf"],
  "genres": ["fantasy", "fiction", "mystery", "science-fiction", ...],
  "tones": ["dark", "hopeful", "warm", "melancholic", ...],
  "vibes": ["cozy mystery", "epic fantasy", "literary fiction", ...]
}
```

### 6. Get Statistics

```
GET /api/stats
```

**Response:**
```json
{
  "total_books": 250,
  "read": 180,
  "unread": 50,
  "reading": 10,
  "want_to_read": 10,
  "with_ratings": 120,
  "anchor_books": 25,
  "by_genre": {
    "fantasy": 45,
    "fiction": 80,
    "mystery": 30
  }
}
```

## Implementation Approach

### Phase 1: Minimal Viable API (Current Proposal)

1. **Simple Flask server** (`api/server.py`)
   - Read `books.csv` on each request (or cache in memory with refresh)
   - Basic routing and error handling
   - JSON responses

2. **Filtering logic** (`api/filters.py`)
   - Parse query parameters
   - Filter books in-memory
   - Handle pagination

3. **Search logic** (`api/filters.py`)
   - Simple text matching (title, author)
   - Case-insensitive substring search
   - Return match scores

4. **Recommendations** (`api/recommendations.py`)
   - Reuse logic from `scripts/recommend.py`
   - Parse natural language queries (simple keyword extraction)
   - Return structured results

### Phase 2: Future Enhancements (Not Now)

- Caching layer (in-memory or Redis)
- Full-text search (if needed)
- Natural language parsing (NLP libraries)
- Vector embeddings for semantic search
- WebSocket for real-time updates

## Small Conventions to Adopt Now

### 1. Genre/Tag Normalization

**Current**: Genres use pipe-delimited format (`fantasy|fiction`)

**Recommendation**: Keep this consistent. When displaying in UI, split on `|` and display as tags/chips.

**Action**: Document in `DESIGN.md` that pipe (`|`) is the standard delimiter for multi-valued fields.

### 2. Empty vs Null Fields

**Current**: Some fields may be empty strings or None

**Recommendation**: Standardize on `None` for empty fields in API responses (convert empty strings to `null` in JSON).

**Action**: Add utility function to normalize field values for API responses.

### 3. Date Format Consistency

**Current**: Dates in `YYYY-MM-DD` format

**Recommendation**: Keep this. API can return ISO 8601 format (already compatible).

**Action**: No change needed, but document in API responses.

### 4. Work ID Stability

**Current**: `work_id` is stable identifier

**Recommendation**: Use `work_id` as primary key in API (not row index).

**Action**: Already done, but ensure API always uses `work_id` for lookups.

## Tradeoffs

### Pros of This Approach

1. **Simple**: Minimal code, easy to understand
2. **No database**: CSV remains source of truth
3. **Flexible**: Can evolve without breaking changes
4. **Testable**: Easy to test with sample CSV files
5. **Stateless**: No session management needed

### Cons / Limitations

1. **Performance**: Reading CSV on each request may be slow for large libraries (1000+ books)
   - **Mitigation**: Add in-memory caching with refresh mechanism
   - **Future**: Can add database later if needed

2. **Search limitations**: Simple substring search, not full-text
   - **Mitigation**: Sufficient for MVP
   - **Future**: Can add proper search library if needed

3. **Natural language parsing**: Simple keyword extraction, not true NLP
   - **Mitigation**: Good enough for structured queries
   - **Future**: Can add NLP/embeddings later

4. **No real-time updates**: API reads CSV, doesn't watch for changes
   - **Mitigation**: Acceptable for read-only API
   - **Future**: Can add file watching or polling

## File Structure Example

```
api/
├── __init__.py
├── server.py              # Flask app setup, route definitions
├── handlers.py             # Request handlers (parse params, call logic)
├── filters.py              # Filtering and search logic
├── recommendations.py       # Recommendation query logic
└── utils.py                # API-specific utilities (normalize responses, etc.)
```

## Dependencies

**Minimal (Phase 1):**
- `flask` (or stdlib `http.server`)

**Future (Phase 2, not now):**
- `flask-cors` (if frontend on different domain)
- Search library (if needed)
- NLP library (if needed)

## Next Steps (When Ready to Implement)

1. Create `api/` directory structure
2. Implement basic Flask server with health check endpoint
3. Implement `/api/books` endpoint with basic filtering
4. Add search endpoint
5. Integrate recommendation logic
6. Add error handling and validation
7. Write simple tests with fixture CSV

## Questions to Resolve Later

1. **Caching strategy**: In-memory cache with TTL? Refresh on file change?
2. **Authentication**: Will frontend need auth? (Not needed for MVP)
3. **CORS**: Will frontend be on different domain?
4. **Rate limiting**: Needed? (Probably not for personal use)
5. **API versioning**: How to handle breaking changes? (Use `/api/v1/` prefix)

## Summary

This proposal provides a minimal, read-only API layer that:
- Sits on top of `books.csv` without changing it
- Supports browsing, filtering, searching, and recommendations
- Uses minimal dependencies (Flask or stdlib)
- Can evolve without breaking changes
- Keeps the CSV as the single source of truth

The API is designed to be simple enough to implement quickly, but structured enough to grow as needs evolve.

