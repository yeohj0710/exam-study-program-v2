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


def test_right_study_controls_are_minimal_until_hovered():
    css = CSS_PATH.read_text(encoding="utf-8")

    def blocks_for(selector: str) -> list[str]:
        blocks = []
        start = 0
        while True:
            try:
                start = css.index(selector, start)
            except ValueError:
                return blocks
            end = css.index("}", start)
            blocks.append(css[start:end])
            start = end + 1

    progress_start = css.index(".progress-pill {")
    progress_block = css[progress_start : css.index("}", progress_start)]
    composer_start = css.index(".composer-button {")
    composer_block = css[composer_start : css.index("}", composer_start)]
    side_blocks = blocks_for(".side-control-button {")

    assert "border-color: transparent;" in progress_block
    assert "background: transparent;" in progress_block
    assert any("border-color: transparent;" in block for block in side_blocks)
    assert any("background: transparent;" in block for block in side_blocks)
    assert "border: 1px solid transparent;" in composer_block
    assert "background: transparent;" in composer_block
    assert "box-shadow: none;" in composer_block
    assert "backdrop-filter: none;" in composer_block

    hover_selectors = [
        ".progress-button:hover,\n.progress-button:focus-visible",
        ".side-control-button:hover,\n.side-control-button:focus-visible",
        ".composer-button:hover,\n.composer-button:focus-visible",
    ]
    for selector in hover_selectors:
        start = css.index(selector)
        block = css[start : css.index("}", start)]
        assert "border-color: var(--border);" in block
        assert "background: var(--surface);" in block


def test_edge_rails_peek_until_hover_or_focus():
    css = CSS_PATH.read_text(encoding="utf-8")

    app_start = css.index(".app-rail {")
    app_block = css[app_start : css.index("}", app_start)]
    controls_start = css.index(".study-control-rail {")
    controls_block = css[controls_start : css.index("}", controls_start)]

    assert "--edge-rail-width:" in css
    assert "--edge-rail-peek:" in css
    assert "left: 0;" in app_block
    assert "right: 0;" in controls_block
    assert "width: var(--edge-rail-width);" in app_block
    assert "width: var(--edge-rail-width);" in controls_block
    assert "transform: translateX(calc(-1 * (var(--edge-rail-width) - var(--edge-rail-peek))));" in app_block
    assert "transform: translateX(calc(var(--edge-rail-width) - var(--edge-rail-peek)));" in controls_block

    for selector in [
        ".app-rail:hover,\n.app-rail:focus-within",
        ".study-control-rail:hover,\n.study-control-rail:focus-within",
    ]:
        start = css.index(selector)
        block = css[start : css.index("}", start)]
        assert "transform: translateX(0);" in block

    assert ".app-rail::before,\n.study-control-rail::before" in css


def test_right_rail_uses_left_edge_spacing_when_side_panel_is_open():
    css = CSS_PATH.read_text(encoding="utf-8")
    side_start = css.index(".final-shell.with-side-panel .study-control-rail")
    side_block = css[side_start : css.index("}", side_start)]

    assert "right: var(--side-panel-width);" in side_block
    assert "right: calc(var(--side-panel-width) + 20px);" not in side_block
