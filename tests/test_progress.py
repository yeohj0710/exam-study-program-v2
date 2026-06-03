from pathlib import Path

from studyforge.models import ImportReport, Library, SourceDocument, StudyCard
from studyforge.progress import apply_progress, load_progress, record_rating, save_progress


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
        front_text="front",
        back_text="back",
        raw_text="raw",
        confidence=1.0,
    )
    return Library(sources=[source], cards=[card], report=ImportReport(cards_created=1))


def test_record_good_rating_schedules_tomorrow():
    progress = {}
    entry = record_rating(progress, "card-1", "good", now=1_000)

    assert entry.seen_count == 1
    assert entry.correct_count == 1
    assert entry.wrong_count == 0
    assert entry.interval_days == 1.0
    assert entry.due_at == 1_000 + 24 * 60 * 60


def test_record_again_schedules_quick_retry():
    progress = {}
    entry = record_rating(progress, "card-1", "again", now=1_000)

    assert entry.wrong_count == 1
    assert entry.streak == 0
    assert entry.due_at == 1_600


def test_progress_round_trip_and_apply(tmp_path: Path):
    progress = {}
    record_rating(progress, "card-1", "easy", now=2_000)
    path = tmp_path / "progress.json"
    save_progress(path, progress)

    loaded = load_progress(path)
    library = apply_progress(make_library(), loaded)

    assert library.cards[0].study_seen_count == 1
    assert library.cards[0].study_last_rating == "easy"
    assert library.cards[0].study_interval_days == 3.0
