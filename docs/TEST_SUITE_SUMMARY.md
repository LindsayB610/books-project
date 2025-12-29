# Test Suite Summary

## What Was Created

A minimal test suite focused on data safety and critical logic, as specified in `agents.md`.

### Test Files

1. **`tests/test_csv_utils.py`** (Most Critical)
   - Tests for `safe_merge()` - protected fields preservation
   - Tests for `union_pipe()` - pipe-delimited field unioning
   - Tests for `is_manually_set()` - manual field detection
   - **Key test**: Protected fields should NEVER be overwritten

2. **`tests/test_normalization.py`**
   - Title normalization (punctuation, prefixes, whitespace)
   - Author normalization (format conversion)
   - ISBN13/ASIN normalization
   - Canonical ID computation

3. **`tests/test_deduplication.py`**
   - ISBN13 matching
   - ASIN matching
   - Title+author matching
   - Fuzzy matching (only when no identifiers)
   - Match confidence scoring

4. **`tests/test_work_id.py`**
   - work_id stability (same input = same output)
   - Priority order (ISBN13 > ASIN > hash)
   - Preservation of existing work_id

5. **`tests/test_golden_file.py`**
   - End-to-end tests with fixture data
   - CSV reading/writing integrity
   - Data preservation through round-trip

### Test Fixtures

- **`tests/fixtures/sample_books.csv`** - Sample books with various scenarios:
  - Books with ISBN13
  - Books with ASIN
  - Books with hash-based work_id
  - Books with protected fields set
  - Books with various read_status values

### Documentation

- **`tests/README.md`** - Test suite documentation

## Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_csv_utils.py

# Run with verbose output
pytest tests/ -v
```

## Test Coverage

### ✅ Covered (Critical Paths)

- **Data Safety**: All protected fields in `safe_merge()`
- **Normalization**: All normalization functions
- **Deduplication**: Matching logic and thresholds
- **Work ID**: Generation and stability
- **CSV I/O**: Reading and writing integrity
- **Metadata Enrichment**: Safety logic (never overwrite existing data), with mocked API calls

### ⚠️ Partially Covered

- **API Endpoints**: Basic integration test exists (`api/test_api.py`), could add more unit tests

### ❌ Not Covered (By Design)

- UI/UX behavior
- Performance/optimization
- Every possible edge case
- External API calls (real network requests - tested with mocks instead)

## Test Philosophy

This is a **minimal** test suite that focuses on:

1. **Data Safety** - Protected fields must never be overwritten (CRITICAL)
2. **Stability** - work_id and matching must be deterministic
3. **Correctness** - Core logic (merge, dedupe, normalize) must work correctly

The suite follows the project's philosophy: "We are not building a huge test suite, but we require unit tests for normalization and dedupe edge cases, OR golden-file tests for small sample CSV inputs."

## Key Test Cases

### Most Critical: Protected Fields

```python
def test_protected_field_preserved_when_existing_has_value(self):
    """Protected fields should NEVER be overwritten if existing has value."""
    existing = {'rating': '5', 'notes': 'My favorite book'}
    new = {'rating': '3', 'notes': 'Different notes'}
    merged = safe_merge(existing, new)
    
    assert merged['rating'] == '5'  # Preserved!
    assert merged['notes'] == 'My favorite book'  # Preserved!
```

This test ensures the **Prime Directive** is never violated: "Never overwrite manual/protected fields."

## Next Steps

1. **Run the tests** to verify they pass:
   ```bash
   pytest tests/
   ```

2. **Add more tests** as needed when:
   - Adding new protected fields
   - Changing merge logic
   - Adding new normalization rules

3. **Consider adding**:
   - More API endpoint tests (if building frontend)
   - Performance tests (if scale becomes an issue)
   - Integration tests for full pipeline (if needed)

## Dependencies Added

- `pytest>=7.4.0` - Test framework

No other test dependencies added (keeping it minimal).

