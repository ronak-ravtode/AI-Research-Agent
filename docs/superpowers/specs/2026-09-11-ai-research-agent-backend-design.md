# AI Research Agent Backend Design Spec

## Overview

Agentic AI Research Assistant backend that autonomously decomposes research questions, searches the web, extracts evidence, verifies claims, detects conflicts, generates citations, and produces structured reports.

**Core workflow:** `Question → Planning → Search → Extraction → Verification → More Research Decision → Analysis → Conflict Detection → Citation → Report`

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | Python + FastAPI | REST API + SSE |
| Orchestration | LangGraph | Stateful multi-step agent workflow |
| LLM | Groq API (via LangChain) | Fast inference |
| Search | Tavily | Web search |
| Extraction | Firecrawl | Clean webpage content |
| Database | Supabase PostgreSQL | Persistent data |
| Vector Search | pgvector | Semantic research memory |
| Embeddings | Compatible API | Vector embeddings |
| Validation | Pydantic | Request/response validation |
| HTTP | httpx | External API calls |
| Testing | Pytest | Unit + integration tests |

## Repository Structure

```
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── research.py
│   │   ├── reports.py
│   │   ├── sources.py
│   │   ├── history.py
│   │   └── health.py
│   ├── agents/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── planner.py
│   │   ├── researcher.py
│   │   ├── extractor.py
│   │   ├── verifier.py
│   │   ├── analyst.py
│   │   ├── conflict_detector.py
│   │   └── writer.py
│   ├── tools/
│   │   ├── tavily_search.py
│   │   ├── firecrawl_extract.py
│   │   └── calculator.py
│   ├── services/
│   │   ├── llm.py
│   │   ├── embeddings.py
│   │   ├── research.py
│   │   ├── citations.py
│   │   ├── source_quality.py
│   │   ├── confidence.py
│   │   └── memory.py
│   ├── database/
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repositories.py
│   ├── schemas/
│   │   ├── research.py
│   │   ├── source.py
│   │   ├── evidence.py
│   │   └── report.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   └── utils/
│       ├── text.py
│       ├── urls.py
│       └── hashing.py
├── tests/
├── requirements.txt
├── .env.example
├── Dockerfile
├── README.md
└── .gitignore
```

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/health | Health check |
| POST | /api/research | Start research session |
| GET | /api/research/{id} | Get research status |
| GET | /api/research/{id}/stream | SSE progress stream |
| GET | /api/research/{id}/sources | Get retrieved sources |
| GET | /api/research/{id}/report | Get final report |
| GET | /api/history | Research history |

### Request/Response

**Start research:**
```json
POST /api/research
{ "query": "What is the impact of AI on software development?", "depth": "standard" }
Response: { "research_id": "uuid", "status": "started" }
```

## Database Schema

### Tables

1. **research_sessions** - id, user_id, query, status, research_depth, started_at, completed_at, created_at
2. **research_tasks** - id, research_id, task_number, description, status, agent_name, result, created_at, completed_at
3. **sources** - id, research_id, title, url, domain, author, published_date, source_type, search_query, relevance_score, reliability_score, retrieved_at
4. **evidence** - id, research_id, source_id, claim, evidence_text, evidence_type, confidence_score, created_at
5. **citations** - id, research_id, claim, source_id, citation_number, created_at
6. **reports** - id, research_id, title, executive_summary, methodology, findings, analysis, conclusion, references, created_at
7. **agent_logs** - id, research_id, agent_name, action, input_summary, output_summary, status, created_at

### Status Values

Research statuses: `planning`, `researching`, `extracting`, `verifying`, `analyzing`, `writing`, `completed`, `failed`

Verification statuses: `supported`, `partially_supported`, `unsupported`, `contradicted`

## Agent Graph

```
START → Query Understanding → Planner → Research Task → Search → Source Extraction
→ Source Evaluation → Evidence Extraction → Research Sufficiency Check
  ├─ insufficient → Generate New Search Query → Search (loop, max 2-4 iterations)
  └─ sufficient → Analysis → Conflict Detection → Citation Mapping → Report Generation
    → Final Verification → END
```

## LangGraph State

```python
ResearchState = {
    "research_id": str,
    "user_query": str,
    "research_plan": list,
    "current_task": str,
    "completed_tasks": list,
    "search_queries": list,
    "sources": list,
    "evidence": list,
    "verified_claims": list,
    "conflicts": list,
    "analysis": str,
    "citations": list,
    "confidence_scores": dict,
    "report": dict,
    "iteration": int,
    "status": str,
    "errors": list
}
```

## Agent Components

| Agent | Input | Output | Purpose |
|-------|-------|--------|---------|
| Planner | User query | Research plan (objective + subtasks) | Decompose question into tasks |
| Researcher | Task | Search queries + sources | Search web via Tavily |
| Extractor | Source + query | Claims with evidence | Extract relevant information |
| Verifier | Claim + evidence + source | Verification status + confidence | Validate claims |
| Sufficiency Decision | Evidence state | sufficient/insufficient + next queries | Decide if more research needed |
| Analyst | Verified evidence | Grouped findings + analysis | Synthesize findings |
| Conflict Detector | Claims | Detected conflicts | Find contradictions |
| Citation Engine | Claim → evidence → source | Citation mappings | Map citations |
| Writer | All verified data | Structured report | Generate report |
| Final Verifier | Report | Verification metrics | Check completeness |

## External Services

- **Groq**: LLM inference for all agent reasoning
- **Tavily**: Web search and result retrieval
- **Firecrawl**: Clean webpage content extraction
- **Supabase PostgreSQL**: Persistent storage
- **pgvector**: Semantic similarity search for research memory
- **Embedding API**: Convert text to vectors

## Research Depth Modes

| Mode | Subtasks | Sources | Iterations |
|------|----------|---------|------------|
| Quick | 2-3 | 3-5 | 1 |
| Standard | 3-5 | 8-15 | 2 |
| Deep | 5-8 | 15-25 | 3-4 |

## Implementation Order

1. FastAPI foundation
2. Database setup
3. Groq LLM service
4. LangGraph state
5. Planner agent
6. Tavily search tool
7. Researcher agent
8. Firecrawl extraction
9. Information extractor
10. Source quality scoring
11. Verifier agent
12. Research sufficiency decision
13. Analysis agent
14. Conflict detection
15. Citation engine
16. Report writer
17. Final verification
18. pgvector memory
19. SSE progress streaming
20. Testing

## Testing Strategy

- **Unit tests**: Planner, search tool, URL normalization, source scoring, citation mapping, confidence calculation, conflict detection
- **Integration tests**: FastAPI → LangGraph → Tavily → Database flow
- **E2E tests**: Fixed research questions (AI impact, autonomous vehicles, renewable energy, cybersecurity, AI in dev)

## Evaluation Metrics

- Citation accuracy: correct citations / total citations
- Citation coverage: cited major claims / total major claims
- Retrieval precision: relevant sources / total sources
- Hallucination rate: unsupported claims / total claims
- Task completion rate: completed tasks / planned tasks
