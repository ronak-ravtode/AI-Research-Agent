from app.services.confidence import calculate_confidence


def test_confidence_empty():
    result = calculate_confidence([])
    assert result["overall"] == 0.0


def test_confidence_all_supported():
    claims = [
        {"claim": "A", "verification_status": "supported", "confidence": 0.9},
        {"claim": "B", "verification_status": "supported", "confidence": 0.8},
    ]
    result = calculate_confidence(claims)
    assert result["overall"] > 0.8
    assert result["summary"]["supported"] == 2


def test_confidence_mixed():
    claims = [
        {"claim": "A", "verification_status": "supported", "confidence": 0.9},
        {"claim": "B", "verification_status": "contradicted", "confidence": 0.7},
    ]
    result = calculate_confidence(claims)
    assert 0.0 <= result["overall"] <= 1.0
    assert result["summary"]["contradicted"] == 1