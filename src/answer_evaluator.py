"""Answer evaluation module for assessing student responses using keyword matching."""

import re
from datetime import datetime
from typing import Dict, List, Optional

from .models import Concept, Feedback, Question


class AnswerEvaluator:
    """Evaluates student answers using keyword matching against model answers."""

    def __init__(self, feedback_templates: Dict, concepts: Optional[List[Concept]] = None):
        """
        Initialize AnswerEvaluator.

        Args:
            feedback_templates: Loaded feedback templates dictionary
            concepts: Optional list of all concepts for related concept lookup
        """
        self.templates = feedback_templates
        self.concepts = concepts or []
        self._concept_map: Dict[str, Concept] = {c.id: c for c in self.concepts}

        # Load scoring thresholds
        self.thresholds = self.templates.get("scoring_thresholds", {
            "correct": {"min_score": 80, "max_score": 100},
            "partially_correct": {"min_score": 40, "max_score": 79},
            "incorrect": {"min_score": 0, "max_score": 39},
        })

        # Load keyword weights
        self.keyword_weights = self.templates.get("keyword_weights", {
            "exact_match": 1.0,
            "partial_match": 0.5,
        })

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text, lowercased and deduplicated."""
        # Tokenize: split on whitespace and punctuation, keep Korean chars
        tokens = re.findall(r"[a-zA-Z0-9가-힣]+", text.lower())
        # Filter out very short English tokens (1-2 chars) but keep Korean
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "and", "or", "but", "in", "on", "at", "to", "for", "of",
            "with", "by", "from", "it", "this", "that", "not", "no",
            "as", "if", "its", "has", "have", "had", "do", "does",
            "did", "will", "would", "can", "could", "should", "may",
        }
        keywords = []
        seen = set()
        for token in tokens:
            if token in seen:
                continue
            if token in stop_words:
                continue
            if len(token) < 2:
                continue
            seen.add(token)
            keywords.append(token)
        return keywords

    def _calculate_score(self, student_keywords: List[str], model_keywords: List[str]) -> float:
        """
        Calculate correctness score based on keyword overlap.

        Score = (weighted matched keywords / total model keywords) * 100
        """
        if not model_keywords:
            return 0.0

        total_weight = 0.0
        model_set = set(model_keywords)

        for model_kw in model_set:
            # Check exact match
            if model_kw in student_keywords:
                total_weight += self.keyword_weights.get("exact_match", 1.0)
                continue
            # Check partial match (model keyword is substring of student keyword or vice versa)
            partial_found = False
            for student_kw in student_keywords:
                if len(model_kw) >= 3 and len(student_kw) >= 3:
                    if model_kw in student_kw or student_kw in model_kw:
                        total_weight += self.keyword_weights.get("partial_match", 0.5)
                        partial_found = True
                        break
            # No match found for this model keyword

        score = (total_weight / len(model_set)) * 100
        return min(score, 100.0)

    def _get_feedback_category(self, score: float) -> str:
        """Determine feedback category based on score thresholds."""
        for category in ["correct", "partially_correct", "incorrect"]:
            threshold = self.thresholds.get(category, {})
            min_score = threshold.get("min_score", 0)
            max_score = threshold.get("max_score", 100)
            if min_score <= score <= max_score:
                return category
        return "incorrect"

    def _find_related_concepts(self, question: Question) -> List[str]:
        """Find related concept names for the question's concepts."""
        related = []
        for concept_id in question.concept_ids:
            concept = self._concept_map.get(concept_id)
            if concept:
                related.append(concept.name)
                for rel_id in concept.related_concepts:
                    rel_concept = self._concept_map.get(rel_id)
                    if rel_concept and rel_concept.name not in related:
                        related.append(rel_concept.name)
        return related

    def _get_definitions(self, question: Question) -> Dict[str, str]:
        """Get definitions for key concepts related to the question."""
        definitions = {}
        for concept_id in question.concept_ids:
            concept = self._concept_map.get(concept_id)
            if concept:
                definitions[concept.name] = concept.definition
        return definitions

    def _identify_gaps(self, student_keywords: List[str], model_keywords: List[str]) -> List[str]:
        """Identify keywords present in model answer but missing from student answer."""
        student_set = set(student_keywords)
        gaps = []
        for kw in model_keywords:
            if kw not in student_set:
                # Check partial match too
                partial = any(
                    (kw in s_kw or s_kw in kw)
                    for s_kw in student_set
                    if len(kw) >= 3 and len(s_kw) >= 3
                )
                if not partial:
                    gaps.append(kw)
        return gaps

    def _identify_strengths(self, student_keywords: List[str], model_keywords: List[str]) -> List[str]:
        """Identify keywords the student correctly included."""
        model_set = set(model_keywords)
        strengths = []
        for kw in student_keywords:
            if kw in model_set:
                strengths.append(kw)
        return strengths

    def _generate_korean_feedback(self, category: str, score: float,
                                   related_concepts: List[str],
                                   definitions: Dict[str, str],
                                   gaps: List[str], strengths: List[str],
                                   model_answer: str,
                                   question: Question) -> str:
        """Generate feedback text in Korean using templates."""
        template = self.templates.get(category, {})
        explanation_templates = self.templates.get("explanation_templates", {})

        parts = []

        # Score
        score_fmt = explanation_templates.get("score_format_korean", "점수: {score}/100")
        parts.append(score_fmt.format(score=round(score)))

        # Main message
        message = template.get("message_korean", "")
        if message:
            parts.append(message)

        # Strengths
        if strengths and template.get("feedback_structure", {}).get("include_strengths", False):
            header = explanation_templates.get("strengths_header_korean", "잘한 점:")
            parts.append(f"\n{header}")
            parts.append(", ".join(strengths[:5]))

        # Gaps
        if gaps and template.get("feedback_structure", {}).get("include_gaps", False):
            header = explanation_templates.get("gaps_header_korean", "보완할 점:")
            parts.append(f"\n{header}")
            parts.append(", ".join(gaps[:5]))

        # Guidance (for partially_correct and incorrect)
        guidance = template.get("guidance_korean", "")
        if guidance:
            parts.append(f"\n{guidance}")

        # Related concepts
        if related_concepts and template.get("feedback_structure", {}).get("include_related_concepts", True):
            header = explanation_templates.get("related_concepts_header_korean", "관련 개념:")
            parts.append(f"\n{header}")
            for concept_name in related_concepts[:5]:
                parts.append(f"- {concept_name}")

        # Definitions
        if definitions and template.get("feedback_structure", {}).get("include_definitions", True):
            for name, defn in list(definitions.items())[:3]:
                def_fmt = explanation_templates.get("definition_format_korean", "{concept_name}: {definition}")
                parts.append(def_fmt.format(concept_name=name, definition=defn))

        # Model answer
        if template.get("feedback_structure", {}).get("include_model_answer", True):
            header = explanation_templates.get("model_answer_header_korean", "모범 답안:")
            parts.append(f"\n{header}")
            parts.append(model_answer)

        # Topic-specific key points
        topic_templates = self.templates.get("feedback_templates_by_topic", {})
        topic_data = topic_templates.get(question.topic_area, {})
        key_points = topic_data.get("key_points_korean", [])
        if key_points:
            parts.append("\n학습 포인트:")
            for point in key_points[:3]:
                parts.append(f"- {point}")

        return "\n".join(parts)

    def evaluate_answer(self, question: Question, student_answer: str,
                        concept: Optional[Concept] = None) -> Feedback:
        """
        Evaluate a student's answer against the model answer.

        Args:
            question: The question being answered
            student_answer: The student's answer text
            concept: Optional primary concept (unused, concepts looked up from question)

        Returns:
            Feedback object with evaluation results
        """
        # Extract keywords
        student_keywords = self._extract_keywords(student_answer)
        model_keywords = self._extract_keywords(question.model_answer)

        # Calculate score
        score = self._calculate_score(student_keywords, model_keywords)

        # Get feedback category
        category = self._get_feedback_category(score)

        # Find related concepts and definitions
        related_concepts = self._find_related_concepts(question)
        definitions = self._get_definitions(question)

        # Identify gaps and strengths
        gaps = self._identify_gaps(student_keywords, model_keywords)
        strengths = self._identify_strengths(student_keywords, model_keywords)

        # Build explanation
        explanation = f"키워드 매칭 기반 평가: 모범 답안의 {len(set(model_keywords))}개 키워드 중 매칭된 키워드를 기반으로 점수를 산출했습니다."

        # Generate Korean feedback
        feedback_korean = self._generate_korean_feedback(
            category, score, related_concepts, definitions,
            gaps, strengths, question.model_answer, question
        )

        return Feedback(
            question_id=question.id,
            student_answer=student_answer,
            correctness_score=round(score, 1),
            related_concepts=related_concepts,
            definitions=definitions,
            explanation=explanation,
            model_answer=question.model_answer,
            gaps_identified=gaps,
            strengths=strengths,
            feedback_text_korean=feedback_korean,
        )
