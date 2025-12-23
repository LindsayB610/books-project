# Books CSV Builder + Recommender - Design Document

## CSV Schema (`books.csv`)

### Core Identifiers (for deduplication)
- `isbn13` - Primary stable identifier (preferred)
- `asin` - Amazon/Kindle identifier (secondary)
- `title` - Normalized title (for fallback matching)
- `author` - Normalized author name (last, first)
- `work_id` - Stable internal identifier (isbn13, asin, or hash-based) - **This is the primary stable identifier**

### Metadata (auto-populated from sources)
- `publication_year` - Year published
- `publisher` - Publisher name
- `language` - Language code (e.g., "en", "fr")
- `pages` - Page count
- `genres` - Pipe-delimited tags/genres: "fantasy|fiction|mystery" (use `|` for multi-valued fields, tags are lowercased)
- `description` - Book description/summary

### Formats & Ownership
- `formats` - Pipe-delimited: "kindle|physical|audiobook" (use `|` for multi-valued fields)
- `physical_owned` - 0/1 flag
- `kindle_owned` - 0/1 flag
- `audiobook_owned` - 0/1 flag

### Source Provenance (for debugging/tracking)
- `goodreads_id` - Goodreads book ID
- `goodreads_url` - Goodreads URL
- `sources` - Pipe-delimited list: "goodreads|kindle|physical_shelf" (use `|` for multi-valued fields)

### Dates
- `date_added` - When first added to system (YYYY-MM-DD)
- `date_read` - Date finished reading (YYYY-MM-DD or YYYY-MM) - **Optional/deprecated: not populated by default**
- `date_updated` - Last update timestamp (YYYY-MM-DD)

### Status
- `read_status` - "read", "unread", "dnf", "reading", "want_to_read"

### Manual Preference Fields (HIGH PRIORITY - never overwrite)
- `rating` - 1-5 (allow halves: 1, 1.5, 2, 2.5, etc.)
- `reread` - 0/1 flag
- `reread_count` - Number of times reread
- `dnf` - 0/1 flag (did not finish)
- `dnf_reason` - Free text reason
- `pacing_rating` - 1-5 (how was the pacing?)
- `tone` - Free text (e.g., "dark", "hopeful", "melancholic")
- `vibe` - Free text (e.g., "cozy mystery", "epic fantasy", "literary fiction")
- `what_i_wanted` - Free text (what were you hoping for?)
- `did_it_deliver` - 0/1 flag
- `favorite_elements` - Free text (what worked?)
- `pet_peeves` - Free text (what didn't work?)
- `notes` - Free text (general notes)
- `anchor_type` - "all_time_favorite", "recent_hit", "recent_miss", "dnf", or empty

---

## Deduplication Rules

### Priority Order for Matching
1. **ISBN13 match** (highest confidence)
2. **ASIN match** (high confidence)
3. **Normalized title + author match** (lower confidence, requires fuzzy matching)

### Normalization Rules
- **Title**: lowercase, remove punctuation, normalize whitespace, remove common prefixes ("the", "a", "an")
- **Author**: "Last, First" format, lowercase, remove punctuation
- **ISBN13**: strip hyphens/spaces, validate checksum
- **ASIN**: case-insensitive

### Merge Strategy
When merging records from multiple sources:
1. If work_id matches → merge into single row
2. Combine formats (union of all formats)
3. Combine sources (union of all sources)
4. **Never overwrite** manual preference fields if they exist
5. Update metadata only if field is empty/null
6. Prefer most complete metadata (more fields filled)

---

## Update Rules (Critical)

### Safe Fields (can be auto-updated)
- Metadata fields (publication_year, publisher, etc.)
- Format flags (physical_owned, kindle_owned, etc.)
- Source provenance fields
- Dates (date_updated always updates)

### Protected Fields (never overwrite if manually set)
- All preference fields: rating, reread, reread_count, dnf, dnf_reason, pacing_rating, tone, vibe, what_i_wanted, did_it_deliver, favorite_elements, pet_peeves, notes, anchor_type
- read_status (if manually set)
- date_read (if manually set)

### Update Logic
```python
def safe_merge(existing_row, new_data):
    # For protected fields: only update if existing is empty/null
    # For safe fields: update if new data is more complete
    # Always preserve manual annotations
```

---

## Pipeline Architecture

### Structure
```
books-project/
├── books.csv                    # Canonical output (human-editable)
├── sources/                     # Input data
│   ├── goodreads_export.csv
│   ├── kindle_library.json     # (or CSV)
│   └── physical_shelf_photos/  # Images for OCR
├── scripts/
│   ├── ingest_goodreads.py
│   ├── ingest_kindle.py
│   ├── ingest_physical_shelf.py
│   └── merge_and_dedupe.py     # Main merge logic
├── utils/
│   ├── normalization.py        # Title/author normalization
│   ├── deduplication.py        # Matching logic
│   └── csv_utils.py            # Safe CSV reading/writing
└── DESIGN.md                   # This file
```

### Workflow
1. **Ingest** each source independently → temporary CSVs
2. **Normalize** all identifiers and metadata
3. **Deduplicate** across all sources
4. **Merge** into canonical books.csv (preserving manual fields)
5. **Validate** output

### Key Functions
- `normalize_title(title)` → normalized string
- `normalize_author(author)` → "Last, First"
- `generate_work_id(row)` → isbn13, asin, or hash(title+author)
- `find_matches(new_row, existing_rows)` → list of potential matches
- `safe_merge(existing, new)` → merged row (respects protected fields)

---

## Implementation Notes

### CSV Format
- UTF-8 encoding
- Comma-separated
- Quote fields containing commas
- Header row always present
- Sort by: author, then title (for readability)

### Error Handling
- Log all merge decisions
- Flag ambiguous matches for manual review
- Preserve original source data in provenance fields

### Future Extensibility
- Schema can evolve by adding columns (backward compatible)
- New sources can be added as new ingest scripts
- Recommendation engine will read books.csv and focus on anchor_type books

---

## Implementation Status

1. ✅ Design schema (this document)
2. ✅ Create sample books.csv with headers
3. ✅ Implement normalization utilities
4. ✅ Implement deduplication logic (with bounded fuzzy matching)
5. ✅ Create ingest scripts (Goodreads, Kindle)
6. ✅ Test merge pipeline
7. ✅ Add validation and logging
8. ✅ Add possible-duplicate reporting
9. ✅ Create recommendations stub
10. ⏸️ Physical shelf OCR (deferred until Goodreads+Kindle stable)

## Enhanced Features

### Bounded Fuzzy Matching
- High threshold (0.90+) for title and author similarity
- Only triggers when both title AND author similarity >= 0.90
- Prevents false positives while catching legitimate duplicates

### Duplicate Reporting
- `find_duplicates.py` scans entire CSV for possible duplicates
- Reports matches with confidence scores
- Helps identify books that should be merged manually

### Validation
- Comprehensive data quality checks
- Validates ratings, dates, identifiers
- Flags anchor books missing key preference data

