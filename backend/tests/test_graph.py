from app.agents.graph import create_research_graph
from app.agents.state import ResearchState


def test_graph_creates():
    """Test that the research graph can be created."""
    graph = create_research_graph()
    assert graph is not None


def test_research_state_has_required_keys():
    """Test that ResearchState has all required keys."""
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
