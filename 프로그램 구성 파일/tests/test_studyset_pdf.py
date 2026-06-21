from pathlib import Path

import fitz
from PIL import Image

from studyforge.final_models import Question
from studyforge.studyset_pdf import export_cram_studyset_pdf, export_studyset_pdf


def test_export_studyset_pdf_renders_clean_mobile_qa_without_markdown_tokens(tmp_path):
    image_path = tmp_path / "assets" / "sample-set" / "source-001.png"
    image_path.parent.mkdir(parents=True)
    Image.new("RGB", (280, 120), color=(240, 240, 240)).save(image_path)
    output_path = tmp_path / "exports" / "sample-set.pdf"
    questions = [
        Question(
            id="sample-set-001",
            studyset_id="sample-set",
            ordinal=1,
            title="Question 1",
            prompt_markdown=(
                "Vitamin B6와 PLP에 관한 설명으로 옳은 것을 모두 고르시오.\n\n"
                "- PLP는 **아미노기 전이**에 관여한다.\n"
                "- PLP는 cysteine 합성과 무관하다."
            ),
            answer_markdown="PLP는 ==아미노기 전이==에 관여한다.",
            source_markdown=(
                r"출처: G:\내 드라이브\예방약학\예방약학 수업자료.pdf p.12"
                "\n![출처](assets/sample-set/source-001.png)"
            ),
        )
    ]

    written_path = export_studyset_pdf(
        studyset_id="sample-set",
        questions=questions,
        output_path=output_path,
        asset_root=tmp_path,
    )

    assert written_path == output_path
    assert output_path.read_bytes().startswith(b"%PDF")
    document = fitz.open(output_path)
    text = "\n".join(page.get_text() for page in document)
    assert "sample-set" in text
    assert "Q1" in text
    assert "Vitamin B6와 PLP" in text
    assert "아미노기 전이" in text
    assert "답" in text
    assert "출처: 예방약학 수업자료.pdf p.12" in text
    assert "G:" not in text
    assert "**" not in text
    assert "==" not in text
    assert "![출처]" not in text
    assert document[0].get_images()


def test_export_studyset_pdf_rejects_empty_question_sets(tmp_path):
    output_path = tmp_path / "empty.pdf"

    try:
        export_studyset_pdf(
            studyset_id="empty",
            questions=[],
            output_path=output_path,
            asset_root=tmp_path,
        )
    except ValueError as exc:
        assert "questions" in str(exc)
    else:
        raise AssertionError("empty PDF export should fail")


def test_export_studyset_pdf_puts_explicit_choice_explanations_before_background_without_duplicate_answer(tmp_path):
    output_path = tmp_path / "exports" / "choice-explanation.pdf"
    questions = [
        Question(
            id="sample-set-001",
            studyset_id="sample-set",
            ordinal=1,
            title="Question 1",
            prompt_markdown=(
                "연결로 옳지 않은 것은?\n\n"
                "- 보기 A\n"
                "- 보기 B\n"
                "- 보기 C"
            ),
            answer_markdown="DO NOT PRINT DIRECT ANSWER",
            explanation_markdown="전체 배경 설명은 보기별 판단 뒤에 온다.",
            choice_explanation_markdown=(
                "O 보기 A // 맞는 연결이다.\n"
                "X 보기 B -> 틀린 연결이다.\n"
                "O 보기 C // 맞는 연결이다."
            ),
            source_markdown="출처: 강의자료.pdf p.1",
        )
    ]

    export_studyset_pdf(
        studyset_id="sample-set",
        questions=questions,
        output_path=output_path,
        asset_root=tmp_path,
    )

    document = fitz.open(output_path)
    text = "\n".join(page.get_text() for page in document)

    assert "보기 해설" in text
    assert "해설" in text
    assert text.index("보기 해설") < text.index("해설")
    assert "DO NOT PRINT DIRECT ANSWER" not in text


def test_export_cram_studyset_pdf_keeps_only_last_minute_question_answer(tmp_path):
    output_path = tmp_path / "exports" / "cram.pdf"
    questions = [
        Question(
            id="sample-set-001",
            studyset_id="sample-set",
            ordinal=1,
            title="Question 1",
            prompt_markdown=(
                "건강기능식품 원료 연결로 옳은 것을 모두 고르시오.\n\n"
                "- 코엔자임Q10은 항산화와 항고혈압에 연결된다.\n"
                "- 밀크씨슬은 전립선 건강에 연결된다.\n"
                "![출처](assets/sample/source.png)"
            ),
            answer_markdown=(
                "아래 표시 보기\n"
                "O 코엔자임Q10은 항산화와 항고혈압에 연결된다. // CoQ10은 isoprenoid 계열이다.\n"
                "X 밀크씨슬은 전립선 건강에 연결된다. -> 밀크씨슬은 간 건강 개선과 연결된다.\n"
                "해설: 긴 설명은 5분 PDF에 필요 없다."
            ),
            source_markdown="출처: 강의자료.pdf p.405\n![출처](assets/sample/source.png)",
        ),
        Question(
            id="sample-set-002",
            studyset_id="sample-set",
            ordinal=2,
            title="Question 2",
            prompt_markdown="가르시니아의 기능성분은?",
            answer_markdown="hydroxycitric acid, HCA\n해설: 껍질에 약 10~30% 함유된다.",
            source_markdown="출처: 강의자료.pdf p.391",
        ),
    ]

    written_path = export_cram_studyset_pdf(
        studyset_id="sample-set",
        questions=questions,
        output_path=output_path,
    )

    assert written_path == output_path
    assert output_path.read_bytes().startswith(b"%PDF")
    document = fitz.open(output_path)
    text = "\n".join(page.get_text() for page in document)
    assert "sample-set" in text
    assert "Q1." in text
    assert "건강기능식품 원료 연결로 옳은 것을 모두 고르시오." in text
    assert "코엔자임Q10은 항산화와 항고혈압에 연결된다." in text
    assert "Q2." in text
    assert "가르시니아의 기능성분은?" in text
    assert "hydroxycitric acid, HCA" in text
    assert "아래 표시 보기" not in text
    assert "밀크씨슬은 전립선 건강" not in text
    assert "해설" not in text
    assert "출처" not in text
    assert "강의자료.pdf" not in text
    assert not document[0].get_images()
