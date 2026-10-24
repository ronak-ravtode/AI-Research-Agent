# AI Research Agent

A cited, agentic web-research assistant. The user asks a research
question; the backend plans searches, reads live web pages, decides
whether the evidence is enough (and follows up on gaps when it is
not), writes a cited report, checks every claim against the retrieved
material, and (optionally) reuses the memory of an earlier run when
answering a follow-up.

- **Frontend:** Next.js 16 (App Router), TypeScript, Tailwind CSS
- **Backend:** FastAPI, SQLAlchemy async, PostgreSQL (Supabase or any Postgres)
- **Providers:** Groq (`openai/gpt-oss-120b`) · Tavily (search) · Firecrawl (page extraction)

## How one run works

```
User question
  |
  v
[planning] --------- plan search queries (Sequenced thinking / LLM)
  |
[searching] -------- Tavily web search, initial results
  |                  (one broader search if too few results)
[reading] ---------- Firecrawl full-text extraction
  |                  (one broader search + re-read if only snippets)
[deciding] --------- Coverage reviewer = "is the evidence enough?"
  |                  -> yes: continue
  |                  -> no: planner is RE-INVOKED with the gap as feedback
  |                      (reviewer's suggested queries are the fallback)
  |                      -> bounded loop, max 2 rounds (MAX_AGENT_ITERATIONS)
[writing] ---------- Draft with numbered [n] citations
  |
[verifying] -------- Verifier agent = "does every claim have a source?"
  |                  unsupported claims removed or qualified
  |                  -> if claims were removed: draft goes BACK to the writer
  |                     for a critique-driven rewrite, then re-verified
  |                     (bounded, MAX_REWRITE_ROUNDS = 1)
  v
[complete] --------- Report + sources + activity log persisted
```

Every stage transition is persisted, streamed over SSE, and mirrored
to polling so the UI never freezes silently.

## Features

- **Agentic loop, bounded:** a coverage reviewer can trigger follow-up
  searches. Each round **re-invokes the planner with the reviewer's
  gap feedback** (reviewer's own query suggestions are the fallback),
  capped by `MAX_AGENT_ITERATIONS` (default 2) so cost is finite.
- **Verifier⇄writer negotiation:** when the verifier removes
  unsupported claims, the draft goes back to the writer (`report.revise`)
  for a critique-driven rewrite, which is then re-verified. Bounded by
  `MAX_REWRITE_ROUNDS` (default 1).
- **Memory & follow-ups:** from a completed report you can ask a
  follow-up; the child run reuses the parent's question, answer, and
  top `MAX_CONTEXT_SOURCES` sources (parents are never mutated, and all
  reused sources are copied into the child so citations stay valid).
- **Transparent plan:** planned queries are stored with the session,
  sent to the client, and shown as chips; activity logs expose every
  decision.
- **Thin evidence fallback:** if extraction leaves only snippet-level
  pages, one broader search on the original question is attempted and
  only fresh URLs are read.
- **Citation integrity:** reports pad/adjust citations; the live eval
  asserts no dangling references and no invented URLs.
- **Visual quality gate:** when manually asked for a visual-quality
  review, run the web-design-guidelines skill over the rendered page
  (screenshots first), not just a static read of the JSX.

## Architecture

```
frontend (Next.js)             backend (FastAPI)
  page.tsx                       api/research.py   -> research.py  (orchestrator)
  ResearchProgress (SSE)         api/sources.py    -> report.py    (draft + finalize)
  SourceList                     services/planning.py   (query planner)
  History                        services/search.py     (Tavily)
  ResearchReport                 services/extraction.py (Firecrawl)
                                 services/coverage.py   (evidence-gap reviewer)
                                 services/verification.py (critic/corrector)
                                 database/models.py  (sessions, reports, sources, activity)
```

Length caps live in `backend/app/core/config.py`; each stage degrades
softly (snippet fallback, skip verification note, fail-open reviewers)
instead of failing the whole run.

## Setup

1. Copy `backend/.env.example` to `backend/.env` and fill in
   `GROQ_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, and
   `DATABASE_URL` (any asyncpg Postgres URI).
2. Backend:

   ```
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

   SQLAlchemy creates the tables on startup.
3. Frontend:

   ```
   cd frontend
   npm install
   npm run dev
   ```

   `next.config.ts` proxies `/api/*` to the backend; provider keys
   never reach the browser.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/research` | Start a run. Optional `parent_research_id` makes it a memory-backed follow-up. |
| GET | `/api/research/{id}` | Status, stage, planned queries, parent link, report when complete. |
| GET | `/api/research/{id}/sources` | All sources for the run. |
| GET | `/api/research/{id}/activity` | Stage-by-stage activity log. |
| GET | `/api/research/{id}/stream` | SSE: `stage` / `complete` / `error` / `timeout`. |
| GET | `/api/history` | Recent runs (with follow-up links). |

## Tuning

| Env var | Default | Meaning |
| --- | --- | --- |
| `MAX_AGENT_ITERATIONS` | 2 | Max follow-up rounds driven by the coverage reviewer (planner re-invoked each round). |
| `MAX_REWRITE_ROUNDS` | 1 | Verifier⇄writer negotiation rounds when the verifier flags a draft. |
| `MAX_CONTEXT_SOURCES` | 3 | Parent sources reused in a follow-up. |
| `MAX_CONTEXT_CHARS` | 6000 | Cap on prior Q&A context handed to planning/drafting. |
| `MAX_SEARCH_QUERIES` | 4 | Queries per search call. |
| `MAX_SEARCH_RESULTS` | 8 | Results per search call. |
| `MAX_EXTRACT_SOURCES` | 5 | Pages actually read per extraction batch. |
| `MAX_SOURCE_CHARS` / `MAX_TOTAL_SOURCE_CHARS` | 6000 / 20000 | Per-page / prompt budget caps. |

## Evaluation

`backend/scripts/evaluate.py` runs a small live suite against the real
providers: every run must reach `completed` with 2+ sources, generate a
report, and pass citation-integrity checks (no dangling `[n]`, no URLs
not present in the sources table). Set a live `DATABASE_URL` first, then:

```
cd backend
python scripts/evaluate.py
```

Results are appended to `eval-live.csv`. See `docs/evaluation.md` for
the criteria and the agentic-loop checks (bounded iterations, follow-up
memory, verifier revisions).

## Tests

```
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

The suite stubs every provider; DB tests run on SQLite. Frontend
quality gates: `npm run lint`, `npx tsc --noEmit`, `npm run build`.

## Docs

- Design spec (agentic upgrade): `docs/superpowers/specs/2026-10-23-agentic-upgrade-design.md`
- Original workspace design: `docs/superpowers/specs/2026-10-16-simplified-research-workspace-design.md`
- Evaluation details: `docs/evaluation.md`
