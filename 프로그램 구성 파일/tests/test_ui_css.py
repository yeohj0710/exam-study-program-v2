from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSS_PATH = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "App.css"


def test_inline_answer_source_has_spacing_from_answer_text():
    css = CSS_PATH.read_text(encoding="utf-8")
    selector = ".answer-section .markdown-content .markdown-source"
    start = css.index(selector)
    block = css[start : css.index("}", start)]

    assert "margin-top:" in block
    assert "padding-top:" in block
