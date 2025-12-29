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

**For detailed rationale behind architectural decisions and constraints, see:** [Section 15: Architectural Decisions & Rationale](#15-architectural-decisions--rationale)

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
- Lightweight read-only API to support a frontend (see section 9 for detailed plans)
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

## 9) Frontend & API Plans (future layer)

### 9.1 Overall Philosophy

**Frontend is a future layer, not something to build yet.**
- The backend (CSV + pipeline) is the source of truth
- No database, no embeddings, no heavy infra until there's a real UX need
- Everything should work per user / per dataset, privately
- The CSV remains human-editable and portable

**One-sentence summary:**
We designed a future read-only frontend and API layer that sits on top of a per-user `books.csv`, supports filtering and natural-language recommendations, and preserves data safety by keeping the CSV as the source of truth; it's fully planned but intentionally not implemented yet.

### 9.2 Architecture Choice (Dataset-Per-User)

The dataset-per-user model (see section 3.1) provides clean isolation for frontend support:

```
datasets/
  lindsay/
    sources/
    books.csv
    reports/
  user_123/
    sources/
    books.csv
    reports/
```

**Why this matters for the frontend:**
- Clean isolation between users
- Simple mental model ("your library lives here")
- Easy to scale to non-you users later
- No accidental data mixing
- Each user's data stays in their dataset

### 9.3 API Layer (Planned, Not Implemented)

A read-only API proposal has been documented (see `API_DESIGN.md` for full details).

**Key characteristics:**
- **Read-only at first** (never writes to `books.csv` directly)
- **Stateless** (each request reads fresh from `books.csv`)
- **Optional in-memory caching later** (for performance)
- **No database required** (`books.csv` remains source of truth)
- **Minimal dependencies** (FastAPI preferred when implemented)

**Proposed endpoints (example set):**
- `GET /api/books` - List books with filters (read_status, tags, tone, vibe, anchor_type), pagination, sorting
- `GET /api/books/{work_id}` - Get single book by work_id
- `GET /api/books/search?q=...` - Search by title/author/notes
- `POST /api/recommendations` - Natural-language recommendation queries
  ```json
  {
    "query": "urban fantasy series",
    "limit": 5,
    "filters": { ... }
  }
  ```
- `GET /api/filters/options` - Get available filter values
- `GET /api/stats` - Library statistics

The recommender endpoint aligns exactly with the core goal: *"Give me 3–5 books I'd like, with reasons."*

**Technology direction:**
- **FastAPI preferred** when implemented (better typing, schema validation, clean docs)
- Flask was mentioned as a minimal example, but not the end goal
- Frontend tech intentionally not decided yet (React/Svelte/etc. deferred)

### 9.4 Frontend Scope (Intentionally Minimal)

When it exists, the frontend should support:

**Core UX:**
- Browse library
- Filter by: tags, read_status, tone, vibe
- Search (title / author / notes)
- Ask natural-language recommendation queries
- See why each recommendation was suggested

**Explicit non-goals (for now):**
- ❌ No editing `books.csv` directly from the UI
- ❌ No collaborative libraries
- ❌ No global/shared recommendation model
- ❌ No "social" features

**Editing (ratings, notes, anchors) can come later via:**
- Controlled API writes, or
- A "changes overlay" file that merges back safely

### 9.5 Privacy & Multi-User Considerations

**Already baked into the architecture:**
- Each user's data stays in their dataset
- No cross-user learning by default
- Any future sharing would be explicit opt-in
- Raw uploads (Goodreads/Kindle) treated as sensitive

### 9.6 Current State

- Frontend is **documented, not built**
- API design exists as a **proposal only** (see `API_DESIGN.md`)
- Backend is **stable and ready** for a frontend whenever you choose
- **No rework required** to add it later

---

## 10) Operational workflow (current)

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

## 11) Current milestones achieved (historical record)
- Pipeline stabilized on real Goodreads data (~808 books).
- Fixed a set of "None-handling" robustness issues (strip() on None) across ingestion/merge/validate.
- Implemented dataset-per-user architecture (`--dataset` everywhere).
- Standardized pipe-delimited union logic (`tags`, `formats`, `sources`).
- Created robust smoke-check test plan that does not rely on fragile shell `cut` due to CSV quoting.
- Added helper scripts for smoke checking.
- Built future API proposal doc (read-only) for a frontend, with explicit non-goals.

---

## 12) Known limitations / intentional constraints
- No ASIN extraction from Amazon UI pages (unless future DevTools approach used).
- No external genre enrichment yet; `genres` intentionally blank.
- No UI yet; CLI-first.
- No database or embeddings; intentionally deferred.
- "Read history" is Goodreads-centric; Kindle UI read flags are secondary.

---

## 13) Next steps (recommended order)

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
9. Read-only API layer + eventual frontend (see section 9 for detailed plans).

---

## 14) "Don't lose the plot" guardrails
- Do not optimize prematurely.
- Do not build a database unless a real UX requires it.
- Do not allow auto-merging with low confidence.
- Do not overwrite manual fields.
- Keep scripts small and boring.
- Prefer incremental ingestion and human review to brittle automation.

---

## 15) Architectural Decisions & Rationale

**Purpose:** This section preserves intent, constraints, and rationale behind architectural decisions to prevent decision drift.

### 15.1 Why the canonical data store is a CSV (not a database)

**Decision:** The project uses a **single canonical CSV (`books.csv`)** as the source of truth.

**Rationale:**
CSV was chosen deliberately because it is:
- human-editable
- portable
- diffable (Git-friendly)
- resilient to tool churn
- understandable without any runtime environment

The dataset is:
- small enough to fit comfortably in memory
- infrequently mutated
- enriched incrementally, not transactionally

A database was explicitly *not* chosen to avoid:
- schema migrations
- lock-in to a specific engine
- ORM complexity
- write-path risk to user data
- premature performance optimization

**Implication:**
All tooling must treat `books.csv` as:
- authoritative
- user-owned
- stable across time

No script may assume it can "fix" or rewrite user intent.

**When to revisit:**
Only if `books.csv` grows beyond comfortable in-memory size **and** performance becomes a real UX problem.

### 15.2 Manual fields are sacred (non-negotiable)

**Decision:**
Certain fields are considered **manual / user-owned** and must never be overwritten by ingestion or merge logic unless explicitly requested.

Examples include:
- rating
- notes
- dnf / dnf_reason
- tone / vibe / pacing_rating
- what_i_wanted / did_it_deliver
- pet_peeves / favorite_elements
- anchor_type
- would_recommend

**Rationale:**
The project's value comes from *subjective preference signal*, not metadata completeness.

Overwriting these fields:
- destroys trust
- erases nuance
- and undermines the entire recommender philosophy

**Implementation consequence:**
Merge logic (`safe_merge`) must:
- prefer existing values
- only fill protected fields if currently empty
- never auto-correct or normalize subjective data

### 15.3 One row per WORK (not edition)

**Decision:**
Each row in `books.csv` represents a **conceptual work**, not a specific edition or format.

**Rationale:**
The project answers questions like:
- "Have I read this?"
- "Would I like this?"
- "What should I read next?"

It does *not* aim to answer:
- "Which ISBN did I read?"
- "Which edition do I own?"

Edition-level fidelity introduces:
- unnecessary duplication
- brittle matching logic
- and little recommendation value

**Implementation consequence:**
- Multiple formats are tracked via:
  - `formats`
  - `physical_owned` / `kindle_owned` / `audiobook_owned`
- Identity matching prioritizes:
  - ISBN13
  - ASIN
  - then title + author (strict)

### 15.4 Tags vs Genres (and why both exist)

**Decision:**
- `tags` = user-defined labels (Goodreads shelves, personal labels)
- `genres` = **reserved for future external metadata enrichment**

**Rationale:**
Goodreads "shelves" are not true genres.
They are:
- personal
- messy
- overlapping
- high-signal for taste

True genres (from OpenLibrary, Google Books, etc.) are:
- standardized
- externally defined
- useful for broader filtering

Conflating the two would require painful migration later.

**Current state:**
- `tags` populated from Goodreads
- `genres` intentionally left blank

### 15.5 Recommendation philosophy (this is not Netflix)

**Decision:**
Recommendations are:
- **query-based**
- conservative
- explainable
- driven by a small set of anchors

**Key principles:**
- Fewer, better recommendations beat long ranked lists
- "Finishable and enjoyable" > "theoretically interesting"
- Negative signal (misses) matters as much as positive
- The system should be able to explain *why* a book was suggested

**Anchor strategy:**
The user does **not** enrich all books.

Instead:
- ~10–20 `all_time_favorite`
- ~20 `recent_hit` / `recent_miss` (when available)

This avoids noise from average or forgotten reads.

**Explicit non-goals:**
- No collaborative filtering
- No global popularity bias
- No embeddings (yet)
- No opaque scoring

**When to revisit:**
Only if anchor-based recommendations plateau and additional anchors stop improving quality.

### 15.6 Kindle strategy (pragmatic by design)

**Decision:**
Kindle data is treated as:
- **inventory and recency signal**
- not authoritative read history

**Rationale:**
- Amazon does not provide a clean export
- UI shows only 25 items per page
- ASINs are not easily available in bulk
- Attempting perfection here creates brittle automation

**Consequence:**
- Partial Kindle ingestion is acceptable
- Kindle rows may lack ASIN
- Deduplication relies on strict title + author matching
- Possible duplicates are reported, not auto-merged

Goodreads remains the authoritative source for:
- read_status
- ratings
- rereads

**When to revisit:**
Only if Amazon provides a stable export or a reliable API becomes available.

### 15.7 Dataset-per-user architecture (Option A)

**Decision:**
Each user has an isolated dataset folder:

```
datasets/<name>/
  sources/
  books.csv
  reports/
```

**Rationale:**
- Privacy by default
- No accidental data mixing
- Simple mental model
- Easy path to multi-user support later

**Implication:**
All scripts must:
- accept `--dataset`
- avoid global state
- treat dataset boundaries as hard isolation lines

### 15.8 Explicit non-goals (for now)

The following were explicitly decided *against*:

- No database
- No ORM
- No embeddings or vector search
- No auto-merging at low confidence
- No frontend write access to canonical data
- No social or shared libraries
- No attempt at perfect Kindle export
- No requirement to enrich every book

These are not "missing features."  
They are **deliberate exclusions**.

### 15.9 When to revisit these decisions

Revisiting decisions is allowed **only when real conditions change**.

**CSV → database:**
Revisit only if:
- `books.csv` grows beyond comfortable in-memory size **and**
- performance becomes a real UX problem

**Rule-based recommender → embeddings:**
Revisit only if:
- anchor-based recommendations plateau
- additional anchors stop improving quality

**Read-only frontend → write support:**
Revisit only if:
- manual CSV editing becomes a usability bottleneck
- and safety guarantees can be preserved (e.g., patch overlays)

**Kindle automation:**
Revisit only if:
- Amazon provides a stable export
- or a reliable API becomes available

### 15.10 "Don't lose the plot" reminders

- Boring, correct systems beat clever ones
- False negatives > false positives
- Human review beats brittle automation
- The CSV belongs to the user, not the code
- Stop when it's "good enough to be useful"

If a future change undermines any of the above, it is probably the wrong change.

---

## 16) Operational Assumptions & Guardrails

**Purpose:** This section captures "operator knowledge" and implicit assumptions that prevent well-intentioned changes from undermining the system's design.

### 16.1 System Hardening on Real Data

**Operational Reality:**
The pipeline has been exercised on:
- ~808 Goodreads rows
- Messy, real-world CSVs with edge cases
- Multiple real bugs were found and fixed:
  - None vs empty strings
  - `.strip()` failures on None values
  - CSV quoting edge cases
  - Validation edge cases

**Implication:**
- Validation passing means something now
- Defensive coding patterns (e.g., `(value or '').strip()`) are intentional and should not be removed
- The system has been hardened against real Goodreads and Kindle data

**Guardrail:**
Do not "simplify" defensive code without understanding why it exists.

### 16.2 Human-in-the-Loop Is a Feature, Not a Failure

**Philosophical Choice:**
The system is explicitly designed to:
- Surface ambiguity
- Stop and ask a human
- Require human judgment for subjective decisions

**Examples:**
- `possible_duplicates.csv` reports for manual review
- Conservative merge thresholds (0.92+ for auto-merge)
- No auto-fix in validation scripts
- Explicit counts and verbose merge logs

**Guardrail:**
Any step that requires taste judgment, identity ambiguity, or subjective resolution must surface data for human review rather than guessing.

**Why this matters:**
This is a philosophical choice that might otherwise be optimized away in favor of automation. It is intentional.

### 16.3 CSV Semantics: Empty ≈ None

**Design Decision:**
In CSV context:
- Empty string == missing == None
- Validation and merge logic treat these equivalently
- This is intentional and correct

**Implication:**
- Validators accept blanks
- Merge logic handles empty strings as missing data
- No need to "normalize" empties into literal "None" strings

**Guardrail:**
Do not try to distinguish between empty strings and None in CSV processing. They are semantically equivalent.

### 16.4 Performance Expectations Are Modest by Design

**Scale Assumptions:**
- Expected scale: low thousands of rows, not millions
- Latency tolerance: seconds, not milliseconds
- Frequency: occasional batch runs, not continuous ingestion

**Implication:**
- Simplicity > throughput
- No need for caching, threading, or complexity "just in case"
- In-memory processing is sufficient

**Guardrail:**
Do not add performance optimizations (caching, threading, async) unless there is a real performance problem at the expected scale.

### 16.5 CLI Is the Primary UX (for now)

**Design Intent:**
CLI is not a "missing" UI — it is intentionally the primary interface.

**CLI Output Characteristics:**
- Readable and narratable
- Confidence-building
- Verbose merge logs with explicit counts
- Friendly status messages

**Implication:**
- Scripts printing summaries is a UX decision, not noise
- Output should be human-friendly, not machine-optimized

**Guardrail:**
Do not remove or minimize CLI output in favor of "cleaner" code. The output is part of the user experience.

### 16.6 Recommender Output Is Advisory, Not Prescriptive

**Design Philosophy:**
The recommender is designed to:
- Suggest, not decide
- Provide advisory outputs for human decision-making
- Never mutate state based on recommendations

**Implication:**
- Recommendations are outputs, not actions
- The system never auto-marks books as read, adds to lists, or takes actions based on recommendations

**Guardrail:**
The recommender must remain read-only. It should never mutate `books.csv` or any other state.

### 16.7 Anchor Fatigue Is Expected

**Operational Reality:**
Users may not remember:
- Recent hits
- Recent misses
- Specific details about books

**Design Response:**
- This is normal and expected
- Anchors can be added reactively after seeing recommendations
- The system does not require complete anchor coverage to be useful

**Guardrail:**
Do not assume that missing anchors indicate a problem. Partial anchor coverage is acceptable and expected.

### 16.8 Partial Data Is First-Class

**Design Philosophy:**
The system is designed for:
- Partial Kindle coverage
- Partial ASIN presence
- Partial shelf ingestion
- Missing metadata fields

**Implication:**
- Partial ≠ broken
- The system gracefully handles missing data
- Deduplication works with partial identifiers
- Validation allows for missing optional fields

**Guardrail:**
Do not treat partial data as errors. The system is designed to work with incomplete information.

---

## Appendix: Glossary
- **Canonical CSV**: the authoritative dataset (`books.csv`)
- **Protected fields**: user-edited preference fields that must not be overwritten
- **Anchor books**: small curated subset used to drive recommendations
- **Tags**: user shelves/labels; freeform; not authoritative genres
- **Genres**: authoritative genres from external enrichment; future
- **Dataset-per-user**: each user has isolated folder state for sources/books/reports

