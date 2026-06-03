from pathlib import Path

import fitz

from studyforge.pdf_importer import import_pdf


def make_pdf(path: Path, decor_color: tuple[float, float, float] = (1, 0, 0)) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Define SAR?")
    page.insert_text((72, 96), "Structure-activity relationship")
    page.insert_text((72, 140), "Define total synthesis?")
    page.insert_text((72, 164), "Making a target compound from simple starting materials")
    page.draw_rect(fitz.Rect(300, 300, 320, 320), color=decor_color, fill=decor_color)
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


def test_import_pdf_ids_survive_non_text_source_changes(tmp_path):
    pdf = tmp_path / "sample.pdf"
    make_pdf(pdf, decor_color=(1, 0, 0))
    first_source, first_cards, _ = import_pdf(pdf, tmp_path / "assets", subject="subject", deck="sample")

    pdf.unlink()
    make_pdf(pdf, decor_color=(0, 0, 1))
    second_source, second_cards, _ = import_pdf(pdf, tmp_path / "assets", subject="subject", deck="sample")

    assert first_source.fingerprint != second_source.fingerprint
    assert first_source.id == second_source.id
    assert [card.id for card in first_cards] == [card.id for card in second_cards]
