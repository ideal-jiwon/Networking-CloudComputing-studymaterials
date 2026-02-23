# Design Document: Midterm Study System

## Overview

The Midterm Study System is a Python-based application that helps students prepare for exams by extracting concepts from PDF lecture materials, generating scenario-based practice questions using AI, and providing an interactive study environment with comprehensive feedback. The system consists of five main components: PDF processing, concept extraction, question generation, interactive study interface, and progress tracking.

The system follows a pipeline architecture where PDF content flows through extraction, concept identification, question generation, and finally to the interactive study interface. All data is persisted in a JSON-based storage system for session continuity.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Study Interface                          │
│                    (Web UI or CLI)                              │
└────────────────┬────────────────────────────┬───────────────────┘
                 │                            │
                 ▼                            ▼
┌────────────────────────────┐  ┌──────────────────────────────┐
│    Question Generator      │  │    Answer Evaluator          │
│    (Claude API)            │  │    (Claude API)              │
└────────────────┬───────────┘  └──────────────┬───────────────┘
                 │                              │
                 ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Content Store                              │
│              (JSON files: concepts.json,                        │
│               questions.json, progress.json)                    │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────┐  ┌──────────────────────────────┐
│    PDF Processor           │  │    Concept Extractor         │
│    (PyPDF2/pdfplumber)     │  │    (Claude API)              │
└────────────────────────────┘  └──────────────────────────────┘
                 ▲
                 │
┌────────────────────────────┐
│   Lecture PDFs (17 files)  │
└────────────────────────────┘
```

### Data Flow

1. **Initialization Phase**: PDF Processor extracts text from all 17 lecture PDFs
2. **Concept Extraction Phase**: Concept Extractor uses Claude API to identify and structure concepts from extracted text
3. **Question Generation Phase**: Question Generator creates scenario-based questions for each concept
4. **Study Phase**: Student interacts with Study Interface to answer questions
5. **Evaluation Phase**: Answer Evaluator assesses responses and provides feedback
6. **Tracking Phase**: Coverage Tracker monitors progress and selects next questions

## Components and Interfaces

### 1. PDF Processor

**Responsibility**: Extract text content from PDF lecture materials

**Interface**:
```python
class PDFProcessor:
    def extract_text_from_pdf(pdf_path: str) -> str:
        """Extract text content from a single PDF file"""
        
    def process_all_pdfs(pdf_directory: str) -> Dict[str, str]:
        """Process all PDFs in directory, return mapping of filename to content"""
        
    def extract_with_structure(pdf_path: str) -> List[Section]:
        """Extract text while preserving section structure"""
```

**Implementation Notes**:
- Use `pdfplumber` library for robust text extraction
- Handle different PDF encodings (UTF-8, Latin-1)
- Preserve paragraph breaks and section headings
- Log errors for problematic PDFs but continue processing
- Return structured data with metadata (filename, page numbers, sections)

### 2. Concept Extractor

**Responsibility**: Identify and structure key concepts from extracted text

**Interface**:
```python
class ConceptExtractor:
    def extract_concepts(text: str, source_file: str, topic: str) -> List[Concept]:
        """Extract concepts from text using Claude API"""
        
    def structure_concept(raw_concept: str, context: str) -> Concept:
        """Structure a concept with definition, context, and relationships"""
        
    def find_related_concepts(concept: Concept, all_concepts: List[Concept]) -> List[str]:
        """Identify relationships between concepts"""
```

**Concept Data Model**:
```python
@dataclass
class Concept:
    id: str
    name: str
    definition: str
    context: str
    source_file: str
    topic_area: str
    related_concepts: List[str]
    keywords: List[str]
    extraction_timestamp: str
```

**Implementation Notes**:
- Use Claude API with structured prompts to extract concepts
- Prompt should request: concept name, definition, context, keywords
- Group concepts by topic area (Cloud Computing, DevOps, Networking, etc.)
- Identify relationships by analyzing keyword overlap and contextual similarity
- Store concepts in `concepts.json` with unique IDs

### 3. Question Generator

**Responsibility**: Generate scenario-based practice questions from concepts

**Interface**:
```python
class QuestionGenerator:
    def generate_question(concept: Concept, related_concepts: List[Concept]) -> Question:
        """Generate a scenario-based question for a concept"""
        
    def generate_model_answer(question: Question) -> str:
        """Generate a comprehensive model answer"""
        
    def validate_question_quality(question: Question) -> bool:
        """Validate that question meets quality standards"""
```

**Question Data Model**:
```python
@dataclass
class Question:
    id: str
    concept_ids: List[str]
    scenario: str
    question_text: str
    model_answer: str
    difficulty: str  # "basic", "intermediate", "advanced"
    topic_area: str
    generation_timestamp: str
```

**Implementation Notes**:
- Use Claude API with few-shot examples from sample questions
- Prompt should emphasize: real-world scenarios, application over memorization, explanation-based answers
- Include 2-3 sample questions in the prompt as style examples
- Generate questions that test understanding, analysis, and recommendation skills
- Validate questions are not simple recall (should require multi-sentence answers)
- Store questions in `questions.json`

**Question Generation Prompt Template**:
```
You are creating exam questions for a cloud computing course. Generate a scenario-based question that tests understanding, not memorization.

Concept: {concept_name}
Definition: {concept_definition}
Context: {concept_context}

Style examples:
[Include 2-3 sample questions from samplequestions.md]

Requirements:
- Create a realistic scenario with specific details
- Ask for explanation, analysis, or recommendation
- Require multi-sentence answer demonstrating understanding
- Test application of concept to real-world situation

Generate the question in this format:
Scenario: [detailed scenario]
Question: [what to explain/analyze/recommend]
```

### 4. Study Interface

**Responsibility**: Provide interactive environment for practicing questions

**Interface**:
```python
class StudyInterface:
    def start_session() -> None:
        """Initialize a new study session"""
        
    def get_next_question() -> Question:
        """Retrieve next question prioritizing untested concepts"""
        
    def submit_answer(question_id: str, answer: str) -> Feedback:
        """Submit answer and receive feedback"""
        
    def display_feedback(feedback: Feedback) -> None:
        """Display feedback in Korean"""
        
    def show_progress() -> CoverageStats:
        """Display coverage statistics"""
```

**Implementation Options**:
- **Option A**: Simple CLI interface using `rich` library for formatting
- **Option B**: Web interface using Flask with simple HTML/CSS/JavaScript
- **Recommendation**: Start with CLI for faster development, can add web UI later

**CLI Interface Flow**:
```
=== 중간고사 준비 시스템 ===

진행 상황: 15/87 개념 완료 (17%)

[질문 1/87]

시나리오: Sarah는 두 개의 애플리케이션을 구축하고 있습니다...

질문: TCP와 UDP의 주요 차이점을 설명하고...

답변을 입력하세요 (완료하려면 Ctrl+D):
> [사용자 입력]

[피드백]
관련 개념: TCP, UDP, 전송 계층 프로토콜
...

다음 질문으로 이동하시겠습니까? (y/n):
```

### 5. Answer Evaluator

**Responsibility**: Assess student answers and generate comprehensive feedback

**Interface**:
```python
class AnswerEvaluator:
    def evaluate_answer(question: Question, student_answer: str, concept: Concept) -> Feedback:
        """Evaluate answer and generate feedback"""
        
    def generate_feedback_korean(evaluation: Evaluation, concept: Concept) -> str:
        """Generate Korean language feedback"""
        
    def identify_gaps(student_answer: str, model_answer: str) -> List[str]:
        """Identify missing points or misconceptions"""
```

**Feedback Data Model**:
```python
@dataclass
class Feedback:
    question_id: str
    student_answer: str
    correctness_score: float  # 0.0 to 1.0
    related_concepts: List[str]
    definitions: Dict[str, str]
    explanation: str
    model_answer: str
    gaps_identified: List[str]
    strengths: List[str]
    feedback_text_korean: str
    feedback_text_english: str
    timestamp: str
```

**Implementation Notes**:
- Use Claude API to evaluate answers against model answers
- Prompt should request: correctness assessment, gap identification, strengths, comprehensive feedback
- Generate feedback in both Korean and English languages
- Include related concepts and definitions for deeper learning
- Reference specific lecture materials where relevant
- Store feedback in `progress.json` linked to user session

**Evaluation Prompt Template**:
```
You are evaluating a student's answer to an exam question. Provide comprehensive feedback in both Korean and English.

Question: {question_text}
Model Answer: {model_answer}
Student Answer: {student_answer}

Evaluate the answer and provide:
1. Correctness score (0-100)
2. What the student got right
3. What is missing or incorrect
4. Related concepts they should review
5. Comprehensive explanation in Korean
6. Comprehensive explanation in English
7. Definitions of key terms in both Korean and English

Format your response with clear sections for Korean and English feedback.
```

### 6. Coverage Tracker

**Responsibility**: Monitor which concepts have been tested and ensure comprehensive coverage

**Interface**:
```python
class CoverageTracker:
    def mark_concept_covered(concept_id: str, question_id: str) -> None:
        """Mark a concept as tested"""
        
    def get_untested_concepts() -> List[Concept]:
        """Get list of concepts not yet tested"""
        
    def get_coverage_stats() -> CoverageStats:
        """Get coverage statistics overall and by topic"""
        
    def select_next_concept(strategy: str = "untested_first") -> Concept:
        """Select next concept to test based on strategy"""
```

**Coverage Stats Data Model**:
```python
@dataclass
class CoverageStats:
    total_concepts: int
    tested_concepts: int
    coverage_percentage: float
    coverage_by_topic: Dict[str, float]
    untested_topics: List[str]
```

**Implementation Notes**:
- Maintain mapping of concept_id to list of question_ids answered
- Prioritize untested concepts when selecting next question
- Provide topic-level coverage statistics
- Allow filtering by topic area
- Store coverage data in `progress.json`

### 7. Content Store

**Responsibility**: Persist and retrieve all system data

**Interface**:
```python
class ContentStore:
    def save_concepts(concepts: List[Concept]) -> None:
        """Save concepts to concepts.json"""
        
    def load_concepts() -> List[Concept]:
        """Load concepts from concepts.json"""
        
    def save_questions(questions: List[Question]) -> None:
        """Save questions to questions.json"""
        
    def load_questions() -> List[Question]:
        """Load questions from questions.json"""
        
    def save_progress(progress: Progress) -> None:
        """Save user progress to progress.json"""
        
    def load_progress() -> Progress:
        """Load user progress from progress.json"""
```

**Storage Structure**:
```
data/
├── concepts.json          # All extracted concepts
├── questions.json         # All generated questions
├── progress.json          # User progress and coverage
└── extracted_text/        # Raw extracted PDF text
    ├── L01_01.txt
    ├── L02_01.txt
    └── ...
```

**Implementation Notes**:
- Use JSON for human-readable storage and easy debugging
- Implement atomic writes to prevent data corruption
- Add data validation on load
- Support incremental updates (don't rewrite entire files)
- Consider SQLite for future scalability if needed

## Data Models

### Complete Data Schema

```python
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

@dataclass
class Concept:
    id: str
    name: str
    definition: str
    context: str
    source_file: str
    topic_area: str
    related_concepts: List[str]
    keywords: List[str]
    extraction_timestamp: str

@dataclass
class Question:
    id: str
    concept_ids: List[str]
    scenario: str
    question_text: str
    model_answer: str
    difficulty: str
    topic_area: str
    generation_timestamp: str

@dataclass
class Feedback:
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
    timestamp: str

@dataclass
class Progress:
    session_id: str
    start_time: str
    concept_coverage: Dict[str, List[str]]  # concept_id -> [question_ids]
    answered_questions: List[str]
    total_questions_answered: int
    coverage_stats: CoverageStats

@dataclass
class CoverageStats:
    total_concepts: int
    tested_concepts: int
    coverage_percentage: float
    coverage_by_topic: Dict[str, float]
    untested_topics: List[str]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: PDF Processing Completeness
*For any* directory containing PDF files, when the PDF_Processor processes all files, the number of extracted text entries should equal the number of successfully processed PDFs, and any failed PDFs should have corresponding error log entries.
**Validates: Requirements 1.1, 1.3**

### Property 2: PDF Processing Resilience
*For any* set of PDFs where some fail to process, the PDF_Processor should continue processing remaining files and the total number of processed files plus failed files should equal the total number of input files.
**Validates: Requirements 1.3**

### Property 3: Content Persistence Round-Trip
*For any* extracted content, concepts, questions, or progress data saved to the Content_Store, loading the data should produce equivalent objects with all fields preserved.
**Validates: Requirements 1.4, 7.1, 7.3, 7.5**

### Property 4: Concept Data Completeness
*For any* concept extracted by the Concept_Extractor, the concept object should have all required fields populated: id, name, definition, context, source_file, topic_area, related_concepts, keywords, and extraction_timestamp.
**Validates: Requirements 2.2, 2.3, 2.4**

### Property 5: Question Data Completeness
*For any* question generated by the Question_Generator, the question object should have all required fields populated: id, concept_ids (non-empty), scenario, question_text, model_answer, difficulty, topic_area, and generation_timestamp.
**Validates: Requirements 3.5**

### Property 6: Answer Submission Flow
*For any* student answer submitted through the Study_Interface, the answer should be passed to the Answer_Evaluator and feedback should be returned.
**Validates: Requirements 4.3**

### Property 7: Feedback Data Completeness
*For any* feedback generated by the Answer_Evaluator, the feedback object should have all required fields populated: question_id, student_answer, correctness_score, related_concepts, definitions, explanation, model_answer, gaps_identified, strengths, feedback_text_korean, and timestamp.
**Validates: Requirements 5.2, 5.3, 5.4, 5.5**

### Property 8: Korean Language Support
*For any* Korean text input by a student or generated by the system, storing and retrieving the text should preserve all Korean characters without corruption or encoding errors.
**Validates: Requirements 4.5, 5.6, 10.1, 10.2, 10.3, 10.4, 10.5**

### Property 9: Coverage Tracking Updates
*For any* question answered by a student, the Coverage_Tracker should mark all associated concept_ids as covered, and those concepts should appear in the coverage records.
**Validates: Requirements 6.1, 6.2**

### Property 10: Untested Concept Identification
*For any* set of concepts and coverage records, the concepts identified as untested should be exactly those concepts whose IDs do not appear in the coverage records.
**Validates: Requirements 6.3**

### Property 11: Untested Concept Prioritization
*For any* question selection when untested concepts exist, the selected question should be associated with at least one concept that is not in the coverage records.
**Validates: Requirements 6.4**

### Property 12: Coverage Statistics Calculation
*For any* coverage state, the calculated coverage percentage should equal (number of tested concepts / total concepts) × 100, and topic-level percentages should be calculated using the same formula for concepts within each topic.
**Validates: Requirements 6.5, 9.4**

### Property 13: Content Store Query Filtering
*For any* query to the Content_Store filtering by topic, source_file, or coverage status, all returned concepts should match the filter criteria, and no concepts matching the criteria should be excluded.
**Validates: Requirements 7.6**

### Property 14: API Error Handling
*For any* API call that results in an error, the system should handle the error without crashing, log the error, and either retry the request or return a graceful error response.
**Validates: Requirements 8.4**

### Property 15: API Rate Limit Queueing
*For any* API request that encounters a rate limit error, the request should be added to a queue, and when the rate limit clears, queued requests should be processed in order.
**Validates: Requirements 8.5**

### Property 16: Topic Coverage Completeness
*For any* complete execution of the system with all 17 PDFs processed, questions should exist for all major topic areas: Cloud Computing, DevOps & SDLC, Twelve-Factor App, Linux CLI, AWS/GCP/Azure, Regions & Availability Zones, Git, Testing, CI/CD, Networking, IaC, Terraform, IAM, Firewalls, VMs, Machine Images, cloud-init, and systemd.
**Validates: Requirements 9.2**

### Property 17: Topic Filtering
*For any* topic filter applied to question selection, all returned questions should have a topic_area matching the filter, and no questions with matching topic_area should be excluded.
**Validates: Requirements 9.5**

## Error Handling

### PDF Processing Errors

**Error Types**:
- File not found
- Corrupted PDF files
- Unsupported PDF encryption
- Encoding errors
- Permission errors

**Handling Strategy**:
- Log error with filename and error type
- Continue processing remaining files
- Store partial results
- Report summary of failures at end of processing
- Provide option to retry failed files

**Implementation**:
```python
def process_all_pdfs(pdf_directory: str) -> Tuple[Dict[str, str], List[str]]:
    """
    Returns: (successful_extractions, failed_files)
    """
    successful = {}
    failed = []
    
    for pdf_file in get_pdf_files(pdf_directory):
        try:
            text = extract_text_from_pdf(pdf_file)
            successful[pdf_file] = text
        except Exception as e:
            logger.error(f"Failed to process {pdf_file}: {e}")
            failed.append(pdf_file)
    
    return successful, failed
```

### AI API Errors

**Error Types**:
- Network timeouts
- Rate limiting (429 errors)
- Invalid API key (401 errors)
- Service unavailable (503 errors)
- Invalid request format (400 errors)
- Token limit exceeded

**Handling Strategy**:
- Implement exponential backoff for retries
- Queue requests when rate limited
- Cache successful responses to avoid re-processing
- Provide fallback behavior for non-critical operations
- Display user-friendly error messages in Korean

**Implementation**:
```python
def call_claude_api_with_retry(prompt: str, max_retries: int = 3) -> str:
    """Call Claude API with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            response = claude_api.call(prompt)
            return response
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Rate limited, waiting {wait_time}s")
                time.sleep(wait_time)
            else:
                raise
        except NetworkError as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                raise
```

### Data Storage Errors

**Error Types**:
- Disk full
- Permission errors
- File corruption
- JSON parsing errors
- Concurrent access conflicts

**Handling Strategy**:
- Validate data before writing
- Use atomic writes (write to temp file, then rename)
- Implement file locking for concurrent access
- Keep backups of previous versions
- Validate data integrity on load

**Implementation**:
```python
def save_concepts_atomic(concepts: List[Concept]) -> None:
    """Save concepts with atomic write to prevent corruption"""
    temp_file = "data/concepts.json.tmp"
    backup_file = "data/concepts.json.bak"
    target_file = "data/concepts.json"
    
    # Write to temp file
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump([asdict(c) for c in concepts], f, ensure_ascii=False, indent=2)
    
    # Backup existing file
    if os.path.exists(target_file):
        shutil.copy(target_file, backup_file)
    
    # Atomic rename
    os.replace(temp_file, target_file)
```

### User Input Errors

**Error Types**:
- Empty answers
- Invalid commands
- Encoding issues with Korean text

**Handling Strategy**:
- Validate input before processing
- Provide clear error messages in Korean
- Allow users to retry or skip
- Preserve user input even if processing fails

## Testing Strategy

### Dual Testing Approach

The system will use both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs

Both approaches are complementary and necessary. Unit tests catch concrete bugs and validate specific scenarios, while property tests verify general correctness across a wide range of inputs.

### Unit Testing

**Focus Areas**:
- Specific examples of PDF extraction with known content
- Edge cases: empty PDFs, single-page PDFs, PDFs with special characters
- Error conditions: missing files, corrupted PDFs, permission errors
- Integration points: API calls, file I/O, data serialization
- Korean text handling: specific Korean strings, mixed Korean/English text

**Testing Framework**: pytest

**Example Unit Tests**:
```python
def test_extract_text_from_valid_pdf():
    """Test extraction from a known valid PDF"""
    text = extract_text_from_pdf("test_data/sample.pdf")
    assert "Cloud Computing" in text
    assert len(text) > 100

def test_extract_text_handles_missing_file():
    """Test error handling for missing file"""
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf("nonexistent.pdf")

def test_korean_text_round_trip():
    """Test Korean text is preserved through storage"""
    original = "클라우드 컴퓨팅"
    concept = Concept(name=original, ...)
    store.save_concepts([concept])
    loaded = store.load_concepts()[0]
    assert loaded.name == original
```

### Property-Based Testing

**Testing Library**: Hypothesis (Python property-based testing library)

**Configuration**: Minimum 100 iterations per property test

**Tagging Format**: Each test must reference its design document property:
```python
# Feature: midterm-study-system, Property 1: PDF Processing Completeness
```

**Focus Areas**:
- Data structure completeness across all generated objects
- Round-trip properties for persistence and encoding
- Coverage tracking calculations with various concept sets
- Filtering and querying with different criteria
- Error handling with various failure scenarios

**Example Property Tests**:
```python
from hypothesis import given, strategies as st

# Feature: midterm-study-system, Property 3: Content Persistence Round-Trip
@given(st.lists(st.builds(Concept, ...)))
def test_concept_persistence_round_trip(concepts):
    """For any list of concepts, saving and loading should preserve all data"""
    store.save_concepts(concepts)
    loaded = store.load_concepts()
    assert len(loaded) == len(concepts)
    for original, loaded_concept in zip(concepts, loaded):
        assert original.id == loaded_concept.id
        assert original.name == loaded_concept.name
        assert original.definition == loaded_concept.definition

# Feature: midterm-study-system, Property 4: Concept Data Completeness
@given(st.text(), st.text())
def test_concept_data_completeness(text, source_file):
    """For any extracted concept, all required fields should be populated"""
    concepts = extractor.extract_concepts(text, source_file, "Cloud Computing")
    for concept in concepts:
        assert concept.id is not None and concept.id != ""
        assert concept.name is not None and concept.name != ""
        assert concept.definition is not None
        assert concept.context is not None
        assert concept.source_file == source_file
        assert concept.topic_area == "Cloud Computing"
        assert isinstance(concept.related_concepts, list)
        assert isinstance(concept.keywords, list)
        assert concept.extraction_timestamp is not None

# Feature: midterm-study-system, Property 8: Korean Language Support
@given(st.text(alphabet=st.characters(whitelist_categories=('Lo',)), min_size=1))
def test_korean_text_preservation(korean_text):
    """For any Korean text, storage and retrieval should preserve all characters"""
    concept = Concept(id="test", name=korean_text, ...)
    store.save_concepts([concept])
    loaded = store.load_concepts()[0]
    assert loaded.name == korean_text

# Feature: midterm-study-system, Property 10: Untested Concept Identification
@given(st.lists(st.builds(Concept, ...)), st.sets(st.text()))
def test_untested_concept_identification(all_concepts, tested_ids):
    """Untested concepts should be exactly those not in coverage records"""
    coverage = {cid: ["q1"] for cid in tested_ids if cid in [c.id for c in all_concepts]}
    tracker = CoverageTracker(coverage)
    untested = tracker.get_untested_concepts(all_concepts)
    untested_ids = {c.id for c in untested}
    expected_untested = {c.id for c in all_concepts if c.id not in tested_ids}
    assert untested_ids == expected_untested

# Feature: midterm-study-system, Property 12: Coverage Statistics Calculation
@given(st.integers(min_value=1, max_value=100), st.integers(min_value=0, max_value=100))
def test_coverage_percentage_calculation(total, tested):
    """Coverage percentage should equal (tested / total) × 100"""
    tested = min(tested, total)  # Ensure tested <= total
    stats = CoverageStats(total_concepts=total, tested_concepts=tested, ...)
    expected = (tested / total) * 100
    assert abs(stats.coverage_percentage - expected) < 0.01
```

### Integration Testing

**Focus Areas**:
- End-to-end flow: PDF → Concepts → Questions → Study Session
- API integration with Claude
- File system operations
- Multi-component interactions

**Example Integration Tests**:
```python
def test_full_pipeline_integration():
    """Test complete flow from PDF to study session"""
    # Process PDFs
    texts, failed = processor.process_all_pdfs("test_data/pdfs")
    assert len(failed) == 0
    
    # Extract concepts
    concepts = []
    for filename, text in texts.items():
        concepts.extend(extractor.extract_concepts(text, filename, "Test Topic"))
    assert len(concepts) > 0
    
    # Generate questions
    questions = []
    for concept in concepts[:5]:  # Test with first 5 concepts
        question = generator.generate_question(concept, [])
        questions.append(question)
    assert len(questions) == 5
    
    # Simulate study session
    interface = StudyInterface()
    question = interface.get_next_question()
    feedback = interface.submit_answer(question.id, "Test answer")
    assert feedback.feedback_text_korean is not None
```

### Test Coverage Goals

- **Unit test coverage**: Minimum 80% code coverage
- **Property test coverage**: All 17 correctness properties implemented
- **Integration test coverage**: All major component interactions tested
- **Edge case coverage**: All identified edge cases from requirements tested

### Continuous Testing

- Run unit tests on every code change
- Run property tests (with reduced iterations) on every commit
- Run full property test suite (100+ iterations) nightly
- Run integration tests before releases

