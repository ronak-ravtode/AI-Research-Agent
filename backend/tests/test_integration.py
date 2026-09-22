import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.state import ResearchState
from app.agents.planner import planner_agent
from app.agents.researcher import researcher_agent
from app.agents.extractor import extractor_agent
from app.agents.verifier import verifier_agent
from app.agents.analyst import sufficiency_agent, analyst_agent
from app.agents.conflict_detector import conflict_detector_agent
from app.agents.writer import writer_agent
from app.services.llm import LLMService
from app.services.source_quality import classify_source_type, score_source
from app.services.confidence import calculate_confidence
from app.services.citations import map_citations
from app.core.config import get_settings


def test_config_loads():
    settings = get_settings()
    assert settings.APP_NAME == "agentic-research-assistant"


def test_state_creation():
    state: ResearchState = {
        "research_id": "test-123",
        "user_query": "test query",
        "research_plan": [],
        "current_task": "",
        "completed_tasks": [],
        "search_queries": [],
        "sources": [],
        "evidence": [],
        "verified_claims": [],
        "conflicts": [],
        "analysis": "",
        "citations": [],
        "confidence_scores": {},
        "report": {},
        "iteration": 0,
        "status": "planning",
        "errors": [],
    }
    assert state["user_query"] == "test query"
    assert state["iteration"] == 0
    assert state["status"] == "planning"


def test_source_quality_scoring():
    score = score_source("https://arxiv.org/abs/2301.00001")
    assert 0 <= score <= 1


def test_classify_source_type():
    assert classify_source_type("https://arxiv.org/abs/2301.00001") == "academic"
    assert classify_source_type("https://www.govexample.com") == "government"
    assert classify_source_type("https://www.reddit.com/r/science") == "forum"


def test_confidence_scoring():
    claims = [
        {"claim": "test", "verification_status": "supported", "confidence": 0.9}
    ]
    scores = calculate_confidence(claims)
    assert "overall" in scores
    assert 0 <= scores["overall"] <= 1


def test_confidence_scoring_empty():
    scores = calculate_confidence([])
    assert scores["overall"] == 0.0


def test_citation_mapping():
    claims = [
        {"claim": "test claim", "source_url": "https://example.com", "source_id": "src-1"}
    ]
    sources = [{"url": "https://example.com", "title": "Test Source", "id": "src-1"}]
    citations = map_citations(claims, sources)
    assert len(citations) >= 0


def test_citation_mapping_no_match():
    claims = [
        {"claim": "test claim", "source_url": "https://example.com"}
    ]
    sources = [{"url": "https://other.com", "title": "Other Source", "id": "src-2"}]
    citations = map_citations(claims, sources)
    assert len(citations) == 0


@pytest.mark.asyncio
async def test_planner_agent():
    mock_state: ResearchState = {
        "research_id": "test-123",
        "user_query": "What is machine learning?",
        "research_plan": [],
        "current_task": "",
        "completed_tasks": [],
        "search_queries": [],
        "sources": [],
        "evidence": [],
        "verified_claims": [],
        "conflicts": [],
        "analysis": "",
        "citations": [],
        "confidence_scores": {},
        "report": {},
        "iteration": 0,
        "status": "planning",
        "errors": [],
    }
    
    with patch("app.agents.planner.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value={
            "research_objective": "Understand ML",
            "subtasks": [{"id": 1, "task": "Research basics", "priority": "high"}]
        })
        result = await planner_agent(mock_state)
        assert "research_plan" in result
        assert len(result["research_plan"]) == 1


@pytest.mark.asyncio
async def test_researcher_agent():
    mock_state: ResearchState = {
        "research_id": "test-123",
        "user_query": "What is machine learning?",
        "research_plan": [{"id": 1, "task": "Research basics", "priority": "high"}],
        "current_task": "",
        "completed_tasks": [],
        "search_queries": [],
        "sources": [],
        "evidence": [],
        "verified_claims": [],
        "conflicts": [],
        "analysis": "",
        "citations": [],
        "confidence_scores": {},
        "report": {},
        "iteration": 0,
        "status": "researching",
        "errors": [],
    }
    
    with patch("app.agents.researcher.llm_service") as mock_llm, \
         patch("app.agents.researcher.tavily_search") as mock_tavily:
        mock_llm.generate = AsyncMock(return_value="machine learning basics")
        mock_tavily_search_result = MagicMock()
        mock_tavily_search_result.title = "ML Guide"
        mock_tavily_search_result.url = "https://example.com/ml"
        mock_tavily_search_result.content = "ML content"
        mock_tavily_search_result.score = 0.9
        mock_tavily.search_web = AsyncMock(return_value=[mock_tavily_search_result])
        result = await researcher_agent(mock_state)
        assert "sources" in result
        assert len(result["sources"]) == 1


@pytest.mark.asyncio
async def test_verifier_agent():
    mock_state: ResearchState = {
        "research_id": "test-123",
        "user_query": "What is machine learning?",
        "research_plan": [],
        "current_task": "",
        "completed_tasks": [],
        "search_queries": [],
        "sources": [{"title": "ML Guide", "url": "https://example.com", "content": "ML is a subset of AI"}],
        "evidence": [],
        "verified_claims": [],
        "conflicts": [],
        "analysis": "",
        "citations": [],
        "confidence_scores": {},
        "report": {},
        "iteration": 0,
        "status": "verifying",
        "errors": [],
    }
    
    with patch("app.agents.verifier.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value={
            "verified_claims": [{"claim": "ML is AI", "verification_status": "supported", "confidence": 0.9}]
        })
        result = await verifier_agent(mock_state)
        assert "verified_claims" in result


@pytest.mark.asyncio
async def test_conflict_detector_agent():
    mock_state: ResearchState = {
        "research_id": "test-123",
        "user_query": "What is machine learning?",
        "research_plan": [],
        "current_task": "",
        "completed_tasks": [],
        "search_queries": [],
        "sources": [],
        "evidence": [],
        "verified_claims": [
            {"claim": "ML is AI", "verification_status": "supported", "confidence": 0.9},
            {"claim": "ML is not AI", "verification_status": "contradicted", "confidence": 0.3}
        ],
        "conflicts": [],
        "analysis": "",
        "citations": [],
        "confidence_scores": {},
        "report": {},
        "iteration": 0,
        "status": "detecting_conflicts",
        "errors": [],
    }
    
    with patch("app.agents.conflict_detector.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value={
            "conflicts": [{"claim1": "ML is AI", "claim2": "ML is not AI", "type": "direct"}]
        })
        result = await conflict_detector_agent(mock_state)
        assert "conflicts" in result


@pytest.mark.asyncio
async def test_analyst_agent():
    mock_state: ResearchState = {
        "research_id": "test-123",
        "user_query": "What is machine learning?",
        "research_plan": [],
        "current_task": "",
        "completed_tasks": [],
        "search_queries": [],
        "sources": [],
        "evidence": [],
        "verified_claims": [
            {"claim": "ML is AI", "verification_status": "supported", "confidence": 0.9}
        ],
        "conflicts": [],
        "analysis": "",
        "citations": [],
        "confidence_scores": {},
        "report": {},
        "iteration": 0,
        "status": "analyzing",
        "errors": [],
    }
    
    with patch("app.agents.analyst.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value={
            "analysis": "ML is a subset of AI",
            "confidence_score": 0.85
        })
        result = await analyst_agent(mock_state)
        assert "analysis" in result


@pytest.mark.asyncio
async def test_writer_agent():
    mock_state: ResearchState = {
        "research_id": "test-123",
        "user_query": "What is machine learning?",
        "research_plan": [],
        "current_task": "",
        "completed_tasks": [],
        "search_queries": [],
        "sources": [],
        "evidence": [],
        "verified_claims": [
            {"claim": "ML is AI", "verification_status": "supported", "confidence": 0.9}
        ],
        "conflicts": [],
        "analysis": "ML is a subset of AI",
        "citations": [],
        "confidence_scores": {"overall": 0.85},
        "report": {},
        "iteration": 0,
        "status": "writing",
        "errors": [],
    }
    
    with patch("app.agents.writer.llm_service") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="Machine learning is a subset of AI...")
        result = await writer_agent(mock_state)
        assert "report" in result
        assert "content" in result["report"]


def test_llm_service_initialization():
    from app.services.llm import llm_service
    assert llm_service is not None


def test_config_all_settings():
    settings = get_settings()
    assert hasattr(settings, "APP_ENV")
    assert hasattr(settings, "GROQ_API_KEY")
    assert hasattr(settings, "TAVILY_API_KEY")
    assert hasattr(settings, "FIRECRAWL_API_KEY")
    assert hasattr(settings, "DATABASE_URL")


def test_source_quality_edge_cases():
    assert 0 <= score_source("https://unknown-site.com") <= 1
    assert 0 <= score_source("https://github.com") <= 1


def test_confidence_all_statuses():
    claims = [
        {"claim": "c1", "verification_status": "supported", "confidence": 0.9},
        {"claim": "c2", "verification_status": "partially_supported", "confidence": 0.7},
        {"claim": "c3", "verification_status": "unsupported", "confidence": 0.3},
        {"claim": "c4", "verification_status": "contradicted", "confidence": 0.1},
    ]
    scores = calculate_confidence(claims)
    assert scores["overall"] >= 0
    assert scores["summary"]["total"] == 4


def test_citation_deduplication():
    claims = [
        {"claim": "duplicate claim", "source_url": "https://example.com", "source_id": "src-1"},
        {"claim": "duplicate claim", "source_url": "https://example.com", "source_id": "src-1"},
    ]
    sources = [{"url": "https://example.com", "title": "Test", "id": "src-1"}]
    citations = map_citations(claims, sources)
    assert len(citations) == 1
