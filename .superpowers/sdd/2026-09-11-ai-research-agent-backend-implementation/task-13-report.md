# Task 13: Confidence Scoring Service

## Status: DONE

## Files Created
- `backend/app/services/confidence.py` - Pure utility function `calculate_confidence()`
- `backend/tests/test_confidence.py` - Unit tests (3 tests)

## Implementation Details
- Function calculates overall confidence score based on verified claims
- Formula: `supported_ratio * 0.9 + partial_ratio * 0.5 - contradicted_penalty * 0.3`
- Returns overall score (0.0-1.0), individual claim scores, and summary statistics
- Handles empty claims list gracefully

## Test Results
- 3/3 tests passed
- Tests cover: empty claims, all supported claims, mixed claims

## Dependencies
- No dependencies - pure utility function

## Notes
- Implementation matches the plan exactly
- No external imports needed (only typing module for type hints)