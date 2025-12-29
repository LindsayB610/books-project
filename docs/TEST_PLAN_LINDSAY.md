# Test Plan: Goodreads Import for datasets/lindsay

## Pre-Flight Verification

### 1. Verify Dataset Structure

**Check paths:**
```bash
# Verify input file exists
ls -la datasets/lindsay/sources/goodreads_export.csv

# Check if books.csv exists (may not exist yet - that's OK)
ls -la datasets/lindsay/books.csv 2>/dev/null || echo "books.csv does not exist yet (will be created)"

# Verify reports directory exists or will be created
ls -d datasets/lindsay/reports/ 2>/dev/null || echo "reports/ directory will be created automatically"
```

**Expected:**
- ✅ `datasets/lindsay/sources/goodreads_export.csv` exists
- ⚠️ `datasets/lindsay/books.csv` may not exist (will be created by merge script)
- ⚠️ `datasets/lindsay/reports/` may not exist (will be created automatically)

**If paths don't exist:**
- Scripts will create missing directories automatically
- Only `goodreads_export.csv` must exist before running

---

## Step 1: Goodreads Ingestion (Preview-Only)

### Command
```bash
python scripts/ingest_goodreads.py --dataset datasets/lindsay
```

### What It Does
- **Reads from:** `datasets/lindsay/sources/goodreads_export.csv`
- **Writes to:** `datasets/lindsay/sources/goodreads_canonical.csv`
- **Prints:** Preview of first 3 mapped rows (non-sensitive fields only)

### Expected Behavior
✅ **Correct mappings:**
- `read_status` comes ONLY from `Exclusive Shelf`:
  - `read` → `read`
  - `currently-reading` → `reading`
  - `to-read` → `want_to_read`
  - Other/empty → `None`
- `tags` populated from `Bookshelves`:
  - Comma-separated in Goodreads → pipe-delimited in canonical
  - All tags lowercased
  - Example: `"favorites, historical-fiction"` → `"favorites|historical-fiction"`
- `genres` = `None` (reserved for future enrichment)
- `date_read` = `None` (not populated)
- `reread_count` from `Read Count` (integer, default 0)
- `reread` = 1 if `reread_count > 1`, else 0
- `physical_owned` = 1 if `Owned Copies > 0`, else 0 (None if parse fails)
- `isbn13` normalized (None if normalization fails)
- `work_id` = None (not generated during ingestion)

### Preview Output Format
```
Row 1:
  Title: [title]
  Author: [author]
  ISBN13: [isbn13 or N/A]
  Read Status: [read_status or N/A]
  Rating: [rating or N/A]
  Reread Count: [reread_count or N/A]
  Physical Owned: [physical_owned or N/A]
  Tags: [tags or N/A]
  Genres: [genres or N/A]
  Goodreads ID: [goodreads_id or N/A]
```

### ⚠️ Stop and Report If:
- Any `read_status` value is not `read`, `reading`, `want_to_read`, or empty/None
- `tags` contains commas (should be pipe-delimited)
- `tags` contains uppercase (should be lowercased)
- `genres` is populated (should be empty/None)
- `date_read` is populated (should be empty/None)
- `work_id` is populated (should be empty/None)

**Note:** CSV files store empty values as empty strings, which is equivalent to None for our purposes.

---

## Step 2: Smoke-Check Canonical Output

### Verification Commands

**Note:** You can use the helper script `scripts/smoke_check_canonical.py` for a concise report, or use the Python one-liners below for manual inspection.

**Helper script (optional):**
```bash
python scripts/smoke_check_canonical.py --dataset datasets/lindsay
```

**Manual checks (Python one-liners):**

**1. Check header matches canonical schema:**
```bash
head -1 datasets/lindsay/sources/goodreads_canonical.csv
```

**Expected header:**
```
work_id,isbn13,asin,title,author,publication_year,publisher,language,pages,genres,tags,description,formats,physical_owned,kindle_owned,audiobook_owned,goodreads_id,goodreads_url,sources,date_added,date_read,date_updated,read_status,rating,reread,reread_count,dnf,dnf_reason,pacing_rating,tone,vibe,what_i_wanted,did_it_deliver,favorite_elements,pet_peeves,notes,anchor_type,would_recommend
```

**B) Unique read_status values (CSV-safe):**
```bash
python -c "import csv; from collections import Counter; p='datasets/lindsay/sources/goodreads_canonical.csv'; c=Counter(); f=open(p, newline='', encoding='utf-8'); r=csv.DictReader(f); [c.update([(row.get('read_status') or '').strip()]) for row in r]; print(c)"
```

**Expected values:**
- `read`, `reading`, `want_to_read`, or empty string
- **Should NOT see:** `currently-reading`, `to-read`, or other Goodreads values

**C) Confirm genres is empty (reserved for external enrichment):**
```bash
python -c "import csv; p='datasets/lindsay/sources/goodreads_canonical.csv'; f=open(p, newline='', encoding='utf-8'); r=csv.DictReader(f); vals=set((row.get('genres') or '').strip() for row in r); print(vals)"
```

**Expected:**
- Should be `{''}` or `set()` (all values empty/None)
- Genres reserved for future enrichment

**D) Confirm tags are pipe-delimited and lowercased (sample + bad examples):**
```bash
python -c "import csv, itertools, re; p='datasets/lindsay/sources/goodreads_canonical.csv'; f=open(p, newline='', encoding='utf-8'); r=csv.DictReader(f); tags=[(row.get('tags') or '').strip() for row in itertools.islice(r, 200)]; bad=[t for t in tags if t and (',' in t or re.search(r'[A-Z]', t))]; sample=[t for t in tags if t][:10]; print('sample tags:', sample); print('bad tags examples:', bad[:10])"
```

**Expected:**
- `sample tags:` shows pipe-delimited, lowercased examples
- `bad tags examples:` should be empty (no commas, no uppercase)
- Example: `['favorites|historical-fiction|romance', 'fantasy|urban-fantasy']`

**E) Confirm date_read is empty (we don't populate it):**
```bash
python -c "import csv; from collections import Counter; p='datasets/lindsay/sources/goodreads_canonical.csv'; c=Counter(); f=open(p, newline='', encoding='utf-8'); r=csv.DictReader(f); [c.update([(row.get('date_read') or '').strip()]) for row in r]; print(list(c.items())[:10])"
```

**Expected:**
- Mostly empty strings: `[('', N)]` where N is the count
- `date_read` not populated by ingestion

---

## Step 3: Merge and Dedupe

### Command
```bash
python scripts/merge_and_dedupe.py --dataset datasets/lindsay
```

### What It Does
- **Reads from:**
  - `datasets/lindsay/books.csv` (if exists, otherwise starts empty)
  - `datasets/lindsay/sources/goodreads_canonical.csv`
- **Writes to:**
  - `datasets/lindsay/books.csv` (creates if doesn't exist)
  - `datasets/lindsay/reports/possible_duplicates.csv` (if any possible duplicates found)

### Expected Behavior
✅ **Correct behavior:**
- Creates `datasets/lindsay/books.csv` if it doesn't exist
- Creates `datasets/lindsay/reports/` directory if missing
- Generates `work_id` only for truly new rows (not for merged rows)
- Preserves existing `work_id` on merges
- Uses `safe_merge()` to preserve protected/manual fields
- Combines `formats`, `sources`, `tags` using pipe-delimited union
- Reports possible duplicates (confidence >= 0.80 but < 0.92) to `reports/possible_duplicates.csv`

### Output Messages
```
============================================================
Books CSV Merge and Deduplication
Dataset: datasets/lindsay
============================================================

Loading existing books.csv...
  Found X existing books
  (or: No existing books.csv found (will create new))

Loading canonical source data from datasets/lindsay/sources/...
  Found X books from goodreads_canonical.csv

Merging and deduplicating...
  Merged: [title] (confidence: 0.95)
  Added new: [title]
  Added (possible duplicate): [title] (confidence: 0.85)

⚠️  Found X possible duplicate(s) (confidence >= 0.80)
  Wrote report to datasets/lindsay/reports/possible_duplicates.csv
  Review manually and merge if appropriate

Writing canonical books.csv...
  Wrote X books to books.csv
```

### ⚠️ Stop and Report If:
- `work_id` is generated for rows that should have been merged
- Protected fields (rating, notes, etc.) are overwritten
- `formats`, `sources`, or `tags` contain commas (should be pipe-delimited)
- Script crashes or produces unexpected errors

---

## Step 4: Validation

### Command
```bash
python scripts/validate_books_csv.py --dataset datasets/lindsay
```

### What It Does
- Reads `datasets/lindsay/books.csv`
- Validates data quality without auto-fixing
- Reports errors, warnings, and info

### Expected Output (Clean Run)

**On first import (expected warnings):**
```
Loading datasets/lindsay/books.csv...
Validating X books...

=== Validation Report ===

INFO: Validating X books
INFO: All work_ids are unique
INFO: All ISBN13 values are unique
INFO: All ASIN values are unique
WARNING: X books missing required field: title
WARNING: X books missing required field: author
WARNING: X books have invalid read_status (expected: read, reading, want_to_read, unread, dnf, None)
WARNING: X books have invalid rating (must be 0-5, allow halves)
WARNING: X books have invalid reread_count (must be integer >= 0)
WARNING: X books have invalid dnf (must be 0 or 1)
WARNING: X books have delimiter issues in pipe-delimited fields
```

### Expected Warnings on First Import
✅ **Normal/Expected:**
- Missing `title`/`author` (if Goodreads export has incomplete data)
- Invalid `read_status` (if Goodreads has unexpected values - should be rare)
- Invalid `rating` (if Goodreads has non-numeric or out-of-range values)
- Delimiter issues (if tags contain commas - should be caught by ingestion)

### Real Problems (Require Investigation)
❌ **Should NOT see:**
- Duplicate `work_id` (indicates merge bug)
- Duplicate ISBN13/ASIN (indicates deduplication failure)
- Many books with invalid `read_status` (indicates mapping bug)
- Many delimiter issues (indicates ingestion bug)

### Exit Codes
- **Exit 0:** No errors (warnings are OK)
- **Exit 1:** Errors found (requires investigation)

---

## Step 5: Recommendation Sanity Test

### Command
```bash
python scripts/recommend.py --dataset datasets/lindsay --query "urban fantasy series" --limit 5
```

### What It Does
- Reads `datasets/lindsay/books.csv`
- Extracts preferences from anchor books (`anchor_type` populated)
- Scores unread books based on tag/genre overlap
- Returns 3-5 recommendations with reasons

### Expected Behavior (No Anchors Yet)

**If no anchor books exist:**
```
Loading datasets/lindsay/books.csv...
Loaded X books

⚠️  No anchor books found (all_time_favorite or recent_hit).
   Please enrich some books with anchor_type in books.csv
```

**This is expected on first import** - you haven't enriched anchor books yet.

### Expected Behavior (With Anchors)

**If anchor books exist:**
```
Loading datasets/lindsay/books.csv...
Loaded X books

================================================================================
📖 Recommendations (5 books)
================================================================================

1. [Title]
   by [Author]
   Tags: tag1|tag2|tag3
   ISBN13: [isbn13]
   Score: 0.85
   Why: Matches positive tags: fantasy, urban-fantasy, Matches positive tone: dark

2. [Title]
   ...
```

### ⚠️ Stop and Report If:
- Script crashes (should handle missing anchors gracefully)
- Recommendations include books with `read_status` = `read` or `dnf` (should be excluded)
- Tags/genres are not parsed correctly (should split on `|`)

---

## Step 6: If Any Step Fails

### Reporting Template

**If a step fails, report:**

1. **Which step failed:**
   - Step 1: Goodreads ingestion
   - Step 2: Smoke-check canonical output
   - Step 3: Merge and dedupe
   - Step 4: Validation
   - Step 5: Recommendation sanity test

2. **The error/traceback:**
   ```
   [Paste full error message and traceback]
   ```

3. **The minimal corrective change:**
   - What needs to be fixed
   - Which file/function needs updating
   - Expected vs actual behavior

### Do NOT:
- ❌ Auto-fix without user approval
- ❌ Guess at root cause
- ❌ Modify data files directly
- ❌ Skip validation steps

### Do:
- ✅ Report exact error message
- ✅ Identify which script/function failed
- ✅ Suggest minimal fix
- ✅ Wait for user approval before making changes

---

## Quick Reference: All Commands

```bash
# 1. Pre-flight check
ls -la datasets/lindsay/sources/goodreads_export.csv

# 2. Ingest Goodreads
python scripts/ingest_goodreads.py --dataset datasets/lindsay

# 3. Smoke-check (manual inspection)
head -1 datasets/lindsay/sources/goodreads_canonical.csv
python -c "import csv; from collections import Counter; p='datasets/lindsay/sources/goodreads_canonical.csv'; c=Counter(); f=open(p, newline='', encoding='utf-8'); r=csv.DictReader(f); [c.update([(row.get('read_status') or '').strip()]) for row in r]; print(c)"
python -c "import csv; p='datasets/lindsay/sources/goodreads_canonical.csv'; f=open(p, newline='', encoding='utf-8'); r=csv.DictReader(f); vals=set((row.get('genres') or '').strip() for row in r); print(vals)"
python -c "import csv, itertools, re; p='datasets/lindsay/sources/goodreads_canonical.csv'; f=open(p, newline='', encoding='utf-8'); r=csv.DictReader(f); tags=[(row.get('tags') or '').strip() for row in itertools.islice(r, 200)]; bad=[t for t in tags if t and (',' in t or re.search(r'[A-Z]', t))]; sample=[t for t in tags if t][:10]; print('sample tags:', sample); print('bad tags examples:', bad[:10])"

# 4. Merge and dedupe
python scripts/merge_and_dedupe.py --dataset datasets/lindsay

# 5. Validate
python scripts/validate_books_csv.py --dataset datasets/lindsay

# 6. Test recommendations
python scripts/recommend.py --dataset datasets/lindsay --query "urban fantasy series" --limit 5
```

---

## Success Criteria

✅ **All steps pass if:**
1. Ingestion produces canonical CSV with correct schema
2. Merge creates/updates `books.csv` without errors
3. Validation reports only expected warnings (no errors)
4. Recommendations handle missing anchors gracefully
5. All paths resolve correctly via `--dataset datasets/lindsay`
6. Pipe-delimited fields (`tags`, `formats`, `sources`) are correctly formatted
7. Protected fields are preserved
8. `work_id` is generated only for new rows

