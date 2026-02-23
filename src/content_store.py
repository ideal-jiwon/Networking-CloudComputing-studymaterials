"""Content storage module for persisting concepts, questions, and progress."""

import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import asdict

from .models import Concept, Question, Progress, CoverageStats


class ContentStore:
    """Handles persistence of concepts, questions, and progress data using JSON files."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize ContentStore with data directory.
        
        Args:
            data_dir: Directory path for storing JSON files
        """
        self.data_dir = Path(data_dir)
        self.concepts_file = self.data_dir / "concepts.json"
        self.questions_file = self.data_dir / "questions.json"
        self.progress_file = self.data_dir / "progress.json"
        self.extracted_text_dir = self.data_dir / "extracted_text"
        
        # Create directory structure if it doesn't exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create data directory structure if it doesn't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_text_dir.mkdir(parents=True, exist_ok=True)
    
    def _atomic_write(self, file_path: Path, data: str) -> None:
        """Write data to file atomically to prevent corruption.
        
        Args:
            file_path: Target file path
            data: String data to write
        """
        temp_file = file_path.with_suffix('.tmp')
        backup_file = file_path.with_suffix('.bak')
        
        # Write to temporary file
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(data)
        
        # Backup existing file if it exists
        if file_path.exists():
            shutil.copy(file_path, backup_file)
        
        # Atomic rename
        os.replace(temp_file, file_path)

    def save_concepts(self, concepts: List[Concept]) -> None:
        """Save concepts to concepts.json with atomic write.
        
        Args:
            concepts: List of Concept objects to save
        """
        data = json.dumps(
            [asdict(c) for c in concepts],
            ensure_ascii=False,
            indent=2
        )
        self._atomic_write(self.concepts_file, data)
    
    def load_concepts(self) -> List[Concept]:
        """Load concepts from concepts.json with validation.
        
        Returns:
            List of Concept objects
        
        Raises:
            FileNotFoundError: If concepts.json doesn't exist
            json.JSONDecodeError: If JSON is invalid
            ValueError: If concept data is invalid
        """
        if not self.concepts_file.exists():
            return []
        
        with open(self.concepts_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate and convert to Concept objects
        concepts = []
        for item in data:
            self._validate_concept_data(item)
            concepts.append(Concept(**item))
        
        return concepts
    
    def _validate_concept_data(self, data: Dict) -> None:
        """Validate concept data has all required fields.
        
        Args:
            data: Dictionary containing concept data
        
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = [
            'id', 'name', 'definition', 'context', 
            'source_file', 'topic_area', 'extraction_timestamp'
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

    def save_questions(self, questions: List[Question]) -> None:
        """Save questions to questions.json with atomic write.
        
        Args:
            questions: List of Question objects to save
        """
        data = json.dumps(
            [asdict(q) for q in questions],
            ensure_ascii=False,
            indent=2
        )
        self._atomic_write(self.questions_file, data)
    
    def load_questions(self) -> List[Question]:
        """Load questions from questions.json with validation.
        
        Returns:
            List of Question objects
        
        Raises:
            FileNotFoundError: If questions.json doesn't exist
            json.JSONDecodeError: If JSON is invalid
            ValueError: If question data is invalid
        """
        if not self.questions_file.exists():
            return []
        
        with open(self.questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate and convert to Question objects
        questions = []
        for item in data:
            self._validate_question_data(item)
            questions.append(Question(**item))
        
        return questions
    
    def _validate_question_data(self, data: Dict) -> None:
        """Validate question data has all required fields.
        
        Args:
            data: Dictionary containing question data
        
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = [
            'id', 'concept_ids', 'scenario', 'question_text',
            'model_answer', 'difficulty', 'topic_area', 'generation_timestamp'
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

    def save_progress(self, progress: Progress) -> None:
        """Save progress to progress.json with atomic write.
        
        Args:
            progress: Progress object to save
        """
        # Convert Progress to dict, handling nested CoverageStats
        progress_dict = asdict(progress)
        
        data = json.dumps(
            progress_dict,
            ensure_ascii=False,
            indent=2
        )
        self._atomic_write(self.progress_file, data)
    
    def load_progress(self) -> Optional[Progress]:
        """Load progress from progress.json with validation.
        
        Returns:
            Progress object or None if file doesn't exist
        
        Raises:
            json.JSONDecodeError: If JSON is invalid
            ValueError: If progress data is invalid
        """
        if not self.progress_file.exists():
            return None
        
        with open(self.progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate and convert to Progress object
        self._validate_progress_data(data)
        
        # Convert nested coverage_stats dict to CoverageStats object
        if 'coverage_stats' in data and data['coverage_stats']:
            data['coverage_stats'] = CoverageStats(**data['coverage_stats'])
        
        return Progress(**data)
    
    def _validate_progress_data(self, data: Dict) -> None:
        """Validate progress data has all required fields.
        
        Args:
            data: Dictionary containing progress data
        
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = [
            'session_id', 'start_time', 'concept_coverage',
            'answered_questions', 'total_questions_answered', 'coverage_stats'
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
    
    def query_concepts_by_topic(self, topic_area: str) -> List[Concept]:
        """Query concepts filtered by topic area.
        
        Args:
            topic_area: Topic area to filter by
        
        Returns:
            List of Concept objects matching the topic area
        """
        all_concepts = self.load_concepts()
        return [c for c in all_concepts if c.topic_area == topic_area]
    
    def query_concepts_by_source(self, source_file: str) -> List[Concept]:
        """Query concepts filtered by source file.
        
        Args:
            source_file: Source file name to filter by
        
        Returns:
            List of Concept objects from the specified source file
        """
        all_concepts = self.load_concepts()
        return [c for c in all_concepts if c.source_file == source_file]
    
    def query_concepts_by_coverage_status(
        self, 
        tested: bool, 
        progress: Optional[Progress] = None
    ) -> List[Concept]:
        """Query concepts filtered by coverage status (tested or untested).
        
        Args:
            tested: If True, return tested concepts; if False, return untested concepts
            progress: Progress object containing coverage data. If None, loads from file.
        
        Returns:
            List of Concept objects matching the coverage status
        """
        all_concepts = self.load_concepts()
        
        # Load progress if not provided
        if progress is None:
            progress = self.load_progress()
        
        # If no progress data, all concepts are untested
        if progress is None:
            return [] if tested else all_concepts
        
        # Get set of tested concept IDs
        tested_concept_ids = set(progress.concept_coverage.keys())
        
        # Filter based on tested status
        if tested:
            return [c for c in all_concepts if c.id in tested_concept_ids]
        else:
            return [c for c in all_concepts if c.id not in tested_concept_ids]
