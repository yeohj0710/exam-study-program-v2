from pathlib import Path

from PIL import Image
from fastapi.testclient import TestClient

from studyforge import api
from studyforge.models import Asset, ImportReport, Library, SourceDocument, StudyCard
from studyforge.storage import save_library


def make_library(tmp_path: Path) -> tuple[Path, Path]:
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")
    asset_root = tmp_path / "assets"
    asset_root.mkdir()
    Image.new("RGB", (20, 10), "white").save(asset_root / "front.png")
    Image.new("RGB", (20, 10), "white").save(asset_root / "crop.png")
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
    library_path = tmp_path / "library.json"
    save_library(Library(sources=[source], cards=[card], report=ImportReport(cards_created=1)), library_path)
    return library_path, asset_root


def test_validation_endpoint_returns_report(tmp_path, monkeypatch):
    library_path, asset_root = make_library(tmp_path)
    monkeypatch.setattr(api, "LIBRARY_PATH", library_path)
    monkeypatch.setattr(api, "REVIEWS_PATH", tmp_path / "reviews.json")
    monkeypatch.setattr(api, "PROGRESS_PATH", tmp_path / "progress.json")
    monkeypatch.setattr(api, "LEGACY_ASSET_ROOT", asset_root)
    client = TestClient(api.app)

    response = client.get("/api/validation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["missing_asset_count"] == 0
    assert payload["card_count"] == 1


def test_import_endpoint_does_not_auto_scan_pdf_folder(tmp_path, monkeypatch):
    library_path = tmp_path / "library.json"
    asset_root = tmp_path / "assets"
    pdf_root = tmp_path / "pdfs"
    pdf_root.mkdir()
    (pdf_root / "ignored.pdf").write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(api, "LIBRARY_PATH", library_path)
    monkeypatch.setattr(api, "REVIEWS_PATH", tmp_path / "reviews.json")
    monkeypatch.setattr(api, "PROGRESS_PATH", tmp_path / "progress.json")
    monkeypatch.setattr(api, "LEGACY_ASSET_ROOT", asset_root)
    client = TestClient(api.app)

    response = client.post("/api/import", json={"source_root": str(pdf_root)})

    assert response.status_code == 400
    assert not library_path.exists()
