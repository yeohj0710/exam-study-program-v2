from pathlib import Path

import fitz
from PIL import Image

from studyforge.final_models import Question
from studyforge.studyset_pdf import export_studyset_pdf


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
