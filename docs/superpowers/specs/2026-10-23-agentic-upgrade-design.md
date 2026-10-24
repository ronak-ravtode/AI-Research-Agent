# Agentic Upgrade — Design Spec (2026-10-23)

Status: implemented
Related: `2026-10-16-simplified-research-workspace-design.md` (baseline pipeline)

## Problem

The baseline app was a fixed four-stage pipeline:
plan → search → read → write. Course rubric wants an *agentic*
research loop: multi-step reasoning, criticism of its own work, and
memory across related questions.

## Goals

1. The agent judges whether retrieved evidence is sufficient and
   autonomously searches again when it is not.
2. A second LLM pass verifies the draft against the sources and
   removes or qualifies unsupported claims.
3. Follow-up questions reuse a previous run's memory (question,
   answer, best sources) without rewriting the parent.
4. The user can see the plan (planned queries) and every agent
   decision in the activity log and UI.
5. Snippet-only pages trigger one extra broadened read instead of
   shipping a snippet-based report.
6. Everything stays bounded, fail-open, and testable offline.

## Non-goals

- Generic agent frameworks (LangGraph, AutoGen). The loop is 60 lines
  and explicit; adding a framework would obscure it.
- Unbounded iteration. `MAX_AGENT_ITERATIONS` (default 2) caps the
  coverage→search→extract loop.
- Chained follow-ups (child of child). The API documents that a
  follow-up whose parent is unfinished is rejected; a follow-up must
  point at a completed run. (The current schema allows a child of a
  child, but the frontend always parents to the latest completed run.)

## Multi-agent roles

| Agent | Module | Decision role | Failure behavior |
| --- | --- | --- | --- |
| Planner | `services/planning.py` | turns question (+ prior context, or gap feedback on re-plan) into queries | fails the run if the LLM is unreachable |
| Coverage reviewer | `services/coverage.py` | sufficient / insufficient + follow-up queries + reason | fail-open: `sufficient=True` on any error |
| Verifier | `services/verification.py` | revised body, removed_claims count, note | fail-open: keep draft on any error |
| Writer | `services/report.py` | draft (`write_draft`), critique-driven rewrite (`revise`), cited `finalize` | draft fails the run; `revise` failure is caught by the orchestrator (verifier's edit ships) |

## Agent loop (bounded)

```
queries = planner(question, prior_context)
sources = search → extract (with broaden_if_thin, broaden_if_shallow)
sources += parent memory sources (follow-ups)
for round in range(MAX_AGENT_ITERATIONS):
    decision = coverage(question, sources, tried_queries)
    log decision.reason                      # visible "deciding"
    if decision.sufficient: break
    # Mid-loop replanning: re-invoke the planner with the gap as feedback
    replanned = planner(question, context=gap_feedback(tried_queries, decision))
    new = first_of(replanned, decision.followup_queries) minus tried_queries
    if not new: break
    follow-up search + extract (only new URLs)
    # any error → log "continuing with the available evidence", stop looping
draft  = writer.write_draft(question, sources, prior_context)
result = verifier.verify(question, draft, sources)
# Verifier→writer negotiation (bounded by MAX_REWRITE_ROUNDS, default 1):
while result.revised and round < MAX_REWRITE_ROUNDS:
    rewritten = writer.revise(question, result.body, sources, feedback=result.note)
    result    = verifier.verify(question, rewritten, sources)
final  = writer.finalize(result.body, sources, question)
```

Mid-loop replanning detail: the planner is re-consulted with the
tried queries, the reviewer's gap reason, and its suggested queries as
steering context. Fresh planner queries take priority; the reviewer's
suggestions are the fallback when the planner errors or repeats known
queries. Negotiation detail: `report.revise` receives the critic's
edited body + note and rewrites; the rewrite is re-verified. A
re-verification failure ships the rewrite (fail-open); the loop budget
defaults to 1 so at most two verifier passes occur per run.

Every loop step emits a persisted activity row so the UI timeline
shows the "deciding" stage honestly, including failure-to-refine.

## Memory design

- `research_sessions.parent_session_id` → self-FK, `SET NULL`
  on parent delete, indexed.
- On a follow-up:
  - parent must exist (404) and be `completed` (400) and well-formed
    (400).
  - load top `MAX_CONTEXT_SOURCES` parent sources by search score →
    they become part of the child's evidence *and* are copied into the
    child's sources table, so a later purge of parent rows cannot break
    the child's citations.
  - prior context = parent question + parent report body (references
    stripped), capped at `MAX_CONTEXT_CHARS`; planning and drafting
    both receive it.
- Parent is never mutated.

## New stages

`deciding` (coverage reviewer) and `verifying` (critic) join
planning/searching/reading/writing between extraction and completion.
The SSE stream and polling fallback carry them transparently because
they are ordinary stage rows.

## Visibility

- `planned_queries` (JSON text) stored on the session, returned by the
  status endpoint, rendered as chips in the UI.
- `parent_research_id` returned in status + history and rendered as a
  "Follow-up" badge; the running view shows the same badge.

## Data / API changes

- `StartResearchRequest.parent_research_id?: UUID`
- `ResearchStatusResponse.planned_queries: list[str]`,
  `parent_research_id: UUID | null`
- `HistoryItem.parent_research_id: UUID | null`
- New config: `MAX_AGENT_ITERATIONS`, `MAX_CONTEXT_SOURCES`,
  `MAX_CONTEXT_CHARS`.

## Test strategy (offline, provider-stubbed)

- `test_research_service.py`: stage order, planned-query persistence,
  coverage loop (bounded at 2 rounds), reason surfaced, refinement
  failure does not fail the run, snippet fallback, memory flows
  (plan context + draft context), mid-loop replanning (planner
  re-invoked with gap feedback; falls back to reviewer queries on
  error/repeat), verifier⇄writer negotiation (revise → re-verify,
  bounded at 1 rewrite round).
- `test_coverage.py` / `test_verification.py`: fail-open contracts,
  payload sanitation, dedupe/caps.
- `test_api.py` / `test_report.py`: validation of parent links,
  history/status serialization, citation padding.
- Frontend gated by lint + tsc + build (no test framework yet).

## Alternatives considered

- **LangGraph style graph**: more colorful, less auditable; rejected.
- **Critic may re-ask for sources individually**: explosion of calls;
  rejected in favor of batch follow-up queries.
- **Explicit orchestrator LLM** ("decide next stage from state"):
  removes the determinism, testability, and cost bounds the design is
  built on; consciously rejected in favor of the fixed control flow.
- **Honor-system citations (persist draft as-is)**: violates the
  citation-integrity acceptance criterion; rejected.
