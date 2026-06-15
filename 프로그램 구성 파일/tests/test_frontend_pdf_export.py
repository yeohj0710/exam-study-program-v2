from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
API_TS = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "api.ts"


def test_frontend_api_exports_studyset_pdf_blob_with_filename():
    source = API_TS.read_text(encoding="utf-8")

    assert "export async function exportStudySetPdf" in source
    assert "`/api/studysets/${encodeURIComponent(studysetId)}/pdf`" in source
    assert "await response.blob()" in source
    assert "content-disposition" in source
    assert "filename" in source


def test_frontend_api_exports_cram_pdf_blob_with_filename():
    source = API_TS.read_text(encoding="utf-8")

    assert "export async function exportStudySetCramPdf" in source
    assert "`/api/studysets/${encodeURIComponent(studysetId)}/cram-pdf`" in source
    assert "5분문답.pdf" in source
    assert "await response.blob()" in source
