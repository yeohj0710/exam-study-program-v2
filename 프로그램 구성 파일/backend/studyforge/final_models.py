from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


IssueSeverity = Literal["error", "warning"]


@dataclass
class ValidationIssue:
    severity: IssueSeverity
    code: str
    message: str
    question_id: str | None = None
    line: int | None = None


@dataclass
class Question:
    id: str
    studyset_id: str
    ordinal: int
    title: str
    prompt_markdown: str
    answer_markdown: str
    note_markdown: str = ""
    asset_paths: list[str] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)


@dataclass
class MarkdownParseResult:
    studyset_id: str
    title: str
    questions: list[Question]
    issues: list[ValidationIssue] = field(default_factory=list)


@dataclass
class StudySet:
    id: str
    title: str
    slug: str
    path: str
    updated_at: float
    question_count: int = 0
    issue_count: int = 0


@dataclass
class QuestionProgress:
    question_id: str
    memorized: bool = False
    seen_count: int = 0
    reveal_count: int = 0
    last_seen_at: float | None = None
    updated_at: float = 0.0
