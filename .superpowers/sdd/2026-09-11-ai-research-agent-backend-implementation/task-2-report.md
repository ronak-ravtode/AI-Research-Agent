# Task 2: Database Models - Report

## Status: DONE

## Commit
- `4239d6b` feat: database models for research sessions, sources, evidence

## Test Summary
- 4/4 tests passing (2 new model tests + 2 existing config tests)

## Files Created
- `backend/app/database/__init__.py` - Package exports
- `backend/app/database/database.py` - Engine, session factory, Base, get_db dependency
- `backend/app/database/models.py` - All 7 models with enums, UUID PKs, relationships
- `backend/tests/test_models.py` - Model instantiation tests

## Models Implemented
1. **ResearchSession** - research_sessions table with status enum, relationships to tasks/sources/reports/logs
2. **ResearchTask** - research_tasks table with status enum, FK to session, relationship to evidence
3. **Source** - sources table with relevance_score, FK to session, relationships to evidence/citations
4. **Evidence** - evidence table with verification_status enum, FKs to task and source, relationship to citations
5. **Citation** - citations table with quote, FKs to evidence and source
6. **Report** - reports table with format field, FK to session
7. **AgentLog** - agent_logs table with agent_name/action, FK to session

## Enums
- `ResearchStatus`: planning, researching, extracting, verifying, analyzing, writing, completed, failed
- `VerificationStatus`: supported, partially_supported, unsupported, contradicted

## Design Decisions
- Used lazy engine/session initialization in database.py to avoid import-time failures when DATABASE_URL is empty
- Added `__init__` methods to models so Column defaults are set at Python construction time (required for test assertions)
- All models use UUID primary keys and `cascade="all, delete-orphan"` for relationships
- Added `aiosqlite` to requirements.txt for async SQLite test support

## Concerns
- `datetime.utcnow()` deprecation warnings in Python 3.14+ (cosmetic, not blocking)
