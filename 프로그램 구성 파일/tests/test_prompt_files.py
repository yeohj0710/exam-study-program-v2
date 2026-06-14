from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_PROMPT = PROJECT_ROOT / "시험공부자료 MD 작성 프롬프트.txt"
DETAIL_PROMPT = PROJECT_ROOT / "프로그램 구성 파일" / "prompts" / "시험공부자료 MD 작성 상세 프롬프트.txt"
FAILURE_CASE_PROMPT = PROJECT_ROOT / "프로그램 구성 파일" / "prompts" / "시험공부자료 MD 작성 실패사례와 처리원칙.txt"
QUALITY_RULEBOOK = PROJECT_ROOT / "프로그램 구성 파일" / "prompts" / "시험공부자료 MD 작성 품질 규정집.txt"


def test_core_prompt_fits_codex_goal_limit():
    prompt = CORE_PROMPT.read_text(encoding="utf-8")

    assert len(prompt) <= 4000


def test_core_prompt_keeps_critical_generation_rules():
    prompt = CORE_PROMPT.read_text(encoding="utf-8")

    required_phrases = [
        "상세 프롬프트",
        "실패사례와 처리원칙",
        "마지막 줄에 붙여넣은 시험범위 자료 경로 안의 파일만",
        "기출문제는 최대한 원문 그대로 복원",
        "단답형 문제로 바꾸지 않는다",
        "답은 번호가 아니라 보기 내용",
        "보기 앞 원문 번호는 제거",
        "빨간 숫자, 정답 표시, 채점 흔적",
        "복원 안 된 보기",
        "누락된 선지는 자료를 참고해 맞거나 틀린 완성 선지",
        "계산 문제는 원본 표와 수치 조건",
        "복합형 조합 보기",
        "답안/풀이에도 `ㄱ은`, `ㄴ은`, `ㄷ은`",
        "보기에는 `**...**` 또는 `==...==` 강조",
        "답안/풀이의 여러 정답이나 설명 문장을 ` / `",
        "출처 페이지/슬라이드 원본 이미지를 답안 맨 아래",
        "PPT/PDF/슬라이드는 텍스트 추출만 믿지 말고",
        "표, 비교표, 계산표",
        "출처:",
        "시험범위 자료 경로:",
    ]
    for phrase in required_phrases:
        assert phrase in prompt


def test_prompt_points_to_failure_cases_file():
    prompt = CORE_PROMPT.read_text(encoding="utf-8")
    detail = DETAIL_PROMPT.read_text(encoding="utf-8")
    failure_cases = FAILURE_CASE_PROMPT.read_text(encoding="utf-8")

    assert FAILURE_CASE_PROMPT.name in prompt
    assert FAILURE_CASE_PROMPT.name in detail
    assert QUALITY_RULEBOOK.name in failure_cases

    required_phrases = [
        "기출 복원 실패",
        "보기 번호와 조합 보기",
        "표/비교표/계산표",
        "출처와 출처 이미지",
        "레퍼런스 활용",
        "답안/풀이에 `ㄴ은`, `ㄷ은`",
        "보기 안에 `**...**` 또는 `==...==` 강조",
        "여러 정답이나 풀이 문장을 ` / `",
        "G:\\내 드라이브\\여형준님\\21 6-1",
        "특정 과목 전용 규칙이 아니라",
    ]
    for phrase in required_phrases:
        assert phrase in failure_cases


def test_prompts_reference_quality_rulebook():
    prompt = CORE_PROMPT.read_text(encoding="utf-8")
    detail = DETAIL_PROMPT.read_text(encoding="utf-8")
    rulebook = QUALITY_RULEBOOK.read_text(encoding="utf-8")

    assert QUALITY_RULEBOOK.name in prompt
    assert QUALITY_RULEBOOK.name in detail

    required_phrases = [
        "셔플 보기 독립성",
        "`- ㄱ.`",
        "`답: ㄱ, ㄴ`",
        "`ㄴ은`",
        "보기 강조 금지",
        "`**...**`",
        "`==...==`",
        "답안 줄바꿈",
        "` / `",
        "문제 수 보존",
    ]
    for phrase in required_phrases:
        assert phrase in rulebook
