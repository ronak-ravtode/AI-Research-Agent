from uuid import uuid4
from app.services.llm import llm_service
from app.tools.tavily_search import tavily_search
from app.tools.firecrawl_extract import firecrawl_extract
from app.agents.state import ResearchState
from app.services.source_quality import score_source, classify_source_type
from urllib.parse import urlparse


SEARCH_QUERY_PROMPT = """Given this research task, generate a focused web search query.
Return only the search query text, nothing else.

Research task: {task}
Research objective: {objective}"""


def _normalize_url(url: str) -> str:
    """Normalize URL for deduplication."""
    from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
    parsed = urlparse(url)
    normalized_path = parsed.path.rstrip("/")
    query_params = parse_qs(parsed.query)
    utm_keys = [k for k in query_params if k.startswith("utm_")]
    for k in utm_keys:
        del query_params[k]
    normalized_query = urlencode(query_params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, normalized_path, parsed.params, normalized_query, ""))


def _deduplicate_sources(sources: list[dict]) -> list[dict]:
    """Remove duplicate sources by normalized URL."""
    seen = {}
    unique = []
    for src in sources:
        norm = _normalize_url(src.get("url", ""))
        if norm not in seen:
            seen[norm] = True
            unique.append(src)
    return unique


async def researcher_agent(state: ResearchState) -> dict:
    plan = state.get("research_plan", [])
    completed = state.get("completed_tasks", [])
    iteration = state.get("iteration", 0)
    existing_sources = state.get("sources", [])
    existing_queries = state.get("search_queries", [])

    tasks_to_research = [t for t in plan if t.get("id") not in completed]

    if not tasks_to_research and iteration > 0:
        if existing_queries:
            query = existing_queries[-1]
        else:
            return {"sources": [], "status": "researching"}
        task_id = None
        task_title = "follow-up search"
    else:
        task = tasks_to_research[0] if tasks_to_research else (plan[0] if plan else None)
        if not task:
            return {"sources": [], "status": "researching"}
        query_prompt = SEARCH_QUERY_PROMPT.format(
            task=task.get("task", ""),
            objective=state.get("user_query", ""),
        )
        query = await llm_service.generate(prompt=query_prompt, temperature=0.3)
        task_id = task.get("id")
        task_title = task.get("task", "")

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

        content = r.content
        if content and len(content) < 200:
            try:
                extracted = await firecrawl_extract.extract_url(r.url)
                if extracted.content and len(extracted.content) > len(content):
                    content = extracted.content
            except Exception:
                pass

        new_sources.append({
            "id": str(uuid4()),
            "title": r.title,
            "url": r.url,
            "domain": domain,
            "content": content,
            "source_type": source_type,
            "relevance_score": r.score,
            "reliability_score": reliability,
            "search_query": query,
            "task_id": task_id,
            "task_title": task_title,
        })

    all_sources = existing_sources + new_sources
    all_sources = _deduplicate_sources(all_sources)

    new_only = [s for s in all_sources if s not in existing_sources]

    return {
        "sources": new_only,
        "search_queries": [query],
        "status": "researching",
    }
