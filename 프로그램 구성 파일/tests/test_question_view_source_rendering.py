from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUESTION_VIEW = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "components" / "QuestionView.tsx"


def test_source_references_render_evidence_markdown_below_source_buttons():
    source = QUESTION_VIEW.read_text(encoding="utf-8")

    assert "sourceEvidenceMarkdown" in source
    assert 'className="source-evidence"' in source
    assert "<MarkdownContent markdown={evidenceMarkdown}" in source
