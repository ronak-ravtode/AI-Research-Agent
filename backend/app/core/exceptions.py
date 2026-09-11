class ResearchAgentError(Exception):
    def __init__(self, message: str, error_code: str = "UNKNOWN"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class LLMServiceError(ResearchAgentError):
    def __init__(self, message: str):
        super().__init__(message, error_code="LLM_ERROR")


class ToolExecutionError(ResearchAgentError):
    def __init__(self, message: str, tool_name: str = ""):
        self.tool_name = tool_name
        super().__init__(message, error_code="TOOL_ERROR")


class DatabaseError(ResearchAgentError):
    def __init__(self, message: str):
        super().__init__(message, error_code="DB_ERROR")
