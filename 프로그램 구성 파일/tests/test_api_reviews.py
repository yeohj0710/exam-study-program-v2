from pathlib import Path

from fastapi.testclient import TestClient

from studyforge import api
from studyforge.models import ImportReport, Library, SourceDocument, StudyCard
from studyforge.storage import save_library


def make_library(path: Path) -> None:
    source = SourceDocument(
        id="source-1",
        type="pdf",
        subject="subject",
        deck="deck",
        path="sample.pdf",
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
        front_text="old front",
        back_text="old back",
        raw_text="raw",
        confidence=0.35,
    )
    save_library(
        Library(sources=[source], cards=[card], report=ImportReport(cards_created=1, low_confidence_cards=1)),
        path,
    )


def test_patch_review_persists_and_library_applies_overlay(tmp_path, monkeypatch):
    library_path = tmp_path / "library.json"
    reviews_path = tmp_path / "reviews.json"
    make_library(library_path)
    monkeypatch.setattr(api, "LIBRARY_PATH", library_path)
    monkeypatch.setattr(api, "REVIEWS_PATH", reviews_path)
    client = TestClient(api.app)

    response = client.patch(
        "/api/cards/card-1/review",
        json={
            "status": "approved",
            "front_text": "new front",
            "back_text": "new back",
            "note": "checked",
        },
    )

    assert response.status_code == 200
    assert reviews_path.exists()
    reviewed_card = response.json()["card"]
    assert reviewed_card["review_status"] == "approved"
    assert reviewed_card["front_text"] == "new front"

    library_response = client.get("/api/library")
    assert library_response.status_code == 200
    library = library_response.json()
    assert library["cards"][0]["back_text"] == "new back"
    assert library["report"]["low_confidence_cards"] == 0
