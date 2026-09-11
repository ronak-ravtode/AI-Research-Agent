# AI Research Agent Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an agentic AI Research Assistant backend that autonomously decomposes research questions, searches the web, extracts evidence, verifies claims, detects conflicts, generates citations, and produces structured reports.

**Architecture:** Python + FastAPI API layer → LangGraph agent orchestration → Groq LLM for reasoning → Tavily for web search → Firecrawl for content extraction → Supabase PostgreSQL + pgvector for storage.

**Tech Stack:** Python 3.11+, FastAPI, LangGraph, LangChain, Groq SDK, Tavily SDK, Firecrawl SDK, SQLAlchemy, Pydantic, httpx, SSE-starlette, pytest.

## Global Constraints

- Python 3.11+ required
- All secrets in `.env`, never committed to git
- Use async/await for all I/O-bound operations
- Use Pydantic for all request/response validation
- Follow existing code conventions (snake_case, type hints)
- Maximum research iterations: 2-4 depending on depth
- Each task ends with an independently testable deliverable

---

## File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── research.py
│   │   ├── reports.py
│   │   ├── sources.py
│   │   ├── history.py
│   │   └── health.py
│   ├── agents/
│   │   ├── __init__.py
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
│   │   ├── __init__.py
│   │   ├── tavily_search.py
│   │   ├── firecrawl_extract.py
│   │   └── calculator.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm.py
│   │   ├── embeddings.py
│   │   ├── research.py
│   │   ├── citations.py
│   │   ├── source_quality.py
│   │   ├── confidence.py
│   │   └── memory.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repositories.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── research.py
│   │   ├── source.py
│   │   ├── evidence.py
│   │   └── report.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   └── utils/
│       ├── __init__.py
│       ├── text.py
│       ├── urls.py
│       └── hashing.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_planner.py
│   ├── test_researcher.py
│   ├── test_extractor.py
│   ├── test_verifier.py
│   ├── test_conflict_detector.py
│   ├── test_citations.py
│   ├── test_source_quality.py
│   ├── test_confidence.py
│   ├── test_urls.py
│   └── test_api.py
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Task 1: Project Setup and Configuration

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/.gitignore`
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

**Interfaces:**
- Consumes: None (first task)
- Produces: `Settings` class with all config, `get_settings()` function

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.9.0
pydantic-settings==2.5.0
sqlalchemy==2.0.35
asyncpg==0.29.0
psycopg2-binary==2.9.9
langgraph==0.2.0
langchain-core==0.3.0
langchain-groq==0.2.0
groq==0.11.0
tavily-python==0.5.0
firecrawl-py==1.5.0
httpx==0.27.0
sse-starlette==2.1.0
pgvector==0.3.0
python-dotenv==1.0.0
pytest==8.3.0
pytest-asyncio==0.24.0
```

- [ ] **Step 2: Create .env.example**

```env
APP_ENV=development
APP_NAME=agentic-research-assistant

GROQ_API_KEY=
GROQ_MODEL=llama-3.1-70b-versatile

TAVILY_API_KEY=

FIRECRAWL_API_KEY=

SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

DATABASE_URL=

EMBEDDING_API_KEY=
EMBEDDING_MODEL=text-embedding-3-small

FRONTEND_URL=http://localhost:3000
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.py[cod]
*$py.class
.env
venv/
.venv/
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
```

- [ ] **Step 4: Create app/__init__.py and tests/__init__.py**

Empty files.

- [ ] **Step 5: Create core/config.py with Settings class**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "agentic-research-assistant"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    TAVILY_API_KEY: str = ""

    FIRECRAWL_API_KEY: str = ""

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    DATABASE_URL: str = ""

    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 6: Create tests/conftest.py with test settings**

```python
import pytest
from app.core.config import Settings


@pytest.fixture
def test_settings():
    return Settings(
        GROQ_API_KEY="test-key",
        TAVILY_API_KEY="test-key",
        FIRECRAWL_API_KEY="test-key",
        DATABASE_URL="sqlite+aiosqlite:///test.db",
    )
```

- [ ] **Step 7: Write test for config**

Create `tests/test_config.py`:

```python
from app.core.config import Settings, get_settings


def test_settings_defaults():
    settings = Settings()
    assert settings.APP_ENV == "development"
    assert settings.GROQ_MODEL == "llama-3.1-70b-versatile"


def test_get_settings_returns_singleton():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add backend/
git commit -m "feat: project setup with FastAPI, config, and dependencies"
```

---

## Task 2: Database Models

**Files:**
- Create: `backend/app/database/__init__.py`
- Create: `backend/app/database/database.py`
- Create: `backend/app/database/models.py`
- Create: `backend/tests/test_models.py`

**Interfaces:**
- Consumes: Settings from Task 1
- Produces: SQLAlchemy models, `get_db()` session dependency

- [ ] **Step 1: Create database/database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings


settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=settings.APP_ENV == "development")
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 2: Create database/models.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.database import Base
import enum


class ResearchStatus(str, enum.Enum):
    PLANNING = "planning"
    RESEARCHING = "researching"
    EXTRACTING = "extracting"
    VERIFYING = "verifying"
    ANALYZING = "analyzing"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"


class VerificationStatus(str, enum.Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=True)
    query = Column(Text, nullable=False)
    status = Column(String, default=ResearchStatus.PLANNING.value)
    research_depth = Column(String, default="standard")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("ResearchTask", back_populates="session", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="session", cascade="all, delete-orphan")
    evidence_items = relationship("Evidence", back_populates="session", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="session", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="session", uselist=False, cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="session", cascade="all, delete-orphan")


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id"), nullable=False)
    task_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="pending")
    agent_name = Column(String, nullable=True)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    session = relationship("ResearchSession", back_populates="tasks")


class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id"), nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    domain = Column(String, nullable=True)
    author = Column(String, nullable=True)
    published_date = Column(String, nullable=True)
    source_type = Column(String, default="unknown")
    search_query = Column(Text, nullable=True)
    relevance_score = Column(Float, default=0.0)
    reliability_score = Column(Float, default=0.0)
    retrieved_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ResearchSession", back_populates="sources")
    evidence_items = relationship("Evidence", back_populates="source")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id"), nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    claim = Column(Text, nullable=False)
    evidence_text = Column(Text, nullable=False)
    evidence_type = Column(String, default="factual")
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ResearchSession", back_populates="evidence_items")
    source = relationship("Source", back_populates="evidence_items")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id"), nullable=False)
    claim = Column(Text, nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    citation_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ResearchSession", back_populates="citations")


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id"), nullable=False)
    title = Column(Text, nullable=False)
    executive_summary = Column(Text, nullable=True)
    methodology = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    analysis = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    references = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ResearchSession", back_populates="report")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ResearchSession", back_populates="agent_logs")
```

- [ ] **Step 3: Write test for models**

Create `tests/test_models.py`:

```python
import uuid
from app.database.models import (
    ResearchSession, ResearchTask, Source, Evidence,
    Citation, Report, AgentLog, ResearchStatus
)


def test_research_session_creation():
    session = ResearchSession(query="Test query")
    assert session.query == "Test query"
    assert session.status == ResearchStatus.PLANNING.value


def test_source_creation():
    source = Source(title="Test", url="https://example.com")
    assert source.title == "Test"
    assert source.relevance_score == 0.0
```

- [ ] **Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/database/ tests/test_models.py
git commit -m "feat: database models for research sessions, sources, evidence"
```

---

## Task 3: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/research.py`
- Create: `backend/app/schemas/source.py`
- Create: `backend/app/schemas/evidence.py`
- Create: `backend/app/schemas/report.py`
- Create: `backend/tests/test_schemas.py`

**Interfaces:**
- Consumes: None (pure data models)
- Produces: `StartResearchRequest`, `ResearchResponse`, `SourceResponse`, `EvidenceResponse`, `ReportResponse`

- [ ] **Step 1: Create schemas/research.py**

```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from typing import Literal


class StartResearchRequest(BaseModel):
    query: str = Field(..., min_length=10, max_length=2000)
    depth: Literal["quick", "standard", "deep"] = "standard"


class ResearchResponse(BaseModel):
    research_id: UUID
    status: str


class ResearchStatusResponse(BaseModel):
    research_id: UUID
    query: str
    status: str
    research_depth: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
```

- [ ] **Step 2: Create schemas/source.py**

```python
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SourceResponse(BaseModel):
    id: UUID
    title: str
    url: str
    domain: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    source_type: str
    relevance_score: float
    reliability_score: float
    retrieved_at: datetime


class SourceListResponse(BaseModel):
    sources: list[SourceResponse]
    total: int
```

- [ ] **Step 3: Create schemas/evidence.py**

```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class EvidenceResponse(BaseModel):
    id: UUID
    source_id: UUID
    claim: str
    evidence_text: str
    evidence_type: str
    confidence_score: float
    verification_status: Optional[str] = None
    created_at: datetime


class EvidenceListResponse(BaseModel):
    evidence: list[EvidenceResponse]
    total: int
```

- [ ] **Step 4: Create schemas/report.py**

```python
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ReportResponse(BaseModel):
    id: UUID
    research_id: UUID
    title: str
    executive_summary: Optional[str] = None
    methodology: Optional[str] = None
    findings: Optional[str] = None
    analysis: Optional[str] = None
    conclusion: Optional[str] = None
    references: Optional[str] = None
    created_at: datetime


class HistoryItem(BaseModel):
    research_id: UUID
    query: str
    status: str
    source_count: int = 0
    completed_at: Optional[datetime] = None
    created_at: datetime
```

- [ ] **Step 5: Write test for schemas**

Create `tests/test_schemas.py`:

```python
from app.schemas.research import StartResearchRequest, ResearchResponse
from uuid import uuid4


def test_start_research_valid():
    req = StartResearchRequest(query="What is the impact of AI on software development?")
    assert req.depth == "standard"


def test_start_research_too_short():
    try:
        StartResearchRequest(query="short")
    except Exception as e:
        assert "min_length" in str(e) or "at least" in str(e)


def test_research_response():
    resp = ResearchResponse(research_id=uuid4(), status="started")
    assert resp.status == "started"
```

- [ ] **Step 6: Run tests**

Run: `cd backend && python -m pytest tests/test_schemas.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/ tests/test_schemas.py
git commit -m "feat: Pydantic schemas for API request/response validation"
```

---

## Task 4: LLM Service (Groq)

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/llm.py`
- Create: `backend/tests/test_llm.py`

**Interfaces:**
- Consumes: Settings from Task 1
- Produces: `LLMService` class with `generate()` and `structured_generate()` methods

- [ ] **Step 1: Create services/llm.py**

```python
from groq import AsyncGroq
from app.core.config import get_settings
from typing import Optional
import json


class LLMService:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def structured_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict:
        response_text = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        return json.loads(cleaned.strip())


llm_service = LLMService()
```

- [ ] **Step 2: Write test for LLM service**

Create `tests/test_llm.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.llm import LLMService


@pytest.fixture
def llm_service():
    with patch("app.services.llm.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(GROQ_API_KEY="test", GROQ_MODEL="test-model")
        with patch("app.services.llm.AsyncGroq"):
            service = LLMService()
            service.client = AsyncMock()
            return service


@pytest.mark.asyncio
async def test_generate_returns_text(llm_service):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Hello world"))]
    llm_service.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await llm_service.generate("Test prompt")
    assert result == "Hello world"


@pytest.mark.asyncio
async def test_structured_generate_returns_dict(llm_service):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"key": "value"}'))]
    llm_service.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await llm_service structured_generate("Test prompt")
    assert result == {"key": "value"}
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_llm.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/llm.py tests/test_llm.py
git commit -m "feat: Groq LLM service with generate and structured_generate"
```

---

## Task 5: LangGraph State and Graph Setup

**Files:**
- Create: `backend/app/agents/__init__.py`
- Create: `backend/app/agents/state.py`
- Create: `backend/app/agents/graph.py`
- Create: `backend/tests/test_graph.py`

**Interfaces:**
- Consumes: LLMService from Task 4
- Produces: `ResearchState` TypedDict, `create_research_graph()` function

- [ ] **Step 1: Create agents/state.py**

```python
from typing import TypedDict, Annotated, Optional
from uuid import UUID
import operator


class ResearchState(TypedDict):
    research_id: str
    user_query: str
    research_plan: list
    current_task: str
    completed_tasks: Annotated[list, operator.add]
    search_queries: Annotated[list, operator.add]
    sources: Annotated[list, operator.add]
    evidence: Annotated[list, operator.add]
    verified_claims: Annotated[list, operator.add]
    conflicts: Annotated[list, operator.add]
    analysis: str
    citations: Annotated[list, operator.add]
    confidence_scores: dict
    report: dict
    iteration: int
    status: str
    errors: Annotated[list, operator.add]
```

- [ ] **Step 2: Create agents/graph.py skeleton**

```python
from langgraph.graph import StateGraph, END
from app.agents.state import ResearchState


def create_research_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", lambda state: state)
    graph.add_node("researcher", lambda state: state)
    graph.add_node("extractor", lambda state: state)
    graph.add_node("verifier", lambda state: state)
    graph.add_node("analyst", lambda state: state)
    graph.add_node("conflict_detector", lambda state: state)
    graph.add_node("writer", lambda state: state)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "extractor")
    graph.add_edge("extractor", "verifier")
    graph.add_edge("verifier", "analyst")
    graph.add_edge("analyst", "conflict_detector")
    graph.add_edge("conflict_detector", "writer")
    graph.add_edge("writer", END)

    return graph.compile()
```

- [ ] **Step 3: Write test for graph**

Create `tests/test_graph.py`:

```python
from app.agents.graph import create_research_graph
from app.agents.state import ResearchState


def test_graph_creates():
    graph = create_research_graph()
    assert graph is not None


def test_research_state_has_required_keys():
    state = ResearchState(
        research_id="test-id",
        user_query="test",
        research_plan=[],
        current_task="",
        completed_tasks=[],
        search_queries=[],
        sources=[],
        evidence=[],
        verified_claims=[],
        conflicts=[],
        analysis="",
        citations=[],
        confidence_scores={},
        report={},
        iteration=0,
        status="planning",
        errors=[],
    )
    assert state["research_id"] == "test-id"
    assert state["iteration"] == 0
```

- [ ] **Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/ tests/test_graph.py
git commit -m "feat: LangGraph state definition and graph skeleton"
```

---

## Task 6: Tavily Search Tool

**Files:**
- Create: `backend/app/tools/__init__.py`
- Create: `backend/app/tools/tavily_search.py`
- Create: `backend/tests/test_tavily.py`

**Interfaces:**
- Consumes: Settings from Task 1
- Produces: `search_web(query, max_results) -> list[SearchResult]`, `SearchResult` dataclass

- [ ] **Step 1: Create tools/tavily_search.py**

```python
from tavily import AsyncTavilyClient
from dataclasses import dataclass
from app.core.config import get_settings
from typing import Optional


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float
    domain: Optional[str] = None


class TavilySearch:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

    async def search_web(
        self,
        query: str,
        max_results: int = 8,
    ) -> list[SearchResult]:
        response = await self.client.search(
            query=query,
            max_results=max_results,
            include_answer=False,
        )

        results = []
        for item in response.get("results", []):
            url = item.get("url", "")
            domain = None
            if url:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc

            results.append(SearchResult(
                title=item.get("title", ""),
                url=url,
                content=item.get("content", ""),
                score=item.get("score", 0.0),
                domain=domain,
            ))

        return results


tavily_search = TavilySearch()
```

- [ ] **Step 2: Write test for Tavily**

Create `tests/test_tavily.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.tools.tavily_search import TavilySearch, SearchResult


@pytest.fixture
def tavily():
    with patch("app.tools.tavily_search.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(TAVILY_API_KEY="test-key")
        with patch("app.tools.tavily_search.AsyncTavilyClient"):
            search = TavilySearch()
            search.client = AsyncMock()
            return search


@pytest.mark.asyncio
async def test_search_returns_results(tavily):
    tavily.client.search = AsyncMock(return_value={
        "results": [
            {"title": "Test", "url": "https://example.com", "content": "Content", "score": 0.9}
        ]
    })

    results = await tavily.search_web("test query")
    assert len(results) == 1
    assert results[0].title == "Test"
    assert results[0].domain == "example.com"


@pytest.mark.asyncio
async def test_search_empty_results(tavily):
    tavily.client.search = AsyncMock(return_value={"results": []})
    results = await tavily.search_web("no results")
    assert len(results) == 0
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_tavily.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/tools/tavily_search.py tests/test_tavily.py
git commit -m "feat: Tavily web search tool with normalized results"
```

---

## Task 7: Firecrawl Extraction Tool

**Files:**
- Create: `backend/app/tools/firecrawl_extract.py`
- Create: `backend/tests/test_firecrawl.py`

**Interfaces:**
- Consumes: Settings from Task 1
- Produces: `extract_url(url) -> ExtractedContent` dataclass

- [ ] **Step 1: Create tools/firecrawl_extract.py**

```python
from firecrawl import FirecrawlApp
from dataclasses import dataclass
from app.core.config import get_settings
from typing import Optional


@dataclass
class ExtractedContent:
    url: str
    title: Optional[str]
    content: str
    markdown: Optional[str] = None


class FirecrawlExtract:
    def __init__(self):
        settings = get_settings()
        self.app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)

    async def extract_url(self, url: str) -> ExtractedContent:
        try:
            result = self.app.scrape_url(url, params={"formats": ["markdown"]})

            return ExtractedContent(
                url=url,
                title=result.get("metadata", {}).get("title"),
                content=result.get("markdown", result.get("content", "")),
                markdown=result.get("markdown"),
            )
        except Exception as e:
            return ExtractedContent(
                url=url,
                title=None,
                content=f"Extraction failed: {str(e)}",
            )


firecrawl_extract = FirecrawlExtract()
```

- [ ] **Step 2: Write test for Firecrawl**

Create `tests/test_firecrawl.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from app.tools.firecrawl_extract import FirecrawlExtract, ExtractedContent


@pytest.fixture
def firecrawl():
    with patch("app.tools.firecrawl_extract.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(FIRECRAWL_API_KEY="test-key")
        with patch("app.tools.firecrawl_extract.FirecrawlApp"):
            extract = FirecrawlExtract()
            extract.app = MagicMock()
            return extract


def test_extract_returns_content(firecrawl):
    firecrawl.app.scrape_url.return_value = {
        "metadata": {"title": "Test Page"},
        "markdown": "# Test content",
    }

    result = firecrawl.extract_url("https://example.com")
    assert result.title == "Test Page"
    assert result.markdown == "# Test content"


def test_extract_handles_error(firecrawl):
    firecrawl.app.scrape_url.side_effect = Exception("API error")

    result = firecrawl.extract_url("https://bad-url.com")
    assert "failed" in result.content.lower()
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_firecrawl.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/tools/firecrawl_extract.py tests/test_firecrawl.py
git commit -m "feat: Firecrawl webpage extraction tool"
```

---

## Task 8: Source Quality Scoring Service

**Files:**
- Create: `backend/app/services/source_quality.py`
- Create: `backend/tests/test_source_quality.py`

**Interfaces:**
- Consumes: `Source` data
- Produces: `score_source(source) -> float`, `classify_source_type(url) -> str`

- [ ] **Step 1: Create services/source_quality.py**

```python
from typing import Optional


SOURCE_TYPE_AUTHORITY = {
    "academic": 0.9,
    "government": 0.85,
    "official": 0.8,
    "industry": 0.7,
    "news": 0.6,
    "blog": 0.4,
    "forum": 0.3,
    "unknown": 0.3,
}


def classify_source_type(url: str, domain: Optional[str] = None) -> str:
    if not domain:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

    if any(d in domain for d in [".edu", ".ac."]):
        return "academic"
    if any(d in domain for d in [".gov", ".mil"]):
        return "government"
    if any(d in domain for d in ["arxiv.org", "ieee.org", "acm.org", "springer.com"]):
        return "academic"
    if any(d in domain for d in ["reuters.com", "apnews.com", "bbc.com", "nytimes.com"]):
        return "news"
    if any(d in domain for d in ["medium.com", "substack.com", "dev.to"]):
        return "blog"
    if any(d in domain for d in ["reddit.com", "stackoverflow.com", "quora.com"]):
        return "forum"
    return "unknown"


def score_source(
    url: str,
    domain: Optional[str] = None,
    relevance_score: float = 0.5,
    evidence_quality: float = 0.5,
    cross_source_agreement: float = 0.5,
) -> float:
    source_type = classify_source_type(url, domain)
    authority = SOURCE_TYPE_AUTHORITY.get(source_type, 0.3)

    reliability = (
        authority * 0.30
        + relevance_score * 0.25
        + 0.5 * 0.20
        + evidence_quality * 0.15
        + cross_source_agreement * 0.10
    )

    return round(min(max(reliability, 0.0), 1.0), 2)
```

- [ ] **Step 2: Write test for source quality**

Create `tests/test_source_quality.py`:

```python
from app.services.source_quality import classify_source_type, score_source


def test_classify_academic():
    assert classify_source_type("https://arxiv.org/abs/2301.00001") == "academic"


def test_classify_government():
    assert classify_source_type("https://www.whitehouse.gov/report") == "government"


def test_classify_news():
    assert classify_source_type("https://www.reuters.com/article") == "news"


def test_classify_unknown():
    assert classify_source_type("https://random-blog.com/post") == "unknown"


def test_score_source_range():
    score = score_source("https://arxiv.org/paper", relevance_score=0.8)
    assert 0.0 <= score <= 1.0
    assert score > 0.5


def test_score_source_low():
    score = score_source("https://forum.example.com", relevance_score=0.2)
    assert score < 0.5
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_source_quality.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/source_quality.py tests/test_source_quality.py
git commit -m "feat: source quality scoring service"
```

---

## Task 9: Planner Agent

**Files:**
- Create: `backend/app/agents/planner.py`
- Create: `backend/tests/test_planner.py`

**Interfaces:**
- Consumes: LLMService from Task 4, ResearchState from Task 5
- Produces: `planner_agent(state) -> ResearchState` with populated `research_plan`

- [ ] **Step 1: Create agents/planner.py**

```python
from app.services.llm import llm_service
from app.agents.state import ResearchState


PLANNER_SYSTEM_PROMPT = """You are a research planning agent. Given a research question, create a detailed research plan.

Your plan should include:
1. A clear research objective
2. 3-5 specific subtasks to investigate
3. Each subtask should be actionable and specific

Respond in JSON format:
{
    "research_objective": "...",
    "subtasks": [
        {"id": 1, "task": "...", "priority": "high|medium|low"},
        ...
    ]
}"""


async def planner_agent(state: ResearchState) -> dict:
    query = state["user_query"]
    depth = state.get("research_depth", "standard")

    prompt = f"""Research question: {query}
Research depth: {depth}

Create a research plan."""

    plan = await llm_service.structured_generate(
        prompt=prompt,
        system_prompt=PLANNER_SYSTEM_PROMPT,
        temperature=0.3,
    )

    return {
        "research_plan": plan.get("subtasks", []),
        "status": "planning",
    }
```

- [ ] **Step 2: Write test for planner**

Create `tests/test_planner.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.planner import planner_agent
from app.agents.state import ResearchState


@pytest.mark.asyncio
async def test_planner_returns_plan():
    mock_plan = {
        "research_objective": "Test objective",
        "subtasks": [
            {"id": 1, "task": "Find studies", "priority": "high"},
            {"id": 2, "task": "Find surveys", "priority": "medium"},
        ],
    }

    with patch("app.agents.planner.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value=mock_plan)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI on development",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[],
            evidence=[],
            verified_claims=[],
            conflicts=[],
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=0,
            status="planning",
            errors=[],
        )

        result = await planner_agent(state)
        assert len(result["research_plan"]) == 2
        assert result["status"] == "planning"
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_planner.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/agents/planner.py tests/test_planner.py
git commit -m "feat: planner agent with research plan generation"
```

---

## Task 10: Researcher Agent

**Files:**
- Create: `backend/app/agents/researcher.py`
- Create: `backend/tests/test_researcher.py`

**Interfaces:**
- Consumes: LLMService from Task 4, TavilySearch from Task 6, ResearchState from Task 5
- Produces: `researcher_agent(state) -> ResearchState` with populated `sources` and `search_queries`

- [ ] **Step 1: Create agents/researcher.py**

```python
from app.services.llm import llm_service
from app.tools.tavily_search import tavily_search
from app.agents.state import ResearchState
from app.services.source_quality import score_source, classify_source_type
from urllib.parse import urlparse


SEARCH_QUERY_PROMPT = """Given this research task, generate a focused web search query.
Return only the search query text, nothing else.

Research task: {task}
Research objective: {objective}"""


async def researcher_agent(state: ResearchState) -> dict:
    plan = state.get("research_plan", [])
    completed = state.get("completed_tasks", [])
    iteration = state.get("iteration", 0)

    tasks_to_research = [t for t in plan if t.get("id") not in completed]

    if not tasks_to_research and iteration > 0:
        search_queries = state.get("search_queries", [])
        if search_queries:
            query = search_queries[-1]
        else:
            return {"sources": [], "status": "researching"}
    else:
        task = tasks_to_research[0] if tasks_to_research else plan[0]
        query_prompt = SEARCH_QUERY_PROMPT.format(
            task=task.get("task", ""),
            objective=state.get("user_query", ""),
        )
        query = await llm_service.generate(prompt=query_prompt, temperature=0.3)

    results = await tavily_search.search_web(query=query, max_results=8)

    new_sources = []
    for r in results:
        domain = None
        if r.url:
            parsed = urlparse(r.url)
            domain = parsed.netloc

        source_type = classify_source_type(r.url, domain)
        reliability = score_source(
            r.url,
            domain=domain,
            relevance_score=r.score,
        )

        new_sources.append({
            "title": r.title,
            "url": r.url,
            "domain": domain,
            "content": r.content,
            "source_type": source_type,
            "relevance_score": r.score,
            "reliability_score": reliability,
            "search_query": query,
        })

    return {
        "sources": new_sources,
        "search_queries": [query],
        "status": "researching",
    }
```

- [ ] **Step 2: Write test for researcher**

Create `tests/test_researcher.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.researcher import researcher_agent
from app.agents.state import ResearchState
from app.tools.tavily_search import SearchResult


@pytest.mark.asyncio
async def test_researcher_searches_and_returns_sources():
    mock_results = [
        SearchResult(title="Study 1", url="https://arxiv.org/paper", content="Content", score=0.9),
        SearchResult(title="Blog 1", url="https://blog.example.com/post", content="Content", score=0.6),
    ]

    with patch("app.agents.researcher.llm_service") as mock_llm, \
         patch("app.agents.researcher.tavily_search") as mock_tavily:
        mock_llm.generate = AsyncMock(return_value="AI productivity study 2026")
        mock_tavily.search_web = AsyncMock(return_value=mock_results)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[{"id": 1, "task": "Find studies", "priority": "high"}],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[],
            evidence=[],
            verified_claims=[],
            conflicts=[],
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=0,
            status="planning",
            errors=[],
        )

        result = await researcher_agent(state)
        assert len(result["sources"]) == 2
        assert result["status"] == "researching"
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_researcher.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/agents/researcher.py tests/test_researcher.py
git commit -m "feat: researcher agent with Tavily search and source scoring"
```

---

## Task 11: Information Extractor Agent

**Files:**
- Create: `backend/app/agents/extractor.py`
- Create: `backend/tests/test_extractor.py`

**Interfaces:**
- Consumes: LLMService from Task 4, ResearchState from Task 5
- Produces: `extractor_agent(state) -> ResearchState` with populated `evidence`

- [ ] **Step 1: Create agents/extractor.py**

```python
from app.services.llm import llm_service
from app.agents.state import ResearchState


EXTRACTOR_SYSTEM_PROMPT = """You are an information extraction agent. Extract factual claims and evidence from the source content.

For each claim, provide:
1. The specific claim being made
2. The supporting evidence text from the source
3. The evidence type (factual, statistical, expert_opinion, anecdotal)
4. Importance score (0.0 to 1.0)

Respond in JSON format:
{
    "claims": [
        {
            "claim": "...",
            "evidence": "...",
            "evidence_type": "factual",
            "importance": 0.8
        }
    ]
}

Only extract claims that are directly supported by the source content."""


async def extractor_agent(state: ResearchState) -> dict:
    sources = state.get("sources", [])
    query = state.get("user_query", "")

    all_evidence = []

    for source in sources:
        content = source.get("content", "")
        if not content or len(content) < 100:
            continue

        prompt = f"""Research question: {query}

Source title: {source.get('title', 'Unknown')}
Source content:
{content[:3000]}"""

        try:
            result = await llm_service.structured_generate(
                prompt=prompt,
                system_prompt=EXTRACTOR_SYSTEM_PROMPT,
                temperature=0.2,
            )

            for claim in result.get("claims", []):
                all_evidence.append({
                    "source_id": source.get("id"),
                    "source_url": source.get("url"),
                    "claim": claim.get("claim", ""),
                    "evidence_text": claim.get("evidence", ""),
                    "evidence_type": claim.get("evidence_type", "factual"),
                    "confidence_score": claim.get("importance", 0.5),
                })
        except Exception:
            continue

    return {
        "evidence": all_evidence,
        "status": "extracting",
    }
```

- [ ] **Step 2: Write test for extractor**

Create `tests/test_extractor.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.extractor import extractor_agent
from app.agents.state import ResearchState


@pytest.mark.asyncio
async def test_extractor_extracts_claims():
    mock_result = {
        "claims": [
            {
                "claim": "AI improves productivity",
                "evidence": "Study shows 30% improvement",
                "evidence_type": "statistical",
                "importance": 0.9,
            }
        ]
    }

    with patch("app.agents.extractor.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value=mock_result)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[{"id": "src-1", "title": "Study", "url": "https://example.com", "content": "x" * 200}],
            evidence=[],
            verified_claims=[],
            conflicts=[],
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=0,
            status="researching",
            errors=[],
        )

        result = await extractor_agent(state)
        assert len(result["evidence"]) == 1
        assert result["status"] == "extracting"
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_extractor.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/agents/extractor.py tests/test_extractor.py
git commit -m "feat: information extractor agent"
```

---

## Task 12: Verification Agent

**Files:**
- Create: `backend/app/agents/verifier.py`
- Create: `backend/tests/test_verifier.py`

**Interfaces:**
- Consumes: LLMService from Task 4, ResearchState from Task 5
- Produces: `verifier_agent(state) -> ResearchState` with populated `verified_claims`

- [ ] **Step 1: Create agents/verifier.py**

```python
from app.services.llm import llm_service
from app.agents.state import ResearchState


VERIFIER_SYSTEM_PROMPT = """You are a claim verification agent. Verify whether the evidence supports the claims.

For each claim, determine:
1. Whether the evidence supports it (supported, partially_supported, unsupported, contradicted)
2. A confidence score (0.0 to 1.0)
3. A brief explanation

Respond in JSON format:
{
    "verified_claims": [
        {
            "claim": "...",
            "evidence": "...",
            "source_url": "...",
            "verification_status": "supported",
            "confidence": 0.9,
            "reason": "..."
        }
    ]
}"""


async def verifier_agent(state: ResearchState) -> dict:
    evidence = state.get("evidence", [])
    query = state.get("user_query", "")

    verified = []

    for item in evidence:
        prompt = f"""Research question: {query}

Claim: {item.get('claim', '')}
Evidence: {item.get('evidence_text', '')}
Source: {item.get('source_url', '')}

Verify this claim."""

        try:
            result = await llm_service.structured_generate(
                prompt=prompt,
                system_prompt=VERIFIER_SYSTEM_PROMPT,
                temperature=0.2,
            )

            for v in result.get("verified_claims", []):
                verified.append({
                    **item,
                    "verification_status": v.get("verification_status", "unsupported"),
                    "confidence": v.get("confidence", 0.5),
                    "reason": v.get("reason", ""),
                })
        except Exception:
            verified.append({
                **item,
                "verification_status": "unsupported",
                "confidence": 0.0,
                "reason": "Verification failed",
            })

    return {
        "verified_claims": verified,
        "status": "verifying",
    }
```

- [ ] **Step 2: Write test for verifier**

Create `tests/test_verifier.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.verifier import verifier_agent
from app.agents.state import ResearchState


@pytest.mark.asyncio
async def test_verifier_verifies_claims():
    mock_result = {
        "verified_claims": [
            {
                "claim": "AI improves productivity",
                "verification_status": "supported",
                "confidence": 0.9,
                "reason": "Study directly supports",
            }
        ]
    }

    with patch("app.agents.verifier.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value=mock_result)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[],
            evidence=[{"claim": "AI improves productivity", "evidence_text": "30% improvement", "source_url": "https://example.com"}],
            verified_claims=[],
            conflicts=[],
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=0,
            status="extracting",
            errors=[],
        )

        result = await verifier_agent(state)
        assert len(result["verified_claims"]) == 1
        assert result["verified_claims"][0]["verification_status"] == "supported"
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_verifier.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/agents/verifier.py tests/test_verifier.py
git commit -m "feat: verification agent for claim validation"
```

---

## Task 13: Confidence Scoring Service

**Files:**
- Create: `backend/app/services/confidence.py`
- Create: `backend/tests/test_confidence.py`

**Interfaces:**
- Consumes: Verified claims data
- Produces: `calculate_confidence(verified_claims) -> dict`

- [ ] **Step 1: Create services/confidence.py**

```python
from typing import Any


def calculate_confidence(verified_claims: list[dict]) -> dict:
    if not verified_claims:
        return {"overall": 0.0, "claim_scores": [], "summary": "No claims to evaluate"}

    claim_scores = []
    supported = 0
    partial = 0
    unsupported = 0
    contradicted = 0

    for claim in verified_claims:
        status = claim.get("verification_status", "unsupported")
        confidence = claim.get("confidence", 0.0)

        if status == "supported":
            supported += 1
        elif status == "partially_supported":
            partial += 1
        elif status == "contradicted":
            contradicted += 1
        else:
            unsupported += 1

        claim_scores.append({
            "claim": claim.get("claim", ""),
            "status": status,
            "confidence": confidence,
        })

    total = len(verified_claims)
    supported_ratio = supported / total
    partial_ratio = partial / total
    contradicted_penalty = contradicted / total

    overall = (supported_ratio * 0.9 + partial_ratio * 0.5 - contradicted_penalty * 0.3)
    overall = max(0.0, min(1.0, overall))

    return {
        "overall": round(overall, 2),
        "claim_scores": claim_scores,
        "summary": {
            "total": total,
            "supported": supported,
            "partially_supported": partial,
            "unsupported": unsupported,
            "contradicted": contradicted,
        },
    }
```

- [ ] **Step 2: Write test for confidence**

Create `tests/test_confidence.py`:

```python
from app.services.confidence import calculate_confidence


def test_confidence_empty():
    result = calculate_confidence([])
    assert result["overall"] == 0.0


def test_confidence_all_supported():
    claims = [
        {"claim": "A", "verification_status": "supported", "confidence": 0.9},
        {"claim": "B", "verification_status": "supported", "confidence": 0.8},
    ]
    result = calculate_confidence(claims)
    assert result["overall"] > 0.8
    assert result["summary"]["supported"] == 2


def test_confidence_mixed():
    claims = [
        {"claim": "A", "verification_status": "supported", "confidence": 0.9},
        {"claim": "B", "verification_status": "contradicted", "confidence": 0.7},
    ]
    result = calculate_confidence(claims)
    assert 0.0 <= result["overall"] <= 1.0
    assert result["summary"]["contradicted"] == 1
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_confidence.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/confidence.py tests/test_confidence.py
git commit -m "feat: confidence scoring service"
```

---

## Task 14: Sufficiency Decision and Analysis Agent

**Files:**
- Create: `backend/app/agents/analyst.py`
- Create: `backend/tests/test_analyst.py`

**Interfaces:**
- Consumes: LLMService from Task 4, ResearchState from Task 5
- Produces: `sufficiency_agent(state) -> ResearchState`, `analyst_agent(state) -> ResearchState`

- [ ] **Step 1: Create agents/analyst.py**

```python
from app.services.llm import llm_service
from app.agents.state import ResearchState


SUFFICIENCY_PROMPT = """You are a research sufficiency evaluator. Determine if the current evidence is sufficient to answer the research question.

Research question: {question}
Evidence collected: {evidence_count} claims from {source_count} sources
Research depth: {depth}
Current iteration: {iteration}
Max iterations: {max_iterations}

Respond in JSON:
{
    "sufficient": true/false,
    "reason": "...",
    "next_searches": ["query1", "query2"]
}"""

ANALYSIS_PROMPT = """You are a research analyst. Analyze the verified evidence to identify patterns, comparisons, and conclusions.

Research question: {question}

Verified claims:
{claims}

Respond in JSON:
{
    "key_findings": ["finding1", "finding2"],
    "patterns": ["pattern1"],
    "comparison": "...",
    "conclusion": "...",
    "gaps": ["gap1"]
}"""


MAX_ITERATIONS = {"quick": 1, "standard": 2, "deep": 4}


async def sufficiency_agent(state: ResearchState) -> dict:
    depth = state.get("research_depth", "standard")
    iteration = state.get("iteration", 0)
    max_iter = MAX_ITERATIONS.get(depth, 2)

    if iteration >= max_iter:
        return {"status": "verifying"}

    evidence = state.get("verified_claims", [])
    sources = state.get("sources", [])

    prompt = SUFFICIENCY_PROMPT.format(
        question=state.get("user_query", ""),
        evidence_count=len(evidence),
        source_count=len(sources),
        depth=depth,
        iteration=iteration,
        max_iterations=max_iter,
    )

    result = await llm_service.structured_generate(
        prompt=prompt,
        temperature=0.2,
    )

    if result.get("sufficient", False):
        return {"status": "verifying"}

    return {
        "search_queries": result.get("next_searches", []),
        "iteration": iteration + 1,
        "status": "researching",
    }


async def analyst_agent(state: ResearchState) -> dict:
    claims = state.get("verified_claims", [])

    prompt = ANALYSIS_PROMPT.format(
        question=state.get("user_query", ""),
        claims="\n".join([
            f"- {c.get('claim', '')} ({c.get('verification_status', 'unknown')})"
            for c in claims
        ]),
    )

    result = await llm_service.structured_generate(
        prompt=prompt,
        temperature=0.3,
    )

    return {
        "analysis": result.get("conclusion", ""),
        "status": "analyzing",
    }
```

- [ ] **Step 2: Write test for analyst**

Create `tests/test_analyst.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.analyst import sufficiency_agent, analyst_agent
from app.agents.state import ResearchState


@pytest.mark.asyncio
async def test_sufficiency_returns_when_max_iterations():
    state = ResearchState(
        research_id="test-id",
        user_query="test",
        research_plan=[],
        current_task="",
        completed_tasks=[],
        search_queries=[],
        sources=[],
        evidence=[],
        verified_claims=[],
        conflicts=[],
        analysis="",
        citations=[],
        confidence_scores={},
        report={},
        iteration=5,
        status="verifying",
        errors=[],
        research_depth="quick",
    )

    result = await sufficiency_agent(state)
    assert result["status"] == "verifying"


@pytest.mark.asyncio
async def test_analyst_returns_analysis():
    mock_result = {
        "key_findings": ["Finding 1"],
        "conclusion": "AI generally improves productivity",
    }

    with patch("app.agents.analyst.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value=mock_result)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[],
            evidence=[],
            verified_claims=[{"claim": "AI improves productivity", "verification_status": "supported"}],
            conflicts=[],
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=1,
            status="verifying",
            errors=[],
        )

        result = await analyst_agent(state)
        assert result["status"] == "analyzing"
        assert len(result["analysis"]) > 0
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_analyst.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/agents/analyst.py tests/test_analyst.py
git commit -m "feat: sufficiency decision and analysis agents"
```

---

## Task 15: Conflict Detection Agent

**Files:**
- Create: `backend/app/agents/conflict_detector.py`
- Create: `backend/tests/test_conflict_detector.py`

**Interfaces:**
- Consumes: LLMService from Task 4, ResearchState from Task 5
- Produces: `conflict_detector_agent(state) -> ResearchState` with populated `conflicts`

- [ ] **Step 1: Create agents/conflict_detector.py**

```python
from app.services.llm import llm_service
from app.agents.state import ResearchState


CONFLICT_PROMPT = """You are a conflict detection agent. Identify contradictions or disagreements in the verified claims.

Research question: {question}

Verified claims:
{claims}

Respond in JSON:
{
    "conflicts": [
        {
            "topic": "...",
            "claim_a": {"text": "...", "source": "...", "value": "..."},
            "claim_b": {"text": "...", "source": "...", "value": "..."},
            "possible_explanation": "...",
            "severity": "high|medium|low"
        }
    ]
}

If no conflicts found, return {{"conflicts": []}}"""


async def conflict_detector_agent(state: ResearchState) -> dict:
    claims = state.get("verified_claims", [])

    if len(claims) < 2:
        return {"conflicts": [], "status": "analyzing"}

    prompt = CONFLICT_PROMPT.format(
        question=state.get("user_query", ""),
        claims="\n".join([
            f"- [{c.get('verification_status', 'unknown')}] {c.get('claim', '')} (Source: {c.get('source_url', 'unknown')})"
            for c in claims
        ]),
    )

    result = await llm_service.structured_generate(
        prompt=prompt,
        temperature=0.2,
    )

    return {
        "conflicts": result.get("conflicts", []),
        "status": "analyzing",
    }
```

- [ ] **Step 2: Write test for conflict detector**

Create `tests/test_conflict_detector.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.conflict_detector import conflict_detector_agent
from app.agents.state import ResearchState


@pytest.mark.asyncio
async def test_conflict_detector_finds_conflicts():
    mock_result = {
        "conflicts": [
            {
                "topic": "Productivity improvement",
                "claim_a": {"text": "+30%", "source": "A", "value": "30%"},
                "claim_b": {"text": "+10%", "source": "B", "value": "10%"},
                "possible_explanation": "Different methodologies",
                "severity": "medium",
            }
        ]
    }

    with patch("app.agents.conflict_detector.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value=mock_result)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[],
            evidence=[],
            verified_claims=[
                {"claim": "+30% productivity", "source_url": "https://a.com"},
                {"claim": "+10% productivity", "source_url": "https://b.com"},
            ],
            conflicts=[],
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=1,
            status="analyzing",
            errors=[],
        )

        result = await conflict_detector_agent(state)
        assert len(result["conflicts"]) == 1
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_conflict_detector.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/agents/conflict_detector.py tests/test_conflict_detector.py
git commit -m "feat: conflict detection agent"
```

---

## Task 16: Citation Engine

**Files:**
- Create: `backend/app/services/citations.py`
- Create: `backend/tests/test_citations.py`

**Interfaces:**
- Consumes: Verified claims, sources
- Produces: `map_citations(verified_claims, sources) -> list[Citation]`

- [ ] **Step 1: Create services/citations.py**

```python
from typing import Any
from uuid import uuid4


def map_citations(verified_claims: list[dict], sources: list[dict]) -> list[dict]:
    source_url_to_id = {s.get("url"): s.get("id") for s in sources}
    citations = []
    citation_counter = 1

    seen_claims = set()

    for claim in verified_claims:
        claim_text = claim.get("claim", "")
        source_url = claim.get("source_url", "")

        if claim_text in seen_claims:
            continue

        source_id = claim.get("source_id") or source_url_to_id.get(source_url)

        if not source_id:
            continue

        citations.append({
            "id": str(uuid4()),
            "claim": claim_text,
            "source_id": source_id,
            "source_url": source_url,
            "citation_number": citation_counter,
        })

        citation_counter += 1
        seen_claims.add(claim_text)

    return citations
```

- [ ] **Step 2: Write test for citations**

Create `tests/test_citations.py`:

```python
from app.services.citations import map_citations


def test_map_citations_basic():
    claims = [
        {"claim": "AI improves productivity", "source_url": "https://a.com", "source_id": "s1"},
        {"claim": "AI reduces costs", "source_url": "https://b.com", "source_id": "s2"},
    ]
    sources = [{"id": "s1", "url": "https://a.com"}, {"id": "s2", "url": "https://b.com"}]

    citations = map_citations(claims, sources)
    assert len(citations) == 2
    assert citations[0]["citation_number"] == 1
    assert citations[1]["citation_number"] == 2


def test_map_citations_deduplicates():
    claims = [
        {"claim": "AI improves productivity", "source_url": "https://a.com", "source_id": "s1"},
        {"claim": "AI improves productivity", "source_url": "https://b.com", "source_id": "s2"},
    ]
    sources = [{"id": "s1", "url": "https://a.com"}, {"id": "s2", "url": "https://b.com"}]

    citations = map_citations(claims, sources)
    assert len(citations) == 1
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_citations.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/citations.py tests/test_citations.py
git commit -m "feat: citation engine for mapping claims to sources"
```

---

## Task 17: Report Writer Agent

**Files:**
- Create: `backend/app/agents/writer.py`
- Create: `backend/tests/test_writer.py`

**Interfaces:**
- Consumes: LLMService from Task 4, ResearchState from Task 5
- Produces: `writer_agent(state) -> ResearchState` with populated `report`

- [ ] **Step 1: Create agents/writer.py**

```python
from app.services.llm import llm_service
from app.agents.state import ResearchState


WRITER_SYSTEM_PROMPT = """You are a research report writer. Generate a structured research report based on the provided data.

The report must include these sections:
1. Executive Summary
2. Research Question
3. Methodology
4. Key Findings
5. Comparative Analysis
6. Conflicting Evidence
7. Confidence Assessment
8. Conclusion
9. References

Use markdown formatting. Be factual and cite sources using [N] notation.
Do not introduce information not present in the provided data."""


async def writer_agent(state: ResearchState) -> dict:
    verified_claims = state.get("verified_claims", [])
    conflicts = state.get("conflicts", [])
    analysis = state.get("analysis", "")
    citations = state.get("citations", [])
    sources = state.get("sources", [])

    citations_text = "\n".join([
        f"[{c.get('citation_number', i+1)}] {c.get('source_url', '')}"
        for i, c in enumerate(citations)
    ])

    prompt = f"""Research question: {state.get('user_query', '')}

Verified claims:
{chr(10).join([f"- [{c.get('verification_status', 'unknown')}] {c.get('claim', '')}" for c in verified_claims])}

Conflicts:
{chr(10).join([f"- {c.get('topic', '')}: {c.get('possible_explanation', '')}" for c in conflicts])}

Analysis: {analysis}

Citations:
{citations_text}

Generate the research report."""

    report_text = await llm_service.generate(
        prompt=prompt,
        system_prompt=WRITER_SYSTEM_PROMPT,
        temperature=0.3,
        max_tokens=4096,
    )

    return {
        "report": {
            "title": f"Research Report: {state.get('user_query', '')[:100]}",
            "content": report_text,
            "citations": citations,
        },
        "status": "writing",
    }
```

- [ ] **Step 2: Write test for writer**

Create `tests/test_writer.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.writer import writer_agent
from app.agents.state import ResearchState


@pytest.mark.asyncio
async def test_writer_generates_report():
    with patch("app.agents.writer.llm_service") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="# Research Report\n\n## Executive Summary\n...")

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[],
            evidence=[],
            verified_claims=[{"claim": "AI improves productivity", "verification_status": "supported"}],
            conflicts=[],
            analysis="AI generally improves productivity",
            citations=[{"citation_number": 1, "source_url": "https://a.com"}],
            confidence_scores={},
            report={},
            iteration=1,
            status="analyzing",
            errors=[],
        )

        result = await writer_agent(state)
        assert result["status"] == "writing"
        assert "title" in result["report"]
        assert "content" in result["report"]
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_writer.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/agents/writer.py tests/test_writer.py
git commit -m "feat: report writer agent"
```

---

## Task 18: Research Service (Orchestration)

**Files:**
- Create: `backend/app/services/research.py`
- Create: `backend/tests/test_research_service.py`

**Interfaces:**
- Consumes: All agents from Tasks 9-17, database from Task 2
- Produces: `ResearchService` class with `start_research()`, `get_status()`, `get_sources()`, `get_report()`

- [ ] **Step 1: Create services/research.py**

```python
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import (
    ResearchSession, ResearchTask, Source, Evidence,
    Citation, Report, AgentLog, ResearchStatus
)
from app.agents.planner import planner_agent
from app.agents.researcher import researcher_agent
from app.agents.extractor import extractor_agent
from app.agents.verifier import verifier_agent
from app.agents.analyst import sufficiency_agent, analyst_agent
from app.agents.conflict_detector import conflict_detector_agent
from app.agents.writer import writer_agent
from app.services.citations import map_citations
from app.services.confidence import calculate_confidence
from app.agents.state import ResearchState


class ResearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_research(self, query: str, depth: str = "standard") -> str:
        research_id = uuid4()

        session = ResearchSession(
            id=research_id,
            query=query,
            research_depth=depth,
            status=ResearchStatus.PLANNING.value,
            started_at=datetime.utcnow(),
        )
        self.db.add(session)
        await self.db.flush()

        state = ResearchState(
            research_id=str(research_id),
            user_query=query,
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[],
            evidence=[],
            verified_claims=[],
            conflicts=[],
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=0,
            status="planning",
            errors=[],
            research_depth=depth,
        )

        try:
            state = {**state, **await planner_agent(state)}
            await self._log(research_id, "planner", "Created research plan", "planning", "completed")

            state = {**state, **await researcher_agent(state)}
            await self._log(research_id, "researcher", "Searched web sources", "researching", "completed")

            state = {**state, **await extractor_agent(state)}
            await self._log(research_id, "extractor", "Extracted evidence", "extracting", "completed")

            state = {**state, **await verifier_agent(state)}
            await self._log(research_id, "verifier", "Verified claims", "verifying", "completed")

            state = {**state, **await sufficiency_agent(state)}

            if state.get("status") == "researching":
                state = {**state, **await researcher_agent(state)}
                state = {**state, **await extractor_agent(state)}
                state = {**state, **await verifier_agent(state)}

            state = {**state, **await analyst_agent(state)}
            await self._log(research_id, "analyst", "Analyzed findings", "analyzing", "completed")

            state = {**state, **await conflict_detector_agent(state)}
            await self._log(research_id, "conflict_detector", "Detected conflicts", "analyzing", "completed")

            citations = map_citations(state.get("verified_claims", []), state.get("sources", []))
            state["citations"] = citations
            state["confidence_scores"] = calculate_confidence(state.get("verified_claims", []))

            state = {**state, **await writer_agent(state)}
            await self._log(research_id, "writer", "Generated report", "writing", "completed")

            await self._save_results(research_id, state)

            session.status = ResearchStatus.COMPLETED.value
            session.completed_at = datetime.utcnow()

        except Exception as e:
            session.status = ResearchStatus.FAILED.value
            await self._log(research_id, "system", f"Error: {str(e)}", "failed", "failed")

        return str(research_id)

    async def _log(self, research_id, agent_name, action, status, log_status):
        log = AgentLog(
            research_id=research_id,
            agent_name=agent_name,
            action=action,
            status=log_status,
        )
        self.db.add(log)

    async def _save_results(self, research_id, state):
        for source in state.get("sources", []):
            db_source = Source(
                research_id=research_id,
                title=source.get("title", ""),
                url=source.get("url", ""),
                domain=source.get("domain"),
                source_type=source.get("source_type", "unknown"),
                relevance_score=source.get("relevance_score", 0.0),
                reliability_score=source.get("reliability_score", 0.0),
                search_query=source.get("search_query"),
            )
            self.db.add(db_source)

        for claim in state.get("verified_claims", []):
            evidence = Evidence(
                research_id=research_id,
                source_id=claim.get("source_id"),
                claim=claim.get("claim", ""),
                evidence_text=claim.get("evidence_text", ""),
                evidence_type=claim.get("evidence_type", "factual"),
                confidence_score=claim.get("confidence", 0.0),
            )
            self.db.add(evidence)

        for citation in state.get("citations", []):
            db_citation = Citation(
                research_id=research_id,
                claim=citation.get("claim", ""),
                source_id=citation.get("source_id"),
                citation_number=citation.get("citation_number", 0),
            )
            self.db.add(db_citation)

        report_data = state.get("report", {})
        if report_data:
            report = Report(
                research_id=research_id,
                title=report_data.get("title", "Research Report"),
                findings=report_data.get("content"),
            )
            self.db.add(report)
```

- [ ] **Step 2: Write test for research service**

Create `tests/test_research_service.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.research import ResearchService


@pytest.mark.asyncio
async def test_research_service_initializes():
    mock_db = AsyncMock()
    service = ResearchService(mock_db)
    assert service.db == mock_db
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/test_research_service.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/research.py tests/test_research_service.py
git commit -m "feat: research service orchestrating all agents"
```

---

## Task 19: API Endpoints

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/health.py`
- Create: `backend/app/api/research.py`
- Create: `backend/app/api/reports.py`
- Create: `backend/app/api/sources.py`
- Create: `backend/app/api/history.py`
- Create: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: ResearchService from Task 18, database from Task 2
- Produces: FastAPI router with all endpoints

- [ ] **Step 1: Create api/health.py**

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "agentic-research-assistant"}
```

- [ ] **Step 2: Create api/research.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.schemas.research import StartResearchRequest, ResearchResponse
from app.services.research import ResearchService

router = APIRouter()


@router.post("/api/research", response_model=ResearchResponse)
async def start_research(
    request: StartResearchRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ResearchService(db)
    research_id = await service.start_research(
        query=request.query,
        depth=request.depth,
    )
    return ResearchResponse(research_id=research_id, status="started")
```

- [ ] **Step 3: Create api/sources.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.database import get_db
from app.database.models import Source

router = APIRouter()


@router.get("/api/research/{research_id}/sources")
async def get_sources(research_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Source).where(Source.research_id == research_id)
    )
    sources = result.scalars().all()
    return {
        "sources": [
            {
                "id": str(s.id),
                "title": s.title,
                "url": s.url,
                "domain": s.domain,
                "source_type": s.source_type,
                "relevance_score": s.relevance_score,
                "reliability_score": s.reliability_score,
            }
            for s in sources
        ],
        "total": len(sources),
    }
```

- [ ] **Step 4: Create api/reports.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.database import get_db
from app.database.models import Report

router = APIRouter()


@router.get("/api/research/{research_id}/report")
async def get_report(research_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).where(Report.research_id == research_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        return {"error": "Report not found"}
    return {
        "id": str(report.id),
        "title": report.title,
        "findings": report.findings,
        "created_at": report.created_at.isoformat(),
    }
```

- [ ] **Step 5: Create api/history.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.database import get_db
from app.database.models import ResearchSession

router = APIRouter()


@router.get("/api/history")
async def get_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResearchSession).order_by(ResearchSession.created_at.desc()).limit(50)
    )
    sessions = result.scalars().all()
    return {
        "history": [
            {
                "research_id": str(s.id),
                "query": s.query,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in sessions
        ]
    }
```

- [ ] **Step 6: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api import health, research, reports, sources, history

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(research.router)
app.include_router(reports.router)
app.include_router(sources.router)
app.include_router(history.router)
```

- [ ] **Step 7: Write test for API**

Create `tests/test_api.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_history_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/history")
        assert response.status_code == 200
```

- [ ] **Step 8: Run tests**

Run: `cd backend && python -m pytest tests/test_api.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add backend/app/api/ backend/app/main.py tests/test_api.py
git commit -m "feat: FastAPI endpoints for research, sources, reports, history"
```

---

## Task 20: SSE Progress Streaming

**Files:**
- Modify: `backend/app/api/research.py`
- Create: `backend/tests/test_sse.py`

**Interfaces:**
- Consumes: ResearchService from Task 18
- Produces: `GET /api/research/{id}/stream` SSE endpoint

- [ ] **Step 1: Add SSE endpoint to api/research.py**

```python
from sse_starlette.sse import EventSourceResponse
import asyncio
import json


@router.get("/api/research/{research_id}/stream")
async def stream_research(research_id: str, db: AsyncSession = Depends(get_db)):
    async def event_generator():
        while True:
            result = await db.execute(
                select(ResearchSession).where(ResearchSession.id == research_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                yield {"event": "error", "data": json.dumps({"message": "Session not found"})}
                break

            yield {
                "event": "status",
                "data": json.dumps({
                    "research_id": str(research_id),
                    "status": session.status,
                }),
            }

            if session.status in ["completed", "failed"]:
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "research_id": str(research_id),
                        "status": session.status,
                    }),
                }
                break

            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())
```

- [ ] **Step 2: Run tests**

Run: `cd backend && python -m pytest tests/test_sse.py -v`
Expected: PASS (or skip if SSE testing is complex)

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/research.py
git commit -m "feat: SSE progress streaming for research sessions"
```

---

## Task 21: Embeddings and pgvector Memory

**Files:**
- Create: `backend/app/services/embeddings.py`
- Create: `backend/app/services/memory.py`
- Create: `backend/tests/test_memory.py`

**Interfaces:**
- Consumes: Settings from Task 1, database from Task 2
- Produces: `EmbeddingService.embed_text()`, `MemoryService.search_similar()`

- [ ] **Step 1: Create services/embeddings.py**

```python
import httpx
from app.core.config import get_settings


class EmbeddingService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.EMBEDDING_API_KEY
        self.model = settings.EMBEDDING_MODEL

    async def embed_text(self, text: str) -> list[float]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": text},
            )
            data = response.json()
            return data["data"][0]["embedding"]


embedding_service = EmbeddingService()
```

- [ ] **Step 2: Create services/memory.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embeddings import embedding_service


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_finding(self, research_id: str, content: str, metadata: dict = None):
        embedding = await embedding_service.embed_text(content)

        await self.db.execute(
            """INSERT INTO research_memory (research_id, content, embedding, metadata)
               VALUES (:research_id, :content, :embedding, :metadata)""",
            {
                "research_id": research_id,
                "content": content,
                "embedding": str(embedding),
                "metadata": str(metadata or {}),
            },
        )

    async def search_similar(self, query: str, limit: int = 5) -> list[dict]:
        embedding = await embedding_service.embed_text(query)

        result = await self.db.execute(
            """SELECT content, metadata, 1 - (embedding <=> :embedding) as similarity
               FROM research_memory
               ORDER BY embedding <=> :embedding
               LIMIT :limit""",
            {"embedding": str(embedding), "limit": limit},
        )

        return [{"content": r[0], "metadata": r[1], "similarity": r[2]} for r in result]
```

- [ ] **Step 3: Write test for memory**

Create `tests/test_memory.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.memory import MemoryService


@pytest.mark.asyncio
async def test_memory_service_initializes():
    mock_db = AsyncMock()
    service = MemoryService(mock_db)
    assert service.db == mock_db
```

- [ ] **Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_memory.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/embeddings.py backend/app/services/memory.py tests/test_memory.py
git commit -m "feat: embeddings and pgvector research memory"
```

---

## Task 22: Error Handling and Logging

**Files:**
- Create: `backend/app/core/exceptions.py`
- Create: `backend/app/core/logging.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: None
- Produces: Custom exceptions, logging configuration

- [ ] **Step 1: Create core/exceptions.py**

```python
class ResearchError(Exception):
    pass


class LLMError(ResearchError):
    pass


class SearchError(ResearchError):
    pass


class ExtractionError(ResearchError):
    pass


class DatabaseError(ResearchError):
    pass
```

- [ ] **Step 2: Create core/logging.py**

```python
import logging
from app.core.config import get_settings


def setup_logging():
    settings = get_settings()
    level = logging.DEBUG if settings.APP_ENV == "development" else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    return logging.getLogger("research-agent")


logger = setup_logging()
```

- [ ] **Step 3: Add exception handler to main.py**

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import ResearchError


@app.exception_handler(ResearchError)
async def research_error_handler(request: Request, exc: ResearchError):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__},
    )
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/exceptions.py backend/app/core/logging.py backend/app/main.py
git commit -m "feat: error handling and logging configuration"
```

---

## Task 23: Utility Functions

**Files:**
- Create: `backend/app/utils/__init__.py`
- Create: `backend/app/utils/text.py`
- Create: `backend/app/utils/urls.py`
- Create: `backend/app/utils/hashing.py`
- Create: `backend/tests/test_utils.py`

**Interfaces:**
- Consumes: None
- Produces: `normalize_url()`, `hash_content()`, `truncate_text()`

- [ ] **Step 1: Create utils/urls.py**

```python
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


def normalize_url(url: str) -> str:
    parsed = urlparse(url)

    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]

    path = parsed.path.rstrip("/")

    query_params = parse_qs(parsed.query)
    utm_params = {k: v for k, v in query_params.items() if not k.startswith("utm_")}
    query = urlencode(utm_params, doseq=True) if utm_params else ""

    normalized = urlunparse((
        parsed.scheme,
        domain,
        path,
        parsed.params,
        query,
        "",
    ))

    return normalized
```

- [ ] **Step 2: Create utils/hashing.py**

```python
import hashlib


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def hash_url(url: str) -> str:
    from app.utils.urls import normalize_url
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode()).hexdigest()
```

- [ ] **Step 3: Create utils/text.py**

```python
def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_whitespace(text: str) -> str:
    return " ".join(text.split())
```

- [ ] **Step 4: Write test for utils**

Create `tests/test_utils.py`:

```python
from app.utils.urls import normalize_url
from app.utils.text import truncate_text, clean_whitespace
from app.utils.hashing import hash_content


def test_normalize_url_strips_utm():
    url = "https://www.example.com/article?utm_source=newsletter&id=123"
    normalized = normalize_url(url)
    assert "utm_" not in normalized
    assert "id=123" in normalized


def test_normalize_url_removes_www():
    url = "https://www.example.com/article"
    normalized = normalize_url(url)
    assert "www." not in normalized


def test_normalize_url_strips_trailing_slash():
    url = "https://example.com/article/"
    normalized = normalize_url(url)
    assert not normalized.endswith("/")


def test_truncate_text():
    result = truncate_text("Hello world", max_length=5)
    assert result == "Hello..."


def test_clean_whitespace():
    result = clean_whitespace("  Hello   world  ")
    assert result == "Hello world"


def test_hash_content():
    h = hash_content("test")
    assert len(h) == 64
```

- [ ] **Step 5: Run tests**

Run: `cd backend && python -m pytest tests/test_utils.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/utils/ tests/test_utils.py
git commit -m "feat: utility functions for URL normalization, hashing, text"
```

---

## Task 24: Final Integration Test

**Files:**
- Create: `backend/tests/test_integration.py`

**Interfaces:**
- Consumes: All previous tasks
- Produces: End-to-end integration test

- [ ] **Step 1: Create integration test**

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.research import ResearchService
from app.agents.state import ResearchState


@pytest.mark.asyncio
async def test_full_research_flow():
    mock_db = AsyncMock()
    service = ResearchService(mock_db)

    with patch("app.services.research.planner_agent") as mock_planner, \
         patch("app.services.research.researcher_agent") as mock_researcher, \
         patch("app.services.research.extractor_agent") as mock_extractor, \
         patch("app.services.research.verifier_agent") as mock_verifier, \
         patch("app.services.research.sufficiency_agent") as mock_sufficiency, \
         patch("app.services.research.analyst_agent") as mock_analyst, \
         patch("app.services.research.conflict_detector_agent") as mock_conflict, \
         patch("app.services.research.writer_agent") as mock_writer:

        mock_planner.return_value = {"research_plan": [{"id": 1, "task": "Test"}]}
        mock_researcher.return_value = {"sources": [{"url": "https://test.com"}]}
        mock_extractor.return_value = {"evidence": [{"claim": "Test claim"}]}
        mock_verifier.return_value = {"verified_claims": [{"claim": "Test", "verification_status": "supported"}]}
        mock_sufficiency.return_value = {"status": "verifying"}
        mock_analyst.return_value = {"analysis": "Test analysis"}
        mock_conflict.return_value = {"conflicts": []}
        mock_writer.return_value = {"report": {"title": "Test Report", "content": "..."}}

        research_id = await service.start_research(
            query="What is the impact of AI?",
            depth="quick",
        )

        assert research_id is not None
        assert mock_db.add.called
```

- [ ] **Step 2: Run integration test**

Run: `cd backend && python -m pytest tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_integration.py
git commit -m "feat: integration test for full research flow"
```

---

## Task 25: Run All Tests

- [ ] **Step 1: Run full test suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Fix any failures**

Address any failing tests.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore: all tests passing, backend MVP complete"
```
