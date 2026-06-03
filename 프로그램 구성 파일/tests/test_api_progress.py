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
        front_text="front",
        back_text="back",
        raw_text="raw",
        confidence=1.0,
    )
    save_library(Library(sources=[source], cards=[card], report=ImportReport(cards_created=1)), path)


def test_patch_study_progress_persists_and_updates_library(tmp_path, monkeypatch):
    library_path = tmp_path / "library.json"
    progress_path = tmp_path / "progress.json"
    make_library(library_path)
    monkeypatch.setattr(api, "LIBRARY_PATH", library_path)
    monkeypatch.setattr(api, "REVIEWS_PATH", tmp_path / "reviews.json")
    monkeypatch.setattr(api, "PROGRESS_PATH", progress_path)
    client = TestClient(api.app)

    response = client.patch("/api/cards/card-1/study", json={"rating": "easy"})

    assert response.status_code == 200
    assert progress_path.exists()
    card = response.json()["card"]
    assert card["study_seen_count"] == 1
    assert card["study_correct_count"] == 1
    assert card["study_last_rating"] == "easy"

    library_response = client.get("/api/library")
    assert library_response.status_code == 200
    assert library_response.json()["cards"][0]["study_seen_count"] == 1


def test_delete_study_progress_restores_card_to_new(tmp_path, monkeypatch):
    library_path = tmp_path / "library.json"
    progress_path = tmp_path / "progress.json"
    make_library(library_path)
    monkeypatch.setattr(api, "LIBRARY_PATH", library_path)
    monkeypatch.setattr(api, "REVIEWS_PATH", tmp_path / "reviews.json")
    monkeypatch.setattr(api, "PROGRESS_PATH", progress_path)
    client = TestClient(api.app)

    mark_response = client.patch("/api/cards/card-1/study", json={"rating": "easy"})
    assert mark_response.status_code == 200

    response = client.delete("/api/cards/card-1/study")

    assert response.status_code == 200
    card = response.json()["card"]
    assert card["study_seen_count"] == 0
    assert card["study_correct_count"] == 0
    assert card["study_last_rating"] == "new"

    library_response = client.get("/api/library")
    assert library_response.status_code == 200
    assert library_response.json()["cards"][0]["study_last_rating"] == "new"


def test_patch_study_rejects_new_rating(tmp_path, monkeypatch):
    library_path = tmp_path / "library.json"
    make_library(library_path)
    monkeypatch.setattr(api, "LIBRARY_PATH", library_path)
    monkeypatch.setattr(api, "REVIEWS_PATH", tmp_path / "reviews.json")
    monkeypatch.setattr(api, "PROGRESS_PATH", tmp_path / "progress.json")
    client = TestClient(api.app)

    response = client.patch("/api/cards/card-1/study", json={"rating": "new"})

    assert response.status_code == 422


def test_patch_study_rejects_intermediate_ratings(tmp_path, monkeypatch):
    library_path = tmp_path / "library.json"
    make_library(library_path)
    monkeypatch.setattr(api, "LIBRARY_PATH", library_path)
    monkeypatch.setattr(api, "REVIEWS_PATH", tmp_path / "reviews.json")
    monkeypatch.setattr(api, "PROGRESS_PATH", tmp_path / "progress.json")
    client = TestClient(api.app)

    response = client.patch("/api/cards/card-1/study", json={"rating": "good"})

    assert response.status_code == 422


def test_patch_study_rejects_again_rating(tmp_path, monkeypatch):
    library_path = tmp_path / "library.json"
    make_library(library_path)
    monkeypatch.setattr(api, "LIBRARY_PATH", library_path)
    monkeypatch.setattr(api, "REVIEWS_PATH", tmp_path / "reviews.json")
    monkeypatch.setattr(api, "PROGRESS_PATH", tmp_path / "progress.json")
    client = TestClient(api.app)

    response = client.patch("/api/cards/card-1/study", json={"rating": "again"})

    assert response.status_code == 422
