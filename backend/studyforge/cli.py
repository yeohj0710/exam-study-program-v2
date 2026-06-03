from __future__ import annotations

import argparse
from pathlib import Path

from .importer import build_library
from .storage import library_summary, save_library


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


if __name__ == "__main__":
    main()
