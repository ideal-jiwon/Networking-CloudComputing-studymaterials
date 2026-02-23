#!/usr/bin/env python3
"""Data preparation helper script for the Midterm Study System.

Commands:
    extract          - Extract text from PDFs in classmaterials/ and save to data/extracted_text/
    template         - Generate empty template files for concepts.json and questions.json
    format-questions - Parse samplequestions.md and output structured question templates
    validate         - Run comprehensive data validation

Usage:
    python prepare_data.py extract
    python prepare_data.py template [--output-dir DIR]
    python prepare_data.py format-questions [--input FILE]
    python prepare_data.py validate [--data-dir DIR]
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path so we can import from src/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pdf_processor import PDFProcessor
from src.data_loader import DataLoader
from src.topic_validator import TopicValidator


# ---------------------------------------------------------------------------
# extract command
# ---------------------------------------------------------------------------

def cmd_extract(args):
    """Extract text from all PDFs in classmaterials/ and save as .txt files."""
    pdf_dir = args.pdf_dir
    output_dir = Path(args.output_dir)

    if not Path(pdf_dir).exists():
        print(f"[ERROR] PDF directory not found: {pdf_dir}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    processor = PDFProcessor()
    print(f"Extracting text from PDFs in {pdf_dir} ...")
    successful, failed = processor.process_all_pdfs(pdf_dir)

    for filename, text in successful.items():
        txt_name = Path(filename).stem + ".txt"
        out_path = output_dir / txt_name
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  [OK] {filename} -> {out_path} ({len(text)} chars)")

    if failed:
        print(f"\nFailed to process {len(failed)} file(s):")
        for name in failed:
            print(f"  [FAIL] {name}")

    print(f"\nDone: {len(successful)} extracted, {len(failed)} failed.")
    return 0


# ---------------------------------------------------------------------------
# template command
# ---------------------------------------------------------------------------

CONCEPT_TEMPLATE = [
    {
        "id": "c-{topic}-{num}  (unique id, e.g. c-cloud-001)",
        "name": "개념 이름 (Concept Name in English)",
        "definition": "한국어로 된 개념 정의 (Korean definition of the concept)",
        "context": "English context explaining when/how this concept is used",
        "source_file": "L01_01_Fundamentals of Cloud Computing_pdf.pdf",
        "topic_area": "Fundamentals of Cloud Computing",
        "related_concepts": ["c-cloud-002", "c-cloud-003"],
        "keywords": ["keyword1", "keyword2", "키워드"],
        "extraction_timestamp": "2024-01-01T00:00:00",
    }
]

QUESTION_TEMPLATE = [
    {
        "id": "q001  (unique id, e.g. q001)",
        "concept_ids": ["c-cloud-001"],
        "scenario": "A realistic scenario describing a situation the student must analyse...",
        "question_text": "The actual question asking the student to explain, analyse, or recommend...",
        "model_answer": "A comprehensive model answer covering key points...",
        "difficulty": "basic | medium | advanced",
        "topic_area": "Fundamentals of Cloud Computing",
        "generation_timestamp": "2024-01-01T00:00:00",
    }
]


def cmd_template(args):
    """Generate empty template JSON files for concepts and questions."""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    concepts_path = output_dir / "concepts_template.json"
    questions_path = output_dir / "questions_template.json"

    with open(concepts_path, "w", encoding="utf-8") as f:
        json.dump(CONCEPT_TEMPLATE, f, ensure_ascii=False, indent=2)
    print(f"Concept template written to {concepts_path}")

    with open(questions_path, "w", encoding="utf-8") as f:
        json.dump(QUESTION_TEMPLATE, f, ensure_ascii=False, indent=2)
    print(f"Question template written to {questions_path}")

    print("\nField descriptions:")
    print("  Concept fields:")
    print("    id              - Unique identifier (format: c-{topic}-{num})")
    print("    name            - Korean + English concept name")
    print("    definition      - Korean definition of the concept")
    print("    context         - English context / explanation")
    print("    source_file     - PDF filename the concept comes from")
    print("    topic_area      - Topic area matching classtopics.md")
    print("    related_concepts- List of related concept ids")
    print("    keywords        - Search keywords (Korean + English)")
    print("    extraction_timestamp - ISO timestamp")
    print()
    print("  Question fields:")
    print("    id              - Unique identifier (format: q{num})")
    print("    concept_ids     - List of concept ids this question tests")
    print("    scenario        - Real-world scenario description")
    print("    question_text   - The actual question")
    print("    model_answer    - Comprehensive model answer")
    print("    difficulty      - basic, medium, or advanced")
    print("    topic_area      - Topic area matching classtopics.md")
    print("    generation_timestamp - ISO timestamp")
    return 0


# ---------------------------------------------------------------------------
# format-questions command
# ---------------------------------------------------------------------------

def parse_sample_questions(filepath: str) -> list:
    """Parse samplequestions.md and return a list of question dicts.

    Each question block starts with a line matching 'Question N – Title'.
    The paragraph(s) before the last paragraph form the scenario,
    and the last paragraph is the question text.
    """
    path = Path(filepath)
    if not path.exists():
        print(f"[ERROR] File not found: {filepath}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into question blocks using the "Question N" header pattern
    pattern = re.compile(r"^(Question\s+\d+\s*[–—-]\s*.+)$", re.MULTILINE)
    headers = list(pattern.finditer(content))

    questions = []
    for i, match in enumerate(headers):
        header = match.group(1).strip()
        start = match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
        body = content[start:end].strip()

        # Split body into paragraphs (separated by blank lines)
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]

        if len(paragraphs) >= 2:
            scenario = "\n\n".join(paragraphs[:-1])
            question_text = paragraphs[-1]
        elif paragraphs:
            scenario = ""
            question_text = paragraphs[0]
        else:
            scenario = ""
            question_text = ""

        # Extract question number from header
        num_match = re.search(r"Question\s+(\d+)", header)
        q_num = num_match.group(1) if num_match else str(i + 1)

        questions.append(
            {
                "id": f"q{q_num.zfill(3)}",
                "concept_ids": ["<FILL_IN>"],
                "scenario": scenario,
                "question_text": question_text,
                "model_answer": "<FILL_IN>",
                "difficulty": "medium",
                "topic_area": "<FILL_IN>",
                "generation_timestamp": datetime.now().isoformat(),
            }
        )

    return questions


def cmd_format_questions(args):
    """Parse samplequestions.md and output structured question templates."""
    questions = parse_sample_questions(args.input)

    if not questions:
        print("No questions parsed. Check the input file.")
        return 1

    print(f"Parsed {len(questions)} question(s) from {args.input}\n")
    output = json.dumps(questions, ensure_ascii=False, indent=2)
    print(output)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\nSaved to {out_path}")

    print("\nNOTE: Fields marked <FILL_IN> must be completed manually:")
    print("  - concept_ids : list of concept ids this question tests")
    print("  - model_answer: comprehensive model answer")
    print("  - topic_area  : topic area matching classtopics.md")
    return 0


# ---------------------------------------------------------------------------
# validate command
# ---------------------------------------------------------------------------

def cmd_validate(args):
    """Run comprehensive data validation and print a report."""
    data_dir = args.data_dir
    print(f"Validating data in {data_dir} ...\n")

    loader = DataLoader(data_dir=data_dir)
    all_ok = True

    # --- Load concepts ---
    try:
        concepts, concept_errors = loader.load_concepts_from_file()
        print(f"Concepts: loaded {len(concepts)}")
        if concept_errors:
            all_ok = False
            for err in concept_errors:
                print(f"  [WARN] {err}")
    except (FileNotFoundError, ValueError) as e:
        print(f"  [ERROR] {e}")
        concepts = []
        all_ok = False

    # --- Load questions ---
    try:
        questions, question_errors = loader.load_questions_from_file()
        print(f"Questions: loaded {len(questions)}")
        if question_errors:
            all_ok = False
            for err in question_errors:
                print(f"  [WARN] {err}")
    except (FileNotFoundError, ValueError) as e:
        print(f"  [ERROR] {e}")
        questions = []
        all_ok = False

    # --- Load feedback templates ---
    try:
        templates, template_errors = loader.load_feedback_templates()
        print(f"Feedback templates: loaded")
        if template_errors:
            all_ok = False
            for err in template_errors:
                print(f"  [WARN] {err}")
    except (FileNotFoundError, ValueError) as e:
        print(f"  [ERROR] {e}")
        all_ok = False

    # --- Data integrity ---
    if concepts and questions:
        print("\n--- Data Integrity ---")
        warnings = loader.validate_data_integrity(concepts, questions)
        if warnings:
            all_ok = False
            for w in warnings:
                print(f"  [WARN] {w}")
        else:
            print("  All concept-question relationships are valid.")

    # --- Topic coverage ---
    print("\n--- Topic Coverage ---")
    try:
        validator = TopicValidator()
        report = validator.generate_report(concepts, questions)

        print(f"  Required topics : {report.total_required_topics}")
        print(f"  With concepts   : {report.topics_with_concepts}")
        print(f"  With questions  : {report.topics_with_questions}")
        print(f"  Fully covered   : {report.topics_fully_covered}")

        if report.missing_concepts:
            all_ok = False
            print(f"\n  Topics missing concepts:")
            for t in report.missing_concepts:
                print(f"    - {t}")

        if report.missing_questions:
            all_ok = False
            print(f"\n  Topics missing questions:")
            for t in report.missing_questions:
                print(f"    - {t}")

        if report.topic_details:
            print(f"\n  Per-topic breakdown:")
            for td in report.topic_details:
                status = "OK" if td.has_concepts and td.has_questions else "INCOMPLETE"
                print(f"    [{status}] {td.topic}: {td.concept_count} concepts, {td.question_count} questions")
    except Exception as e:
        print(f"  [ERROR] Topic validation failed: {e}")
        all_ok = False

    # --- Summary ---
    print()
    if all_ok:
        print("=== VALIDATION PASSED ===")
    else:
        print("=== VALIDATION FOUND ISSUES (see warnings above) ===")

    return 0 if all_ok else 1


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Data preparation helper for the Midterm Study System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # extract
    p_extract = subparsers.add_parser("extract", help="Extract text from PDFs")
    p_extract.add_argument("--pdf-dir", default="classmaterials", help="PDF directory (default: classmaterials)")
    p_extract.add_argument("--output-dir", default="data/extracted_text", help="Output directory (default: data/extracted_text)")

    # template
    p_template = subparsers.add_parser("template", help="Generate template JSON files")
    p_template.add_argument("--output-dir", default="data", help="Output directory (default: data)")

    # format-questions
    p_fq = subparsers.add_parser("format-questions", help="Parse samplequestions.md into JSON")
    p_fq.add_argument("--input", default="samplequestions.md", help="Input file (default: samplequestions.md)")
    p_fq.add_argument("--output", default=None, help="Optional output file path")

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate data completeness")
    p_validate.add_argument("--data-dir", default="data", help="Data directory (default: data)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "extract": cmd_extract,
        "template": cmd_template,
        "format-questions": cmd_format_questions,
        "validate": cmd_validate,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
