"""Interactive study interface for practicing questions using rich library."""

import sys
from typing import List, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown

from .models import Concept, Question, Feedback, CoverageStats
from .data_loader import DataLoader
from .coverage_tracker import CoverageTracker
from .answer_evaluator import AnswerEvaluator
from .content_store import ContentStore


class StudyInterface:
    """Interactive CLI study interface using rich library for formatting."""

    def __init__(
        self,
        data_loader: Optional[DataLoader] = None,
        content_store: Optional[ContentStore] = None,
        console: Optional[Console] = None,
        input_func=None,
    ):
        """Initialize StudyInterface.

        Args:
            data_loader: DataLoader instance for loading study data.
            content_store: ContentStore instance for persisting progress.
            console: Rich Console instance (for testing injection).
            input_func: Callable for reading user input (for testing injection).
        """
        self.data_loader = data_loader or DataLoader()
        self.content_store = content_store or ContentStore()
        self.console = console or Console()
        self._input_func = input_func or input

        self.concepts: List[Concept] = []
        self.questions: List[Question] = []
        self.feedback_templates: Dict = {}
        self.coverage_tracker: Optional[CoverageTracker] = None
        self.evaluator: Optional[AnswerEvaluator] = None
        self.question_number: int = 0
        self._session_active: bool = False
        self.topic_filter: Optional[str] = None
        self._asked_question_ids: set = set()

    def start_session(self) -> None:
        """Initialize a study session by loading data and restoring progress."""
        self.console.print(
            Panel(
                "[bold cyan]중간고사 준비 시스템[/bold cyan]",
                title="=== Midterm Study System ===",
                expand=False,
            )
        )

        # Load data
        self.concepts, self.questions, self.feedback_templates, errors = (
            self.data_loader.load_all_data()
        )

        if errors:
            self.console.print(
                f"[yellow]데이터 로딩 경고: {len(errors)}개의 문제가 발견되었습니다.[/yellow]"
            )

        if not self.concepts or not self.questions:
            self.console.print("[red]오류: 개념 또는 질문 데이터가 없습니다.[/red]")
            self._session_active = False
            return

        # Restore progress if available
        progress = self.content_store.load_progress()
        existing_coverage = progress.concept_coverage if progress else None

        self.coverage_tracker = CoverageTracker(self.concepts, existing_coverage)
        self.evaluator = AnswerEvaluator(self.feedback_templates, self.concepts)
        self.question_number = 0
        self._session_active = True

        # Show initial progress
        stats = self.coverage_tracker.get_coverage_stats()
        self.console.print(
            f"\n진행 상황: {stats.tested_concepts}/{stats.total_concepts} 개념 완료 "
            f"({stats.coverage_percentage:.0f}%)\n"
        )

    def get_next_question(self) -> Optional[Question]:
        """Retrieve the next question prioritizing untested concepts.
        Skips questions that have already been asked in this session.

        Respects the current topic_filter if set.

        Returns:
            Next Question object, or None if no questions available.
        """
        if not self.coverage_tracker or not self.questions:
            return None

        concept = self.coverage_tracker.select_next_concept(
            topic_filter=self.topic_filter
        )
        if concept is None:
            return None

        # Find a question that covers this concept and hasn't been asked yet
        for q in self.questions:
            if q.id not in self._asked_question_ids and concept.id in q.concept_ids:
                if self.topic_filter is None or q.topic_area == self.topic_filter:
                    self._asked_question_ids.add(q.id)
                    return q

        # Fallback: return first unseen question matching topic filter
        if self.topic_filter:
            for q in self.questions:
                if q.id not in self._asked_question_ids and q.topic_area == self.topic_filter:
                    self._asked_question_ids.add(q.id)
                    return q
            return None

        # Fallback: any unseen question
        for q in self.questions:
            if q.id not in self._asked_question_ids:
                self._asked_question_ids.add(q.id)
                return q

        return None


    def display_question(self, question: Question) -> None:
        """Display a question with rich formatting.

        Args:
            question: Question to display.
        """
        self.question_number += 1
        total = len(self.questions)

        self.console.print(
            Panel(
                f"[bold]시나리오:[/bold]\n{question.scenario}\n\n"
                f"[bold]질문:[/bold]\n{question.question_text}",
                title=f"[질문 {self.question_number}/{total}]",
                border_style="blue",
            )
        )

    def get_answer_input(self) -> str:
        """Get multi-line text input from the user.

        User types their answer and presses Enter twice on an empty line to submit.
        Single-line commands ('q', 'p', 's') are returned immediately on the first line.

        Returns:
            The user's answer as a single string.
        """
        self.console.print(
            "[dim]답변을 입력하세요 (완료하려면 빈 줄 두 번 입력, 명령어: q/p/s/t):[/dim]"
        )
        lines: List[str] = []
        empty_count = 0

        while True:
            try:
                line = self._input_func("> ")
            except EOFError:
                break

            # On the first line, check for single-char commands
            if not lines and line.strip().lower() in ("q", "p", "s", "t"):
                return line.strip()

            if line.strip() == "":
                empty_count += 1
                if empty_count >= 2:
                    break
                lines.append("")
            else:
                empty_count = 0
                lines.append(line)

        return "\n".join(lines).strip()

    def submit_answer(self, question_id: str, answer: str) -> Optional[Feedback]:
        """Submit an answer to the evaluator and update coverage.

        Args:
            question_id: ID of the question being answered.
            answer: Student's answer text.

        Returns:
            Feedback object, or None if evaluation fails.
        """
        if not self.evaluator or not self.coverage_tracker:
            return None

        # Find the question
        question = next((q for q in self.questions if q.id == question_id), None)
        if question is None:
            return None

        # Evaluate
        feedback = self.evaluator.evaluate_answer(question, answer)

        # Mark concepts as covered
        for concept_id in question.concept_ids:
            self.coverage_tracker.mark_concept_covered(concept_id, question_id)

        return feedback

    def display_feedback(self, feedback: Feedback) -> None:
        """Display feedback in Korean with rich formatting.

        Args:
            feedback: Feedback object to display.
        """
        # Score color
        score = feedback.correctness_score
        if score >= 80:
            score_style = "bold green"
        elif score >= 40:
            score_style = "bold yellow"
        else:
            score_style = "bold red"

        # Build feedback content
        parts: List[str] = []

        # Related concepts
        if feedback.related_concepts:
            parts.append(
                f"[bold]관련 개념:[/bold] {', '.join(feedback.related_concepts)}"
            )

        # Definitions
        if feedback.definitions:
            parts.append("\n[bold]주요 정의:[/bold]")
            for name, defn in feedback.definitions.items():
                parts.append(f"  • {name}: {defn}")

        # Korean feedback text
        if feedback.feedback_text_korean:
            parts.append(f"\n{feedback.feedback_text_korean}")

        # Model answer
        parts.append(f"\n[bold]모범 답안:[/bold]\n{feedback.model_answer}")

        content = "\n".join(parts)

        self.console.print(
            Panel(
                content,
                title=f"[피드백] 점수: [{score_style}]{score:.0f}/100[/{score_style}]",
                border_style="green" if score >= 80 else "yellow" if score >= 40 else "red",
            )
        )

    def show_progress(self) -> Optional[CoverageStats]:
        """Display coverage statistics.

        Returns:
            CoverageStats object, or None if tracker not initialized.
        """
        if not self.coverage_tracker:
            return None

        stats = self.coverage_tracker.get_coverage_stats()

        # Overall progress
        self.console.print(
            Panel(
                f"[bold]{stats.tested_concepts}/{stats.total_concepts} 개념 완료 "
                f"({stats.coverage_percentage:.1f}%)[/bold]",
                title="진행 상황",
                border_style="cyan",
            )
        )

        # Topic-level progress table
        if stats.coverage_by_topic:
            table = Table(title="주제별 진행 상황")
            table.add_column("주제", style="cyan")
            table.add_column("진행률", justify="right")
            table.add_column("상태", justify="center")

            for topic, pct in sorted(stats.coverage_by_topic.items()):
                if pct >= 100:
                    status = "[green]✓ 완료[/green]"
                elif pct > 0:
                    status = "[yellow]진행 중[/yellow]"
                else:
                    status = "[red]미시작[/red]"
                table.add_row(topic, f"{pct:.0f}%", status)

            self.console.print(table)

        # Untested topics
        if stats.untested_topics:
            self.console.print(
                f"\n[yellow]미학습 주제: {', '.join(stats.untested_topics)}[/yellow]"
            )

        # Completion notification
        if stats.coverage_percentage >= 100:
            self.console.print(
                Panel(
                    "[bold green]축하합니다! 모든 개념을 학습했습니다! 🎉[/bold green]",
                    border_style="green",
                )
            )

        return stats

    def show_untested_concepts(self) -> None:
        """Display list of untested concepts."""
        if not self.coverage_tracker:
            return

        untested = self.coverage_tracker.get_untested_concepts()
        if not untested:
            self.console.print("[green]모든 개념이 학습되었습니다![/green]")
            return

        table = Table(title=f"미학습 개념 ({len(untested)}개)")
        table.add_column("#", style="dim", width=4)
        table.add_column("개념", style="cyan")
        table.add_column("주제", style="yellow")

        for i, concept in enumerate(untested, 1):
            table.add_row(str(i), concept.name, concept.topic_area)

        self.console.print(table)

    def select_topic(self) -> None:
        """Let the user select a topic to filter questions by.

        Displays a numbered list of available topics. Entering 0 clears the filter.
        """
        topics = sorted({c.topic_area for c in self.concepts})
        if not topics:
            self.console.print("[yellow]사용 가능한 주제가 없습니다.[/yellow]")
            return

        self.console.print("\n[bold cyan]주제 선택[/bold cyan]")
        self.console.print("  0. 전체 (필터 해제)")
        for i, topic in enumerate(topics, 1):
            self.console.print(f"  {i}. {topic}")

        try:
            choice = self._input_func("주제 번호를 입력하세요: ")
            idx = int(choice)
        except (EOFError, ValueError):
            self.console.print("[yellow]잘못된 입력입니다.[/yellow]")
            return

        if idx == 0:
            self.topic_filter = None
            self.console.print("[green]주제 필터가 해제되었습니다.[/green]")
        elif 1 <= idx <= len(topics):
            self.topic_filter = topics[idx - 1]
            self.console.print(f"[green]주제 필터 설정: {self.topic_filter}[/green]")
        else:
            self.console.print("[yellow]잘못된 번호입니다.[/yellow]")


    def run(self) -> None:
        """Main loop that drives the study session.

        Supports commands:
            'q' - quit
            'p' - show progress
            's' - skip question
            't' - select topic filter
        """
        self.start_session()

        if not self._session_active:
            return

        while True:
            question = self.get_next_question()
            if question is None:
                if self.topic_filter:
                    self.console.print(
                        f"[yellow]'{self.topic_filter}' 주제에 대한 질문이 없습니다.[/yellow]"
                    )
                else:
                    self.console.print("[yellow]더 이상 질문이 없습니다.[/yellow]")
                break

            self.display_question(question)

            # Get answer (with command support)
            answer = self.get_answer_input()

            # Handle commands
            if answer.lower() == "q":
                self.console.print("[cyan]학습을 종료합니다. 수고하셨습니다![/cyan]")
                self._save_progress()
                break
            elif answer.lower() == "p":
                self.show_progress()
                continue
            elif answer.lower() == "s":
                self.console.print("[dim]질문을 건너뜁니다.[/dim]")
                continue
            elif answer.lower() == "t":
                self.select_topic()
                continue

            if not answer:
                self.console.print("[yellow]답변을 입력해주세요.[/yellow]")
                continue

            # Submit and show feedback
            feedback = self.submit_answer(question.id, answer)
            if feedback:
                self.display_feedback(feedback)

            # Ask to continue
            self.console.print()
            try:
                choice = self._input_func(
                    "다음 질문으로 이동하시겠습니까? (y/n/p/q): "
                )
            except EOFError:
                break

            if choice.lower() == "q":
                self.console.print("[cyan]학습을 종료합니다. 수고하셨습니다![/cyan]")
                self._save_progress()
                break
            elif choice.lower() == "p":
                self.show_progress()
            elif choice.lower() == "n":
                self.console.print("[cyan]학습을 종료합니다. 수고하셨습니다![/cyan]")
                self._save_progress()
                break

        # Check for 100% completion
        if self.coverage_tracker:
            stats = self.coverage_tracker.get_coverage_stats()
            if stats.coverage_percentage >= 100:
                self.console.print(
                    Panel(
                        "[bold green]축하합니다! 모든 개념을 학습했습니다! 🎉[/bold green]",
                        border_style="green",
                    )
                )


    def _save_progress(self) -> None:
        """Save current progress to content store."""
        if not self.coverage_tracker:
            return

        from datetime import datetime
        from .models import Progress

        stats = self.coverage_tracker.get_coverage_stats()
        progress = Progress(
            session_id="current",
            start_time=datetime.now().isoformat(),
            concept_coverage=self.coverage_tracker.concept_coverage,
            answered_questions=[],
            total_questions_answered=self.question_number,
            coverage_stats=stats,
        )
        self.content_store.save_progress(progress)
        self.console.print("[dim]진행 상황이 저장되었습니다.[/dim]")
