# Evaluation

Two layers: an offline unit suite (provider-stubbed, deterministic)
and a live harness against the real providers.

## 1. Offline suite

```
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Current state: **144 passed**. Covering:

| Layer | Focus |
| --- | --- |
| pipeline contract (`test_research_service.py`) | stage order incl. `deciding`/`verifying`, planned-query persistence, bounded agent loop (exactly 2 coverage rounds when evidence never suffices), refinement-search failure does not fail the run ("continuing with the available evidence"), snippet-only fallback triggers one broader search, follow-up memory: parent question + answer reach planner and drafter, **mid-loop replanning**: planner is re-invoked with the reviewer's gap feedback (falls back to reviewer queries on planner error or repeated queries), **verifier⇄writer negotiation**: a flagged draft goes back to `report.revise` and is re-verified, bounded at 1 rewrite round |
| structured logging (`test_logging.py`) | non-ASCII agent messages (e.g. non-breaking hyphens) never crash the Windows console stream |
| coverage reviewer (`test_coverage.py`) | fail-open (`sufficient=True` on LLM errors/malformed payload), dedupe vs tried queries, cap on follow-up count |
| verifier (`test_verification.py`) | fail-open (draft kept), removes unsupported claims, note passthrough |
| citations (`test_report.py`) | dangling `[n]` padded to valid ranges, references built only from stored sources, prior-context stripping of old citation brackets |
| API (`test_api.py`) | parent validation (malformed 400, missing 404, unfinished 400), child creation, status exposes `planned_queries` + `parent_research_id`, history carries parent links |
| contract (`test_contract.py` etc.) | failure messages, stage serialization |

Frontend gates: `npm run lint`, `npx tsc --noEmit`, `npm run build`.

## 2. Live harness

`backend/scripts/evaluate.py` runs 8 real research questions end to
end (no mocks) and reports per run:

- `status` — must be `completed`
- `sources` / `full_pages` — evidence the extractor really read pages,
  not just snippets
- `citations` / `dangling_citations` — every `[n]` inside the answer
  must point at a stored source
- `invented_urls` — any URL in the answer body that is not in the
  sources table (the references section is backend-built, so any
  extra URL is a hallucination)

Exit code is non-zero unless every run completed with zero dangling
citations and zero invented URLs.

### Running it

1. Fill `backend/.env` with real provider keys **and a reachable
   `DATABASE_URL`** (the harness writes row data; a dead Supabase
   project fails with DNS errors — common fix here: point it at local
   PostgreSQL).
2. Then:

```
cd backend
python scripts/evaluate.py --csv ..\eval-live.csv
```

### Last live results

**Agentic pipeline, live re-run (2026-10-23, local Postgres, Groq
`openai/gpt-oss-120b` + Tavily + Firecrawl): 8/8 completed, 0 dangling
citations, 0 invented URLs.** Baseline average ≈ 174–176 s per run,
~6 stored sources each. Artifacts: `eval-live-agentic.csv` (first 2
questions) and `eval-live-agentic-rest.csv` (remaining 6); the older
`eval-live.csv` recorded the pre-agentic baseline (8/8, average ≈ 60 s
per run — slower now because the extra reviewer/verifier/replan agent
calls are real).

Agent behaviour actually observed in the traces (not just in tests):

- **Deciding stage**: the coverage reviewer returned reasoned verdicts
  ("The sources together explain technical, operational causes…").
- **Bounded follow-up loop**: on one question the reviewer judged the
  evidence thin — the runner followed up on reviewer-suggested queries
  across two rounds (the configured cap) and then wrote anyway.
- **Mid-loop replanning**: follow-up rounds re-consulted the planner
  with the gap feedback before falling back to reviewer queries.
- **Verifier⇄writer negotiation, live**: three runs had claims
  removed/qualified by the verifier ("FactScore improvement claim for
  RAG was unsupported", "removed unsupported 'far more effective' than
  cramming", "removed unsupported link to the 2022 Pakistan floods");
  the writer critique-rewrote, and the rewritten answer was
  re-verified before shipping.
- **Fail-open behaviour, live**: one coverage call degraded (JSON
  decode error) → the run continued and completed from available
  evidence; a rate-limit retry fired inside the verifier and still
  produced a completed run.
- A schema-sync fix was applied first (the harness now runs
  `sync_schema`, so an older database gets `parent_session_id` /
  `planned_queries` added automatically).
