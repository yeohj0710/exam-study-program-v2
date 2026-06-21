from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_CONTENT = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "components" / "MarkdownContent.tsx"


def test_choice_prefixes_are_stripped_before_rendering():
    source = MARKDOWN_CONTENT.read_text(encoding="utf-8")

    assert "CHOICE_PREFIX_RE" in source
    assert "ANSWER_PREFIX_RE" in source
    assert "stripChoicePrefix" in source
    assert "stripAnswerPrefix" in source
    assert "stripChoicePrefix(firstLine.slice(2).trim())" in source
    assert "stripLeadingAnswerPrefix" in source
    assert "\\u2460-\\u2473" in source
    assert "\\d{1,2}" in source


def test_markdown_images_retry_transient_load_failures():
    source = MARKDOWN_CONTENT.read_text(encoding="utf-8")

    assert "maxImageLoadRetries" in source
    assert "retryDelayMs" in source
    assert "setRetryToken((value) => value + 1)" in source
    assert "setFailed(false)" in source
    assert "window.setTimeout" in source
    assert "window.clearTimeout" in source


def test_failed_markdown_image_can_be_retried_manually():
    source = MARKDOWN_CONTENT.read_text(encoding="utf-8")

    assert 'type="button"' in source
    assert 'className="image-retry-button"' in source
    assert "다시 불러오기" in source


def test_answer_mode_has_dedicated_explanation_label_rendering():
    source = MARKDOWN_CONTENT.read_text(encoding="utf-8")

    assert "answerMode" in source
    assert "ANSWER_CALLOUT_RE" in source
    assert "markdown-answer-label" in source
    assert "stripLeadingAnswerPrefix={stripLeadingAnswerPrefix}" not in source


def test_answer_mode_groups_hierarchy_without_using_choice_cards():
    source = MARKDOWN_CONTENT.read_text(encoding="utf-8")

    assert "isAnswerHeading" in source
    assert "isAnswerBullet" in source
    assert "renderAnswerGroup" in source
    assert "markdown-answer-group" in source
    assert "answerMode && (isAnswerHeading(lines[index]) || isAnswerBullet(lines[index]))" in source


def test_question_view_has_dedicated_answer_label_before_answer_body():
    question_view = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "components" / "QuestionView.tsx"
    source = question_view.read_text(encoding="utf-8")

    assert "markdown-answer-label primary" in source
    assert "<span>답</span>" in source
