import logging
import json
from datetime import datetime
from typing import Any


class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _format(self, level: str, message: str, data: dict = None) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "data": data or {},
        }
        return json.dumps(log_entry)

    def info(self, message: str, data: dict = None):
        self.logger.info(self._format("INFO", message, data))

    def error(self, message: str, data: dict = None):
        self.logger.error(self._format("ERROR", message, data))

    def warning(self, message: str, data: dict = None):
        self.logger.warning(self._format("WARNING", message, data))


logger = StructuredLogger("agentic-research-assistant")
