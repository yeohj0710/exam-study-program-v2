from base64 import b64encode
import threading
import time

from fastapi.testclient import TestClient

from studyforge import api, final_api
from studyforge.final_progress import load_final_progress


def test_studyset_api_creates_saves_and_returns_simple_questions(tmp_path, monkeypatch):
    monkeypatch.setattr(final_api, "DATA_ROOT", tmp_path / "문제 데이터")
    monkeypatch.setattr(final_api, "STUDYSETS_ROOT", tmp_path / "문제 데이터")
    monkeypatch.setattr(final_api, "ASSET_ROOT", tmp_path / "문제 데이터" / "assets")
    monkeypatch.setattr(final_api, "FINAL_PROGRESS_PATH", tmp_path / "문제 데이터" / "progress.json")
    client = TestClient(api.app)

    create_response = client.post("/api/studysets", json={"title": "medchem final"})

    assert create_response.status_code == 200
    studyset_id = create_response.json()["id"]
    assert studyset_id == "medchem-final"

    markdown = """# SAR question
<!-- sf:id: medchem-final-001 -->

- choice A
- choice B

답: choice A
"""
    save_response = client.put(f"/api/studysets/{studyset_id}", json={"markdown": markdown})

    assert save_response.status_code == 200
    assert save_response.json()["title"] == "medchem-final"
    assert save_response.json()["questions"][0]["id"] == "medchem-final-001"

    questions_response = client.get(f"/api/studysets/{studyset_id}/questions")

    assert questions_response.status_code == 200
    question = questions_response.json()["questions"][0]
    assert question["title"] == "Question 1"
    assert question["prompt_markdown"].startswith("SAR question")
    assert question["answer_markdown"] == "choice A"
    assert question["progress"]["memorized"] is False


def test_studyset_api_saves_markdown_without_inserting_hidden_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(final_api, "STUDYSETS_ROOT", tmp_path / "문제 데이터")
    monkeypatch.setattr(final_api, "ASSET_ROOT", tmp_path / "문제 데이터" / "assets")
    monkeypatch.setattr(final_api, "FINAL_PROGRESS_PATH", tmp_path / "문제 데이터" / "progress.json")
    client = TestClient(api.app)
    client.post("/api/studysets", json={"title": "medchem final"})
    markdown = "# 문제\n\n문제 텍스트\n\n답: 정답\n"

    response = client.put("/api/studysets/medchem-final", json={"markdown": markdown})

    assert response.status_code == 200
    assert response.json()["markdown"] == markdown
    assert "<!-- sf:id:" not in (tmp_path / "문제 데이터" / "medchem-final.md").read_text(encoding="utf-8")


def test_question_progress_api_writes_final_progress_only(tmp_path, monkeypatch):
    final_progress_path = tmp_path / "문제 데이터" / "progress.json"
    legacy_progress_path = tmp_path / "progress.json"
    monkeypatch.setattr(final_api, "STUDYSETS_ROOT", tmp_path / "문제 데이터")
    monkeypatch.setattr(final_api, "ASSET_ROOT", tmp_path / "문제 데이터" / "assets")
    monkeypatch.setattr(final_api, "FINAL_PROGRESS_PATH", final_progress_path)
    monkeypatch.setattr(api, "PROGRESS_PATH", legacy_progress_path)
    client = TestClient(api.app)

    seen_response = client.patch("/api/questions/medchem-final-001/progress", json={"action": "seen"})
    reveal_response = client.patch("/api/questions/medchem-final-001/progress", json={"action": "reveal"})
    memorize_response = client.patch("/api/questions/medchem-final-001/progress", json={"action": "memorized"})

    assert seen_response.status_code == 200
    assert reveal_response.status_code == 200
    assert memorize_response.status_code == 200
    assert final_progress_path.exists()
    assert not legacy_progress_path.exists()
    progress = load_final_progress(final_progress_path)
    assert progress["medchem-final-001"].seen_count == 1
    assert progress["medchem-final-001"].reveal_count == 1
    assert progress["medchem-final-001"].memorized is True

    restore_response = client.delete("/api/questions/medchem-final-001/progress")

    assert restore_response.status_code == 200
    assert restore_response.json()["progress"]["memorized"] is False


def test_question_progress_updates_are_serialized_when_requests_overlap(tmp_path, monkeypatch):
    progress_path = tmp_path / "progress.json"
    monkeypatch.setattr(final_api, "FINAL_PROGRESS_PATH", progress_path)
    original_save = final_api.save_final_progress
    seen_waiting = threading.Event()
    release_seen = threading.Event()
    errors: list[BaseException] = []

    def delayed_save(path, progress):
        entry = progress.get("question-1")
        if entry and entry.seen_count == 1 and not entry.memorized:
            seen_waiting.set()
            if not release_seen.wait(2):
                raise AssertionError("timed out waiting to release seen save")
        original_save(path, progress)

    def call_seen():
        try:
            final_api.patch_question_progress("question-1", final_api.QuestionProgressRequest(action="seen"))
        except BaseException as exc:
            errors.append(exc)

    def call_memorized():
        try:
            final_api.patch_question_progress("question-1", final_api.QuestionProgressRequest(action="memorized"))
        except BaseException as exc:
            errors.append(exc)

    monkeypatch.setattr(final_api, "save_final_progress", delayed_save)
    seen_thread = threading.Thread(target=call_seen)
    seen_thread.start()
    assert seen_waiting.wait(2)

    memorized_thread = threading.Thread(target=call_memorized)
    memorized_thread.start()
    time.sleep(0.2)
    release_seen.set()
    seen_thread.join(2)
    memorized_thread.join(2)

    assert not seen_thread.is_alive()
    assert not memorized_thread.is_alive()
    assert not errors
    assert load_final_progress(progress_path)["question-1"].memorized is True


def test_studyset_asset_api_stores_base64_image_and_returns_markdown_link(tmp_path, monkeypatch):
    monkeypatch.setattr(final_api, "STUDYSETS_ROOT", tmp_path / "문제 데이터")
    monkeypatch.setattr(final_api, "ASSET_ROOT", tmp_path / "문제 데이터" / "assets")
    monkeypatch.setattr(final_api, "FINAL_PROGRESS_PATH", tmp_path / "문제 데이터" / "progress.json")
    client = TestClient(api.app)
    client.post("/api/studysets", json={"title": "medchem final"})
    content = b"image-bytes"

    response = client.post(
        "/api/studysets/medchem-final/assets",
        json={
            "content_base64": b64encode(content).decode("ascii"),
            "content_type": "image/png",
            "alt_text": "diagram",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["relative_path"].startswith("assets/medchem-final/img-")
    assert payload["markdown"].startswith("![diagram](assets/medchem-final/img-")
    stored_path = tmp_path / "문제 데이터" / payload["relative_path"]
    assert stored_path.read_bytes() == content


def test_validation_endpoint_includes_final_studysets_without_legacy_library(tmp_path, monkeypatch):
    studysets_root = tmp_path / "문제 데이터"
    studysets_root.mkdir()
    (studysets_root / "medchem-final.md").write_text(
        "# No answer\n<!-- sf:id: no-answer -->\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(api, "LIBRARY_PATH", tmp_path / "missing-library.json")
    monkeypatch.setattr(api, "REVIEWS_PATH", tmp_path / "reviews.json")
    monkeypatch.setattr(api, "PROGRESS_PATH", tmp_path / "progress.json")
    monkeypatch.setattr(api, "LEGACY_ASSET_ROOT", tmp_path / "legacy-assets")
    monkeypatch.setattr(api, "ASSET_ROOT", tmp_path / "문제 데이터" / "assets")
    monkeypatch.setattr(final_api, "STUDYSETS_ROOT", studysets_root)
    monkeypatch.setattr(final_api, "ASSET_ROOT", tmp_path / "문제 데이터" / "assets")
    monkeypatch.setattr(final_api, "FINAL_PROGRESS_PATH", tmp_path / "문제 데이터" / "progress.json")
    client = TestClient(api.app)

    response = client.get("/api/validation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["card_count"] == 0
    assert payload["final"]["studyset_count"] == 1
    assert payload["final"]["question_count"] == 1
    assert payload["final"]["issues"][0]["code"] == "missing_answer"


def test_source_open_endpoint_opens_pdf_at_page(tmp_path, monkeypatch):
    source = tmp_path / "예방약학.pdf"
    source.write_bytes(b"%PDF-1.4\n")
    opened: list[str] = []
    monkeypatch.setattr(final_api.webbrowser, "open", lambda url: opened.append(url) or True)
    client = TestClient(api.app)

    response = client.post("/api/source/open", json={"reference": f"{source} p.12"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["path"] == str(source)
    assert payload["page"] == 12
    assert opened == [f"{source.as_uri()}#page=12"]


def test_source_resolve_endpoint_returns_browser_file_url(tmp_path):
    source = tmp_path / "예방약학.pdf"
    content = b"%PDF-1.4\nsource"
    source.write_bytes(content)
    client = TestClient(api.app)

    resolve_response = client.post("/api/source/resolve", json={"reference": f"{source} p.12"})

    assert resolve_response.status_code == 200
    payload = resolve_response.json()
    assert payload["path"] == str(source)
    assert payload["page"] == 12
    assert payload["url"].startswith("/api/source/file?path=")
    assert payload["url"].endswith("#page=12")

    file_url = payload["url"].split("#", 1)[0]
    file_response = client.get(file_url)

    assert file_response.status_code == 200
    assert file_response.content == content
