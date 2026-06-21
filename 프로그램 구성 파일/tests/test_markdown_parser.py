from studyforge.markdown_parser import insert_missing_question_ids, parse_studyset_markdown


def test_parse_simple_hash_question_with_choices_and_answer():
    markdown = """# What starts a question?
<!-- sf:id: sample-001 -->

Pick one.

- # Question
- ## Q. Question
- ### Answer

답: # Question
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=None)

    assert result.title == "sample-final"
    assert result.issues == []
    assert len(result.questions) == 1
    question = result.questions[0]
    assert question.id == "sample-001"
    assert question.title == "Question 1"
    assert question.prompt_markdown.startswith("What starts a question?\n\nPick one.")
    assert "- # Question" in question.prompt_markdown
    assert question.answer_markdown == "# Question"
    assert question.note_markdown == ""


def test_parse_short_answer_without_choices():
    markdown = """# Source file format?
<!-- sf:id: sample-001 -->

답: Markdown
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=None)

    assert len(result.questions) == 1
    assert result.questions[0].title == "Question 1"
    assert result.questions[0].prompt_markdown == "Source file format?"
    assert result.questions[0].answer_markdown == "Markdown"


def test_source_lines_are_separated_from_answer_markdown():
    markdown = """# 문제
<!-- sf:id: source-question -->

표도상구균 독소형 식중독은 어느 쪽에 가까운가?

답: 독소형 식중독
출처: C:\\자료\\예방약학.pdf p.12 + C:\\자료\\기출.pdf p.3
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=None)

    question = result.questions[0]
    assert question.answer_markdown == "독소형 식중독"
    assert question.source_markdown == "출처: C:\\자료\\예방약학.pdf p.12 + C:\\자료\\기출.pdf p.3"


def test_wrapped_source_lines_stay_out_of_answer_markdown():
    markdown = """# 문제
<!-- sf:id: wrapped-source -->

자료 출처가 줄바꿈된 문제

답: 정답
출처: G:\\내 드라이브\\과목\\6.1.
 영양과 건강.pdf p.24
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=None)

    question = result.questions[0]
    assert question.answer_markdown == "정답"
    assert question.source_markdown == "출처: G:\\내 드라이브\\과목\\6.1.\n 영양과 건강.pdf p.24"


def test_source_page_image_after_source_stays_in_source_markdown():
    markdown = """# 문제
<!-- sf:id: source-image -->

기출 원문 문제

답: 정답
출처: G:\\내 드라이브\\과목\\2023 기출.pdf p.4

![출처 페이지](assets/sample-final/source-001.png)
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=None)

    question = result.questions[0]
    assert question.answer_markdown == "정답"
    assert question.source_markdown == (
        "출처: G:\\내 드라이브\\과목\\2023 기출.pdf p.4\n\n"
        "![출처 페이지](assets/sample-final/source-001.png)"
    )


def test_answer_background_and_choice_explanations_are_structured_sections():
    markdown = """# 문제
<!-- sf:id: structured-explanation -->

옳은 것을 모두 고르시오.

- 맞는 보기
- 틀린 보기

답: 맞는 보기

[배경설명]
처음 보는 사람도 이해할 수 있도록 용어와 전체 맥락을 설명한다.

[보기해설]
O 맞는 보기 // 왜 맞는지 쉽게 설명한다.
X 틀린 보기 -> 고친 보기. 왜 틀렸는지 설명한다.

출처: C:\\자료\\강의.pdf p.12
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=None)

    question = result.questions[0]
    assert question.answer_markdown == "맞는 보기"
    assert question.explanation_markdown == "처음 보는 사람도 이해할 수 있도록 용어와 전체 맥락을 설명한다."
    assert question.choice_explanation_markdown == (
        "O 맞는 보기 // 왜 맞는지 쉽게 설명한다.\n"
        "X 틀린 보기 -> 고친 보기. 왜 틀렸는지 설명한다."
    )
    assert question.source_markdown == "출처: C:\\자료\\강의.pdf p.12"


def test_insert_missing_question_ids_places_comment_after_hash_heading():
    markdown = """# First question

답: first

# Existing id question
<!-- sf:id: existing-id -->

답: second
"""

    updated = insert_missing_question_ids(markdown, studyset_id="sample-final")

    assert "# First question\n<!-- sf:id: sample-final-001 -->" in updated
    assert updated.count("<!-- sf:id: existing-id -->") == 1


def test_duplicate_question_ids_are_errors_and_second_question_is_marked():
    markdown = """# First
<!-- sf:id: duplicate-id -->

답: first

# Second
<!-- sf:id: duplicate-id -->

답: second
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=None)

    duplicate_issues = [issue for issue in result.issues if issue.code == "duplicate_question_id"]
    assert len(duplicate_issues) == 1
    assert duplicate_issues[0].severity == "error"
    assert duplicate_issues[0].question_id == "duplicate-id"
    assert result.questions[1].issues == duplicate_issues


def test_missing_answer_is_warning():
    markdown = """# No answer
<!-- sf:id: no-answer -->

Prompt only.
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=None)

    assert result.questions[0].answer_markdown == ""
    missing_answer_issues = [issue for issue in result.issues if issue.code == "missing_answer"]
    assert len(missing_answer_issues) == 1
    assert missing_answer_issues[0].severity == "warning"


def test_missing_relative_image_asset_is_warning(tmp_path):
    markdown = """# Image question
<!-- sf:id: image-question -->

![diagram](assets/sample-final/missing.png)

답: diagram
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=tmp_path)

    assert result.questions[0].asset_paths == ["assets/sample-final/missing.png"]
    missing_asset_issues = [issue for issue in result.issues if issue.code == "missing_asset"]
    assert len(missing_asset_issues) == 1
    assert missing_asset_issues[0].severity == "warning"
    assert missing_asset_issues[0].question_id == "image-question"


def test_absolute_image_link_is_warning(tmp_path):
    markdown = """# Absolute image
<!-- sf:id: absolute-image -->

![diagram](C:\\Users\\hjyeo\\image.png)

답: diagram
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=tmp_path)

    absolute_issues = [issue for issue in result.issues if issue.code == "absolute_asset_path"]
    assert len(absolute_issues) == 1
    assert absolute_issues[0].severity == "warning"
    assert absolute_issues[0].question_id == "absolute-image"


def test_labelled_shuffle_choices_are_warnings():
    markdown = """# 문제
<!-- sf:id: labelled-choices -->

옳은 것을 모두 고르시오.

- ㄱ. 맞는 설명
- ㄴ. 틀린 설명

답: ㄱ
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=None)

    codes = {issue.code for issue in result.issues}
    assert "choice_label_in_shuffled_option" in codes
    assert "label_only_answer_for_shuffled_choices" in codes


def test_choice_emphasis_in_shuffled_choices_is_warning():
    markdown = """# 문제
<!-- sf:id: emphasized-choice -->

옳은 것을 모두 고르시오.

- 정답 보기의 **핵심 단서**
- 평범한 오답

답: 정답 보기의 핵심 단서
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=None)

    codes = {issue.code for issue in result.issues}
    assert "choice_emphasis_in_shuffled_option" in codes


def test_answer_label_reference_for_shuffled_choices_is_warning():
    markdown = """# 문제
<!-- sf:id: labelled-answer-reference -->

옳은 것을 모두 고르시오.

- 실제 정답 보기
- 실제 오답 보기

답: 실제 정답 보기
ㄴ은 실제 오답 보기 설명이다.
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=None)

    codes = {issue.code for issue in result.issues}
    assert "answer_label_reference_for_shuffled_choices" in codes


def test_answer_inline_slash_separator_is_warning():
    markdown = """# 문제
<!-- sf:id: slash-separated-answer -->

옳은 것을 모두 고르시오.

- 첫 번째 정답 보기
- 두 번째 정답 보기

답: 첫 번째 정답 보기이다. / 두 번째 정답 보기이다.
"""

    result = parse_studyset_markdown(markdown, studyset_id="sample-final", asset_root=None)

    codes = {issue.code for issue in result.issues}
    assert "answer_inline_slash_separator" in codes
