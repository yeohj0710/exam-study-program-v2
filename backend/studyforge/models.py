from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import time
from typing import Any, Literal

AssetRole = Literal["front_image", "choice_image", "answer_image", "source_page", "page_crop"]
CardSource = Literal["pdf", "legacy_capture", "manual", "page_fallback"]
ReviewStatus = Literal["unreviewed", "approved", "needs_work"]


@dataclass
class Asset:
    id: str
    role: AssetRole
    path: str
    source_path: str | None = None
    width: int | None = None
    height: int | None = None
    sha1: str | None = None


@dataclass
class SourceDocument:
    id: str
    type: Literal["pdf", "legacy_bank"]
    subject: str
    deck: str
    path: str
    fingerprint: str
    page_count: int | None = None
    imported_at: float = field(default_factory=time)


@dataclass
class StudyCard:
    id: str
    subject: str
    deck: str
    source: CardSource
    source_document_id: str
    source_path: str
    source_page: int | None
    source_item: str | None
    front_text: str
    back_text: str
    raw_text: str
    confidence: float
    review_flags: list[str] = field(default_factory=list)
    review_status: ReviewStatus = "unreviewed"
    review_note: str = ""
    reviewed_at: float | None = None
    assets: list[Asset] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time)
    updated_at: float = field(default_factory=time)


@dataclass
class ImportReport:
    sources_scanned: int = 0
    pdfs_imported: int = 0
    legacy_decks_imported: int = 0
    cards_created: int = 0
    low_confidence_cards: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class Library:
    schema_version: int = 1
    generated_at: float = field(default_factory=time)
    sources: list[SourceDocument] = field(default_factory=list)
    cards: list[StudyCard] = field(default_factory=list)
    report: ImportReport = field(default_factory=ImportReport)


def library_to_dict(library: Library) -> dict[str, Any]:
    return asdict(library)


def library_from_dict(payload: dict[str, Any]) -> Library:
    sources = [SourceDocument(**item) for item in payload.get("sources", [])]
    cards = []
    for item in payload.get("cards", []):
        assets = [Asset(**asset) for asset in item.get("assets", [])]
        item = {**item, "assets": assets}
        cards.append(StudyCard(**item))
    report = ImportReport(**payload.get("report", {}))
    return Library(
        schema_version=payload.get("schema_version", 1),
        generated_at=payload.get("generated_at", time()),
        sources=sources,
        cards=cards,
        report=report,
    )
