from app.tools.tavily_search import tavily_search

__all__ = ["tavily_search"]


def get_firecrawl_extract():
    from app.tools.firecrawl_extract import firecrawl_extract
    return firecrawl_extract
