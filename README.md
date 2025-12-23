# Books CSV Builder + Recommender

A system for building and maintaining a canonical `books.csv` that represents your reading history and preferences, merging data from multiple sources (Goodreads, Kindle, physical shelves) while preserving your manual annotations.

## Quick Start

1. Place your data sources in the `sources/` directory:
   - `goodreads_export.csv` - Export from Goodreads
   - `kindle_library.json` or `.csv` - Kindle library data
   - `physical_shelf_photos/` - Photos of your bookshelves (deferred)

2. Run the ingestion pipeline:
   ```bash
   python scripts/merge_and_dedupe.py
   ```

3. Validate your data:
   ```bash
   python scripts/validate.py
   ```

4. Check for possible duplicates:
   ```bash
   python scripts/find_duplicates.py
   ```

5. Manually edit `books.csv` to add your preferences for:
   - ~10-20 all-time favorites (set `anchor_type` to `all_time_favorite`)
   - ~20 recent reads (set `anchor_type` to `recent_hit` or `recent_miss`)

6. Generate recommendations:
   ```bash
   python scripts/recommend.py
   ```

## Philosophy

- **books.csv is the single source of truth** - safe to edit manually
- **Never overwrites manual fields** - your ratings, notes, and preferences are protected
- **One row per work** - not per edition (unless explicitly needed)
- **Selective enrichment** - only enrich the books that matter for recommendations

## Schema

See `DESIGN.md` for the complete schema and merge rules.

## Directory Structure

```
books-project/
├── books.csv              # Canonical output (edit this!)
├── sources/               # Input data
├── scripts/               # Ingestion scripts
├── utils/                 # Utilities
└── DESIGN.md             # Full design documentation
```

## Manual Fields (Protected)

These fields are never overwritten by the pipeline once you set them:
- `rating`, `reread`, `reread_count`
- `dnf`, `dnf_reason`
- `pacing_rating`, `tone`, `vibe`
- `what_i_wanted`, `did_it_deliver`
- `favorite_elements`, `pet_peeves`, `notes`
- `anchor_type`

## Scripts

- **`scripts/merge_and_dedupe.py`** - Main merge pipeline (ingests sources, deduplicates, merges)
- **`scripts/validate.py`** - Validates data quality and flags issues
- **`scripts/find_duplicates.py`** - Finds and reports possible duplicates using fuzzy matching
- **`scripts/recommend.py`** - Generates recommendations based on anchor books
- **`scripts/ingest_goodreads.py`** - Converts Goodreads export to canonical format
- **`scripts/ingest_kindle.py`** - Converts Kindle library to canonical format

## Features

### Smart Deduplication
- Uses ISBN13 > ASIN > title+author matching
- Bounded fuzzy matching with high thresholds (0.90+)
- Reports possible duplicates for manual review

### Data Validation
- Checks required fields, identifier formats, ratings
- Validates date formats and format consistency
- Flags anchor books missing key data

### Recommendations
- Uses `anchor_type` books to learn preferences
- Extracts tones, vibes, genres, favorite elements
- Scores unread books based on preference matching

## Next Steps

1. Review `DESIGN.md` for the full specification
2. Add your source data to `sources/`
3. Run the pipeline: `python scripts/merge_and_dedupe.py`
4. Validate: `python scripts/validate.py`
5. Manually enrich your anchor books in `books.csv`
6. Generate recommendations: `python scripts/recommend.py`

