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
    assert "border-top:" not in block


def test_source_section_has_no_divider_line():
    css = CSS_PATH.read_text(encoding="utf-8")
    selector = ".source-section"
    start = css.index(selector)
    block = css[start : css.index("}", start)]

    assert "margin:" in block
    assert "border-top:" not in block


def test_source_evidence_images_are_large_enough_to_read():
    css = CSS_PATH.read_text(encoding="utf-8")
    section_start = css.index(".source-evidence {")
    section_block = css[section_start : css.index("}", section_start)]
    figure_start = css.index(".source-evidence .markdown-image {")
    figure_block = css[figure_start : css.index("}", figure_start)]
    image_start = css.index(".source-evidence .markdown-image img {")
    image_block = css[image_start : css.index("}", image_start)]

    assert "1200px" in section_block
    assert "width: 100%;" in figure_block
    assert "max-width: none;" in figure_block
    assert "width: 100%;" in image_block
    assert "max-height: none;" in image_block


def test_markdown_text_wraps_by_words_before_breaking_long_tokens():
    css = CSS_PATH.read_text(encoding="utf-8")
    selector = ".markdown-content p"
    start = css.index(selector)
    block = css[start : css.index("}", start)]

    assert "overflow-wrap: break-word;" in block
    assert "word-break: keep-all;" in block
    assert "line-break: strict;" in block
    assert "overflow-wrap: anywhere;" not in block
