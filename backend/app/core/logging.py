import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any


class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _format(self, level: str, message: str, data: dict = None) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "data": data or {},
        }
        return json.dumps(log_entry)

    def info(self, message: str, data: dict = None):
        self.logger.info(self._format("INFO", message, data))

    def error(self, message: str, data: dict = None, exc_info=None):
        """`exc_info` may be an exception instance, True, or None.

        An exception instance is rendered by the underlying logging machinery, so the
        traceback reaches the server log while `data` stays the only structured payload.
        """
        self.logger.error(self._format("ERROR", message, data), exc_info=exc_info)

    def warning(self, message: str, data: dict = None):
        self.logger.warning(self._format("WARNING", message, data))

    def debug(self, message: str, data: dict = None):
        self.logger.debug(self._format("DEBUG", message, data))


logger = StructuredLogger("agentic-research-assistant")
