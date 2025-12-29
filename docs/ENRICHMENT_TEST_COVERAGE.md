# Metadata Enrichment Test Coverage

## Overview

Test coverage for `scripts/enrich_metadata.py` focuses on the **critical safety logic**: ensuring that existing data is never overwritten.

## Test Philosophy

Following the project's minimal test suite philosophy:
- ✅ Test **critical safety logic** (never overwrite existing data)
- ✅ Test edge cases for ISBN extraction
- ✅ Test fallback logic (Google Books)
- ✅ Use **mocked API calls** (don't test actual external API requests)

This aligns with `TEST_SUITE_SUMMARY.md` which states: "External API calls" are not covered, but we test the logic with mocks.

## Test Coverage

### ✅ Covered

1. **ISBN Extraction** (`TestExtractISBN`)
   - Valid ISBN13 extraction
   - Normalization (removes hyphens)
   - Missing ISBN handling
   - Empty ISBN handling

2. **Critical Safety Logic** (`TestEnrichBookMetadataSafety`)
   - ✅ **Never overwrite existing genres** - Most important test
   - ✅ **Never overwrite existing description** - Most important test
   - ✅ Can fill empty genres field
   - ✅ Can fill empty description field
   - ✅ Handles None values correctly
   - ✅ Skips enrichment when both fields are filled
   - ✅ Skips enrichment when ISBN is missing

3. **Google Books Fallback** (`TestEnrichBookMetadataGoogleBooks`)
   - Uses Google Books when OpenLibrary missing data
   - Doesn't call Google Books unnecessarily

4. **Error Handling** (`TestEnrichBookMetadataErrorHandling`)
   - Handles API returning None gracefully
   - Doesn't crash on API errors

### ❌ Not Covered (By Design)

- Real network requests to OpenLibrary/Google Books APIs
- API rate limiting behavior
- Description HTML cleaning edge cases
- Genre filtering edge cases
- Performance/throughput

## Key Test: Never Overwrite

The most critical tests are `test_never_overwrite_existing_genres` and `test_never_overwrite_existing_description`. These ensure the **Prime Directive** is never violated:

```python
def test_never_overwrite_existing_genres(self):
    """Never overwrite existing genres field."""
    book = {
        'genres': 'Fantasy|Fiction',  # Already set
        'description': ''  # Empty
    }
    
    # Mock API to return different genres
    with patch('scripts.enrich_metadata.fetch_openlibrary_data') as mock_fetch:
        mock_fetch.return_value = {
            'genres': 'Science Fiction|Adventure',  # Different!
            'description': 'A test description'
        }
        
        updated_book, stats = enrich_book_metadata(book, rate_limit=0)
        
        # Genres should NOT be overwritten
        assert updated_book['genres'] == 'Fantasy|Fiction'  # Preserved!
        assert stats['genres_added'] is False
```

This ensures that even if the API returns different data, existing user data is never overwritten.

## Running Tests

```bash
# Run all enrichment tests
pytest tests/test_enrichment.py -v

# Run specific test class
pytest tests/test_enrichment.py::TestEnrichBookMetadataSafety -v

# Run with coverage
pytest tests/test_enrichment.py --cov=scripts.enrich_metadata
```

## Why Mocked APIs?

The project philosophy explicitly excludes testing external API calls. Instead:
- We mock the API functions (`fetch_openlibrary_data`, `fetch_google_books_data`)
- We test the **logic** that uses API responses
- We verify that existing data is never overwritten regardless of API response

This is a pragmatic approach that:
- ✅ Tests critical safety logic
- ✅ Avoids flaky tests (no network dependency)
- ✅ Runs fast (no network delays)
- ✅ Aligns with project philosophy

## Test Statistics

- **Total Tests**: 14
- **Test Classes**: 4
- **Focus Areas**: Safety (6 tests), ISBN extraction (4 tests), Fallback (2 tests), Error handling (2 tests)

All tests pass ✅

