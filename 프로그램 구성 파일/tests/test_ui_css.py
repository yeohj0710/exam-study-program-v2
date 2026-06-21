from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSS_PATH = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "App.css"
INDEX_CSS_PATH = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "index.css"


def compact_media_css(css: str) -> str:
    start = css.find("@media (max-width: 920px)")
    return "" if start == -1 else css[start:]


def optional_block(css: str, selector: str) -> str:
    if selector not in css:
        return ""
    start = css.index(selector)
    return css[start : css.index("}", start)]


def test_inline_answer_source_has_spacing_from_answer_text():
    css = CSS_PATH.read_text(encoding="utf-8")
    selector = ".answer-section .markdown-content .markdown-source"
    start = css.index(selector)
    block = css[start : css.index("}", start)]

    assert "margin-top:" in block
    assert "padding-top:" in block
    assert "border-top:" not in block


def test_answer_hierarchy_has_answer_only_bullet_layout():
    css = CSS_PATH.read_text(encoding="utf-8")
    content_selector = ".answer-section .markdown-content"
    content_start = css.index(content_selector)
    content_block = css[content_start : css.index("}", content_start)]
    group_selector = ".answer-section .markdown-answer-group"
    group_start = css.index(group_selector)
    group_block = css[group_start : css.index("}", group_start)]
    h3_selector = ".answer-section .markdown-answer-group h3"
    bullet_selector = ".answer-section .markdown-content .markdown-answer-bullet"
    bullet_start = css.index(bullet_selector)
    bullet_block = css[bullet_start : css.index("}", bullet_start)]
    bullet_text_selector = ".answer-section .markdown-content .markdown-answer-bullet > span:last-child"
    bullet_text_start = css.index(bullet_text_selector)
    bullet_text_block = css[bullet_text_start : css.index("}", bullet_text_start)]

    h3_start = css.index(h3_selector)
    h3_block = css[h3_start : css.index("}", h3_start)]

    assert "text-align: center;" in content_block
    assert "margin: 16px auto 10px;" in group_block
    assert "justify-items: center;" in group_block
    assert "text-align: center;" in group_block
    assert "border-bottom:" in h3_block
    assert "text-align: center;" in h3_block
    assert "font-size:" in h3_block
    assert "display: flex;" in bullet_block
    assert "justify-content: center;" in bullet_block
    assert "margin: 5px auto;" in bullet_block
    assert "text-align: center;" in bullet_block
    assert "text-align: center;" in bullet_text_block
    assert "text-align: left;" not in group_block
    assert "text-align: left;" not in bullet_block
    assert ".markdown-choice" not in bullet_block


def test_answer_callout_label_stays_centered_inside_answer_markdown():
    css = CSS_PATH.read_text(encoding="utf-8")
    selector = ".answer-section .markdown-content .markdown-answer-label"
    start = css.index(selector)
    block = css[start : css.index("}", start)]

    assert "margin-left: auto;" in block
    assert "margin-right: auto;" in block
    assert "text-align: center;" in block


def test_source_section_has_no_divider_line():
    css = CSS_PATH.read_text(encoding="utf-8")
    selector = ".source-section"
    start = css.index(selector)
    block = css[start : css.index("}", start)]

    assert "margin:" in block
    assert "border-top:" not in block


def test_first_choice_explanation_does_not_create_second_answer_divider():
    css = CSS_PATH.read_text(encoding="utf-8")
    selector = ".answer-section > .choice-explanation-section:first-child"
    start = css.index(selector)
    block = css[start : css.index("}", start)]

    assert "margin-top: 0;" in block
    assert "padding-top: 0;" in block
    assert "border-top: 0;" in block


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


def test_right_controls_are_workspace_anchored_not_viewport_fixed():
    css = CSS_PATH.read_text(encoding="utf-8")

    controls_start = css.index(".study-control-rail {")
    controls_block = css[controls_start : css.index("}", controls_start)]
    open_start = css.index(".final-shell.with-side-panel .study-control-rail {")
    open_block = css[open_start : css.index("}", open_start)]

    assert "position: absolute;" in controls_block
    assert "position: fixed;" not in controls_block
    assert "left: 0;" in open_block
    assert "right: auto;" in open_block
    assert "right: calc(var(--side-panel-width) - var(--rail-space));" not in open_block


def test_left_rail_blends_into_open_set_panel_without_inner_divider():
    css = CSS_PATH.read_text(encoding="utf-8")
    selector = ".final-shell.with-set-panel .app-rail {"
    start = css.index(selector)
    block = css[start : css.index("}", start)]
    before_selector = ".final-shell.with-set-panel .app-rail::before {"
    before_start = css.index(before_selector)
    before_block = css[before_start : css.index("}", before_start)]

    assert "top: 0;" in block
    assert "bottom: 0;" in block
    assert "width: var(--rail-space);" in block
    assert "background: var(--surface);" in block
    assert "border-right:" not in block
    assert "opacity: 1;" in block
    assert "transform: none;" in block
    assert "display: none;" in before_block


def test_right_rail_blends_inside_open_side_panel_without_inner_divider():
    css = CSS_PATH.read_text(encoding="utf-8")
    side_start = css.index(".final-shell.with-side-panel .study-control-rail {")
    side_block = css[side_start : css.index("}", side_start)]
    panel_selector = ".final-shell.with-side-panel .editor-panel,\n.final-shell.with-side-panel .validation-panel {"
    panel_start = css.index(panel_selector)
    panel_block = css[panel_start : css.index("}", panel_start)]
    before_selector = ".final-shell.with-side-panel .study-control-rail::before {"
    before_start = css.index(before_selector)
    before_block = css[before_start : css.index("}", before_start)]

    assert "left: 0;" in side_block
    assert "right: auto;" in side_block
    assert "width: var(--rail-space);" in side_block
    assert "background: var(--surface);" in side_block
    assert "border-right:" not in side_block
    assert "opacity: 1;" in side_block
    assert "transform: none;" in side_block
    assert "padding-left: calc(var(--rail-space) + 22px);" in panel_block
    assert "display: none;" in before_block


def test_compact_width_keeps_three_column_shell_when_panels_are_open():
    css = CSS_PATH.read_text(encoding="utf-8")
    media_css = compact_media_css(css)

    assert "grid-template-columns: minmax(0, 1fr);" not in media_css
    assert "--study-main-min-width:" in css
    assert (
        "width: max(100vw, calc(var(--rail-space) + var(--set-panel-width) + "
        "var(--study-main-min-width) + var(--side-panel-width)));"
    ) in css


def test_compact_width_can_scroll_to_preserved_side_columns():
    css = CSS_PATH.read_text(encoding="utf-8")
    index_css = INDEX_CSS_PATH.read_text(encoding="utf-8")

    assert "max-width: 100vw;" not in css
    assert "overflow-x: auto;" in index_css
    assert "overflow-y: hidden;" in index_css


def test_compact_width_keeps_side_panels_in_normal_grid_flow():
    css = CSS_PATH.read_text(encoding="utf-8")
    media_css = compact_media_css(css)
    panel_block = optional_block(media_css, ".set-panel-shell,\n  .side-panel-shell {")

    assert "position: fixed;" not in panel_block


def test_compact_width_keeps_right_rail_visible_with_open_side_panel():
    css = CSS_PATH.read_text(encoding="utf-8")
    media_css = compact_media_css(css)
    side_block = optional_block(media_css, ".final-shell.with-side-panel .study-control-rail {")

    assert "display: none;" not in side_block
