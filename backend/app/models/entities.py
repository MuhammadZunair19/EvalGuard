from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, UUIDTimestampMixin


class IndexingStatus(StrEnum):
    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"


class Document(UUIDTimestampMixin, Base):
    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(16))
    storage_path: Mapped[str] = mapped_column(String(512))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    indexing_status: Mapped[str] = mapped_column(String(20), default=IndexingStatus.PENDING)
    chunks: Mapped[list["DocumentChunk"]] = relationship(cascade="all, delete-orphan")


class DocumentChunk(UUIDTimestampMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (UniqueConstraint("document_id", "position"),)

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    vector_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


class EvaluationDataset(UUIDTimestampMixin, Base):
    __tablename__ = "evaluation_datasets"

    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_cases: Mapped[list["TestCase"]] = relationship(cascade="all, delete-orphan")


class TestCase(UUIDTimestampMixin, Base):
    __tablename__ = "test_cases"

    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_datasets.id", ondelete="CASCADE")
    )
    category: Mapped[str] = mapped_column(String(80))
    question: Mapped[str] = mapped_column(Text)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_behavior: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_facts: Mapped[list[str]] = mapped_column(JSON, default=list)
    expected_document: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expected_chunk: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    test_type: Mapped[str] = mapped_column(String(40))
    repetitions: Mapped[int] = mapped_column(Integer, default=1)


class PromptVersion(UUIDTimestampMixin, Base):
    __tablename__ = "prompt_versions"
    __table_args__ = (UniqueConstraint("name", "version"),)

    name: Mapped[str] = mapped_column(String(120))
    system_prompt: Mapped[str] = mapped_column(Text)
    template: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)


class EvaluationRun(UUIDTimestampMixin, Base):
    __tablename__ = "evaluation_runs"

    dataset_id: Mapped[str] = mapped_column(ForeignKey("evaluation_datasets.id"))
    prompt_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("prompt_versions.id"), nullable=True
    )
    model: Mapped[str] = mapped_column(String(120))
    embedding_model: Mapped[str] = mapped_column(String(120))
    top_k: Mapped[int] = mapped_column(Integer)
    chunk_configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    thresholds: Mapped[dict[str, float]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default=RunStatus.PENDING)
    test_count: Mapped[int] = mapped_column(Integer, default=0)
    pass_count: Mapped[int] = mapped_column(Integer, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    pass_percentage: Mapped[float] = mapped_column(Float, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    results: Mapped[list["TestResult"]] = relationship(cascade="all, delete-orphan")


class TestResult(UUIDTimestampMixin, Base):
    __tablename__ = "test_results"

    run_id: Mapped[str] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"))
    test_case_id: Mapped[str] = mapped_column(ForeignKey("test_cases.id"))
    passed: Mapped[bool] = mapped_column(Boolean)
    actual_answer: Mapped[str] = mapped_column(Text)
    retrieved_context: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    failure_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float)
    unsupported_claims: Mapped[list[str]] = mapped_column(JSON, default=list)
    metrics: Mapped[list["MetricResult"]] = relationship(cascade="all, delete-orphan")


class MetricResult(UUIDTimestampMixin, Base):
    __tablename__ = "metric_results"

    test_result_id: Mapped[str] = mapped_column(ForeignKey("test_results.id", ondelete="CASCADE"))
    metric: Mapped[str] = mapped_column(String(80))
    score: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)
    threshold: Mapped[float] = mapped_column(Float)
    details: Mapped[str] = mapped_column(Text)


class QualityThreshold(UUIDTimestampMixin, Base):
    __tablename__ = "quality_thresholds"

    name: Mapped[str] = mapped_column(String(80), unique=True)
    value: Mapped[float] = mapped_column(Float)
    comparator: Mapped[str] = mapped_column(String(8), default=">=")
