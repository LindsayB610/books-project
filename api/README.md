# Books API

Read-only REST API for the Books CSV Builder + Recommender project.

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Server

```bash
# Default dataset (datasets/default)
python -m api.server

# Or with uvicorn directly
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Endpoints

### `GET /`
Root endpoint with API information.

### `GET /api/books`
List books with filtering, sorting, and pagination.

**Query Parameters:**
- `limit` (int, default: 50, max: 500): Number of results
- `offset` (int, default: 0): Pagination offset
- `read_status` (string): Filter by read status
- `genres` (string, comma-separated): Filter by genres/tags
- `tone` (string): Filter by tone
- `vibe` (string): Filter by vibe
- `anchor_type` (string): Filter by anchor type
- `has_rating` (bool): Only books with ratings
- `sort` (string): Sort field (title, author, date_read, rating)
- `order` (string): Sort order (asc, desc)

**Example:**
```bash
curl "http://localhost:8000/api/books?limit=10&read_status=read&sort=rating&order=desc"
```

### `GET /api/books/{work_id}`
Get a single book by work_id.

**Example:**
```bash
curl "http://localhost:8000/api/books/isbn13:9781501139239"
```

### `GET /api/books/search`
Search books by query string.

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (int, default: 20): Number of results
- `fields` (string, comma-separated): Fields to search (title, author, notes)

**Example:**
```bash
curl "http://localhost:8000/api/books/search?q=evelyn+hugo"
```

### `POST /api/recommendations`
Get book recommendations based on natural language query.

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

**Example:**
```bash
curl -X POST "http://localhost:8000/api/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"query": "urban fantasy", "limit": 5}'
```

### `GET /api/filters/options`
Get available filter options for UI dropdowns.

**Example:**
```bash
curl "http://localhost:8000/api/filters/options"
```

### `GET /api/stats`
Get library statistics.

**Example:**
```bash
curl "http://localhost:8000/api/stats"
```

## Configuration

The API currently uses the default dataset (`datasets/default`). To change this, modify `DEFAULT_DATASET` in `api/server.py` or make it configurable via environment variable.

## Notes

- The API is **read-only** - it never modifies `books.csv`
- Data is read fresh on each request (stateless design)
- Empty strings are converted to `null` in JSON responses
- All endpoints return JSON

## Future Enhancements

- Configurable dataset via environment variable or config file
- File watching for automatic cache refresh
- CORS support for frontend
- Authentication (if needed for multi-user)

