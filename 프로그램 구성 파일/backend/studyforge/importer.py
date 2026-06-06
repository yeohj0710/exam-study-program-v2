from __future__ import annotations

from pathlib import Path

from .legacy_importer import import_legacy_bank
from .models import ImportReport, Library
from .pdf_importer import import_pdf
from .sources import discover_midterm_pdfs


def build_library(
    *,
    source_root: Path | None,
    pdf_paths: list[Path] | None = None,
    legacy_root: Path | None,
    asset_root: Path,
    include_lectures: bool = False,
    max_pages_per_pdf: int | None = None,
    copy_legacy_assets: bool = False,
    render_pdf_pages: bool = True,
) -> Library:
    library = Library(generated_at=0.0)
    report = ImportReport()
    asset_root.mkdir(parents=True, exist_ok=True)

    for pdf in pdf_paths or []:
        try:
            source, cards, warnings = import_pdf(
                pdf,
                asset_root,
                max_pages=max_pages_per_pdf,
                render_pages=render_pdf_pages,
            )
            library.sources.append(source)
            library.cards.extend(cards)
            report.pdfs_imported += 1
            report.sources_scanned += 1
            report.warnings.extend(warnings)
        except Exception as exc:
            report.warnings.append(f"PDF import failed: {pdf}: {exc}")

    if source_root:
        pdfs = discover_midterm_pdfs(source_root, include_lectures=include_lectures)
        report.sources_scanned += len(pdfs)
        for pdf in pdfs:
            try:
                source, cards, warnings = import_pdf(
                    pdf,
                    asset_root,
                    max_pages=max_pages_per_pdf,
                    render_pages=render_pdf_pages,
                )
                library.sources.append(source)
                library.cards.extend(cards)
                report.pdfs_imported += 1
                report.warnings.extend(warnings)
            except Exception as exc:
                report.warnings.append(f"PDF import failed: {pdf}: {exc}")

    if legacy_root:
        try:
            sources, cards, warnings = import_legacy_bank(
                legacy_root,
                asset_root,
                copy_assets=copy_legacy_assets,
            )
            library.sources.extend(sources)
            library.cards.extend(cards)
            report.legacy_decks_imported += len(sources)
            report.sources_scanned += len(sources)
            report.warnings.extend(warnings)
        except Exception as exc:
            report.warnings.append(f"legacy import failed: {legacy_root}: {exc}")

    unique_cards = {}
    for card in library.cards:
        unique_cards[card.id] = card
    library.cards = list(unique_cards.values())
    report.cards_created = len(library.cards)
    report.low_confidence_cards = sum(1 for card in library.cards if card.confidence < 0.55)
    library.report = report
    return library
