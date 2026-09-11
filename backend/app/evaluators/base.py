import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvaluationInput:
    question: str
    answer: str
    contexts: list[str]
    expected_answer: str | None = None
    expected_facts: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvaluationOutput:
    metric: str
    score: float
    passed: bool
    threshold: float
    details: str
    unsupported_claims: list[str] = field(default_factory=list)


class Evaluator:
    metric: str

    def evaluate(self, item: EvaluationInput, threshold: float) -> EvaluationOutput:
        raise NotImplementedError


def tokens(text: str) -> set[str]:
    stop = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in stop}


def overlap(left: str, right: str) -> float:
    left_tokens, right_tokens = tokens(left), tokens(right)
    if not left_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens)


def output(
    metric: str, score: float, threshold: float, details: str, unsupported: list[str] | None = None
) -> EvaluationOutput:
    bounded = round(max(0.0, min(1.0, score)), 4)
    return EvaluationOutput(
        metric, bounded, bounded >= threshold, threshold, details, unsupported or []
    )
