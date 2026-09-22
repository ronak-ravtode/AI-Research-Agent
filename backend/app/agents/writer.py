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
    confidence_scores = state.get("confidence_scores", {})

    citations_text = "\n".join([
        f"[{c.get('citation_number', i+1)}] {c.get('source_url', '')}"
        for i, c in enumerate(citations)
    ])

    confidence_text = ""
    if confidence_scores:
        overall = confidence_scores.get("overall", 0.0)
        summary = confidence_scores.get("summary", {})
        confidence_text = f"Overall confidence: {overall}\n"
        if isinstance(summary, dict):
            confidence_text += (
                f"Supported: {summary.get('supported', 0)}, "
                f"Partially: {summary.get('partially_supported', 0)}, "
                f"Unsupported: {summary.get('unsupported', 0)}, "
                f"Contradicted: {summary.get('contradicted', 0)}"
            )

    prompt = f"""Research question: {state.get('user_query', '')}

Verified claims:
{chr(10).join([f"- [{c.get('verification_status', 'unknown')}] {c.get('claim', '')}" for c in verified_claims])}

Conflicts:
{chr(10).join([f"- {c.get('topic', '')}: {c.get('possible_explanation', '')}" for c in conflicts])}

Analysis: {analysis}

Confidence: {confidence_text}

Citations:
{citations_text}

Generate the research report."""

    try:
        report_text = await llm_service.generate(
            prompt=prompt,
            system_prompt=WRITER_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception:
        report_text = f"# Research Report\n\n## Research Question\n{state.get('user_query', '')}\n\n## Analysis\n{analysis}\n\n## Claims\n" + "\n".join([
            f"- {c.get('claim', '')} ({c.get('verification_status', 'unknown')})"
            for c in verified_claims
        ])

    return {
        "report": {
            "title": f"Research Report: {state.get('user_query', '')[:100]}",
            "content": report_text,
            "citations": citations,
        },
        "status": "writing",
    }
