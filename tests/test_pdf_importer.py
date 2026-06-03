from pathlib import Path

import fitz

from studyforge.pdf_importer import import_pdf


def make_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Define SAR?")
    page.insert_text((72, 96), "Structure-activity relationship")
    page.insert_text((72, 140), "Define total synthesis?")
    page.insert_text((72, 164), "Making a target compound from simple starting materials")
    doc.save(path)
    doc.close()


def test_import_pdf_segments_and_renders_page(tmp_path):
    pdf = tmp_path / "sample.pdf"
    make_pdf(pdf)

    source, cards, warnings = import_pdf(
        pdf,
        tmp_path / "assets",
        subject="의약화학",
        deck="sample",
    )

    assert warnings == []
    assert source.page_count == 1
    assert len(cards) == 2
    roles = [asset.role for asset in cards[0].assets]
    assert roles == ["front_image", "source_page", "page_crop"]
    for asset in cards[0].assets:
        assert (tmp_path / "assets" / asset.path).exists()
    assert "has_front_crop" in cards[0].review_flags
    assert "has_question_crop" in cards[0].review_flags
