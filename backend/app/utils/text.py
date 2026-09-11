def truncate_text(text: str, max_length: int = 500) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def clean_text(text: str) -> str:
    import re
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_key_phrases(text: str) -> list[str]:
    import re
    patterns = [
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
        r'\b\d+(?:\.\d+)?(?:\s*%)\b',
    ]
    phrases = []
    for pattern in patterns:
        phrases.extend(re.findall(pattern, text))
    return list(set(phrases))