from pathlib import Path

from studyforge.models import ImportReport, Library, SourceDocument, StudyCard
from studyforge.reviews import CardReview, apply_reviews, load_reviews, save_reviews


def make_library() -> Library:
    source = SourceDocument(
        id="source-1",
        type="pdf",
        subject="subject",
        deck="deck",
        path="sample.pdf",
        fingerprint="fingerprint",
    )
    card = StudyCard(
        id="card-1",
        subject="subject",
        deck="deck",
        source="pdf",
        source_document_id=source.id,
        source_path=source.path,
        source_page=1,
        source_item="1",
        front_text="old front",
        back_text="old back",
        raw_text="raw",
        confidence=0.35,
    )
    return Library(sources=[source], cards=[card], report=ImportReport(cards_created=1, low_confidence_cards=1))


def test_review_overlay_updates_text_and_low_confidence_count(tmp_path: Path):
    reviews = {
        "card-1": CardReview(
            card_id="card-1",
            status="approved",
            front_text="new front",
            back_text="new back",
            note="checked",
        )
    }

    reviewed = apply_reviews(make_library(), reviews)

    assert reviewed.cards[0].front_text == "new front"
    assert reviewed.cards[0].back_text == "new back"
    assert reviewed.cards[0].review_status == "approved"
    assert reviewed.cards[0].review_note == "checked"
    assert reviewed.report.low_confidence_cards == 0


def test_reviews_round_trip(tmp_path: Path):
    path = tmp_path / "reviews.json"
    save_reviews(path, {"card-1": CardReview(card_id="card-1", status="needs_work", note="split")})

    loaded = load_reviews(path)

    assert loaded["card-1"].status == "needs_work"
    assert loaded["card-1"].note == "split"
