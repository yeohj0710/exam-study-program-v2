from pathlib import Path

from studyforge.sources import discover_midterm_pdfs, infer_subject_from_pdf, should_import_midterm_pdf


def test_discover_midterm_pdfs_keeps_target_folder_scope(tmp_path):
    root = tmp_path / "21 6-1"
    target = root / "바이오공정개론" / "중간고사 정리자료" / "바이오공정개론 중간고사 범위 정리.pdf"
    summary = root / "바이오의약품학" / "중간고사 정리자료" / "5. 중간고사 요약 자료.pdf"
    lecture = root / "백신공정이론" / "중간고사 범위 수업자료" / "백신공정이론 중간고사 범위 정리.pdf"
    senior = root / "바이오공정개론" / "선배 자료" / "중간고사 정리_아영.pdf"
    grade = root / "예방약학" / "중간고사 정리자료" / "예방약학 중간고사 성적.pdf"
    for path in [target, summary, lecture, senior, grade]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"%PDF-1.4\n")

    discovered = [path.relative_to(root) for path in discover_midterm_pdfs(root)]

    assert discovered == [
        Path("바이오공정개론/중간고사 정리자료/바이오공정개론 중간고사 범위 정리.pdf"),
        Path("바이오의약품학/중간고사 정리자료/5. 중간고사 요약 자료.pdf"),
    ]


def test_import_predicate_can_include_lecture_materials():
    lecture = Path("백신공정이론/중간고사 범위 수업자료/백신공정이론 중간고사 범위 정리.pdf")

    assert should_import_midterm_pdf(lecture) is False
    assert should_import_midterm_pdf(lecture, include_lectures=True) is True


def test_discover_midterm_pdfs_falls_back_to_plain_pdf_folder(tmp_path):
    source_root = tmp_path / "PDF 넣는 곳"
    target = source_root / "백신공정이론 중간고사.pdf"
    grade = source_root / "백신공정이론 중간고사 성적.pdf"
    nested = source_root / "추가자료" / "예방약학 예상문제.pdf"
    for path in [target, grade, nested]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"%PDF-1.4\n")

    discovered = [path.relative_to(source_root) for path in discover_midterm_pdfs(source_root)]

    assert discovered == [
        Path("백신공정이론 중간고사.pdf"),
        Path("추가자료/예방약학 예상문제.pdf"),
    ]


def test_infer_subject_from_midterm_folder():
    pdf = Path("G:/내 드라이브/여형준님/21 6-1/의약화학/중간고사 정리자료/의약화학 중간고사 범위 정리.pdf")

    assert infer_subject_from_pdf(pdf) == "의약화학"


def test_infer_subject_from_plain_pdf_folder():
    pdf = Path("G:/자료/PDF 넣는 곳/백신공정이론 중간고사.pdf")

    assert infer_subject_from_pdf(pdf) == "PDF 넣는 곳"
