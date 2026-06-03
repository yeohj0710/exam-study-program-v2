from __future__ import annotations

from pathlib import Path


def infer_subject_from_pdf(path: Path) -> str:
    parts = path.parts
    for index, part in enumerate(parts):
        if part in {"중간고사 정리자료", "중간고사 범위 수업자료"} and index > 0:
            return parts[index - 1]
    return path.parent.parent.name if path.parent.name else path.stem


def should_import_midterm_pdf(path: Path, include_lectures: bool = False) -> bool:
    name = path.name
    path_text = str(path)
    in_study_folder = "중간고사 정리자료" in path_text
    in_lecture_folder = "중간고사 범위 수업자료" in path_text
    if not in_study_folder and not (include_lectures and in_lecture_folder):
        return False
    if "성적" in name:
        return False
    if "수업자료" in name and not include_lectures:
        return False
    return any(token in name for token in ("정리", "요약", "문제", "풀이")) or include_lectures


def discover_midterm_pdfs(root: Path, include_lectures: bool = False) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(root)
    return sorted(
        [
            path
            for path in root.rglob("*.pdf")
            if should_import_midterm_pdf(path, include_lectures=include_lectures)
        ],
        key=lambda item: str(item),
    )
