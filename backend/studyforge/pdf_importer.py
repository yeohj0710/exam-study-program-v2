from __future__ import annotations

from pathlib import Path
import fitz

from .hashing import cheap_file_fingerprint, file_sha1, slugify, stable_id
from .models import Asset, SourceDocument, StudyCard
from .sources import infer_subject_from_pdf
from .text_segmenter import segment_text


def render_page(page: fitz.Page, target: Path, zoom: float = 1.35) -> tuple[int, int]:
    target.parent.mkdir(parents=True, exist_ok=True)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    pix.save(target)
    return pix.width, pix.height


def import_pdf(
    pdf_path: Path,
    asset_root: Path,
    *,
    subject: str | None = None,
    deck: str | None = None,
    max_pages: int | None = None,
    render_pages: bool = True,
) -> tuple[SourceDocument, list[StudyCard], list[str]]:
    pdf_path = pdf_path.resolve()
    subject = subject or infer_subject_from_pdf(pdf_path)
    deck = deck or pdf_path.stem
    warnings: list[str] = []

    doc = fitz.open(pdf_path)
    fingerprint = file_sha1(pdf_path) if pdf_path.stat().st_size < 35_000_000 else cheap_file_fingerprint(pdf_path)
    source_id = stable_id("pdf", pdf_path, fingerprint, length=18)
    source = SourceDocument(
        id=source_id,
        type="pdf",
        subject=subject,
        deck=deck,
        path=str(pdf_path),
        fingerprint=fingerprint,
        page_count=doc.page_count,
    )

    cards: list[StudyCard] = []
    page_limit = min(doc.page_count, max_pages) if max_pages is not None else doc.page_count
    source_slug = slugify(f"{subject}-{deck}")

    for page_index in range(page_limit):
        page = doc[page_index]
        page_number = page_index + 1
        text = page.get_text("text")
        segments = segment_text(text)
        if not segments:
            segments = []
            warnings.append(f"{pdf_path.name} page {page_number}: no extractable text")

        page_asset: Asset | None = None
        if render_pages:
            page_rel = Path("pdf") / source_slug / f"page-{page_number:04d}.png"
            page_target = asset_root / page_rel
            width, height = render_page(page, page_target)
            page_asset = Asset(
                id=stable_id(source_id, "page", page_number),
                role="source_page",
                path=page_rel.as_posix(),
                source_path=str(pdf_path),
                width=width,
                height=height,
                sha1=cheap_file_fingerprint(page_target),
            )

        if not segments:
            card_id = stable_id(source_id, page_number, "empty")
            cards.append(
                StudyCard(
                    id=card_id,
                    subject=subject,
                    deck=deck,
                    source="page_fallback",
                    source_document_id=source_id,
                    source_path=str(pdf_path),
                    source_page=page_number,
                    source_item=None,
                    front_text=f"{deck} page {page_number}",
                    back_text="",
                    raw_text="",
                    confidence=0.12,
                    review_flags=["no_extractable_text", "needs_manual_review"],
                    assets=[page_asset] if page_asset else [],
                    tags=["pdf", "fallback"],
                )
            )
            continue

        for segment_index, segment in enumerate(segments, start=1):
            flags = list(segment.flags)
            if page_asset:
                flags.append("has_page_snapshot")
            if segment.confidence < 0.55:
                flags.append("needs_manual_review")
            card_id = stable_id(source_id, page_number, segment_index, segment.raw_text)
            cards.append(
                StudyCard(
                    id=card_id,
                    subject=subject,
                    deck=deck,
                    source="pdf" if "page_fallback" not in flags else "page_fallback",
                    source_document_id=source_id,
                    source_path=str(pdf_path),
                    source_page=page_number,
                    source_item=str(segment_index),
                    front_text=segment.front_text,
                    back_text=segment.back_text,
                    raw_text=segment.raw_text,
                    confidence=segment.confidence,
                    review_flags=flags,
                    assets=[page_asset] if page_asset else [],
                    tags=["pdf", subject],
                )
            )

    return source, cards, warnings
