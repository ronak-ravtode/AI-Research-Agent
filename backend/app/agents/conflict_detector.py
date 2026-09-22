from app.services.llm import llm_service
from app.agents.state import ResearchState

CONFLICT_PROMPT = """You are a conflict detection agent. Identify contradictions or disagreements in the verified claims.

Research question: {question}

Verified claims:
{claims}

Respond in JSON:
{{
    "conflicts": [
        {{
            "topic": "...",
            "claim_a": {{"text": "...", "source": "...", "value": "..."}},
            "claim_b": {{"text": "...", "source": "...", "value": "..."}},
            "possible_explanation": "...",
            "severity": "high|medium|low"
        }}
    ]
}}

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

    try:
        result = await llm_service.structured_generate(
            prompt=prompt,
            temperature=0.2,
        )
    except Exception:
        return {"conflicts": [], "status": "analyzing"}

    return {
        "conflicts": result.get("conflicts", []),
        "status": "analyzing",
    }
