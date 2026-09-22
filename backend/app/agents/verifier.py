from app.services.llm import llm_service
from app.agents.state import ResearchState

VERIFIER_SYSTEM_PROMPT = """You are a claim verification agent. Verify whether the evidence supports the claims.

For each claim, determine:
1. Whether the evidence supports it (supported, partially_supported, unsupported, contradicted)
2. A confidence score (0.0 to 1.0)
3. A brief explanation

Respond in JSON format:
{
    "verified_claims": [
        {
            "claim": "...",
            "evidence": "...",
            "source_url": "...",
            "verification_status": "supported",
            "confidence": 0.9,
            "reason": "..."
        }
    ]
}"""


async def verifier_agent(state: ResearchState) -> dict:
    evidence = state.get("evidence", [])
    query = state.get("user_query", "")

    verified = []

    for item in evidence:
        prompt = f"""Research question: {query}

Claim: {item.get('claim', '')}
Evidence: {item.get('evidence_text', '')}
Source: {item.get('source_url', '')}

Verify this claim."""

        try:
            result = await llm_service.structured_generate(
                prompt=prompt,
                system_prompt=VERIFIER_SYSTEM_PROMPT,
                temperature=0.2,
            )

            for v in result.get("verified_claims", []):
                verified.append({
                    **item,
                    "verification_status": v.get("verification_status", "unsupported"),
                    "confidence": v.get("confidence", 0.5),
                    "reason": v.get("reason", ""),
                })
        except Exception:
            verified.append({
                **item,
                "verification_status": "unsupported",
                "confidence": 0.0,
                "reason": "Verification failed",
            })

    return {
        "verified_claims": verified,
        "status": "verifying",
    }
