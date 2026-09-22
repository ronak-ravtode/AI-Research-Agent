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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.database import Base


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=True)
    query = Column(Text, nullable=False)
    research_depth = Column(String(50), nullable=False, default="standard")
    status = Column(String(50), nullable=False, default="planning")
    summary = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    tasks = relationship("ResearchTask", back_populates="session", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="session", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="session", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "planning")
        kwargs.setdefault("research_depth", "standard")
        kwargs.setdefault("created_at", datetime.now(timezone.utc))
        kwargs.setdefault("updated_at", datetime.now(timezone.utc))
        super().__init__(**kwargs)


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    task_number = Column(Integer, nullable=False, default=1)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="planning")
    agent_name = Column(String(100), nullable=True)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    session = relationship("ResearchSession", back_populates="tasks")
    evidence = relationship("Evidence", back_populates="task", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "planning")
        kwargs.setdefault("created_at", datetime.now(timezone.utc))
        super().__init__(**kwargs)


class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=True)
    author = Column(String(255), nullable=True)
    published_date = Column(String(100), nullable=True)
    source_type = Column(String(50), nullable=True, default="unknown")
    search_query = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    relevance_score = Column(Float, nullable=False, default=0.0)
    reliability_score = Column(Float, nullable=False, default=0.0)
    retrieved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    session = relationship("ResearchSession", back_populates="sources")
    evidence = relationship("Evidence", back_populates="source", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="source", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        kwargs.setdefault("relevance_score", 0.0)
        kwargs.setdefault("reliability_score", 0.0)
        kwargs.setdefault("source_type", "unknown")
        kwargs.setdefault("created_at", datetime.now(timezone.utc))
        super().__init__(**kwargs)


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("research_tasks.id", ondelete="CASCADE"), nullable=False
    )
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    claim = Column(Text, nullable=False)
    evidence_text = Column(Text, nullable=False)
    evidence_type = Column(String(50), nullable=False, default="factual")
    verification_status = Column(String(50), nullable=False, default="supported")
    confidence_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    task = relationship("ResearchTask", back_populates="evidence")
    source = relationship("Source", back_populates="evidence")
    citations = relationship("Citation", back_populates="evidence", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        kwargs.setdefault("verification_status", "supported")
        kwargs.setdefault("confidence_score", 0.0)
        kwargs.setdefault("evidence_type", "factual")
        kwargs.setdefault("created_at", datetime.now(timezone.utc))
        super().__init__(**kwargs)


class Citation(Base):
    __tablename__ = "citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    evidence_id = Column(
        UUID(as_uuid=True), ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False
    )
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    claim = Column(Text, nullable=True)
    citation_number = Column(Integer, nullable=False, default=1)
    quote = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    evidence = relationship("Evidence", back_populates="citations")
    source = relationship("Source", back_populates="citations")

    def __init__(self, **kwargs):
        kwargs.setdefault("citation_number", 1)
        kwargs.setdefault("created_at", datetime.now(timezone.utc))
        super().__init__(**kwargs)


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    executive_summary = Column(Text, nullable=True)
    methodology = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    analysis = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    references = Column(Text, nullable=True)
    format = Column(String(50), nullable=False, default="markdown")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    session = relationship("ResearchSession", back_populates="reports")

    def __init__(self, **kwargs):
        kwargs.setdefault("format", "markdown")
        kwargs.setdefault("created_at", datetime.now(timezone.utc))
        super().__init__(**kwargs)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    agent_name = Column(String(100), nullable=False)
    action = Column(Text, nullable=False)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    status = Column(String(50), nullable=True, default="completed")
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    session = relationship("ResearchSession", back_populates="agent_logs")

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "completed")
        kwargs.setdefault("created_at", datetime.now(timezone.utc))
        super().__init__(**kwargs)
