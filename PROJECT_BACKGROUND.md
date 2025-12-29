# Books Project Background Doc
**Project codename:** Books CSV Builder + Query Recommender  
**Owner:** Lindsay  
**Last updated:** Dec 26, 2025  
**Status:** ✅ Pipeline stable with real data; Kindle ingestion in-progress; physical shelf ingestion planned.

---

## 0) Why this exists

This project started as a "book advent calendar" inspiration (a human read a paragraph about reading preferences and picked 12 books). The real goal is broader:

- Maintain a **single, canonical, portable record** of:
  - books read
  - books owned/accessible (Kindle, physical, etc.)
  - subjective preference data (ratings, vibe, tone, DNFs, notes)
- Use that record to power **interactive recommendation queries**, e.g.:
  - "I want an urban fantasy series to get into."
  - "Give me 3–5 suggestions I'm likely to finish and enjoy, with reasons."

The CSV is the source of truth. Everything else is tooling around it.

---

## 1) Product goal (what "done" looks like)

### v1 (current)
- ✅ Ingest Goodreads export into canonical form.
- ✅ Merge/dedupe into `books.csv` with strong data-safety guarantees.
- ✅ Validate data quality with a dedicated validation script.
- ✅ Query-based recommender stub that:
  - returns 3–5 suggestions
  - avoids read/dnf items
  - uses "anchor books" to steer taste
- ✅ Dataset-per-user folder structure (Option A).

### v2 (near future)
- Kindle dataset ingestion:
  - add new books that exist in Kindle but not Goodreads
  - dedupe against Goodreads where overlaps exist
- Improve rec quality using:
  - more anchors (favorites + recent hits/misses)
  - tags and negative constraints
- Add "possible duplicates" manual workflow loop

### v3+ (far future)
- Physical shelf inventory ingestion (photos → OCR → title/author extraction)
- External metadata enrichment for **true genres** and richer metadata:
  - fill `genres` from authoritative sources (OpenLibrary/Google Books/etc.)
  - keep `tags` as user-defined shelves/labels
- Lightweight read-only API to support a frontend
- Multi-user "bring your own exports" model (dataset-per-user) with isolation/privacy.

---

## 2) Key design principles (non-negotiables)

### 2.1 CSV-first, portable, durable
- The canonical artifact is a single file: **`books.csv`**
- It must remain:
  - human-editable
  - stable across time
  - easy to back up (Git, Drive, etc.)
  - tool-agnostic (not tied to a DB)

### 2.2 Manual edits are sacred
Manual preference fields must never be overwritten by ingestion/merge runs unless explicitly requested.

Examples of "sacred" data:
- rating
- notes
- dnf / dnf_reason
- tone / vibe / pacing_rating
- what_i_wanted / did_it_deliver
- pet_peeves / favorite_elements
- anchor_type
- would_recommend

### 2.3 Determinism > cleverness
- Output ordering deterministic (sorted by author/title).
- Union operations deterministic (sorted pipe-delimited output).
- Matching prefers false negatives over false positives.
- "Maybe duplicates" are reported, not merged automatically.

### 2.4 One row per WORK (not edition)
Unless explicitly changed later:
- represent the conceptual work ("Storm Front") as one row, even if formats/editions differ.
- multiple formats are tracked via owned flags + formats list.
- edition-level fidelity is not a requirement.

---

## 3) Repository architecture

### 3.1 Dataset-per-user model (Option A)
Each dataset is self-contained and isolated. No shared global state.

```
datasets/
  lindsay/
    sources/
      goodreads_export.csv
      goodreads_canonical.csv
      kindle_library.csv
      kindle_canonical.csv
      …
    books.csv
    reports/
      possible_duplicates.csv
      validation_report.txt (optional)
```

Scripts accept `--dataset`:
- default `datasets/default`
- user dataset example `--dataset datasets/lindsay`

### 3.2 Code structure
- `scripts/` = CLI entrypoints (thin wrappers)
- `utils/` = reusable pure logic (normalization, dedupe, CSV I/O, work_id generation)
- `reports/` = machine outputs meant for human review

---

## 4) Canonical schema

### 4.1 Canonical header (current)
```csv
work_id,isbn13,asin,title,author,publication_year,publisher,language,pages,
genres,tags,description,formats,physical_owned,kindle_owned,audiobook_owned,
goodreads_id,goodreads_url,sources,date_added,date_read,date_updated,
read_status,rating,reread,reread_count,dnf,dnf_reason,pacing_rating,tone,
vibe,what_i_wanted,did_it_deliver,favorite_elements,pet_peeves,notes,
anchor_type,would_recommend
```

### 4.2 Field semantics

**Identity & linking**
- `work_id`: stable internal identifier; required for reliable referencing in UI/API contexts.
- `isbn13`: best external ID; often missing in Goodreads/Kindle.
- `asin`: Kindle/Amazon identifier; often missing from export UI.
- `title`, `author`: normalized strings used for fallback matching.

**Bibliographic metadata (mostly auto)**
- `publication_year`, `publisher`, `language`, `pages`
- `description` (future external enrichment)
- `genres` = true genres from external enrichment (future)
- `tags` = user labels/shelves; freeform; pipe-delimited

**Formats & ownership**
- `formats`: pipe-delimited union of known formats (e.g., `kindle|physical`)
- `physical_owned`, `kindle_owned`, `audiobook_owned`: 0/1 flags

**Provenance**
- `goodreads_id`, `goodreads_url`
- `sources`: pipe-delimited union (`goodreads|kindle|shelves`)
- strictly provenance, not preference

**Dates**
- `date_added`: when first introduced to canonical system
- `date_updated`: last pipeline touch
- `date_read`: retained for compatibility but not used; typically blank

**Status + preference**
- `read_status`: `read` | `reading` | `want_to_read` | `dnf` | (optional others)
- `rating`: user rating (1–5; optionally halves)
- `reread`: 0/1
- `reread_count`: integer >= 0
- `dnf`: 0/1
- `dnf_reason`: free text
- `pacing_rating`: 1–5
- `tone`, `vibe`: free text
- `what_i_wanted`: free text
- `did_it_deliver`: 0/1
- `favorite_elements`, `pet_peeves`: free text
- `notes`: free text (manual, sacred)
- `anchor_type`: `all_time_favorite` | `recent_hit` | `recent_miss` | `dnf` | empty
- `would_recommend`: 0/1

---

## 5) Ingestion sources & expectations

### 5.1 Goodreads (primary read-history spine)
- Exported CSV from Goodreads "Export Library"
- Used for:
  - `read_status` (Exclusive Shelf)
  - `ratings` (with "0 = none" handling)
  - `reread_count` (Read Count)
  - `tags` (Bookshelves)
  - `physical_owned` proxy (Owned Copies)

**Important constraints**
- Goodreads export lacks descriptions and often lacks ISBN13.
- No ASIN.
- Many rows will have `isbn13=None` and `tags=None`. This is expected.

### 5.2 Kindle (inventory/recency spine; in progress)

**User strategy due to Amazon UI limitations:**
- Amazon "Manage Your Content and Devices" only shows 25 items/page.
- User exports pages as PDFs/screens and converts to CSV.

**Kindle exports may lack ASIN.**
- In that case, dedupe relies on title+author strict matching and duplicate reporting.
- Partial ingestion is acceptable; pipeline supports incremental updates.

**Fields typically captured from UI pages:**
- title
- author(s)
- acquired vs borrowed
- acquired date
- read flag (if shown)

### 5.3 Physical shelves (future)

**Goal:**
- identify physical inventory via photos
- extract title/author via OCR/vision
- mark `physical_owned=1`
- default `read_status` remains whatever Goodreads says; shelves are inventory, not reading history.

---

## 6) Merge & dedupe strategy

### 6.1 Matching priority (strict)
1. ISBN13 exact match (highest confidence)
2. ASIN exact match (high confidence)
3. normalized (title + author) match
4. bounded fuzzy match only if necessary and high threshold

### 6.2 Confidence thresholds (conservative)
- Auto-merge threshold: >= 0.92
- Possible duplicate report: 0.80–0.92
- Below 0.80: treat as distinct record

### 6.3 Merge rules (safe_merge)
- **Protected fields:**
  - never overwritten if already set
- **Safe fields:**
  - filled only if missing
- **Multi-valued pipe-delimited fields unioned deterministically:**
  - `tags`, `formats`, `sources`

### 6.4 Reporting
- Ambiguous matches go to:
  - `datasets/<name>/reports/possible_duplicates.csv`
- Human reviews possible duplicates and decides whether to merge manually.

---

## 7) Validation (quality checks)

Validation script reports:
- Duplicate `work_id`
- Duplicate `isbn13` / `asin`
- Missing required `title`/`author`
- Invalid enums (`read_status`, `anchor_type`)
- Invalid numeric fields (rating range, `reread_count` int, `dnf` 0/1)
- Pipe delimiter sanity for multi-valued fields

Validation should:
- never auto-fix
- never mutate `books.csv`
- fail loudly on structural errors

---

## 8) Recommendations: query-based (not advent calendar)

### 8.1 Query model

User intent is freeform text:
- "urban fantasy series"
- "cozy but not saccharine"
- "fast-paced sci-fi, low gore"

Recommender returns 3–5 suggestions:
- excludes already-read and DNF
- provides reasons ("why this fits")

### 8.2 Anchor strategy (selective enrichment)

User does not intend to enrich every book.

Instead:
- 10–20 `all_time_favorite` anchors
- 20-ish `recent_hit`/`recent_miss` anchors (as available)

This is a deliberate signal-to-noise strategy.

### 8.3 Scoring signals

**v1 scoring (simple):**
- tag overlap with positive anchors
- tone/vibe overlap with positive anchors (if present)
- penalties for negative anchors (`recent_miss`/`dnf`) using `pet_peeves`/`tone`/`vibe`
- query keyword boosts matching tags

No embeddings yet. No external calls. Boring and explainable.

---

## 9) Operational workflow (current)

### Goodreads ingest (working)
```bash
python3 scripts/ingest_goodreads.py --dataset datasets/lindsay
python3 scripts/merge_and_dedupe.py --dataset datasets/lindsay
python3 scripts/validate_books_csv.py --dataset datasets/lindsay
```

### Kindle ingest (planned next)
1. Append page-extracted CSV rows into:
   ```
   datasets/lindsay/sources/kindle_library.csv
   ```
2. Run:
   ```bash
   python3 scripts/ingest_kindle.py --dataset datasets/lindsay
   python3 scripts/merge_and_dedupe.py --dataset datasets/lindsay
   python3 scripts/validate_books_csv.py --dataset datasets/lindsay
   ```

---

## 10) Current milestones achieved (historical record)
- Pipeline stabilized on real Goodreads data (~808 books).
- Fixed a set of "None-handling" robustness issues (strip() on None) across ingestion/merge/validate.
- Implemented dataset-per-user architecture (`--dataset` everywhere).
- Standardized pipe-delimited union logic (`tags`, `formats`, `sources`).
- Created robust smoke-check test plan that does not rely on fragile shell `cut` due to CSV quoting.
- Added helper scripts for smoke checking.
- Built future API proposal doc (read-only) for a frontend, with explicit non-goals.

---

## 11) Known limitations / intentional constraints
- No ASIN extraction from Amazon UI pages (unless future DevTools approach used).
- No external genre enrichment yet; `genres` intentionally blank.
- No UI yet; CLI-first.
- No database or embeddings; intentionally deferred.
- "Read history" is Goodreads-centric; Kindle UI read flags are secondary.

---

## 12) Next steps (recommended order)

### Short term
1. Continue Kindle page extraction → append to kindle CSV.
2. Implement/confirm `ingest_kindle.py` mapping fields into canonical.
3. Merge Kindle canonical into `books.csv`; review duplicates report.
4. Mark a small set of anchors (favorites already started).
5. Run query recommender and iteratively refine anchors.

### Medium term
6. Add external metadata enrichment script to populate `genres`, `description`, etc.
7. Improve recommender scoring using enriched genres and stronger negative constraints.

### Long term
8. Shelf photo OCR ingestion for physical inventory.
9. Read-only API layer + eventual frontend.

---

## 13) "Don't lose the plot" guardrails
- Do not optimize prematurely.
- Do not build a database unless a real UX requires it.
- Do not allow auto-merging with low confidence.
- Do not overwrite manual fields.
- Keep scripts small and boring.
- Prefer incremental ingestion and human review to brittle automation.

---

## Appendix: Glossary
- **Canonical CSV**: the authoritative dataset (`books.csv`)
- **Protected fields**: user-edited preference fields that must not be overwritten
- **Anchor books**: small curated subset used to drive recommendations
- **Tags**: user shelves/labels; freeform; not authoritative genres
- **Genres**: authoritative genres from external enrichment; future
- **Dataset-per-user**: each user has isolated folder state for sources/books/reports

