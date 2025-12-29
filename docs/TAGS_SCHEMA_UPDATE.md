# Tags Column Addition - Summary

## Schema Change

**Added `tags` column** immediately after `genres` in canonical schema.

**Updated Header:**
```
work_id,isbn13,asin,title,author,publication_year,publisher,language,pages,genres,tags,description,formats,...
```

**Field Definitions:**
- `genres` - External genres (reserved for future metadata enrichment), pipe-delimited
- `tags` - User shelves/labels (Goodreads Bookshelves + manual tags), pipe-delimited, lowercased, freeform

## Changes Made

### 1. Updated `books.csv` Header
- Added `tags` column after `genres`
- Total fields: 38 (was 37)

### 2. Updated `scripts/ingest_goodreads.py`
- **Bookshelves → tags**: Maps Goodreads Bookshelves to `tags` field (pipe-delimited, lowercased)
- **genres = None**: Sets `genres` to None (reserved for future enrichment)
- Updated `CANONICAL_FIELDS` to include `tags` in correct position
- Updated preview output to show both tags and genres

### 3. Updated `scripts/ingest_kindle.py`
- Added `tags = None` (Kindle doesn't have user shelves)
- `genres = None` (reserved for future enrichment)

### 4. Updated `scripts/merge_and_dedupe.py`
- Added `tags` to `CANONICAL_FIELDS` in correct position

### 5. Updated `scripts/recommend.py`
- **Prefer tags over genres**: Extracts tags first, then genres (for future enrichment)
- Updated both positive and negative anchor extraction
- Updated book scoring to check tags first, then genres
- Updated output messages to reference "tags" (with genres as fallback)

### 6. Updated `scripts/validate_books_csv.py`
- Added `tags` to pipe-delimited fields validation

### 7. Updated `DESIGN.md`
- Documented `genres` as external genres (reserved for future enrichment)
- Documented `tags` as user shelves/labels (Goodreads + manual), pipe-delimited, lowercased, freeform

## Data Safety

- **Backward compatible**: Existing `books.csv` files will have `tags` as None/empty
- **No data loss**: All existing fields preserved
- **Protected fields**: Still protected (tags is not a protected field, but follows same merge rules)

## Migration Notes

When running on existing `books.csv`:
- Existing rows will have `tags = None` (empty)
- New Goodreads ingestion will populate `tags` from Bookshelves
- Manual tags can be added later
- `genres` remains empty until external enrichment is implemented

## Updated File Paths

**Input:**
- `sources/goodreads_export.csv` → `ingest_goodreads.py` → `sources/goodreads_canonical.csv` (with tags)

**Output:**
- `books.csv` (now includes tags column)

## Example

**Goodreads Bookshelves:** `"favorites, historical-fiction, romance"`

**Mapped to canonical:**
- `tags`: `"favorites|historical-fiction|romance"`
- `genres`: `None`

