from langgraph.graph import StateGraph, END
from app.agents.state import ResearchState
from app.agents.planner import planner_agent
from app.agents.researcher import researcher_agent
from app.agents.extractor import extractor_agent
from app.agents.verifier import verifier_agent
from app.agents.analyst import sufficiency_agent, analyst_agent
from app.agents.conflict_detector import conflict_detector_agent
from app.agents.writer import writer_agent


def _should_continue_research(state: ResearchState) -> str:
    """Conditional edge: after verifier, check if more research is needed."""
    status = state.get("status", "")
    if status == "researching":
        return "researcher"
    return "analyst"


def create_research_graph():
    """Create and compile the research agent workflow graph."""
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner_agent)
    graph.add_node("researcher", researcher_agent)
    graph.add_node("extractor", extractor_agent)
    graph.add_node("verifier", verifier_agent)
    graph.add_node("sufficiency", sufficiency_agent)
    graph.add_node("analyst", analyst_agent)
    graph.add_node("conflict_detector", conflict_detector_agent)
    graph.add_node("writer", writer_agent)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "extractor")
    graph.add_edge("extractor", "verifier")
    graph.add_edge("verifier", "sufficiency")
    graph.add_conditional_edges(
        "sufficiency",
        _should_continue_research,
        {
            "researcher": "researcher",
            "analyst": "analyst",
        },
    )
    graph.add_edge("analyst", "conflict_detector")
    graph.add_edge("conflict_detector", "writer")
    graph.add_edge("writer", END)

    return graph.compile()
