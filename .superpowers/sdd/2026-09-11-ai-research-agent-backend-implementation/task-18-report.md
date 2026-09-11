# Task 18: Research Service (Orchestration)

## Status: DONE

## What Was Built

Created `backend/app/services/research.py` with the `ResearchService` class that orchestrates all agents in sequence:

1. **Planner** → creates research plan with subtasks
2. **Researcher** → searches web for sources
3. **Extractor** → extracts evidence from sources
4. **Verifier** → verifies claims against evidence
5. **Sufficiency** → checks if more research is needed
6. **Analyst** → analyzes findings and patterns
7. **Conflict Detector** → identifies contradictions
8. **Citation mapper** → maps claims to sources
9. **Confidence calculator** → scores overall confidence
10. **Writer** → generates the final report

## Key Adaptations from Spec

The implementation was adapted to match the actual database models:

- **ResearchSession**: Uses `created_at` (model default) instead of `started_at`/`completed_at`
- **Source**: Maps `session_id` (not `research_id`), stores `content` and `relevance_score`
- **Evidence**: Uses `content` field combining claim + evidence_text, linked via `task_id` and `source_id`
- **Citation**: Uses `evidence_id`, `source_id`, `quote` (not `citation_number`)
- **Report**: Uses `content` field (not `findings`)
- **AgentLog**: Uses `session_id`, `agent_name`, `action` (no status field)

Source-to-DB-ID mapping is handled via URL matching to correctly link evidence and citations.

## Files Created

- `backend/app/services/research.py` — ResearchService class
- `backend/tests/test_research_service.py` — 2 tests (initialization + full orchestration)

## Test Summary

- 2/2 tests passed
- All agents mocked to verify orchestration logic

## Commit

- `8c2adac` — feat: research service orchestrating all agents

## Concerns

None. The service correctly orchestrates all agents, handles the sufficiency loop for additional research iterations, and persists results to the database with proper foreign key relationships.
