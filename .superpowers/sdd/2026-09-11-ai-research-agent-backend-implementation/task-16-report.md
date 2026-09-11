# Task 16: Citation Engine

## Status
DONE

## Files Created
- `backend/app/services/citations.py` - Citation mapping utility function
- `backend/tests/test_citations.py` - Tests for citation mapping

## Implementation
- Implemented `map_citations()` function that:
  - Maps claims to their sources
  - Deduplicates claims by text
  - Resolves source IDs via URL lookup
  - Assigns sequential citation numbers
  - Returns citations with unique IDs, claim text, source ID, source URL, and citation number

## Tests
- `test_map_citations_basic`: Verifies basic citation mapping with two claims
- `test_map_citations_deduplicates`: Verifies duplicate claim text is ignored

## Commit
- SHA: 4c4a293
- Message: feat: citation engine for mapping claims to sources

## Test Summary
2 tests passed, 0 failed
