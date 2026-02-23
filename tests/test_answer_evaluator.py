"""Unit tests for the AnswerEvaluator module."""

import json
import pytest
from src.models import Concept, Feedback, Question
from src.answer_evaluator import AnswerEvaluator


@pytest.fixture
def feedback_templates():
    """Load actual feedback templates from data file."""
    with open("data/feedback_templates.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_concepts():
    """Create sample concepts for testing."""
    return [
        Concept(
            id="c-network-003",
            name="TCP vs UDP",
            definition="TCP: 연결 지향적, 신뢰성 있는 전송. UDP: 비연결형, 빠르지만 전송 보장 없음",
            context="Transport layer protocols",
            source_file="L05_01.pdf",
            topic_area="Networking Fundamentals",
            related_concepts=["c-network-001"],
            keywords=["TCP", "UDP", "reliable", "connectionless"],
        ),
        Concept(
            id="c-network-001",
            name="네트워킹 기초",
            definition="네트워크는 통신 링크로 연결된 시스템들의 모음",
            context="Networking basics",
            source_file="L05_01.pdf",
            topic_area="Networking Fundamentals",
            related_concepts=[],
            keywords=["LAN", "WAN", "network"],
        ),
    ]


@pytest.fixture
def sample_question():
    """Create a sample question for testing."""
    return Question(
        id="q001",
        concept_ids=["c-network-003"],
        scenario="Sarah is building two applications.",
        question_text="Explain the key differences between TCP and UDP.",
        model_answer="TCP is connection-oriented, provides reliable ordered delivery with error checking and retransmission. UDP is connectionless, faster but no delivery guarantees. Banking portal should use TCP. Sports ticker should use UDP.",
        difficulty="medium",
        topic_area="Networking Fundamentals",
    )


@pytest.fixture
def evaluator(feedback_templates, sample_concepts):
    """Create an AnswerEvaluator instance."""
    return AnswerEvaluator(feedback_templates, sample_concepts)


class TestKeywordExtraction:
    def test_extracts_english_keywords(self, evaluator):
        keywords = evaluator._extract_keywords("TCP is connection-oriented protocol")
        assert "tcp" in keywords
        assert "connection" in keywords
        assert "protocol" in keywords

    def test_extracts_korean_keywords(self, evaluator):
        keywords = evaluator._extract_keywords("클라우드 컴퓨팅은 인터넷을 통해 제공됩니다")
        assert "클라우드" in keywords
        assert "컴퓨팅은" in keywords

    def test_filters_stop_words(self, evaluator):
        keywords = evaluator._extract_keywords("the protocol is for the network")
        assert "the" not in keywords
        assert "is" not in keywords
        assert "for" not in keywords

    def test_deduplicates_keywords(self, evaluator):
        keywords = evaluator._extract_keywords("TCP TCP TCP protocol")
        assert keywords.count("tcp") == 1

    def test_empty_text(self, evaluator):
        keywords = evaluator._extract_keywords("")
        assert keywords == []


class TestScoreCalculation:
    def test_perfect_match(self, evaluator):
        model_kw = ["tcp", "udp", "reliable", "connectionless"]
        student_kw = ["tcp", "udp", "reliable", "connectionless"]
        score = evaluator._calculate_score(student_kw, model_kw)
        assert score == 100.0

    def test_no_match(self, evaluator):
        model_kw = ["tcp", "udp", "reliable"]
        student_kw = ["pizza", "burger", "fries"]
        score = evaluator._calculate_score(student_kw, model_kw)
        assert score == 0.0

    def test_partial_keyword_overlap(self, evaluator):
        model_kw = ["tcp", "udp", "reliable", "connectionless"]
        student_kw = ["tcp", "udp"]
        score = evaluator._calculate_score(student_kw, model_kw)
        assert 40 <= score <= 60

    def test_empty_model_keywords(self, evaluator):
        score = evaluator._calculate_score(["tcp"], [])
        assert score == 0.0

    def test_partial_string_match(self, evaluator):
        """Partial match: 'connection' partially matches 'connectionless'."""
        model_kw = ["connectionless"]
        student_kw = ["connection"]
        score = evaluator._calculate_score(student_kw, model_kw)
        assert score > 0  # partial match should give some credit


class TestFeedbackCategory:
    def test_correct_category(self, evaluator):
        assert evaluator._get_feedback_category(90) == "correct"
        assert evaluator._get_feedback_category(80) == "correct"
        assert evaluator._get_feedback_category(100) == "correct"

    def test_partially_correct_category(self, evaluator):
        assert evaluator._get_feedback_category(50) == "partially_correct"
        assert evaluator._get_feedback_category(40) == "partially_correct"
        assert evaluator._get_feedback_category(79) == "partially_correct"

    def test_incorrect_category(self, evaluator):
        assert evaluator._get_feedback_category(0) == "incorrect"
        assert evaluator._get_feedback_category(20) == "incorrect"
        assert evaluator._get_feedback_category(39) == "incorrect"


class TestEvaluateAnswer:
    def test_returns_feedback_object(self, evaluator, sample_question):
        feedback = evaluator.evaluate_answer(sample_question, "TCP is reliable")
        assert isinstance(feedback, Feedback)

    def test_feedback_has_all_fields(self, evaluator, sample_question):
        feedback = evaluator.evaluate_answer(sample_question, "TCP provides reliable delivery")
        assert feedback.question_id == "q001"
        assert feedback.student_answer == "TCP provides reliable delivery"
        assert isinstance(feedback.correctness_score, float)
        assert isinstance(feedback.related_concepts, list)
        assert isinstance(feedback.definitions, dict)
        assert isinstance(feedback.explanation, str)
        assert feedback.model_answer == sample_question.model_answer
        assert isinstance(feedback.gaps_identified, list)
        assert isinstance(feedback.strengths, list)
        assert isinstance(feedback.feedback_text_korean, str)
        assert feedback.timestamp  # auto-generated

    def test_good_answer_scores_high(self, evaluator, sample_question):
        good_answer = (
            "TCP is connection-oriented and provides reliable ordered delivery "
            "with error checking and retransmission. UDP is connectionless and faster "
            "but has no delivery guarantees. Banking portal should use TCP for reliability. "
            "Sports ticker should use UDP for speed."
        )
        feedback = evaluator.evaluate_answer(sample_question, good_answer)
        assert feedback.correctness_score >= 60

    def test_empty_answer_scores_zero(self, evaluator, sample_question):
        feedback = evaluator.evaluate_answer(sample_question, "")
        assert feedback.correctness_score == 0.0

    def test_irrelevant_answer_scores_low(self, evaluator, sample_question):
        feedback = evaluator.evaluate_answer(sample_question, "I like pizza and burgers")
        assert feedback.correctness_score < 40

    def test_includes_related_concepts(self, evaluator, sample_question):
        feedback = evaluator.evaluate_answer(sample_question, "TCP is reliable")
        assert len(feedback.related_concepts) > 0
        assert "TCP vs UDP" in feedback.related_concepts

    def test_includes_definitions(self, evaluator, sample_question):
        feedback = evaluator.evaluate_answer(sample_question, "TCP is reliable")
        assert "TCP vs UDP" in feedback.definitions

    def test_includes_model_answer(self, evaluator, sample_question):
        feedback = evaluator.evaluate_answer(sample_question, "TCP is reliable")
        assert feedback.model_answer == sample_question.model_answer


class TestKoreanFeedback:
    def test_feedback_contains_korean(self, evaluator, sample_question):
        feedback = evaluator.evaluate_answer(sample_question, "TCP is reliable")
        assert "점수:" in feedback.feedback_text_korean

    def test_correct_answer_korean_message(self, evaluator, sample_question):
        good_answer = (
            "TCP is connection-oriented and provides reliable ordered delivery "
            "with error checking and retransmission. UDP is connectionless and faster "
            "but has no delivery guarantees. Banking portal should use TCP. "
            "Sports ticker should use UDP for speed and lower overhead."
        )
        feedback = evaluator.evaluate_answer(sample_question, good_answer)
        if feedback.correctness_score >= 80:
            assert "훌륭합니다" in feedback.feedback_text_korean

    def test_incorrect_answer_korean_message(self, evaluator, sample_question):
        feedback = evaluator.evaluate_answer(sample_question, "I have no idea")
        assert "다시 한번" in feedback.feedback_text_korean or "복습" in feedback.feedback_text_korean

    def test_model_answer_in_korean_feedback(self, evaluator, sample_question):
        feedback = evaluator.evaluate_answer(sample_question, "some answer")
        assert "모범 답안:" in feedback.feedback_text_korean

    def test_korean_student_answer(self, evaluator, sample_question):
        """Test that Korean student answers are processed correctly."""
        korean_answer = "TCP는 연결 지향적이고 신뢰성 있는 전송을 제공합니다"
        feedback = evaluator.evaluate_answer(sample_question, korean_answer)
        assert isinstance(feedback, Feedback)
        assert feedback.student_answer == korean_answer


class TestEdgeCases:
    def test_no_concepts_provided(self, feedback_templates, sample_question):
        evaluator = AnswerEvaluator(feedback_templates, concepts=[])
        feedback = evaluator.evaluate_answer(sample_question, "TCP is reliable")
        assert isinstance(feedback, Feedback)
        assert feedback.related_concepts == []
        assert feedback.definitions == {}

    def test_question_with_unknown_concept_id(self, feedback_templates):
        evaluator = AnswerEvaluator(feedback_templates, concepts=[])
        question = Question(
            id="q999",
            concept_ids=["nonexistent-concept"],
            scenario="Test",
            question_text="Test question",
            model_answer="Test answer with keywords",
            difficulty="easy",
            topic_area="Unknown Topic",
        )
        feedback = evaluator.evaluate_answer(question, "Test answer")
        assert isinstance(feedback, Feedback)
