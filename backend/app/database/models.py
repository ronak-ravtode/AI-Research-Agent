import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.database import Base


class ResearchStatus(str, enum.Enum):
    PLANNING = "planning"
    RESEARCHING = "researching"
    EXTRACTING = "extracting"
    VERIFYING = "verifying"
    ANALYZING = "analyzing"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"


class VerificationStatus(str, enum.Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    status = Column(
        Enum(ResearchStatus), nullable=False, default=ResearchStatus.PLANNING.value
    )
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tasks = relationship("ResearchTask", back_populates="session", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="session", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="session", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "status" not in kwargs:
            kwargs["status"] = ResearchStatus.PLANNING.value
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.utcnow()
        if "updated_at" not in kwargs:
            kwargs["updated_at"] = datetime.utcnow()
        super().__init__(**kwargs)


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(ResearchStatus), nullable=False, default=ResearchStatus.PLANNING.value
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    session = relationship("ResearchSession", back_populates="tasks")
    evidence = relationship("Evidence", back_populates="task", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "status" not in kwargs:
            kwargs["status"] = ResearchStatus.PLANNING.value
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.utcnow()
        if "updated_at" not in kwargs:
            kwargs["updated_at"] = datetime.utcnow()
        super().__init__(**kwargs)


class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    relevance_score = Column(Float, nullable=False, default=0.0)
    fetched_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    session = relationship("ResearchSession", back_populates="sources")
    evidence = relationship("Evidence", back_populates="source", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="source", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "relevance_score" not in kwargs:
            kwargs["relevance_score"] = 0.0
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.utcnow()
        super().__init__(**kwargs)


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("research_tasks.id", ondelete="CASCADE"), nullable=False
    )
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    content = Column(Text, nullable=False)
    verification_status = Column(
        Enum(VerificationStatus),
        nullable=False,
        default=VerificationStatus.SUPPORTED.value,
    )
    confidence_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    task = relationship("ResearchTask", back_populates="evidence")
    source = relationship("Source", back_populates="evidence")
    citations = relationship("Citation", back_populates="evidence", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "verification_status" not in kwargs:
            kwargs["verification_status"] = VerificationStatus.SUPPORTED.value
        if "confidence_score" not in kwargs:
            kwargs["confidence_score"] = 0.0
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.utcnow()
        super().__init__(**kwargs)


class Citation(Base):
    __tablename__ = "citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id = Column(
        UUID(as_uuid=True), ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False
    )
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    quote = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    evidence = relationship("Evidence", back_populates="citations")
    source = relationship("Source", back_populates="citations")

    def __init__(self, **kwargs):
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.utcnow()
        super().__init__(**kwargs)


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    format = Column(String(50), nullable=False, default="markdown")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    session = relationship("ResearchSession", back_populates="reports")

    def __init__(self, **kwargs):
        if "format" not in kwargs:
            kwargs["format"] = "markdown"
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.utcnow()
        super().__init__(**kwargs)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False
    )
    agent_name = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    session = relationship("ResearchSession", back_populates="agent_logs")

    def __init__(self, **kwargs):
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.utcnow()
        super().__init__(**kwargs)
