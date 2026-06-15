from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_LAUNCHERS = PROJECT_ROOT / "프로그램 구성 파일" / "scripts" / "build_windows_launchers.ps1"
BOOTSTRAP_SOURCE = PROJECT_ROOT / "프로그램 구성 파일" / "launcher" / "StudyForgeBootstrap.cs"


def test_windows_launcher_bundles_reportlab_for_pdf_export_imports():
    script = BUILD_LAUNCHERS.read_text(encoding="utf-8")

    assert '--collect-submodules "reportlab"' in script
    assert '--collect-data "reportlab"' in script


def test_windows_launcher_builds_core_in_temp_dist_before_replacing_existing_exe():
    script = BUILD_LAUNCHERS.read_text(encoding="utf-8")

    assert "$CoreBuildDistDir" in script
    assert "--distpath $CoreBuildDistDir" in script
    assert "$BuiltCoreExe = Join-Path $CoreBuildDistDir \"ExamStudyCore.exe\"" in script
    assert "Copy-Item -LiteralPath $BuiltCoreExe -Destination $CoreExe -Force" in script
    assert "Remove-Item -LiteralPath $CoreExe -Force" not in script


def test_bootstrap_waits_for_core_exe_during_distribution_update():
    source = BOOTSTRAP_SOURCE.read_text(encoding="utf-8")

    assert "await WaitForFileAsync(coreExe" in source
    assert "\\uc2e4\\ud589 \\ud30c\\uc77c\\uc744 \\uc900\\ube44\\ud558\\uace0 \\uc788\\uc2b5\\ub2c8\\ub2e4." in source
    assert "File.Exists(coreExe)" in source
