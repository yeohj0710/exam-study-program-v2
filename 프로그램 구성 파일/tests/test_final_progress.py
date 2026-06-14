from studyforge.final_progress import (
    load_final_progress,
    mark_memorized,
    record_reveal,
    record_seen,
    restore_question,
    save_final_progress,
)


def test_final_progress_round_trip_mark_restore_and_counts(tmp_path):
    path = tmp_path / "final-progress.json"
    progress = {}

    record_seen(progress, "question-1", now=1_000)
    record_reveal(progress, "question-1", now=1_001)
    mark_memorized(progress, "question-1", now=1_002)
    save_final_progress(path, progress)

    loaded = load_final_progress(path)
    entry = loaded["question-1"]
    assert entry.question_id == "question-1"
    assert entry.seen_count == 1
    assert entry.reveal_count == 1
    assert entry.memorized is True
    assert entry.last_seen_at == 1_000
    assert entry.updated_at == 1_002

    restore_question(loaded, "question-1", now=1_003)
    assert loaded["question-1"].memorized is False
    assert loaded["question-1"].updated_at == 1_003
