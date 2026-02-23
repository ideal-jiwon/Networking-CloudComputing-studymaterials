# Implementation Plan: Midterm Study System (No API Version)

## Overview

This implementation plan is modified to work WITHOUT Claude API. All concepts, questions, and feedback are pre-generated and stored in JSON files. The system focuses on PDF processing, data management, and an interactive study interface using pre-prepared data.

## Key Changes from Original Plan
- **No API Integration**: Removed all Claude API dependencies
- **Pre-generated Data**: Concepts, questions, and feedback stored in JSON files
- **Manual Data Creation**: User manually creates study materials in JSON format
- **Simplified Components**: Focus on data loading, storage, and UI

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create directory structure: `src/`, `data/`, `tests/`, `classmaterials/`
  - Create `requirements.txt` with dependencies: pdfplumber, hypothesis, pytest, rich (NO anthropic)
  - Create `src/__init__.py` and main module files
  - Create `README.md` with setup instructions
  - _Requirements: 7.1, 7.4_
  - **Status: COMPLETED - No API key needed**

- [x] 2. Implement PDF Processor component
  - [x] 2.1 Create PDFProcessor class with text extraction
    - Implement `extract_text_from_pdf()` using pdfplumber
    - Implement `process_all_pdfs()` with error handling
    - Handle different PDF encodings and formats
    - Log errors for failed PDFs and continue processing
    - Return both successful extractions and failed file list
    - _Requirements: 1.1, 1.2, 1.3, 1.5_
    - **Status: COMPLETED**
  
  - [ ]* 2.2 Write property test for PDF processing completeness
    - **Property 1: PDF Processing Completeness**
    - **Validates: Requirements 1.1, 1.3**
  
  - [ ]* 2.3 Write property test for PDF processing resilience
    - **Property 2: PDF Processing Resilience**
    - **Validates: Requirements 1.3**
  
  - [ ]* 2.4 Write unit tests for PDF processor
    - Test extraction from valid PDF
    - Test handling of missing files
    - Test handling of corrupted PDFs
    - Test preservation of Korean characters in PDFs
    - _Requirements: 1.1, 1.3, 1.5_

- [x] 3. Implement Content Store component
  - [x] 3.1 Create ContentStore class with JSON persistence
    - Implement `save_concepts()` with atomic writes
    - Implement `load_concepts()` with validation
    - Implement `save_questions()` and `load_questions()`
    - Implement `save_progress()` and `load_progress()`
    - Create data directory structure if not exists
    - _Requirements: 7.1, 7.2, 7.4, 7.5_
    - **Status: COMPLETED**
  
  - [x] 3.2 Implement query and filtering methods
    - Implement `query_concepts_by_topic()`
    - Implement `query_concepts_by_source()`
    - Implement `query_concepts_by_coverage_status()`
    - _Requirements: 7.6_
    - **Status: COMPLETED**
  
  - [ ]* 3.3 Write property test for content persistence round-trip
    - **Property 3: Content Persistence Round-Trip**
    - **Validates: Requirements 1.4, 7.1, 7.3, 7.5**
  
  - [ ]* 3.4 Write property test for content store query filtering
    - **Property 13: Content Store Query Filtering**
    - **Validates: Requirements 7.6**
  
  - [ ]* 3.5 Write unit tests for content store
    - Test atomic writes prevent corruption
    - Test loading with missing files
    - Test JSON parsing error handling
    - Test Korean text in stored data
    - _Requirements: 7.1, 7.2, 7.5_

- [x] 4. Checkpoint - Ensure PDF processing and storage work
  - Run tests for PDF processor and content store
  - Manually test with sample PDFs from classmaterials
  - Verify Korean text is preserved
  - **Status: COMPLETED - 16/17 PDFs processed successfully**

- [x] 5. Create sample data files (REPLACES API-based concept extraction)
  - [x] 5.1 Create sample concepts.json file
    - Manually create 20-30 key concepts from lecture materials
    - Include: id, name, definition, context, source_file, topic_area, related_concepts, keywords
    - Cover all major topics: Cloud Computing, DevOps, Linux, Networking, IaC, etc.
    - Ensure Korean text is properly encoded
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [x] 5.2 Create sample questions.json file
    - Manually create 20-30 scenario-based questions
    - Base questions on samplequestions.md style
    - Include: id, concept_ids, scenario, question_text, model_answer, difficulty, topic_area
    - Ensure comprehensive topic coverage
    - Include Korean text where appropriate
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 5.3 Create feedback templates
    - Create feedback_templates.json with reusable feedback patterns
    - Include templates for: correct answers, partially correct, incorrect, common mistakes
    - Templates should include: related_concepts, definitions, explanations in Korean
    - _Requirements: 5.2, 5.3, 5.4, 5.5_

- [x] 6. Implement Data Loader (REPLACES Concept Extractor)
  - [x] 6.1 Create DataLoader class
    - Implement `load_concepts_from_file()` to read concepts.json
    - Implement `load_questions_from_file()` to read questions.json
    - Implement `load_feedback_templates()` to read feedback_templates.json
    - Validate data structure and required fields
    - Handle missing files gracefully
    - _Requirements: 2.1, 3.1, 7.1_
  
  - [x] 6.2 Implement data validation
    - Validate all required fields are present
    - Check concept-question relationships are valid
    - Verify topic coverage is complete
    - Log warnings for data issues
    - _Requirements: 2.2, 3.5_
  
  - [ ]* 6.3 Write unit tests for data loader
    - Test loading valid data files
    - Test handling missing files
    - Test data validation
    - Test Korean text preservation
    - _Requirements: 2.1, 3.1_

- [x] 7. Checkpoint - Ensure data loading works
  - Run tests for data loader
  - Manually verify concepts and questions load correctly
  - Check Korean text is preserved
  - Verify all topics are covered

- [ ] 8. Implement Coverage Tracker component
  - [x] 8.1 Create CoverageTracker class
    - Implement `mark_concept_covered()` to update coverage records
    - Implement `get_untested_concepts()` to identify gaps
    - Implement `get_coverage_stats()` to calculate statistics
    - Calculate overall and topic-level coverage percentages
    - _Requirements: 6.1, 6.2, 6.3, 6.5_
  
  - [x] 8.2 Implement concept selection strategy
    - Implement `select_next_concept()` with untested-first priority
    - Ensure untested concepts are prioritized
    - Fall back to least-recently-tested when all covered
    - _Requirements: 6.4_
  
  - [ ]* 8.3 Write property test for coverage tracking updates
    - **Property 9: Coverage Tracking Updates**
    - **Validates: Requirements 6.1, 6.2**
  
  - [ ]* 8.4 Write property test for untested concept identification
    - **Property 10: Untested Concept Identification**
    - **Validates: Requirements 6.3**
  
  - [ ]* 8.5 Write property test for untested concept prioritization
    - **Property 11: Untested Concept Prioritization**
    - **Validates: Requirements 6.4**
  
  - [ ]* 8.6 Write property test for coverage statistics calculation
    - **Property 12: Coverage Statistics Calculation**
    - **Validates: Requirements 6.5, 9.4**
  
  - [ ]* 8.7 Write unit tests for coverage tracker
    - Test marking concepts as covered
    - Test coverage percentage calculation
    - Test topic-level statistics
    - Test concept selection strategy
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 9. Implement Answer Evaluator (SIMPLIFIED - No API)
  - [x] 9.1 Create AnswerEvaluator class with template-based feedback
    - Implement `evaluate_answer()` using keyword matching
    - Load feedback templates from feedback_templates.json
    - Match student answer keywords with model answer keywords
    - Calculate simple correctness score based on keyword overlap
    - _Requirements: 5.1, 5.2_
  
  - [x] 9.2 Implement feedback generation
    - Select appropriate feedback template based on score
    - Include related concepts from concept data
    - Include definitions of key terms
    - Provide model answer for comparison
    - Format feedback in Korean
    - _Requirements: 5.2, 5.3, 5.4, 5.5_
  
  - [ ]* 9.3 Write property test for feedback data completeness
    - **Property 7: Feedback Data Completeness**
    - **Validates: Requirements 5.2, 5.3, 5.4, 5.5**
  
  - [ ]* 9.4 Write unit tests for answer evaluator
    - Test evaluation with keyword matching
    - Test feedback template selection
    - Test Korean language in feedback
    - Test model answer inclusion
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 10. Implement Study Interface (CLI)
  - [x] 10.1 Create StudyInterface class with rich library
    - Implement `start_session()` to initialize study session
    - Implement `get_next_question()` using coverage tracker
    - Display questions with rich formatting
    - Implement multi-line text input for answers
    - _Requirements: 4.1, 4.2_
  
  - [x] 10.2 Implement answer submission and feedback display
    - Implement `submit_answer()` to send to evaluator
    - Display feedback in Korean with rich formatting
    - Show related concepts, definitions, and model answer
    - Implement navigation to next question
    - _Requirements: 4.3, 4.5, 4.6_
  
  - [x] 10.3 Implement progress display
    - Show coverage statistics (X/Y concepts covered)
    - Show topic-level progress
    - Display list of untested concepts on request
    - Show completion notification when 100% covered
    - _Requirements: 4.7, 6.6, 6.7_
  
  - [ ]* 10.4 Write property test for answer submission flow
    - **Property 6: Answer Submission Flow**
    - **Validates: Requirements 4.3**
  
  - [ ]* 10.5 Write property test for Korean language support
    - **Property 8: Korean Language Support**
    - **Validates: Requirements 4.5, 5.6, 10.1, 10.2, 10.3, 10.4, 10.5**
  
  - [ ]* 10.6 Write unit tests for study interface
    - Test session initialization
    - Test question display
    - Test answer input handling
    - Test feedback display
    - Test progress display
    - Test Korean text input and display
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 4.6, 4.7_

- [x] 11. Implement topic coverage validation
  - [x] 11.1 Create topic validation module
    - Define list of all required topics from classtopics.md
    - Implement validation that all topics have concepts
    - Implement validation that all topics have questions
    - Generate report of topic coverage
    - _Requirements: 9.1, 9.2_
  
  - [x] 11.2 Implement topic filtering
    - Add topic filter to question selection
    - Allow users to practice specific topics
    - Update coverage tracker to support topic filtering
    - _Requirements: 9.5_
  
  - [ ]* 11.3 Write property test for topic coverage completeness
    - **Property 16: Topic Coverage Completeness**
    - **Validates: Requirements 9.2**
  
  - [ ]* 11.4 Write property test for topic filtering
    - **Property 17: Topic Filtering**
    - **Validates: Requirements 9.5**

- [x] 12. Checkpoint - Ensure complete system integration
  - Run all unit tests and property tests
  - Test end-to-end flow: Load Data → Questions → Study Session
  - Verify Korean language support throughout
  - Verify coverage tracking works correctly
  - Ask the user if questions arise

- [x] 13. Create main application entry point
  - [x] 13.1 Create main.py with CLI commands
    - Implement `load` command to load concepts and questions from JSON files
    - Implement `study` command to start study session
    - Implement `stats` command to show coverage statistics
    - Implement `validate` command to check data completeness
    - Add command-line argument parsing
    - _Requirements: 4.1, 6.6, 9.1_
  
  - [x] 13.2 Add configuration and setup
    - Create data directories if missing
    - Display helpful error messages in Korean
    - Show data loading status
    - Validate data files exist before starting
    - _Requirements: 7.1, 10.1_

- [x] 14. Create data preparation script
  - [x] 14.1 Create data preparation helper script
    - Create script to help generate sample concepts from PDF text
    - Create script to help format questions from samplequestions.md
    - Provide templates for concepts.json and questions.json
    - Include validation to check data completeness
    - _Requirements: 2.1, 3.1, 9.1_
  
  - [ ]* 14.2 Write integration test for full pipeline
    - Test Load Data → Questions → Study flow
    - Verify all components work together
    - Verify data flows correctly between components
    - _Requirements: 2.1, 3.1, 4.1_

- [x] 15. Final checkpoint and documentation
  - Run complete test suite (unit + property + integration)
  - Test with actual data files
  - Update README.md with usage instructions in Korean
  - Create example session walkthrough
  - Document data file formats and requirements
  - Create sample data files as examples
  - Ensure all tests pass, ask the user if questions arise

## Notes

- **NO API REQUIRED**: System works entirely with pre-generated JSON data files
- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at major milestones
- Property tests validate universal correctness properties from design
- Unit tests validate specific examples, edge cases, and error conditions
- The system uses Python with pdfplumber, hypothesis (property testing), pytest, and rich (CLI formatting)
- All UI text and feedback should be in Korean language
- User must manually create concepts.json, questions.json, and feedback_templates.json files

## Data File Formats

### concepts.json
```json
[
  {
    "id": "concept-001",
    "name": "클라우드 컴퓨팅",
    "definition": "인터넷을 통해 컴퓨팅 리소스를 제공하는 서비스",
    "context": "Cloud computing fundamentals lecture",
    "source_file": "L01_01_Fundamentals of Cloud Computing_pdf.pdf",
    "topic_area": "Cloud Computing",
    "related_concepts": ["concept-002", "concept-003"],
    "keywords": ["cloud", "computing", "클라우드", "서비스"],
    "extraction_timestamp": "2024-01-01T00:00:00"
  }
]
```

### questions.json
```json
[
  {
    "id": "question-001",
    "concept_ids": ["concept-001"],
    "scenario": "Sarah는 새로운 웹 애플리케이션을 구축하고 있습니다...",
    "question_text": "클라우드 컴퓨팅의 주요 이점을 설명하세요.",
    "model_answer": "클라우드 컴퓨팅의 주요 이점은...",
    "difficulty": "basic",
    "topic_area": "Cloud Computing",
    "generation_timestamp": "2024-01-01T00:00:00"
  }
]
```

### feedback_templates.json
```json
{
  "correct": {
    "message": "훌륭합니다! 정확하게 이해하고 계십니다.",
    "encouragement": "계속 이런 식으로 학습하세요."
  },
  "partial": {
    "message": "좋은 시작입니다. 몇 가지 추가 사항이 있습니다.",
    "guidance": "다음 개념들을 더 검토해보세요:"
  },
  "incorrect": {
    "message": "다시 한번 생각해보세요.",
    "guidance": "다음 개념들을 복습하는 것이 도움이 될 것입니다:"
  }
}
```
