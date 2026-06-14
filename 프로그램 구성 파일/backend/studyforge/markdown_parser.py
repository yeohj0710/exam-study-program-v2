from __future__ import annotations

import re
from pathlib import Path

from .final_models import MarkdownParseResult, Question, ValidationIssue

QUESTION_RE = re.compile(r"^#\s+(?P<title>.+?)\s*$")
QUESTION_ID_RE = re.compile(r"<!--\s*sf:id:\s*(?P<id>[-A-Za-z0-9_:.]+)\s*-->")
ANSWER_RE = re.compile(r"^(?:답|정답)\s*:\s*(?P<answer>.*)$", re.IGNORECASE)
SOURCE_RE = re.compile(r"^(?:출처|reference|source)\s*[:：]", re.IGNORECASE)
GENERIC_QUESTION_HEADING_RE = re.compile(r"^(?:question|q|문제|문항)\s*\d*$", re.IGNORECASE)


def _strip_blank_edges(lines: list[str]) -> str:
    start = 0
    end = len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start:end])


def _asset_paths(markdown: str) -> list[str]:
    return re.findall(r"!\[[^\]]*]\(([^)]+)\)", markdown)


def _question_starts(lines: list[str]) -> list[int]:
    return [index for index, line in enumerate(lines) if QUESTION_RE.match(line)]


def _is_generic_question_heading(title: str) -> bool:
    return bool(GENERIC_QUESTION_HEADING_RE.match(title.strip()))


def insert_missing_question_ids(markdown: str, *, studyset_id: str) -> str:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    starts = _question_starts(lines)
    missing_by_start: dict[int, str] = {}
    for ordinal, start in enumerate(starts, start=1):
        end = starts[ordinal] if ordinal < len(starts) else len(lines)
        block = "\n".join(lines[start + 1 : end])
        if not QUESTION_ID_RE.search(block):
            missing_by_start[start] = f"<!-- sf:id: {studyset_id}-{ordinal:03d} -->"

    output: list[str] = []
    for index, line in enumerate(lines):
        output.append(line)
        if index in missing_by_start:
            output.append(missing_by_start[index])
    return "\n".join(output)


def parse_studyset_markdown(
    markdown: str,
    *,
    studyset_id: str,
    asset_root: Path | None,
) -> MarkdownParseResult:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    result = MarkdownParseResult(studyset_id=studyset_id, title=studyset_id, questions=[])
    seen_ids: set[str] = set()

    starts = _question_starts(lines)
    for ordinal, start in enumerate(starts, start=1):
        end = starts[ordinal] if ordinal < len(starts) else len(lines)
        heading = lines[start]
        match = QUESTION_RE.match(heading)
        heading_text = match.group("title").strip() if match else ""
        title = f"Question {ordinal}"
        block = lines[start + 1 : end]

        question_id = ""
        content_lines: list[str] = []
        for line in block:
            id_match = QUESTION_ID_RE.search(line)
            if id_match and not question_id:
                question_id = id_match.group("id")
                continue
            content_lines.append(line)

        prompt_lines: list[str] = []
        answer_lines: list[str] = []
        source_lines: list[str] = []
        has_answer = False
        section = "prompt"
        in_source = False
        parse_lines = content_lines
        if heading_text and not _is_generic_question_heading(heading_text):
            rest_lines = content_lines[:]
            while rest_lines and not rest_lines[0].strip():
                rest_lines.pop(0)
            parse_lines = [heading_text, "", *rest_lines]

        for line in parse_lines:
            answer_match = ANSWER_RE.match(line)
            if answer_match:
                section = "answer"
                in_source = False
                has_answer = True
                first_answer = answer_match.group("answer").strip()
                if first_answer:
                    answer_lines.append(first_answer)
                continue

            if section == "answer":
                if SOURCE_RE.match(line.strip()):
                    in_source = True
                    source_lines.append(line)
                elif in_source and line.strip():
                    source_lines.append(line)
                elif in_source:
                    in_source = False
                    answer_lines.append(line)
                else:
                    answer_lines.append(line)
            else:
                prompt_lines.append(line)

        if not question_id:
            question_id = f"{studyset_id}-{ordinal:03d}"

        question = Question(
            id=question_id,
            studyset_id=studyset_id,
            ordinal=ordinal,
            title=title,
            prompt_markdown=_strip_blank_edges(prompt_lines),
            answer_markdown=_strip_blank_edges(answer_lines),
            source_markdown=_strip_blank_edges(source_lines),
            note_markdown="",
            asset_paths=_asset_paths("\n".join(parse_lines)),
        )
        _append_asset_issues(question, result, asset_root, line_number=start + 1)

        if not has_answer:
            issue = ValidationIssue(
                severity="warning",
                code="missing_answer",
                message="Question is missing an answer line. Use `답: ...`.",
                question_id=question.id,
                line=start + 1,
            )
            question.issues.append(issue)
            result.issues.append(issue)

        if question.id in seen_ids:
            issue = ValidationIssue(
                severity="error",
                code="duplicate_question_id",
                message=f"Duplicate question id: {question.id}",
                question_id=question.id,
                line=start + 1,
            )
            question.issues.append(issue)
            result.issues.append(issue)
        seen_ids.add(question.id)
        result.questions.append(question)

    return result


def _append_asset_issues(
    question: Question,
    result: MarkdownParseResult,
    asset_root: Path | None,
    *,
    line_number: int,
) -> None:
    if asset_root is None:
        return
    for asset_path in question.asset_paths:
        path = Path(asset_path)
        if path.is_absolute():
            issue = ValidationIssue(
                severity="warning",
                code="absolute_asset_path",
                message=f"Image link should use a relative asset path: {asset_path}",
                question_id=question.id,
                line=line_number,
            )
            question.issues.append(issue)
            result.issues.append(issue)
        elif not (asset_root / path).exists():
            issue = ValidationIssue(
                severity="warning",
                code="missing_asset",
                message=f"Linked asset does not exist: {asset_path}",
                question_id=question.id,
                line=line_number,
            )
            question.issues.append(issue)
            result.issues.append(issue)
