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
- `문제 데이터\`: user-facing Markdown study/question sets and their assets.

## Exam Study Markdown Data Work

When the user asks to create, extend, repair, or polish Exam Study Markdown data, do not rely on this file alone. First open and follow:
- `시험공부자료 MD 작성 프롬프트.txt`
- `프로그램 구성 파일\prompts\시험공부자료 MD 작성 상세 프롬프트.txt`
- `프로그램 구성 파일\prompts\시험공부자료 MD 작성 실패사례와 처리원칙.txt`
- `프로그램 구성 파일\prompts\시험공부자료 MD 작성 품질 규정집.txt`

Use those files whenever the request mentions any of these, even indirectly:
- 시험공부자료, 문제 데이터, Markdown 문제, 정리자료, 암기자료, 문제셋, 출처 이미지, 기출 복원.
- "이 문항 고쳐줘", "보기 이상함", "풀이 개선", "더 외우기 좋게", or similar feedback about an Exam Study card.
- A screenshot of the Exam Study app or exported question view.

For new Markdown data:
- Save final Markdown directly under `문제 데이터`.
- Save images under `문제 데이터\assets\<Markdown 파일명>\...`.
- Use only the user-provided exam-scope path for question facts and `출처:` lines.
- Follow the prompt files and quality rulebook before writing any final data.

For existing Markdown data edits:
- First identify the target Markdown under `문제 데이터` and read the surrounding question block.
- Preserve the existing problem count unless the user explicitly asks to add or remove questions.
- Keep every edited question with `답:` and `출처:` lines and keep asset links relative.
- Re-run parser/tests or a focused structural check before reporting completion.

Memorization-oriented Markdown cleanup:
- Treat every edit as a study-screen readability edit, not just a factual patch.
- Make the edited block clean, compact, and easy to memorize when rendered in the app.
- Keep one idea per line when an answer or explanation contains multiple facts, exceptions, examples, or cause-effect links.
- Do not turn answers into long paragraphs. Split dense explanations into short answer lines, but do not add arbitrary labels such as `핵심:`, `요약:`, or `암기포인트:`.
- Remove visual clutter before finishing: repeated wording, redundant filler, slash-joined explanations, awkward inline parentheticals, accidental choice labels, and raw Markdown tokens that do not help recall.
- Preserve the standard rhythm: question text, optional clean choices, `답:` with the direct answer first, short supporting lines only when needed, then `출처:` and source images.
- In visible choices, keep wording parallel and uncluttered. Do not add emphasis, answer hints, source notes, or explanatory asides inside choices.
- For multiple-choice or "choose all" cards, the answer area should briefly correct the wrong choices when the distractors test specific pairings, categories, mechanisms, or exceptions.
- Keep wrong-choice corrections compact and parallel, usually `wrong pairing -> correct pairing` or `choice keyword -> correct fact`; do not write long prose for each option.
- When every option is a term-to-category or term-to-function pairing, list the relevant mappings in the same format so the card is easy to memorize.
- For factual multiple-choice explanations, prefer explicit O/X review lines: correct statements first, then wrong statements. Write wrong items as `X original wrong sentence -> corrected fact` so the user sees both the trap and the fix.
- For wrong O/X review items, the part after `->` must first give the corrected sentence or corrected mapping. If that alone leaves the trap unclear, add one short support sentence after it. Do not use visible labels such as `옳게 고치기:`, `해설:`, `핵심:`, or `정답 조합은`.
- For correct O review items, normally add one short support line that explains why the statement is true in easier words. The support line should not merely repeat the choice.
- Use `O original correct sentence // one short support sentence`; the renderer shows only the support sentence below the O card, not the delimiter.
- Ground O/X corrections and support sentences in the cited course material or cited source image. Do not add general-knowledge explanations that are not supported by that question's `출처:`.
- Keep revealed-answer ordering deterministic: hidden choices may be shuffled, but revealed choices and answer explanations should group O items before X items while preserving original order inside each group.
- When regrouping revealed problem choices, keep the visible choice sentences as normal plain choices. Do not inject O/X badges, colors, corrections, or explanation text into the problem-choice area; only the order changes.
- Revealed problem-choice regrouping may change O/X order, but must not rewrite the original choice sentence. Put correction text only in the revealed answer review.
- Use blue/red visual treatment for revealed O/X review UI, with compact badges and spacing for wrapped lines. Do not rely on divider lines to distinguish one-line and two-line choices.
- If a screenshot fix changes only one flawed phrase, still reread the whole question block and lightly tidy nearby answer formatting when it is messy.
- Do not over-polish by inventing new facts, mnemonics, or explanations not grounded in the cited source. Clean structure and wording, not the evidence.

Last-minute PDF export:
- Keep the existing full `문답 PDF` as the detailed export with questions, answers, source text, and source images.
- The `5분 문답 PDF` is a separate cram export for the currently selected dataset. It should contain only compact question prompts and direct answer facts.
- Do not include source images, `출처:` lines, long explanations, wrong-choice prose, or source-page screenshots in the `5분 문답 PDF`.
- For O/X review answers, include only the O items as direct answer facts. Strip `//` support text and `->` corrections from the cram export.
- If a correct answer is represented as an `O 아래 조합` block, include the following bullet mappings as the answer facts.
- The cram export is for the final 5 minutes before an exam; prefer density, scanability, and deterministic dataset order over rich explanation.

For screenshot-based study-card fixes:
- Inspect visible clues: card number, subject/course text, question wording, answer wording, `출처:` line, source image filename/path, and visible asset names.
- Search `문제 데이터\*.md` for distinctive question or answer text from the screenshot.
- If exact text search fails, search by subject name, source file name, page number, or visible keywords.
- If exactly one Markdown question block is confidently identified, edit that block according to the prompt files and quality rulebook.
- If multiple candidates match or the target cannot be identified from the screenshot, ask the user for the Markdown filename or one more identifying clue before editing.
- Do not invent source facts from the screenshot. Use the existing Markdown and the source files already cited by that question when content must be corrected.

Common quality failures to prevent:
- Shuffled choices containing labels/numbers such as `- ㄱ.`, `- ①`, or `- 5.`.
- Answers/explanations referring to removed choice labels such as `답: ㄱ, ㄴ`, `ㄴ은`, or `ㄷ은`.
- Emphasis inside visible choices, such as `**...**` or `==...==`, that reveals the answer before reveal.
- Multiple answer or explanation sentences joined with ` / ` instead of line breaks.
- Existing set edits that accidentally change the number of `# 문제` blocks.

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

Use PowerShell from `C:\dev\exam-study-program-v2`.

Frontend:
```powershell
cd "C:\dev\exam-study-program-v2\프로그램 구성 파일"
npm run lint
npm run build
```

Backend tests:
```powershell
cd "C:\dev\exam-study-program-v2\프로그램 구성 파일"
python -m pytest
```

Windows launchers:
```powershell
cd "C:\dev\exam-study-program-v2"
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

Remote: `https://github.com/yeohj0710/exam-study-program-v2.git`

Deployment for this project currently means committing and pushing the runnable Windows distribution to `main`, including:
- root exe when rebuilt,
- `ExamStudyCore.exe` when rebuilt,
- `dist` assets when frontend is rebuilt,
- source and tests.

There is no hosted web deployment target currently configured.
