from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from time import time

from .models import Library, ReviewStatus, StudyCard


@dataclass
class CardReview:
    card_id: str
    status: ReviewStatus = "unreviewed"
    front_text: str | None = None
    back_text: str | None = None
    note: str = ""
    updated_at: float = field(default_factory=time)


def load_reviews(path: Path) -> dict[str, CardReview]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    reviews = {}
    for item in payload.get("reviews", []):
        review = CardReview(**item)
        reviews[review.card_id] = review
    return reviews


def save_reviews(path: Path, reviews: dict[str, CardReview]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "updated_at": time(),
        "reviews": [asdict(review) for review in sorted(reviews.values(), key=lambda item: item.card_id)],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_review(card: StudyCard, review: CardReview) -> None:
    if review.front_text is not None:
        card.front_text = review.front_text
    if review.back_text is not None:
        card.back_text = review.back_text
    card.review_status = review.status
    card.review_note = review.note
    card.reviewed_at = review.updated_at


def apply_reviews(library: Library, reviews: dict[str, CardReview]) -> Library:
    for card in library.cards:
        review = reviews.get(card.id)
        if review:
            apply_review(card, review)
    library.report.low_confidence_cards = sum(
        1 for card in library.cards if card.confidence < 0.55 and card.review_status != "approved"
    )
    return library
