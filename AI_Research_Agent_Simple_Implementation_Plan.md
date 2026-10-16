# AI Research Agent — Simple Implementation Plan

## 1. Goal

Turn the existing application into a straightforward research website. A user enters almost any research question; the backend searches the web with Tavily, opens useful pages with Firecrawl, asks Groq to synthesize the collected material, and returns a readable answer with numbered citations and source links.

The website should look and feel like a research workspace: while research is running, it shows what stage is happening, which sources were found, and when the report is ready. It should be understandable in a project demonstration without looking like an over-engineered multi-agent platform.

**Important:** citations and source links make an answer easier to check; they do not guarantee that every claim is true. The UI must let users open the original sources.

## 2. Keep the Existing Stack

Use what is already in the repository instead of starting over:

- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS v4.
- **Backend:** Python, FastAPI.
- **LLM:** Groq API.
- **Web search:** Tavily API.
- **Page extraction:** Firecrawl API.
- **Persistence:** Supabase PostgreSQL.
- **Progress:** Server-Sent Events (SSE), using the existing API route.

### Simplify

- Keep LangGraph only if it is already working; reduce the graph to a small, understandable workflow (see Section 3). Do not add more agents.
- Keep the current Next.js API rewrite/proxy and existing frontend route unless there is a concrete reason to change them.
- Use PostgreSQL for research history and results.
- Reuse existing tests and API schemas where practical.

### Stop building for the simple version

Do not spend time on OpenAI embeddings, pgvector memory, semantic recall, separate confidence scoring, a separate conflict-detector agent, complex source-quality formulas, a large multi-agent architecture, authentication, file uploads, background-worker infrastructure, or elaborate analytics dashboards. Remove these only after checking for live dependencies; do not delete working functionality blindly.

This scope still demonstrates a multi-step research workflow: query planning, external tool use, source extraction, answer synthesis, citations, and observable progress. It is not just a chat prompt.

## 3. The Simple Research Workflow

Use four main stages. These can be four LangGraph nodes or four clearly separated Python functions called by one orchestration service.

```text
User question
    ↓
1. Plan search queries
    ↓
2. Search web with Tavily
    ↓
3. Extract selected pages with Firecrawl
    ↓
4. Generate a cited answer with Groq
    ↓
Save answer + sources + status
    ↓
Display research report in the frontend
```

### Stage 1 — Plan the search

- Validate that the question is not empty.
- Use Groq to produce 2–4 concise search queries for broad or multi-part questions.
- If planning fails, use the original question as the search query instead of failing the whole research run.
- Store the queries and show a short activity message such as `Breaking the question into search queries`.

### Stage 2 — Search with Tavily

- Run the planned queries through Tavily.
- Deduplicate results by normalized URL.
- Keep a manageable set, normally 5–8 results total.
- Retain the title, URL, snippet/content, domain, and search score returned by Tavily.
- Show the number of results found in the activity panel.

### Stage 3 — Extract pages with Firecrawl

- Select the best 3–5 relevant URLs from the search results.
- Fetch readable page content with Firecrawl.
- If a page cannot be scraped, fall back to its Tavily snippet/content and mark that source as `snippet only`.
- Remove empty pages and duplicate URLs.
- Limit text sent to the LLM so prompts do not grow without bounds. Use a configurable per-source limit and retain the source ID next to every piece of content.
- Label source types accurately. Do not call every web result a research paper; use terms such as `Research paper`, `Official documentation`, `Government`, `News`, or `Web article` only when the source supports that classification.

### Stage 4 — Generate the report with Groq

Give Groq the user's question and the extracted source material. Ask for a structured response containing:

- A direct answer / executive summary.
- Key findings, grouped into short sections where useful.
- Important limitations or disagreements found in the provided material, if any.
- Numbered citations tied only to source IDs supplied to the model.
- A short conclusion.

**Citation rule:** the model must not invent URLs, titles, or citation numbers. The backend maps cited source IDs to the actual stored source records. Any citation that cannot be mapped to a retrieved source must be removed or flagged before the report is shown.

If the model cannot support a claim from the retrieved material, it should qualify the statement or say the available sources do not establish it. Do not claim the result is guaranteed accurate.

### Optional fallback

Keep one simple fallback only: if search returns too few usable results or most extracted pages are empty, run one broader Tavily search using the original question. Avoid a complex autonomous loop with several agents and confidence judges.

## 4. Research-Style Frontend

Build a clean reading and research interface, not a complex admin dashboard.

### Main screen layout

- **Header:** `AI Research Assistant` with a small subtitle such as `Web research with cited sources`.
- **Question input:** large textarea with a clear `Start research` button. Enter should not accidentally submit multiline text; use an explicit button or Ctrl/⌘+Enter.
- **Research activity:** a compact vertical timeline that updates as the backend progresses.
- **Sources area:** source cards showing title, domain, source type, retrieval status, and an `Open source` link.
- **Report area:** the final answer in readable sections with inline `[1]`, `[2]` citations that open or scroll to the matching source.
- **History:** a small list of previous research questions, status, and date. Selecting one opens the saved result.

### Activity timeline examples

Show clear, user-facing events such as:

1. `Planning the search`
2. `Searching the web with Tavily`
3. `Found 7 possible sources`
4. `Reading selected pages`
5. `Preparing the cited answer`
6. `Research complete`

Display the event time and current status. Show real events from the backend; do not fake a detailed activity stream or display internal chain-of-thought. Progress messages should describe actions and results, not private reasoning.

### Report presentation

- Clear report title generated from the user's question.
- Short answer first, followed by findings and conclusion.
- Inline citations linked to a `Sources` section.
- For each source, show title, domain, source type, optional publication date, and an external link.
- Provide `Copy answer` and `Open source` actions if they can be implemented simply.
- Render report content safely as Markdown. Do not enable arbitrary HTML from model output.

### UI states

Handle these states explicitly:

- Idle: prompt input and sample questions.
- Running: progress indicator, current step, and sources as they arrive if available.
- Completed: report and source list.
- Failed: readable error and a `Try again` action.
- Empty history: friendly empty state.
- Reconnecting SSE: show `Reconnecting to research updates…`; continue fetching session status as a fallback.

Do not create separate pages for every report section. One research page with tabs or anchored sections is enough.

## 5. Small Backend API

Retain the current endpoints if they already work. The simple version needs these capabilities:

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Check that the backend is running. |
| `POST /api/research` | Create a session and start a research run; return the research ID immediately. |
| `GET /api/research/{id}` | Return status, current stage, question, and report when available. |
| `GET /api/research/{id}/stream` | Stream progress events using SSE. |
| `GET /api/research/{id}/sources` | Return retrieved sources. |
| `GET /api/history` | Return a limited list of previous sessions. |

A separate report endpoint is optional if the session endpoint already returns the report. Avoid creating routes that duplicate the same data.

### Simple progress implementation

The existing SSE implementation polls the session every two seconds. That is acceptable for this project if it is made reliable:

- Persist `status`, `current_stage`, `progress_message`, and `updated_at` on the research session.
- Update those fields when each actual stage starts or completes.
- Have SSE send an event only when the status/stage/message changes, plus keep-alive comments when needed.
- Send a final `complete` or `error` event and close the stream.
- The frontend must close EventSource on completion, failure, or leaving the research page.
- Do not leave the UI in a permanent running state if the stream reports an error.

Do not build Redis, Celery, WebSockets, or a separate event service for this implementation.

## 6. Simple Data Model

Use the existing ORM tables when possible. The minimal data that must be saved is:

### `research_sessions`

- `id`
- `query`
- `status` (`queued`, `running`, `completed`, `failed`)
- `current_stage`
- `progress_message`
- `created_at`, `updated_at`, `completed_at`
- `error_message` (safe, user-readable message; no secrets or raw stack trace)

### `sources`

- `id`, `research_id`
- `title`, `url`, `domain`
- `source_type`
- `snippet` or short extracted summary
- `retrieval_method` (`firecrawl` or `tavily_snippet`)
- `retrieved_at`

### `reports`

- `id`, `research_id`
- `title`
- `answer_markdown`
- `created_at`

Keep a research task or activity table only if it is already useful for history/progress. Avoid storing redundant copies of the same report fields. Do not make a pgvector/embedding table part of the critical path.

## 7. Error Handling and API Keys

- Keep `GROQ_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, and database credentials on the backend only.
- Never prefix provider secrets with `NEXT_PUBLIC_`, send them to the browser, or include them in logs.
- Read keys through backend environment/configuration and validate required keys at startup or before a run.
- Handle search timeout, scrape failure, empty search results, LLM errors, database errors, cancellation/disconnect, and invalid research IDs.
- A Firecrawl failure for one source should not necessarily fail the entire research session; use its Tavily snippet where available.
- Do not swallow all exceptions and then report success. Save a failed status and a safe error message, log the exception server-side, and ensure the frontend receives a final error event.
- Use request timeouts and limit the number of URLs, page length, search queries, and LLM input size.
- Make sure the backend only fetches URLs returned by the search provider. If accepting arbitrary URLs is added later, validate them to reduce SSRF risk.

## 8. What to Simplify in the Existing Code

Make these changes incrementally, keeping tests green after each group of edits.

1. **Research graph:** reduce the eight-node graph to a small plan → search → extract → write workflow. If LangGraph adds more maintenance than value, keep those same stages as ordinary Python functions behind one `ResearchService`; do not maintain two orchestration systems.
2. **Remove dead agent paths:** stop calling or delete the separate confidence and conflict-detector agents if the UI and report no longer depend on them. The answer may mention an observable disagreement between sources when the provided evidence clearly shows one, but do not add another agent just to detect it.
3. **Embeddings and memory:** remove the unused embedding API configuration, orphaned memory service, and pgvector setup from the runtime path. Preserve database data; do not run destructive migrations without checking existing users/data.
4. **Citations:** ensure the report contains citation references that map to real stored source IDs. Remove the unused citation block if it is not part of the final report design.
5. **Persistence:** write the complete report to one canonical report field instead of storing only a 500-character summary. Save sources before marking the session completed.
6. **SSE:** update stage/status fields from the actual workflow; send only changed events; handle both `complete` and `error` in the frontend.
7. **Errors:** replace blanket exception swallowing with explicit failed-session persistence and safe API/SSE errors.
8. **Frontend form:** prevent double submission while a run is active; reset the state on a new run; handle failed sessions with a proper error panel rather than a bare 404.
9. **UI content:** remove empty/confusing confidence widgets and unused typography classes. Use a restrained research theme and readable Markdown styles.
10. **Docs:** update the README and project plan to match what the application actually does. Do not leave features documented as complete when they are not implemented.

Before removing any module, search for imports and usages, then remove or update tests that specifically enforce retired features. Do not delete tests for core search, extraction, citations, session persistence, or error handling.

## 9. Suggested Project Structure

Keep the existing repository where possible. A simple target structure is:

```text
backend/
  app/
    main.py
    api/
      research.py
      history.py
      health.py
    services/
      research.py          # orchestrates the workflow
      llm.py               # Groq wrapper
      search.py            # Tavily search
      extraction.py        # Firecrawl + snippet fallback
      report.py            # answer formatting and citation checks
    database/
      models.py
      database.py
    schemas/
      research.py
  tests/

frontend/
  src/ (or app/, depending on current Next.js layout)
    app/page.tsx
    components/
      ResearchForm.tsx
      ResearchProgress.tsx
      ResearchReport.tsx
      SourceList.tsx
      History.tsx
    lib/api.ts
    types/research.ts
```

This is a logical target, not a requirement to move files merely for naming consistency.

## 10. Four Implementation Phases

### Phase 1 — Make the current happy path reliable

- Run the existing app and establish the current working baseline.
- Trace one request from `POST /api/research` through persistence to the frontend.
- Fix exceptions being swallowed, the stuck running state, and double submissions.
- Confirm that a completed session really has a report and sources saved.

**Done when:** one question can be submitted and a saved result can be reopened without manually editing data.

### Phase 2 — Simplify search and answer generation

- Reduce the graph/service to the four workflow stages.
- Ensure Tavily search results are deduplicated and limited.
- Extract a few selected pages using Firecrawl, with a snippet fallback.
- Generate a short answer with citations mapped to the actual retrieved sources.
- Remove dead embedding/memory/confidence paths from the runtime only after confirming they are unused.

**Done when:** a report answers the question, contains valid source links, and never displays a citation that points to a nonexistent source.

### Phase 3 — Build the research-style UI and progress

- Keep the current main route and implement the prompt, progress timeline, report, sources, and history.
- Persist and stream real stage changes.
- Show source titles during or after research when available.
- Add clear idle, running, completed, failed, and reconnecting states.
- Style report Markdown and citations for comfortable reading.

**Done when:** a demo user can see that the system is searching and reading sources before the cited report appears.

### Phase 4 — Verify and prepare the demonstration

- Run the full backend test suite and add tests for citation mapping, SSE completion/failure, and persistence of successful/failed runs.
- Test 8–10 representative questions from different topics, such as AI, cybersecurity, education, climate, and software development.
- Include one test for empty results and one for a Firecrawl failure.
- Check that the browser contains no provider API keys.
- Verify the README setup instructions on a clean environment.
- Record a short demo flow for the project viva.

**Done when:** the main user journey works repeatedly, sources open correctly, failed runs show a useful error, and the demo does not rely on mocked provider responses.

## 11. Minimal Evaluation

Use a small manually reviewed set of 20–30 research questions for project testing. This is an evaluation benchmark, not model-training data. For each run, review:

- Does the answer address the question?
- Do cited URLs exist and match the displayed source titles?
- Do the sources support the claims near the citations?
- Are important claims clearly qualified when evidence is weak?
- Does the app finish or present an understandable failure state?

Track simple counts or percentages in a spreadsheet. Do not build a metrics dashboard unless time remains.

## 12. Demo Flow for the Teacher

1. Enter a question, for example: `What are the main cybersecurity risks of generative AI?`
2. Start research.
3. Show the activity timeline: planning, web search, opening selected pages, and writing the cited answer.
4. Open the report and click a citation.
5. Open one source to demonstrate that it is a real web page, not a made-up reference.
6. Open history and reload the saved research session.
7. Briefly show the backend keys are configured server-side and explain that Groq synthesizes retrieved evidence while Tavily and Firecrawl provide the external research tools.

## 13. Acceptance Checklist

- [ ] A user can submit a non-empty research question.
- [ ] Backend uses Groq, Tavily, and Firecrawl from server-side configuration.
- [ ] Firecrawl failures fall back to available search snippets when possible.
- [ ] Progress reflects the actual stage, not a repeated generic status.
- [ ] The final answer includes links/citations to sources actually retrieved.
- [ ] The report and sources are saved and can be opened from history.
- [ ] Frontend handles completed and failed runs without hanging.
- [ ] Provider secrets are never exposed to the browser.
- [ ] Tests cover success, empty search results, provider failure, citation mapping, and SSE terminal events.
- [ ] README and implementation plan describe the final working product accurately.

## Final Recommendation

**Do not rebuild the project from scratch.** Keep the working Next.js and FastAPI foundation. Simplify the research logic, fix reliable progress/error reporting, make citations traceable to real results, and give the frontend a calm, research-paper-style layout. A focused, working research flow is stronger for a semester project than several advanced features that are only partially wired up.
