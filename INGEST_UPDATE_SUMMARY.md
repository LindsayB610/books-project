# Goodreads Ingestion Update Summary

## Key Changes to `ingest_goodreads.py`

### 1. Strict Exclusive Shelf Mapping
- **Before**: Inferred `read_status` from rating or Bookshelves
- **After**: Uses `Exclusive Shelf` field ONLY
  - `read` → `read`
  - `currently-reading` → `reading`
  - `to-read` → `want_to_read`
  - No inference from other fields

### 2. Read Count Handling
- **Before**: Could be None
- **After**: Defaults to `0` if missing
- `reread_count` = Read Count (as integer string)
- `reread` = `1` if count > 1, else `0`

### 3. Owned Copies → physical_owned
- Maps `Owned Copies` to `physical_owned`
- `1` if count > 0, else `0`

### 4. Bookshelves → Genres (Pipe-Delimited)
- **Before**: Comma-separated (same as Goodreads)
- **After**: Converts comma-separated to pipe-delimited (`|`)
- Example: `"fantasy, fiction, favorites"` → `"fantasy|fiction|favorites"`

### 5. Notes Formatting
- **Before**: Simple concatenation
- **After**: Labels added:
  - `"My Review: {review}\n\nPrivate Notes: {notes}"` (if both)
  - `"My Review: {review}"` (if only review)
  - `"Private Notes: {notes}"` (if only notes)

### 6. Publication Year Fallback
- Uses `Year Published`, falls back to `Original Publication Year` if missing

### 7. Work ID
- Leaves `work_id` blank (None) - let `merge_and_dedupe.py` assign/preserve

### 8. Full Schema Mapping
- Now maps all 37 canonical fields
- All preference fields left empty/null (for manual enrichment)

## Example Preview (3 Mapped Rows)

Assuming a Goodreads export with these sample rows:

### Row 1: Read book with rating and reread
**Goodreads fields:**
- Title: "The Seven Husbands of Evelyn Hugo"
- Author: "Taylor Jenkins Reid"
- ISBN13: "9781501139239"
- Exclusive Shelf: "read"
- My Rating: "5"
- Read Count: "2"
- Owned Copies: "1"
- Bookshelves: "favorites, historical-fiction, romance"
- Date Read: "2023/02/15"
- My Review: "Loved this book!"

**Mapped canonical row:**
```
work_id: None
title: "The Seven Husbands of Evelyn Hugo"
author: "Taylor Jenkins Reid"
isbn13: "9781501139239"
read_status: "read"
rating: "5"
reread_count: "2"
reread: "1"
physical_owned: "1"
genres: "favorites|historical-fiction|romance"
date_read: "2023-02-15"
notes: "My Review: Loved this book!"
```

### Row 2: Currently reading, no rating
**Goodreads fields:**
- Title: "Project Hail Mary"
- Author: "Andy Weir"
- ISBN13: "9780593135204"
- Exclusive Shelf: "currently-reading"
- My Rating: ""
- Read Count: "0"
- Owned Copies: "0"
- Bookshelves: "science-fiction, to-read"
- Date Read: ""

**Mapped canonical row:**
```
work_id: None
title: "Project Hail Mary"
author: "Andy Weir"
isbn13: "9780593135204"
read_status: "reading"
rating: None
reread_count: "0"
reread: "0"
physical_owned: "0"
genres: "science-fiction|to-read"
date_read: None
notes: None
```

### Row 3: To-read with private notes
**Goodreads fields:**
- Title: "The Midnight Library"
- Author: "Matt Haig"
- ISBN13: "9780525559474"
- Exclusive Shelf: "to-read"
- My Rating: ""
- Read Count: "0"
- Owned Copies: "1"
- Bookshelves: "fiction, philosophy"
- Private Notes: "Recommended by friend"

**Mapped canonical row:**
```
work_id: None
title: "The Midnight Library"
author: "Matt Haig"
isbn13: "9780525559474"
read_status: "want_to_read"
rating: None
reread_count: "0"
reread: "0"
physical_owned: "1"
genres: "fiction|philosophy"
date_read: None
notes: "Private Notes: Recommended by friend"
```

## Recommendation Engine Updates

### Changes to `recommend.py`:

1. **Query-based scoring**: Added `--query` and `--limit` args (default 5, range 3-5)

2. **Tag/genre-based scoring**:
   - Positive genres from `all_time_favorite` + `recent_hit`
   - Negative genres from `recent_miss` + `dnf`
   - Score = positive overlap - negative overlap

3. **Candidate selection**: Only `unread`, `want_to_read`, or `reading` status

4. **Output**: 3-5 results with "why this fits" reasons based on genre/tag matches

5. **No description matching**: Removed all description-based scoring

## Testing

To test the updated ingestion:
```bash
# Place your Goodreads export in sources/goodreads_export.csv
python scripts/ingest_goodreads.py

# This will show a preview of the first 3 mapped rows
# Then merge into books.csv:
python scripts/merge_and_dedupe.py
```

