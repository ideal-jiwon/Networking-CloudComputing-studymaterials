"""Unit tests for TopicValidator class."""

import pytest
from datetime import datetime
from pathlib import Path

from src.models import Concept, Question
from src.topic_validator import TopicValidator, TopicCoverageReport, TopicReport


def _make_concept(id: str, topic_area: str) -> Concept:
    return Concept(
        id=id,
        name=f"Concept {id}",
        definition="def",
        context="ctx",
        source_file="L01.pdf",
        topic_area=topic_area,
        related_concepts=[],
        keywords=[],
        extraction_timestamp=datetime.now().isoformat(),
    )


def _make_question(id: str, topic_area: str) -> Question:
    return Question(
        id=id,
        concept_ids=["c1"],
        scenario="scenario",
        question_text="question",
        model_answer="answer",
        difficulty="basic",
        topic_area=topic_area,
        generation_timestamp=datetime.now().isoformat(),
    )


class TestLoadRequiredTopics:
    """Tests for _load_required_topics()."""

    def test_loads_from_classtopics(self, tmp_path):
        topics_file = tmp_path / "classtopics.md"
        topics_file.write_text(
            "Fundamentals of Cloud Computing\nIntroduction to DevOps\n",
            encoding="utf-8",
        )
        validator = TopicValidator(str(topics_file))
        assert validator.required_topics == [
            "Fundamentals of Cloud Computing",
            "Introduction to DevOps",
        ]

    def test_maps_aws_subtopic_to_parent(self, tmp_path):
        topics_file = tmp_path / "classtopics.md"
        topics_file.write_text(
            "Overview of Public Cloud Providers\n"
            "Amazon Web Services (AWSLinks to an external site.)\n"
            "Google Cloud Platform (GCPLinks to an external site.)\n",
            encoding="utf-8",
        )
        validator = TopicValidator(str(topics_file))
        # AWS and GCP should be mapped to parent, deduplicated
        assert validator.required_topics == ["Overview of Public Cloud Providers"]

    def test_missing_file_returns_empty(self, tmp_path):
        validator = TopicValidator(str(tmp_path / "nonexistent.md"))
        assert validator.required_topics == []

    def test_skips_blank_lines(self, tmp_path):
        topics_file = tmp_path / "classtopics.md"
        topics_file.write_text(
            "Topic A\n\n\nTopic B\n", encoding="utf-8"
        )
        validator = TopicValidator(str(topics_file))
        assert validator.required_topics == ["Topic A", "Topic B"]


class TestValidateConcepts:
    """Tests for validate_concepts()."""

    def test_all_topics_covered(self, tmp_path):
        topics_file = tmp_path / "classtopics.md"
        topics_file.write_text("TopicA\nTopicB\n", encoding="utf-8")
        validator = TopicValidator(str(topics_file))

        concepts = [_make_concept("c1", "TopicA"), _make_concept("c2", "TopicB")]
        assert validator.validate_concepts(concepts) == []

    def test_missing_topic(self, tmp_path):
        topics_file = tmp_path / "classtopics.md"
        topics_file.write_text("TopicA\nTopicB\n", encoding="utf-8")
        validator = TopicValidator(str(topics_file))

        concepts = [_make_concept("c1", "TopicA")]
        assert validator.validate_concepts(concepts) == ["TopicB"]


class TestValidateQuestions:
    """Tests for validate_questions()."""

    def test_all_topics_covered(self, tmp_path):
        topics_file = tmp_path / "classtopics.md"
        topics_file.write_text("TopicA\nTopicB\n", encoding="utf-8")
        validator = TopicValidator(str(topics_file))

        questions = [_make_question("q1", "TopicA"), _make_question("q2", "TopicB")]
        assert validator.validate_questions(questions) == []

    def test_missing_topic(self, tmp_path):
        topics_file = tmp_path / "classtopics.md"
        topics_file.write_text("TopicA\nTopicB\n", encoding="utf-8")
        validator = TopicValidator(str(topics_file))

        questions = [_make_question("q1", "TopicA")]
        assert validator.validate_questions(questions) == ["TopicB"]


class TestGenerateReport:
    """Tests for generate_report()."""

    def test_full_coverage_report(self, tmp_path):
        topics_file = tmp_path / "classtopics.md"
        topics_file.write_text("TopicA\nTopicB\n", encoding="utf-8")
        validator = TopicValidator(str(topics_file))

        concepts = [_make_concept("c1", "TopicA"), _make_concept("c2", "TopicB")]
        questions = [_make_question("q1", "TopicA"), _make_question("q2", "TopicB")]

        report = validator.generate_report(concepts, questions)

        assert report.total_required_topics == 2
        assert report.topics_with_concepts == 2
        assert report.topics_with_questions == 2
        assert report.topics_fully_covered == 2
        assert report.missing_concepts == []
        assert report.missing_questions == []

    def test_partial_coverage_report(self, tmp_path):
        topics_file = tmp_path / "classtopics.md"
        topics_file.write_text("TopicA\nTopicB\nTopicC\n", encoding="utf-8")
        validator = TopicValidator(str(topics_file))

        concepts = [_make_concept("c1", "TopicA"), _make_concept("c2", "TopicB")]
        questions = [_make_question("q1", "TopicA")]

        report = validator.generate_report(concepts, questions)

        assert report.total_required_topics == 3
        assert report.topics_with_concepts == 2
        assert report.topics_with_questions == 1
        assert report.topics_fully_covered == 1
        assert "TopicC" in report.missing_concepts
        assert "TopicB" in report.missing_questions
        assert "TopicC" in report.missing_questions

    def test_empty_data(self, tmp_path):
        topics_file = tmp_path / "classtopics.md"
        topics_file.write_text("TopicA\n", encoding="utf-8")
        validator = TopicValidator(str(topics_file))

        report = validator.generate_report([], [])

        assert report.total_required_topics == 1
        assert report.topics_fully_covered == 0
        assert report.missing_concepts == ["TopicA"]
        assert report.missing_questions == ["TopicA"]

    def test_topic_details_counts(self, tmp_path):
        topics_file = tmp_path / "classtopics.md"
        topics_file.write_text("TopicA\n", encoding="utf-8")
        validator = TopicValidator(str(topics_file))

        concepts = [
            _make_concept("c1", "TopicA"),
            _make_concept("c2", "TopicA"),
            _make_concept("c3", "TopicA"),
        ]
        questions = [_make_question("q1", "TopicA"), _make_question("q2", "TopicA")]

        report = validator.generate_report(concepts, questions)

        assert len(report.topic_details) == 1
        detail = report.topic_details[0]
        assert detail.topic == "TopicA"
        assert detail.concept_count == 3
        assert detail.question_count == 2
        assert detail.has_concepts is True
        assert detail.has_questions is True
