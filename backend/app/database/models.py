import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.database.database import Base

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

TERMINAL_STATUSES = (STATUS_COMPLETED, STATUS_FAILED)

RETRIEVAL_FIRECRAWL = "firecrawl"
RETRIEVAL_SNIPPET = "tavily_snippet"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default=STATUS_QUEUED)
    current_stage = Column(String(50), nullable=True)
    progress_message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    sources = relationship(
        "Source", back_populates="session", cascade="all, delete-orphan"
    )
    reports = relationship(
        "Report", back_populates="session", cascade="all, delete-orphan"
    )
    activity = relationship(
        "ResearchActivity", back_populates="session", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("status", STATUS_QUEUED)
        kwargs.setdefault("created_at", _utcnow())
        kwargs.setdefault("updated_at", _utcnow())
        super().__init__(**kwargs)


class Source(Base):
    __tablename__ = "sources"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("research_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=True)
    source_type = Column(String(50), nullable=False, default="Web article")
    snippet = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    retrieval_method = Column(String(20), nullable=False, default=RETRIEVAL_SNIPPET)
    search_score = Column(Float, nullable=False, default=0.0)
    retrieved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    session = relationship("ResearchSession", back_populates="sources")

    def __init__(self, **kwargs):
        kwargs.setdefault("source_type", "Web article")
        kwargs.setdefault("retrieval_method", RETRIEVAL_SNIPPET)
        kwargs.setdefault("search_score", 0.0)
        kwargs.setdefault("created_at", _utcnow())
        super().__init__(**kwargs)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("research_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(500), nullable=False)
    answer_markdown = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    session = relationship("ResearchSession", back_populates="reports")

    def __init__(self, **kwargs):
        kwargs.setdefault("created_at", _utcnow())
        super().__init__(**kwargs)


class ResearchActivity(Base):
    """Append-only timeline of real workflow events.

    Doubles as the change signal for SSE: a client remembers the highest id it has seen
    and asks for everything above it, so an event is emitted only when one really happened.
    """

    __tablename__ = "research_activity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("research_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    session = relationship("ResearchSession", back_populates="activity")

    def __init__(self, **kwargs):
        kwargs.setdefault("created_at", _utcnow())
        super().__init__(**kwargs)
