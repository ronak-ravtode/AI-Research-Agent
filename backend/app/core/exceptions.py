"""Error contract for the research pipeline.

Every failure the workflow can produce is one of these. Each carries a short, user-safe
message that may be shown to the browser; the underlying cause is only ever written to the
server log. Never build one of these messages from an exception string, a traceback, or a
credential.
"""


class ResearchRunError(Exception):
    """Base class for any failure that should end a research run.

    `user_message` is deliberately conservative: it says what went wrong without leaking
    provider names, hostnames, keys, or stack traces.
    """

    user_message = "Research could not be completed. Please try again."
    error_code = "RESEARCH_ERROR"

    def __init__(self, detail: str = "", error_code: str = None):
        self.detail = detail
        if error_code:
            self.error_code = error_code
        super().__init__(detail or self.user_message)


class SearchError(ResearchRunError):
    user_message = "The web search could not be reached. Please try again in a moment."
    error_code = "SEARCH_ERROR"


class NoResultsError(ResearchRunError):
    user_message = "No usable sources were found for that question. Try rephrasing it."
    error_code = "NO_RESULTS_ERROR"


class ExtractionError(ResearchRunError):
    user_message = "Could not read any source pages. Please try again."
    error_code = "EXTRACTION_ERROR"


class ReportGenerationError(ResearchRunError):
    user_message = "The answer could not be written from the collected sources."
    error_code = "REPORT_ERROR"


class RateLimitError(ResearchRunError):
    user_message = "Rate limit reached on the AI model provider. Please wait a few moments before trying again."
    error_code = "RATE_LIMIT_ERROR"


class ConfigurationError(ResearchRunError):
    user_message = "The server is not configured correctly. Please contact the administrator."
    error_code = "CONFIG_ERROR"
