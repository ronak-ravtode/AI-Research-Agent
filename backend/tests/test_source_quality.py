from app.services.source_quality import classify_source_type, score_source

def test_classify_academic():
    assert classify_source_type("https://arxiv.org/abs/2301.00001") == "academic"

def test_classify_government():
    assert classify_source_type("https://www.whitehouse.gov/report") == "government"

def test_classify_news():
    assert classify_source_type("https://www.reuters.com/article") == "news"

def test_classify_unknown():
    assert classify_source_type("https://random-blog.com/post") == "unknown"

def test_score_source_range():
    score = score_source("https://arxiv.org/paper", relevance_score=0.8)
    assert 0.0 <= score <= 1.0
    assert score > 0.5

def test_score_source_low():
    score = score_source("https://forum.example.com", relevance_score=0.2)
    assert score < 0.5
