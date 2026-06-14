from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_TSX = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "App.tsx"


def test_answer_reveal_does_not_reshuffle_choices_but_answer_hide_does():
    source = APP_TSX.read_text(encoding="utf-8")

    assert "if (question && !nextShowAnswer)" in source
    assert "session.currentQuestion ? `${session.currentQuestion.id}:${choiceShuffleSeed}` : ''" in source
    assert "session.showAnswer && session.currentQuestion ? `${session.currentQuestion.id}:${choiceShuffleSeed}` : ''" not in source
