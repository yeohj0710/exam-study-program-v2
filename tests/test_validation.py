from pathlib import Path

from PIL import Image

from studyforge.models import Asset, ImportReport, Library, SourceDocument, StudyCard
from studyforge.progress import CardProgress
from studyforge.reviews import CardReview
from studyforge.validation import resolve_asset_path, validate_library


def write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (20, 10), "white").save(path)


def make_library(tmp_path: Path) -> tuple[Library, Path]:
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")
    asset_root = tmp_path / "assets"
    front = asset_root / "front.png"
    crop = asset_root / "crop.png"
    write_png(front)
    write_png(crop)
    source = SourceDocument(
        id="source-1",
        type="pdf",
        subject="subject",
        deck="deck",
        path=str(source_path),
        fingerprint="fingerprint",
    )
    card = StudyCard(
        id="card-1",
        subject="subject",
        deck="deck",
        source="pdf",
        source_document_id=source.id,
        source_path=source.path,
        source_page=1,
        source_item="1",
        front_text="front",
        back_text="back",
        raw_text="raw",
        confidence=1.0,
        assets=[
            Asset(id="front", role="front_image", path="front.png"),
            Asset(id="crop", role="page_crop", path="crop.png"),
        ],
    )
    return Library(sources=[source], cards=[card], report=ImportReport(cards_created=1)), asset_root


def test_validate_ok_library(tmp_path):
    library, asset_root = make_library(tmp_path)

    report = validate_library(library, asset_root)

    assert report.ok is True
    assert report.card_count == 1
    assert report.asset_count == 2
    assert report.issues == []


def test_validate_missing_asset(tmp_path):
    library, asset_root = make_library(tmp_path)
    library.cards[0].assets[0].path = "missing.png"

    report = validate_library(library, asset_root)

    assert report.ok is False
    assert report.missing_asset_count == 1
    assert report.issues[0].code == "missing_asset"


def test_validate_orphan_overlays_are_warnings(tmp_path):
    library, asset_root = make_library(tmp_path)

    report = validate_library(
        library,
        asset_root,
        reviews={"old-card": CardReview(card_id="old-card")},
        progress={"old-card": CardProgress(card_id="old-card")},
    )

    assert report.ok is True
    assert report.orphan_review_count == 1
    assert report.orphan_progress_count == 1
    assert {issue.severity for issue in report.issues} == {"warning"}


def test_resolve_asset_path_preserves_drive_paths(tmp_path):
    resolved = resolve_asset_path("G:\\내 드라이브\\capture.png", tmp_path / "assets")

    assert str(resolved) == "G:\\내 드라이브\\capture.png"
