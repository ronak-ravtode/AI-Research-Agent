import pytest
from app.core.logging import StructuredLogger


def test_logger_initializes():
    logger = StructuredLogger("test")
    assert logger.logger.name == "test"


def test_logger_format():
    logger = StructuredLogger("test")
    result = logger._format("INFO", "test message")
    assert "INFO" in result
    assert "test message" in result
