# StudyForge Final MD Implementation Plan

Date: 2026-06-14

This plan implements `2026-06-14-final-md-studyforge-design.md`.

## Phase 0: Baseline

1. Run and record current baseline:
   - `git status --short --branch`
   - `python -m pytest`
   - `npm run lint`
   - `npm run build`
2. Keep the current launcher and distribution paths intact:
   - Root exe/cmd remains the non-developer entrypoint.
   - `프로그램 구성 파일\launcher\ExamStudyCore.exe` remains the packaged server launcher.
   - `프로그램 구성 파일\dist` remains the built frontend output.

## Phase 1: Backend Data Core

Create final-study modules under `프로그램 구성 파일\backend\studyforge`.

1. Add `final_models.py`.
   - Define `StudySet`, `Question`, `QuestionProgress`, `ValidationIssue`, and response helpers.
   - Do not modify existing `models.py` for legacy cards except where compatibility requires imports.
2. Add `markdown_parser.py`.
   - Parse UTF-8 Markdown into `Question` objects.
   - Support `## Q.`, `<!-- sf:id: ... -->`, `### Answer`, and `### Note`.
   - Return questions plus validation issues.
   - Provide a helper to insert missing ids into Markdown.
3. Add parser tests.
   - Valid single question.
   - Multiple questions.
   - Missing answer warning.
   - Duplicate id error.
   - Korean round trip.
   - Missing-id insertion.

Exit criteria:

- New parser tests pass.
- Existing backend tests still pass.

## Phase 2: Studyset Storage And Assets

1. Add `studysets.py`.
   - List `data/studysets/*.md`.
   - Create a new studyset file from a title.
   - Read and save Markdown.
   - Slugify names consistently.
2. Add `asset_manager.py`.
   - Store pasted/dropped image bytes under `data/assets/<studyset-slug>/`.
   - Accept PNG, JPEG, WebP, and GIF.
   - Return a relative Markdown image link.
   - Reject non-image uploads.
3. Add storage and asset tests.
   - Create/list/read/save studysets.
   - Store image and verify returned path exists.
   - Reject non-image content.
   - Report missing linked asset in validation.

Exit criteria:

- Studyset and asset tests pass.
- No existing import/progress/review tests regress.

## Phase 3: Final Progress And API

1. Add `final_progress.py`.
   - Store progress in `data/final-progress.json` keyed by `sf:id`.
   - Track `memorized`, `seen_count`, `reveal_count`, `last_seen_at`, `updated_at`.
   - Do not read or write legacy `data/progress.json`.
2. Add final routes in `final_api.py` and import/register them from `api.py`.
   - `GET /api/studysets`
   - `POST /api/studysets`
   - `GET /api/studysets/{studyset_id}`
   - `PUT /api/studysets/{studyset_id}`
   - `POST /api/studysets/{studyset_id}/assets`
   - `GET /api/studysets/{studyset_id}/questions`
   - `PATCH /api/questions/{question_id}/progress`
   - `DELETE /api/questions/{question_id}/progress`
   - Extend `/api/validation` to include final studysets while preserving legacy validation fields during transition.
3. Add API tests.
   - List empty studysets.
   - Create a set.
   - Save Markdown and receive parsed questions.
   - Upload image and insert returned link.
   - Mark memorized and restore.
   - Validation reports missing answer and missing asset.

Exit criteria:

- All backend tests pass.
- API returns UTF-8 Korean correctly.

## Phase 4: Frontend Rewrite Around Final Workflow

Split the current frontend instead of extending the existing `App.tsx` monolith.

1. Add frontend types and API client.
   - `src/types.ts`
   - `src/api.ts`
2. Add session hook.
   - `useStudySession` owns selected set, queue, cursor, answer visibility, filter, and keyboard handlers.
   - Queue shuffles eligible non-memorized questions once per round.
3. Build primary components.
   - `StudyWorkspace`
   - `StudySetPanel`
   - `QuestionView`
   - `MarkdownEditor`
   - `ValidationPanel`
4. Replace `App.tsx` with the new workspace shell.
5. Replace `App.css` with final-workspace CSS.
   - Keep the UI restrained and dense.
   - Avoid nested cards, decorative gradients, or marketing layout.
   - Ensure dark theme parity.

Exit criteria:

- `npm run lint` passes.
- `npm run build` passes.
- Basic study flow works against a sample Markdown file.

## Phase 5: Editor And Image Paste UX

1. Editor save:
   - Saves raw Markdown.
   - Reparses immediately.
   - Keeps current question if its id still exists.
2. Image paste/drop:
   - Reads clipboard or dropped file image.
   - Uploads to final asset API.
   - Inserts returned Markdown link at cursor.
   - Shows upload failure without losing unsaved text.
3. Validation panel:
   - Shows missing answer, duplicate id, missing image, absolute path issues.
   - Clicks jump editor to approximate issue location when line info is available.

Exit criteria:

- Image paste works in browser verification.
- Editor save updates study view without reload.
- Dark mode and narrow viewport remain usable.

## Phase 6: Sample Final Studyset

Create one small bundled sample only if no real final MD exists yet:

```md
# 예방약학 기말

## Q. 다음 중 장내미생물에 의해 생성되지 않는 비타민은?
<!-- sf:id: sample-yebang-final-001 -->

- 레티놀
- biotin
- 토코페롤
- 코발아민
- 비타민 K

### Answer
레티놀

### Note
기출 PDF 기반 예시 문항.
```

If real Codex-generated subject MDs are available before this phase, use those instead of the sample.

Exit criteria:

- Fresh launch has at least one editable studyset.
- The app is useful immediately without importing the old capture bank.

## Phase 7: Verification And Distribution

1. Run full checks:
   - `python -m pytest`
   - `npm run lint`
   - `npm run build`
   - `python scripts\run_cli.py validate`
2. Run local server:
   - `npm run start`
   - Verify `http://127.0.0.1:8765`
3. Browser verification:
   - Study first question.
   - Reveal answer with `J`.
   - Next with `K`.
   - Mark memorized with `1`.
   - Restore with `R`.
   - Open editor with `Ctrl+E`.
   - Paste image and save.
   - Toggle dark mode.
4. Rebuild distribution artifacts when source changes require it:
   - `npm run build`
   - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_windows_launchers.ps1`
5. Verify normal-user launch:
   - Double-click or run the root cmd/exe path.
   - Confirm the browser opens the final MD workspace without command-line setup.

Exit criteria:

- Root exe/cmd launch the final MD workspace.
- No command-line steps are required for a normal user.
- The repository contains updated source, tests, built frontend, and launchers when rebuilt.

## Defaults And Non-Goals

Defaults:

- Final MD flow is primary.
- Legacy capture bank remains available only through old code until a later compatibility pass.
- PDF direct import is not v1.
- Markdown files are the canonical source; compiled JSON is cache.

Non-goals for v1:

- Rich WYSIWYG editor.
- OCR.
- Multi-user sync.
- Remote storage.
- Full Anki-style spaced repetition.
- Hosted deployment.
