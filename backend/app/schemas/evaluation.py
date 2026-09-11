from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class DatasetResponse(DatasetCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class DatasetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class TestCaseCreate(BaseModel):
    category: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=1)
    expected_answer: str | None = None
    expected_behavior: str | None = None
    expected_facts: list[str] = []
    expected_document: str | None = None
    expected_chunk: str | None = None
    tags: list[str] = []
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    test_type: Literal[
        "factual",
        "missing-context",
        "hallucination",
        "retrieval",
        "adversarial",
        "prompt-injection",
        "edge-case",
        "consistency",
        "latency",
        "regression",
    ]
    repetitions: int = Field(default=1, ge=1, le=10)

    @model_validator(mode="after")
    def validate_expectation(self):
        if self.expected_answer is None and self.expected_behavior is None:
            raise ValueError("expected_answer or expected_behavior is required")
        return self


class TestCaseResponse(TestCaseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    dataset_id: str
    created_at: datetime


class TestCaseUpdate(BaseModel):
    category: str | None = Field(default=None, min_length=1, max_length=80)
    question: str | None = Field(default=None, min_length=1)
    expected_answer: str | None = None
    expected_behavior: str | None = None
    expected_facts: list[str] | None = None
    expected_document: str | None = None
    expected_chunk: str | None = None
    tags: list[str] | None = None
    difficulty: Literal["easy", "medium", "hard"] | None = None
    test_type: (
        Literal[
            "factual",
            "missing-context",
            "hallucination",
            "retrieval",
            "adversarial",
            "prompt-injection",
            "edge-case",
            "consistency",
            "latency",
            "regression",
        ]
        | None
    ) = None
    repetitions: int | None = Field(default=None, ge=1, le=10)


DEFAULT_THRESHOLDS = {
    "faithfulness": 0.85,
    "answer_relevance": 0.80,
    "context_precision": 0.80,
    "context_recall": 0.80,
    "answer_correctness": 0.80,
    "hallucination": 0.05,
    "retrieval_hit_rate": 0.90,
    "p95_latency_ms": 3000.0,
    "citation_validation": 1.0,
    "consistency": 0.80,
}


class EvaluationRunCreate(BaseModel):
    dataset_id: str
    prompt_version_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    model: str = "llama3.1:8b"
    thresholds: dict[str, float] | None = None


class EvaluationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    dataset_id: str
    prompt_version_id: str | None
    model: str
    embedding_model: str
    top_k: int
    thresholds: dict[str, float]
    status: str
    test_count: int
    pass_count: int
    fail_count: int
    pass_percentage: float
    summary: dict[str, Any]
    created_at: datetime
    completed_at: datetime | None


class PromptCreate(BaseModel):
    name: str
    system_prompt: str
    template: str
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_template_variables(self):
        if "{context}" not in self.template or "{question}" not in self.template:
            raise ValueError("template must contain {context} and {question}")
        return self


class PromptResponse(PromptCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class QualityThresholdUpdate(BaseModel):
    value: float = Field(ge=0)
    comparator: Literal[">=", "<="]


class QualityThresholdResponse(QualityThresholdUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    created_at: datetime
