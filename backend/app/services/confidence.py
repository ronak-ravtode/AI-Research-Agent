from typing import Any


def calculate_confidence(verified_claims: list[dict]) -> dict:
    if not verified_claims:
        return {"overall": 0.0, "claim_scores": [], "summary": "No claims to evaluate"}

    claim_scores = []
    supported = 0
    partial = 0
    unsupported = 0
    contradicted = 0

    for claim in verified_claims:
        status = claim.get("verification_status", "unsupported")
        confidence = claim.get("confidence", 0.0)

        if status == "supported":
            supported += 1
        elif status == "partially_supported":
            partial += 1
        elif status == "contradicted":
            contradicted += 1
        else:
            unsupported += 1

        claim_scores.append({
            "claim": claim.get("claim", ""),
            "status": status,
            "confidence": confidence,
        })

    total = len(verified_claims)
    supported_ratio = supported / total
    partial_ratio = partial / total
    contradicted_penalty = contradicted / total

    overall = (supported_ratio * 0.9 + partial_ratio * 0.5 - contradicted_penalty * 0.3)
    overall = max(0.0, min(1.0, overall))

    return {
        "overall": round(overall, 2),
        "claim_scores": claim_scores,
        "summary": {
            "total": total,
            "supported": supported,
            "partially_supported": partial,
            "unsupported": unsupported,
            "contradicted": contradicted,
        },
    }