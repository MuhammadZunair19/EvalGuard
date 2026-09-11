import re

from backend.app.evaluators.base import EvaluationInput, EvaluationOutput, Evaluator, output, overlap, tokens


class AnswerRelevanceEvaluator(Evaluator):
    metric = "answer_relevance"

    def evaluate(self, item: EvaluationInput, threshold: float) -> EvaluationOutput:
        score = overlap(item.question, item.answer)
        if item.expected_answer:
            score = max(score, overlap(item.expected_answer, item.answer))
        return output(self.metric, score, threshold, "Measures whether the answer addresses the question.")


class FaithfulnessEvaluator(Evaluator):
    metric = "faithfulness"

    def evaluate(self, item: EvaluationInput, threshold: float) -> EvaluationOutput:
        claims = [claim.strip() for claim in re.split(r"(?<=[.!?])\s+", item.answer) if len(tokens(claim)) > 1]
        context = " ".join(item.contexts)
        unsupported = [claim for claim in claims if overlap(claim, context) < 0.6]
        score = 1.0 if not claims else 1 - len(unsupported) / len(claims)
        return output(self.metric, score, threshold, "Checks answer claims against retrieved context.", unsupported)


class ContextPrecisionEvaluator(Evaluator):
    metric = "context_precision"

    def evaluate(self, item: EvaluationInput, threshold: float) -> EvaluationOutput:
        target = " ".join([item.question, item.expected_answer or "", *item.expected_facts])
        relevant = sum(overlap(target, context) >= 0.2 for context in item.contexts)
        score = relevant / len(item.contexts) if item.contexts else 0.0
        return output(self.metric, score, threshold, "Fraction of retrieved chunks relevant to the test target.")


class ContextRecallEvaluator(Evaluator):
    metric = "context_recall"

    def evaluate(self, item: EvaluationInput, threshold: float) -> EvaluationOutput:
        context = " ".join(item.contexts)
        facts = item.expected_facts or ([item.expected_answer] if item.expected_answer else [])
        if not facts:
            score = 1.0
        else:
            score = sum(overlap(fact, context) >= 0.6 for fact in facts) / len(facts)
        return output(self.metric, score, threshold, "Coverage of expected facts in retrieved context.")


class CorrectnessEvaluator(Evaluator):
    metric = "answer_correctness"

    def evaluate(self, item: EvaluationInput, threshold: float) -> EvaluationOutput:
        score = overlap(item.expected_answer, item.answer) if item.expected_answer else 1.0
        return output(self.metric, score, threshold, "Semantic token coverage against the reference answer.")


class HallucinationEvaluator(Evaluator):
    metric = "hallucination"

    def evaluate(self, item: EvaluationInput, threshold: float) -> EvaluationOutput:
        faithfulness = FaithfulnessEvaluator().evaluate(item, 0)
        score = 1 - faithfulness.score
        bounded = round(max(0.0, min(1.0, score)), 4)
        return EvaluationOutput(self.metric, bounded, bounded <= threshold, threshold, "Share of answer claims unsupported by context.", faithfulness.unsupported_claims)


class CitationValidator(Evaluator):
    metric = "citation_validation"

    def evaluate(self, item: EvaluationInput, threshold: float) -> EvaluationOutput:
        citations = [int(value) for value in re.findall(r"\[(\d+)\]", item.answer)]
        score = 1.0 if citations and all(1 <= value <= len(item.contexts) for value in citations) else 0.0
        return output(self.metric, score, threshold, "Validates that citations refer to returned source chunks.")

