# Targeted Refinements Summary

## Schema Changes

### Added Fields
1. **`work_id`** (first column)
   - Stable identifier (UUID or hash-based)
   - Generated once for new records using priority: ISBN13 > ASIN > hash(title+author)
   - Preserved across re-runs (protected field)
   - Format: `isbn13:XXXXXXXXXXXXX`, `asin:XXXXXXXXXX`, or `hash:XXXXXXXX`

2. **`would_recommend`** (0/1)
   - Boolean flag for recommendation preference
   - Protected field (never overwritten once set)

### Removed Fields
1. **`kindle_asin`**
   - Removed from canonical schema
   - Merged into single `asin` field
   - Backward compatibility: merge script still accepts `kindle_asin` from old data and merges it into `asin`

### Field Order
- `work_id` is now the first column in `books.csv`
- All other fields remain in the same order

## New Scripts

### 1. `scripts/validate_books_csv.py`
Comprehensive validation script that checks:
- Duplicate `work_id` values
- Duplicate ISBN13 or ASIN values
- Missing required fields (title, author)
- Invalid values:
  - Ratings out of range (1-5)
  - Non-integer `reread_count`
  - Invalid enum values (`read_status`, `anchor_type`, boolean fields)
- Prints human-readable report
- Does NOT auto-fix (safe to run before/after merges)
- Exits with error code if errors found

### 2. `scripts/recommendations_stub.py`
Generates structured prompts for recommendation generation:
- Reads `books.csv` and extracts books with `anchor_type` set
- Separates by type: `all_time_favorite`, `recent_hit`, `recent_miss`, `dnf`
- Outputs Markdown or JSON format
- Includes key preference signals:
  - `tone`, `vibe`, `pacing_rating`
  - `favorite_elements`, `pet_peeves`
  - `what_i_wanted`, `did_it_deliver`
  - `would_recommend`
- Designed for human-AI conversation (no ML/embeddings)

Usage:
```bash
python scripts/recommendations_stub.py --format markdown > prompt.md
python scripts/recommendations_stub.py --format json > prompt.json
```

## Enhanced Features

### Bounded Fuzzy Matching (Strict)
Updated `utils/deduplication.py`:
- **Fuzzy matching ONLY applies when both ISBN13 and ASIN are missing**
- Uses aggressive normalization + high similarity threshold (0.92+)
- Requires both title AND author similarity >= 0.92
- If confidence below threshold: does NOT merge, emits "possible duplicate" for manual review
- Philosophy: False merges are worse than duplicates

### Work ID Generation
New `utils/work_id.py`:
- Generates stable IDs based on identifiers
- Priority: ISBN13 > ASIN > hash(title+author)
- Preserves existing `work_id` values (protected field)
- Used automatically in merge pipeline

## Updated Scripts

### `scripts/merge_and_dedupe.py`
- Generates `work_id` for new books
- Preserves existing `work_id` values
- Backward compatibility: merges `kindle_asin` into `asin` if present
- Updated schema to include `work_id` and `would_recommend`

### `scripts/ingest_goodreads.py`
- Removed `kindle_asin` field
- Added `would_recommend` field

### `scripts/ingest_kindle.py`
- Removed `kindle_asin` field (merged into `asin`)
- Added `would_recommend` field

### `scripts/find_duplicates.py`
- Updated to use single `asin` field (removed `kindle_asin` references)

### `scripts/validate.py`
- Updated to use single `asin` field

### `utils/csv_utils.py`
- Added `work_id` and `would_recommend` to protected fields
- Enhanced `safe_merge()` to preserve `work_id` from existing records

## Assumptions Made

1. **Backward Compatibility**: Old data with `kindle_asin` will be automatically merged into `asin` during merge operations. This is a one-time migration.

2. **Work ID Stability**: Once a `work_id` is generated, it should remain stable. The generation logic prioritizes identifiers (ISBN13/ASIN) over hashes for better stability.

3. **Fuzzy Matching Safety**: The 0.92 threshold for fuzzy matching is intentionally high to prevent false merges. Lower confidence matches are flagged for manual review rather than auto-merged.

4. **Validation Philosophy**: The validation script reports issues but does not auto-fix, allowing manual review and control.

5. **Recommendations Stub**: The stub is designed as scaffolding for human-AI conversation, not as a full recommendation engine. It outputs structured prompts that can be used with LLMs or other AI systems.

## Files Modified

- `books.csv` - Updated header with `work_id` (first), removed `kindle_asin`, added `would_recommend`
- `scripts/merge_and_dedupe.py` - Work ID generation, schema updates
- `scripts/ingest_goodreads.py` - Schema updates
- `scripts/ingest_kindle.py` - Schema updates
- `scripts/find_duplicates.py` - Removed `kindle_asin` references
- `scripts/validate.py` - Removed `kindle_asin` references
- `utils/deduplication.py` - Strict fuzzy matching (only when identifiers missing)
- `utils/csv_utils.py` - Protected fields updated
- `utils/normalization.py` - Removed `kindle_asin` references
- `utils/work_id.py` - NEW: Work ID generation logic
- `DESIGN.md` - Updated schema documentation

## Files Created

- `scripts/validate_books_csv.py` - Comprehensive validation
- `scripts/recommendations_stub.py` - Structured prompt generation
- `utils/work_id.py` - Work ID utilities

## Testing Recommendations

Before ingesting real data:
1. Run `python scripts/validate_books_csv.py` on empty `books.csv` (should pass)
2. Test work_id generation with sample data
3. Verify fuzzy matching only triggers when ISBN13/ASIN missing
4. Test recommendations_stub with sample anchor books
5. Verify backward compatibility with old `kindle_asin` data

