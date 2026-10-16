# Frontend

The research interface for the AI Research Assistant. One route (`/`) with four
components. All requests go to `/api/*` on the same origin and are proxied to FastAPI by
the rewrite in `next.config.ts`, so the browser never holds a provider key.

## Run

```bash
npm install
npm run dev          # http://localhost:3000
```

The backend must be running on port 8000 for the proxy to resolve.

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Dev server |
| `npm run build` | Production build |
| `npm start` | Serve the production build |
| `npm run lint` | ESLint |
| `npx tsc --noEmit` | Type check |

## Structure

```
src/
  app/page.tsx                 view machine: idle | running | completed | failed
  app/layout.tsx               shell + metadata
  app/globals.css              research-paper theme and report typography
  components/ResearchForm.tsx  question input, Ctrl/⌘+Enter, sample questions
  components/ResearchProgress.tsx  activity timeline, reconnecting state
  components/ResearchReport.tsx    Markdown answer, clickable citations, Copy answer
  components/SourceList.tsx   source cards with Open source links
  components/History.tsx       previous research
  lib/api.ts                   typed API client + SSE helper
  types/research.ts            response types
```

## Notes

- Provider keys are backend-only. `lib/api.ts` sends nothing but the user's question.
- Citations are rendered from text nodes after Markdown parsing, so existing link syntax
  is never rewritten. Raw HTML from the model is disabled.
- `react-markdown` is the only runtime dependency added for the report view.
