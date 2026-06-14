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
