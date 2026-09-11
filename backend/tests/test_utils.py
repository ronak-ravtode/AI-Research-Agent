import pytest
from app.utils.text import truncate_text, clean_text, extract_key_phrases
from app.utils.url import extract_domain, is_valid_url

def test_truncate_text():
    assert truncate_text("short", 10) == "short"
    assert len(truncate_text("a" * 20, 10)) == 13

def test_clean_text():
    assert clean_text("  hello   world  ") == "hello world"

def test_extract_key_phrases():
    phrases = extract_key_phrases("John Smith visited New York")
    assert "John Smith" in phrases or "New York" in phrases

def test_extract_domain():
    assert extract_domain("https://example.com/path") == "example.com"

def test_is_valid_url():
    assert is_valid_url("https://example.com") is True
    assert is_valid_url("not-a-url") is False