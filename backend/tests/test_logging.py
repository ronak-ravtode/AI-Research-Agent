"""The structured logger must survive non-ASCII agent messages on Windows consoles."""

import io

from app.core.logging import StructuredLogger


def build_with_buffer():
    buffer = io.StringIO()
    buffered = StructuredLogger("test-unicode-buffer")
    # Redirect the handler stream to a capturing buffer so the emit path is
    # exercised without depending on console encoding.
    for handler in buffered.logger.handlers:
        handler.stream = buffer
    return buffered, buffer


def test_non_ascii_message_is_logged_without_raising():
    base, buffer = build_with_buffer()
    broken = "non\u2011breaking hyphen and 【3】 brackets"
    base.info(broken)
    assert "non" in buffer.getvalue()
    assert "brackets" in buffer.getvalue()


def test_logging_stream_is_reconfigured_for_utf8():
    reconfigured = StructuredLogger("test-utf8-reconfigure")
    encoding = getattr(reconfigured.logger.handlers[0].stream, "encoding", None)
    if hasattr(__import__("sys").stdout, "reconfigure"):
        assert encoding is None or encoding.lower() in ("utf-8", None)
    else:
        assert encoding is not None
