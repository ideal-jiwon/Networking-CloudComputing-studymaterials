"""Topic coverage validation module.

Validates that all required course topics from classtopics.md have
corresponding concepts and questions in the study data.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from .models import Concept, Question

logger = logging.getLogger(__name__)

# Raw lines from classtopics.md that are sub-items of "Overview of Public Cloud Providers"
# and don't exist as standalone topic_area values in the data.
_SUBTOPIC_TO_PARENT = {
    "Amazon Web Services (AWS)": "Overview of Public Cloud Providers",
    "Google Cloud Platform (GCP)": "Overview of Public Cloud Providers",
}


@dataclass
class TopicReport:
    """Per-topic coverage report entry."""
    topic: str
    concept_count: int
    question_count: int
    has_concepts: bool
    has_questions: bool


@dataclass
class TopicCoverageReport:
    """Full topic coverage report."""
    total_required_topics: int
    topics_with_concepts: int
    topics_with_questions: int
    topics_fully_covered: int
    topic_details: List[TopicReport] = field(default_factory=list)
    missing_concepts: List[str] = field(default_factory=list)
    missing_questions: List[str] = field(default_factory=list)


class TopicValidator:
    """Validates that all required course topics have concepts and questions."""

    def __init__(self, topics_file: str = "classtopics.md"):
        self.topics_file = Path(topics_file)
        self.required_topics = self._load_required_topics()

    def _load_required_topics(self) -> List[str]:
        """Load and clean required topics from classtopics.md.

        Sub-items like 'Amazon Web Services (AWSLinks to an external site.)'
        are mapped to their parent topic 'Overview of Public Cloud Providers'
        and deduplicated.
        """
        if not self.topics_file.exists():
            logger.warning("classtopics.md not found at %s", self.topics_file)
            return []

        with open(self.topics_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        seen = set()
        topics: List[str] = []
        for raw in lines:
            # Remove web artifacts like "Links to an external site."
            cleaned = raw.replace("Links to an external site.", "").strip()

            # Clean up parentheses artifacts:
            # e.g. "Amazon Web Services (AWS" -> "Amazon Web Services"
            cleaned = re.sub(r'\s*\([^)]*$', '', cleaned).strip()

            if not cleaned:
                continue

            # Map sub-topics to parent
            mapped = _SUBTOPIC_TO_PARENT.get(cleaned, cleaned)
            if mapped not in seen:
                seen.add(mapped)
                topics.append(mapped)

        logger.info("Loaded %d unique required topics", len(topics))
        return topics

    def validate_concepts(self, concepts: List[Concept]) -> List[str]:
        """Return list of required topics that have NO concepts."""
        concept_topics = {c.topic_area for c in concepts}
        return [t for t in self.required_topics if t not in concept_topics]

    def validate_questions(self, questions: List[Question]) -> List[str]:
        """Return list of required topics that have NO questions."""
        question_topics = {q.topic_area for q in questions}
        return [t for t in self.required_topics if t not in question_topics]

    def generate_report(
        self, concepts: List[Concept], questions: List[Question]
    ) -> TopicCoverageReport:
        """Generate a full topic coverage report.

        Args:
            concepts: All loaded concepts.
            questions: All loaded questions.

        Returns:
            TopicCoverageReport with per-topic details.
        """
        # Count concepts per topic
        concept_counts: Dict[str, int] = {}
        for c in concepts:
            concept_counts[c.topic_area] = concept_counts.get(c.topic_area, 0) + 1

        # Count questions per topic
        question_counts: Dict[str, int] = {}
        for q in questions:
            question_counts[q.topic_area] = question_counts.get(q.topic_area, 0) + 1

        details: List[TopicReport] = []
        missing_concepts: List[str] = []
        missing_questions: List[str] = []
        topics_with_concepts = 0
        topics_with_questions = 0
        topics_fully_covered = 0

        for topic in self.required_topics:
            cc = concept_counts.get(topic, 0)
            qc = question_counts.get(topic, 0)
            has_c = cc > 0
            has_q = qc > 0

            details.append(TopicReport(
                topic=topic,
                concept_count=cc,
                question_count=qc,
                has_concepts=has_c,
                has_questions=has_q,
            ))

            if has_c:
                topics_with_concepts += 1
            else:
                missing_concepts.append(topic)

            if has_q:
                topics_with_questions += 1
            else:
                missing_questions.append(topic)

            if has_c and has_q:
                topics_fully_covered += 1

        return TopicCoverageReport(
            total_required_topics=len(self.required_topics),
            topics_with_concepts=topics_with_concepts,
            topics_with_questions=topics_with_questions,
            topics_fully_covered=topics_fully_covered,
            topic_details=details,
            missing_concepts=missing_concepts,
            missing_questions=missing_questions,
        )
