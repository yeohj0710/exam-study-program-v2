from studyforge import studysets as studysets_module
from studyforge.studysets import create_studyset, list_studysets, read_studyset, save_studyset


def test_create_list_read_and_save_studyset_uses_file_name_as_title(tmp_path):
    studysets_root = tmp_path / "문제 데이터"

    created = create_studyset(studysets_root, title="medchem final")

    assert created.id == "medchem-final"
    assert created.title == "medchem-final"
    assert created.slug == "medchem-final"
    assert (studysets_root / "medchem-final.md").exists()

    markdown = "# SAR question\n\n- A\n- B\n\n답: A\n"
    save_studyset(studysets_root, created.id, markdown)

    assert read_studyset(studysets_root, created.id) == markdown
    listed = list_studysets(studysets_root)
    assert [(item.id, item.title, item.question_count) for item in listed] == [
        ("medchem-final", "medchem-final", None)
    ]


def test_list_studysets_uses_file_metadata_without_parsing_markdown(tmp_path, monkeypatch):
    studysets_root = tmp_path / "문제 데이터"
    studysets_root.mkdir()
    (studysets_root / "large-set.md").write_text("# 문제\n\n본문\n\n답: 정답\n", encoding="utf-8")

    def fail_if_parsed(*args, **kwargs):
        raise AssertionError("listing studysets should not parse full Markdown")

    monkeypatch.setattr(studysets_module, "parse_studyset_markdown", fail_if_parsed, raising=False)

    listed = list_studysets(studysets_root)

    assert len(listed) == 1
    assert listed[0].id == "large-set"
    assert listed[0].title == "large-set"
    assert listed[0].question_count is None
    assert listed[0].issue_count is None


def test_read_and_save_preserve_user_facing_korean_file_names(tmp_path):
    studysets_root = tmp_path / "문제 데이터"
    studysets_root.mkdir()
    studyset_id = "의약화학 기말고사"
    markdown = "# 문제\n\n문제 텍스트\n\n답: 정답\n"
    (studysets_root / f"{studyset_id}.md").write_text(markdown, encoding="utf-8")

    assert read_studyset(studysets_root, studyset_id) == markdown

    updated = "# 문제\n\n다음 문제\n\n답: 다음 정답\n"
    save_studyset(studysets_root, studyset_id, updated)

    assert (studysets_root / f"{studyset_id}.md").read_text(encoding="utf-8") == updated
    assert not (studysets_root / "의약화학-기말고사.md").exists()
