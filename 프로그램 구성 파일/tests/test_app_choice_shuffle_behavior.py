from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_TSX = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "App.tsx"
SESSION_HOOK = PROJECT_ROOT / "프로그램 구성 파일" / "src" / "hooks" / "useStudySession.ts"


def test_answer_reveal_does_not_reshuffle_choices_but_answer_hide_does():
    source = APP_TSX.read_text(encoding="utf-8")

    assert "if (question && !nextShowAnswer)" in source
    assert "session.currentQuestion ? `${session.currentQuestion.id}:${choiceShuffleSeed}` : ''" in source
    assert "session.showAnswer && session.currentQuestion ? `${session.currentQuestion.id}:${choiceShuffleSeed}` : ''" not in source


def test_manual_reload_button_refetches_current_studyset_without_reshuffling():
    source = APP_TSX.read_text(encoding="utf-8")

    assert "RefreshCw" in source
    assert "const reloadStudySet = useCallback" in source
    assert "await fetchStudySet(selectedStudySetId)" in source
    assert "문제 데이터 다시 읽기" in source
    assert "lastSeenRef.current = session.currentQuestion?.id ?? ''" in source
    assert "setRefreshingStudySet(false)" in source
    reload_section = source[source.index("const reloadStudySet = useCallback") : source.index("const saveMarkdown = useCallback")]
    assert "session.reshuffle()" not in reload_section


def test_changed_question_set_reconciles_existing_order_and_cursor():
    source = SESSION_HOOK.read_text(encoding="utf-8")

    assert "function reconcileOrder" in source
    assert "const preservedOrderIds = order.orderIds.filter" in source
    assert "const currentQuestionId = order.orderIds[order.cursor]" in source
    assert "const preservedCursor = currentQuestionId ? nextOrderIds.indexOf(currentQuestionId) : -1" in source
    assert "cursor: preservedCursor >= 0 ? preservedCursor : fallbackCursor" in source
