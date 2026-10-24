# Viva Preparation — AI Research Agent

**Team of 4 · AI subject · Project explanation + viva**

How to use this document:

- Sections 1–3 are for **everyone**. Learn them by heart.
- Sections 4–7 are your **individual ownership areas**: your files, what each file does, and every function in it.
- Sections 8–10 are the **team drill**: demo order, question routing, verification before the viva.

---

## 1. The 90-second introduction (problem → solution)

Deliver this as the opening. M1 (leader) speaks unless the examiner asks someone else.

### The problem

> Today, if a student or researcher asks a question, they get two bad options:
>
> 1. **Search engines** return links, not answers. You must open 6–8 pages and read them yourself.
> 2. **Chatbots** return a fluent answer with no proof. You cannot tell which sentence is supported by a real page and which one the model invented.
>
> So the real problem is not "getting an answer". It is **getting an answer you can verify**, without spending an hour collecting evidence.

### The solution

> We built an **agentic research assistant**. You ask one question. The system then:
>
> 1. **Plans** several targeted search queries.
> 2. **Searches** the live web and **reads** the actual pages.
> 3. **Judges its own evidence** — if something important is missing, it goes back and searches again, up to a fixed limit.
> 4. **Writes** a report where every claim carries a numbered citation.
> 5. **Verifies** the draft against the retrieved pages and removes unsupported claims.
>
> Everything is saved and streamed live, so the user sees every decision the agent made.

### One-line pitch (memorise this)

> **"A cited, self-checking research agent: it plans, reads, judges, writes, and verifies — and every claim traces back to a page it actually read."**

### The numbers (say them if there is time)

- **169 automated tests** passing (provider calls stubbed, deterministic).
- **8/8 live runs** completed against real providers.
- **0 dangling citations, 0 invented URLs** in those runs.
- Average **~175 seconds** per run, **~6 sources** per report.

> Verify these before the viva (Section 10). If the number changed, say the new one.

---

## 2. The 30-second individual intro

If an examiner points at one member and says *"Introduce your project"*, any of you can say:

> "Our project is an AI research agent. A user asks a question; the system plans searches, reads live web pages, decides whether the evidence is sufficient, writes a cited report, and then verifies every claim against the sources. I was responsible for **[your area]** — **[one sentence of what that means]**. The whole pipeline is bounded and fails safely, so it cannot loop forever or silently invent facts."

Then stop. Let them ask.

---

## 3. Basic information every member MUST know

### 3.1 What the user does

| Step | What happens |
|---|---|
| 1 | User types a question on the home page and picks a depth: Quick / Standard / Deep |
| 2 | They land on `/r/<id>` immediately — the run continues in the background |
| 3 | The activity timeline updates live: planning → searching → reading → deciding → writing → verifying |
| 4 | When complete: report + verification badge + numbered sources |
| 5 | They can open any source's full text, ask a **follow-up** (reuses the earlier run's memory), rename, export `.md`, or delete the run |

### 3.2 The pipeline (draw this on the board)

```
Question
   ↓
PLANNING      LLM turns the question into up to 4 search queries
   ↓
SEARCHING     Tavily returns ranked results (fallback: one broader search)
   ↓
READING       Firecrawl extracts full page text (fallback: snippets only)
   ↓
DECIDING      LLM reviewer: "is the evidence enough?"
                 ├─ yes → continue
                 └─ no  → planner is re-invoked with the GAP as feedback
                          → search + read again (max 2 rounds)
   ↓
WRITING       LLM drafts the report with [n] citations
   ↓
VERIFYING     LLM checks each claim against the sources
                 └─ if claims removed → writer rewrites → re-verify (max 1 round)
   ↓
COMPLETE      Report + sources + activity saved to PostgreSQL
```

**Say this out loud:** *"The loop can go backwards only at two places, and both are bounded."*

### 3.3 Tech stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind CSS | Server layout + client components only where interaction is needed |
| Backend | FastAPI (Python), SQLAlchemy async, Pydantic | Async I/O, request validation, automatic API docs |
| Database | PostgreSQL (asyncpg driver) | Relational integrity, cascading deletes, simple schema |
| LLM | Groq — `openai/gpt-oss-120b` | Fast inference for a multi-call agent loop |
| Search | Tavily | Ranked web results with snippets and scores |
| Extraction | Firecrawl | Full-text page extraction (markdown) |
| Streaming | Server-Sent Events (SSE) | One-way server→client progress, simple over HTTP |

### 3.4 The five limits (the most examinable facts)

| Constant | Default | Meaning |
|---|---|---|
| `MAX_AGENT_ITERATIONS` | 2 | Follow-up rounds after an evidence gap |
| `MAX_REWRITE_ROUNDS` | 1 | Writer rewrites after the verifier flags a draft |
| `MAX_SEARCH_QUERIES` | 4 | Queries per search call |
| `MAX_SEARCH_RESULTS` | 8 | Results per search call |
| `MAX_EXTRACT_SOURCES` | 5 | Pages actually read per batch |

Plus context caps: **6,000 chars per page**, **20,000 chars total** (this is why the model never gets an unlimited prompt).

### 3.5 The five run statuses

`queued` → `running` → `completed` | `failed` | `cancelled`

Every status that crosses a boundary is normalised, so an old row that stored a stage name (e.g. `planning`) can never break the API contract.

### 3.6 Data model — four tables

| Table | Holds | Key detail |
|---|---|---|
| `research_sessions` | The run: query, status, stage, plan, parent link | `cancel_requested`, `max_iterations`, `parent_session_id` |
| `sources` | Every page read | `content` (full text), `retrieval_method`, `search_score` |
| `reports` | The final report | `verification_note`, `removed_claims`, `verification_revised`, `verification_available` |
| `research_activity` | Append-only timeline | Integer `id` = the exact change signal for SSE |

### 3.7 API surface

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/research` | Start a run (optional `parent_research_id`, `max_iterations`) |
| GET | `/api/research/{id}` | Status, stage, plan, report, verification fields |
| GET | `/api/research/{id}/sources` | Source list (no full text — payload size) |
| GET | `/api/research/{id}/sources/{sid}` | One source **with** full text + citation number |
| GET | `/api/research/{id}/activity` | Full timeline (for refresh / history) |
| GET | `/api/research/{id}/stream` | SSE: `stage`, `complete`, `error`, `timeout`, `keepalive` |
| POST | `/api/research/{id}/cancel` | Cooperative cancel (idempotent) |
| PATCH | `/api/research/{id}` | Rename (display title) |
| DELETE | `/api/research/{id}` | Delete run + sources + report + activity |
| GET | `/api/history` | Paginated, filterable, searchable list |
| GET | `/api/health` | Non-secret runtime facts for the UI |

### 3.8 Frontend routes

| Route | Page | Owner |
|---|---|---|
| `/` | Home / chat composer + suggestions | M3 |
| `/library` | All research: filter, search, rename, delete | M4 |
| `/settings` | Theme, depth, citation preview, runtime facts | M4 |
| `/r/[id]` | Live run: progress, verification, report, sources | M4 |
| `/r/[id]/sources/[sourceId]` | Full-text source reader | M4 |

### 3.9 The three design principles (use these words)

1. **Bounded autonomy** — the agent can change course, but only inside hard numeric limits.
2. **Fail-open, not fail-crash** — a broken reviewer or verifier degrades to "write from available evidence, and say so", instead of destroying the run.
3. **Persist everything** — every stage transition is a database row, so refresh, history, audit, and streaming all read the same truth.

### 3.10 Three honest limitations (never hide these)

1. **No authentication / multi-user isolation** — it is a single-user academic deployment.
2. **In-process background tasks** — a server restart loses an in-flight run; there is no queue.
3. **Small evaluation set** — 8 live questions, one model, no human rating study.

Say *"these are the next engineering steps"*, not *"we did not have time"*.

---

## 4. MEMBER 1 — Backend Platform, API & Integration (Team Leader)

### Your role in one line

> "I own the backend platform: the API contract, the database, the background execution, streaming, cancellation, history, configuration, and integration of the AI services into a reliable service."

### Files you own

| File | What it does |
|---|---|
| `backend/app/main.py` | App creation, routers, CORS, startup checks and schema sync |
| `backend/app/api/research.py` | Start / status / stream / cancel / rename / delete / activity |
| `backend/app/api/sources.py` | Source list, source detail, history |
| `backend/app/api/health.py` | Runtime facts for Settings and the sidebar |
| `backend/app/database/models.py` | 4 tables + status constants + `normalize_status` |
| `backend/app/database/database.py` | Async engine, session factories, connection health |
| `backend/app/database/migrations.py` | Idempotent schema sync on startup |
| `backend/app/schemas/research.py` | Request/response models for a run |
| `backend/app/schemas/source.py` | Request/response models for sources |
| `backend/app/schemas/report.py` | History item model |
| `backend/app/core/config.py` | All bounds, timeouts, keys |
| `backend/app/core/exceptions.py` | Typed errors + user-safe messages |
| `backend/app/core/logging.py` | Structured, console-safe logging |
| `backend/app/utils/url.py` | Small URL helpers |
| `frontend/src/lib/api.ts` | Typed client for your API contract |
| `frontend/src/types/research.ts` | Shared TypeScript contract types |

### File-by-file breakdown

#### `backend/app/main.py`

**Purpose:** creates the FastAPI application, wires the three routers, configures CORS, and prepares the database on startup.

| Symbol | Explanation |
|---|---|
| `settings` | Module-level settings instance used for CORS and startup logging. |
| `STARTUP_HELP` | Human-readable troubleshooting text printed when the database is unreachable. |
| `lifespan(app)` | Async context manager: verifies the DB with `SELECT 1`, runs `sync_schema`, logs what changed, and disposes the engine on shutdown. |
| `app` | The FastAPI instance: title, version, and lifespan handler attached. |
| `origins` | Allowed CORS origins — the configured frontend URL plus localhost in development. |
| `app.add_middleware(...)` | Registers CORS with deduplicated origins, credentials, and all methods/headers. |
| `app.include_router(...)` | Mounts the health, research, and sources routers. |

#### `backend/app/api/research.py`

**Purpose:** the HTTP surface for one run's whole lifecycle, including the SSE stream and cooperative cancellation.

| Symbol | Explanation |
|---|---|
| `POLL_INTERVAL_SECONDS` (1.0) | How often the SSE generator checks the database for new activity rows. |
| `KEEPALIVE_SECONDS` (15.0) | Emits a `keepalive` event so proxies do not drop an idle stream. |
| `MAX_STREAM_SECONDS` (900.0) | Hard cap; after this the stream closes and the client falls back to polling. |
| `_parse_uuid(research_id)` | Converts a path string to `UUID`, raising HTTP 400 on a malformed id. |
| `_parse_plan(raw)` | Parses the stored `planned_queries` JSON defensively; bad data becomes an empty list. |
| `_run_in_background(research_id)` | Opens its own DB session and runs `ResearchService`; logs handler bugs instead of crashing the worker. |
| `start_research(request, background_tasks, db)` | Validates an optional parent, inserts a `queued` session, schedules the workflow, returns the id immediately. |
| `cancel_research(research_id, db)` | Sets `cancel_requested`; cancels a still-queued run outright; idempotent for terminal runs. |
| `rename_research(research_id, request, db)` | Sets or clears `display_title` without touching the real question. |
| `delete_research(research_id, db)` | Deletes the session; foreign-key cascades remove sources, report, and activity. |
| `get_research_status(research_id, db)` | Returns status, stage, plan, parent link, report body, and verification fields. |
| `stream_research(research_id)` | SSE endpoint; its inner `event_generator()` streams new activity rows by increasing id, emits `keepalive`, and closes on a terminal status or timeout. |
| `get_activity(research_id, db)` | Returns the full ordered timeline, used when a page is reopened or refreshed. |

#### `backend/app/api/sources.py`

**Purpose:** read-side endpoints for evidence and history — everything the run page and library need after a run exists.

| Symbol | Explanation |
|---|---|
| `DEFAULT_HISTORY_LIMIT` (20) / `MAX_HISTORY_LIMIT` (100) | Safe pagination bounds for the history endpoint. |
| `VALID_STATUSES` | Whitelist for the status filter, so an unknown filter is a 400 rather than a silent empty list. |
| `_parse_uuid(research_id)` | Same UUID parsing contract as the research router. |
| `_source_response(source)` | Maps one ORM `Source` row to the API model, deliberately excluding `content`. |
| `get_sources(research_id, db)` | Lists a run's sources in citation order, metadata only. |
| `get_source(research_id, source_id, db)` | Returns one source with full text plus its 1-based citation `index` and the run's `total`. |
| `get_history(db, limit, offset, status, q)` | Returns a page of runs newest-first, with source/report counts from grouped subqueries, a total count, and `has_more`. |

#### `backend/app/api/health.py`

**Purpose:** one honest, non-secret snapshot of what this deployment is actually running.

| Symbol | Explanation |
|---|---|
| `health_check()` | Returns service name, version, environment, provider identities, active limits, and whether all required keys are configured. |

#### `backend/app/database/models.py`

**Purpose:** defines the four tables, the status vocabulary, and the normalisation rule that keeps the API contract stable.

| Symbol | Explanation |
|---|---|
| `STATUS_QUEUED / RUNNING / COMPLETED / FAILED / CANCELLED` | The only five statuses the client may ever see. |
| `VALID_STATUSES`, `TERMINAL_STATUSES` | Membership sets used for validation and for deciding when a stream may close. |
| `_LEGACY_STAGE_STATUSES` | Old rows could store a stage name; this set lets `normalize_status` map them back to `running`. |
| `normalize_status(raw)` | Coerces any stored value into one of the five statuses, treating unknowns as `queued` so legacy rows stay visible. |
| `RETRIEVAL_FIRECRAWL`, `RETRIEVAL_SNIPPET` | Constants describing how a source's text was obtained. |
| `_utcnow()` | Single timezone-aware timestamp helper used by all defaults. |
| `ResearchSession` | The run row: query, `display_title`, status, `cancel_requested`, parent link, plan JSON, stage/message, `max_iterations`, timestamps, and relationships. |
| `Source` | One retrieved page: title, URL, domain, type, snippet, full `content`, retrieval method, score, retrieval time. |
| `Report` | The finished answer plus the verifier's verdict (`verification_note`, `removed_claims`, `revised`, `available`). |
| `ResearchActivity` | Append-only timeline row with an auto-increment integer id — the change signal for SSE. |

#### `backend/app/database/database.py`

**Purpose:** owns the async engine and the two session dependencies, and makes hosted PostgreSQL connections fail fast instead of hanging.

| Symbol | Explanation |
|---|---|
| `_normalize_db_url(url)` | Rewrites `postgres://` and `postgresql://` URLs to the `postgresql+asyncpg://` driver form. |
| `_connect_args(db_url)` | Returns driver-specific connection arguments; enables TLS for Supabase or an explicit `sslmode=require`, with sane timeouts. |
| `_get_engine()` | Lazily builds the single async engine with `pool_pre_ping` and `pool_recycle` to survive dropped connections. |
| `_get_session_factory()` | Lazily builds the `async_sessionmaker`, with `expire_on_commit=False` so returned objects stay usable. |
| `Base` | Declarative base shared by all models and by schema inspection. |
| `get_db()` | Request dependency for read-write work: commits on success, rolls back on exception. |
| `get_db_readonly()` | Request dependency for read-only endpoints: never commits. |

#### `backend/app/database/migrations.py`

**Purpose:** upgrades an existing database in place, because `create_all` adds tables but never columns. It is narrow, idempotent, and never deletes rows.

| Symbol | Explanation |
|---|---|
| `PG` | Explicit PostgreSQL dialect, so `Uuid` renders as `UUID` and aware datetimes as `TIMESTAMPTZ`. |
| `_collect_schema(sync_conn)` | Introspects existing table and column names inside `run_sync` to avoid async/greenlet errors. |
| `Change(table, statement)` | A single planned DDL statement, paired with the table it affects. |
| `_render_type(column)` | Compiles a mapped column's type into PostgreSQL DDL. |
| `_render_default(column)` | Renders a server-side default when one is a literal; callables are skipped because the app supplies those values. |
| `plan_changes(conn)` | Computes everything needed: create missing tables, add missing columns, convert naive timestamps to `timestamptz`, and relax stale `NOT NULL` columns. |
| `apply_changes(conn, changes)` | Executes the planned statements, skipping table creation (handled by `create_all`) and SQLite-incompatible `ALTER COLUMN`. |
| `sync_schema(conn, drop_obsolete=False)` | Orchestrates plan → create → apply, optionally drops obsolete tables, and returns a human-readable summary for the startup log. |

#### `backend/app/schemas/research.py`

**Purpose:** the Pydantic contract for starting and reading a run — the authority on what the client may send and receive.

| Symbol | Explanation |
|---|---|
| `StartResearchRequest` | Validates `query` (10–2000 chars), optional `parent_research_id`, and optional `max_iterations` clamped to 0–3. |
| `ResearchResponse` | Minimal start response: `research_id` and `status`. |
| `ResearchStatusResponse` | Full status payload: stage, plan, parent link, report body, and the four verification fields. |
| `RenameResearchRequest` | Validates an optional display title (max 300 chars); empty clears it. |

#### `backend/app/schemas/source.py`

**Purpose:** the source contract, split deliberately so the list is light and the detail carries the full page.

| Symbol | Explanation |
|---|---|
| `SourceResponse` | Source metadata without `content` — used by the list endpoint. |
| `SourceListResponse` | `sources` plus a `total`, so the UI can state the count without guessing. |
| `SourceDetailResponse` | Extends the metadata with `content`, a 1-based `index`, and the run's `total` for "source n of m". |

#### `backend/app/schemas/report.py`

**Purpose:** the history row model shared by the sidebar and the library.

| Symbol | Explanation |
|---|---|
| `HistoryItem` | One list row: id, question, display title, status, parent link, source count, whether a report exists, and timestamps. |

#### `backend/app/core/config.py`

**Purpose:** the single source of truth for every key, timeout, and bound in the system.

| Symbol | Explanation |
|---|---|
| `REQUIRED_KEYS` | The four settings that must be non-empty for a run to work. |
| `Settings` | Pydantic settings model: provider keys, database URL, frontend URL, three timeouts, and all search/extraction/agent/rewrite limits. |
| `Settings.missing_required_keys()` | Returns the names of blank required keys, for logging only. |
| `Settings.validate_required_keys()` | Raises `ConfigurationError` before a run starts if anything required is missing. |
| `get_settings()` | Cached accessor, so configuration is parsed once per process. |

#### `backend/app/core/exceptions.py`

**Purpose:** one error contract where every failure carries a short user-safe message; the real cause stays in the server log.

| Symbol | Explanation |
|---|---|
| `ResearchRunError` | Base class holding `user_message` and `error_code`, plus a server-side `detail`. |
| `SearchError` | Search provider unreachable or failed. |
| `NoResultsError` | Search worked but produced nothing usable. |
| `ExtractionError` | No page could be read at all. |
| `ReportGenerationError` | The draft or revision could not be produced. |
| `RateLimitError` | Provider quota hit; the message tells the user to wait. |
| `ConfigurationError` | Missing server configuration. |
| `ResearchCancelled` | Deliberately *not* a `ResearchRunError`: cancellation is a third outcome, not a failure. |

#### `backend/app/core/logging.py`

**Purpose:** structured, flush-on-write logging that cannot crash on non-ASCII agent text (a real Windows `cp1252` problem).

| Symbol | Explanation |
|---|---|
| `_console()` | Reconfigures stdout to UTF-8 with replacement, so any agent message is printable. |
| `StructuredLogger.__init__(name)` | Creates one handler on stdout, sets INFO level, and disables propagation to avoid duplicate lines. |
| `StructuredLogger._emit(level, message, data, exc_info)` | Formats `key=value` pairs, drops empty ones, writes the line, and flushes every handler. |
| `StructuredLogger.info / error / warning / debug` | Level-specific wrappers; `error` can carry a traceback while keeping `data` structured. |
| `logger` | The shared application logger instance. |

#### `backend/app/utils/url.py`

**Purpose:** two tiny URL helpers kept separate from the provider code.

| Symbol | Explanation |
|---|---|
| `extract_domain(url)` | Returns the network location (host) of a URL. |
| `is_valid_url(url)` | Returns true only when both a scheme and a host are present. |

#### `frontend/src/lib/api.ts` (the client side of your contract)

**Purpose:** the only place the frontend talks to the backend; it centralises error handling and the SSE wiring.

| Symbol | Explanation |
|---|---|
| `BASE` | Empty string: all calls are same-origin and reach FastAPI through the Next.js rewrite. |
| `ApiError` | Error type carrying both a message and an HTTP status (0 means a network failure). |
| `request<T>(path, init)` | Shared fetch wrapper: no-store, maps network failure to a clear message, prefers the backend's `detail`. |
| `readError(response)` | Extracts `detail` from an error body, falling back to a generic status message. |
| `startResearch(query, options)` | POSTs a new run with optional parent id and depth override. |
| `getResearchStatus(id)` | Fetches the full status payload for one run. |
| `getSources(id)` | Fetches the metadata-only source list. |
| `getSource(id, sourceId)` | Fetches one source with full text and citation number. |
| `getActivity(id)` | Fetches the complete timeline and unwraps the `activity` array. |
| `getHistory(params)` | Builds the query string for limit/offset/status/search and returns one page. |
| `cancelResearch(id)` | Asks a live run to stop; safe to call repeatedly. |
| `renameResearch(id, title)` | Sets or clears the display title. |
| `deleteResearch(id)` | Deletes a run and its children. |
| `getHealth()` | Reads the non-secret runtime facts. |
| `streamResearch(id, handlers)` | Opens an `EventSource`, dispatches `stage`/`complete`/`error`/`timeout`, reports transport failure separately, and returns a close function. |
| `parse<T>(raw)` | Safely JSON-parses an SSE event, returning null instead of tearing the stream down. |

#### `frontend/src/types/research.ts`

**Purpose:** the TypeScript mirror of the Pydantic contract, so a backend field rename becomes a compile error.

| Symbol | Explanation |
|---|---|
| `ResearchStatus`, `Stage` | The five statuses and the eight stage names, as string unions. |
| `ResearchStatusResponse` | Full run payload including `planned_queries`, verification fields, and `max_iterations`. |
| `Source`, `SourceDetail`, `SourceListResponse` | Metadata, full-text variant, and list wrapper. |
| `HistoryItem`, `HistoryResponse` | One history row and one paginated page. |
| `ActivityEvent`, `CompleteEvent` | SSE stage payload and the terminal payload. |
| `HealthResponse` | Provider identities, limits, and configuration flag. |

### Say this in the demo (≈60 seconds)

> "The key backend decision is that a research run takes about three minutes, so it cannot live inside one HTTP request. `POST /api/research` writes a `queued` row, schedules the workflow on a **background task with its own database session**, and returns the id immediately. The browser then goes to `/r/<id>` and subscribes to **SSE**.
>
> Progress is not invented in memory. Every stage transition commits the session row **and** appends an `research_activity` row in the same transaction. The activity table is append-only with a monotonic integer id, so the client just asks for `id > last_id` — that is an exact change signal, not timestamp guessing.
>
> Cancellation is **cooperative**: the API sets `cancel_requested`, and the workflow checks it at the next stage boundary. We do not kill a thread, because that would leave a half-written report. Everything is idempotent, and every failure ends in a persisted terminal state."

---

## 5. MEMBER 2 — Agent Orchestration (The AI Layer)

### Your role in one line

> "I own the intelligence of the system: how the agent plans, decides whether evidence is enough, when to search again, how it writes, and how it verifies its own claims."

### Files you own

| File | What it does |
|---|---|
| `backend/app/services/research.py` | The workflow: stages, adaptive loop, memory, persistence |
| `backend/app/services/planning.py` | Question → search queries, including gap-driven re-planning |
| `backend/app/services/search.py` | Tavily calls, URL normalisation, dedupe |
| `backend/app/services/extraction.py` | Firecrawl extraction, cleaning, snippet fallback |
| `backend/app/services/coverage.py` | The reviewer: "is the evidence sufficient?" |
| `backend/app/services/report.py` | Drafting, revising, citation validation, references |
| `backend/app/services/verification.py` | Claim checking against sources |
| `backend/app/services/llm.py` | Provider wrapper, retries, structured JSON |

### File-by-file breakdown

#### `backend/app/services/research.py`

**Purpose:** the orchestrator. It runs one research session end to end, owns the bounded agent loop, records every stage, and guarantees a terminal state.

| Symbol | Explanation |
|---|---|
| `STAGE_PLAN / SEARCH / EXTRACT / DECIDE / WRITE / VERIFY / DONE` | Canonical stage names, shared with the API and UI. |
| `MIN_ITERATIONS` (0) / `MAX_ITERATIONS` (3) | Legal depth range accepted from the UI. |
| `ResearchOptions` | Per-run options object, carrying the depth override. |
| `ResearchService.__init__(db, options)` | Binds the service to one database session and one run's options. |
| `run(session_id)` | Entry point: validates configuration, loads the session, and converts any exception into a persisted `failed` or `cancelled` state. |
| `_execute(session)` | The pipeline itself: plan, search, read, coverage loop with replanning, draft, verify, negotiate a rewrite, then persist sources and report. |
| `_load_memory(session)` | For a follow-up, loads the parent's question, answer, and best sources, returning them as reusable context. |
| `_only_new_results(existing, incoming)` | Filters search results to URLs not already seen, using normalised URLs. |
| `_merge_sources(*groups, limit)` | Merges source lists, deduping by URL and keeping the copy with the most text. |
| `_broaden_if_shallow(session, query, results, sources)` | Fallback when fewer than two pages have real text: one broader search, then read only fresh URLs. |
| `_broaden_if_thin(query, results)` | Fallback when search returned fewer than two results: one broader search on the original question. |
| `_persist_sources(session, sources)` | Writes source rows and flushes them before the report, so a report can never cite an unstored source. |
| `_stage(session, stage, message)` | Sets status/stage/message, appends an activity row, and commits — the atomic progress update. |
| `_raise_if_cancelled(session)` | Refreshes `cancel_requested` from the database and raises `ResearchCancelled` at a stage boundary. |
| `_activity(session, stage, message)` | Adds one append-only timeline row (no commit on its own). |
| `_mark_failed(session, message)` | Records a safe user-facing failure with a terminal timestamp and activity entry. |
| `_mark_cancelled(session_id)` | Records cancellation as its own terminal state, idempotently. |
| `_fail(session_id, exc)` | Rolls back partial work, logs the real cause, and persists only the safe message. |
| `_load(session_id)` | Loads a session row or returns `None`. |

#### `backend/app/services/planning.py`

**Purpose:** turns one question into a small set of distinct queries, and can be re-invoked mid-loop with an evidence-gap brief.

| Symbol | Explanation |
|---|---|
| `SYSTEM_PROMPT` | Instructs JSON-only output, 2–4 short queries, distinct angles, and no repetition of tried queries when a gap is provided. |
| `_clean_query(raw)` | Collapses whitespace and strips stray quotes. |
| `_coerce_queries(payload)` | Accepts several plausible JSON shapes and returns a clean list of non-empty strings. |
| `PlanningService.__init__()` | Caches the configured maximum query count. |
| `plan_queries(question, context)` | Calls the LLM for queries, dedupes, caps the count, and degrades to the original question on any failure. |

#### `backend/app/services/search.py`

**Purpose:** the only place Tavily's response shape is understood; everything downstream sees one normalised result type.

| Symbol | Explanation |
|---|---|
| `TRACKING_PARAMS` | Analytics parameters stripped during normalisation so the same page is not fetched twice. |
| `SearchResult` | Normalised result: title, URL, snippet, score, domain, and a normalised URL key. |
| `normalize_url(url)` | Lowercases scheme/host, drops `www.`, trims trailing slashes, and removes tracking parameters. |
| `is_fetchable_url(url)` | Allows only plain `http(s)` URLs with a host — defence in depth before scraping. |
| `SearchService.__init__()` | Creates a Tavily client backed by an `httpx` client that enforces the configured search timeout. |
| `search(queries)` | Runs all queries concurrently, merges results, tolerates individual failures, raises only if every query fails, then dedupes and caps. |
| `_search_one(query)` | Executes one query, validates each URL, and maps raw items into `SearchResult` objects. |
| `_dedupe(results)` | Keeps the highest-scoring copy per normalised URL and returns results sorted by score. |

#### `backend/app/services/extraction.py`

**Purpose:** reads pages into clean text, classifies them, and degrades any unreadable page to its search snippet rather than failing the run.

| Symbol | Explanation |
|---|---|
| `DOMAIN_PATTERNS`, `EDU_SUFFIXES` | Conservative domain-to-source-type mapping (papers, government, docs, news, academia). |
| `RetrievedSource` | A persistable source: metadata, snippet, full content, method, and score. |
| `RetrievedSource.text` (property) | Returns the scraped page if available, otherwise the snippet — the single "best available evidence" rule. |
| `classify_source_type(url, title)` | Labels a source by domain, defaulting to the honest "Web article". |
| `FIRECRAWL_MARKER_RE` | Matches Firecrawl's inline link markers, which are meaningless across pages and mislead the model. |
| `clean_page_text(text)` | Removes those markers, collapses run-on whitespace, and normalises blank lines. |
| `ExtractionService.__init__()` | Caches the API key and the read/character limits; the client is built lazily. |
| `extract(results)` | Takes the top fetchable results, scrapes them concurrently, falls back per-source on failure, and raises only if every source is empty. |
| `_extract_one(result)` | Scrapes and cleans one URL, truncates to the per-page cap, and returns a full-text source or `None`. |
| `_from_snippet(result)` | Builds a snippet-only source, marked `tavily_snippet` so the UI can be honest about it. |
| `_scrape(url)` | Calls Firecrawl for markdown of the main content, bounded by `SCRAPE_TIMEOUT`. |

#### `backend/app/services/coverage.py`

**Purpose:** the adaptive gate. It judges whether the collected evidence can answer the question and, if not, names the gap.

| Symbol | Explanation |
|---|---|
| `SYSTEM_PROMPT` | Defines the JSON verdict, when to mark insufficient, and the rules for follow-up queries. |
| `MAX_FOLLOWUP_QUERIES` (2) | Hard cap on suggested queries, independent of the caller. |
| `CoverageDecision` | Verdict object: `sufficient`, `followup_queries`, `reason`. |
| `_clean_queries(raw)` | Normalises and dedupes a model-supplied query list. |
| `CoverageService.__init__()` | Reads the configured query cap. |
| `CoverageService.assess(question, sources, tried_queries)` | Builds the evidence prompt, calls the model at low temperature, and fails open to "sufficient" on errors, malformed payloads, or when no new query is proposed. |

#### `backend/app/services/report.py`

**Purpose:** writes the body and makes citations impossible to fake — the model never produces URLs or a reference list.

| Symbol | Explanation |
|---|---|
| `SYSTEM_PROMPT` | Requires `[n]` citations, forbids inventing numbers, URLs, or a reference list, and fixes the Markdown structure. |
| `CITATION_RE` | Matches ASCII and full-width citation brackets (including Firecrawl-style annotations) while leaving Markdown links intact. |
| `ReportResult` | Title plus final markdown. |
| `build_source_material(sources)` | Renders numbered source blocks with a per-page cap and a total budget, skipping empty text. |
| `validate_citations(body, source_count)` | Normalises bracket styles and removes citations outside `1..n`; surviving numbers are never renumbered. |
| `build_reference_list(sources)` | Builds the reference section from stored sources only. |
| `_prepare_prior_context(text)` | Strips old citation brackets from parent context and caps it, so stale numbers cannot be reused. |
| `ReportService.write_draft(question, sources, prior_context)` | Builds the prompt, generates the body, maps provider errors to typed errors, and validates citations. |
| `ReportService.revise(question, body, sources, feedback)` | Rewrites a verifier-flagged draft using the critique, keeping only supported claims and the existing structure. |
| `ReportService.finalize(body, sources, question)` | Validates citations, appends the stored-source reference list, and derives a title. |
| `ReportService.write_report(question, sources)` | Convenience path: draft then finalize, used outside the agent loop. |
| `_derive_title(question)` | Produces a readable title without another model call. |

#### `backend/app/services/verification.py`

**Purpose:** the second opinion. It checks the finished draft against the same numbered sources and returns a corrected body.

| Symbol | Explanation |
|---|---|
| `SYSTEM_PROMPT` | Defines the JSON verdict, requires the full revised body when unsupported claims exist, and forbids new facts, citations, or URLs. |
| `VerificationResult` | Body, `revised` flag, `removed_claims`, and a one-line note. |
| `_as_int(value)` | Safely coerces the claim count to a non-negative integer. |
| `VerificationService.verify(question, body, sources)` | Skips cleanly when there is nothing to check; otherwise calls the model and fails open to the original draft on errors or unusable payloads. |

#### `backend/app/services/llm.py`

**Purpose:** one wrapper around Groq that every agent call goes through, with bounded retries and defensive JSON parsing.

| Symbol | Explanation |
|---|---|
| `RETRYABLE_MARKERS` | Substrings that identify transient provider conditions worth retrying. |
| `MAX_ATTEMPTS` (3), `BACKOFF_BASE_SECONDS` (2), `BACKOFF_CAP_SECONDS` (20) | Retry budget and exponential backoff bounds. |
| `is_transient(message)` | Decides whether an error message describes a retryable condition. |
| `LLMService.__init__()` | Creates the async Groq client and caches the model name. |
| `LLMService._complete(messages, temperature, max_tokens)` | Performs one completion, retrying transient errors with exponential backoff plus jitter. |
| `LLMService.generate(prompt, system_prompt, temperature, max_tokens)` | Builds the message list and returns plain text. |
| `LLMService.structured_generate(...)` | Returns parsed JSON, stripping code fences and recovering a JSON object embedded in prose. |

### Say this in the demo (≈60 seconds)

> "A normal RAG pipeline does one retrieval and one generation. Ours closes the loop.
>
> After reading, a **coverage reviewer** gets the question, the sources, and the queries already tried, and returns JSON: sufficient or not, plus the reason. If it is not sufficient, we do **not** just trust its suggested queries — we **re-invoke the planner with the gap as feedback**, so it can reason about the whole question again. The reviewer's queries are only the fallback. That whole loop is capped at two rounds.
>
> Then the writer drafts with numbered citations. The **verifier** checks every claim against the sources and removes or qualifies unsupported ones. If it removed anything, the draft goes **back to the writer** with that critique, and the rewrite is re-verified. That negotiation is capped at one round.
>
> Every one of these steps is **fail-open**: if a reviewer call fails, we continue with the evidence we have and record that in the activity log. Availability matters more than perfection — but the degradation is always visible."

---

## 6. MEMBER 3 — Chat Page, Composer & App Shell (Frontend)

### Your role in one line

> "I own the entry experience: the chat-style composer, depth selection, suggestions, routing into a run, the app shell with sidebar and command palette, and the browser-level preferences."

### Files you own

| File | What it does |
|---|---|
| `frontend/src/app/layout.tsx` | Root layout, metadata, pre-paint theme script |
| `frontend/src/app/(app)/layout.tsx` | Wraps every page in the app shell |
| `frontend/src/app/(app)/page.tsx` | Home: submit question → start run → redirect |
| `frontend/src/components/ResearchForm.tsx` | Composer, auto-resize, validation, depth picker, suggestions |
| `frontend/src/components/AppShell.tsx` | Sidebar, header, mobile drawer, route titles, health footer |
| `frontend/src/components/CommandPalette.tsx` | ⌘K navigation and quick actions |
| `frontend/src/components/RecentResearch.tsx` | Sidebar recent list |
| `frontend/src/components/ThemeToggle.tsx` | Light / dark toggle |
| `frontend/src/lib/preferences.tsx` | Preferences context, localStorage, theming |
| `frontend/src/app/error.tsx` | Route-level error boundary |
| `frontend/src/app/not-found.tsx` | Global 404 page |

### File-by-file breakdown

#### `frontend/src/app/layout.tsx`

**Purpose:** the root layout. It loads global CSS, sets metadata, provides the preferences context, and applies the saved theme before first paint.

| Symbol | Explanation |
|---|---|
| `metadata` | Page title and description used by Next.js. |
| `THEME_SCRIPT` | Tiny inline script in `<head>` that reads the stored preference and sets the `dark` class before paint, avoiding a light flash. |
| `RootLayout({ children })` | Renders `<html>`/`<body>`, injects the theme script, and wraps children in `PreferencesProvider`. |

#### `frontend/src/app/(app)/layout.tsx`

**Purpose:** one place where the persistent shell is applied to every app route.

| Symbol | Explanation |
|---|---|
| `AppLayout({ children })` | Renders `AppShell` around the route content; stays a server component, keeping the client boundary small. |

#### `frontend/src/app/(app)/page.tsx`

**Purpose:** the home/chat page. It owns submit, error display, and the redirect into a new run.

| Symbol | Explanation |
|---|---|
| `Home()` | Reads preferences, tracks submitting/error state, renders the composer and an error banner. |
| `handleSubmit(question)` | Starts the run with the selected depth, then routes to `/r/<id>`; on failure, shows the backend's message and re-enables the form. |

#### `frontend/src/components/ResearchForm.tsx`

**Purpose:** the reusable composer — used as the hero input on the home page and as the compact follow-up bar on a run page.

| Symbol | Explanation |
|---|---|
| `SUGGESTIONS` | Four example questions with icons and accent colours, used to seed the empty state. |
| `MIN_LENGTH` (10), `MAX_LENGTH` (2000) | Client-side mirror of the server's validation bounds. |
| `ResearchForm({ onSubmit, disabled, compact })` | Owns the query text, auto-resizes the textarea, validates length, and renders either the hero or compact variant. |
| `submit()` | Guards on validity, calls `onSubmit` with the trimmed question, and clears the field. |
| `handleKeyDown(event)` | Enter submits; Shift+Enter inserts a newline. |
| `handleFormSubmit(event)` | Prevents the default form post and delegates to `submit()`. |
| `DepthPicker({ value, onChange, size })` | Segmented Quick / Standard / Deep control with `aria-pressed` states. |

#### `frontend/src/components/AppShell.tsx`

**Purpose:** the persistent frame: sidebar navigation, mobile drawer, header with route title, command palette, and a live provider footer.

| Symbol | Explanation |
|---|---|
| `Logo()` | Inline SVG brand mark with gradients; no image asset needed. |
| `NavLink({ href, active, icon, label, onClick })` | One sidebar link with active styling and `aria-current`. |
| `pageTitle(pathname)` | Maps the current route to a human header title, including the source-reader case. |
| `AppShell({ children })` | Reads pathname and preferences, fetches health once, and renders sidebar, overlay, header, main, and palette. |
| `closeMobile()` | Closes the mobile drawer after navigation. |
| Sidebar behaviour | Desktop collapse state is persisted; below `lg` the sidebar becomes an overlay with a backdrop. |

#### `frontend/src/components/CommandPalette.tsx`

**Purpose:** keyboard-first navigation (⌘K / Ctrl+K) across actions and recent runs, with full arrow-key support.

| Symbol | Explanation |
|---|---|
| `ICONS` | Inline SVG path data for the available commands. |
| `Icon({ children })` | Shared SVG wrapper that standardises size and stroke. |
| `CommandPalette()` | Owns open/query/items/active state, listens for the shortcut and a custom open event, and fetches recent runs when opened. |
| `close()` | Closes the dialog and clears the query. |
| `onKeyDown(event)` | Toggles on ⌘K/Ctrl+K and closes on Escape. |
| `commands` (memo) | Five fixed actions (new, library, settings, theme toggle, copy link) plus one entry per recent run. |
| `filtered` (memo) | Case-insensitive filter over label and hint. |
| `activeIndex` | Clamps the highlight when a filter shortens the list, without a state-syncing effect. |
| `choose(command)` | Closes the palette, then runs the command. |
| `onInputKeyDown(event)` | Arrow keys cycle the highlight; Enter executes the selected command. |

#### `frontend/src/components/RecentResearch.tsx`

**Purpose:** the sidebar's short history list, refreshed on navigation and on a timer so new runs appear without a reload.

| Symbol | Explanation |
|---|---|
| `RecentResearch({ activeId, refreshKey, limit, onNavigate })` | Loads up to `limit` runs, polls every 15 seconds, and highlights the current run. |
| `load()` (inner) | Fetches history, ignores late responses after unmount, and tracks a simple error flag. |
| Render states | Skeleton while loading, error message on failure, empty state, then the list with follow-up marker, status dot, source count, and relative time. |

#### `frontend/src/components/ThemeToggle.tsx`

**Purpose:** a single-button light/dark switch that writes through the preferences context.

| Symbol | Explanation |
|---|---|
| `ThemeToggle({ className })` | Reads the resolved theme, toggles the stored preference, and swaps sun/moon icons with an accessible label. |

#### `frontend/src/lib/preferences.tsx`

**Purpose:** one versioned, device-local preferences store with a hydration-safe read and system-theme resolution.

| Symbol | Explanation |
|---|---|
| `Theme`, `Depth` | Union types for the three theme modes and three depth levels. |
| `Preferences` | The stored shape: theme, depth, citation preview, sidebar open. |
| `STORAGE_KEY` (`ara.prefs.v1`) | Versioned key, so a future shape change can migrate instead of crashing. |
| `DEFAULT_PREFERENCES` | System theme, standard depth, previews on, sidebar open. |
| `DEPTH_OPTIONS` | Maps each depth to a label, an iteration count (0/2/3), and a description. |
| `depthFromIterations(iterations)` | Reverse mapping, used to display which depth a stored run used. |
| `readStored()` | Reads and merges stored preferences, falling back to defaults on any error. |
| `systemIsDark()` | Reads the OS colour-scheme media query. |
| `PreferencesProvider({ children })` | Hydrates after mount via a microtask, tracks OS theme changes, applies the theme class, and persists every update. |
| `usePreferences()` | Context hook that throws if used outside the provider, so misuse fails loudly. |

#### `frontend/src/app/error.tsx`

**Purpose:** route-level error boundary, so one broken page does not blank the whole app.

| Symbol | Explanation |
|---|---|
| `Error({ error, reset })` | Logs the error once and renders a recoverable message with a "Try again" button that calls `reset`. |

#### `frontend/src/app/not-found.tsx`

**Purpose:** the global 404 page for unknown routes.

| Symbol | Explanation |
|---|---|
| `NotFound()` | Static 404 message with a link back to a new research. |

### Say this in the demo (≈50 seconds)

> "The home page is deliberately chat-like: one large composer, Enter to submit, Shift+Enter for a newline, an auto-resizing textarea, and a depth selector.
>
> The important architectural point is that submitting does **not** wait for the research. The client calls `POST /api/research`, gets an id, and immediately routes to `/r/<id>`. That is why the UI never freezes for three minutes, and why every run is shareable by URL.
>
> Validation exists on both sides: the client blocks under 10 characters, and Pydantic enforces the same rule on the server. Depth maps to an iteration count — Quick 0, Standard 2, Deep 3 — and the server clamps it to 0–3.
>
> Preferences are per-device in `localStorage` under one versioned key. They are read **after** mount inside a microtask, so server and client markup match and we do not get hydration errors. The saved theme is also applied by a tiny inline script before first paint, so there is no light flash."

---

## 7. MEMBER 4 — Research Page, Sources, Library & Settings (Frontend)

### Your role in one line

> "I own everything after submission: live run state, the activity timeline, the cited report, the verification panel, the source reader, the library, and settings."

### Files you own

| File | What it does |
|---|---|
| `frontend/src/app/(app)/r/[id]/page.tsx` | Run route, keyed by id |
| `frontend/src/components/ResearchRun.tsx` | Run header, actions, report, sources, follow-up |
| `frontend/src/components/ResearchProgress.tsx` | Live activity timeline |
| `frontend/src/components/ResearchReport.tsx` | Markdown report + citation linkification |
| `frontend/src/components/SourceList.tsx` | Numbered source cards |
| `frontend/src/components/VerificationPanel.tsx` | Trust badge: clean / revised / unavailable |
| `frontend/src/components/StatusBadge.tsx` | Status pill, dot, and label |
| `frontend/src/lib/useResearch.ts` | Live-state hook: load, SSE, polling, cancel |
| `frontend/src/lib/format.ts` | Dates, durations, slug, markdown download |
| `frontend/src/app/(app)/r/[id]/sources/[sourceId]/page.tsx` | Source route |
| `frontend/src/components/SourceReader.tsx` | Full-text reader with prev/next |
| `frontend/src/app/(app)/library/page.tsx` | Library route |
| `frontend/src/components/Library.tsx` | Filters, search, rename, delete, pagination |
| `frontend/src/app/(app)/settings/page.tsx` | Settings route |
| `frontend/src/components/SettingsPanel.tsx` | Preferences + runtime facts |

### File-by-file breakdown

#### `frontend/src/app/(app)/r/[id]/page.tsx`

**Purpose:** a thin async route that reads the dynamic id and mounts the run component with a key, so a new run gets fresh state.

| Symbol | Explanation |
|---|---|
| `ResearchPage({ params })` | Awaits `params`, then renders `<ResearchRun key={id} id={id} />`; the key forces a full remount when the id changes. |

#### `frontend/src/components/ResearchRun.tsx`

**Purpose:** the run page's composition root — header, actions, progress, verification, report, sources, and the follow-up composer.

| Symbol | Explanation |
|---|---|
| `ResearchRun({ id })` | Consumes `useResearch`, derives running/completed/failed flags, and renders the correct states. |
| `copyLink()` | Copies the current URL to the clipboard with a short "Link copied" confirmation. |
| `handleFollowUp(question)` | Starts a child run with `parentResearchId`, then routes to it. |
| `handleRetry()` | Starts a fresh run with the same question after a failure or cancellation. |
| `isRunning / isCompleted / isFailed / isCancelled` | Status predicates that drive which controls and panels are shown. |
| `title`, `depth`, `duration` | Derived display values: display title or question, depth label from stored iterations, and human duration. |
| Render states | Skeleton while loading, a 404 state, a load-failure state, then the full page with the follow-up composer pinned at the bottom. |

#### `frontend/src/components/ResearchProgress.tsx`

**Purpose:** the live activity timeline — the visible proof that the agent is actually working.

| Symbol | Explanation |
|---|---|
| `STAGE_LABEL` | Human phrasing for every stage (e.g. `deciding` → "Judging the evidence"). |
| `SPINNER_STAGES` | Stages that mean "still working", used to decide whether to show a spinner. |
| `ResearchProgress({ events, reconnecting, failed, cancelled, initiallyCollapsed })` | Renders a collapsible timeline with a status icon, step count, and reconnect badge. |
| Auto-scroll effect | Scrolls to the newest event when not collapsed, so the latest step stays visible. |
| `current`, `busy`, `isFinished` | Derives the header icon and spinner state from the last event and the terminal flags. |
| Timeline rendering | One row per event with a connector line, the message, the human stage label, and a clock time; `aria-live` announces updates. |

#### `frontend/src/components/ResearchReport.tsx`

**Purpose:** renders the markdown answer and turns every citation into a real, inspectable link.

| Symbol | Explanation |
|---|---|
| `CITATION` | Regex matching full-width citation brackets emitted by some models in the body. |
| `ResearchReport({ researchId, title, markdown, sources, citationPreview })` | Renders the report header, copy button, honesty note, and markdown body with custom renderers. |
| `copyAnswer()` | Copies the raw markdown to the clipboard with a temporary confirmation. |
| `linkifyCitations(children, sources, researchId, showPreview)` | Walks text nodes, replaces each `[n]` with a badge linking to the source reader, and optionally renders a hover/focus preview card. |
| Custom `a` renderer | Opens external links in a new tab with `rel="noopener noreferrer"`. |

#### `frontend/src/components/SourceList.tsx`

**Purpose:** the numbered evidence grid under the report, in the same order as the citations.

| Symbol | Explanation |
|---|---|
| `sourceAnchor(id)` | Builds the stable DOM id used for deep links to a source card. |
| `SourceList({ researchId, sources })` | Renders nothing when empty; otherwise a responsive grid of source cards. |
| Card content | Citation number, domain, source type, a "Snippet" warning when only a snippet exists, title, snippet excerpt, URL, and Read/Original links. |

#### `frontend/src/components/VerificationPanel.tsx`

**Purpose:** turns the verifier's stored verdict into one honest, visible trust signal.

| Symbol | Explanation |
|---|---|
| `VerificationPanel({ note, revised, available, removedClaims })` | Renders nothing when there is nothing to say; otherwise picks one of three tones. |
| Unavailable tone | Amber: verification could not run, so the draft shipped unchecked. |
| Revised tone | Blue: claims were checked and adjusted, with the count removed or qualified. |
| Clean tone | Green: claims were checked and supported. |

#### `frontend/src/components/StatusBadge.tsx`

**Purpose:** consistent colour and wording for the five run statuses, tolerant of unexpected values from legacy rows.

| Symbol | Explanation |
|---|---|
| `STYLES` | Per-status dot and chip classes, including a pulsing dot for `running`. |
| `styleFor(status)` | Looks up a style and falls back to the neutral `queued` look for unknown values, so a page cannot crash. |
| `StatusDot({ status })` | Small coloured indicator, hidden from screen readers. |
| `StatusLabel({ status })` | Human label; `running` is shown as "Researching". |
| `StatusBadge({ status, className })` | Pill combining dot and label. |

#### `frontend/src/lib/useResearch.ts`

**Purpose:** the single source of live run state — initial load, SSE, a polling backstop, cancellation, and final reload.

| Symbol | Explanation |
|---|---|
| `TERMINAL` | The three statuses that end a run. |
| `POLL_MS` (2500) | Polling interval used as the transport backstop. |
| `ResearchState` | The hook's public shape: status, events, sources, loading, notFound, error, reconnecting, stopping. |
| `useResearch(id)` | Owns all run state and wires loading, streaming, polling, cancellation, and cleanup. |
| `stopTransports()` | Closes the SSE connection and clears the polling interval. |
| `syncActivity(activity)` | Adopts the server's timeline only if it is at least as long, so a stale fetch cannot erase newer events. |
| `reload(researchId)` | Fetches status, sources, and activity in parallel, then applies them if the component and id are still current. |
| `finish(researchId)` | Stops transports and reloads the final payload once a run is terminal. |
| `startPolling(researchId)` | Polls status and activity every 2.5 s, detects cancellation, and finishes on a terminal status. |
| `connect(researchId)` | Opens SSE and handles stage events, completion, errors, and transport disconnects. |
| Effect | Resets state, does the initial parallel load, then starts streaming and polling only if the run is still active; cleans up on unmount. |
| `stop()` | Calls the cancel endpoint and finishes immediately if the server reports a terminal status. |
| `appendEvent(prev, event)` | Appends an event unless it duplicates the last one, preventing double-rendered stages. |

#### `frontend/src/lib/format.ts`

**Purpose:** all display formatting in one place, with UTC handling that survives SQLite dropping the timezone suffix.

| Symbol | Explanation |
|---|---|
| `parseTimestamp(iso)` | Parses a timestamp, treating a bare value as UTC and returning null on invalid input. |
| `formatRelativeDate(iso)` | "just now", "12m ago", a clock time for today, "yesterday", or a short month/day. |
| `formatDateTime(iso)` | Absolute date and time, omitting the year when it is the current year. |
| `formatClock(iso)` | Hour/minute/second used by the activity timeline. |
| `formatDuration(start, end)` | Human duration, using "now" when the end is missing. |
| `dateGroupLabel(iso)` | Library grouping: Today, Yesterday, earlier this week/month, or month and year. |
| `slugify(value)` | Safe filename stem derived from a title. |
| `downloadMarkdown(title, markdown)` | Creates a blob and triggers a client-side `.md` download, then revokes the URL. |

#### `frontend/src/app/(app)/r/[id]/sources/[sourceId]/page.tsx`

**Purpose:** the deep-linkable source route; keying on both ids guarantees fresh state when moving between sources.

| Symbol | Explanation |
|---|---|
| `SourcePage({ params })` | Awaits both params and renders `<SourceReader key={"<id>-<sourceId>"} … />`, so prev/next navigation remounts cleanly. |

#### `frontend/src/components/SourceReader.tsx`

**Purpose:** the evidence view — the full extracted text behind one citation, with navigation to its neighbours.

| Symbol | Explanation |
|---|---|
| `SourceReader({ researchId, sourceId })` | Fetches the detail and the sibling list in parallel and handles loading, not-found, and error states. |
| Fetch effect | Cancels on unmount, distinguishes 404 from network failure, and stores both the detail and the ordered list. |
| `position`, `previous`, `next` | Locate the current source in citation order to build the prev/next cards. |
| `hasFullText` | Distinguishes a scraped page from a snippet-only source, which drives the warning and the rendering path. |
| Render | Breadcrumb ("Source n of m"), citation badge, type/domain/method chips, title, original link, body (markdown or snippet), and prev/next navigation. |

#### `frontend/src/app/(app)/library/page.tsx`

**Purpose:** thin route wrapper for the library.

| Symbol | Explanation |
|---|---|
| `LibraryPage()` | Renders `<Library />`. |

#### `frontend/src/components/Library.tsx`

**Purpose:** the management view for saved runs: filter, search, paginate, rename, delete.

| Symbol | Explanation |
|---|---|
| `PAGE_SIZE` (20), `FILTERS` | Page size and the five status filter options. |
| `Library()` | Owns items, pagination, filter, debounced search, rename/delete state, and errors. |
| Debounce effect | Waits 300 ms after typing before applying the search, avoiding a request per keystroke. |
| `load()` | Fetches the first page and uses a request-sequence number so a slow older response cannot overwrite a newer one. |
| `loadMore()` | Appends the next page and keeps the existing rows if it fails. |
| `startRename(item)` | Enters inline edit mode seeded with the current title. |
| `saveRename(item)` | Saves a trimmed title or clears it, then updates the row locally. |
| `remove(item)` | Confirms, deletes on the server, and removes the row plus decrements the total. |
| `rows` | Precomputes each row's date group and whether it starts a new group, so rendering stays declarative. |

#### `frontend/src/app/(app)/settings/page.tsx`

**Purpose:** thin route wrapper for settings.

| Symbol | Explanation |
|---|---|
| `SettingsPage()` | Renders `<SettingsPanel />`. |

#### `frontend/src/components/SettingsPanel.tsx`

**Purpose:** all user preferences plus a read-only view of what the deployment is actually running.

| Symbol | Explanation |
|---|---|
| `THEMES`, `DEPTHS` | Option lists for the theme and depth controls. |
| `Section({ title, description, children })` | Consistent titled section layout. |
| `Switch({ checked, onChange, label })` | Accessible toggle implemented as a `role="switch"` button. |
| `SettingsPanel()` | Reads preferences, fetches health once, and renders appearance, depth, reading, runtime, and data sections. |
| Appearance | Light / dark / system cards with `aria-pressed`, showing the currently resolved theme. |
| Research depth | Three cards plus a compact `DepthPicker`, explaining the follow-up round count. |
| Reading | Citation-preview toggle. |
| Runtime | Renders model, search, extraction, limits, environment, version, and key status from `/api/health`. |
| Local data | Confirms preferences are browser-only and offers a reset. |

### Say this in the demo (≈60 seconds)

> "The run page is the hardest part of the frontend because it has to stay correct while data arrives from two directions.
>
> `useResearch` does three things in parallel on load: status, sources, and activity. If the run is not terminal, it opens **SSE** for low-latency stage events **and** starts a **2.5-second polling backstop**. The polling exists because the Next.js development rewrite buffers SSE — without it the UI would look frozen. So we degrade gracefully instead of depending on one transport.
>
> Events are deduplicated by last stage plus message, and the activity list is never allowed to shrink, so a stale in-flight fetch cannot erase a newer event.
>
> When the run completes we reload the final payload. Then the verification panel shows one of three states — clean, revised with a claim count, or unavailable — and every `[n]` in the report maps to a numbered source. The source reader is a separate deep-linkable route that fetches the full text, because the list endpoint deliberately omits it."

---

## 8. Live demo script (5–6 minutes)

**Before the viva:** pre-run one completed question so you always have a finished report. Start a second live run at minute 0 in a second tab, so it is mid-pipeline when you need it.

| Time | Who | Action |
|---|---|---|
| 0:00 | M1 | One-line pitch + problem/solution (Section 1) |
| 0:40 | M3 | Home page: type a question, show depth selector, press Enter |
| 1:00 | M3 | Point out the instant redirect and the shareable URL |
| 1:10 | M2 | Narrate the pipeline: planning → searching → reading → deciding |
| 2:00 | M4 | Activity timeline: stage messages, step count, live status |
| 2:30 | M1 | Show the cancel button and explain cooperative cancellation |
| 3:00 | M2 | Show planned-query chips; explain replanning when a gap appears |
| 3:40 | M4 | Open the completed report: verification panel, citations, sources |
| 4:20 | M4 | Open one source: full text vs snippet-only badge, prev/next |
| 4:40 | M3 | Follow-up composer → child run shows the "Follow-up" badge |
| 5:00 | M4 | Library: filter, search, rename; Settings: runtime facts |
| 5:30 | M1 | Close with architecture + the four numbers |

**Fallback if the network dies:** use the pre-run session, then show `docs/evaluation.md` and the `eval-live-*.csv` artifacts. Never debug live for more than 20 seconds — switch to the recorded evidence.

---

## 9. Question routing — who answers what

| If the examiner asks about… | Answers | Hand-off line if it is not yours |
|---|---|---|
| Architecture overview, stages, why agentic | M2 | "That is the orchestration layer — my teammate." |
| Planning prompt, search, extraction, context caps | M2 | — |
| Verification, hallucination, evaluation numbers | M2 | — |
| API design, statuses, database, cascades | M1 | — |
| Background execution, SSE mechanics, cancellation | M1 | — |
| Config, keys, deployment, logs | M1 | — |
| Home page, composer, validation, depth, shell | M3 | — |
| Preferences, theme, hydration, accessibility | M3 | — |
| Run page, live state, polling fallback | M4 | — |
| Report rendering, citations, verification UI | M4 | — |
| Source reader, library, settings | M4 | — |
| "Is this really AI?" / limitations / future work | M1 leads, M2 supports | — |

**Rule:** never guess outside your area. Say *"That part is owned by X — X, do you want to take it?"* Examiners reward a team that knows its boundaries.

---

## 10. Pre-viva verification (run the day before)

Backend tests:

```
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: all passing. Note the exact count - if it is not 169, use the real number in the viva.

Frontend quality gates:

```
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

Start both services and check health:

```
cd backend
uvicorn app.main:app --reload
```

Open `http://localhost:8000/api/health` and confirm `"configured": true`.

Then run one complete question and open its source reader. If that works, the demo works.

---

## Appendix A — Glossary (use precise words)

| Term | Meaning in this project |
|---|---|
| **Agentic loop** | A pipeline whose control flow can move backwards based on model judgement |
| **Coverage reviewer** | The LLM that judges whether evidence is sufficient |
| **Replanning** | Re-invoking the planner with the identified gap as feedback |
| **Fail-open** | On component failure, continue with available evidence and record it |
| **Grounding** | Restricting generation to retrieved source text |
| **Verifier** | Independent LLM pass that removes unsupported claims |
| **Citation integrity** | Every `[n]` resolves to a stored source; no URL outside the sources table |
| **SSE** | Server-Sent Events, one-way streaming over HTTP |
| **Cooperative cancellation** | A flag checked at stage boundaries instead of killing a process |
| **Append-only activity log** | Rows are only added, never edited — used as the change signal |
| **Idempotent** | Calling it twice has the same effect as calling it once (cancel) |

## Appendix B — File map for quick reference

```
backend/app/
  main.py                  app + routers + startup schema sync
  api/research.py          start, status, stream, cancel, rename, delete, activity
  api/sources.py           source list/detail, history
  api/health.py            runtime facts
  services/research.py     the workflow + adaptive loop + memory
  services/planning.py     query planning / replanning
  services/search.py       Tavily
  services/extraction.py   Firecrawl + snippet fallback
  services/coverage.py     evidence sufficiency reviewer
  services/report.py       draft, revise, citations
  services/verification.py claim verification
  services/llm.py          provider wrapper
  database/models.py       4 tables + statuses
  database/database.py     engine + session factories
  database/migrations.py   in-place schema sync
  core/config.py           all bounds and keys
  core/exceptions.py       typed errors
  core/logging.py          structured logging

frontend/src/
  app/layout.tsx                     root layout + pre-paint theme
  app/error.tsx                      error boundary
  app/not-found.tsx                  global 404
  app/(app)/layout.tsx               app shell wrapper
  app/(app)/page.tsx                 home / composer
  app/(app)/r/[id]/page.tsx          run page
  app/(app)/r/[id]/sources/[id]/...  source reader
  app/(app)/library/page.tsx         library
  app/(app)/settings/page.tsx        settings
  components/AppShell.tsx            sidebar, header, palette
  components/ResearchForm.tsx        composer + depth picker
  components/ResearchRun.tsx         run orchestration
  components/ResearchProgress.tsx    timeline
  components/ResearchReport.tsx      report + citations
  components/SourceReader.tsx        full text
  components/Library.tsx             filters, rename, delete
  components/SettingsPanel.tsx       preferences + runtime
  lib/useResearch.ts                 live state hook
  lib/preferences.tsx                localStorage prefs
  lib/api.ts                         typed API client
  lib/format.ts                      formatting helpers
  types/research.ts                  shared contract types
```
