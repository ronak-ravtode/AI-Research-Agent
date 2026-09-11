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