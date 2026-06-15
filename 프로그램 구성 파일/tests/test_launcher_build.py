from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_LAUNCHERS = PROJECT_ROOT / "프로그램 구성 파일" / "scripts" / "build_windows_launchers.ps1"


def test_windows_launcher_bundles_reportlab_for_pdf_export_imports():
    script = BUILD_LAUNCHERS.read_text(encoding="utf-8")

    assert '--collect-submodules "reportlab"' in script
    assert '--collect-data "reportlab"' in script
