"""Unit tests for StudyInterface - tests logic with mocked I/O."""

import pytest
from unittest.mock import MagicMock, patch, call
from io import StringIO

from rich.console import Console

from src.models import Concept, Question, Feedback, CoverageStats, Progress
from src.study_interface import StudyInterface


# --- Fixtures ---

def make_concepts(n=3):
    """Create a list of test concepts."""
    return [
        Concept(
            id=f"c-{i}",
            name=f"개념 {i}",
            definition=f"Definition for concept {i}",
            context=f"Context {i}",
            source_file=f"L0{i}.pdf",
            topic_area="Cloud Computing" if i % 2 == 0 else "Networking",
            related_concepts=[],
            keywords=[f"kw{i}"],
        )
        for i in range(1, n + 1)
    ]


def make_questions(concepts):
    """Create questions linked to concepts."""
    return [
        Question(
            id=f"q-{i}",
            concept_ids=[c.id],
            scenario=f"Scenario for question {i}",
            question_text=f"Question text {i}?",
            model_answer=f"Model answer with keyword kw{i} and details",
            difficulty="medium",
            topic_area=c.topic_area,
        )
        for i, c in enumerate(concepts, 1)
    ]


def make_feedback_templates():
    """Minimal feedback templates for testing."""
    return {
        "correct": {
            "message_korean": "훌륭합니다!",
            "feedback_structure": {
                "include_model_answer": True,
                "include_related_concepts": True,
                "include_definitions": True,
                "include_strengths": True,
                "include_gaps": False,
            },
        },
        "partially_correct": {
            "message_korean": "좋은 시작입니다!",
            "guidance_korean": "더 검토해보세요:",
            "feedback_structure": {
                "include_model_answer": True,
                "include_related_concepts": True,
                "include_definitions": True,
                "include_strengths": True,
                "include_gaps": True,
            },
        },
        "incorrect": {
            "message_korean": "다시 생각해보세요.",
            "guidance_korean": "복습하세요:",
            "feedback_structure": {
                "include_model_answer": True,
                "include_related_concepts": True,
                "include_definitions": True,
                "include_strengths": False,
                "include_gaps": True,
            },
        },
        "scoring_thresholds": {
            "correct": {"min_score": 80, "max_score": 100},
            "partially_correct": {"min_score": 40, "max_score": 79},
            "incorrect": {"min_score": 0, "max_score": 39},
        },
        "keyword_weights": {"exact_match": 1.0, "partial_match": 0.5},
        "explanation_templates": {
            "score_format_korean": "점수: {score}/100",
            "related_concepts_header_korean": "관련 개념:",
            "model_answer_header_korean": "모범 답안:",
            "strengths_header_korean": "잘한 점:",
            "gaps_header_korean": "보완할 점:",
            "definition_format_korean": "{concept_name}: {definition}",
        },
        "common_mistakes": {},
        "feedback_templates_by_topic": {},
    }


def build_interface(concepts=None, questions=None, templates=None, input_responses=None):
    """Build a StudyInterface with mocked dependencies."""
    if concepts is None:
        concepts = make_concepts()
    if questions is None:
        questions = make_questions(concepts)
    if templates is None:
        templates = make_feedback_templates()

    data_loader = MagicMock()
    data_loader.load_all_data.return_value = (concepts, questions, templates, [])

    content_store = MagicMock()
    content_store.load_progress.return_value = None

    console = Console(file=StringIO(), force_terminal=True)

    input_iter = iter(input_responses or [])

    def mock_input(prompt=""):
        try:
            return next(input_iter)
        except StopIteration:
            raise EOFError()

    interface = StudyInterface(
        data_loader=data_loader,
        content_store=content_store,
        console=console,
        input_func=mock_input,
    )
    return interface, console


# --- Task 10.1: Session initialization and question display ---


class TestStartSession:
    def test_start_session_loads_data(self):
        interface, console = build_interface()
        interface.start_session()

        assert interface.concepts is not None
        assert len(interface.concepts) == 3
        assert len(interface.questions) == 3
        assert interface.coverage_tracker is not None
        assert interface.evaluator is not None
        assert interface._session_active is True

    def test_start_session_no_concepts(self):
        interface, console = build_interface(concepts=[], questions=[])
        interface.start_session()

        assert interface._session_active is False

    def test_start_session_restores_progress(self):
        concepts = make_concepts()
        questions = make_questions(concepts)
        templates = make_feedback_templates()

        data_loader = MagicMock()
        data_loader.load_all_data.return_value = (concepts, questions, templates, [])

        content_store = MagicMock()
        progress = Progress(
            session_id="prev",
            start_time="2024-01-01",
            concept_coverage={"c-1": ["q-1"]},
            answered_questions=["q-1"],
            total_questions_answered=1,
            coverage_stats=CoverageStats(
                total_concepts=3, tested_concepts=1,
                coverage_percentage=33.3,
                coverage_by_topic={}, untested_topics=[],
            ),
        )
        content_store.load_progress.return_value = progress

        console = Console(file=StringIO(), force_terminal=True)
        interface = StudyInterface(
            data_loader=data_loader,
            content_store=content_store,
            console=console,
            input_func=lambda p: "",
        )
        interface.start_session()

        # c-1 should already be covered
        assert "c-1" in interface.coverage_tracker.concept_coverage


class TestGetNextQuestion:
    def test_returns_question_for_untested_concept(self):
        interface, _ = build_interface()
        interface.start_session()

        q = interface.get_next_question()
        assert q is not None
        assert isinstance(q, Question)

    def test_returns_none_when_no_questions(self):
        interface, _ = build_interface(concepts=[], questions=[])
        interface.start_session()

        q = interface.get_next_question()
        assert q is None

    def test_returns_none_before_session_start(self):
        interface, _ = build_interface()
        q = interface.get_next_question()
        assert q is None


class TestDisplayQuestion:
    def test_display_question_increments_counter(self):
        interface, console = build_interface()
        interface.start_session()

        q = interface.questions[0]
        interface.display_question(q)
        assert interface.question_number == 1

        interface.display_question(q)
        assert interface.question_number == 2

    def test_display_question_outputs_scenario(self):
        interface, console = build_interface()
        interface.start_session()

        q = interface.questions[0]
        interface.display_question(q)

        output = console.file.getvalue()
        assert "시나리오" in output
        assert "질문" in output


class TestGetAnswerInput:
    def test_multiline_input(self):
        """User types multiple lines, then two empty lines to submit."""
        responses = ["line one", "line two", "", ""]
        interface, _ = build_interface(input_responses=responses)

        answer = interface.get_answer_input()
        assert "line one" in answer
        assert "line two" in answer

    def test_empty_answer(self):
        """Two immediate empty lines produce empty answer."""
        responses = ["", ""]
        interface, _ = build_interface(input_responses=responses)

        answer = interface.get_answer_input()
        assert answer == ""

    def test_eof_terminates_input(self):
        """EOFError stops input collection."""
        interface, _ = build_interface(input_responses=[])
        answer = interface.get_answer_input()
        assert answer == ""


# --- Task 10.2: Answer submission and feedback display ---


class TestSubmitAnswer:
    def test_submit_returns_feedback(self):
        interface, _ = build_interface()
        interface.start_session()

        q = interface.questions[0]
        feedback = interface.submit_answer(q.id, "some answer with kw1")

        assert feedback is not None
        assert isinstance(feedback, Feedback)
        assert feedback.question_id == q.id

    def test_submit_marks_concepts_covered(self):
        interface, _ = build_interface()
        interface.start_session()

        q = interface.questions[0]
        interface.submit_answer(q.id, "answer")

        # The concept should now be covered
        concept_id = q.concept_ids[0]
        assert concept_id in interface.coverage_tracker.concept_coverage

    def test_submit_invalid_question_returns_none(self):
        interface, _ = build_interface()
        interface.start_session()

        feedback = interface.submit_answer("nonexistent-id", "answer")
        assert feedback is None

    def test_submit_before_session_returns_none(self):
        interface, _ = build_interface()
        feedback = interface.submit_answer("q-1", "answer")
        assert feedback is None


class TestDisplayFeedback:
    def test_display_feedback_shows_korean_text(self):
        interface, console = build_interface()
        interface.start_session()

        q = interface.questions[0]
        feedback = interface.submit_answer(q.id, "answer with kw1")
        interface.display_feedback(feedback)

        output = console.file.getvalue()
        assert "피드백" in output
        assert "모범 답안" in output

    def test_display_feedback_shows_related_concepts(self):
        interface, console = build_interface()
        interface.start_session()

        q = interface.questions[0]
        feedback = interface.submit_answer(q.id, "answer")
        interface.display_feedback(feedback)

        output = console.file.getvalue()
        assert "관련 개념" in output


# --- Task 10.3: Progress display ---


class TestShowProgress:
    def test_show_progress_displays_stats(self):
        interface, console = build_interface()
        interface.start_session()

        stats = interface.show_progress()
        assert stats is not None
        assert isinstance(stats, CoverageStats)

        output = console.file.getvalue()
        assert "진행 상황" in output

    def test_show_progress_before_session_returns_none(self):
        interface, _ = build_interface()
        stats = interface.show_progress()
        assert stats is None

    def test_show_progress_shows_topic_table(self):
        interface, console = build_interface()
        interface.start_session()

        interface.show_progress()
        output = console.file.getvalue()
        assert "주제별 진행 상황" in output

    def test_show_progress_after_answering(self):
        interface, console = build_interface()
        interface.start_session()

        q = interface.questions[0]
        interface.submit_answer(q.id, "answer")

        stats = interface.show_progress()
        assert stats.tested_concepts >= 1

    def test_completion_notification(self):
        """When all concepts are covered, show completion message."""
        concepts = make_concepts(2)
        questions = make_questions(concepts)
        interface, console = build_interface(concepts=concepts, questions=questions)
        interface.start_session()

        # Answer all questions
        for q in questions:
            interface.submit_answer(q.id, "answer")

        stats = interface.show_progress()
        output = console.file.getvalue()
        assert "축하합니다" in output


class TestShowUntestedConcepts:
    def test_shows_untested_list(self):
        interface, console = build_interface()
        interface.start_session()

        interface.show_untested_concepts()
        output = console.file.getvalue()
        assert "미학습 개념" in output

    def test_all_tested_shows_message(self):
        concepts = make_concepts(1)
        questions = make_questions(concepts)
        interface, console = build_interface(concepts=concepts, questions=questions)
        interface.start_session()

        interface.submit_answer(questions[0].id, "answer")
        interface.show_untested_concepts()

        output = console.file.getvalue()
        assert "모든 개념이 학습되었습니다" in output


# --- Run loop tests ---


class TestRunLoop:
    def test_quit_command(self):
        """Typing 'q' as answer quits the session."""
        responses = ["q"]
        interface, console = build_interface(input_responses=responses)
        interface.run()

        output = console.file.getvalue()
        assert "종료" in output

    def test_skip_command(self):
        """Typing 's' skips the question, then 'q' quits."""
        responses = ["s", "q"]
        interface, console = build_interface(input_responses=responses)
        interface.run()

        output = console.file.getvalue()
        assert "건너뜁니다" in output

    def test_progress_command(self):
        """Typing 'p' shows progress, then 'q' quits."""
        responses = ["p", "q"]
        interface, console = build_interface(input_responses=responses)
        interface.run()

        output = console.file.getvalue()
        assert "진행 상황" in output

    def test_answer_then_continue(self):
        """Answer a question, see feedback, then quit."""
        # Answer input: "my answer", then empty, empty (submit)
        # Then navigation: "y" to continue, then "q" to quit
        responses = ["my answer", "", "", "q"]
        interface, console = build_interface(input_responses=responses)
        interface.run()

        output = console.file.getvalue()
        assert "피드백" in output

    def test_answer_then_quit_at_navigation(self):
        """Answer a question, then quit at navigation prompt."""
        responses = ["my answer with kw1", "", "", "n"]
        interface, console = build_interface(input_responses=responses)
        interface.run()

        output = console.file.getvalue()
        assert "종료" in output

    def test_save_progress_on_quit(self):
        """Progress is saved when quitting."""
        responses = ["q"]
        interface, console = build_interface(input_responses=responses)
        interface.run()

        interface.content_store.save_progress.assert_called_once()


# --- Task 11.2: Topic filtering ---


class TestSelectTopic:
    def test_select_topic_sets_filter(self):
        """Selecting a valid topic number sets the topic_filter."""
        concepts = make_concepts(3)
        questions = make_questions(concepts)
        # Topics are "Cloud Computing" (even) and "Networking" (odd), sorted
        # Cloud Computing, Networking -> indices 1, 2
        responses = ["1"]  # select first topic alphabetically
        interface, console = build_interface(
            concepts=concepts, questions=questions, input_responses=responses
        )
        interface.start_session()
        interface.select_topic()

        assert interface.topic_filter is not None

    def test_select_topic_zero_clears_filter(self):
        """Selecting 0 clears the topic filter."""
        responses = ["0"]
        interface, console = build_interface(input_responses=responses)
        interface.start_session()
        interface.topic_filter = "Networking"
        interface.select_topic()

        assert interface.topic_filter is None

    def test_select_topic_invalid_input(self):
        """Invalid input doesn't crash."""
        responses = ["abc"]
        interface, console = build_interface(input_responses=responses)
        interface.start_session()
        interface.select_topic()

        output = console.file.getvalue()
        assert "잘못된 입력" in output

    def test_select_topic_out_of_range(self):
        """Out of range number shows error."""
        responses = ["99"]
        interface, console = build_interface(input_responses=responses)
        interface.start_session()
        interface.select_topic()

        output = console.file.getvalue()
        assert "잘못된 번호" in output


class TestGetNextQuestionWithTopicFilter:
    def test_topic_filter_returns_matching_question(self):
        concepts = make_concepts(3)
        questions = make_questions(concepts)
        interface, _ = build_interface(concepts=concepts, questions=questions)
        interface.start_session()
        interface.topic_filter = "Networking"

        q = interface.get_next_question()
        assert q is not None
        assert q.topic_area == "Networking"

    def test_topic_filter_returns_none_for_empty_topic(self):
        concepts = make_concepts(3)
        questions = make_questions(concepts)
        interface, _ = build_interface(concepts=concepts, questions=questions)
        interface.start_session()
        interface.topic_filter = "Nonexistent Topic"

        q = interface.get_next_question()
        assert q is None


class TestRunLoopTopicCommand:
    def test_topic_command_in_run_loop(self):
        """Typing 't' triggers topic selection, then 'q' quits."""
        # 't' -> topic selection, '0' -> clear filter, 'q' -> quit
        responses = ["t", "0", "q"]
        interface, console = build_interface(input_responses=responses)
        interface.run()

        output = console.file.getvalue()
        assert "주제 선택" in output
        assert "필터 해제" in output
