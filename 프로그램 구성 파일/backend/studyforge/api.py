from __future__ import annotations

import hashlib
import os
import threading
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .importer import build_library
from .models import ReviewStatus, library_to_dict
from .progress import apply_progress, load_progress, record_rating, save_progress
from .reviews import CardReview, apply_reviews, load_reviews, save_reviews
from .storage import library_summary, load_library, save_library
from .validation import validate_library

PROJECT_ROOT = Path(os.environ.get("STUDYFORGE_APP_ROOT", Path(__file__).resolve().parents[2]))
DATA_ROOT = PROJECT_ROOT / "data"
LIBRARY_PATH = DATA_ROOT / "library.json"
REVIEWS_PATH = DATA_ROOT / "reviews.json"
PROGRESS_PATH = DATA_ROOT / "progress.json"
ASSET_ROOT = DATA_ROOT / "assets"
DIST_ROOT = PROJECT_ROOT / "dist"
INSTANCE_ID = hashlib.sha1(str(PROJECT_ROOT).encode("utf-8")).hexdigest()[:16]

app = FastAPI(title="Exam Study App API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ASSET_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=ASSET_ROOT), name="assets")
if (DIST_ROOT / "app-assets").exists():
    app.mount("/app-assets", StaticFiles(directory=DIST_ROOT / "app-assets"), name="app-assets")


class ImportRequest(BaseModel):
    source_root: str | None = None
    legacy_root: str | None = None
    include_lectures: bool = False
    max_pages_per_pdf: int | None = None
    copy_legacy_assets: bool = False
    render_pdf_pages: bool = True


class ReviewRequest(BaseModel):
    status: ReviewStatus = "unreviewed"
    front_text: str | None = None
    back_text: str | None = None
    note: str = Field(default="", max_length=2000)


class StudyRequest(BaseModel):
    rating: Literal["easy"]


def require_library():
    if not LIBRARY_PATH.exists():
        raise HTTPException(status_code=404, detail="Library has not been imported yet.")
    library = apply_reviews(load_library(LIBRARY_PATH), load_reviews(REVIEWS_PATH))
    return apply_progress(library, load_progress(PROGRESS_PATH))


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "library_exists": LIBRARY_PATH.exists(),
        "instance_id": INSTANCE_ID,
        "project_root": str(PROJECT_ROOT),
        "data_root": str(DATA_ROOT),
    }


@app.post("/api/shutdown")
def shutdown() -> dict[str, object]:
    def stop_process() -> None:
        os._exit(0)

    threading.Timer(0.25, stop_process).start()
    return {"ok": True}


@app.get("/api/library")
def get_library() -> dict[str, object]:
    library = require_library()
    return library_to_dict(library)


@app.get("/api/summary")
def get_summary() -> dict[str, object]:
    return library_summary(require_library())


@app.get("/api/validation")
def get_validation() -> dict[str, object]:
    report = validate_library(
        require_library(),
        ASSET_ROOT,
        reviews=load_reviews(REVIEWS_PATH),
        progress=load_progress(PROGRESS_PATH),
    )
    return report.to_dict()


@app.post("/api/import")
def rebuild_library(request: ImportRequest) -> dict[str, object]:
    if not request.source_root and not request.legacy_root:
        raise HTTPException(status_code=400, detail="source_root or legacy_root is required.")
    library = build_library(
        source_root=Path(request.source_root) if request.source_root else None,
        legacy_root=Path(request.legacy_root) if request.legacy_root else None,
        asset_root=ASSET_ROOT,
        include_lectures=request.include_lectures,
        max_pages_per_pdf=request.max_pages_per_pdf,
        copy_legacy_assets=request.copy_legacy_assets,
        render_pdf_pages=request.render_pdf_pages,
    )
    save_library(library, LIBRARY_PATH)
    library = apply_reviews(library, load_reviews(REVIEWS_PATH))
    return library_summary(apply_progress(library, load_progress(PROGRESS_PATH)))


@app.patch("/api/cards/{card_id}/review")
def update_card_review(card_id: str, request: ReviewRequest) -> dict[str, object]:
    library = require_library()
    card_ids = {card.id for card in library.cards}
    if card_id not in card_ids:
        raise HTTPException(status_code=404, detail="Card not found.")

    reviews = load_reviews(REVIEWS_PATH)
    reviews[card_id] = CardReview(
        card_id=card_id,
        status=request.status,
        front_text=request.front_text,
        back_text=request.back_text,
        note=request.note,
    )
    save_reviews(REVIEWS_PATH, reviews)
    reviewed_library = require_library()
    reviewed_payload = library_to_dict(reviewed_library)
    reviewed_card = next(card for card in reviewed_payload["cards"] if card["id"] == card_id)
    return {"card": reviewed_card}


@app.patch("/api/cards/{card_id}/study")
def update_card_study(card_id: str, request: StudyRequest) -> dict[str, object]:
    library = require_library()
    card_ids = {card.id for card in library.cards}
    if card_id not in card_ids:
        raise HTTPException(status_code=404, detail="Card not found.")

    progress = load_progress(PROGRESS_PATH)
    record_rating(progress, card_id, request.rating)
    save_progress(PROGRESS_PATH, progress)

    updated_library = require_library()
    updated_payload = library_to_dict(updated_library)
    updated_card = next(card for card in updated_payload["cards"] if card["id"] == card_id)
    return {"card": updated_card, "summary": library_summary(updated_library)}


@app.get("/api/external-asset")
def external_asset(path: str) -> FileResponse:
    target = Path(path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Asset not found.")
    if target.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        raise HTTPException(status_code=400, detail="Unsupported asset type.")
    return FileResponse(target)


@app.get("/")
def app_index() -> FileResponse:
    index_path = DIST_ROOT / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend has not been built yet.")
    return FileResponse(index_path)


@app.get("/{path:path}")
def app_fallback(path: str) -> FileResponse:
    if path.startswith("api/") or path.startswith("assets/"):
        raise HTTPException(status_code=404, detail="Not found.")

    target = (DIST_ROOT / path).resolve()
    dist_root = DIST_ROOT.resolve()
    if (target == dist_root or dist_root in target.parents) and target.is_file():
        return FileResponse(target)
    if path.startswith("app-assets/"):
        raise HTTPException(status_code=404, detail="Not found.")
    return app_index()
