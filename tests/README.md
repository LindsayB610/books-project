# Test Suite

Minimal test suite focused on data safety and critical logic.

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_csv_utils.py

# Run with verbose output
pytest tests/ -v

# Run with coverage (if pytest-cov installed)
pytest tests/ --cov=utils --cov=api
```

## Test Structure

### `test_csv_utils.py`
Tests for CSV utilities, focusing on:
- `safe_merge()` - Protected fields preservation (CRITICAL)
- `union_pipe()` - Pipe-delimited field unioning
- `is_manually_set()` - Manual field detection

### `test_normalization.py`
Tests for normalization functions:
- Title normalization (punctuation, prefixes, whitespace)
- Author normalization (format conversion)
- ISBN13/ASIN normalization
- Canonical ID computation

### `test_deduplication.py`
Tests for deduplication logic:
- ISBN13 matching
- ASIN matching
- Title+author matching
- Fuzzy matching (only when no identifiers)
- Match confidence scoring

### `test_work_id.py`
Tests for work_id generation:
- Stability (same input = same output)
- Priority order (ISBN13 > ASIN > hash)
- Preservation of existing work_id

### `test_golden_file.py`
End-to-end tests with fixture data:
- CSV reading/writing integrity
- Full pipeline with sample data
- Data preservation through round-trip

## Test Fixtures

### `fixtures/sample_books.csv`
Sample books CSV with:
- Books with ISBN13
- Books with ASIN
- Books with hash-based work_id
- Books with protected fields set
- Books with various read_status values

## Philosophy

This is a **minimal** test suite focused on:
1. **Data Safety** - Protected fields must never be overwritten
2. **Stability** - work_id and matching must be deterministic
3. **Correctness** - Core logic (merge, dedupe, normalize) must work correctly

We do NOT test:
- UI/UX behavior
- Performance/optimization
- Every edge case (focus on critical paths)

## Adding New Tests

When adding new functionality:
1. Add tests for protected field preservation (if touching merge logic)
2. Add tests for normalization edge cases (if adding new normalizers)
3. Add golden-file test if changing pipeline behavior

## Test Coverage Goals

- ✅ All protected fields in `safe_merge()`
- ✅ All normalization functions
- ✅ Deduplication matching logic
- ✅ work_id generation and stability
- ⚠️ API endpoints (basic integration test exists, could add more)

