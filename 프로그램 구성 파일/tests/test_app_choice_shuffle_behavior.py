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
    assert "문제 데이터 다시 읽기 (F5)" in source
    assert "const currentQuestionId = session.currentQuestion?.id ?? ''" in source
    assert "lastSeenRef.current = currentQuestionId" in source
    assert "setRefreshingStudySet(false)" in source
    reload_section = source[source.index("const reloadStudySet = useCallback") : source.index("const saveMarkdown = useCallback")]
    assert "session.reshuffle()" not in reload_section


def test_right_study_controls_have_keyboard_shortcuts_and_tooltips():
    source = APP_TSX.read_text(encoding="utf-8")

    assert 'title="문제 목록 (L)"' in source
    assert 'title="PDF 내보내기 (P)"' in source
    assert 'title="문제 데이터 다시 읽기 (F5)"' in source
    assert 'title="문제 섞기 (S)"' in source
    assert "if (key === 'l' && session.total) {" in source
    assert "setShowQuestionPicker(true)" in source
    assert "if (key === 'p' && selectedStudySetId && !exportingPdf) {" in source
    assert "void exportPdf()" in source
    assert "if (key === 'f5' && selectedStudySetId && !refreshingStudySet) {" in source
    assert "void reloadStudySet()" in source
    assert "if (key === 's' && session.total) {" in source
    assert "setConfirmShuffle(true)" in source


def test_default_theme_is_dark_until_user_session_overrides_it():
    source = APP_TSX.read_text(encoding="utf-8")

    default_theme_section = source[source.index("function defaultTheme") : source.index("function readSession")]

    assert "return 'dark'" in default_theme_section
    assert "prefers-color-scheme" not in default_theme_section
    assert "const [themeMode, setThemeMode] = useState<ThemeMode>(initialSession.themeMode ?? defaultTheme())" in source


def test_glare_controls_render_only_in_dark_mode():
    source = APP_TSX.read_text(encoding="utf-8")
    rail_section = source[source.index("rail={") : source.index("setPanel={")]

    assert "{themeMode === 'dark' && (" in rail_section
    assert 'aria-label="밝기 조절"' in rail_section
    assert "changeGlareLevel(-glareStep)" in rail_section
    assert "changeGlareLevel(glareStep)" in rail_section
    assert "event.altKey && themeMode === 'dark' && key === '['" in source
    assert "event.altKey && themeMode === 'dark' && key === ']'" in source


def test_shutdown_control_is_replaced_by_passive_fullscreen_hint():
    source = APP_TSX.read_text(encoding="utf-8")

    assert "Power" not in source
    assert "shutdownApp" not in source
    assert "confirmShutdown" not in source
    assert "setConfirmShutdown" not in source
    assert 'className="rail-fullscreen-hint"' in source
    assert 'title="전체화면 (F11)"' in source
    assert "<Maximize2" in source


def test_pdf_export_saves_dirty_markdown_before_downloading():
    source = APP_TSX.read_text(encoding="utf-8")

    assert "Download" in source
    assert "exportStudySetPdf" in source
    assert "const [exportingPdf, setExportingPdf] = useState(false)" in source
    assert "const exportPdf = useCallback" in source
    export_section = source[source.index("const exportPdf = useCallback") : source.index("const uploadImage = useCallback")]
    assert "if (dirty) {" in export_section
    assert "await saveMarkdown()" in export_section
    assert "await exportStudySetPdf(selectedStudySetId)" in export_section
    assert "downloadBlob(blob, filename)" in export_section


def test_changed_question_set_reconciles_existing_order_and_cursor():
    source = SESSION_HOOK.read_text(encoding="utf-8")

    assert "function reconcileOrder" in source
    assert "const preservedOrderIds = order.orderIds.filter" in source
    assert "const currentQuestionId = order.orderIds[order.cursor]" in source
    assert "const preservedCursor = currentQuestionId ? nextOrderIds.indexOf(currentQuestionId) : -1" in source
    assert "cursor: preservedCursor >= 0 ? preservedCursor : fallbackCursor" in source
