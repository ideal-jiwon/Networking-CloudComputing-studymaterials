"""Unit tests for ContentStore class."""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.content_store import ContentStore
from src.models import Concept, Question, Progress, CoverageStats


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def content_store(temp_data_dir):
    """Create a ContentStore instance with temporary directory."""
    return ContentStore(data_dir=temp_data_dir)


@pytest.fixture
def sample_concept():
    """Create a sample Concept for testing."""
    return Concept(
        id="concept-1",
        name="클라우드 컴퓨팅",
        definition="인터넷을 통해 컴퓨팅 리소스를 제공하는 서비스",
        context="Cloud computing fundamentals",
        source_file="L01_01.pdf",
        topic_area="Cloud Computing",
        related_concepts=["concept-2"],
        keywords=["cloud", "computing", "클라우드"],
        extraction_timestamp=datetime.now().isoformat()
    )


@pytest.fixture
def sample_question():
    """Create a sample Question for testing."""
    return Question(
        id="question-1",
        concept_ids=["concept-1"],
        scenario="Sarah는 새로운 웹 애플리케이션을 구축하고 있습니다.",
        question_text="클라우드 컴퓨팅의 주요 이점을 설명하세요.",
        model_answer="클라우드 컴퓨팅의 주요 이점은...",
        difficulty="basic",
        topic_area="Cloud Computing",
        generation_timestamp=datetime.now().isoformat()
    )


@pytest.fixture
def sample_progress():
    """Create a sample Progress for testing."""
    coverage_stats = CoverageStats(
        total_concepts=10,
        tested_concepts=5,
        coverage_percentage=50.0,
        coverage_by_topic={"Cloud Computing": 50.0},
        untested_topics=[]
    )
    return Progress(
        session_id="session-1",
        start_time=datetime.now().isoformat(),
        concept_coverage={"concept-1": ["question-1"]},
        answered_questions=["question-1"],
        total_questions_answered=1,
        coverage_stats=coverage_stats
    )


class TestContentStoreInitialization:
    """Tests for ContentStore initialization."""
    
    def test_creates_data_directory(self, temp_data_dir):
        """Test that ContentStore creates data directory structure."""
        store = ContentStore(data_dir=temp_data_dir)
        assert Path(temp_data_dir).exists()
        assert (Path(temp_data_dir) / "extracted_text").exists()
    
    def test_sets_correct_file_paths(self, content_store, temp_data_dir):
        """Test that ContentStore sets correct file paths."""
        assert content_store.concepts_file == Path(temp_data_dir) / "concepts.json"
        assert content_store.questions_file == Path(temp_data_dir) / "questions.json"
        assert content_store.progress_file == Path(temp_data_dir) / "progress.json"



class TestConceptPersistence:
    """Tests for concept save and load operations."""
    
    def test_save_and_load_concepts(self, content_store, sample_concept):
        """Test saving and loading concepts preserves all data."""
        concepts = [sample_concept]
        content_store.save_concepts(concepts)
        
        loaded = content_store.load_concepts()
        assert len(loaded) == 1
        assert loaded[0].id == sample_concept.id
        assert loaded[0].name == sample_concept.name
        assert loaded[0].definition == sample_concept.definition
        assert loaded[0].context == sample_concept.context
        assert loaded[0].source_file == sample_concept.source_file
        assert loaded[0].topic_area == sample_concept.topic_area
        assert loaded[0].related_concepts == sample_concept.related_concepts
        assert loaded[0].keywords == sample_concept.keywords
    
    def test_load_concepts_empty_file(self, content_store):
        """Test loading concepts when file doesn't exist returns empty list."""
        loaded = content_store.load_concepts()
        assert loaded == []
    
    def test_save_concepts_preserves_korean_text(self, content_store, sample_concept):
        """Test that Korean text is preserved through save/load cycle."""
        concepts = [sample_concept]
        content_store.save_concepts(concepts)
        
        loaded = content_store.load_concepts()
        assert loaded[0].name == "클라우드 컴퓨팅"
        assert "클라우드" in loaded[0].keywords
    
    def test_save_concepts_atomic_write(self, content_store, sample_concept):
        """Test that atomic write creates backup file."""
        concepts = [sample_concept]
        content_store.save_concepts(concepts)
        
        # Save again to trigger backup
        sample_concept.name = "Updated"
        content_store.save_concepts([sample_concept])
        
        # Backup file should exist
        backup_file = content_store.concepts_file.with_suffix('.bak')
        assert backup_file.exists()
    
    def test_load_concepts_validates_data(self, content_store, temp_data_dir):
        """Test that loading concepts validates required fields."""
        # Write invalid JSON (missing required field)
        invalid_data = [{"id": "test", "name": "Test"}]
        with open(content_store.concepts_file, 'w') as f:
            json.dump(invalid_data, f)
        
        with pytest.raises(ValueError, match="Missing required field"):
            content_store.load_concepts()


class TestQuestionPersistence:
    """Tests for question save and load operations."""
    
    def test_save_and_load_questions(self, content_store, sample_question):
        """Test saving and loading questions preserves all data."""
        questions = [sample_question]
        content_store.save_questions(questions)
        
        loaded = content_store.load_questions()
        assert len(loaded) == 1
        assert loaded[0].id == sample_question.id
        assert loaded[0].concept_ids == sample_question.concept_ids
        assert loaded[0].scenario == sample_question.scenario
        assert loaded[0].question_text == sample_question.question_text
        assert loaded[0].model_answer == sample_question.model_answer
        assert loaded[0].difficulty == sample_question.difficulty
        assert loaded[0].topic_area == sample_question.topic_area
    
    def test_load_questions_empty_file(self, content_store):
        """Test loading questions when file doesn't exist returns empty list."""
        loaded = content_store.load_questions()
        assert loaded == []
    
    def test_save_questions_preserves_korean_text(self, content_store, sample_question):
        """Test that Korean text in questions is preserved."""
        questions = [sample_question]
        content_store.save_questions(questions)
        
        loaded = content_store.load_questions()
        assert "Sarah는" in loaded[0].scenario
        assert "클라우드 컴퓨팅" in loaded[0].question_text
    
    def test_load_questions_validates_data(self, content_store):
        """Test that loading questions validates required fields."""
        # Write invalid JSON (missing required field)
        invalid_data = [{"id": "test", "scenario": "Test"}]
        with open(content_store.questions_file, 'w') as f:
            json.dump(invalid_data, f)
        
        with pytest.raises(ValueError, match="Missing required field"):
            content_store.load_questions()



class TestProgressPersistence:
    """Tests for progress save and load operations."""
    
    def test_save_and_load_progress(self, content_store, sample_progress):
        """Test saving and loading progress preserves all data."""
        content_store.save_progress(sample_progress)
        
        loaded = content_store.load_progress()
        assert loaded is not None
        assert loaded.session_id == sample_progress.session_id
        assert loaded.start_time == sample_progress.start_time
        assert loaded.concept_coverage == sample_progress.concept_coverage
        assert loaded.answered_questions == sample_progress.answered_questions
        assert loaded.total_questions_answered == sample_progress.total_questions_answered
        
        # Check nested CoverageStats
        assert loaded.coverage_stats.total_concepts == 10
        assert loaded.coverage_stats.tested_concepts == 5
        assert loaded.coverage_stats.coverage_percentage == 50.0
    
    def test_load_progress_empty_file(self, content_store):
        """Test loading progress when file doesn't exist returns None."""
        loaded = content_store.load_progress()
        assert loaded is None
    
    def test_save_progress_atomic_write(self, content_store, sample_progress):
        """Test that atomic write works for progress."""
        content_store.save_progress(sample_progress)
        
        # Save again to trigger backup
        sample_progress.total_questions_answered = 2
        content_store.save_progress(sample_progress)
        
        # Backup file should exist
        backup_file = content_store.progress_file.with_suffix('.bak')
        assert backup_file.exists()
    
    def test_load_progress_validates_data(self, content_store):
        """Test that loading progress validates required fields."""
        # Write invalid JSON (missing required field)
        invalid_data = {"session_id": "test"}
        with open(content_store.progress_file, 'w') as f:
            json.dump(invalid_data, f)
        
        with pytest.raises(ValueError, match="Missing required field"):
            content_store.load_progress()


class TestMultipleObjects:
    """Tests for handling multiple objects."""
    
    def test_save_multiple_concepts(self, content_store):
        """Test saving and loading multiple concepts."""
        concepts = [
            Concept(
                id=f"concept-{i}",
                name=f"Concept {i}",
                definition=f"Definition {i}",
                context="Context",
                source_file="test.pdf",
                topic_area="Test",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            )
            for i in range(5)
        ]
        
        content_store.save_concepts(concepts)
        loaded = content_store.load_concepts()
        
        assert len(loaded) == 5
        assert all(c.id == f"concept-{i}" for i, c in enumerate(loaded))
    
    def test_save_multiple_questions(self, content_store):
        """Test saving and loading multiple questions."""
        questions = [
            Question(
                id=f"question-{i}",
                concept_ids=[f"concept-{i}"],
                scenario=f"Scenario {i}",
                question_text=f"Question {i}",
                model_answer=f"Answer {i}",
                difficulty="basic",
                topic_area="Test",
                generation_timestamp=datetime.now().isoformat()
            )
            for i in range(5)
        ]
        
        content_store.save_questions(questions)
        loaded = content_store.load_questions()
        
        assert len(loaded) == 5
        assert all(q.id == f"question-{i}" for i, q in enumerate(loaded))


class TestQueryMethods:
    """Tests for concept query and filtering methods."""
    
    def test_query_concepts_by_topic(self, content_store):
        """Test querying concepts by topic area."""
        concepts = [
            Concept(
                id="concept-1",
                name="Cloud Computing Concept",
                definition="Definition 1",
                context="Context",
                source_file="L01.pdf",
                topic_area="Cloud Computing",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            ),
            Concept(
                id="concept-2",
                name="Networking Concept",
                definition="Definition 2",
                context="Context",
                source_file="L02.pdf",
                topic_area="Networking",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            ),
            Concept(
                id="concept-3",
                name="Another Cloud Concept",
                definition="Definition 3",
                context="Context",
                source_file="L03.pdf",
                topic_area="Cloud Computing",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            )
        ]
        
        content_store.save_concepts(concepts)
        
        # Query by Cloud Computing topic
        cloud_concepts = content_store.query_concepts_by_topic("Cloud Computing")
        assert len(cloud_concepts) == 2
        assert all(c.topic_area == "Cloud Computing" for c in cloud_concepts)
        assert set(c.id for c in cloud_concepts) == {"concept-1", "concept-3"}
        
        # Query by Networking topic
        network_concepts = content_store.query_concepts_by_topic("Networking")
        assert len(network_concepts) == 1
        assert network_concepts[0].id == "concept-2"
        
        # Query by non-existent topic
        empty_result = content_store.query_concepts_by_topic("Non-existent")
        assert len(empty_result) == 0
    
    def test_query_concepts_by_source(self, content_store):
        """Test querying concepts by source file."""
        concepts = [
            Concept(
                id="concept-1",
                name="Concept from L01",
                definition="Definition 1",
                context="Context",
                source_file="L01_01.pdf",
                topic_area="Cloud Computing",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            ),
            Concept(
                id="concept-2",
                name="Another from L01",
                definition="Definition 2",
                context="Context",
                source_file="L01_01.pdf",
                topic_area="Cloud Computing",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            ),
            Concept(
                id="concept-3",
                name="Concept from L02",
                definition="Definition 3",
                context="Context",
                source_file="L02_01.pdf",
                topic_area="Networking",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            )
        ]
        
        content_store.save_concepts(concepts)
        
        # Query by L01_01.pdf
        l01_concepts = content_store.query_concepts_by_source("L01_01.pdf")
        assert len(l01_concepts) == 2
        assert all(c.source_file == "L01_01.pdf" for c in l01_concepts)
        assert set(c.id for c in l01_concepts) == {"concept-1", "concept-2"}
        
        # Query by L02_01.pdf
        l02_concepts = content_store.query_concepts_by_source("L02_01.pdf")
        assert len(l02_concepts) == 1
        assert l02_concepts[0].id == "concept-3"
        
        # Query by non-existent source
        empty_result = content_store.query_concepts_by_source("L99_99.pdf")
        assert len(empty_result) == 0
    
    def test_query_concepts_by_coverage_status_tested(self, content_store):
        """Test querying tested concepts."""
        concepts = [
            Concept(
                id="concept-1",
                name="Tested Concept 1",
                definition="Definition 1",
                context="Context",
                source_file="L01.pdf",
                topic_area="Cloud Computing",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            ),
            Concept(
                id="concept-2",
                name="Untested Concept",
                definition="Definition 2",
                context="Context",
                source_file="L02.pdf",
                topic_area="Networking",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            ),
            Concept(
                id="concept-3",
                name="Tested Concept 2",
                definition="Definition 3",
                context="Context",
                source_file="L03.pdf",
                topic_area="DevOps",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            )
        ]
        
        content_store.save_concepts(concepts)
        
        # Create progress with some tested concepts
        coverage_stats = CoverageStats(
            total_concepts=3,
            tested_concepts=2,
            coverage_percentage=66.67,
            coverage_by_topic={},
            untested_topics=[]
        )
        progress = Progress(
            session_id="session-1",
            start_time=datetime.now().isoformat(),
            concept_coverage={
                "concept-1": ["question-1"],
                "concept-3": ["question-2"]
            },
            answered_questions=["question-1", "question-2"],
            total_questions_answered=2,
            coverage_stats=coverage_stats
        )
        content_store.save_progress(progress)
        
        # Query tested concepts
        tested_concepts = content_store.query_concepts_by_coverage_status(tested=True)
        assert len(tested_concepts) == 2
        assert set(c.id for c in tested_concepts) == {"concept-1", "concept-3"}
    
    def test_query_concepts_by_coverage_status_untested(self, content_store):
        """Test querying untested concepts."""
        concepts = [
            Concept(
                id="concept-1",
                name="Tested Concept",
                definition="Definition 1",
                context="Context",
                source_file="L01.pdf",
                topic_area="Cloud Computing",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            ),
            Concept(
                id="concept-2",
                name="Untested Concept 1",
                definition="Definition 2",
                context="Context",
                source_file="L02.pdf",
                topic_area="Networking",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            ),
            Concept(
                id="concept-3",
                name="Untested Concept 2",
                definition="Definition 3",
                context="Context",
                source_file="L03.pdf",
                topic_area="DevOps",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            )
        ]
        
        content_store.save_concepts(concepts)
        
        # Create progress with one tested concept
        coverage_stats = CoverageStats(
            total_concepts=3,
            tested_concepts=1,
            coverage_percentage=33.33,
            coverage_by_topic={},
            untested_topics=[]
        )
        progress = Progress(
            session_id="session-1",
            start_time=datetime.now().isoformat(),
            concept_coverage={"concept-1": ["question-1"]},
            answered_questions=["question-1"],
            total_questions_answered=1,
            coverage_stats=coverage_stats
        )
        content_store.save_progress(progress)
        
        # Query untested concepts
        untested_concepts = content_store.query_concepts_by_coverage_status(tested=False)
        assert len(untested_concepts) == 2
        assert set(c.id for c in untested_concepts) == {"concept-2", "concept-3"}
    
    def test_query_concepts_by_coverage_status_no_progress(self, content_store):
        """Test querying concepts when no progress file exists."""
        concepts = [
            Concept(
                id="concept-1",
                name="Concept 1",
                definition="Definition 1",
                context="Context",
                source_file="L01.pdf",
                topic_area="Cloud Computing",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            ),
            Concept(
                id="concept-2",
                name="Concept 2",
                definition="Definition 2",
                context="Context",
                source_file="L02.pdf",
                topic_area="Networking",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            )
        ]
        
        content_store.save_concepts(concepts)
        
        # Query tested concepts (should be empty when no progress)
        tested_concepts = content_store.query_concepts_by_coverage_status(tested=True)
        assert len(tested_concepts) == 0
        
        # Query untested concepts (should return all when no progress)
        untested_concepts = content_store.query_concepts_by_coverage_status(tested=False)
        assert len(untested_concepts) == 2
        assert set(c.id for c in untested_concepts) == {"concept-1", "concept-2"}
    
    def test_query_concepts_by_coverage_status_with_progress_param(self, content_store):
        """Test querying concepts with progress parameter provided."""
        concepts = [
            Concept(
                id="concept-1",
                name="Tested Concept",
                definition="Definition 1",
                context="Context",
                source_file="L01.pdf",
                topic_area="Cloud Computing",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            ),
            Concept(
                id="concept-2",
                name="Untested Concept",
                definition="Definition 2",
                context="Context",
                source_file="L02.pdf",
                topic_area="Networking",
                related_concepts=[],
                keywords=[],
                extraction_timestamp=datetime.now().isoformat()
            )
        ]
        
        content_store.save_concepts(concepts)
        
        # Create progress object (not saved to file)
        coverage_stats = CoverageStats(
            total_concepts=2,
            tested_concepts=1,
            coverage_percentage=50.0,
            coverage_by_topic={},
            untested_topics=[]
        )
        progress = Progress(
            session_id="session-1",
            start_time=datetime.now().isoformat(),
            concept_coverage={"concept-1": ["question-1"]},
            answered_questions=["question-1"],
            total_questions_answered=1,
            coverage_stats=coverage_stats
        )
        
        # Query with progress parameter
        tested_concepts = content_store.query_concepts_by_coverage_status(
            tested=True, 
            progress=progress
        )
        assert len(tested_concepts) == 1
        assert tested_concepts[0].id == "concept-1"
        
        untested_concepts = content_store.query_concepts_by_coverage_status(
            tested=False, 
            progress=progress
        )
        assert len(untested_concepts) == 1
        assert untested_concepts[0].id == "concept-2"
