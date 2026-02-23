"""Data models for the Midterm Study System."""

from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime


@dataclass
class Concept:
    """Represents a key concept extracted from lecture materials."""
    id: str
    name: str
    definition: str
    context: str
    source_file: str
    topic_area: str
    related_concepts: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    extraction_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Question:
    """Represents a scenario-based practice question."""
    id: str
    concept_ids: List[str]
    scenario: str
    question_text: str
    model_answer: str
    difficulty: str
    topic_area: str
    generation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Feedback:
    """Represents feedback on a student's answer."""
    question_id: str
    student_answer: str
    correctness_score: float
    related_concepts: List[str]
    definitions: Dict[str, str]
    explanation: str
    model_answer: str
    gaps_identified: List[str]
    strengths: List[str]
    feedback_text_korean: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CoverageStats:
    """Statistics about concept coverage."""
    total_concepts: int
    tested_concepts: int
    coverage_percentage: float
    coverage_by_topic: Dict[str, float]
    untested_topics: List[str]


@dataclass
class Progress:
    """Tracks user progress through study sessions."""
    session_id: str
    start_time: str
    concept_coverage: Dict[str, List[str]]  # concept_id -> [question_ids]
    answered_questions: List[str]
    total_questions_answered: int
    coverage_stats: CoverageStats
