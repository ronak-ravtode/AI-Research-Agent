# Task 7: Firecrawl Extraction Tool

## Status: DONE

## Changes

### Files Created
- `backend/app/tools/firecrawl_extract.py` — FirecrawlExtract class with `extract_url` method
- `backend/tests/test_firecrawl.py` — 2 tests with mocked API calls

### Files Modified
- `backend/app/tools/__init__.py` — Added lazy `get_firecrawl_extract()` accessor

## Implementation Notes

- Lazy-initialized `FirecrawlApp` via `@property` to avoid module-level instantiation failing when `FIRECRAWL_API_KEY` is empty (prevents import-time errors in tests and dev environments)
- Test fixture patches `get_settings`, `FirecrawlApp`, and sets `_app` directly on the instance
- `extract_url` wraps `scrape_url` with markdown format params and graceful error handling
- Added `firecrawl` package dependency (`pip install firecrawl`)

## Test Results

11/11 tests pass (2 new firecrawl + 9 existing). Pre-existing import errors in `test_graph.py` and `test_llm.py` (missing `langgraph`, `groq`) are unrelated.

## Commit

`eac7fa6` feat: Firecrawl webpage extraction tool
