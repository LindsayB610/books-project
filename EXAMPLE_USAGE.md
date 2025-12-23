# Example Usage

This document shows how to use the Books CSV Builder pipeline.

## Step 1: Prepare Your Source Data

### Goodreads Export
1. Go to Goodreads → My Books
2. Click "Import and export" → "Export library"
3. Save the CSV as `sources/goodreads_export.csv`

### Kindle Library
Export your Kindle library (format may vary):
- Save as `sources/kindle_library.csv` or `sources/kindle_library.json`
- Should include: Title, Author, ASIN, ISBN fields

### Physical Shelf Photos (Future)
- Place photos in `sources/physical_shelf_photos/`
- OCR processing will be added later

## Step 2: Run the Pipeline

### Option A: Run Individual Ingestion Scripts First

```bash
# Convert Goodreads export to canonical format
python scripts/ingest_goodreads.py

# Convert Kindle library to canonical format
python scripts/ingest_kindle.py

# Merge everything into books.csv
python scripts/merge_and_dedupe.py
```

### Option B: Run Merge Directly (Auto-detects sources)

```bash
python scripts/merge_and_dedupe.py
```

The merge script will:
- Load existing `books.csv` (if it exists)
- Load all source data from `sources/`
- Deduplicate and merge
- Write updated `books.csv`

## Step 3: Manually Enrich Your Anchor Books

Open `books.csv` in your favorite editor and fill in preference fields for:

### ~10-20 All-Time Favorites
Set `anchor_type` to `all_time_favorite` and fill in:
- `rating` (1-5, can use halves like 4.5)
- `reread` (1 if you've reread it)
- `reread_count` (how many times)
- `tone`, `vibe` (e.g., "dark", "hopeful", "cozy mystery")
- `favorite_elements` (what worked)
- `notes` (any thoughts)

### ~20 Recent Reads (Hits and Misses)
Set `anchor_type` to `recent_hit` or `recent_miss` and fill in:
- `rating`
- `what_i_wanted` (what were you hoping for?)
- `did_it_deliver` (1 or 0)
- `favorite_elements` or `pet_peeves`
- `dnf` and `dnf_reason` if you didn't finish

## Step 4: Re-run Pipeline (Safe)

When you add new source data or update sources:

```bash
python scripts/merge_and_dedupe.py
```

**Your manual fields will be preserved!** The pipeline only updates:
- Metadata (publication_year, publisher, etc.)
- Format flags
- Source provenance

It will **never overwrite**:
- `rating`, `notes`, `tone`, `vibe`
- `favorite_elements`, `pet_peeves`
- `anchor_type`
- Any other preference fields you've set

## Example CSV Row

```csv
isbn13,asin,title,author,...,rating,reread,tone,vibe,anchor_type,notes
9780143127741,B00ABC123,The Seven Husbands of Evelyn Hugo,Jenkins Reid, Taylor,2022,Atria Books,en,400,Historical Fiction,romance,kindle,0,1,0,123456,https://www.goodreads.com/book/show/123456,B00ABC123,goodreads,kindle,2023-01-15,2023-02-01,2024-01-01,read,5,1,2,,,4.5,warm,glamorous Hollywood drama,escapist historical fiction,1,character development; plot twists; emotional depth,,,all_time_favorite,One of my all-time favorites. The character development is incredible.
```

## Troubleshooting

### "No source data found"
- Make sure your source files are in the `sources/` directory
- Check file names match expected names (see Step 1)

### Duplicate books appearing
- The deduplication uses ISBN13 > ASIN > title+author matching
- If books aren't matching, check that identifiers are present in source data
- Low-confidence matches will be flagged in `notes` field

### Manual fields being overwritten
- This shouldn't happen! Check that fields are in the `PROTECTED_FIELDS` list in `utils/csv_utils.py`
- If it does happen, check the merge logic in `safe_merge()` function

## Next Steps

Once you have a well-enriched `books.csv`:
1. Use it for recommendation generation
2. Export subsets for specific purposes
3. Track reading progress over time

