# Books CSV Builder + Recommender

A system for building and maintaining a canonical `books.csv` that represents your reading history and preferences, merging data from multiple sources (Goodreads, Kindle, physical shelves) while preserving your manual annotations.

**Features:**
- 📚 Merge and deduplicate books from multiple sources
- 🔒 Protect manual annotations (ratings, notes, preferences)
- 🎯 Generate personalized recommendations based on anchor books
- 🌐 Optional read-only REST API for browsing and searching
- ✅ Comprehensive test suite for data safety

## Dataset-Per-User Architecture

This project supports multiple user datasets. Each dataset is self-contained in its own directory:

```
datasets/
├── default/          # Default dataset (used if --dataset not specified)
│   ├── sources/      # Input data (Goodreads export, etc.)
│   ├── books.csv     # Canonical output (edit this!)
│   └── reports/      # Validation and duplicate reports
├── lindsay/          # Example: user-specific dataset
│   ├── sources/
│   ├── books.csv
│   └── reports/
└── user_123/         # Example: another user dataset
    ├── sources/
    ├── books.csv
    └── reports/
```

All scripts accept a `--dataset` argument (default: `datasets/default`). This allows you to:
- Maintain separate reading histories for different users
- Test changes on a separate dataset
- Keep multiple book collections organized

## Quick Start

1. Create your dataset directory (or use the default):
   ```bash
   mkdir -p datasets/default/sources
   ```

2. Place your data sources in `datasets/default/sources/`:
   - `goodreads_export.csv` - Export from Goodreads
   - `kindle_library.json` or `.csv` - Kindle library data
   - `physical_shelf_photos/` - Photos of your bookshelves (deferred)

3. Ingest Goodreads data:
   ```bash
   python scripts/ingest_goodreads.py --dataset datasets/default
   ```

4. Run the merge pipeline:
   ```bash
   python scripts/merge_and_dedupe.py --dataset datasets/default
   ```

5. Validate your data:
   ```bash
   python scripts/validate_books_csv.py --dataset datasets/default
   ```

6. Check for possible duplicates:
   ```bash
   python scripts/find_duplicates.py --dataset datasets/default
   ```

7. Manually edit `datasets/default/books.csv` to add your preferences for:
   - ~10-20 all-time favorites (set `anchor_type` to `all_time_favorite`)
   - ~20 recent reads (set `anchor_type` to `recent_hit` or `recent_miss`)

8. Generate recommendations:
   ```bash
   python scripts/recommend.py --dataset datasets/default --query "urban fantasy"
   ```

## Philosophy

- **books.csv is the single source of truth** - safe to edit manually
- **Never overwrites manual fields** - your ratings, notes, and preferences are protected
- **One row per work** - not per edition (unless explicitly needed)
- **Selective enrichment** - only enrich the books that matter for recommendations

## Schema

See `docs/DESIGN.md` for the complete schema and merge rules.

## Directory Structure

```
books-project/
├── datasets/              # User datasets (dataset-per-user)
│   └── default/          # Default dataset
│       ├── sources/      # Input data
│       ├── books.csv     # Canonical output (edit this!)
│       └── reports/      # Validation and duplicate reports
├── api/                  # API layer (FastAPI server)
│   ├── server.py         # Main API server
│   ├── filters.py        # Filtering/search logic
│   ├── recommendations.py # Recommendation API wrapper
│   └── README.md         # API documentation
├── scripts/              # Ingestion and pipeline scripts
├── tests/                # Test suite
│   ├── fixtures/         # Test data fixtures
│   └── README.md         # Test documentation
├── utils/                # Core utilities
├── docs/                 # Documentation (see docs/README.md)
└── README.md             # This file
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

All scripts support `--dataset` argument (default: `datasets/default`):

- **`scripts/ingest_goodreads.py`** - Converts Goodreads export to canonical format
  ```bash
  python scripts/ingest_goodreads.py --dataset datasets/default
  ```

- **`scripts/merge_and_dedupe.py`** - Main merge pipeline (ingests sources, deduplicates, merges)
  ```bash
  python scripts/merge_and_dedupe.py --dataset datasets/default
  ```

- **`scripts/validate_books_csv.py`** - Validates data quality and flags issues
  ```bash
  python scripts/validate_books_csv.py --dataset datasets/default
  ```

- **`scripts/find_duplicates.py`** - Finds and reports possible duplicates using fuzzy matching
  ```bash
  python scripts/find_duplicates.py --dataset datasets/default
  ```

- **`scripts/recommend.py`** - Generates recommendations based on anchor books
  ```bash
  python scripts/recommend.py --dataset datasets/default --query "urban fantasy" --limit 5
  ```

- **`scripts/ingest_kindle.py`** - Converts Kindle library to canonical format

## API (Optional)

A read-only REST API is available for browsing, filtering, searching, and getting recommendations:

```bash
# Start the API server
python -m api.server
# or
uvicorn api.server:app --reload
```

Then visit `http://localhost:8000/docs` for interactive API documentation.

See `api/README.md` for full API documentation.

## Testing

The project includes a test suite focused on data safety and critical logic:

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v
```

See `tests/README.md` for test documentation.

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

## Example: Working with Multiple Datasets

```bash
# Create a new dataset for a specific user
mkdir -p datasets/lindsay/sources

# Ingest Goodreads data for this user
python scripts/ingest_goodreads.py --dataset datasets/lindsay

# Merge and deduplicate
python scripts/merge_and_dedupe.py --dataset datasets/lindsay

# Validate
python scripts/validate_books_csv.py --dataset datasets/lindsay

# Generate recommendations
python scripts/recommend.py --dataset datasets/lindsay --query "mystery" --limit 5
```

## Next Steps

1. Review `docs/DESIGN.md` for the full specification
2. Create your dataset: `mkdir -p datasets/default/sources`
3. Add your source data to `datasets/default/sources/`
4. Ingest: `python scripts/ingest_goodreads.py --dataset datasets/default`
5. Run the pipeline: `python scripts/merge_and_dedupe.py --dataset datasets/default`
6. Validate: `python scripts/validate_books_csv.py --dataset datasets/default`
7. Manually enrich your anchor books in `datasets/default/books.csv`
8. Generate recommendations: `python scripts/recommend.py --dataset datasets/default`

