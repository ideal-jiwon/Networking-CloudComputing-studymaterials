# Midterm Study System

An interactive study system for midterm exam preparation. It uses pre-generated concepts and scenario-based practice questions extracted from lecture materials, with a CLI-based study interface that provides keyword-matching feedback and tracks your coverage across all topics.

No API keys required — the system runs entirely on pre-generated JSON data files.

## Features

- PDF text extraction from lecture materials
- Structured concept management via JSON files
- Scenario-based practice questions with real-world contexts
- Interactive CLI study sessions (powered by the `rich` library)
- Keyword-based answer evaluation with automatic feedback
- Per-concept and per-topic coverage tracking
- Topic filtering for focused study

## Installation

### Prerequisites

- Python 3.8+

### Setup

1. Clone the repository:
```bash
git clone git@github.com:ideal-jiwon/Networking-CloudComputing-studymaterials.git
cd Networking-CloudComputing-studymaterials
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Place lecture PDF files in the `classmaterials/` directory.

## Project Structure

```
├── src/                        # Source code
│   ├── models.py              # Data models (Concept, Question, Feedback, etc.)
│   ├── pdf_processor.py       # PDF text extraction
│   ├── data_loader.py         # JSON data loading and validation
│   ├── content_store.py       # Data persistence (JSON-based)
│   ├── answer_evaluator.py    # Keyword-matching answer evaluation
│   ├── coverage_tracker.py    # Study progress tracking
│   ├── study_interface.py     # CLI study interface
│   └── topic_validator.py     # Topic coverage validation
├── data/                       # Data files
│   ├── concepts.json          # Core concepts
│   ├── questions.json         # Scenario-based questions
│   ├── feedback_templates.json # Feedback templates
│   └── extracted_text/        # Extracted PDF text
├── tests/                      # Test files
├── classmaterials/             # Lecture PDF files
├── main.py                     # Main entry point (CLI)
├── prepare_data.py             # Data preparation tools
└── requirements.txt            # Python dependencies
```

## Usage

### 1. Load and verify data

Load concepts and questions, and display a summary:
```bash
python main.py load
```

### 2. Start a study session

Launch an interactive study session:
```bash
python main.py study
```

Commands available during a study session:
- Type your answer and press Enter to get feedback
- `n` — next question
- `p` — show progress
- `t` — filter by topic
- `s` — skip current question
- `q` — quit (progress is saved automatically)

### 3. Check study progress

View coverage statistics:
```bash
python main.py stats
```

### 4. Validate data files

Check data completeness and integrity:
```bash
python main.py validate
```

## Data Preparation Tools

```bash
python prepare_data.py extract          # Extract text from PDFs
python prepare_data.py template         # Generate template files
python prepare_data.py format-questions # Parse sample questions
python prepare_data.py validate         # Validate data files
```

## Data File Formats

### concepts.json

```json
[
  {
    "id": "c-cloud-001",
    "name": "Cloud Computing",
    "definition": "A service model that delivers computing resources on-demand over the internet",
    "context": "Cloud computing is the delivery of computing services over the internet.",
    "source_file": "L01_01_Fundamentals of Cloud Computing_pdf.pdf",
    "topic_area": "Fundamentals of Cloud Computing",
    "related_concepts": ["c-cloud-002", "c-cloud-003"],
    "keywords": ["cloud", "computing", "service model"]
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (format: `c-{topic}-{number}`) |
| `name` | string | Concept name |
| `definition` | string | Concept definition |
| `context` | string | Context from lecture material |
| `source_file` | string | Source PDF filename |
| `topic_area` | string | Topic area (matches classtopics.md) |
| `related_concepts` | list[string] | Related concept IDs |
| `keywords` | list[string] | Search keywords |

### questions.json

```json
[
  {
    "id": "q001",
    "concept_ids": ["c-network-003"],
    "scenario": "Sarah is building two applications: a banking portal...",
    "question_text": "Explain the key differences between TCP and UDP...",
    "model_answer": "TCP is connection-oriented, provides reliable ordered delivery...",
    "difficulty": "medium",
    "topic_area": "Networking Fundamentals"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (format: `q{number}`) |
| `concept_ids` | list[string] | Related concept IDs (at least one required) |
| `scenario` | string | Real-world scenario |
| `question_text` | string | Question text |
| `model_answer` | string | Model answer |
| `difficulty` | string | Difficulty level (`basic`, `medium`, `hard`) |
| `topic_area` | string | Topic area |

### feedback_templates.json

```json
{
  "correct": {
    "message_korean": "Excellent! You have a correct understanding.",
    "message_english": "Excellent! You have a correct understanding."
  },
  "partially_correct": {
    "message_korean": "Good start! Here are a few additional points.",
    "guidance_korean": "Review the following concepts:"
  },
  "incorrect": {
    "message_korean": "Let's think about this again.",
    "guidance_korean": "It would help to review these concepts:"
  },
  "scoring_thresholds": {
    "correct": { "min_score": 80 },
    "partially_correct": { "min_score": 40 },
    "incorrect": { "min_score": 0 }
  }
}
```

Scoring thresholds: correct (80+), partially correct (40–79), incorrect (0–39).

## Topics Covered

- Fundamentals of Cloud Computing
- The Software Development Life Cycle (SDLC)
- The Twelve-Factor App
- Introduction to DevOps
- The Linux Command Line
- Cloud Regions & Availability Zones
- Unit, Integration, Performance, and Load Testing
- Continuous Integration with GitHub Actions
- Version Control with Git
- Git Forking Workflow
- Networking Fundamentals
- Infrastructure as Code w/Terraform
- Identity & Access Management (IAM)
- Network Firewall
- Virtual Machines
- Custom Machine Images
- cloud-init
- systemd — System and Service Manager

## Development

### Running Tests

```bash
pytest tests/ -v                              # All tests
pytest tests/ --cov=src -v                    # With coverage
pytest tests/ -v --hypothesis-show-statistics  # With property-based test stats
```

### Testing Strategy

- Unit tests: Verify specific component behavior
- Property-based tests: Validate universal properties using Hypothesis
- Integration tests: Verify data flow between components

## License

This project was created for educational purposes.
