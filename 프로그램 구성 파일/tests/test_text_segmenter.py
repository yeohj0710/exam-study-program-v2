from studyforge.text_segmenter import segment_text


def test_segments_korean_question_answer_blocks():
    text = """
SAR를 정의하시오.
화합물의 화학 구조와 생물학적 활성 사이의 상관관계
전합성과 반합성을 각각 정의하시오.
전합성: 간단한 출발물질에서 목표 화합물을 만드는 합성
반합성: 천연물을 변형해 만드는 합성
"""

    segments = segment_text(text)

    assert len(segments) == 2
    assert segments[0].front_text == "SAR를 정의하시오."
    assert "상관관계" in segments[0].back_text
    assert segments[0].confidence > 0.7


def test_arrow_correction_keeps_choices_on_front():
    text = """
다음 중 옳지 않은 것을 바르게 고치시오.
수소 결합은 HBD와 HBA 사이에서 일어난다.
유기 분자 안의 F 원자는 항상 강한 수소 결합 수용자이다.
소수성 상호작용은 엔트로피 증가와 관련된다.
유기 분자 안의 F 원자는 항상 강한 수소 결합 수용자이다.
→ 보통 강한 HBA로 보기 어렵다.
"""

    segment = segment_text(text)[0]

    assert "소수성 상호작용" in segment.front_text
    assert segment.back_text.startswith("유기 분자")
    assert "→" in segment.back_text
    assert segment.confidence > 0.8


def test_fallback_for_unstructured_page():
    segments = segment_text("제목\n내용 한 줄\n내용 두 줄")

    assert len(segments) == 1
    assert "page_fallback" in segments[0].flags
    assert segments[0].confidence < 0.55


def test_english_q_headers_start_new_segments():
    text = """
Q5 Single Answer
Which one of the following is a regression task?
A. Email spam classification
B. Tomorrow's temperature
Answer: B.
Q6 Single Answer
Which relation holds?
Answer: A.
"""

    segments = segment_text(text)

    assert len(segments) == 2
    assert segments[0].front_text.startswith("Q5 Single Answer")
    assert "Which one" in segments[0].front_text
    assert "Answer: B." in segments[0].back_text
    assert "Q6" not in segments[0].raw_text
    assert segments[1].front_text.startswith("Q6 Single Answer")


def test_spaced_solution_marker_starts_back_side():
    text = """
Which one is a regression task?
A. Spam classification
B. Temperature prediction
S O L U T I O N
Answer: B.
"""

    segment = segment_text(text)[0]

    assert "S O L U T I O N" not in segment.front_text
    assert segment.back_text.startswith("S O L U T I O N")


def test_skips_question_range_outline_rows():
    text = """
Part A · Foundations & Representation
Q1-Q4
Part B · Tasks, Linear Algebra & Trees
Q5-Q8
Part C · Segmentation, Classification & Distance
Q9-Q11
Part D · Activations & Losses
Q12-Q14
"""

    assert segment_text(text) == []
