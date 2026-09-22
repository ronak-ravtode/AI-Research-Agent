from app.services.llm import llm_service
from app.agents.state import ResearchState

SUFFICIENCY_PROMPT = """You are a research sufficiency evaluator. Determine if the current evidence is sufficient to answer the research question.

Research question: {question}
Evidence collected: {evidence_count} claims from {source_count} sources
Research depth: {depth}
Current iteration: {iteration}
Max iterations: {max_iterations}

Respond in JSON:
{{
    "sufficient": true/false,
    "reason": "...",
    "next_searches": ["query1", "query2"]
}}"""

ANALYSIS_PROMPT = """You are a research analyst. Analyze the verified evidence to identify patterns, comparisons, and conclusions.

Research question: {question}

Verified claims:
{claims}

Respond in JSON:
{{
    "key_findings": ["finding1", "finding2"],
    "patterns": ["pattern1"],
    "comparison": "...",
    "conclusion": "...",
    "gaps": ["gap1"]
}}"""

MAX_ITERATIONS = {"quick": 1, "standard": 2, "deep": 4}


async def sufficiency_agent(state: ResearchState) -> dict:
    depth = state.get("research_depth", "standard")
    iteration = state.get("iteration", 0)
    max_iter = MAX_ITERATIONS.get(depth, 2)

    if iteration >= max_iter:
        return {"status": "analyzing"}

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

    try:
        result = await llm_service.structured_generate(
            prompt=prompt,
            temperature=0.2,
        )
    except Exception:
        return {"status": "analyzing"}

    if result.get("sufficient", False):
        return {"status": "analyzing"}

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

    try:
        result = await llm_service.structured_generate(
            prompt=prompt,
            temperature=0.3,
        )
    except Exception:
        return {
            "analysis": "Analysis could not be completed due to processing errors.",
            "status": "analyzing",
        }

    return {
        "analysis": result.get("conclusion", ""),
        "status": "analyzing",
    }
