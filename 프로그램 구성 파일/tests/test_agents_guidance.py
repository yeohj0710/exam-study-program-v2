from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTS = PROJECT_ROOT / "AGENTS.md"


def test_agents_routes_exam_study_markdown_work_to_prompt_files():
    agents = AGENTS.read_text(encoding="utf-8")

    required_phrases = [
        "Exam Study Markdown/question-data work",
        "문제 데이터 작성 프롬프트.txt",
        "시험공부자료 MD 작성 상세 프롬프트.txt",
        "시험공부자료 MD 작성 실패사례와 처리원칙.txt",
        "시험공부자료 MD 작성 품질 규정집.txt",
        "시험공부자료 MD 작성 운영 원칙.txt",
        "시험공부자료 MD 작성 선별 전략.txt",
        "문제 데이터",
        "`답: ㄱ, ㄴ`",
        "`**...**`",
        "` / `",
        "Do not inflate question count",
        "Use prevention-pharmacy style only when a question actually has choices/OX review",
        "If a course is mostly short answer",
        "no TODO/확인 필요",
    ]
    for phrase in required_phrases:
        assert phrase in agents


def test_agents_uses_current_v2_paths_and_remote():
    agents = AGENTS.read_text(encoding="utf-8")

    assert "C:\\dev\\exam-study-program-v2" in agents
    assert "https://github.com/yeohj0710/exam-study-program-v2.git" in agents
    assert "C:\\dev\\exam-study-program`" not in agents
    assert "https://github.com/yeohj0710/studyforge.git" not in agents
