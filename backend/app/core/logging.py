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
            # stdout is block-buffered when redirected to a file, which hides exactly the
            # failure traces this logger exists to produce.
            handler.flush()
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

    def _emit(self, level: str, message: str, data: dict = None, exc_info=None) -> None:
        log = getattr(self.logger, level.lower())
        extra = ""
        if data:
            non_empty = {k: v for k, v in data.items() if v not in (None, [], {})}
            if non_empty:
                extra = " " + " ".join(f"{k}={v}" for k, v in non_empty.items())
        log(f"[{level}] {message}{extra}", exc_info=exc_info)
        for handler in self.logger.handlers:
            handler.flush()

    def info(self, message: str, data: dict = None):
        self._emit("INFO", message, data)

    def error(self, message: str, data: dict = None, exc_info=None):
        """`exc_info` may be an exception instance, True, or None.

        An exception instance is rendered by the underlying logging machinery, so the
        traceback reaches the server log while `data` stays the only structured payload.
        """
        self._emit("ERROR", message, data, exc_info)

    def warning(self, message: str, data: dict = None):
        self._emit("WARNING", message, data)

    def debug(self, message: str, data: dict = None):
        self._emit("DEBUG", message, data)


logger = StructuredLogger("agentic-research-assistant")
