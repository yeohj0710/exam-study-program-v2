# StudyForge Final MD Design

Date: 2026-06-14

## Summary

StudyForge Final turns the current capture-image memorization app into a local-first Markdown study workspace for final-exam prep.

The v1 source of truth is Markdown plus local assets:

```text
프로그램 구성 파일/
  data/
    studysets/
      예방약학-기말.md
      의약화학-기말.md
    assets/
      예방약학-기말/
        img-20260614-191200-a1b2.png
    final-progress.json
    compiled/
      library.json
```

The existing Windows launcher, local FastAPI server, Vite/React frontend, and offline distribution model stay. The legacy capture/PDF import system is preserved as a compatibility island, but it is not the v1 product path.

## Product Decisions

- Build v1 around final-exam Markdown studysets only.
- Keep raw text as text; do not turn text questions into images.
- Let Codex or the user edit one Markdown file per subject/exam.
- Let the app handle image storage and Markdown link insertion from paste or drag-and-drop.
- Keep memorization minimal: choose a set, show a question, reveal the answer, go next, mark memorized, restore.
- Use a quiet, utilitarian UI similar in restraint to ChatGPT/Codex: no marketing page, no decorative hero, no nested card-heavy layout.
- Support dark mode as a first-class theme, not an afterthought.

## Markdown Format

Each studyset is one UTF-8 Markdown file under `data/studysets`.

```md
# 예방약학 기말

## Q. 다음 중 장내미생물에 의해 생성되지 않는 비타민은?
<!-- sf:id: yebang-final-001 -->

- 레티놀
- biotin
- 토코페롤
- 코발아민
- 비타민 K

![관련 표](assets/예방약학-기말/img-20260614-191200-a1b2.png)

### Answer
레티놀

### Note
장내미생물 생성 가능 비타민과 아닌 것을 구분.
```

Rules:

- `#` is the studyset title.
- `## Q.` starts a question and continues until the next `## Q.` or end of file.
- `<!-- sf:id: ... -->` is the stable question id.
- Text before `### Answer` is the question side.
- Text under `### Answer` and before `### Note` is the answer side.
- `### Note` is optional explanation or memory hint.
- Markdown image links are allowed on the question, answer, or note side.
- Image links must be relative to `data/`.
- If a question has no `sf:id`, the backend generates one and can insert it into the Markdown file on save.

Unsupported in v1:

- Nested subquestions with separate scoring.
- Tables that need cell-level editing.
- Remote image URLs as canonical assets.
- Direct PDF-to-question generation as a normal user flow.

## Parsed Data Model

Backend parsed objects should be separate from legacy `StudyCard`.

```python
StudySet:
  id: str
  title: str
  slug: str
  path: str
  updated_at: float
  question_count: int
  issue_count: int

Question:
  id: str
  studyset_id: str
  ordinal: int
  title: str
  prompt_markdown: str
  answer_markdown: str
  note_markdown: str
  asset_paths: list[str]
  issues: list[ValidationIssue]

QuestionProgress:
  question_id: str
  memorized: bool
  seen_count: int
  reveal_count: int
  last_seen_at: float | None
  updated_at: float
```

Question ids are stable and must drive progress. The parser should not use array index as the persisted identity.

## Backend API

Add final-MD APIs while leaving existing legacy APIs available until the new UI no longer needs them.

Required endpoints:

- `GET /api/studysets`
  Returns studyset summaries from `data/studysets`.
- `POST /api/studysets`
  Creates a Markdown file from a title and optional slug.
- `GET /api/studysets/{studyset_id}`
  Returns raw Markdown, parsed questions, and validation issues.
- `PUT /api/studysets/{studyset_id}`
  Saves raw Markdown, normalizes missing ids, reparses, and returns the new state.
- `POST /api/studysets/{studyset_id}/assets`
  Accepts pasted or dropped image data, stores it under `data/assets/<studyset-slug>/`, and returns a Markdown image link.
- `GET /api/studysets/{studyset_id}/questions`
  Returns parsed questions with progress applied.
- `PATCH /api/questions/{question_id}/progress`
  Marks a question memorized or records reveal/seen events.
- `DELETE /api/questions/{question_id}/progress`
  Restores a memorized question.
- `GET /api/validation`
  Returns Markdown and asset validation for all final studysets.

Asset serving:

- Continue serving `/assets/...` from `data/assets`.
- Reject asset uploads that are not image MIME types.
- Use content hashing or timestamp plus random suffix to avoid overwrite.
- Return relative Markdown links like `![image](assets/예방약학-기말/img-20260614-191200-a1b2.png)`.

## Frontend UX

The app opens directly into the study workspace.

Layout:

- Left rail: set picker, search, theme, edit toggle, shutdown.
- Optional left panel: studyset list with counts.
- Center surface: current question and answer reveal.
- Bottom composer: answer, next, memorize, restore.
- Optional right panel: Markdown editor, image insert controls, validation issues.

Keyboard:

- `J` or `Space`: reveal/hide answer.
- `K` or right arrow: next question.
- `1`: mark memorized after answer is visible.
- `R`: restore memorized question.
- `/`: focus search.
- `Ctrl+E`: toggle editor.
- `Ctrl+B`: toggle set panel.
- `Ctrl+I`: toggle info/validation panel.
- `Ctrl+-`, `Ctrl+=`, `Ctrl+0`: keep zoom controls.

Study behavior:

- Default queue includes non-memorized questions in the selected studyset.
- Start each round with a full shuffle of eligible questions.
- A round should not repeat questions until all eligible questions have appeared.
- Memorized questions disappear from the default queue.
- The memorized filter can show and restore excluded questions.
- Choice shuffling is optional and off by default; Markdown order remains canonical.

Editor behavior:

- The editor edits the raw Markdown file.
- Save reparses and updates the current question list without restarting the app.
- Pasted or dropped images are uploaded first, then a Markdown image link is inserted at the cursor.
- If the parser finds missing `sf:id` comments, save inserts them near the question heading.
- Validation issues appear inline enough to fix quickly, but do not block saving except for file write errors.

## Validation

Validation should report:

- Missing `### Answer`.
- Empty prompt.
- Duplicate question id as an error; study mode excludes duplicate-id questions after the first occurrence until fixed.
- Missing local image asset as a warning; render a compact missing-image placeholder in study mode.
- Unsupported absolute image link as a warning; render only if it stays under an explicitly allowed local path.
- Studyset with zero questions.
- Progress entries for deleted question ids as warnings.

Validation should allow imperfect drafts. The study mode should skip questions with no answer unless the user opens a draft/filter view.

## Implementation Boundaries

Keep modules small and replace the current single-file frontend shape.

Backend modules:

- `final_models.py`
- `markdown_parser.py`
- `studysets.py`
- `asset_manager.py`
- `final_progress.py`
- `final_api.py`, imported by `api.py`

Frontend modules:

- `types.ts`
- `api.ts`
- `hooks/useStudySession.ts`
- `components/StudyWorkspace.tsx`
- `components/StudySetPanel.tsx`
- `components/QuestionView.tsx`
- `components/MarkdownEditor.tsx`
- `components/ValidationPanel.tsx`

Do not do a broad visual redesign unrelated to the final-study workflow. Do not keep adding features to the old `App.tsx` monolith; split the new UI as part of the work.

## Testing And Acceptance

Backend tests:

- Parse a valid Markdown studyset into one question.
- Parse multiple questions with stable ids.
- Generate and insert missing ids.
- Reject or warn duplicate ids.
- Report missing answer and missing asset.
- Save and reload Markdown without losing Korean text.
- Store pasted image bytes and return a relative Markdown link.
- Persist progress by stable question id.
- Restore memorized progress.
- Preserve legacy tests unless intentionally moved.

Frontend checks:

- `npm run lint`
- `npm run build`
- Browser run at `http://127.0.0.1:8765`
- Study queue shows all non-memorized questions once per round.
- `J`, `K`, `1`, `R`, `/`, `Ctrl+E`, dark mode all work.
- Editor save updates study mode.
- Image paste inserts a usable Markdown image link and renders the image.
- Mobile/narrow viewport does not overlap text or controls.

Progress storage:

- Final MD progress uses `data/final-progress.json`.
- Existing legacy endpoints may keep using `data/progress.json` until legacy support is intentionally retired.
- Final UI must not write to the legacy progress schema.

Final deliverable:

- Local Windows app still launches from root exe/cmd.
- Offline study mode works from committed/bundled files.
- Final MD workflow is the primary UI.
- Legacy image-bank support is not required in the v1 primary interface.
