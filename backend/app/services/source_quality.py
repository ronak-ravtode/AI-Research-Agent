from typing import Optional

SOURCE_TYPE_AUTHORITY = {
    "academic": 0.9,
    "government": 0.85,
    "official": 0.8,
    "industry": 0.7,
    "news": 0.6,
    "blog": 0.4,
    "forum": 0.3,
    "unknown": 0.3,
}

def classify_source_type(url: str, domain: Optional[str] = None) -> str:
    if not domain:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

    if any(d in domain for d in [".edu", ".ac."]):
        return "academic"
    if any(d in domain for d in [".gov", ".mil"]):
        return "government"
    if any(d in domain for d in ["arxiv.org", "ieee.org", "acm.org", "springer.com"]):
        return "academic"
    if any(d in domain for d in ["reuters.com", "apnews.com", "bbc.com", "nytimes.com"]):
        return "news"
    if any(d in domain for d in ["medium.com", "substack.com", "dev.to"]):
        return "blog"
    if any(d in domain for d in ["reddit.com", "stackoverflow.com", "quora.com"]):
        return "forum"
    return "unknown"

def score_source(
    url: str,
    domain: Optional[str] = None,
    relevance_score: float = 0.5,
    evidence_quality: float = 0.5,
    cross_source_agreement: float = 0.5,
) -> float:
    source_type = classify_source_type(url, domain)
    authority = SOURCE_TYPE_AUTHORITY.get(source_type, 0.3)

    reliability = (
        authority * 0.30
        + relevance_score * 0.25
        + 0.5 * 0.20
        + evidence_quality * 0.15
        + cross_source_agreement * 0.10
    )

    return round(min(max(reliability, 0.0), 1.0), 2)
