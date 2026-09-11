from urllib.parse import urlparse

def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc

def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])
    except Exception:
        return False