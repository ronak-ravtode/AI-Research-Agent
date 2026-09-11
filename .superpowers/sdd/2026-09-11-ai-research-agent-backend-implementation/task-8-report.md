# Task 8: Source Quality Scoring Service

## Status: DONE

## Files Created
- `backend/app/services/source_quality.py` — `classify_source_type` and `score_source` functions
- `backend/tests/test_source_quality.py` — 6 unit tests

## Implementation Summary
- `classify_source_type(url, domain)` categorizes URLs into academic, government, news, blog, forum, or unknown based on domain patterns
- `score_source(...)` computes a weighted reliability score (0–1) from source authority, relevance, evidence quality, and cross-source agreement
- `SOURCE_TYPE_AUTHORITY` dict maps source types to base authority scores

## Tests
All 6 tests pass:
- `test_classify_academic` — arxiv.org → "academic"
- `test_classify_government` — whitehouse.gov → "government"
- `test_classify_news` — reuters.com → "news"
- `test_classify_unknown` — random domain → "unknown"
- `test_score_source_range` — academic source with high relevance → score in [0.0, 1.0] and > 0.5
- `test_score_source_low` — forum source with low relevance → score < 0.5
