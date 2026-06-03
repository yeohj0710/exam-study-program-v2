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


def make_blank_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.draw_rect(fitz.Rect(72, 72, 240, 180), color=(0, 0, 0), width=1)
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


def test_import_pdf_creates_review_card_for_image_only_page(tmp_path):
    pdf = tmp_path / "scan.pdf"
    make_blank_pdf(pdf)

    source, cards, warnings = import_pdf(
        pdf,
        tmp_path / "assets",
        subject="스캔자료",
        deck="scan",
    )

    assert source.page_count == 1
    assert warnings == ["scan.pdf page 1: no extractable text"]
    assert len(cards) == 1
    assert cards[0].source == "page_fallback"
    assert cards[0].front_text == "scan page 1"
    assert "needs_manual_review" in cards[0].review_flags
    assert "full_page_front_fallback" in cards[0].review_flags
    assert "full_page_crop_fallback" in cards[0].review_flags
    roles = [asset.role for asset in cards[0].assets]
    assert roles == ["front_image", "source_page", "page_crop"]
    for asset in cards[0].assets:
        assert (tmp_path / "assets" / asset.path).exists()


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


def test_import_pdf_is_deterministic_for_same_pdf(tmp_path):
    pdf = tmp_path / "sample.pdf"
    make_pdf(pdf)

    first_source, first_cards, first_warnings = import_pdf(
        pdf,
        tmp_path / "assets-first",
        subject="의약화학",
        deck="sample",
    )
    second_source, second_cards, second_warnings = import_pdf(
        pdf,
        tmp_path / "assets-second",
        subject="의약화학",
        deck="sample",
    )

    def card_signature(card):
        return {
            "id": card.id,
            "subject": card.subject,
            "deck": card.deck,
            "source": card.source,
            "source_document_id": card.source_document_id,
            "source_page": card.source_page,
            "source_item": card.source_item,
            "front_text": card.front_text,
            "back_text": card.back_text,
            "raw_text": card.raw_text,
            "confidence": card.confidence,
            "review_flags": card.review_flags,
            "tags": card.tags,
            "created_at": card.created_at,
            "updated_at": card.updated_at,
            "assets": [
                {
                    "id": asset.id,
                    "role": asset.role,
                    "path": asset.path,
                    "width": asset.width,
                    "height": asset.height,
                    "sha1": asset.sha1,
                }
                for asset in card.assets
            ],
        }

    assert first_warnings == second_warnings == []
    assert first_source.id == second_source.id
    assert first_source.fingerprint == second_source.fingerprint
    assert first_source.imported_at == second_source.imported_at == 0.0
    assert [card_signature(card) for card in first_cards] == [
        card_signature(card) for card in second_cards
    ]
