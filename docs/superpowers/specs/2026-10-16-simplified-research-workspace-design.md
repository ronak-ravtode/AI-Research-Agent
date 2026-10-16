# Simplified Research Workspace — Design Spec

- **Date:** 2026-10-16
- **Status:** Approved
- **Implements:** `AI_Research_Agent_Simple_Implementation_Plan.md`
- **Supersedes:** `AI_Research_Agent_Backend_Implementation_Plan-1.md`, `docs/superpowers/specs/2026-09-11-ai-research-agent-backend-design.md`, `docs/superpowers/plans/2026-09-11-ai-research-agent-backend-implementation.md`

## Goal

Turn the existing application into a straightforward research website: a user submits a
question, the backend plans search queries, searches the web with Tavily, reads pages with
Firecrawl, and returns a readable answer with numbered citations that resolve to real,
retrievable sources. The UI shows real stage progress while the run happens.

## Verified baseline (2026-10-16)

| Fact | Status |
|---|---|
| Backend test suite | 74/74 passing across 23 files |
| Groq API key | Live — `openai/gpt-oss-120b` returns 200 |
| Tavily API key | Live — search returns results |
| Firecrawl API key | Live — 1025 credits remaining |
| Supabase project `srtnodlyshjqjwogssmp` | **Gone.** Pooler returns `tenant/user ... not found`; both `db.<ref>` and `<ref>.supabase.co` fail DNS |
| Local PostgreSQL 18.4 | Running on `localhost:5432` (`postgres`/`postgres`) |

The configured `DATABASE_URL` therefore cannot connect. `backend/.env` must be pointed at a
valid PostgreSQL instance. All code in this spec is database-independent and is verified
against SQLite; live end-to-end verification additionally requires a reachable database.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Orchestration | Four plain async Python functions | With no branching or cycles left, LangGraph manages nothing. Removing it deletes a dependency and ~200 lines while making each stage a readable `await` |
| Schema migration | Additive on a fresh database | A new/empty database needs no migration; `create_all` provisions the final schema directly |
| Retired code | Delete outright | Half-wired features plus their tests make the README unable to describe the product honestly |
| Frontend | Rebuild to the plan's §9 component set | The timeline, clickable citations, markdown rendering and failure states do not exist today |
| Theme | Light research-paper | Plan §4 and §Final both ask for a calm, paper-like reading layout; the current dark-only theme is not that |

## Architecture

```
POST /api/research  ──▶ insert session (queued) ──▶ return id
                            │
                            ▼  (BackgroundTask, own DB session)
        ResearchService.run_research(session_id, query)
            ├─ stage: running  "Breaking the question into search queries"
            ├─ plan_queries(query)                    → 2–4 queries
            ├─ stage: running  "Searching the web with Tavily"
            ├─ search(queries)                        → 5–8 deduplicated results
            ├─ stage: running  "Found N possible sources"
            ├─ extract(top 3–5)                       → page text, else snippet
            ├─ stage: running  "Reading selected pages"
            ├─ stage: running  "Preparing the cited answer"
            ├─ write_report(query, sources)           → markdown body
            ├─ validate_citations(body, sources)      → drop/renumber
            ├─ persist sources → persist report → status=completed
            └─ on any failure: rollback, status=failed, safe error_message, log exc_info
```

Every stage transition writes `status`, `current_stage`, `progress_message` **and** a
`research_activity` row inside the same transaction, so the timeline and the session row
can never disagree.

### Stages

1. **Plan** (`services/planning.py`) — Groq returns 2–4 concise queries as JSON. On any
   failure the original question is used as the single query. The run does not fail here.
2. **Search** (`services/search.py`) — Tavily per query, deduplicated by normalized URL,
   capped at 8 total. Keeps title, url, snippet, domain, score.
3. **Extract** (`services/extraction.py`) — top 3–5 results by score, Firecrawl scrape with
   a hard timeout. A failed scrape degrades that one source to `retrieval_method="tavily_snippet"`.
   Empty pages are dropped. Source type is classified conservatively.
4. **Report** (`services/report.py`) — Groq receives the question plus labeled source
   material and returns the report body only. It is never asked to emit URLs or a reference
   list.

### Fallback

If fewer than 2 usable results survive, or fewer than 2 sources end up with real page text,
run **one** broader Tavily search using the original question. No loop, no judge.

## Data model — 8 tables to 4

| Table | Columns |
|---|---|
| `research_sessions` | `id`, `query`, `status` (`queued`\|`running`\|`completed`\|`failed`), `current_stage`, `progress_message`, `error_message`, `created_at`, `updated_at`, `completed_at` |
| `sources` | `id`, `session_id`, `title`, `url`, `domain`, `source_type`, `snippet`, `content`, `retrieval_method`, `search_score`, `retrieved_at`, `created_at` |
| `reports` | `id`, `session_id`, `title`, `answer_markdown`, `created_at` |
| `research_activity` | `id`, `session_id`, `stage`, `message`, `created_at` |

Removed: `research_tasks`, `evidence`, `citations`, `agent_logs`.

`research_activity` earns its place twice: it is the timeline for a reopened session, and it
gives SSE a single monotonic change signal (`WHERE id > last_seen_id`) instead of diffing
four columns.

## Citation integrity

The model writes the **body only**. The References section is generated by the backend from
stored `Source` rows, so a fabricated URL or title is structurally impossible.

Validation of the returned body: find every `[n]`; drop any `n` outside `1..len(sources)`;
renumber the survivors compactly so citation numbers are contiguous. The frontend renders
each `[n]` as an anchor that scrolls the matching source card into view.

## Errors

`app/core/exceptions.py` already defines a hierarchy that nothing raises. It is now the real
error contract: `SearchError`, `ExtractionError`, `ReportGenerationError`, all deriving from
`ResearchRunError`.

- One catch site in `run_research`: rollback, `status="failed"`, `error_message` set to a
  fixed user-safe sentence (never an exception string, never a traceback, never a key).
- The full exception is logged server-side with `exc_info`.
- A failed run still emits a terminal `error` SSE event, so the frontend can never hang.
- Provider calls carry `httpx` timeouts: 30s search, 45s scrape, 90s completion.
- Bounds: ≤4 queries, ≤8 results, ≤5 extractions, ≤6000 characters of source text each,
  ≤20 000 characters total into the model.
- Only URLs returned by Tavily are ever fetched, and each is re-validated for `http`/`https`
  before the request (defence in depth against SSRF).

## SSE

Poll `research_activity` once per second for `id > last_seen_id`. Emit only new rows as
`stage` events. Emit an SSE comment `: keep-alive` every 15 seconds so proxies do not close
the connection. On a terminal session status, emit `complete` or `error` and close.

The frontend closes the `EventSource` on `complete`, on `error`, and on unmount. If the
`EventSource` itself errors, the UI shows "Reconnecting to research updates…" and falls back
to polling `GET /api/research/{id}`, so a run can never appear stuck.

## API

| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | static health |
| POST | `/api/research` | `{research_id, status}` immediately; run proceeds in background |
| GET | `/api/research/{id}` | status, current stage, progress message, error message, question, and the report when finished |
| GET | `/api/research/{id}/stream` | SSE `stage` / `complete` / `error` |
| GET | `/api/research/{id}/sources` | stored sources |
| GET | `/api/history` | 50 most recent sessions |

`GET /api/research/{id}/report` is dropped: the session endpoint already returns the report,
and two routes returning the same data is exactly the duplication plan §5 warns against.

## Frontend

```
src/
  app/page.tsx              view machine: idle | running | completed | failed
  app/layout.tsx            paper shell
  app/globals.css           research-paper tokens
  components/
    ResearchForm.tsx        textarea, Ctrl/⌘+Enter, sample questions, disabled while running
    ResearchProgress.tsx    activity timeline, reconnecting state
    ResearchReport.tsx      react-markdown, citation anchors, Copy answer
    SourceList.tsx          source cards, id anchors, Open source
    History.tsx             previous questions, status, date
  lib/api.ts                typed client, real error messages from response bodies
  types/research.ts         shared response types
```

`react-markdown` is added with raw HTML disabled, so model output can never inject markup.
States handled explicitly: idle, running, completed, failed, reconnecting, empty history.

## Tests

Rewritten around what remains, all provider calls mocked:

- search: dedupe by normalized URL, result cap, empty results, provider failure
- extraction: Firecrawl success, Firecrawl failure → snippet fallback, empty page dropped,
  per-source character cap, http/https validation
- report: citation indices in range kept, out-of-range dropped, renumbering contiguous,
  reference list built only from stored sources, no model URL reaches the report
- orchestration: stage transitions recorded in order, sources persisted before
  `completed`, provider failure → `status=failed` + safe message, no exception escapes
- API: `POST` returns an id immediately, status endpoint shape, invalid UUID → 400,
  unknown id → 404
- SSE: emits only new activity, terminal `complete`, terminal `error`

Tests that exist only to enforce retired features are deleted. Core search, extraction,
citation, persistence and error-handling coverage is not reduced.

## Verification

Phase 4 runs 8–10 representative questions across AI, cybersecurity, education, climate and
software topics against live providers with no mocks, plus an empty-results case and a forced
Firecrawl failure. The browser bundle is checked for provider keys. The demo flow in plan §12
is walked end to end.

## Out of scope

Embeddings, pgvector, semantic recall, confidence scoring, the conflict-detector agent,
weighted source-quality scoring, authentication, file uploads, background-worker
infrastructure, metrics dashboards.
