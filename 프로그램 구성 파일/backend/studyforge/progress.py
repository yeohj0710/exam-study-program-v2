from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from time import time

from .models import Library, StudyCard, StudyRating

SECONDS_PER_DAY = 24 * 60 * 60


@dataclass
class CardProgress:
    card_id: str
    seen_count: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    streak: int = 0
    interval_days: float = 0.0
    ease: float = 2.3
    due_at: float = 0.0
    last_studied_at: float | None = None
    last_rating: StudyRating = "new"
    updated_at: float = field(default_factory=time)


def load_progress(path: Path) -> dict[str, CardProgress]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    progress: dict[str, CardProgress] = {}
    for item in payload.get("cards", []):
        entry = CardProgress(**item)
        progress[entry.card_id] = entry
    return progress


def save_progress(path: Path, progress: dict[str, CardProgress]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "updated_at": time(),
        "cards": [asdict(entry) for entry in sorted(progress.values(), key=lambda item: item.card_id)],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_progress(progress: dict[str, CardProgress], card_id: str) -> None:
    progress.pop(card_id, None)


def record_rating(
    progress: dict[str, CardProgress],
    card_id: str,
    rating: StudyRating,
    *,
    now: float | None = None,
) -> CardProgress:
    if rating == "new":
        raise ValueError("rating must be again, hard, good, or easy")
    current_time = now if now is not None else time()
    entry = progress.get(card_id, CardProgress(card_id=card_id))
    entry.seen_count += 1
    entry.last_rating = rating
    entry.last_studied_at = current_time
    entry.updated_at = current_time

    if rating == "again":
        entry.wrong_count += 1
        entry.streak = 0
        entry.interval_days = 0.0
        entry.ease = max(1.4, entry.ease - 0.2)
        entry.due_at = current_time + 10 * 60
    elif rating == "hard":
        entry.correct_count += 1
        entry.streak += 1
        entry.interval_days = max(0.5, entry.interval_days * 1.2)
        entry.ease = max(1.4, entry.ease - 0.05)
        entry.due_at = current_time + entry.interval_days * SECONDS_PER_DAY
    elif rating == "good":
        entry.correct_count += 1
        entry.streak += 1
        entry.interval_days = 1.0 if entry.interval_days == 0 else entry.interval_days * entry.ease
        entry.due_at = current_time + entry.interval_days * SECONDS_PER_DAY
    elif rating == "easy":
        entry.correct_count += 1
        entry.streak += 1
        entry.interval_days = 3.0 if entry.interval_days == 0 else entry.interval_days * entry.ease * 1.4
        entry.ease = min(3.2, entry.ease + 0.15)
        entry.due_at = current_time + entry.interval_days * SECONDS_PER_DAY

    progress[card_id] = entry
    return entry


def apply_progress_to_card(card: StudyCard, entry: CardProgress) -> None:
    card.study_seen_count = entry.seen_count
    card.study_correct_count = entry.correct_count
    card.study_wrong_count = entry.wrong_count
    card.study_streak = entry.streak
    card.study_interval_days = entry.interval_days
    card.study_due_at = entry.due_at
    card.study_last_studied_at = entry.last_studied_at
    card.study_last_rating = entry.last_rating


def apply_progress(library: Library, progress: dict[str, CardProgress]) -> Library:
    for card in library.cards:
        entry = progress.get(card.id)
        if entry:
            apply_progress_to_card(card, entry)
    return library
