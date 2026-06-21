from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_PROMPT = PROJECT_ROOT / "문제 데이터 작성 프롬프트.txt"
DETAIL_PROMPT = PROJECT_ROOT / "프로그램 구성 파일" / "prompts" / "시험공부자료 MD 작성 상세 프롬프트.txt"
OPERATING_PROMPT = PROJECT_ROOT / "프로그램 구성 파일" / "prompts" / "시험공부자료 MD 작성 운영 원칙.txt"
SELECTION_PROMPT = PROJECT_ROOT / "프로그램 구성 파일" / "prompts" / "시험공부자료 MD 작성 선별 전략.txt"
FAILURE_CASE_PROMPT = PROJECT_ROOT / "프로그램 구성 파일" / "prompts" / "시험공부자료 MD 작성 실패사례와 처리원칙.txt"
QUALITY_RULEBOOK = PROJECT_ROOT / "프로그램 구성 파일" / "prompts" / "시험공부자료 MD 작성 품질 규정집.txt"


def test_core_prompt_fits_codex_goal_limit():
    prompt = CORE_PROMPT.read_text(encoding="utf-8")

    assert len(prompt) <= 2000


def test_core_prompt_keeps_critical_generation_rules():
    prompt = CORE_PROMPT.read_text(encoding="utf-8")

    required_phrases = [
        "상세 프롬프트",
        "운영 원칙",
        "선별 전략",
        "실패사례와 처리원칙",
        "마지막 줄의 시험범위 자료 경로 안의 파일만",
        "기출은 원문 복원",
        "출처 페이지/슬라이드 원본 이미지를 답안 맨 아래",
        "PPT/PDF/슬라이드는 텍스트 추출만 믿지 말고",
        "출처:",
        "시험범위 자료 경로:",
    ]
    for phrase in required_phrases:
        assert phrase in prompt


def test_prompt_points_to_failure_cases_file():
    prompt = CORE_PROMPT.read_text(encoding="utf-8")
    detail = DETAIL_PROMPT.read_text(encoding="utf-8")
    failure_cases = FAILURE_CASE_PROMPT.read_text(encoding="utf-8")
    selection = SELECTION_PROMPT.read_text(encoding="utf-8")

    assert FAILURE_CASE_PROMPT.name in prompt
    assert FAILURE_CASE_PROMPT.name in detail
    assert OPERATING_PROMPT.name in prompt
    assert OPERATING_PROMPT.name in detail
    assert SELECTION_PROMPT.name in prompt
    assert SELECTION_PROMPT.name in detail
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

    selection_required_phrases = [
        "예방약학_기말고사_문제.md",
        "바이오의약품학_기말고사_문제.md",
        "의약화학_기말고사_문제.md",
        "기출문제 공지.txt",
        "요약자료",
        "공지의 장별 문항 수와 유형",
        "객관식 O 항목 설명은 반복이면 지운다",
        "`[해설]`은 표준 라벨로 허용",
    ]
    for phrase in selection_required_phrases:
        assert phrase in selection


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
