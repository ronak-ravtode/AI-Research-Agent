# Task 25: Run All Tests - Report

## Status: DONE

## Summary

Ran the complete test suite. Initial collection error due to missing `sse-starlette` module was resolved by installing the package. After fix, all **74 tests passed**.

## Test Results

- **Total tests:** 74
- **Passed:** 74
- **Failed:** 0
- **Errors:** 0
- **Warnings:** 25 (deprecation warnings for `datetime.utcnow()` and unawaited coroutines in mocks — non-blocking)

## Fix Applied

- Installed missing `sse-starlette` package (required by `app.api.research` module)

## Test Files Covered

| Test File | Tests |
|-----------|-------|
| test_analyst.py | 4 |
| test_api.py | 2 |
| test_citations.py | 2 |
| test_confidence.py | 3 |
| test_config.py | 2 |
| test_conflict_detector.py | 3 |
| test_extractor.py | 4 |
| test_firecrawl.py | 2 |
| test_graph.py | 2 |
| test_integration.py | 20 |
| test_llm.py | 2 |
| test_logging.py | 2 |
| test_memory.py | 1 |
| test_models.py | 2 |
| test_planner.py | 1 |
| test_research_service.py | 2 |
| test_researcher.py | 1 |
| test_schemas.py | 3 |
| test_source_quality.py | 5 |
| test_tavily.py | 2 |
| test_utils.py | 5 |
| test_verifier.py | 1 |
| test_writer.py | 3 |
| **Total** | **74** |

## Warnings (Non-blocking)

1. **DeprecationWarning** — `datetime.utcnow()` used in `database/models.py` and `core/logging.py`. Should migrate to `datetime.now(datetime.UTC)`.
2. **RuntimeWarning** — Unawaited coroutines in `test_research_service.py` mock setup. Non-impacting for test correctness.
3. **RequestsDependencyWarning** — urllib3/chardet version mismatch. Non-impacting.

## Conclusion

All tests pass. The backend test suite is fully functional with 74 tests across 23 test files.
