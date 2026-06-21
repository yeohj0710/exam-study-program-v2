from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUESTION_VIEW = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "components" / "QuestionView.tsx"


def test_source_references_render_evidence_markdown_below_source_buttons():
    source = QUESTION_VIEW.read_text(encoding="utf-8")

    assert "sourceEvidenceMarkdown" in source
    assert 'className="source-evidence"' in source
    assert "<MarkdownContent markdown={evidenceMarkdown}" in source


def test_plain_topic_lines_after_source_render_as_evidence_not_source_button_text():
    source = QUESTION_VIEW.read_text(encoding="utf-8")

    assert "SOURCE_CONTINUATION_RE" in source
    assert "SOURCE_CONTINUATION_RE.test(line)" in source
    assert "evidenceLines.push(line)" in source


def test_relative_source_references_open_matching_evidence_image():
    source = QUESTION_VIEW.read_text(encoding="utf-8")

    assert "sourceReferenceFallbackUrl" in source
    assert "isLocalFileReference" in source
    assert "source-p0*" in source
    assert "if (fallbackUrl) {" in source
    assert "window.open(fallbackUrl, '_blank', 'noopener,noreferrer')" in source
