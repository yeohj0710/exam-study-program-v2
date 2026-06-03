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
    assert cards[0].assets[0].role == "source_page"
    assert (tmp_path / "assets" / cards[0].assets[0].path).exists()
