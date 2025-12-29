# Agents Guide: Books CSV Builder + Recommender

This document is for AI assistants working with this project. It provides essential context, conventions, and workflows.

## Project Overview

This is a **books management system** that:
- Merges book data from multiple sources (Goodreads, Kindle, physical shelves)
- Maintains a canonical `books.csv` as the single source of truth
- Preserves manual user annotations (ratings, notes, preferences)
- Generates book recommendations based on enriched "anchor" books

**Core Philosophy**: The CSV is human-editable and safe. Manual fields are NEVER overwritten.

**Prime Directive**: Never overwrite manual/protected fields.

**For detailed project background, goals, and design rationale, see:** [`docs/PROJECT_BACKGROUND.md`](./docs/PROJECT_BACKGROUND.md)

## Project Structure

```
books-project/
├── datasets/                    # User datasets (dataset-per-user)
│   └── default/                # Default dataset
│       ├── sources/            # Input data
│       ├── books.csv          # Canonical output (edit this!)
│       └── reports/           # Validation and duplicate reports
├── api/                        # API layer (FastAPI server)
│   ├── server.py              # Main API server
│   ├── cache.py               # CSV caching
│   ├── filters.py             # Filtering/search logic
│   ├── recommendations.py    # Recommendation API wrapper
│   └── README.md              # API documentation
├── scripts/
│   ├── merge_and_dedupe.py      # Main pipeline (ingest → merge → dedupe)
│   ├── validate_books_csv.py    # Data quality validation
│   ├── find_duplicates.py       # Duplicate detection
│   ├── recommendations_stub.py  # Generate recommendation prompts
│   ├── recommend.py             # Simple recommendation engine
│   ├── ingest_goodreads.py      # Goodreads format converter
│   └── ingest_kindle.py         # Kindle format converter
├── tests/                       # Test suite
│   ├── fixtures/                # Test data fixtures
│   ├── test_csv_utils.py        # CSV utilities tests
│   ├── test_normalization.py    # Normalization tests
│   ├── test_deduplication.py    # Deduplication tests
│   ├── test_work_id.py          # Work ID tests
│   └── test_golden_file.py      # End-to-end tests
├── utils/
│   ├── csv_utils.py             # Safe CSV I/O (preserves manual fields)
│   ├── deduplication.py         # Matching logic (strict fuzzy matching)
│   ├── normalization.py         # Title/author/identifier normalization
│   └── work_id.py               # Stable ID generation
├── docs/                        # Documentation
│   ├── DESIGN.md                # Complete schema specification
│   ├── API_DESIGN.md            # API design proposal
│   └── PROJECT_BACKGROUND.md    # Project background and rationale
└── agents.md                    # This file
```

## Critical Rules

### 1. Protected Fields (NEVER Overwrite)
These fields are **protected** and should NEVER be overwritten once manually set:
- `work_id` - Stable identifier
- `rating`, `reread`, `reread_count`
- `dnf`, `dnf_reason`
- `pacing_rating`, `tone`, `vibe`
- `what_i_wanted`, `did_it_deliver`
- `favorite_elements`, `pet_peeves`, `notes`
- `anchor_type`, `would_recommend`
- `read_status`, `date_read` (if manually set)

**Implementation**: See `utils/csv_utils.py` → `PROTECTED_FIELDS` and `safe_merge()`

### 2. Schema Stability
- **DO NOT** remove or rename existing fields
- **DO NOT** change field order without good reason
- **DO** add new fields at the end if needed
- **DO** maintain backward compatibility

Current schema (37 fields):
```
work_id, isbn13, asin, title, author, publication_year, publisher,
language, pages, genres, description, formats, physical_owned,
kindle_owned, audiobook_owned, goodreads_id, goodreads_url,
sources, date_added, date_read, date_updated, read_status,
rating, reread, reread_count, dnf, dnf_reason, pacing_rating,
tone, vibe, what_i_wanted, did_it_deliver, favorite_elements,
pet_peeves, notes, anchor_type, would_recommend
```

### 3. Deduplication Rules
- **Priority**: ISBN13 > ASIN > exact title+author > fuzzy title+author
- **Fuzzy matching**: ONLY when both ISBN13 and ASIN are missing
- **Threshold**: 0.92+ similarity required for fuzzy matches
- **Philosophy**: False merges are worse than duplicates

**Implementation**: See `utils/deduplication.py` → `find_matches()`

### 4. Work ID Generation
- **Stable**: Once generated, preserved across runs
- **Priority**: ISBN13 > ASIN > hash(title+author)
- **Format**: `isbn13:XXXXXXXXXXXXX`, `asin:XXXXXXXXXX`, or `hash:XXXXXXXX`
- **Protected**: Never overwrite existing work_id

**Implementation**: See `utils/work_id.py` → `generate_work_id()`

## Common Workflows

### Adding New Source Data
1. User places file in `sources/` (e.g., `goodreads_export.csv`)
2. Run: `python scripts/merge_and_dedupe.py`
3. Script will:
   - Load existing `books.csv` (preserves manual fields)
   - Ingest new source data
   - Deduplicate and merge
   - Write updated `books.csv`
4. User can then manually enrich anchor books

### Validating Data
```bash
python scripts/validate_books_csv.py
```
- Checks for duplicate work_ids, ISBNs, ASINs
- Validates required fields, ratings, enums
- Reports errors/warnings (does NOT auto-fix)

### Finding Duplicates
```bash
python scripts/find_duplicates.py
```
- Scans entire CSV for possible duplicates
- Uses fuzzy matching with high thresholds
- Reports matches for manual review

### Generating Recommendations
```bash
# Generate structured prompt
python scripts/recommendations_stub.py --format markdown > prompt.md

# Or use simple recommendation engine
python scripts/recommend.py -n 12
```

## Python Best Practices

### Project Philosophy

This project is a data pipeline that produces a canonical `books.csv`. The CSV is the source of truth and is human-edited. Our job is to ingest, dedupe, merge, and validate without destroying user annotations.

**Prime Directive**: Never overwrite manual/protected fields.

### Code Style & Structure Rules

#### File Size and Module Discipline
- **Max file size**: 300 lines per Python file (excluding comments/docstrings)
- If a script grows beyond this, split into:
  - `utils/` modules for reusable logic
  - `scripts/` as thin CLI wrappers
- No "god scripts." `merge_and_dedupe.py` must orchestrate, not contain everything

#### Clear Separation of Concerns
- **`scripts/`** = CLI entry points only (argparse, printing summaries, calling library functions)
- **`utils/`** = pure functions and reusable logic (normalization, matching, merging, IO)
- Avoid circular imports. Prefer simple dependency direction:
  ```
  scripts → utils → standard library
  ```

#### Determinism
Pipeline runs must be deterministic:
- Stable ordering
- Stable IDs
- Stable output formatting
- Randomness is not allowed unless explicitly seeded and justified

### CSV Handling Rules (Critical)

#### CSV is Sacred
Treat `books.csv` as a user-owned artifact:
- Preserve column order
- Preserve manual edits
- Preserve work_id stability
- Never auto-delete rows
- Never auto-merge "uncertain matches"

#### Protected/Manual Fields
- Protected fields must never be overwritten once populated (unless user explicitly requests)
- If a protected field exists in `books.csv`, new ingestion data must not replace it
- If protected field is empty, it can be filled

#### Always Preserve Raw Inputs
- Raw source files in `sources/` must be treated as immutable inputs
- Never modify raw exports; normalize in-memory or via intermediate outputs only

#### Delimiters & Quoting
- Use the CSV utilities (no ad-hoc CSV writing)
- Quote correctly
- For multi-valued fields (genres, formats, sources), use one delimiter consistently (recommend `|`)

### Dedupe and Merge Rules

#### Matching Precedence
1. `isbn13`
2. `asin`
3. Strict title+author match
4. Bounded fuzzy (only as last resort)

#### False Merges are Worse than Duplicates
- If confidence is below threshold:
  - Do not merge
  - Emit a "possible duplicates" report

#### Merge Strategy
- Prefer keeping two records separate over collapsing incorrectly
- Metadata fields may be filled only if missing
- Union list-like fields (formats, sources)
- Never downgrade information (don't replace a populated field with blank)

### Validation Requirements

Any change to ingestion/merge logic must include running (or updating) validation.

Validation should check:
- Duplicate `work_id`
- Duplicate `isbn13` / `asin`
- Missing required fields (title, author)
- Invalid enums (`read_status`, `anchor_type`)
- Invalid numeric fields (rating, reread_count)
- Date formats

**Validation scripts should report issues, not auto-fix them.**

### Logging and Reporting

Print concise, human-readable summaries:
- Number of rows ingested
- Number of merges performed
- Number of new rows created
- Number of ambiguous matches flagged

Write "possible duplicates" output to a file for manual review (CSV or JSON).

### Testing Expectations (Lightweight)

We are not building a huge test suite, but we require:
- Unit tests for normalization and dedupe edge cases, OR
- Golden-file tests for small sample CSV inputs

At minimum:
- Add a tiny fixture set under `tests/fixtures/` and a sanity script

### Anti-patterns (Do Not Do These)

- ❌ No "smart" auto-fixing user data
- ❌ No rewriting `books.csv` formatting beyond what's necessary
- ❌ No adding dependencies unless clearly justified (standard library preferred)
- ❌ No speculative architecture (no DB, no ORM, no embeddings yet)
- ❌ No silent behavior changes: update docs if behavior changes

### When in Doubt

Ask the user or emit a report. Do not guess.

## Commit Discipline (Required)

This project evolves via small, intentional commits. Because `books.csv` is user-owned and manually edited, careless commits can permanently damage data or trust.

### Commit Size & Scope

- **One concern per commit**
- Ingestion logic changes
- Schema changes
- Validation changes
- Recommendation logic changes

**Should never be mixed in a single commit.**

- Avoid "cleanup + refactor + feature" commits

### Schema Changes (High Friction, Intentional Only)

Any change to the `books.csv` schema must include:
- An update to `docs/DESIGN.md`
- A note in `docs/CHANGES_SUMMARY.md` describing:
  - What changed
  - Why it changed
  - Whether it is backward compatible

**Rules:**
- Do not remove or rename columns casually
- Prefer adding columns over modifying existing ones
- Never silently change semantics of a column

### Data Safety Rules

Commits must never:
- Rewrite user notes
- Reorder CSV columns unexpectedly
- Change delimiters without documentation

**Any change that affects merge behavior must be explicitly called out in the commit message.**

### Commit Message Conventions

Use clear, descriptive commit messages:

**Good:**
```
Add validation for duplicate work_id and ISBN
Fix Goodreads ingestion: read_status from Exclusive Shelf only
Add bounded fuzzy matching with duplicate report output
```

**Bad:**
```
Refactor pipeline
Fix stuff
Cleanup
```

### Before Committing Ingestion or Merge Changes

Run validation scripts and verify:
- No protected fields were overwritten
- Row counts are sane
- No unexpected mass merges occurred

**If behavior changed:**
- Update `docs/DESIGN.md`
- Add a brief note to `docs/CHANGES_SUMMARY.md`

### Version Control Expectations

- Treat `books.csv` like a data artifact, not generated junk:
  - Changes should be reviewable
  - Large diffs should be explainable
- Raw source files in `sources/` should be committed only when:
  - They are small test fixtures, OR
  - You explicitly want a snapshot for debugging
- Never commit personal data unintentionally

### When Unsure

- Stop
- Ask the user
- Or emit a report instead of mutating data

## Code Patterns

### Reading CSV Safely
```python
from utils.csv_utils import read_csv_safe
books = read_csv_safe('books.csv')
# Returns list of dicts, empty strings converted to None
```

### Writing CSV Safely
```python
from utils.csv_utils import write_csv_safe
write_csv_safe('books.csv', books, CANONICAL_FIELDS)
# Sorts by author, then title
```

### Merging Data (Preserves Protected Fields)
```python
from utils.csv_utils import safe_merge
merged = safe_merge(existing_row, new_row)
# Protected fields only update if existing is empty
```

### Normalizing Identifiers
```python
from utils.normalization import normalize_title, normalize_author, normalize_isbn13
norm_title = normalize_title("The Great Gatsby")
norm_isbn = normalize_isbn13("978-0-7432-7356-5")
```

### Finding Matches
```python
from utils.deduplication import find_matches
matches = find_matches(new_book, existing_books)
# Returns [(matched_book, confidence_score), ...]
# Sorted by confidence (highest first)
```

## What NOT to Do

### ❌ Don't Auto-Fix Validation Issues
- Validation script reports issues but doesn't fix them
- User should review and fix manually
- Exception: You can suggest fixes, but don't implement without user approval

### ❌ Don't Overwrite Protected Fields
- Even if source data has "better" values
- Even if user made a typo
- Always preserve manual annotations

### ❌ Don't Change Schema Without User Request
- Adding fields is OK (at the end)
- Removing/renaming requires explicit user request
- Breaking changes need migration plan

### ❌ Don't Use Low-Confidence Fuzzy Matching
- Threshold is 0.92+ for a reason
- False merges are worse than duplicates
- When in doubt, flag for manual review

### ❌ Don't Optimize Prematurely
- Keep code simple and readable
- Performance is not a concern yet
- Focus on correctness and maintainability

### ❌ Don't Create God Scripts
- Keep scripts under 300 lines
- Split logic into `utils/` modules
- Scripts should orchestrate, not contain everything

### ❌ Don't Modify Raw Source Files
- Treat `sources/` files as immutable
- Normalize in-memory or via intermediate outputs only

### ❌ Don't Add Unnecessary Dependencies
- Prefer standard library
- Only add dependencies if clearly justified

## Testing Recommendations

When making changes:
1. Run `validate_books_csv.py` before and after
2. Test with sample data (not user's real data)
3. Verify protected fields are preserved
4. Check deduplication doesn't create false merges
5. Ensure backward compatibility

### Testing Requirements
- Unit tests for normalization and dedupe edge cases, OR
- Golden-file tests for small sample CSV inputs
- At minimum: add fixtures under `tests/fixtures/` and a sanity script

## Key Files to Understand

1. **`utils/csv_utils.py`** - Core I/O and merge logic
   - `PROTECTED_FIELDS` - List of protected fields
   - `safe_merge()` - Merge logic that preserves manual fields
   - `read_csv_safe()` / `write_csv_safe()` - Safe CSV operations

2. **`utils/deduplication.py`** - Matching logic
   - `find_matches()` - Main matching function
   - `compute_title_similarity()` / `compute_author_similarity()` - Fuzzy matching
   - Only uses fuzzy when ISBN13/ASIN missing

3. **`scripts/merge_and_dedupe.py`** - Main pipeline
   - `normalize_row()` - Ensures all fields exist, generates work_id
   - `merge_books()` - Deduplicates and merges
   - `load_all_sources()` - Ingests from sources/

4. **`docs/DESIGN.md`** - Complete schema and rules documentation

## User Interaction Patterns

### When User Adds Source Data
1. Confirm file is in `sources/` directory
2. Run merge pipeline
3. Report what was merged/added
4. Suggest running validation

### When User Enriches Anchor Books
1. User manually edits `books.csv`
2. Next merge will preserve their changes
3. Can generate recommendations after enrichment

### When User Asks for Recommendations
1. Check if anchor books exist (`anchor_type` populated)
2. If not, suggest enriching some books first
3. Generate recommendations using anchor books
4. Explain why each book was recommended

## Future Enhancements (Deferred)

- Physical shelf OCR (deferred until Goodreads+Kindle stable)
- Performance optimizations (not needed yet)
- Advanced ML recommendations (current stub is sufficient)

## Questions to Ask User

If unclear about something:
1. **Schema changes**: "Should I add this field? Where in the schema?"
2. **Deduplication**: "These books look similar - should they be merged?"
3. **Validation**: "Found these issues - how should I handle them?"
4. **Recommendations**: "How many recommendations? Any specific criteria?"

## Summary

- **Protect manual fields** - Never overwrite user annotations
- **Stable identifiers** - Preserve work_id across runs
- **Strict matching** - Prefer false negatives over false positives
- **Simple and evolvable** - No premature optimization
- **User in control** - Report issues, don't auto-fix

This project prioritizes **correctness and user control** over automation. When in doubt, preserve user data and ask for guidance.

