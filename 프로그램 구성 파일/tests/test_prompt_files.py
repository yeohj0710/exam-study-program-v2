from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_PROMPT = PROJECT_ROOT / "시험공부자료 MD 작성 프롬프트.txt"


def test_core_prompt_fits_codex_goal_limit():
    prompt = CORE_PROMPT.read_text(encoding="utf-8")

    assert len(prompt) <= 4000


def test_core_prompt_keeps_critical_generation_rules():
    prompt = CORE_PROMPT.read_text(encoding="utf-8")

    required_phrases = [
        "상세 프롬프트",
        "마지막 줄에 붙여넣은 시험범위 자료 경로 안의 파일만",
        "기출문제는 최대한 원문 그대로 복원",
        "단답형 문제로 바꾸지 않는다",
        "출처 페이지/슬라이드 원본 이미지를 답안 맨 아래",
        "PPT/PDF/슬라이드는 텍스트 추출만 믿지 말고",
        "표, 비교표, 계산표",
        "출처:",
        "시험범위 자료 경로:",
    ]
    for phrase in required_phrases:
        assert phrase in prompt
