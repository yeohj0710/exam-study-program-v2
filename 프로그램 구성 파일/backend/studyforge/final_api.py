from __future__ import annotations

from base64 import b64decode
from binascii import Error as Base64Error
from dataclasses import asdict
import os
from pathlib import Path
import re
from threading import Lock
from typing import Literal
from urllib.parse import quote
import webbrowser

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .asset_manager import save_image_asset
from .final_models import QuestionProgress
from .final_progress import (
    load_final_progress,
    mark_memorized,
    record_reveal,
    record_seen,
    restore_question,
    save_final_progress,
)
from .markdown_parser import parse_studyset_markdown
from .studyset_pdf import export_studyset_pdf
from .studysets import create_studyset, list_studysets, read_studyset, save_studyset

PROJECT_ROOT = Path(os.environ.get("STUDYFORGE_APP_ROOT", Path(__file__).resolve().parents[2]))


def resolve_data_root(app_root: Path) -> Path:
    override = os.environ.get("EXAM_STUDY_DATA_ROOT")
    if override:
        return Path(override)
    return app_root.resolve().parent / "문제 데이터"


DATA_ROOT = resolve_data_root(PROJECT_ROOT)
STUDYSETS_ROOT = DATA_ROOT
ASSET_ROOT = DATA_ROOT / "assets"
FINAL_PROGRESS_PATH = DATA_ROOT / "progress.json"

router = APIRouter()
_progress_lock = Lock()


class StudySetCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)


class StudySetSaveRequest(BaseModel):
    markdown: str


class AssetUploadRequest(BaseModel):
    content_base64: str
    content_type: str
    alt_text: str = "image"


class QuestionProgressRequest(BaseModel):
    action: Literal["seen", "reveal", "memorized"]


class SourceOpenRequest(BaseModel):
    reference: str = Field(min_length=1, max_length=2000)


SOURCE_PATH_RE = re.compile(
    r"(?P<path>[A-Za-z]:\\[^+\n\r,]+?\.(?:pdf|pptx?|docx?|hwp|hwpx|png|jpe?g|webp))",
    re.IGNORECASE,
)
SOURCE_PAGE_RE = re.compile(r"(?:p|page|쪽|페이지|slide|슬라이드)\.?\s*(?P<page>\d+)", re.IGNORECASE)


@router.get("/api/studysets")
def get_studysets() -> dict[str, object]:
    return {"studysets": [asdict(item) for item in list_studysets(STUDYSETS_ROOT)]}


@router.post("/api/studysets")
def post_studyset(request: StudySetCreateRequest) -> dict[str, object]:
    return asdict(create_studyset(STUDYSETS_ROOT, title=request.title.strip()))


@router.get("/api/studysets/{studyset_id}")
def get_studyset(studyset_id: str) -> dict[str, object]:
    markdown = _read_or_404(studyset_id)
    return _studyset_payload(studyset_id, markdown)


@router.put("/api/studysets/{studyset_id}")
def put_studyset(studyset_id: str, request: StudySetSaveRequest) -> dict[str, object]:
    markdown = request.markdown
    save_studyset(STUDYSETS_ROOT, studyset_id, markdown)
    return _studyset_payload(studyset_id, markdown)


@router.post("/api/studysets/{studyset_id}/assets")
def post_studyset_asset(studyset_id: str, request: AssetUploadRequest) -> dict[str, object]:
    _read_or_404(studyset_id)
    try:
        content = b64decode(request.content_base64, validate=True)
    except Base64Error as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 image content.") from exc
    try:
        saved = save_image_asset(
            ASSET_ROOT,
            studyset_slug=studyset_id,
            content=content,
            content_type=request.content_type,
            alt_text=request.alt_text,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(saved)


@router.get("/api/studysets/{studyset_id}/questions")
def get_studyset_questions(studyset_id: str) -> dict[str, object]:
    markdown = _read_or_404(studyset_id)
    parsed = parse_studyset_markdown(markdown, studyset_id=studyset_id, asset_root=_data_root())
    return {
        "studyset_id": studyset_id,
        "questions": _questions_payload(parsed.questions),
        "issues": [asdict(issue) for issue in parsed.issues],
    }


@router.get("/api/studysets/{studyset_id}/pdf")
def get_studyset_pdf(studyset_id: str) -> FileResponse:
    markdown = _read_or_404(studyset_id)
    parsed = parse_studyset_markdown(markdown, studyset_id=studyset_id, asset_root=_data_root())
    try:
        output_path = export_studyset_pdf(
            studyset_id=studyset_id,
            questions=parsed.questions,
            output_path=_pdf_export_path(studyset_id),
            asset_root=_data_root(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename=f"{studyset_id}_문답.pdf",
    )


@router.post("/api/source/open")
def post_source_open(request: SourceOpenRequest) -> dict[str, object]:
    target, page = _resolve_source_reference(request.reference)
    url = target.as_uri()
    if target.suffix.lower() == ".pdf" and page:
        url = f"{url}#page={page}"
    if not webbrowser.open(url):
        raise HTTPException(status_code=500, detail="Source could not be opened.")
    return {"ok": True, "path": str(target), "page": page}


@router.post("/api/source/resolve")
def post_source_resolve(request: SourceOpenRequest) -> dict[str, object]:
    target, page = _resolve_source_reference(request.reference)
    return {"ok": True, "path": str(target), "page": page, "url": _source_file_url(target, page)}


@router.get("/api/source/file")
def get_source_file(path: str) -> FileResponse:
    target = _validate_source_file(Path(path))
    media_type = "application/pdf" if target.suffix.lower() == ".pdf" else None
    return FileResponse(target, media_type=media_type)


def validation_report() -> dict[str, object]:
    studysets = list_studysets(STUDYSETS_ROOT)
    issues = []
    question_count = 0
    for studyset in studysets:
        markdown = read_studyset(STUDYSETS_ROOT, studyset.id)
        parsed = parse_studyset_markdown(markdown, studyset_id=studyset.id, asset_root=_data_root())
        question_count += len(parsed.questions)
        issues.extend(asdict(issue) for issue in parsed.issues)
    return {
        "ok": not any(issue["severity"] == "error" for issue in issues),
        "studyset_count": len(studysets),
        "question_count": question_count,
        "issue_count": len(issues),
        "issues": issues,
    }


@router.patch("/api/questions/{question_id}/progress")
def patch_question_progress(question_id: str, request: QuestionProgressRequest) -> dict[str, object]:
    with _progress_lock:
        progress = load_final_progress(FINAL_PROGRESS_PATH)
        if request.action == "seen":
            entry = record_seen(progress, question_id)
        elif request.action == "reveal":
            entry = record_reveal(progress, question_id)
        else:
            entry = mark_memorized(progress, question_id)
        save_final_progress(FINAL_PROGRESS_PATH, progress)
    return {"progress": asdict(entry)}


@router.delete("/api/questions/{question_id}/progress")
def delete_question_progress(question_id: str) -> dict[str, object]:
    with _progress_lock:
        progress = load_final_progress(FINAL_PROGRESS_PATH)
        entry = restore_question(progress, question_id)
        save_final_progress(FINAL_PROGRESS_PATH, progress)
    return {"progress": asdict(entry)}


def _read_or_404(studyset_id: str) -> str:
    try:
        return read_studyset(STUDYSETS_ROOT, studyset_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Studyset not found.") from exc


def _studyset_payload(studyset_id: str, markdown: str) -> dict[str, object]:
    parsed = parse_studyset_markdown(markdown, studyset_id=studyset_id, asset_root=_data_root())
    return {
        "id": studyset_id,
        "title": parsed.title,
        "markdown": markdown,
        "questions": _questions_payload(parsed.questions),
        "issues": [asdict(issue) for issue in parsed.issues],
    }


def _questions_payload(questions) -> list[dict[str, object]]:
    progress = load_final_progress(FINAL_PROGRESS_PATH)
    payload = []
    for question in questions:
        item = asdict(question)
        item["progress"] = asdict(progress.get(question.id, QuestionProgress(question_id=question.id)))
        payload.append(item)
    return payload


def _data_root() -> Path:
    return ASSET_ROOT.parent


def _pdf_export_path(studyset_id: str) -> Path:
    return DATA_ROOT / "exports" / f"{studyset_id}_문답.pdf"


def _resolve_source_reference(reference: str) -> tuple[Path, int | None]:
    normalized = re.sub(r"\s*\r?\n\s*", " ", reference)
    path_match = SOURCE_PATH_RE.search(normalized)
    if not path_match:
        raise HTTPException(status_code=400, detail="Source reference must include a full local file path.")

    target = _validate_source_file(Path(path_match.group("path").strip().strip('"')))

    page = None
    page_text = normalized[path_match.end() : path_match.end() + 80]
    page_match = SOURCE_PAGE_RE.search(page_text)
    if page_match:
        page = int(page_match.group("page"))
    return target, page


def _validate_source_file(target: Path) -> Path:
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Source file not found.")
    if target.suffix.lower() not in {".pdf", ".ppt", ".pptx", ".doc", ".docx", ".hwp", ".hwpx", ".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=400, detail="Unsupported source file type.")
    return target


def _source_file_url(target: Path, page: int | None) -> str:
    url = f"/api/source/file?path={quote(str(target))}"
    if target.suffix.lower() == ".pdf" and page:
        url = f"{url}#page={page}"
    return url
