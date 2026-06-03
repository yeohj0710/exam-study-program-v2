from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from .models import Library, StudyCard
from .progress import CardProgress
from .reviews import CardReview

ValidationSeverity = Literal["error", "warning"]


@dataclass
class ValidationIssue:
    severity: ValidationSeverity
    code: str
    message: str
    card_id: str | None = None
    source_id: str | None = None


@dataclass
class ValidationReport:
    ok: bool
    source_count: int
    card_count: int
    asset_count: int
    missing_asset_count: int = 0
    missing_source_count: int = 0
    duplicate_card_count: int = 0
    orphan_review_count: int = 0
    orphan_progress_count: int = 0
    pdf_cards_missing_front_count: int = 0
    pdf_cards_missing_crop_count: int = 0
    legacy_cards_missing_front_count: int = 0
    legacy_cards_missing_answer_count: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def resolve_asset_path(asset_path: str, asset_root: Path) -> Path:
    candidate = Path(asset_path)
    if candidate.is_absolute() or candidate.drive:
        return candidate
    return asset_root / candidate


def card_has_role(card: StudyCard, role: str) -> bool:
    return any(asset.role == role for asset in card.assets)


def validate_library(
    library: Library,
    asset_root: Path,
    *,
    reviews: dict[str, CardReview] | None = None,
    progress: dict[str, CardProgress] | None = None,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    source_ids = {source.id for source in library.sources}
    card_ids: set[str] = set()
    duplicate_card_count = 0
    missing_source_count = 0
    missing_asset_count = 0
    pdf_cards_missing_front_count = 0
    pdf_cards_missing_crop_count = 0
    legacy_cards_missing_front_count = 0
    legacy_cards_missing_answer_count = 0
    asset_count = 0

    for source in library.sources:
        if not Path(source.path).exists():
            missing_source_count += 1
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="missing_source",
                    message=f"Source path does not exist: {source.path}",
                    source_id=source.id,
                )
            )

    for card in library.cards:
        if card.id in card_ids:
            duplicate_card_count += 1
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="duplicate_card",
                    message=f"Duplicate card id: {card.id}",
                    card_id=card.id,
                )
            )
        card_ids.add(card.id)

        if card.source_document_id not in source_ids:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="missing_card_source",
                    message=f"Card references missing source: {card.source_document_id}",
                    card_id=card.id,
                )
            )

        if card.source in {"pdf", "page_fallback"}:
            if not card_has_role(card, "front_image"):
                pdf_cards_missing_front_count += 1
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="pdf_missing_front",
                        message="PDF card is missing a front crop asset.",
                        card_id=card.id,
                    )
                )
            if not card_has_role(card, "page_crop"):
                pdf_cards_missing_crop_count += 1
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="pdf_missing_crop",
                        message="PDF card is missing a full question crop asset.",
                        card_id=card.id,
                    )
                )

        if card.source == "legacy_capture":
            if not card_has_role(card, "front_image"):
                legacy_cards_missing_front_count += 1
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="legacy_missing_front",
                        message="Legacy card is missing the first/front image.",
                        card_id=card.id,
                    )
                )
            if not card_has_role(card, "answer_image"):
                legacy_cards_missing_answer_count += 1
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="legacy_missing_answer",
                        message="Legacy card is missing the final/answer image.",
                        card_id=card.id,
                    )
                )

        for asset in card.assets:
            asset_count += 1
            if not resolve_asset_path(asset.path, asset_root).exists():
                missing_asset_count += 1
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="missing_asset",
                        message=f"Asset path does not exist: {asset.path}",
                        card_id=card.id,
                    )
                )

    review_keys = set(reviews or {})
    progress_keys = set(progress or {})
    orphan_review_count = len(review_keys - card_ids)
    orphan_progress_count = len(progress_keys - card_ids)

    for card_id in sorted(review_keys - card_ids):
        issues.append(
            ValidationIssue(
                severity="warning",
                code="orphan_review",
                message="Review overlay references a card that is not in the current library.",
                card_id=card_id,
            )
        )
    for card_id in sorted(progress_keys - card_ids):
        issues.append(
            ValidationIssue(
                severity="warning",
                code="orphan_progress",
                message="Progress overlay references a card that is not in the current library.",
                card_id=card_id,
            )
        )

    error_count = sum(1 for issue in issues if issue.severity == "error")
    return ValidationReport(
        ok=error_count == 0,
        source_count=len(library.sources),
        card_count=len(library.cards),
        asset_count=asset_count,
        missing_asset_count=missing_asset_count,
        missing_source_count=missing_source_count,
        duplicate_card_count=duplicate_card_count,
        orphan_review_count=orphan_review_count,
        orphan_progress_count=orphan_progress_count,
        pdf_cards_missing_front_count=pdf_cards_missing_front_count,
        pdf_cards_missing_crop_count=pdf_cards_missing_crop_count,
        legacy_cards_missing_front_count=legacy_cards_missing_front_count,
        legacy_cards_missing_answer_count=legacy_cards_missing_answer_count,
        issues=issues,
    )
