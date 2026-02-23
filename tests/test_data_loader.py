"""Unit tests for DataLoader class."""

import pytest
import json
import tempfile
from pathlib import Path
from src.data_loader import DataLoader
from src.models import Concept, Question


class TestDataLoader:
    """Test suite for DataLoader class."""
    
    def test_load_concepts_from_valid_file(self):
        """Test loading concepts from a valid JSON file."""
        loader = DataLoader(data_dir="data")
        concepts, errors = loader.load_concepts_from_file()
        
        assert len(concepts) > 0, "Should load at least one concept"
        assert len(errors) == 0, "Should have no validation errors"
        
        # Check first concept has required fields
        concept = concepts[0]
        assert concept.id is not None
        assert concept.name is not None
        assert concept.definition is not None
        assert concept.context is not None
        assert concept.source_file is not None
        assert concept.topic_area is not None
        assert isinstance(concept.related_concepts, list)
        assert isinstance(concept.keywords, list)
    
    def test_load_concepts_missing_file(self):
        """Test handling of missing concepts file."""
        loader = DataLoader(data_dir="nonexistent")
        
        with pytest.raises(FileNotFoundError):
            loader.load_concepts_from_file()
    
    def test_load_concepts_invalid_json(self):
        """Test handling of invalid JSON in concepts file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid JSON file
            concepts_file = Path(tmpdir) / "concepts.json"
            with open(concepts_file, 'w') as f:
                f.write("{ invalid json }")
            
            loader = DataLoader(data_dir=tmpdir)
            
            with pytest.raises(ValueError, match="Invalid JSON"):
                loader.load_concepts_from_file()
    
    def test_load_concepts_missing_required_fields(self):
        """Test validation of concepts with missing required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create concepts file with missing fields
            concepts_file = Path(tmpdir) / "concepts.json"
            with open(concepts_file, 'w', encoding='utf-8') as f:
                json.dump([
                    {
                        "id": "test-001",
                        "name": "Test Concept"
                        # Missing: definition, context, source_file, topic_area
                    }
                ], f)
            
            loader = DataLoader(data_dir=tmpdir)
            concepts, errors = loader.load_concepts_from_file()
            
            assert len(concepts) == 0, "Should not load invalid concept"
            assert len(errors) > 0, "Should report validation errors"
            assert "missing required fields" in errors[0].lower()
    
    def test_load_concepts_korean_text_preservation(self):
        """Test that Korean text is preserved correctly."""
        loader = DataLoader(data_dir="data")
        concepts, errors = loader.load_concepts_from_file()
        
        # Find a concept with Korean text
        korean_concepts = [c for c in concepts if '클라우드' in c.name or '컴퓨팅' in c.name]
        assert len(korean_concepts) > 0, "Should have concepts with Korean text"
        
        # Verify Korean text is intact
        concept = korean_concepts[0]
        assert '클라우드' in concept.name or '컴퓨팅' in concept.name
    
    def test_load_questions_from_valid_file(self):
        """Test loading questions from a valid JSON file."""
        loader = DataLoader(data_dir="data")
        questions, errors = loader.load_questions_from_file()
        
        assert len(questions) > 0, "Should load at least one question"
        assert len(errors) == 0, "Should have no validation errors"
        
        # Check first question has required fields
        question = questions[0]
        assert question.id is not None
        assert len(question.concept_ids) > 0, "Should have at least one concept_id"
        assert question.scenario is not None
        assert question.question_text is not None
        assert question.model_answer is not None
        assert question.difficulty is not None
        assert question.topic_area is not None
    
    def test_load_questions_missing_file(self):
        """Test handling of missing questions file."""
        loader = DataLoader(data_dir="nonexistent")
        
        with pytest.raises(FileNotFoundError):
            loader.load_questions_from_file()
    
    def test_load_questions_empty_concept_ids(self):
        """Test validation of questions with empty concept_ids."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create questions file with empty concept_ids
            questions_file = Path(tmpdir) / "questions.json"
            with open(questions_file, 'w', encoding='utf-8') as f:
                json.dump([
                    {
                        "id": "q001",
                        "concept_ids": [],  # Empty list
                        "scenario": "Test scenario",
                        "question_text": "Test question?",
                        "model_answer": "Test answer",
                        "difficulty": "easy",
                        "topic_area": "Test"
                    }
                ], f)
            
            loader = DataLoader(data_dir=tmpdir)
            questions, errors = loader.load_questions_from_file()
            
            assert len(questions) == 0, "Should not load question with empty concept_ids"
            assert len(errors) > 0, "Should report validation error"
            assert "concept_ids" in errors[0].lower()
    
    def test_load_feedback_templates_from_valid_file(self):
        """Test loading feedback templates from a valid JSON file."""
        loader = DataLoader(data_dir="data")
        templates, errors = loader.load_feedback_templates()
        
        assert len(templates) > 0, "Should load feedback templates"
        assert len(errors) == 0, "Should have no validation errors"
        
        # Check expected keys exist
        expected_keys = ['correct', 'partially_correct', 'incorrect']
        for key in expected_keys:
            assert key in templates, f"Should have '{key}' template"
    
    def test_load_feedback_templates_missing_file(self):
        """Test handling of missing feedback templates file."""
        loader = DataLoader(data_dir="nonexistent")
        
        with pytest.raises(FileNotFoundError):
            loader.load_feedback_templates()
    
    def test_validate_data_integrity_valid_references(self):
        """Test data integrity validation with valid concept references."""
        loader = DataLoader(data_dir="data")
        concepts, _ = loader.load_concepts_from_file()
        questions, _ = loader.load_questions_from_file()
        
        warnings = loader.validate_data_integrity(concepts, questions)
        
        # Filter out topic coverage warnings (AWS/GCP sub-topics from classtopics.md
        # are covered under "Overview of Public Cloud Providers")
        ref_warnings = [w for w in warnings if "non-existent" in w or "empty" in w]
        assert len(ref_warnings) == 0, f"Should have no reference warnings, but got: {ref_warnings}"
    
    def test_validate_data_integrity_invalid_concept_reference(self):
        """Test data integrity validation catches invalid concept references."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create concepts file
            concepts_file = Path(tmpdir) / "concepts.json"
            with open(concepts_file, 'w', encoding='utf-8') as f:
                json.dump([
                    {
                        "id": "concept-001",
                        "name": "Test Concept",
                        "definition": "Test definition",
                        "context": "Test context",
                        "source_file": "test.pdf",
                        "topic_area": "Test",
                        "related_concepts": [],
                        "keywords": []
                    }
                ], f)
            
            # Create questions file with invalid concept reference
            questions_file = Path(tmpdir) / "questions.json"
            with open(questions_file, 'w', encoding='utf-8') as f:
                json.dump([
                    {
                        "id": "q001",
                        "concept_ids": ["concept-999"],  # Non-existent concept
                        "scenario": "Test",
                        "question_text": "Test?",
                        "model_answer": "Test",
                        "difficulty": "easy",
                        "topic_area": "Test"
                    }
                ], f)
            
            loader = DataLoader(data_dir=tmpdir)
            concepts, _ = loader.load_concepts_from_file()
            questions, _ = loader.load_questions_from_file()
            
            warnings = loader.validate_data_integrity(concepts, questions)
            
            assert len(warnings) > 0, "Should detect invalid concept reference"
            assert "non-existent concept" in warnings[0].lower()
    
    def test_load_all_data_integration(self):
        """Test loading all data files together."""
        loader = DataLoader(data_dir="data")
        concepts, questions, templates, errors = loader.load_all_data()
        
        assert len(concepts) > 0, "Should load concepts"
        assert len(questions) > 0, "Should load questions"
        assert len(templates) > 0, "Should load templates"
        
        # Filter out topic coverage warnings (AWS/GCP sub-topics from classtopics.md)
        non_topic_errors = [e for e in errors if "classtopics.md" not in e]
        assert len(non_topic_errors) == 0, f"Should have no non-topic errors, but got: {non_topic_errors}"
    
    def test_concepts_have_all_required_fields(self):
        """Test that all loaded concepts have required fields populated."""
        loader = DataLoader(data_dir="data")
        concepts, _ = loader.load_concepts_from_file()
        
        for concept in concepts:
            assert concept.id, f"Concept missing id"
            assert concept.name, f"Concept {concept.id} missing name"
            assert concept.definition, f"Concept {concept.id} missing definition"
            assert concept.context, f"Concept {concept.id} missing context"
            assert concept.source_file, f"Concept {concept.id} missing source_file"
            assert concept.topic_area, f"Concept {concept.id} missing topic_area"
            assert isinstance(concept.related_concepts, list)
            assert isinstance(concept.keywords, list)
    
    def test_questions_have_all_required_fields(self):
        """Test that all loaded questions have required fields populated."""
        loader = DataLoader(data_dir="data")
        questions, _ = loader.load_questions_from_file()
        
        for question in questions:
            assert question.id, f"Question missing id"
            assert len(question.concept_ids) > 0, f"Question {question.id} has empty concept_ids"
            assert question.scenario, f"Question {question.id} missing scenario"
            assert question.question_text, f"Question {question.id} missing question_text"
            assert question.model_answer, f"Question {question.id} missing model_answer"
            assert question.difficulty, f"Question {question.id} missing difficulty"
            assert question.topic_area, f"Question {question.id} missing topic_area"


class TestDataValidation:
    """Tests for enhanced data validation in DataLoader (Task 6.2)."""
    
    def test_validate_detects_empty_concept_fields(self):
        """Test that validation catches concepts with empty required fields."""
        loader = DataLoader(data_dir="data")
        
        concepts = [
            Concept(id="c1", name="", definition="def", context="ctx",
                    source_file="f.pdf", topic_area="Test"),
        ]
        questions = []
        
        warnings = loader.validate_data_integrity(concepts, questions)
        field_warnings = [w for w in warnings if "empty or missing field: name" in w]
        assert len(field_warnings) == 1
    
    def test_validate_detects_empty_question_fields(self):
        """Test that validation catches questions with empty required fields."""
        loader = DataLoader(data_dir="data")
        
        concepts = [
            Concept(id="c1", name="Test", definition="def", context="ctx",
                    source_file="f.pdf", topic_area="Test"),
        ]
        questions = [
            Question(id="q1", concept_ids=["c1"], scenario="",
                     question_text="What?", model_answer="Answer",
                     difficulty="basic", topic_area="Test"),
        ]
        
        warnings = loader.validate_data_integrity(concepts, questions)
        field_warnings = [w for w in warnings if "empty or missing field: scenario" in w]
        assert len(field_warnings) == 1
    
    def test_validate_detects_empty_concept_ids_in_question(self):
        """Test that validation catches questions with empty concept_ids."""
        loader = DataLoader(data_dir="data")
        
        concepts = [
            Concept(id="c1", name="Test", definition="def", context="ctx",
                    source_file="f.pdf", topic_area="Test"),
        ]
        questions = [
            Question(id="q1", concept_ids=[], scenario="Scenario",
                     question_text="What?", model_answer="Answer",
                     difficulty="basic", topic_area="Test"),
        ]
        
        warnings = loader.validate_data_integrity(concepts, questions)
        empty_warnings = [w for w in warnings if "empty concept_ids" in w]
        assert len(empty_warnings) == 1
    
    def test_validate_detects_invalid_concept_reference_in_question(self):
        """Test that validation catches questions referencing non-existent concepts."""
        loader = DataLoader(data_dir="data")
        
        concepts = [
            Concept(id="c1", name="Test", definition="def", context="ctx",
                    source_file="f.pdf", topic_area="Test"),
        ]
        questions = [
            Question(id="q1", concept_ids=["c999"], scenario="Scenario",
                     question_text="What?", model_answer="Answer",
                     difficulty="basic", topic_area="Test"),
        ]
        
        warnings = loader.validate_data_integrity(concepts, questions)
        ref_warnings = [w for w in warnings if "non-existent concept: c999" in w]
        assert len(ref_warnings) == 1
    
    def test_validate_detects_invalid_related_concept(self):
        """Test that validation catches concepts with invalid related_concepts."""
        loader = DataLoader(data_dir="data")
        
        concepts = [
            Concept(id="c1", name="Test", definition="def", context="ctx",
                    source_file="f.pdf", topic_area="Test",
                    related_concepts=["c999"]),
        ]
        questions = []
        
        warnings = loader.validate_data_integrity(concepts, questions)
        ref_warnings = [w for w in warnings if "non-existent related concept: c999" in w]
        assert len(ref_warnings) == 1
    
    def test_validate_valid_related_concepts_no_warnings(self):
        """Test that valid related_concepts produce no warnings."""
        loader = DataLoader(data_dir="data")
        
        concepts = [
            Concept(id="c1", name="Test1", definition="def", context="ctx",
                    source_file="f.pdf", topic_area="Test",
                    related_concepts=["c2"]),
            Concept(id="c2", name="Test2", definition="def", context="ctx",
                    source_file="f.pdf", topic_area="Test",
                    related_concepts=["c1"]),
        ]
        questions = [
            Question(id="q1", concept_ids=["c1", "c2"], scenario="Scenario",
                     question_text="What?", model_answer="Answer",
                     difficulty="basic", topic_area="Test"),
        ]
        
        warnings = loader.validate_data_integrity(concepts, questions)
        # Only topic coverage warnings expected (since "Test" isn't in classtopics.md)
        non_topic_warnings = [w for w in warnings if "classtopics.md" not in w]
        assert len(non_topic_warnings) == 0
    
    def test_validate_topic_coverage_from_classtopics(self):
        """Test that topic coverage validation checks against classtopics.md."""
        loader = DataLoader(data_dir="data")
        concepts, _ = loader.load_concepts_from_file()
        questions, _ = loader.load_questions_from_file()
        
        warnings = loader.validate_data_integrity(concepts, questions)
        
        # AWS and GCP sub-topics should be flagged as missing
        topic_warnings = [w for w in warnings if "classtopics.md" in w]
        assert len(topic_warnings) > 0, "Should detect missing topic coverage"
    
    def test_validate_all_main_topics_covered(self):
        """Test that all main topics from classtopics.md have concepts and questions."""
        loader = DataLoader(data_dir="data")
        concepts, _ = loader.load_concepts_from_file()
        questions, _ = loader.load_questions_from_file()
        
        concept_topics = {c.topic_area for c in concepts}
        question_topics = {q.topic_area for q in questions}
        
        # These main topics should all be covered
        main_topics = [
            "Fundamentals of Cloud Computing",
            "Introduction to DevOps",
            "The Twelve-Factor App",
            "Networking Fundamentals",
            "Infrastructure as Code w/Terraform",
            "Identity & Access Management (IAM)",
            "Virtual Machines",
        ]
        
        for topic in main_topics:
            assert topic in concept_topics, f"Missing concept for topic: {topic}"
            assert topic in question_topics, f"Missing question for topic: {topic}"
    
    def test_load_required_topics(self):
        """Test that _load_required_topics reads classtopics.md correctly."""
        loader = DataLoader(data_dir="data")
        topics = loader._load_required_topics()
        
        assert len(topics) > 0, "Should load topics from classtopics.md"
        assert "Fundamentals of Cloud Computing" in topics
        assert "Networking Fundamentals" in topics
        # Cleaned topics should not contain "Links to an external site."
        for topic in topics:
            assert "Links to an external site." not in topic
    
    def test_load_required_topics_missing_file(self):
        """Test _load_required_topics returns empty list when classtopics.md is not found."""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run from a temp dir where classtopics.md doesn't exist
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                loader = DataLoader(data_dir=tmpdir)
                topics = loader._load_required_topics()
                assert topics == []
            finally:
                os.chdir(original_cwd)
    
    def test_validate_multiple_issues_reported(self):
        """Test that validation reports all issues, not just the first one."""
        loader = DataLoader(data_dir="data")
        
        concepts = [
            Concept(id="c1", name="", definition="", context="ctx",
                    source_file="f.pdf", topic_area="Test",
                    related_concepts=["c999"]),
        ]
        questions = [
            Question(id="q1", concept_ids=["c888"], scenario="",
                     question_text="What?", model_answer="Answer",
                     difficulty="basic", topic_area="Test"),
        ]
        
        warnings = loader.validate_data_integrity(concepts, questions)
        non_topic_warnings = [w for w in warnings if "classtopics.md" not in w]
        
        # Should have: empty name, empty definition, invalid related concept,
        # invalid concept ref in question, empty scenario
        assert len(non_topic_warnings) >= 4, f"Should report multiple issues, got: {non_topic_warnings}"


# --- Task 11.2: get_questions_by_topic ---


class TestGetQuestionsByTopic:
    def test_filters_by_topic(self):
        from src.models import Question
        loader = DataLoader(data_dir="data")
        questions = [
            Question(id="q1", concept_ids=["c1"], scenario="s", question_text="q",
                     model_answer="a", difficulty="basic", topic_area="Cloud Computing"),
            Question(id="q2", concept_ids=["c2"], scenario="s", question_text="q",
                     model_answer="a", difficulty="basic", topic_area="Networking"),
            Question(id="q3", concept_ids=["c3"], scenario="s", question_text="q",
                     model_answer="a", difficulty="basic", topic_area="Cloud Computing"),
        ]
        result = loader.get_questions_by_topic(questions, "Cloud Computing")
        assert len(result) == 2
        assert all(q.topic_area == "Cloud Computing" for q in result)

    def test_returns_empty_for_unknown_topic(self):
        from src.models import Question
        loader = DataLoader(data_dir="data")
        questions = [
            Question(id="q1", concept_ids=["c1"], scenario="s", question_text="q",
                     model_answer="a", difficulty="basic", topic_area="Cloud Computing"),
        ]
        result = loader.get_questions_by_topic(questions, "Unknown")
        assert result == []
