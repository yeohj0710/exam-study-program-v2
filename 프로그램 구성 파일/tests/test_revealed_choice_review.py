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
