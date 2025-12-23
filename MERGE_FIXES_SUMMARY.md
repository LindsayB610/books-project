# Merge and Dedupe Fixes Summary

## Changes Made to `scripts/merge_and_dedupe.py`

### 1. Load Canonical Source Files (Not Raw Exports)

**Before:**
- Read `sources/goodreads_export.csv` (raw export)
- Read `sources/kindle_library.csv` (raw export)

**After:**
- Read `sources/goodreads_canonical.csv` (output of `ingest_goodreads.py`)
- Read `sources/kindle_canonical.csv` (output of `ingest_kindle.py`) - if present
- Canonical files are already in the correct format, no transformation needed

### 2. Never Write Low-Confidence Markers to User Fields

**Before:**
- Appended `[LOW_CONFIDENCE_MATCH: ...]` to `notes` field

**After:**
- No markers written to any user fields
- Uncertainty recorded only in `reports/possible_duplicates.csv`
- Reports directory created automatically if needed

### 3. Clear Confidence Threshold Logic

**Before:**
- Unclear threshold (0.70 for auto-merge, 0.75 for possible duplicate)
- Branching logic made threshold unreachable

**After:**
- `AUTO_MERGE_THRESHOLD = 0.92` (high threshold, prefer false negatives)
- `POSSIBLE_DUPLICATE_THRESHOLD = 0.80`
- Clear behavior:
  - `confidence >= 0.92`: Auto-merge via `safe_merge`
  - `0.80 <= confidence < 0.92`: Do NOT merge, add as new, record in report
  - `confidence < 0.80`: Add as new, no duplicate record

### 4. Work ID Handling

**Before:**
- Generated `work_id` during normalization (for all rows)

**After:**
- Do NOT generate `work_id` during normalization
- Generate `work_id` only when adding a truly new row (no match found or not auto-merged)
- Preserve existing `work_id` on merges (via `safe_merge`)

### 5. Avoid Fragile list.index() Usage

**Before:**
- Used `merged.index(best_match)` which could fail with duplicate dicts

**After:**
- Updated `find_matches()` to return `(index, matched_row, confidence)` tuples
- Use index directly: `merged[best_idx] = safe_merge(...)`
- Stable and safe

### 6. Possible Duplicates Report

**New Feature:**
- Writes `reports/possible_duplicates.csv` with:
  - `work_id_1`, `title_1`, `author_1`, `isbn13_1`
  - `work_id_2`, `title_2`, `author_2`, `isbn13_2`
  - `confidence`, `reason`
- Created automatically if needed
- Human-readable for manual review

## Updated File Paths

**Inputs:**
- `sources/goodreads_canonical.csv` - Output from `ingest_goodreads.py`
- `books.csv` - Existing canonical database

**Output:**
- `books.csv` - Updated canonical database (preserves manual fields)

**Reports:**
- `reports/possible_duplicates.csv` - Possible duplicates for manual review

## Workflow

```bash
# 1. Ingest Goodreads data (produces canonical format)
python scripts/ingest_goodreads.py
# Output: sources/goodreads_canonical.csv

# 2. Merge into books.csv
python scripts/merge_and_dedupe.py
# Input: sources/goodreads_canonical.csv, books.csv
# Output: books.csv (updated), reports/possible_duplicates.csv (if any)

# 3. Validate
python scripts/validate_books_csv.py

# 4. Review possible duplicates (if any)
# Check: reports/possible_duplicates.csv
```

## Data Safety

- **Protected fields**: Never overwritten (via `safe_merge`)
- **Work ID**: Stable, preserved on merges
- **User fields**: No markers or annotations written
- **False merges**: Prevented by high threshold (0.92)
- **Uncertainty**: Reported, not auto-resolved

## Key Improvements

1. **Clear pipeline**: Ingest → Canonical → Merge (no raw exports in merge)
2. **Clean user data**: No markers in notes or other fields
3. **Stable work_ids**: Only generated for new rows, preserved on merges
4. **Safe indexing**: Uses returned indices, not fragile `list.index()`
5. **Clear thresholds**: 0.92 auto-merge, 0.80 possible duplicate
6. **Report-based**: Uncertainty goes to reports, not user data

