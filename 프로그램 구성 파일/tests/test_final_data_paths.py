from studyforge.final_api import resolve_data_root


def test_default_problem_data_root_is_repo_root_problem_data_folder(tmp_path):
    app_root = tmp_path / "프로그램 구성 파일"
    app_root.mkdir()

    assert resolve_data_root(app_root) == tmp_path / "문제 데이터"


def test_env_can_override_problem_data_root(tmp_path, monkeypatch):
    app_root = tmp_path / "프로그램 구성 파일"
    override = tmp_path / "custom-data"
    monkeypatch.setenv("EXAM_STUDY_DATA_ROOT", str(override))

    assert resolve_data_root(app_root) == override
