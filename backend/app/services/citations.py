from uuid import uuid4


def map_citations(verified_claims: list[dict], sources: list[dict]) -> list[dict]:
    source_url_to_id = {s.get("url"): s.get("id") for s in sources}
    citations = []
    citation_counter = 1
    seen_claims = set()

    for claim in verified_claims:
        claim_text = claim.get("claim", "")
        source_url = claim.get("source_url", "")

        if claim_text in seen_claims:
            continue

        source_id = claim.get("source_id") or source_url_to_id.get(source_url)

        if not source_id:
            continue

        citations.append({
            "id": str(uuid4()),
            "claim": claim_text,
            "source_id": source_id,
            "source_url": source_url,
            "citation_number": citation_counter,
        })

        citation_counter += 1
        seen_claims.add(claim_text)

    return citations
