from langgraph.graph import StateGraph, END
from app.agents.state import ResearchState


def create_research_graph():
    """Create and compile the research agent workflow graph."""
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
