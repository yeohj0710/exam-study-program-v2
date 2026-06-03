from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .importer import build_library
from .models import ReviewStatus, library_to_dict
from .reviews import CardReview, apply_reviews, load_reviews, save_reviews
from .storage import library_summary, load_library, save_library

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"
LIBRARY_PATH = DATA_ROOT / "library.json"
REVIEWS_PATH = DATA_ROOT / "reviews.json"
ASSET_ROOT = DATA_ROOT / "assets"

app = FastAPI(title="StudyForge API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ASSET_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=ASSET_ROOT), name="assets")


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


def require_library():
    if not LIBRARY_PATH.exists():
        raise HTTPException(status_code=404, detail="Library has not been imported yet.")
    return apply_reviews(load_library(LIBRARY_PATH), load_reviews(REVIEWS_PATH))


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"ok": True, "library_exists": LIBRARY_PATH.exists()}


@app.get("/api/library")
def get_library() -> dict[str, object]:
    library = require_library()
    return library_to_dict(library)


@app.get("/api/summary")
def get_summary() -> dict[str, object]:
    return library_summary(require_library())


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
    return library_summary(apply_reviews(library, load_reviews(REVIEWS_PATH)))


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


@app.get("/api/external-asset")
def external_asset(path: str) -> FileResponse:
    target = Path(path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Asset not found.")
    if target.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        raise HTTPException(status_code=400, detail="Unsupported asset type.")
    return FileResponse(target)
