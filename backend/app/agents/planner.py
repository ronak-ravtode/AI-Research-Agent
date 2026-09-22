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

    try:
        plan = await llm_service.structured_generate(
            prompt=prompt,
            system_prompt=PLANNER_SYSTEM_PROMPT,
            temperature=0.3,
        )
    except Exception:
        plan = {
            "subtasks": [
                {"id": 1, "task": f"Research: {query}", "priority": "high"}
            ]
        }

    return {
        "research_plan": plan.get("subtasks", []),
        "status": "planning",
    }
