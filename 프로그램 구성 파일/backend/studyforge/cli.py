from __future__ import annotations

import argparse
from pathlib import Path

from .importer import build_library
from .progress import load_progress
from .reviews import load_reviews
from .storage import library_summary, load_library, save_library
from .validation import validate_library


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="studyforge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("import", help="Build a study library from PDFs and legacy captures.")
    build.add_argument("--source-root", type=Path, default=None)
    build.add_argument("--legacy-root", type=Path, default=None)
    build.add_argument("--output", type=Path, default=Path("data/library.json"))
    build.add_argument("--asset-root", type=Path, default=Path("data/assets"))
    build.add_argument("--include-lectures", action="store_true")
    build.add_argument("--max-pages-per-pdf", type=int, default=None)
    build.add_argument("--copy-legacy-assets", action="store_true")
    build.add_argument("--no-render-pdf-pages", action="store_true")

    validate = subparsers.add_parser("validate", help="Validate an imported study library and assets.")
    validate.add_argument("--library", type=Path, default=Path("data/library.json"))
    validate.add_argument("--asset-root", type=Path, default=Path("data/assets"))
    validate.add_argument("--reviews", type=Path, default=Path("data/reviews.json"))
    validate.add_argument("--progress", type=Path, default=Path("data/progress.json"))
    validate.add_argument("--strict", action="store_true", help="Exit non-zero for warnings as well as errors.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "import":
        library = build_library(
            source_root=args.source_root,
            legacy_root=args.legacy_root,
            asset_root=args.asset_root,
            include_lectures=args.include_lectures,
            max_pages_per_pdf=args.max_pages_per_pdf,
            copy_legacy_assets=args.copy_legacy_assets,
            render_pdf_pages=not args.no_render_pdf_pages,
        )
        save_library(library, args.output)
        summary = library_summary(library)
        print(f"Saved {summary['card_count']} cards from {summary['source_count']} sources to {args.output}")
        print(f"Low confidence cards: {summary['low_confidence_count']}")
        if library.report.warnings:
            print("Warnings:")
            for warning in library.report.warnings[:20]:
                print(f"- {warning}")
            if len(library.report.warnings) > 20:
                print(f"- ... {len(library.report.warnings) - 20} more")
    elif args.command == "validate":
        library = load_library(args.library)
        report = validate_library(
            library,
            args.asset_root,
            reviews=load_reviews(args.reviews),
            progress=load_progress(args.progress),
        )
        print(f"Validation ok: {report.ok}")
        print(f"Sources: {report.source_count}")
        print(f"Cards: {report.card_count}")
        print(f"Assets: {report.asset_count}")
        print(f"Missing sources: {report.missing_source_count}")
        print(f"Missing assets: {report.missing_asset_count}")
        print(f"Orphan reviews: {report.orphan_review_count}")
        print(f"Orphan progress: {report.orphan_progress_count}")
        if report.issues:
            print("Issues:")
            for issue in report.issues[:30]:
                target = issue.card_id or issue.source_id or "-"
                print(f"- [{issue.severity}] {issue.code} {target}: {issue.message}")
            if len(report.issues) > 30:
                print(f"- ... {len(report.issues) - 30} more")
        has_warning = any(issue.severity == "warning" for issue in report.issues)
        if not report.ok or (args.strict and has_warning):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
