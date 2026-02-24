"""DataLoader for loading pre-generated concepts, questions, and feedback templates."""

import json
import os
from typing import List, Dict, Tuple
from pathlib import Path
import logging

from .models import Concept, Question

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """Loads and validates pre-generated study data from JSON files."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize DataLoader with data directory path.
        
        Args:
            data_dir: Directory containing JSON data files
        """
        self.data_dir = Path(data_dir)
        self.concepts_file = self.data_dir / "concepts.json"
        self.questions_file = self.data_dir / "questions.json"
        self.feedback_templates_file = self.data_dir / "feedback_templates.json"
    
    def load_concepts_from_file(self) -> Tuple[List[Concept], List[str]]:
        """
        Load concepts from concepts.json file.
        
        Returns:
            Tuple of (list of Concept objects, list of validation errors)
        
        Raises:
            FileNotFoundError: If concepts.json doesn't exist
        """
        if not self.concepts_file.exists():
            logger.error(f"Concepts file not found: {self.concepts_file}")
            raise FileNotFoundError(f"Concepts file not found: {self.concepts_file}")
        
        try:
            with open(self.concepts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            concepts = []
            errors = []
            
            for idx, concept_data in enumerate(data):
                try:
                    # Validate required fields
                    required_fields = ['id', 'name', 'definition', 'context', 
                                     'source_file', 'topic_area']
                    missing_fields = [field for field in required_fields 
                                    if field not in concept_data or not concept_data[field]]
                    
                    if missing_fields:
                        error_msg = f"Concept at index {idx} missing required fields: {missing_fields}"
                        errors.append(error_msg)
                        logger.warning(error_msg)
                        continue
                    
                    # Create Concept object with defaults for optional fields
                    concept = Concept(
                        id=concept_data['id'],
                        name=concept_data['name'],
                        definition=concept_data['definition'],
                        context=concept_data['context'],
                        source_file=concept_data['source_file'],
                        topic_area=concept_data['topic_area'],
                        related_concepts=concept_data.get('related_concepts', []),
                        keywords=concept_data.get('keywords', []),
                        extraction_timestamp=concept_data.get('extraction_timestamp', '')
                    )
                    concepts.append(concept)
                    
                except Exception as e:
                    error_msg = f"Error parsing concept at index {idx}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
            
            logger.info(f"Loaded {len(concepts)} concepts from {self.concepts_file}")
            if errors:
                logger.warning(f"Encountered {len(errors)} validation errors")
            
            return concepts, errors
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in concepts file: {e}")
            raise ValueError(f"Invalid JSON in concepts file: {e}")
        except Exception as e:
            logger.error(f"Error loading concepts: {e}")
            raise
    
    def load_questions_from_file(self) -> Tuple[List[Question], List[str]]:
        """
        Load questions from questions.json file.
        
        Returns:
            Tuple of (list of Question objects, list of validation errors)
        
        Raises:
            FileNotFoundError: If questions.json doesn't exist
        """
        if not self.questions_file.exists():
            logger.error(f"Questions file not found: {self.questions_file}")
            raise FileNotFoundError(f"Questions file not found: {self.questions_file}")
        
        try:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            questions = []
            errors = []
            
            for idx, question_data in enumerate(data):
                try:
                    # Validate required fields
                    required_fields = ['id', 'concept_ids', 'scenario', 'question_text',
                                     'model_answer', 'difficulty', 'topic_area']
                    missing_fields = [field for field in required_fields 
                                    if field not in question_data]
                    
                    if missing_fields:
                        error_msg = f"Question at index {idx} missing required fields: {missing_fields}"
                        errors.append(error_msg)
                        logger.warning(error_msg)
                        continue
                    
                    # Validate concept_ids is non-empty list
                    if not isinstance(question_data['concept_ids'], list) or \
                       len(question_data['concept_ids']) == 0:
                        error_msg = f"Question {question_data.get('id', idx)} has empty or invalid concept_ids"
                        errors.append(error_msg)
                        logger.warning(error_msg)
                        continue
                    
                    # Create Question object
                    question = Question(
                        id=question_data['id'],
                        concept_ids=question_data['concept_ids'],
                        scenario=question_data['scenario'],
                        question_text=question_data['question_text'],
                        model_answer=question_data['model_answer'],
                        difficulty=question_data['difficulty'],
                        topic_area=question_data['topic_area'],
                        generation_timestamp=question_data.get('generation_timestamp', '')
                    )
                    questions.append(question)
                    
                except Exception as e:
                    error_msg = f"Error parsing question at index {idx}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
            
            logger.info(f"Loaded {len(questions)} questions from {self.questions_file}")
            if errors:
                logger.warning(f"Encountered {len(errors)} validation errors")
            
            return questions, errors
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in questions file: {e}")
            raise ValueError(f"Invalid JSON in questions file: {e}")
        except Exception as e:
            logger.error(f"Error loading questions: {e}")
            raise
    
    def load_feedback_templates(self) -> Tuple[Dict, List[str]]:
        """
        Load feedback templates from feedback_templates.json file.
        
        Returns:
            Tuple of (feedback templates dictionary, list of validation errors)
        
        Raises:
            FileNotFoundError: If feedback_templates.json doesn't exist
        """
        if not self.feedback_templates_file.exists():
            logger.error(f"Feedback templates file not found: {self.feedback_templates_file}")
            raise FileNotFoundError(f"Feedback templates file not found: {self.feedback_templates_file}")
        
        try:
            with open(self.feedback_templates_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            
            errors = []
            
            # Validate expected top-level keys
            expected_keys = ['correct', 'partially_correct', 'incorrect', 
                           'common_mistakes', 'feedback_templates_by_topic',
                           'explanation_templates', 'scoring_thresholds', 'keyword_weights']
            
            missing_keys = [key for key in expected_keys if key not in templates]
            if missing_keys:
                error_msg = f"Feedback templates missing expected keys: {missing_keys}"
                errors.append(error_msg)
                logger.warning(error_msg)
            
            # Validate scoring thresholds structure
            if 'scoring_thresholds' in templates:
                for category in ['correct', 'partially_correct', 'incorrect']:
                    if category not in templates['scoring_thresholds']:
                        error_msg = f"Missing scoring threshold for category: {category}"
                        errors.append(error_msg)
                        logger.warning(error_msg)
            
            logger.info(f"Loaded feedback templates from {self.feedback_templates_file}")
            if errors:
                logger.warning(f"Encountered {len(errors)} validation warnings")
            
            return templates, errors
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in feedback templates file: {e}")
            raise ValueError(f"Invalid JSON in feedback templates file: {e}")
        except Exception as e:
            logger.error(f"Error loading feedback templates: {e}")
            raise
    
    def validate_data_integrity(self, concepts: List[Concept], 
                               questions: List[Question]) -> List[str]:
        """
        Validate relationships between concepts and questions.

        Checks:
        - All required fields are present and non-empty in concepts and questions
        - All question concept_ids reference valid concepts
        - All related_concepts reference valid concepts
        - All topics from classtopics.md have at least one concept and one question

        Args:
            concepts: List of loaded concepts
            questions: List of loaded questions

        Returns:
            List of validation warnings
        """
        warnings = []

        # 1. Validate required fields in concepts
        concept_required = ['id', 'name', 'definition', 'context', 'source_file', 'topic_area']
        for concept in concepts:
            for field_name in concept_required:
                value = getattr(concept, field_name, None)
                if not value:
                    warning = f"Concept {concept.id} has empty or missing field: {field_name}"
                    warnings.append(warning)
                    logger.warning(warning)

        # 2. Validate required fields in questions (scenario is optional for concept-only questions)
        question_required = ['id', 'question_text', 'model_answer', 'difficulty', 'topic_area']
        for question in questions:
            for field_name in question_required:
                value = getattr(question, field_name, None)
                if not value:
                    warning = f"Question {question.id} has empty or missing field: {field_name}"
                    warnings.append(warning)
                    logger.warning(warning)
            # concept_ids must be a non-empty list
            if not question.concept_ids:
                warning = f"Question {question.id} has empty concept_ids"
                warnings.append(warning)
                logger.warning(warning)

        # 3. Check that all question concept_ids reference valid concepts
        concept_ids = {concept.id for concept in concepts}

        for question in questions:
            for concept_id in question.concept_ids:
                if concept_id not in concept_ids:
                    warning = f"Question {question.id} references non-existent concept: {concept_id}"
                    warnings.append(warning)
                    logger.warning(warning)

        # 4. Check that all related_concepts reference valid concepts
        for concept in concepts:
            for related_id in concept.related_concepts:
                if related_id not in concept_ids:
                    warning = f"Concept {concept.id} references non-existent related concept: {related_id}"
                    warnings.append(warning)
                    logger.warning(warning)

        # 5. Verify topic coverage against classtopics.md
        required_topics = self._load_required_topics()
        if required_topics:
            concept_topics = {concept.topic_area for concept in concepts}
            question_topics = {question.topic_area for question in questions}

            for topic in required_topics:
                if topic not in concept_topics:
                    warning = f"Topic '{topic}' from classtopics.md has no concepts"
                    warnings.append(warning)
                    logger.warning(warning)
                if topic not in question_topics:
                    warning = f"Topic '{topic}' from classtopics.md has no questions"
                    warnings.append(warning)
                    logger.warning(warning)

        logger.info(f"Data integrity validation complete. Found {len(warnings)} warnings.")
        return warnings
    def _load_required_topics(self) -> List[str]:
        """
        Load required topics from classtopics.md.

        Parses the classtopics.md file and returns a list of topic names.
        Topics that are sub-items (e.g. AWS, GCP links) are mapped to their
        parent topic in the data if they don't exist as standalone topics.

        Returns:
            List of required topic names, or empty list if file not found
        """
        # Look for classtopics.md in project root
        topics_file = Path("classtopics.md")
        if not topics_file.exists():
            # Also check relative to data_dir parent
            topics_file = self.data_dir.parent / "classtopics.md"

        if not topics_file.exists():
            logger.warning("classtopics.md not found, skipping topic coverage validation")
            return []

        try:
            with open(topics_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

            # Clean up topic names (remove web artifacts like "Links to an external site.")
            cleaned_topics = []
            for line in lines:
                # Remove "Links to an external site." artifacts
                topic = line.replace("Links to an external site.", "").strip()
                # Remove trailing parentheses artifacts like "(AWS)" becoming "(AWS"
                # Handle patterns like "Amazon Web Services (AWS)"
                if topic:
                    cleaned_topics.append(topic)

            logger.info(f"Loaded {len(cleaned_topics)} required topics from classtopics.md")
            return cleaned_topics

        except Exception as e:
            logger.warning(f"Error reading classtopics.md: {e}")
            return []

    def get_questions_by_topic(self, questions: List[Question], topic: str) -> List[Question]:
        """Filter questions by topic area.

        Args:
            questions: List of all questions.
            topic: Topic area to filter by.

        Returns:
            List of questions matching the given topic area.
        """
        return [q for q in questions if q.topic_area == topic]

    
    def load_all_data(self) -> Tuple[List[Concept], List[Question], Dict, List[str]]:
        """
        Load all data files and validate integrity.
        
        Returns:
            Tuple of (concepts, questions, feedback_templates, all_errors)
        """
        all_errors = []
        
        # Load concepts
        concepts, concept_errors = self.load_concepts_from_file()
        all_errors.extend(concept_errors)
        
        # Load questions
        questions, question_errors = self.load_questions_from_file()
        all_errors.extend(question_errors)
        
        # Load feedback templates
        feedback_templates, template_errors = self.load_feedback_templates()
        all_errors.extend(template_errors)
        
        # Validate data integrity
        integrity_warnings = self.validate_data_integrity(concepts, questions)
        all_errors.extend(integrity_warnings)
        
        logger.info(f"Data loading complete: {len(concepts)} concepts, "
                   f"{len(questions)} questions, {len(all_errors)} total issues")
        
        return concepts, questions, feedback_templates, all_errors
