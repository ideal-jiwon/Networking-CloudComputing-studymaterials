"""Coverage tracking module for monitoring concept testing progress."""

from typing import List, Dict, Optional
from datetime import datetime

from .models import Concept, CoverageStats


class CoverageTracker:
    """Tracks which concepts have been tested and provides coverage statistics."""

    def __init__(self, concepts: List[Concept], concept_coverage: Optional[Dict[str, List[str]]] = None):
        """Initialize CoverageTracker.

        Args:
            concepts: Complete list of all concepts to track against.
            concept_coverage: Existing coverage mapping of concept_id -> [question_ids].
                              Defaults to empty dict if not provided.
        """
        self.concepts = concepts
        self.concept_coverage: Dict[str, List[str]] = dict(concept_coverage) if concept_coverage else {}

    def mark_concept_covered(self, concept_id: str, question_id: str) -> None:
        """Mark a concept as tested by recording the question that covered it.

        Args:
            concept_id: ID of the concept that was tested.
            question_id: ID of the question used to test the concept.
        """
        if concept_id not in self.concept_coverage:
            self.concept_coverage[concept_id] = []
        if question_id not in self.concept_coverage[concept_id]:
            self.concept_coverage[concept_id].append(question_id)

    def get_untested_concepts(self) -> List[Concept]:
        """Get list of concepts that have not yet been tested.

        Returns:
            List of Concept objects whose IDs are not in the coverage records.
        """
        tested_ids = set(self.concept_coverage.keys())
        return [c for c in self.concepts if c.id not in tested_ids]

    def get_coverage_stats(self) -> CoverageStats:
        """Calculate coverage statistics overall and by topic.

        Returns:
            CoverageStats with overall and topic-level coverage percentages.
        """
        total = len(self.concepts)
        if total == 0:
            return CoverageStats(
                total_concepts=0,
                tested_concepts=0,
                coverage_percentage=0.0,
                coverage_by_topic={},
                untested_topics=[],
            )

        tested_ids = set(self.concept_coverage.keys())
        tested_count = sum(1 for c in self.concepts if c.id in tested_ids)

        coverage_percentage = (tested_count / total) * 100

        # Group concepts by topic
        topics: Dict[str, List[Concept]] = {}
        for concept in self.concepts:
            topics.setdefault(concept.topic_area, []).append(concept)

        coverage_by_topic: Dict[str, float] = {}
        untested_topics: List[str] = []

        for topic, topic_concepts in topics.items():
            topic_tested = sum(1 for c in topic_concepts if c.id in tested_ids)
            topic_total = len(topic_concepts)
            topic_pct = (topic_tested / topic_total) * 100
            coverage_by_topic[topic] = topic_pct
            if topic_tested == 0:
                untested_topics.append(topic)

        return CoverageStats(
            total_concepts=total,
            tested_concepts=tested_count,
            coverage_percentage=coverage_percentage,
            coverage_by_topic=coverage_by_topic,
            untested_topics=sorted(untested_topics),
        )

    def get_coverage_stats_by_topic(self, topic: str) -> CoverageStats:
        """Calculate coverage statistics for a single topic.

        Args:
            topic: Topic area to calculate stats for.

        Returns:
            CoverageStats scoped to the given topic.
        """
        topic_concepts = [c for c in self.concepts if c.topic_area == topic]
        total = len(topic_concepts)
        if total == 0:
            return CoverageStats(
                total_concepts=0,
                tested_concepts=0,
                coverage_percentage=0.0,
                coverage_by_topic={},
                untested_topics=[topic],
            )

        tested_ids = set(self.concept_coverage.keys())
        tested_count = sum(1 for c in topic_concepts if c.id in tested_ids)
        pct = (tested_count / total) * 100

        untested = [topic] if tested_count == 0 else []
        return CoverageStats(
            total_concepts=total,
            tested_concepts=tested_count,
            coverage_percentage=pct,
            coverage_by_topic={topic: pct},
            untested_topics=untested,
        )


    def select_next_concept(self, strategy: str = "untested_first",
                           topic_filter: Optional[str] = None) -> Optional[Concept]:
        """Select the next concept to test based on the given strategy.

        Strategies:
            - "untested_first": Prioritize concepts that haven't been tested yet.
              Falls back to least-recently-tested when all concepts are covered.

        Args:
            strategy: Selection strategy name. Defaults to "untested_first".
            topic_filter: If provided, only consider concepts in this topic area.

        Returns:
            The next Concept to test, or None if there are no concepts.
        """
        pool = self.concepts
        if topic_filter:
            pool = [c for c in self.concepts if c.topic_area == topic_filter]

        if not pool:
            return None

        if strategy == "untested_first":
            tested_ids = set(self.concept_coverage.keys())
            untested = [c for c in pool if c.id not in tested_ids]
            if untested:
                return untested[0]

            # All covered — fall back to least-recently-tested within pool
            return self._least_recently_tested(pool)

        # Default fallback for unknown strategies
        return pool[0]


    def _least_recently_tested(self, pool: Optional[List[Concept]] = None) -> Optional[Concept]:
        """Select the concept that was tested least recently.

        Uses the order of question_ids in the coverage record as a proxy
        for recency — the last question_id added is the most recent test.
        Concepts with fewer total tests are preferred; ties broken by
        earliest last-test position.

        Args:
            pool: Subset of concepts to consider. Defaults to all concepts.

        Returns:
            The least-recently-tested Concept, or None if no concepts exist.
        """
        candidates = pool if pool is not None else self.concepts
        if not candidates:
            return None

        # Build a global ordering of question_ids by first-seen position
        seen_questions: Dict[str, int] = {}
        counter = 0
        for concept in self.concepts:
            for qid in self.concept_coverage.get(concept.id, []):
                if qid not in seen_questions:
                    seen_questions[qid] = counter
                    counter += 1

        def recency_key(concept: Concept) -> int:
            """Return the position of the most recent question for this concept.
            Lower means tested earlier (less recently), so it should be picked first.
            """
            qids = self.concept_coverage.get(concept.id, [])
            if not qids:
                return -1  # untested — highest priority
            return max(seen_questions.get(qid, 0) for qid in qids)

        return min(candidates, key=recency_key)

