from app.database.models import ResearchSession, Source, ResearchStatus


def test_research_session_creation():
    session = ResearchSession(query="Test query")
    assert session.query == "Test query"
    assert session.status == ResearchStatus.PLANNING.value


def test_source_creation():
    source = Source(title="Test", url="https://example.com")
    assert source.title == "Test"
    assert source.relevance_score == 0.0
