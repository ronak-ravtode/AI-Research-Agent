from app.services.citations import map_citations

def test_map_citations_basic():
    claims = [
        {"claim": "AI improves productivity", "source_url": "https://a.com", "source_id": "s1"},
        {"claim": "AI reduces costs", "source_url": "https://b.com", "source_id": "s2"},
    ]
    sources = [{"id": "s1", "url": "https://a.com"}, {"id": "s2", "url": "https://b.com"}]

    citations = map_citations(claims, sources)
    assert len(citations) == 2
    assert citations[0]["citation_number"] == 1
    assert citations[1]["citation_number"] == 2

def test_map_citations_deduplicates():
    claims = [
        {"claim": "AI improves productivity", "source_url": "https://a.com", "source_id": "s1"},
        {"claim": "AI improves productivity", "source_url": "https://b.com", "source_id": "s2"},
    ]
    sources = [{"id": "s1", "url": "https://a.com"}, {"id": "s2", "url": "https://b.com"}]

    citations = map_citations(claims, sources)
    assert len(citations) == 1
