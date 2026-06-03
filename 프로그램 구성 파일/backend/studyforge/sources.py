from __future__ import annotations

from pathlib import Path

PDF_NAME_TOKENS = ("정리", "요약", "문제", "풀이")
MIDTERM_STUDY_FOLDERS = {"중간고사 정리자료", "중간고사 범위 수업자료"}
EXCLUDED_NAME_TOKENS = ("성적",)


def infer_subject_from_pdf(path: Path) -> str:
    parts = path.parts
    for index, part in enumerate(parts):
        if part in MIDTERM_STUDY_FOLDERS and index > 0:
            return parts[index - 1]
    return path.parent.name if path.parent.name else path.stem


def is_excluded_pdf(path: Path, include_lectures: bool = False) -> bool:
    name = path.name
    if any(token in name for token in EXCLUDED_NAME_TOKENS):
        return True
    if "수업자료" in name and not include_lectures:
        return True
    return False


def should_import_midterm_pdf(path: Path, include_lectures: bool = False) -> bool:
    name = path.name
    path_text = str(path)
    in_study_folder = "중간고사 정리자료" in path_text
    in_lecture_folder = "중간고사 범위 수업자료" in path_text
    if not in_study_folder and not (include_lectures and in_lecture_folder):
        return False
    if is_excluded_pdf(path, include_lectures=include_lectures):
        return False
    return any(token in name for token in PDF_NAME_TOKENS) or include_lectures


def should_import_general_pdf(path: Path, include_lectures: bool = False) -> bool:
    if path.suffix.lower() != ".pdf":
        return False
    return not is_excluded_pdf(path, include_lectures=include_lectures)


def discover_midterm_pdfs(root: Path, include_lectures: bool = False) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(root)
    pdfs = sorted(root.rglob("*.pdf"), key=lambda item: str(item))
    targeted = [path for path in pdfs if should_import_midterm_pdf(path, include_lectures=include_lectures)]
    if targeted:
        return targeted
    return [path for path in pdfs if should_import_general_pdf(path, include_lectures=include_lectures)]
