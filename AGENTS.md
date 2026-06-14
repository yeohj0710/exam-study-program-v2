# Exam Study Agent Notes

## Project Goal

Exam Study is a local-first Windows study-card app for non-developers.

Primary user flow:
- User double-clicks `시험 자료 암기 프로그램.exe` in the repo root.
- A splash/loading window appears immediately.
- The app opens a local browser UI backed by a local API at `127.0.0.1`.
- Users study generated cards from PDFs and legacy image decks.

Do not introduce flows that require command-line use for normal users.

## Offline Requirement

The app must work without internet when distributed with these files:
- `시험 자료 암기 프로그램.exe`
- `프로그램 구성 파일\launcher\ExamStudyCore.exe`
- `프로그램 구성 파일\dist\...`
- `프로그램 구성 파일\data\library.json`
- `프로그램 구성 파일\assets\...`

The `127.0.0.1` API is local-only, not an external server. Data is stored locally under `프로그램 구성 파일\data` and local asset folders. Do not add external storage or online dependencies to the normal study flow.

The root `.cmd` file is only a fallback path and may need Python/package setup. The primary offline distribution path is the `.exe`.

## Repository Layout

Root should stay simple for non-developers:
- `시험 자료 암기 프로그램.exe`: main double-click launcher.
- `시험 자료 암기 프로그램.cmd`: fallback launcher.
- `README.md`, `사용설명서.html`: user-facing docs.
- `프로그램 구성 파일\`: implementation, bundled backend/frontend/assets.

Important implementation paths:
- `프로그램 구성 파일\src\`: React frontend.
- `프로그램 구성 파일\backend\studyforge\`: Python backend/import logic.
- `프로그램 구성 파일\launcher\Exam StudyBootstrap.cs`: instant splash/bootstrap exe source.
- `프로그램 구성 파일\launcher\studyforge_launcher.py`: packaged backend launcher.
- `프로그램 구성 파일\scripts\build_frontend.ps1`: frontend build.
- `프로그램 구성 파일\scripts\build_windows_launchers.ps1`: exe/icon rebuild.
- `프로그램 구성 파일\dist\`: built frontend committed for distribution.
- `프로그램 구성 파일\data\library.json`: generated study library.

## Current UI Decisions

Keep the app dense and study-focused, not a landing page.

Current important UI behavior:
- Left deck sidebar is toggleable with `Ctrl+B`.
- Inspector panel is toggleable with `Ctrl+I`.
- Question navigator is collapsed by default and toggled with `Ctrl+P`.
- Question navigator must allow direct jump to a card when expanded.
- Question and answer content are centered inside the study card.
- Wide screens use a centered max-width study layout; do not let content stretch edge-to-edge.
- Bottom study controls stay centered.

Keyboard conventions:
- `Space` or `J`: show/hide answer.
- `K` or right arrow: skip/next.
- `1`: mark as memorized/excluded after answer is shown.
- `R`: restore a memorized/excluded card.
- `Ctrl+-`, `Ctrl+=`, `Ctrl+0`: zoom out/in/reset.

## PDF Import Rules

PDF import must avoid creating cards from table-of-contents/range rows.

Already handled:
- Rows like `Q5-Q8`, `Q5–Q8`, etc. followed by outline text such as `Part A`, `Foundations`, `Linear Algebra`, `Loss Functions`, `Regularization`, `Optimization` are skipped.
- Outline-only PDF pages should not become fallback cards.
- Image-only pages still create manual-review fallback cards.

Relevant files:
- `프로그램 구성 파일\backend\studyforge\text_segmenter.py`
- `프로그램 구성 파일\backend\studyforge\pdf_importer.py`
- `프로그램 구성 파일\tests\test_text_segmenter.py`
- `프로그램 구성 파일\tests\test_pdf_importer.py`

After changing import logic, regenerate local data through `/api/import` or the UI `자료 갱신` flow if current bundled data needs to reflect the change.

## Deterministic Import Check

2026-06-03 real-source verification:
- Source root used: `G:\내 드라이브\여형준님\21 6-1`
- Legacy root used: `G:\내 드라이브\여형준님\21 6-1\족보 암기 프로그램\중간고사`
- Ran `build_library(... copy_legacy_assets=True, render_pdf_pages=True)` twice into separate clean temp asset folders.
- Result after latest fix: both full `library_to_dict()` JSON signatures matched.
- Signature: `a9b48070ecbbada45065e953ba1874dd10a48e1677ec2acca179d1820d5b9f64`
- Counts: 19 sources, 947 cards, 11 PDFs, 8 legacy decks, 79 low-confidence cards.
- Validation: `ok=true`, missing assets 0, missing sources 0, PDF cards missing front 0, PDF cards missing crop 0.
- Bad extraction guards: outline hits 0, thin front images 0, thin crop images 0.

Regression fixed here:
- `legacy_importer.py` copied legacy image assets were previously hashed with `cheap_file_fingerprint(target)` when image measuring was off.
- That included copied temp path/mtime, so clean imports into different asset roots produced different JSON signatures.
- Copied legacy assets now always use content hash `file_sha1(target)`.
- Test coverage: `test_import_legacy_copy_hashes_do_not_depend_on_asset_root`.

## Build And Verification

Use PowerShell from `C:\dev\exam-study-program`.

Frontend:
```powershell
cd "C:\dev\exam-study-program\프로그램 구성 파일"
npm run lint
npm run build
```

Backend tests:
```powershell
cd "C:\dev\exam-study-program\프로그램 구성 파일"
python -m pytest
```

Windows launchers:
```powershell
cd "C:\dev\exam-study-program"
powershell -NoProfile -ExecutionPolicy Bypass -File "프로그램 구성 파일\scripts\build_windows_launchers.ps1"
```

When backend code changes, rebuild `ExamStudyCore.exe` with `build_windows_launchers.ps1` before committing distribution changes.

Before push, normally verify:
- `npm run lint`
- `npm run build`
- `python -m pytest`
- Browser visual check at `http://127.0.0.1:8765` for UI work.

## Launcher And Icon Notes

The root exe is a small C# bootstrap that shows the splash window immediately, then starts `ExamStudyCore.exe` hidden.

Current icon/logo:
- Windows exe icon is generated by `build_windows_launchers.ps1`.
- Splash logo is drawn in `Exam StudyBootstrap.cs`.
- Both should remain visually consistent.

Windows Explorer may cache exe icons. If icon changes appear stale, refresh Explorer/icon cache before assuming the resource failed.

## GitHub Deployment

Remote: `https://github.com/yeohj0710/studyforge.git`

Deployment for this project currently means committing and pushing the runnable Windows distribution to `main`, including:
- root exe when rebuilt,
- `ExamStudyCore.exe` when rebuilt,
- `dist` assets when frontend is rebuilt,
- source and tests.

There is no hosted web deployment target currently configured.
