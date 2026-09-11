import pytest

from backend.app.evaluation.classification import classify_failure
from backend.app.evaluators import AnswerRelevanceEvaluator, CitationValidator, CorrectnessEvaluator, FaithfulnessEvaluator, HallucinationEvaluator
from backend.app.evaluators.base import EvaluationInput


@pytest.mark.ai
def test_correct_grounded_answer_passes_core_metrics():
    item = EvaluationInput(
        question="How many annual leave days do employees receive?",
        answer="Employees receive 25 annual leave days per year [1].",
        contexts=["Employees receive 25 annual leave days per year."],
        expected_answer="25 annual leave days",
    )
    assert CorrectnessEvaluator().evaluate(item, 0.8).passed
    assert FaithfulnessEvaluator().evaluate(item, 0.85).passed
    assert AnswerRelevanceEvaluator().evaluate(item, 0.8).passed
    assert CitationValidator().evaluate(item, 1).passed


@pytest.mark.ai
def test_unsupported_personal_fact_is_a_hallucination():
    item = EvaluationInput(
        question="What is the CEO's daughter's name?",
        answer="The CEO's daughter is Sarah.",
        contexts=["The company handbook describes leave and travel policies."],
    )
    result = HallucinationEvaluator().evaluate(item, 0.05)
    assert not result.passed
    assert result.score == 1
    assert result.unsupported_claims == ["The CEO's daughter is Sarah."]


@pytest.mark.regression
def test_wrong_answer_with_correct_retrieval_is_generation_failure():
    item = EvaluationInput(
        question="How many annual leave days do employees receive?",
        answer="Employees receive 30 annual leave days per year [1].",
        contexts=["Employees receive 25 annual leave days per year."],
        expected_answer="25 days",
    )
    metrics = {
        "answer_relevance": AnswerRelevanceEvaluator().evaluate(item, 0.8),
        "faithfulness": FaithfulnessEvaluator().evaluate(item, 0.85),
        "answer_correctness": CorrectnessEvaluator().evaluate(item, 0.8),
        "hallucination": HallucinationEvaluator().evaluate(item, 0.05),
        "citation_validation": CitationValidator().evaluate(item, 1),
    }
    assert classify_failure(metrics, 1, 100, 3000, "factual") == "Generation Failure"

