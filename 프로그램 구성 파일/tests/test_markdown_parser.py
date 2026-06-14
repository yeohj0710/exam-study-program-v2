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
