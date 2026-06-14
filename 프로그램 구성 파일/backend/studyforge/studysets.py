from __future__ import annotations

from pathlib import Path

from .final_models import StudySet
from .hashing import slugify
from .markdown_parser import parse_studyset_markdown


def _studyset_path(studysets_root: Path, studyset_id: str) -> Path:
    if not studyset_id or any(char in studyset_id for char in '<>:"/\\|?*'):
        raise ValueError("Invalid studyset id.")
    path = (studysets_root / f"{studyset_id}.md").resolve()
    root = studysets_root.resolve()
    if not path.is_relative_to(root):
        raise ValueError("Invalid studyset id.")
    return path


def create_studyset(studysets_root: Path, *, title: str) -> StudySet:
    slug = slugify(title)
    path = studysets_root / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return _studyset_from_path(path)


def read_studyset(studysets_root: Path, studyset_id: str) -> str:
    return _studyset_path(studysets_root, studyset_id).read_text(encoding="utf-8")


def save_studyset(studysets_root: Path, studyset_id: str, markdown: str) -> None:
    path = _studyset_path(studysets_root, studyset_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")


def list_studysets(studysets_root: Path) -> list[StudySet]:
    if not studysets_root.exists():
        return []
    return [_studyset_from_path(path) for path in sorted(studysets_root.glob("*.md"), key=lambda item: item.name)]


def _studyset_from_path(path: Path) -> StudySet:
    markdown = path.read_text(encoding="utf-8")
    slug = path.stem
    parsed = parse_studyset_markdown(markdown, studyset_id=slug, asset_root=None)
    return StudySet(
        id=slug,
        title=slug,
        slug=slug,
        path=str(path),
        updated_at=path.stat().st_mtime,
        question_count=len(parsed.questions),
        issue_count=len(parsed.issues),
    )
