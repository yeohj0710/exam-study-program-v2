# StudyForge

StudyForge is a local-first exam study system that imports Korean midterm PDFs and the old image-capture quiz bank into one reviewable card library.

The repository is intentionally separate from `exam-study-program`. Source materials on `G:\내 드라이브\여형준님` are treated as read-only. Generated libraries and rendered PDF pages are written only under this repository's `data/` directory. Legacy capture images are referenced by default and can be copied explicitly with `--copy-legacy-assets`.

## Architecture

- `backend/studyforge`: FastAPI server, import CLI, PDF parser, legacy image importer, JSON storage.
- `src`: React + TypeScript study UI.
- `tests`: Python regression tests for segmentation and import behavior.
- `data/`: runtime library and assets, ignored by Git.
- `data/reviews.json`: local review/edit overlay, ignored by Git and preserved across re-imports.

## Setup

```powershell
cd C:\dev\studyforge
python -m pip install -r requirements.txt
npm install
```

## Import Materials

Summary PDFs and the existing captured bank:

```powershell
python scripts/run_cli.py import `
  --source-root "G:\내 드라이브\여형준님\21 6-1" `
  --legacy-root "G:\내 드라이브\여형준님\21 6-1\족보 암기 프로그램\중간고사"
```

Quick smoke import with only the first two pages per PDF:

```powershell
npm run import:sample
```

By default, lecture slide PDFs whose names contain `수업자료` are skipped to avoid flooding the card set. Add `--include-lectures` when the full lecture material should be converted too.

## Run

Start the API:

```powershell
npm run dev:api
```

Start the web app in another terminal:

```powershell
npm run dev
```

Open the Vite URL shown in the terminal.

## Verification

```powershell
python -m pytest
npm run build
```

## Import Strategy

- PDF text is split into question-answer cards with Korean exam-question heuristics.
- Each PDF card keeps the rendered source page as evidence, so diagrams and screenshots remain inspectable even when text extraction is incomplete.
- Low-confidence or fallback cards are flagged for review instead of being silently discarded.
- Existing image folders are imported as stable cards: first image is the front, last image is the answer, middle images are choices.
- Existing capture PNGs are referenced by default for speed. Use `--copy-legacy-assets` when a fully self-contained local copy is needed.
- Card IDs are deterministic from source fingerprints and content, so re-imports keep unchanged cards stable while allowing new or changed material to appear.

## Review Workflow

- The inspector panel shows unresolved low-confidence cards and per-card review flags.
- Use `승인 저장` after checking or editing a card. Approved low-confidence cards no longer count as unresolved.
- Use `보류 저장` when a card needs later manual cleanup.
- Edits are stored as an overlay in `data/reviews.json`, not inside the imported source library. Running import again keeps the review overlay for cards whose deterministic IDs remain the same.
