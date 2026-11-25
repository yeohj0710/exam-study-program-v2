from base64 import b64encode
import json
import threading
import time
from urllib.parse import unquote

from fastapi.testclient import TestClient
import fitz
import pytest

from studyforge import api, final_api
from studyforge.final_progress import load_final_progress


@pytest.mark.parametrize("path", ["/", "/index.html", "/study/reopen"])
def test_app_html_does_not_cache_old_bundle_references(path, tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text('<script src="/app-assets/index-current.js"></script>', encoding="utf-8")
    monkeypatch.setattr(api, "DIST_ROOT", tmp_path)

    response = TestClient(api.app).get(path)

    assert response.status_code == 200
    assert "index-current.js" in response.text
    assert response.headers.get("cache-control") == "no-store"


@pytest.fixture
def rename_studysets(tmp_path, monkeypatch):
    root = tmp_path / "문제 데이터"
    root.mkdir()
    monkeypatch.setattr(final_api, "STUDYSETS_ROOT", root)
    monkeypatch.setattr(final_api, "ASSET_ROOT", root / "assets")
    monkeypatch.setattr(final_api, "FINAL_PROGRESS_PATH", root / "progress.json")
    return root, TestClient(api.app)


def test_rename_studyset_keeps_markdown_assets_and_progress(rename_studysets):
    root, client = rename_studysets
    image = root / "assets" / "old-set" / "card.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"image bytes")
    markdown = "# Legacy question\r\n![card](assets/old-set/card.png)\r\n답: A\r\n# Tagged question\r\n<!-- sf:id: stable-id -->\r\n답: B\r\n"
    (root / "old-set.md").write_bytes(markdown.encode())
    (root / "related-set.md").write_text("# Shared image\n![card](assets/old-set/card.png)\n답: B\n", encoding="utf-8")
    for question_id in ("old-set-001", "stable-id"):
        assert client.patch(f"/api/questions/{question_id}/progress", json={"action": "memorized"}).is_success
    progress = (root / "progress.json").read_bytes()

    response = client.patch("/api/studysets/old-set", json={"title": "새 세트 이름"})

    assert response.status_code == 200
    assert response.json()["title"] == "새 세트 이름"
    assert not (root / "old-set.md").exists()
    assert (root / "새 세트 이름.md").read_bytes() == markdown.encode()
    assert not response.json()["issues"]
    assert image.read_bytes() == b"image bytes"
    assert not client.get("/api/studysets/related-set").json()["issues"]
    assert client.get("/api/studysets/old-set").status_code == 404
    assert client.put("/api/studysets/old-set", json={"markdown": "stale edit"}).status_code == 404
    for path in ("/api/studysets/새 세트 이름", "/api/studysets/새 세트 이름/questions"):
        questions = client.get(path).json()["questions"]
        assert [item["id"] for item in questions] == ["old-set-001", "stable-id"]
        assert all(item["progress"]["memorized"] for item in questions)
        assert all(item["studyset_id"] == "새 세트 이름" for item in questions)
    assert (root / "progress.json").read_bytes() == progress
    assert client.patch("/api/studysets/새 세트 이름", json={"title": "old-set"}).is_success
    assert (root / "old-set.md").read_bytes() == markdown.encode()


def test_rename_rejects_invalid_existing_names_and_missing_source(rename_studysets):
    root, client = rename_studysets
    (root / "old.md").write_text("old", encoding="utf-8")
    (root / "existing.md").write_text("existing", encoding="utf-8")
    for title in ("", "  ", "a/b", "a\\b", "..", "a.", "NUL", "test\x00line"):
        assert client.patch("/api/studysets/old", json={"title": title}).status_code == 400
    assert client.patch("/api/studysets/old", json={"title": "existing"}).status_code == 409
    assert client.patch("/api/studysets/missing", json={"title": "new"}).status_code == 404
    assert {name.name: name.read_text(encoding="utf-8") for name in root.iterdir()} == {
        "old.md": "old",
        "existing.md": "existing",
    }


def test_reusing_a_renamed_filename_does_not_share_fallback_progress(rename_studysets):
    root, client = rename_studysets
    markdown = "# Problem\n답: A\n"
    (root / "first.md").write_text(markdown, encoding="utf-8")
    assert client.patch("/api/questions/first-001/progress", json={"action": "memorized"}).is_success
    assert client.patch("/api/studysets/first", json={"title": "second"}).is_success

    (root / "first.md").write_text(markdown, encoding="utf-8")
    first = client.get("/api/studysets/first").json()["questions"][0]
    assert first["id"] != "first-001"
    assert not first["progress"]["memorized"]
    assert client.get("/api/studysets/first").json()["questions"][0]["id"] == first["id"]
    assert client.get("/api/studysets/second").json()["questions"][0]["progress"]["memorized"]


@pytest.mark.parametrize("already_renamed", [False, True])
def test_rename_recovers_after_interruption_on_either_side_of_file_move(rename_studysets, already_renamed):
    root, client = rename_studysets
    manifest = root / ".studyset-namespaces.json"
    manifest.write_text(json.dumps({
        "names": {"current": "original"},
        "pending": {"source": "current", "target": "new", "namespace": "original"},
    }), encoding="utf-8")
    visible_name = "new" if already_renamed else "current"
    (root / f"{visible_name}.md").write_text("# Problem\n답: A\n", encoding="utf-8")

    response = client.get(f"/api/studysets/{visible_name}")

    assert response.json()["questions"][0]["id"] == "original-001"
    assert json.loads(manifest.read_text(encoding="utf-8")) == {"names": {visible_name: "original"}, "pending": None}


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


def test_validation_endpoint_can_scope_final_report_to_selected_studyset(tmp_path, monkeypatch):
    studysets_root = tmp_path / "문제 데이터"
    studysets_root.mkdir()
    (studysets_root / "selected.md").write_text(
        "# Question\n\nPrompt\n\n답: Answer\n",
        encoding="utf-8",
    )
    (studysets_root / "unselected.md").write_text(
        "# No answer\n<!-- sf:id: no-answer -->\n",
        encoding="utf-8",
    )
    original_parse = final_api.parse_studyset_markdown

    def parse_selected_only(markdown, *, studyset_id, asset_root, question_id_prefix=None):
        if studyset_id == "unselected":
            raise AssertionError("selected validation should not parse unselected studysets")
        return original_parse(markdown, studyset_id=studyset_id, asset_root=asset_root, question_id_prefix=question_id_prefix)

    monkeypatch.setattr(api, "LIBRARY_PATH", tmp_path / "missing-library.json")
    monkeypatch.setattr(api, "REVIEWS_PATH", tmp_path / "reviews.json")
    monkeypatch.setattr(api, "PROGRESS_PATH", tmp_path / "progress.json")
    monkeypatch.setattr(api, "LEGACY_ASSET_ROOT", tmp_path / "legacy-assets")
    monkeypatch.setattr(api, "ASSET_ROOT", studysets_root / "assets")
    monkeypatch.setattr(final_api, "STUDYSETS_ROOT", studysets_root)
    monkeypatch.setattr(final_api, "ASSET_ROOT", studysets_root / "assets")
    monkeypatch.setattr(final_api, "FINAL_PROGRESS_PATH", studysets_root / "progress.json")
    monkeypatch.setattr(final_api, "parse_studyset_markdown", parse_selected_only)
    client = TestClient(api.app)

    response = client.get("/api/validation?studyset_id=selected")

    assert response.status_code == 200
    payload = response.json()
    assert payload["final"]["studyset_count"] == 1
    assert payload["final"]["question_count"] == 1
    assert payload["final"]["issues"] == []


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


def test_studyset_pdf_endpoint_returns_clean_downloadable_pdf(tmp_path, monkeypatch):
    studysets_root = tmp_path / "문제 데이터"
    monkeypatch.setattr(final_api, "DATA_ROOT", studysets_root)
    monkeypatch.setattr(final_api, "STUDYSETS_ROOT", studysets_root)
    monkeypatch.setattr(final_api, "ASSET_ROOT", studysets_root / "assets")
    monkeypatch.setattr(final_api, "FINAL_PROGRESS_PATH", studysets_root / "progress.json")
    client = TestClient(api.app)
    client.post("/api/studysets", json={"title": "medchem final"})
    markdown = """# 문제

다음 중 **정답**을 고르시오.

- 보기 A
- 보기 B

답: ==보기 A==
출처: 강의자료.pdf p.3
"""
    client.put("/api/studysets/medchem-final", json={"markdown": markdown})

    response = client.get("/api/studysets/medchem-final/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert "medchem-final_문답.pdf" in unquote(response.headers["content-disposition"])
    assert response.content.startswith(b"%PDF")
    document = fitz.open(stream=response.content, filetype="pdf")
    text = "\n".join(page.get_text() for page in document)
    assert "medchem-final" in text
    assert "Q1" in text
    assert "다음 중 정답을 고르시오." in text
    assert "보기 A" in text
    assert "출처: 강의자료.pdf p.3" in text
    assert "**" not in text
    assert "==" not in text


def test_studyset_cram_pdf_endpoint_returns_last_minute_pdf(tmp_path, monkeypatch):
    studysets_root = tmp_path / "문제 데이터"
    monkeypatch.setattr(final_api, "DATA_ROOT", studysets_root)
    monkeypatch.setattr(final_api, "STUDYSETS_ROOT", studysets_root)
    monkeypatch.setattr(final_api, "ASSET_ROOT", studysets_root / "assets")
    monkeypatch.setattr(final_api, "FINAL_PROGRESS_PATH", studysets_root / "progress.json")
    client = TestClient(api.app)
    client.post("/api/studysets", json={"title": "pharmacy final"})
    markdown = """# 문제

건강기능식품 원료 연결로 옳은 것을 모두 고르시오.

- 코엔자임Q10은 항산화와 항고혈압에 연결된다.
- 밀크씨슬은 전립선 건강에 연결된다.

답: 아래 표시 보기
O 코엔자임Q10은 항산화와 항고혈압에 연결된다. // CoQ10은 isoprenoid 계열이다.
X 밀크씨슬은 전립선 건강에 연결된다. -> 밀크씨슬은 간 건강 개선과 연결된다.
출처: 강의자료.pdf p.405
"""
    client.put("/api/studysets/pharmacy-final", json={"markdown": markdown})

    response = client.get("/api/studysets/pharmacy-final/cram-pdf")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert "pharmacy-final_5분문답.pdf" in unquote(response.headers["content-disposition"])
    assert response.content.startswith(b"%PDF")
    document = fitz.open(stream=response.content, filetype="pdf")
    text = "\n".join(page.get_text() for page in document)
    assert "pharmacy-final" in text
    assert "Q1." in text
    assert "건강기능식품 원료 연결로 옳은 것을 모두 고르시오." in text
    assert "코엔자임Q10은 항산화와 항고혈압에 연결된다." in text
    assert "밀크씨슬은 전립선 건강" not in text
    assert "출처" not in text
    assert "강의자료.pdf" not in text
