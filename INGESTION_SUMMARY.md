# Goodreads Ingestion & Recommender Pivot - Summary

## Changes Made

### 1. Updated Goodreads Ingestion (`scripts/ingest_goodreads.py`)

**Key Changes:**
- **read_status**: Only from `Exclusive Shelf` (read → read, currently-reading → reading, to-read → want_to_read)
- **genres**: Bookshelves converted to pipe-delimited, lowercased tags
- **reread_count**: From Read Count (int, default 0)
- **reread**: 1 if reread_count > 1 else 0
- **physical_owned**: 1 if Owned Copies > 0 else 0 (None if parse fails)
- **isbn13**: Normalize using `normalize_isbn13()`; set to None if normalization fails (no dirty values)
- **date_read**: No longer populated from Goodreads (left as None)
- **date_added**: Improved parsing (accepts %Y/%m/%d, %Y-%m-%d, %Y/%m, %Y-%m)
- **notes**: Combines My Review + Private Notes with labels

### 2. Updated DESIGN.md

- Documented that `genres` is used as "tags/genres" and is pipe-delimited, lowercased
- Documented that `date_read` is optional/deprecated and not populated by default
- Updated references to use `work_id` as the stable internal identifier (replaced `canonical_id`)

### 3. Updated Validation Script (`scripts/validate_books_csv.py`)

**Added:**
- Delimiter sanity check: validates that pipe-delimited fields (genres, formats, sources) don't contain accidental commas
- Reports mixed delimiters (both commas and pipes)

**Existing checks:**
- Duplicate work_id
- Duplicate isbn13/asin
- Missing required fields (title, author)
- Invalid enums (read_status, anchor_type)
- Invalid numeric fields (rating, reread_count, dnf)

### 4. Updated Recommender (`scripts/recommend.py`)

**Pivoted to query-based recommendations:**
- **CLI**: `--query "urban fantasy series"` and `--limit 5` (default 5)
- **Candidate set**: Excludes `read_status` in {read, dnf}
- **Scoring**:
  - Positive anchors: `anchor_type` in {all_time_favorite, recent_hit}
  - Negative anchors: `anchor_type` in {recent_miss, dnf}
  - Score by:
    - Overlap with positive anchor tags/genres/tones/vibes
    - Minus overlap with negative anchor tags/genres/tones/vibes/pet_peeves
    - Query keywords boost matching tags/genres
- **Output**: 3-5 suggestions with short "why this fits" reasons
- **No description matching**: Removed (description is mostly empty)

## File Paths

**Input:**
- `sources/goodreads_export.csv` - Your Goodreads export

**Intermediate:**
- `sources/goodreads_canonical.csv` - Output from `ingest_goodreads.py`

**Output:**
- `books.csv` - Canonical books database (produced/updated by `merge_and_dedupe.py`)

## End-to-End Commands

```bash
# 1. Place your Goodreads export in sources/
# (Export from Goodreads: My Books → Import and export → Export library)
# Save as: sources/goodreads_export.csv

# 2. Ingest Goodreads data
python scripts/ingest_goodreads.py

# 3. Merge into canonical books.csv
python scripts/merge_and_dedupe.py

# 4. Validate the result
python scripts/validate_books_csv.py

# 5. (Optional) Get recommendations
python scripts/recommend.py --query "urban fantasy series" --limit 5
```

## Example Preview (3 Mapped Rows)

The `ingest_goodreads.py` script will automatically show a preview of the first 3 mapped rows. Example output:

```
Row 1:
  Title: The Seven Husbands of Evelyn Hugo
  Author: Taylor Jenkins Reid
  ISBN13: 9781501139239
  Read Status: read
  Rating: 5
  Reread Count: 2
  Physical Owned: 1
  Genres/Tags: favorites|historical-fiction|romance
  Goodreads ID: 32620332

Row 2:
  Title: Project Hail Mary
  Author: Andy Weir
  ISBN13: 9780593135204
  Read Status: reading
  Rating: N/A
  Reread Count: 0
  Physical Owned: 0
  Genres/Tags: science-fiction|to-read
  Goodreads ID: 54493401

Row 3:
  Title: The Midnight Library
  Author: Matt Haig
  ISBN13: 9780525559474
  Read Status: want_to_read
  Rating: N/A
  Reread Count: 0
  Physical Owned: 1
  Genres/Tags: fiction|philosophy
  Goodreads ID: 52578297
```

## Data Safety

- **Protected fields**: Never overwritten (rating, notes, anchor_type, etc.)
- **Work ID**: Stable identifier, preserved across runs
- **False merges**: Worse than duplicates - strict matching thresholds
- **Validation**: Reports issues, does not auto-fix

## Next Steps

1. Export your Goodreads library
2. Run the ingestion pipeline
3. Validate the results
4. Manually enrich anchor books in `books.csv` (set `anchor_type` for favorites/hits/misses)
5. Use query-based recommendations

