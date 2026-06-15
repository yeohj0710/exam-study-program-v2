from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTS = PROJECT_ROOT / "AGENTS.md"


def test_agents_routes_exam_study_markdown_work_to_prompt_files():
    agents = AGENTS.read_text(encoding="utf-8")

    required_phrases = [
        "Exam Study Markdown Data Work",
        "시험공부자료 MD 작성 프롬프트.txt",
        "시험공부자료 MD 작성 상세 프롬프트.txt",
        "시험공부자료 MD 작성 실패사례와 처리원칙.txt",
        "시험공부자료 MD 작성 품질 규정집.txt",
        "문제 데이터",
        "screenshot-based study-card fixes",
        "Search `문제 데이터\\*.md`",
        "Preserve the existing problem count",
        "`답: ㄱ, ㄴ`",
        "`ㄴ은`",
        "`**...**`",
        "` / `",
        "Memorization-oriented Markdown cleanup",
        "one idea per line",
        "Do not turn answers into long paragraphs",
        "Remove visual clutter before finishing",
    ]
    for phrase in required_phrases:
        assert phrase in agents


def test_agents_uses_current_v2_paths_and_remote():
    agents = AGENTS.read_text(encoding="utf-8")

    assert "C:\\dev\\exam-study-program-v2" in agents
    assert "https://github.com/yeohj0710/exam-study-program-v2.git" in agents
    assert "C:\\dev\\exam-study-program`" not in agents
    assert "https://github.com/yeohj0710/studyforge.git" not in agents
