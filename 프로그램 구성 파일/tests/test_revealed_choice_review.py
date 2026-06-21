from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUESTION_VIEW = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "components" / "QuestionView.tsx"
CSS_PATH = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "App.css"


def test_revealed_prompt_groups_plain_choices_and_answer_uses_review_cards():
    source = QUESTION_VIEW.read_text(encoding="utf-8")

    assert "function RevealedPrompt" in source
    assert "function RevealedChoiceReview" in source
    assert "function RevealedAnswer" in source
    assert "classifyChoicesForReveal" in source
    assert "isNegativeQuestion" in source
    assert "correctChoices" in source
    assert "incorrectChoices" in source
    assert "groupedPromptMarkdown" in source
    assert "shuffleChoicesKey={choiceShuffleKey}" in source
    assert '<RevealedPrompt promptMarkdown={question.prompt_markdown} answerMarkdown={question.answer_markdown} />' in source
    assert '<RevealedAnswer promptMarkdown={question.prompt_markdown} answerMarkdown={question.answer_markdown} />' in source


def test_revealed_choice_review_marks_correct_and_incorrect_without_dividers():
    css = CSS_PATH.read_text(encoding="utf-8")

    for selector in [
        ".revealed-choice-list",
        ".revealed-choice.correct",
        ".revealed-choice.incorrect",
        ".revealed-choice-badge",
        ".revealed-choice-correction",
    ]:
        assert selector in css

    correct_start = css.index(".revealed-choice.correct")
    correct_block = css[correct_start : css.index("}", correct_start)]
    incorrect_start = css.index(".revealed-choice.incorrect")
    incorrect_block = css[incorrect_start : css.index("}", incorrect_start)]
    list_start = css.index(".revealed-choice-list")
    list_block = css[list_start : css.index("}", list_start)]

    assert "--choice-review-color: var(--answer-correct);" in correct_block
    assert "--choice-review-color: var(--answer-incorrect);" in incorrect_block
    assert "gap:" in list_block
    assert "border-top:" not in list_block


def test_revealed_prompt_keeps_same_question_to_choice_breathing_room():
    source = QUESTION_VIEW.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")

    assert 'className="revealed-prompt"' in source

    selector = ".revealed-prompt .markdown-choice:first-of-type"
    start = css.index(selector)
    block = css[start : css.index("}", start)]

    assert "margin-top:" in block


def test_answer_reveal_toggle_does_not_force_scroll_position():
    source = QUESTION_VIEW.read_text(encoding="utf-8")

    assert "scrollIntoView" not in source
    assert "answerRef" not in source


def test_question_view_renders_structured_explanation_sections():
    source = QUESTION_VIEW.read_text(encoding="utf-8")
    types = (PROJECT_ROOT / "프로그램 구성 파일" / "src" / "types.ts").read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")

    assert "explanation_markdown" in types
    assert "choice_explanation_markdown" in types
    assert "function StructuredAnswer" in source
    assert "question.explanation_markdown" in source
    assert "question.choice_explanation_markdown" in source
    assert "배경 설명" in source
    assert "보기 해설" in source
    assert ".explanation-section" in css
    assert ".choice-explanation-section" in css


def test_explicit_choice_explanations_replace_duplicate_answer_label_and_render_first():
    source = QUESTION_VIEW.read_text(encoding="utf-8")

    structured_start = source.index("function StructuredAnswer")
    choice_explanation = source.index("<StructuredChoiceExplanation", structured_start)
    background_explanation = source.index('<section className="explanation-section"', structured_start)

    assert "function shouldShowPrimaryAnswerLabel" in source
    assert "const shouldHideDirectAnswer" in source
    assert "{!shouldHideDirectAnswer && (" in source
    assert "{shouldShowPrimaryAnswerLabel(question) && (" in source
    assert choice_explanation < background_explanation


def test_structured_choice_explanations_only_render_explicit_review_items():
    source = QUESTION_VIEW.read_text(encoding="utf-8")

    assert "explicitOnly" in source
    structured_start = source.index("function StructuredChoiceExplanation")
    structured_block = source[structured_start : source.index("function StructuredAnswer", structured_start)]

    assert "explicitOnly: true" in structured_block
