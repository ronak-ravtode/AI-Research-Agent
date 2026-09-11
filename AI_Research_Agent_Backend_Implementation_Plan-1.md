# Agentic AI Research Assistant --- Backend Implementation Plan

## 1. Project Overview

**Project:** Agentic AI Research Assistant for Autonomous Multi-Step
Research and Analysis

The backend will allow an AI agent to understand a research question,
decompose it into tasks, search external sources, extract evidence,
evaluate sources, decide whether more research is required, analyze
findings, detect conflicts, generate traceable citations, produce a
structured report, and store research history.

The core workflow is:

`Question → Planning → Search → Extraction → Verification → More Research Decision → Analysis → Conflict Detection → Citation → Report`

This must be a genuine agentic workflow, not simply
`User → LLM → Answer`.

## 2. Final Backend Technology Stack

  -----------------------------------------------------------------------
  Layer                   Technology              Purpose
  ----------------------- ----------------------- -----------------------
  Backend API             Python + FastAPI        REST API and
                                                  application server

  Agent Orchestration     LangGraph               Stateful multi-step
                                                  agent workflow

  LLM                     Groq API                Fast inference using a
                                                  pretrained LLM

  LLM SDK                 Groq Python SDK /       LLM communication
                          LangChain integration   

  Web Search              Tavily                  Search and retrieve
                                                  relevant web results

  Web Extraction          Firecrawl               Convert webpages into
                                                  clean research content

  Database                Supabase PostgreSQL     Persistent application
                                                  and research data

  Vector Search           pgvector                Semantic retrieval for
                                                  research memory

  Embeddings              Compatible embedding    Convert research
                          API                     content and queries
                                                  into vectors

  Validation              Pydantic                Request, response, and
                                                  structured AI-output
                                                  validation

  HTTP Client             httpx                   External API
                                                  communication

  DB Access               SQLAlchemy or Supabase  Database operations
                          Python client           

  Realtime Progress       Server-Sent Events      Stream agent progress
                          (SSE)                   to frontend

  Testing                 Pytest                  Unit and integration
                                                  testing

  Deployment              Render / Railway /      Backend hosting
                          equivalent              

  Monitoring              Sentry                  Error monitoring
  -----------------------------------------------------------------------

### Explicitly excluded

To keep the project realistic for four weeks, the current architecture
excludes:

-   Redis
-   Celery/background-job infrastructure
-   Uploaded-file storage
-   Dedicated document-upload workflow
-   Extra enterprise security infrastructure

## 3. Backend Architecture

``` text
React Frontend
      |
   HTTP/SSE
      |
      v
   FastAPI
      |
      v
Research Service
      |
      v
  LangGraph
      |
      +-----------------------------+
      |              |              |
      v              v              v
   Planner       Researcher      Verifier
                     |
              +------+------+
              |             |
              v             v
           Tavily       Firecrawl
              |
              v
        Retrieved Sources
              |
              v
      Information Extractor
              |
              v
        Evidence Database
              |
              v
         Analysis Agent
              |
       +------+------+
       |             |
       v             v
Conflict Detector  Confidence
       |             |
       +------+------+
              |
              v
       Citation Engine
              |
              v
       Report Generator
              |
              v
      Final Verification
              |
              v
      Supabase PostgreSQL
              |
              v
           pgvector
```

## 4. Repository Structure

``` text
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

## 5. Environment Configuration

`.env.example`:

``` env
APP_ENV=development
APP_NAME=agentic-research-assistant

GROQ_API_KEY=
GROQ_MODEL=

TAVILY_API_KEY=

FIRECRAWL_API_KEY=

SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

DATABASE_URL=

EMBEDDING_API_KEY=
EMBEDDING_MODEL=

FRONTEND_URL=http://localhost:3000
```

Never commit real secrets to Git.

## 6. FastAPI Layer

FastAPI handles routing, validation, research-session creation, status
retrieval, report retrieval, source retrieval, history, SSE progress,
and health checks.

### Core endpoints

``` http
GET  /api/health

POST /api/research
GET  /api/research/{research_id}
GET  /api/research/{research_id}/stream
GET  /api/research/{research_id}/sources
GET  /api/research/{research_id}/report
GET  /api/history
```

### Start research

``` json
{
  "query": "What is the impact of generative AI on software development?",
  "depth": "standard"
}
```

Response:

``` json
{
  "research_id": "uuid",
  "status": "started"
}
```

## 7. Database Design

Use Supabase PostgreSQL.

### research_sessions

``` text
id
user_id
query
status
research_depth
started_at
completed_at
created_at
```

Statuses:

``` text
planning
researching
extracting
verifying
analyzing
writing
completed
failed
```

### research_tasks

``` text
id
research_id
task_number
description
status
agent_name
result
created_at
completed_at
```

### sources

``` text
id
research_id
title
url
domain
author
published_date
source_type
search_query
relevance_score
reliability_score
retrieved_at
```

### evidence

``` text
id
research_id
source_id
claim
evidence_text
evidence_type
confidence_score
created_at
```

### citations

``` text
id
research_id
claim
source_id
citation_number
created_at
```

### reports

``` text
id
research_id
title
executive_summary
methodology
findings
analysis
conclusion
references
created_at
```

### agent_logs

``` text
id
research_id
agent_name
action
input_summary
output_summary
status
created_at
```

Agent logs are important for demonstrating the workflow during the viva.

## 8. LangGraph State

The shared state should contain:

``` python
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

## 9. Complete Agent Graph

``` text
START
  ↓
Query Understanding
  ↓
Planner
  ↓
Research Task
  ↓
Search
  ↓
Source Extraction
  ↓
Source Evaluation
  ↓
Evidence Extraction
  ↓
Research Sufficiency Check
  |
  +-- insufficient --> Generate New Search Query --> Search
  |
  +-- sufficient ----> Analysis
                         ↓
                   Conflict Detection
                         ↓
                   Citation Mapping
                         ↓
                   Report Generation
                         ↓
                   Final Verification
                         ↓
                        END
```

Set a maximum research iteration count, such as 2--4, to prevent endless
agent loops.

## 10. Groq LLM Service

Groq is the primary LLM inference layer.

Create:

``` text
services/llm.py
```

Expose provider-independent methods:

``` python
class LLMService:
    async def generate(...):
        ...

    async def structured_generate(...):
        ...
```

The service handles:

-   Query understanding
-   Research planning
-   Search-query generation
-   Evidence extraction
-   Source evaluation
-   Analysis
-   Conflict reasoning
-   Report generation
-   Final verification

Use structured outputs wherever possible. Do not rely on free-form text
when the backend expects JSON.

## 11. Planner Agent

Input:

``` text
User research question
```

Output:

``` json
{
  "research_objective": "Evaluate the impact of generative AI on software development",
  "subtasks": [
    {
      "id": 1,
      "task": "Find recent developer productivity studies",
      "priority": "high"
    },
    {
      "id": 2,
      "task": "Find developer survey data",
      "priority": "high"
    },
    {
      "id": 3,
      "task": "Find evidence of limitations and risks",
      "priority": "medium"
    }
  ]
}
```

The planner should generate a finite, actionable research plan.

## 12. Research Agent

Responsibilities:

1.  Read the current research task.
2.  Generate an appropriate search query.
3.  Call Tavily.
4.  Rank candidate results.
5.  Remove duplicates.
6.  Store useful sources.
7.  Decide whether additional searches are required.

Example:

``` text
Task
 ↓
LLM generates search query
 ↓
Tavily
 ↓
Search results
 ↓
Deduplication
 ↓
Source storage
```

## 13. Tavily Integration

Create:

``` text
tools/tavily_search.py
```

Expose:

``` python
async def search_web(
    query: str,
    max_results: int = 8
) -> list[SearchResult]:
    ...
```

Normalize provider responses into your own schema:

``` python
SearchResult(
    title="...",
    url="...",
    content="...",
    score=0.91
)
```

Do not spread Tavily-specific response formats throughout the
application.

## 14. Firecrawl Integration

Create:

``` text
tools/firecrawl_extract.py
```

Workflow:

``` text
Tavily result
      ↓
URL
      ↓
Firecrawl
      ↓
Clean Markdown/Text
      ↓
Content normalization
      ↓
Evidence extraction
```

Only retain content required for the research workflow.

## 15. Information Extraction Agent

Input:

``` text
Source
Research question
Current research task
```

Output:

``` json
{
  "claims": [
    {
      "claim": "AI-assisted coding improved task completion time in the study.",
      "evidence": "Relevant supporting passage...",
      "importance": 0.92
    }
  ]
}
```

Every claim must retain its `source_id`.

Traceability becomes:

``` text
Report Claim
    ↓
Evidence
    ↓
Source
    ↓
URL
```

## 16. Source Quality Service

Create:

``` text
services/source_quality.py
```

Use a transparent heuristic:

``` text
Authority          30%
Relevance          25%
Recency            20%
Evidence Quality   15%
Cross-source       10%
```

Possible source types:

``` text
academic
government
official
industry
news
blog
forum
unknown
```

The score is a project heuristic and must not be presented as an
objective measure of truth.

## 17. Verification Agent

Input:

``` text
Claim
Evidence
Source
```

Output:

``` json
{
  "supported": true,
  "confidence": 0.91,
  "reason": "The source directly supports the claim."
}
```

Possible verification states:

``` text
supported
partially_supported
unsupported
contradicted
```

Unsupported claims should not be presented as established facts.

## 18. Research Sufficiency Decision

After each research round, the agent decides whether evidence is
sufficient.

Example:

``` json
{
  "sufficient": false,
  "reason": "Current evidence lacks recent primary sources.",
  "next_searches": [
    "2026 developer productivity AI study"
  ]
}
```

If insufficient:

``` text
Verifier
 ↓
Need more evidence
 ↓
Generate new queries
 ↓
Tavily
 ↓
Extract
 ↓
Verify
```

If sufficient:

``` text
Verifier
 ↓
Evidence sufficient
 ↓
Analysis
```

## 19. Analysis Agent

The Analysis Agent receives verified evidence, not raw search results.

Responsibilities:

-   Group related evidence.
-   Identify patterns.
-   Compare findings.
-   Separate facts from interpretations.
-   Identify evidence gaps.
-   Prepare conclusions.

Example:

``` text
Evidence Group A:
5 sources report productivity improvements.

Evidence Group B:
2 sources report limited or inconsistent improvements.

Analysis:
Results generally indicate potential productivity gains,
but outcomes vary according to task complexity and user experience.
```

## 20. Conflict Detection

Create:

``` text
agents/conflict_detector.py
```

Compare claims addressing the same research question.

Example:

``` text
Source A:
Productivity increased by 30%.

Source B:
Productivity increased by 10%.
```

Output:

``` text
Conflict detected
```

The system should investigate possible reasons:

-   Different datasets
-   Different methodologies
-   Different participant groups
-   Different measurement criteria

Meaningful disagreements should remain visible in the final report.

## 21. Confidence Scoring

Create:

``` text
services/confidence.py
```

Confidence can consider:

``` text
Source reliability
+
Number of supporting sources
+
Independent source count
+
Evidence strength
+
Agreement between sources
-
Contradictory evidence
```

Example:

``` json
{
  "claim": "AI-assisted coding can improve developer productivity.",
  "confidence": 0.86,
  "supporting_sources": 6,
  "conflicting_sources": 1
}
```

Label this as a **system-generated confidence score**, not statistical
certainty.

## 22. Citation Engine

Create:

``` text
services/citations.py
```

Map:

``` text
Claim
 ↓
Evidence
 ↓
Source
 ↓
Citation ID
```

Example:

``` text
Claim C1
 ↓
Evidence E7
 ↓
Source S4
 ↓
Citation [4]
```

The report generator receives verified citation mappings rather than
inventing references.

## 23. Report Generator

Recommended report structure:

``` text
1. Executive Summary
2. Research Question
3. Methodology
4. Key Findings
5. Comparative Analysis
6. Conflicting Evidence
7. Confidence and Evidence Assessment
8. Conclusion
9. References
```

The writer receives:

-   Verified claims
-   Evidence
-   Source metadata
-   Citation mappings
-   Conflict information
-   Confidence scores

It should not introduce unsupported facts.

## 24. Final Report Verification

Before returning a report, verify:

### Citation completeness

Every important factual claim has a citation.

### Citation correctness

The cited source supports the claim.

### Unsupported claims

Flag unsupported claims.

### Missing sections

Ensure all report sections exist.

### Conflicts

Ensure detected conflicts are represented.

Example:

``` json
{
  "citation_coverage": 0.94,
  "unsupported_claims": 1,
  "conflicts_reported": 2,
  "ready": true
}
```

If serious problems exist, send the report back to the writer for
correction.

## 25. pgvector Research Memory

Research memory supports context across sessions.

Workflow:

``` text
Research Finding
 ↓
Chunk
 ↓
Embedding
 ↓
pgvector
```

New question:

``` text
New Question
 ↓
Embedding
 ↓
Similarity Search
 ↓
Relevant Previous Findings
 ↓
Agent Context
```

Store vectors for:

-   Previous research summaries
-   Important evidence
-   Conclusions
-   Research notes

Do not vectorize every database field.

## 26. Embedding Service

Create:

``` text
services/embeddings.py
```

Interface:

``` python
class EmbeddingService:
    async def embed_text(self, text: str) -> list[float]:
        ...
```

Keep embedding logic independent from Groq so the embedding provider can
be changed without modifying the agent architecture.

## 27. SSE Progress Streaming

Use Server-Sent Events to stream progress to the frontend.

Example:

``` text
event: agent_progress
data: {
  "agent": "researcher",
  "status": "searching",
  "message": "Searching for recent studies..."
}
```

Possible events:

``` text
research_started
planning_started
planning_completed
search_started
sources_found
extraction_started
verification_started
more_research_required
analysis_started
conflict_detected
report_started
report_completed
research_completed
research_failed
```

## 28. API Schemas

Use Pydantic models.

Example:

``` python
class StartResearchRequest(BaseModel):
    query: str
    depth: Literal["quick", "standard", "deep"] = "standard"
```

``` python
class ResearchResponse(BaseModel):
    research_id: UUID
    status: str
```

``` python
class SourceResponse(BaseModel):
    id: UUID
    title: str
    url: str
    domain: str
    relevance_score: float
    reliability_score: float
```

## 29. Duplicate Source Detection

Normalize URLs before storing them.

Examples:

``` text
https://example.com/article
https://example.com/article/
https://example.com/article?utm_source=x
```

should be treated as the same logical source where appropriate.

Use URL normalization and hashing.

## 30. Search Strategy

The planner should create multiple targeted searches.

Example:

``` text
Main Question:
Impact of AI on software development

Queries:
1. AI developer productivity research study
2. AI coding assistant developer survey
3. AI software engineering productivity 2025
4. AI coding limitations research
5. AI-assisted programming controlled experiment
```

The research agent can refine queries after observing results.

## 31. Research Depth

### Quick

``` text
2–3 subtasks
3–5 sources
1 research iteration
```

### Standard

``` text
3–5 subtasks
8–15 sources
2 research iterations
```

### Deep

``` text
5–8 subtasks
15–25 sources
up to 3–4 research iterations
```

All modes use the same agent architecture.

## 32. Agent Logging

Record every important agent action:

``` text
Planner → Created 5 tasks
Researcher → Generated search query
Tavily → Returned 8 results
Extractor → Extracted 17 claims
Verifier → Verified 13 claims
Verifier → Rejected 4 claims
Decision → More research required
Researcher → Started second iteration
Analyst → Detected 2 conflicts
Writer → Generated final report
```

Store these records in `agent_logs`.

## 33. Testing Strategy

### Unit Tests

Test:

``` text
Planner
Search tool
URL normalization
Source scoring
Citation mapping
Confidence calculation
Conflict detection
```

### Integration Tests

Test:

``` text
FastAPI
 ↓
LangGraph
 ↓
Tavily
 ↓
Database
```

Mock external services when appropriate.

### End-to-End Tests

Use fixed research questions such as:

``` text
1. Impact of generative AI on education
2. Benefits and risks of autonomous vehicles
3. Renewable energy adoption trends
4. Cybersecurity risks of generative AI
5. AI in software development
```

## 34. Evaluation Metrics

### Citation Accuracy

``` text
correct citations / total citations × 100
```

### Citation Coverage

``` text
cited major claims / total major claims × 100
```

### Retrieval Precision

``` text
relevant retrieved sources / total retrieved sources
```

### Hallucination Rate

``` text
unsupported claims / total factual claims
```

### Task Completion Rate

``` text
completed planned tasks / total planned tasks
```

### Average Research Time

Measure time from research initiation to report completion.

## 35. Four-Week Backend Development Plan

### Week 1 --- Foundation

-   Create Git repository and Python environment.
-   Initialize FastAPI.
-   Configure project structure.
-   Add Pydantic Settings.
-   Configure Supabase PostgreSQL.
-   Create initial schema.
-   Integrate Groq.
-   Create `LLMService`.
-   Create LangGraph state.
-   Implement planner.
-   Connect `POST /api/research`.

**Target:**

``` text
API → Groq → Planner → Research Plan → Database
```

### Week 2 --- Research Pipeline

-   Integrate Tavily.
-   Normalize search results.
-   Integrate Firecrawl.
-   Implement Research Agent.
-   Implement Information Extractor.
-   Create evidence schema.
-   Implement source quality scoring.
-   Implement Verification Agent.

**Target:**

``` text
Question → Planner → Tavily → Firecrawl → Evidence → Verification
```

### Week 3 --- Agent Intelligence

-   Implement research sufficiency decision.
-   Add conditional LangGraph loop.
-   Implement Analysis Agent.
-   Implement Conflict Detection.
-   Implement Confidence Scoring.
-   Implement Citation Engine.

**Target:**

``` text
Plan → Research → Verify → More Research Decision → Analyze → Conflicts → Citations
```

### Week 4 --- Report and Integration

-   Implement Report Generator.
-   Implement final report verification.
-   Implement pgvector memory.
-   Implement SSE progress streaming.
-   Implement research history.
-   Add error handling.
-   Write unit/integration tests.
-   Perform evaluation.
-   Fix agent loops and prompts.
-   Prepare demo and viva.

**Final target:**

``` text
User
 ↓
FastAPI
 ↓
LangGraph
 ↓
Planner
 ↓
Research
 ↓
Search + Extraction
 ↓
Verification
 ↓
Adaptive Research
 ↓
Analysis
 ↓
Conflict Detection
 ↓
Citation
 ↓
Report
 ↓
Memory
 ↓
Frontend
```

## 36. Recommended Implementation Order

Build in this exact order:

``` text
1. FastAPI
2. Database
3. Groq LLM
4. LangGraph
5. Planner
6. Tavily
7. Researcher
8. Firecrawl
9. Extractor
10. Source scoring
11. Verifier
12. Sufficiency decision
13. Analysis
14. Conflict detection
15. Citation engine
16. Report writer
17. Final verification
18. pgvector memory
19. SSE
20. Testing
```

Do not build all agents simultaneously.

## 37. MVP Definition

The MVP is complete when:

``` text
User submits question
 ↓
Planner creates subtasks
 ↓
Agent searches web
 ↓
Sources retrieved
 ↓
Pages extracted
 ↓
Evidence extracted
 ↓
Sources evaluated
 ↓
Claims verified
 ↓
Agent decides whether more research is needed
 ↓
Evidence analyzed
 ↓
Conflicts detected
 ↓
Citations mapped
 ↓
Report generated
 ↓
Report stored
 ↓
Frontend receives result
```

If this workflow is reliable, the project already satisfies the central
Agentic AI requirements.

## 38. Features to Avoid Until MVP Is Complete

Do not spend time initially on:

-   Multiple LLM providers.
-   Multiple vector databases.
-   Redis.
-   Celery.
-   Microservices.
-   Kubernetes.
-   Complex authentication.
-   Custom model training.
-   Fine-tuning.
-   Voice interface.
-   Mobile application.

These do not improve the core research agent enough to justify their
development cost.

## 39. Final Backend Deliverables

### APIs

``` text
POST /api/research
GET  /api/research/{id}
GET  /api/research/{id}/stream
GET  /api/research/{id}/sources
GET  /api/research/{id}/report
GET  /api/history
GET  /api/health
```

### Agent Components

``` text
Planner
Researcher
Extractor
Verifier
Sufficiency Decision
Analyst
Conflict Detector
Citation Engine
Writer
Final Verifier
```

### External Services

``` text
Groq
Tavily
Firecrawl
Supabase PostgreSQL
pgvector
Embedding Provider
```

### Core Demonstration

The final demo must visibly demonstrate:

``` text
Planning
Tool Usage
External Retrieval
Context/Memory
Intermediate Decisions
Multi-Step Execution
Source Verification
Evidence Synthesis
Citation
Autonomous Report Generation
```

## 40. Final Architecture Principle

**Groq is the reasoning/inference engine. LangGraph controls the agent
workflow. Tavily provides web discovery. Firecrawl provides webpage
extraction. Supabase PostgreSQL stores structured research data.
pgvector provides semantic research memory. FastAPI exposes the backend
to the frontend.**

The architecture should keep these responsibilities separate so the
project remains maintainable, testable, and easy to explain during the
viva.
