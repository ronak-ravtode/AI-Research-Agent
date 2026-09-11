from app.services.llm import llm_service
from app.agents.state import ResearchState

WRITER_SYSTEM_PROMPT = """You are a research report writer. Generate a structured research report based on the provided data.

The report must include these sections:
1. Executive Summary
2. Research Question
3. Methodology
4. Key Findings
5. Comparative Analysis
6. Conflicting Evidence
7. Confidence Assessment
8. Conclusion
9. References

Use markdown formatting. Be factual and cite sources using [N] notation.
Do not introduce information not present in the provided data."""

async def writer_agent(state: ResearchState) -> dict:
    verified_claims = state.get("verified_claims", [])
    conflicts = state.get("conflicts", [])
    analysis = state.get("analysis", "")
    citations = state.get("citations", [])
    sources = state.get("sources", [])

    citations_text = "\n".join([
        f"[{c.get('citation_number', i+1)}] {c.get('source_url', '')}"
        for i, c in enumerate(citations)
    ])

    prompt = f"""Research question: {state.get('user_query', '')}

Verified claims:
{chr(10).join([f"- [{c.get('verification_status', 'unknown')}] {c.get('claim', '')}" for c in verified_claims])}

Conflicts:
{chr(10).join([f"- {c.get('topic', '')}: {c.get('possible_explanation', '')}" for c in conflicts])}

Analysis: {analysis}

Citations:
{citations_text}

Generate the research report."""

    report_text = await llm_service.generate(
        prompt=prompt,
        system_prompt=WRITER_SYSTEM_PROMPT,
        temperature=0.3,
        max_tokens=4096,
    )

    return {
        "report": {
            "title": f"Research Report: {state.get('user_query', '')[:100]}",
            "content": report_text,
            "citations": citations,
        },
        "status": "writing",
    }
