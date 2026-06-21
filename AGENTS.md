# Exam Study Agent Entry

Goal-mode entry file. Detailed rules live in referenced files.

Project root: `C:\dev\exam-study-program-v2`.
Remote: `https://github.com/yeohj0710/exam-study-program-v2.git`.

## Mandatory Preflight

For Exam Study Markdown/question-data work, read before drafting/editing:
- `문제 데이터 작성 프롬프트.txt`
- `프로그램 구성 파일\prompts\시험공부자료 MD 작성 상세 프롬프트.txt`
- `프로그램 구성 파일\prompts\시험공부자료 MD 작성 실패사례와 처리원칙.txt`
- `프로그램 구성 파일\prompts\시험공부자료 MD 작성 품질 규정집.txt`
- `프로그램 구성 파일\prompts\시험공부자료 MD 작성 운영 원칙.txt`
- `프로그램 구성 파일\prompts\시험공부자료 MD 작성 선별 전략.txt`

For app/build/UI/import/launcher/repo tasks, also read:
- `프로그램 구성 파일\prompts\AGENTS 상세 운영 지침.md`

## Markdown Data Rules

- The user may provide only the exam-scope folder path. Inspect real files first; infer subject, exam name, output filename, reference style, and question count.
- Use only files inside the provided exam-scope path for current facts and `출처:`. Outside folders may guide style/tendency only.
- Save final Markdown directly under `문제 데이터`. Save images under `문제 데이터\assets\<Markdown 파일명>\...` and link them relatively.
- Work top-down: map materials, identify priorities, then write by natural units.
- Prioritize target-exam past/restored exams, professor-highlighted slides, repeated concepts, central diagrams/tables, and likely short-answer/short-explanation material.
- If previous-exam slides are included only to show question style, use them as style evidence only; do not ask their content as current-exam questions.
- Do not inflate question count. Make only high-probability questions.

## Card Writing Rules

- Every question block starts with `# 문제`, then question text, optional clean choices/images, `답:`, optional `[배경설명]`/`[해설]`, optional `[보기해설]`, `출처:`, and source image links.
- Answers give the direct answer first. `[배경설명]` defines terms and explains mechanism/context. `[보기해설]` explains choices with `O choice // reason` and `X choice -> corrected fact. reason`.
- Avoid abrupt metaphors. Use simple language with precise definitions.
- Ground facts in that block's cited source. No unsupported general knowledge.
- Do not put `**...**` or `==...==` emphasis inside visible choices. Do not use shuffled labels such as `- ㄱ.`, `- ①`, or answers like `답: ㄱ, ㄴ`.
- Do not join multiple answer/explanation sentences with ` / `. Use separate lines.

## O/X And Choice Review

- Use prevention-pharmacy style only when a question actually has choices/OX review. Do not force it onto short-answer-only courses.
- For choice/OX cards, put review lines in `[보기해설]` or the revealed answer area, not inside visible choices.
- Correct items: `O original correct sentence // short reason if needed`.
- Wrong items: `X original wrong sentence -> corrected sentence or corrected mapping. Short reason if needed`.
- Correct wrong choices only when useful for traps around pairings, mechanisms, exceptions, or categories.
- If a course is mostly short answer, prefer definition/mechanism/explanation cards over artificial multiple choice.

## Verification

Before reporting completion, verify:
- final Markdown exists in `문제 데이터`;
- assets exist and every image link resolves;
- every block has `답:` and `출처:`;
- block count did not change unexpectedly during edits;
- no TODO/확인 필요, broken choices, answer-label references, visible-choice emphasis, or slash-joined explanations remain.
