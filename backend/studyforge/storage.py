from __future__ import annotations

import json
from pathlib import Path
from time import time

from .models import Library, library_from_dict, library_to_dict


def save_library(library: Library, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(library_to_dict(library), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_library(path: Path) -> Library:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return library_from_dict(payload)


def library_summary(library: Library) -> dict[str, object]:
    decks: dict[str, int] = {}
    subjects: dict[str, int] = {}
    now = time()
    for card in library.cards:
        decks[card.deck] = decks.get(card.deck, 0) + 1
        subjects[card.subject] = subjects.get(card.subject, 0) + 1
    return {
        "schema_version": library.schema_version,
        "generated_at": library.generated_at,
        "source_count": len(library.sources),
        "card_count": len(library.cards),
        "low_confidence_count": sum(1 for card in library.cards if card.confidence < 0.55),
        "deck_count": len(decks),
        "subject_count": len(subjects),
        "study_due_count": sum(1 for card in library.cards if card.study_seen_count > 0 and card.study_due_at <= now),
        "study_new_count": sum(1 for card in library.cards if card.study_seen_count == 0),
        "study_seen_count": sum(1 for card in library.cards if card.study_seen_count > 0),
        "decks": decks,
        "subjects": subjects,
        "report": library.report.__dict__,
    }
