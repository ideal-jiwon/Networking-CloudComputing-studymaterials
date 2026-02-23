"""Unit tests for CoverageTracker class."""

import pytest
from datetime import datetime

from src.models import Concept, CoverageStats
from src.coverage_tracker import CoverageTracker


def _make_concept(id: str, topic_area: str = "Cloud Computing") -> Concept:
    """Helper to create a Concept with minimal required fields."""
    return Concept(
        id=id,
        name=f"Concept {id}",
        definition=f"Definition for {id}",
        context="Test context",
        source_file="L01.pdf",
        topic_area=topic_area,
        related_concepts=[],
        keywords=[],
        extraction_timestamp=datetime.now().isoformat(),
    )


# ---------------------------------------------------------------------------
# Task 8.1: CoverageTracker core methods
# ---------------------------------------------------------------------------

class TestMarkConceptCovered:
    """Tests for mark_concept_covered()."""

    def test_mark_new_concept(self):
        concepts = [_make_concept("c1")]
        tracker = CoverageTracker(concepts)

        tracker.mark_concept_covered("c1", "q1")

        assert "c1" in tracker.concept_coverage
        assert tracker.concept_coverage["c1"] == ["q1"]

    def test_mark_same_concept_different_questions(self):
        concepts = [_make_concept("c1")]
        tracker = CoverageTracker(concepts)

        tracker.mark_concept_covered("c1", "q1")
        tracker.mark_concept_covered("c1", "q2")

        assert tracker.concept_coverage["c1"] == ["q1", "q2"]

    def test_mark_duplicate_question_ignored(self):
        concepts = [_make_concept("c1")]
        tracker = CoverageTracker(concepts)

        tracker.mark_concept_covered("c1", "q1")
        tracker.mark_concept_covered("c1", "q1")

        assert tracker.concept_coverage["c1"] == ["q1"]

    def test_mark_multiple_concepts(self):
        concepts = [_make_concept("c1"), _make_concept("c2")]
        tracker = CoverageTracker(concepts)

        tracker.mark_concept_covered("c1", "q1")
        tracker.mark_concept_covered("c2", "q2")

        assert set(tracker.concept_coverage.keys()) == {"c1", "c2"}


class TestGetUntestedConcepts:
    """Tests for get_untested_concepts()."""

    def test_all_untested_initially(self):
        concepts = [_make_concept("c1"), _make_concept("c2"), _make_concept("c3")]
        tracker = CoverageTracker(concepts)

        untested = tracker.get_untested_concepts()
        assert len(untested) == 3

    def test_some_tested(self):
        concepts = [_make_concept("c1"), _make_concept("c2"), _make_concept("c3")]
        tracker = CoverageTracker(concepts, {"c1": ["q1"]})

        untested = tracker.get_untested_concepts()
        assert [c.id for c in untested] == ["c2", "c3"]

    def test_all_tested(self):
        concepts = [_make_concept("c1"), _make_concept("c2")]
        tracker = CoverageTracker(concepts, {"c1": ["q1"], "c2": ["q2"]})

        untested = tracker.get_untested_concepts()
        assert untested == []

    def test_empty_concepts(self):
        tracker = CoverageTracker([])
        assert tracker.get_untested_concepts() == []


class TestGetCoverageStats:
    """Tests for get_coverage_stats()."""

    def test_empty_concepts(self):
        tracker = CoverageTracker([])
        stats = tracker.get_coverage_stats()

        assert stats.total_concepts == 0
        assert stats.tested_concepts == 0
        assert stats.coverage_percentage == 0.0
        assert stats.coverage_by_topic == {}
        assert stats.untested_topics == []

    def test_no_coverage(self):
        concepts = [
            _make_concept("c1", "Cloud Computing"),
            _make_concept("c2", "Networking"),
        ]
        tracker = CoverageTracker(concepts)
        stats = tracker.get_coverage_stats()

        assert stats.total_concepts == 2
        assert stats.tested_concepts == 0
        assert stats.coverage_percentage == 0.0
        assert stats.coverage_by_topic["Cloud Computing"] == 0.0
        assert stats.coverage_by_topic["Networking"] == 0.0
        assert set(stats.untested_topics) == {"Cloud Computing", "Networking"}

    def test_partial_coverage(self):
        concepts = [
            _make_concept("c1", "Cloud Computing"),
            _make_concept("c2", "Cloud Computing"),
            _make_concept("c3", "Networking"),
        ]
        tracker = CoverageTracker(concepts, {"c1": ["q1"]})
        stats = tracker.get_coverage_stats()

        assert stats.total_concepts == 3
        assert stats.tested_concepts == 1
        assert abs(stats.coverage_percentage - (1 / 3) * 100) < 0.01
        assert stats.coverage_by_topic["Cloud Computing"] == 50.0
        assert stats.coverage_by_topic["Networking"] == 0.0
        assert "Networking" in stats.untested_topics

    def test_full_coverage(self):
        concepts = [_make_concept("c1"), _make_concept("c2")]
        tracker = CoverageTracker(concepts, {"c1": ["q1"], "c2": ["q2"]})
        stats = tracker.get_coverage_stats()

        assert stats.total_concepts == 2
        assert stats.tested_concepts == 2
        assert stats.coverage_percentage == 100.0
        assert stats.untested_topics == []

    def test_coverage_only_counts_known_concepts(self):
        """Coverage records for unknown concept IDs should not inflate tested count."""
        concepts = [_make_concept("c1")]
        tracker = CoverageTracker(concepts, {"c1": ["q1"], "c_unknown": ["q2"]})
        stats = tracker.get_coverage_stats()

        assert stats.total_concepts == 1
        assert stats.tested_concepts == 1
        assert stats.coverage_percentage == 100.0


# ---------------------------------------------------------------------------
# Task 8.2: select_next_concept
# ---------------------------------------------------------------------------

class TestSelectNextConcept:
    """Tests for select_next_concept()."""

    def test_returns_none_when_no_concepts(self):
        tracker = CoverageTracker([])
        assert tracker.select_next_concept() is None

    def test_returns_untested_first(self):
        concepts = [_make_concept("c1"), _make_concept("c2"), _make_concept("c3")]
        tracker = CoverageTracker(concepts, {"c1": ["q1"]})

        selected = tracker.select_next_concept()
        assert selected is not None
        assert selected.id in {"c2", "c3"}

    def test_all_untested_returns_first(self):
        concepts = [_make_concept("c1"), _make_concept("c2")]
        tracker = CoverageTracker(concepts)

        selected = tracker.select_next_concept()
        assert selected is not None
        assert selected.id == "c1"

    def test_falls_back_to_least_recently_tested(self):
        concepts = [_make_concept("c1"), _make_concept("c2")]
        tracker = CoverageTracker(concepts)

        # Simulate testing order: c1 first, then c2
        tracker.mark_concept_covered("c1", "q1")
        tracker.mark_concept_covered("c2", "q2")

        # All covered — should pick c1 (tested earlier / least recently)
        selected = tracker.select_next_concept()
        assert selected is not None
        assert selected.id == "c1"

    def test_prioritizes_untested_over_least_recent(self):
        concepts = [_make_concept("c1"), _make_concept("c2"), _make_concept("c3")]
        tracker = CoverageTracker(concepts, {"c1": ["q1"], "c2": ["q2"]})

        selected = tracker.select_next_concept()
        assert selected is not None
        assert selected.id == "c3"  # the only untested concept


# ---------------------------------------------------------------------------
# Task 11.2: Topic filtering in CoverageTracker
# ---------------------------------------------------------------------------


class TestGetCoverageStatsByTopic:
    """Tests for get_coverage_stats_by_topic()."""

    def test_stats_for_existing_topic(self):
        concepts = [
            _make_concept("c1", "Cloud Computing"),
            _make_concept("c2", "Cloud Computing"),
            _make_concept("c3", "Networking"),
        ]
        tracker = CoverageTracker(concepts, {"c1": ["q1"]})
        stats = tracker.get_coverage_stats_by_topic("Cloud Computing")

        assert stats.total_concepts == 2
        assert stats.tested_concepts == 1
        assert stats.coverage_percentage == 50.0
        assert stats.coverage_by_topic == {"Cloud Computing": 50.0}

    def test_stats_for_empty_topic(self):
        concepts = [_make_concept("c1", "Cloud Computing")]
        tracker = CoverageTracker(concepts)
        stats = tracker.get_coverage_stats_by_topic("Networking")

        assert stats.total_concepts == 0
        assert stats.tested_concepts == 0
        assert stats.coverage_percentage == 0.0
        assert stats.untested_topics == ["Networking"]

    def test_stats_for_fully_covered_topic(self):
        concepts = [_make_concept("c1", "Cloud Computing")]
        tracker = CoverageTracker(concepts, {"c1": ["q1"]})
        stats = tracker.get_coverage_stats_by_topic("Cloud Computing")

        assert stats.total_concepts == 1
        assert stats.tested_concepts == 1
        assert stats.coverage_percentage == 100.0
        assert stats.untested_topics == []


class TestSelectNextConceptWithTopicFilter:
    """Tests for select_next_concept() with topic_filter."""

    def test_filter_returns_concept_from_topic(self):
        concepts = [
            _make_concept("c1", "Cloud Computing"),
            _make_concept("c2", "Networking"),
            _make_concept("c3", "Networking"),
        ]
        tracker = CoverageTracker(concepts)

        selected = tracker.select_next_concept(topic_filter="Networking")
        assert selected is not None
        assert selected.topic_area == "Networking"

    def test_filter_returns_none_for_unknown_topic(self):
        concepts = [_make_concept("c1", "Cloud Computing")]
        tracker = CoverageTracker(concepts)

        selected = tracker.select_next_concept(topic_filter="Unknown")
        assert selected is None

    def test_filter_prioritizes_untested_in_topic(self):
        concepts = [
            _make_concept("c1", "Networking"),
            _make_concept("c2", "Networking"),
        ]
        tracker = CoverageTracker(concepts, {"c1": ["q1"]})

        selected = tracker.select_next_concept(topic_filter="Networking")
        assert selected is not None
        assert selected.id == "c2"

    def test_filter_falls_back_when_all_covered(self):
        concepts = [
            _make_concept("c1", "Networking"),
            _make_concept("c2", "Networking"),
        ]
        tracker = CoverageTracker(concepts, {"c1": ["q1"], "c2": ["q2"]})

        selected = tracker.select_next_concept(topic_filter="Networking")
        assert selected is not None
        assert selected.topic_area == "Networking"

    def test_no_filter_returns_any_concept(self):
        concepts = [
            _make_concept("c1", "Cloud Computing"),
            _make_concept("c2", "Networking"),
        ]
        tracker = CoverageTracker(concepts)

        selected = tracker.select_next_concept(topic_filter=None)
        assert selected is not None
