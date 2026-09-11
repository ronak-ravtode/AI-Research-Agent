from app.services.llm import llm_service
from app.agents.state import ResearchState

EXTRACTOR_SYSTEM_PROMPT = """You are an information extraction agent. Extract factual claims and evidence from the source content.

For each claim, provide:
1. The specific claim being made
2. The supporting evidence text from the source
3. The evidence type (factual, statistical, expert_opinion, anecdotal)
4. Importance score (0.0 to 1.0)

Respond in JSON format:
{
    "claims": [
        {
            "claim": "...",
            "evidence": "...",
            "evidence_type": "factual",
            "importance": 0.8
        }
    ]
}

Only extract claims that are directly supported by the source content."""


async def extractor_agent(state: ResearchState) -> dict:
    sources = state.get("sources", [])
    query = state.get("user_query", "")

    all_evidence = []

    for source in sources:
        content = source.get("content", "")
        if not content or len(content) < 100:
            continue

        prompt = f"""Research question: {query}

Source title: {source.get('title', 'Unknown')}
Source content:
{content[:3000]}"""

        try:
            result = await llm_service.structured_generate(
                prompt=prompt,
                system_prompt=EXTRACTOR_SYSTEM_PROMPT,
                temperature=0.2,
            )

            for claim in result.get("claims", []):
                all_evidence.append({
                    "source_id": source.get("id"),
                    "source_url": source.get("url"),
                    "claim": claim.get("claim", ""),
                    "evidence_text": claim.get("evidence", ""),
                    "evidence_type": claim.get("evidence_type", "factual"),
                    "confidence_score": claim.get("importance", 0.5),
                })
        except Exception:
            continue

    return {
        "evidence": all_evidence,
        "status": "extracting",
    }
