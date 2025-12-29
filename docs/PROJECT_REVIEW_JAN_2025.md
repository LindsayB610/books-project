# Project Review: January 2025

**Date:** January 2025  
**Reviewer:** AI Assistant  
**Project:** Books CSV Builder + Recommender

---

## Current State Summary

### ✅ Completed Features

1. **Core Pipeline**
   - Goodreads ingestion (`scripts/ingest_goodreads.py`)
   - Kindle ingestion (`scripts/ingest_kindle.py`)
   - Merge and deduplication (`scripts/merge_and_dedupe.py`)
   - Validation (`scripts/validate_books_csv.py`)
   - Duplicate detection (`scripts/find_duplicates.py`)

2. **Recommendation Engine**
   - Query-based recommendations (`scripts/recommend.py`)
   - Recommendation prompt generation (`scripts/recommendations_stub.py`)
   - Anchor-based scoring

3. **API Layer** (Fully Implemented)
   - FastAPI server (`api/server.py`)
   - All endpoints from `API_DESIGN.md` implemented
   - Caching layer (`api/cache.py`)
   - Filtering and search (`api/filters.py`)
   - Recommendations endpoint (`api/recommendations.py`)
   - API tests (`api/test_api.py`)

4. **Test Suite**
   - Core utility tests (csv_utils, normalization, deduplication, work_id)
   - Golden file tests
   - Minimal coverage focused on data safety

5. **Architecture**
   - Dataset-per-user isolation
   - Protected fields preservation
   - Stable work_id generation
   - Conservative deduplication

### ⏸️ Deferred Features

1. **Physical Shelf OCR** - Explicitly deferred until core pipeline is stable

### 🔄 Planned but Not Implemented

1. **External Metadata Enrichment** - Mentioned as "medium term" priority
   - Populate `genres` field from authoritative sources (OpenLibrary/Google Books)
   - Populate `description` field
   - Currently `genres` is intentionally left empty (reserved for this)
   - Would improve recommendation quality

---

## Recommended Next Steps

Based on the planning documents and current state, here are the best candidates for independent work:

### Priority 1: External Metadata Enrichment Script

**Why this makes sense:**
- Explicitly planned in `PROJECT_BACKGROUND.md` (medium term priority #6)
- Can be built completely independently
- Adds significant value (better recommendations, richer data)
- Respects project philosophy (only fills empty fields, doesn't overwrite protected data)
- Uses free APIs (OpenLibrary, Google Books) - no API keys required for basic use
- Incremental enrichment aligns with project goals

**What it should do:**
1. Read `books.csv` for a dataset
2. For books with ISBN13 or ISBN10, query OpenLibrary/Google Books APIs
3. Fill empty `genres` and `description` fields (never overwrite existing)
4. Respect rate limits (batch processing, optional caching)
5. Support `--dataset` argument
6. Report what was enriched (dry-run mode)

**Design principles:**
- **Safe**: Only fills empty fields (doesn't overwrite)
- **Respectful**: Rate limits, optional delays between requests
- **Transparent**: Reports what was found/added
- **Incremental**: Can be run multiple times (idempotent)
- **Optional**: User can skip if they don't want external data

**Implementation approach:**
- New script: `scripts/enrich_metadata.py`
- Use OpenLibrary API (free, no API key required)
- Fallback to Google Books API (free, no API key required)
- Match by ISBN13/ISBN10
- Extract genres (convert to pipe-delimited format)
- Extract description
- Use `safe_merge()` pattern to only fill empty fields

**Example usage:**
```bash
# Dry run (show what would be enriched)
python scripts/enrich_metadata.py --dataset datasets/lindsay --dry-run

# Actually enrich
python scripts/enrich_metadata.py --dataset datasets/lindsay

# Enrich only genres (skip descriptions)
python scripts/enrich_metadata.py --dataset datasets/lindsay --fields genres

# Limit rate (delay between requests in seconds)
python scripts/enrich_metadata.py --dataset datasets/lindsay --rate-limit 1
```

---

### Priority 2: Code Quality & Documentation Improvements

**Why this makes sense:**
- Independent work that improves maintainability
- No user input required
- Fits project philosophy of incremental improvement

**Potential improvements:**
1. **API dataset configuration** - Currently hardcoded to `datasets/default`, could support env var or config
2. **Better error messages** - More descriptive errors in validation/ingestion
3. **Script help text** - Ensure all scripts have clear `--help` output
4. **Documentation** - Ensure all scripts are documented in main README

---

### Priority 3: Enhanced Validation (Lower Priority)

**Why this could be useful:**
- Adds value without changing core behavior
- Can be built independently
- Helps with data quality

**Potential enhancements:**
1. **Anchor book validation** - Warn if anchor books are missing key preference data (tone, vibe, tags)
2. **Recommendation readiness check** - Validate that enough anchor books exist for recommendations
3. **Data completeness report** - Show statistics on field population

---

## What NOT to Build Right Now

### ❌ Frontend
- Requires user input/design decisions
- Should wait until API is fully tested
- Documented but intentionally not implemented yet

### ❌ Physical Shelf OCR
- Explicitly deferred
- Requires user-provided photos
- More complex, should wait

### ❌ Database Migration
- Explicitly against project philosophy
- CSV-first is a core principle
- Not needed at current scale

### ❌ Advanced ML/Embeddings
- Project philosophy favors simple, explainable recommendations
- Current anchor-based approach is sufficient
- Can revisit if recommendations plateau

---

## Conclusion

**Best Next Step: External Metadata Enrichment Script**

This is the most valuable independent work that:
- ✅ Is explicitly planned
- ✅ Can be completed independently
- ✅ Adds significant value
- ✅ Respects all project principles
- ✅ Requires no user input beyond running the script
- ✅ Uses free, public APIs

The enrichment script would:
1. Populate empty `genres` fields (currently reserved for this purpose)
2. Populate empty `description` fields
3. Improve recommendation quality
4. Make the data more complete
5. Follow safe merge patterns (only fills, never overwrites)

---

## Notes on Implementation

If building the enrichment script:
- Start with OpenLibrary API (simplest, no auth needed)
- Add Google Books as fallback
- Match by ISBN13/ISBN10 (most reliable)
- Use pipe-delimited format for genres (consistent with tags)
- Implement rate limiting (be respectful to free APIs)
- Add dry-run mode (show what would change)
- Report statistics (how many books enriched, which fields)
- Support `--dataset` argument (consistent with other scripts)
- Handle errors gracefully (network failures, missing data, etc.)
- Make it idempotent (safe to run multiple times)

