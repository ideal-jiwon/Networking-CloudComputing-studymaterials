#!/usr/bin/env python3
"""중간고사 준비 시스템 - 메인 애플리케이션 진입점.

Midterm Study System CLI entry point.
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.data_loader import DataLoader
from src.content_store import ContentStore
from src.coverage_tracker import CoverageTracker
from src.study_interface import StudyInterface
from src.topic_validator import TopicValidator

console = Console()

DATA_DIR = "data"
REQUIRED_FILES = {
    "concepts": Path(DATA_DIR) / "concepts.json",
    "questions": Path(DATA_DIR) / "questions.json",
    "feedback_templates": Path(DATA_DIR) / "feedback_templates.json",
}


def ensure_data_directory() -> None:
    """데이터 디렉토리가 없으면 생성합니다."""
    data_path = Path(DATA_DIR)
    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)
        console.print(f"[dim]데이터 디렉토리를 생성했습니다: {DATA_DIR}/[/dim]")


def check_required_files(required: list[str] | None = None) -> bool:
    """필수 데이터 파일이 존재하는지 확인합니다.

    Args:
        required: 확인할 파일 키 목록. None이면 모든 파일을 확인합니다.

    Returns:
        모든 필수 파일이 존재하면 True.
    """
    keys = required or list(REQUIRED_FILES.keys())
    missing = []
    for key in keys:
        path = REQUIRED_FILES[key]
        if not path.exists():
            missing.append(str(path))

    if missing:
        console.print("[red]오류: 다음 데이터 파일이 없습니다:[/red]")
        for f in missing:
            console.print(f"  [red]• {f}[/red]")
        console.print(
            "\n[yellow]데이터 파일을 data/ 디렉토리에 준비해주세요.[/yellow]"
        )
        return False
    return True


def cmd_load(args: argparse.Namespace) -> None:
    """load 명령: 개념과 질문 데이터를 로드하고 요약을 표시합니다."""
    ensure_data_directory()
    if not check_required_files():
        sys.exit(1)

    console.print("[cyan]데이터를 로딩 중입니다...[/cyan]")

    loader = DataLoader(DATA_DIR)
    concepts, questions, feedback_templates, errors = loader.load_all_data()

    # 로딩 결과 요약
    console.print(
        Panel(
            f"[bold]개념:[/bold] {len(concepts)}개 로드 완료\n"
            f"[bold]질문:[/bold] {len(questions)}개 로드 완료\n"
            f"[bold]피드백 템플릿:[/bold] {'로드 완료' if feedback_templates else '없음'}",
            title="📚 데이터 로딩 결과",
            border_style="green",
        )
    )

    # 주제별 분포
    topic_concepts: dict[str, int] = {}
    for c in concepts:
        topic_concepts[c.topic_area] = topic_concepts.get(c.topic_area, 0) + 1

    topic_questions: dict[str, int] = {}
    for q in questions:
        topic_questions[q.topic_area] = topic_questions.get(q.topic_area, 0) + 1

    all_topics = sorted(set(topic_concepts.keys()) | set(topic_questions.keys()))
    if all_topics:
        table = Table(title="주제별 데이터 분포")
        table.add_column("주제", style="cyan")
        table.add_column("개념 수", justify="right")
        table.add_column("질문 수", justify="right")

        for topic in all_topics:
            table.add_row(
                topic,
                str(topic_concepts.get(topic, 0)),
                str(topic_questions.get(topic, 0)),
            )
        console.print(table)

    if errors:
        console.print(f"\n[yellow]경고: {len(errors)}개의 데이터 문제가 발견되었습니다.[/yellow]")
        for err in errors[:5]:
            console.print(f"  [dim]• {err}[/dim]")
        if len(errors) > 5:
            console.print(f"  [dim]... 외 {len(errors) - 5}개[/dim]")


def cmd_study(args: argparse.Namespace) -> None:
    """study 명령: 대화형 학습 세션을 시작합니다."""
    ensure_data_directory()
    if not check_required_files():
        sys.exit(1)

    loader = DataLoader(DATA_DIR)
    store = ContentStore(DATA_DIR)
    interface = StudyInterface(data_loader=loader, content_store=store, console=console)
    interface.run()


def cmd_stats(args: argparse.Namespace) -> None:
    """stats 명령: 학습 진행률 통계를 표시합니다."""
    ensure_data_directory()
    if not check_required_files(["concepts", "questions"]):
        sys.exit(1)

    console.print("[cyan]통계를 계산 중입니다...[/cyan]")

    loader = DataLoader(DATA_DIR)
    concepts, _ = loader.load_concepts_from_file()
    store = ContentStore(DATA_DIR)
    progress = store.load_progress()

    existing_coverage = progress.concept_coverage if progress else None
    tracker = CoverageTracker(concepts, existing_coverage)
    stats = tracker.get_coverage_stats()

    # 전체 진행률
    console.print(
        Panel(
            f"[bold]{stats.tested_concepts}/{stats.total_concepts} 개념 완료 "
            f"({stats.coverage_percentage:.1f}%)[/bold]",
            title="📊 학습 진행률",
            border_style="cyan",
        )
    )

    # 주제별 진행률
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

        console.print(table)

    # 미학습 주제
    if stats.untested_topics:
        console.print(
            f"\n[yellow]미학습 주제: {', '.join(stats.untested_topics)}[/yellow]"
        )

    if stats.coverage_percentage >= 100:
        console.print(
            Panel(
                "[bold green]축하합니다! 모든 개념을 학습했습니다! 🎉[/bold green]",
                border_style="green",
            )
        )


def cmd_validate(args: argparse.Namespace) -> None:
    """validate 명령: 데이터 완전성을 검증합니다."""
    ensure_data_directory()
    if not check_required_files(["concepts", "questions"]):
        sys.exit(1)

    console.print("[cyan]데이터 검증 중입니다...[/cyan]")

    loader = DataLoader(DATA_DIR)
    concepts, concept_errors = loader.load_concepts_from_file()
    questions, question_errors = loader.load_questions_from_file()

    # DataLoader 무결성 검증
    integrity_warnings = loader.validate_data_integrity(concepts, questions)

    # TopicValidator 검증
    validator = TopicValidator()
    report = validator.generate_report(concepts, questions)

    # 결과 표시
    console.print(
        Panel(
            f"[bold]개념:[/bold] {len(concepts)}개 (오류 {len(concept_errors)}개)\n"
            f"[bold]질문:[/bold] {len(questions)}개 (오류 {len(question_errors)}개)\n"
            f"[bold]무결성 경고:[/bold] {len(integrity_warnings)}개",
            title="🔍 데이터 검증 결과",
            border_style="cyan",
        )
    )

    # 주제 커버리지 리포트
    table = Table(title="주제 커버리지 리포트")
    table.add_column("주제", style="cyan")
    table.add_column("개념", justify="right")
    table.add_column("질문", justify="right")
    table.add_column("상태", justify="center")

    for detail in report.topic_details:
        if detail.has_concepts and detail.has_questions:
            status = "[green]✓ 완료[/green]"
        elif detail.has_concepts or detail.has_questions:
            status = "[yellow]부분[/yellow]"
        else:
            status = "[red]없음[/red]"
        table.add_row(
            detail.topic,
            str(detail.concept_count),
            str(detail.question_count),
            status,
        )

    console.print(table)

    console.print(
        f"\n[bold]전체 주제:[/bold] {report.total_required_topics}개 | "
        f"[bold]완전 커버:[/bold] {report.topics_fully_covered}개 | "
        f"[bold]개념 있음:[/bold] {report.topics_with_concepts}개 | "
        f"[bold]질문 있음:[/bold] {report.topics_with_questions}개"
    )

    # 경고 표시
    all_warnings = concept_errors + question_errors + integrity_warnings
    if all_warnings:
        console.print(f"\n[yellow]총 {len(all_warnings)}개의 경고:[/yellow]")
        for w in all_warnings[:10]:
            console.print(f"  [dim]• {w}[/dim]")
        if len(all_warnings) > 10:
            console.print(f"  [dim]... 외 {len(all_warnings) - 10}개[/dim]")

    if report.missing_concepts:
        console.print(
            f"\n[red]개념이 없는 주제: {', '.join(report.missing_concepts)}[/red]"
        )
    if report.missing_questions:
        console.print(
            f"\n[red]질문이 없는 주제: {', '.join(report.missing_questions)}[/red]"
        )

    if not all_warnings and not report.missing_concepts and not report.missing_questions:
        console.print("\n[green]모든 검증을 통과했습니다! ✓[/green]")


def build_parser() -> argparse.ArgumentParser:
    """CLI 인자 파서를 생성합니다."""
    parser = argparse.ArgumentParser(
        description="중간고사 준비 시스템 (Midterm Study System)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "사용 예시:\n"
            "  python main.py load       데이터 로드 및 요약 표시\n"
            "  python main.py study      학습 세션 시작\n"
            "  python main.py stats      학습 진행률 통계\n"
            "  python main.py validate   데이터 완전성 검증\n"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", help="실행할 명령")

    subparsers.add_parser("load", help="개념과 질문 데이터를 로드하고 요약을 표시합니다")
    subparsers.add_parser("study", help="대화형 학습 세션을 시작합니다")
    subparsers.add_parser("stats", help="학습 진행률 통계를 표시합니다")
    subparsers.add_parser("validate", help="데이터 완전성을 검증합니다")

    return parser


def main() -> None:
    """메인 진입점."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "load": cmd_load,
        "study": cmd_study,
        "stats": cmd_stats,
        "validate": cmd_validate,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
