import { useCallback, useEffect, useRef, useState } from 'react'
import type { MouseEvent as ReactMouseEvent } from 'react'
import {
  Check,
  ChevronRight,
  Edit3,
  Eye,
  EyeOff,
  FileText,
  Info,
  Moon,
  Power,
  RotateCcw,
  Shuffle,
  Sun,
  SunDim,
  SunMedium,
  ZoomIn,
  ZoomOut,
} from 'lucide-react'
import {
  fetchStudySet,
  fetchStudySets,
  fetchValidation,
  patchQuestionProgress,
  restoreQuestionProgress,
  saveStudySet,
  shutdownApp,
  uploadStudySetAsset,
} from './api'
import './App.css'
import { MarkdownEditor } from './components/MarkdownEditor'
import { QuestionView } from './components/QuestionView'
import { StudySetPanel } from './components/StudySetPanel'
import { StudyWorkspace } from './components/StudyWorkspace'
import { ValidationPanel } from './components/ValidationPanel'
import { useStudySession } from './hooks/useStudySession'
import type { QuestionProgress, StudySet, StudySetPayload, ThemeMode, ValidationReport } from './types'

const sessionKey = 'exam-study.session.v1'

type SessionState = {
  selectedStudySetId: string
  showSetPanel: boolean
  showEditor: boolean
  showInfo: boolean
  themeMode: ThemeMode
  setPanelWidth: number
  sidePanelWidth: number
  textScale: number
  glareLevel: number
}

function defaultTheme(): ThemeMode {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function readSession(): Partial<SessionState> {
  try {
    const raw = window.localStorage.getItem(sessionKey)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as Partial<SessionState>
    return {
      selectedStudySetId: typeof parsed.selectedStudySetId === 'string' ? parsed.selectedStudySetId : '',
      showSetPanel: typeof parsed.showSetPanel === 'boolean' ? parsed.showSetPanel : false,
      showEditor: typeof parsed.showEditor === 'boolean' ? parsed.showEditor : false,
      showInfo: typeof parsed.showInfo === 'boolean' ? parsed.showInfo : false,
      themeMode: parsed.themeMode === 'dark' || parsed.themeMode === 'light' ? parsed.themeMode : undefined,
      setPanelWidth: typeof parsed.setPanelWidth === 'number' ? parsed.setPanelWidth : 280,
      sidePanelWidth: typeof parsed.sidePanelWidth === 'number' ? parsed.sidePanelWidth : 380,
      textScale: typeof parsed.textScale === 'number' ? parsed.textScale : 0.9,
      glareLevel: typeof parsed.glareLevel === 'number' ? parsed.glareLevel : 0.46,
    }
  } catch {
    return {}
  }
}

function writeSession(state: SessionState) {
  window.localStorage.setItem(sessionKey, JSON.stringify(state))
}

async function fileToBase64(file: File) {
  const buffer = await file.arrayBuffer()
  let binary = ''
  const bytes = new Uint8Array(buffer)
  for (let index = 0; index < bytes.length; index += 1) {
    binary += String.fromCharCode(bytes[index])
  }
  return window.btoa(binary)
}

function applyProgress(payload: StudySetPayload | null, questionId: string, progress: QuestionProgress) {
  if (!payload) return payload
  return {
    ...payload,
    questions: payload.questions.map((question) => (question.id === questionId ? { ...question, progress } : question)),
  }
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function App() {
  const [initialSession] = useState<Partial<SessionState>>(() => readSession())
  const [studysets, setStudysets] = useState<StudySet[]>([])
  const [selectedStudySetId, setSelectedStudySetId] = useState(initialSession.selectedStudySetId ?? '')
  const [payload, setPayload] = useState<StudySetPayload | null>(null)
  const [markdownDraft, setMarkdownDraft] = useState('')
  const [savedMarkdown, setSavedMarkdown] = useState('')
  const [validation, setValidation] = useState<ValidationReport | null>(null)
  const [search, setSearch] = useState('')
  const [, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showSetPanel, setShowSetPanel] = useState(initialSession.showSetPanel ?? false)
  const [showEditor, setShowEditor] = useState(initialSession.showEditor ?? false)
  const [showInfo, setShowInfo] = useState(initialSession.showInfo ?? false)
  const [themeMode, setThemeMode] = useState<ThemeMode>(initialSession.themeMode ?? defaultTheme())
  const [setPanelWidth, setSetPanelWidth] = useState(initialSession.setPanelWidth ?? 280)
  const [sidePanelWidth, setSidePanelWidth] = useState(initialSession.sidePanelWidth ?? 380)
  const [textScale, setTextScale] = useState(initialSession.textScale ?? 0.9)
  const [glareLevel, setGlareLevel] = useState(initialSession.glareLevel ?? 0.46)
  const [choiceShuffleSeed, setChoiceShuffleSeed] = useState(0)
  const [confirmShutdown, setConfirmShutdown] = useState(false)
  const [showQuestionPicker, setShowQuestionPicker] = useState(false)
  const lastSeenRef = useRef('')

  const session = useStudySession(selectedStudySetId, payload?.questions ?? [])
  const dirty = markdownDraft !== savedMarkdown
  const showSidePanel = showEditor || showInfo

  const refreshValidation = useCallback(async () => {
    try {
      setValidation(await fetchValidation())
    } catch {
      setValidation(null)
    }
  }, [])

  const loadStudySet = useCallback(
    async (studysetId: string) => {
      const nextPayload = await fetchStudySet(studysetId)
      setPayload(nextPayload)
      setMarkdownDraft(nextPayload.markdown)
      setSavedMarkdown(nextPayload.markdown)
      setSelectedStudySetId(studysetId)
      lastSeenRef.current = ''
      await refreshValidation()
    },
    [refreshValidation],
  )

  const initializeStudySets = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const nextStudysets = await fetchStudySets()
      setStudysets(nextStudysets)
      const preferred =
        nextStudysets.find((item) => item.id === initialSession.selectedStudySetId)?.id ?? nextStudysets[0]?.id ?? ''
      if (preferred) {
        await loadStudySet(preferred)
      } else {
        setPayload(null)
        setMarkdownDraft('')
        setSavedMarkdown('')
        await refreshValidation()
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '문제 데이터를 불러오지 못했습니다.')
    } finally {
      setLoading(false)
    }
  }, [initialSession.selectedStudySetId, loadStudySet, refreshValidation])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void initializeStudySets()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [initializeStudySets])

  useEffect(() => {
    writeSession({
      selectedStudySetId,
      showSetPanel,
      showEditor,
      showInfo,
      themeMode,
      setPanelWidth,
      sidePanelWidth,
      textScale,
      glareLevel,
    })
  }, [
    selectedStudySetId,
    showSetPanel,
    showEditor,
    showInfo,
    themeMode,
    setPanelWidth,
    sidePanelWidth,
    textScale,
    glareLevel,
  ])

  useEffect(() => {
    const question = session.currentQuestion
    if (!question || lastSeenRef.current === question.id) return
    lastSeenRef.current = question.id
    void patchQuestionProgress(question.id, 'seen').then((progress) => {
      setPayload((current) => applyProgress(current, question.id, progress))
    })
  }, [session.currentQuestion])

  const handleSelectStudySet = useCallback(
    (studysetId: string) => {
      if (dirty && !window.confirm('저장하지 않은 수정이 있습니다. 이동할까요?')) return
      void loadStudySet(studysetId)
    },
    [dirty, loadStudySet],
  )

  const saveMarkdown = useCallback(async () => {
    if (!selectedStudySetId) return
    const nextPayload = await saveStudySet(selectedStudySetId, markdownDraft)
    setPayload(nextPayload)
    setMarkdownDraft(nextPayload.markdown)
    setSavedMarkdown(nextPayload.markdown)
    setStudysets(await fetchStudySets())
    await refreshValidation()
  }, [markdownDraft, refreshValidation, selectedStudySetId])

  const uploadImage = useCallback(
    async (file: File) => {
      if (!selectedStudySetId) throw new Error('선택된 문제 데이터가 없습니다.')
      if (!file.type.startsWith('image/')) throw new Error('이미지 파일만 추가할 수 있습니다.')
      const contentBase64 = await fileToBase64(file)
      const saved = await uploadStudySetAsset(selectedStudySetId, contentBase64, file.type, file.name || 'image')
      await refreshValidation()
      return saved.markdown
    },
    [refreshValidation, selectedStudySetId],
  )

  const toggleAnswer = useCallback(async () => {
    const question = session.currentQuestion
    const nextShowAnswer = !session.showAnswer
    session.setShowAnswer(nextShowAnswer)
    if (question && nextShowAnswer) {
      setChoiceShuffleSeed((value) => value + 1)
      const progress = await patchQuestionProgress(question.id, 'reveal')
      setPayload((current) => applyProgress(current, question.id, progress))
    }
  }, [session])

  const memorizeCurrent = useCallback(async () => {
    const question = session.currentQuestion
    if (!question) return
    const progress = await patchQuestionProgress(question.id, 'memorized')
    setPayload((current) => applyProgress(current, question.id, progress))
  }, [session.currentQuestion])

  const restoreCurrent = useCallback(async () => {
    const question = session.currentQuestion
    if (!question) return
    const progress = await restoreQuestionProgress(question.id)
    setPayload((current) => applyProgress(current, question.id, progress))
  }, [session.currentQuestion])

  const changeTextScale = useCallback((delta: number) => {
    setTextScale((value) => Math.round(clamp(value + delta, 0.76, 1.14) * 100) / 100)
  }, [])

  const changeGlareLevel = useCallback((delta: number) => {
    setGlareLevel((value) => Math.round(clamp(value + delta, 0, 0.92) * 100) / 100)
  }, [])

  const beginSetPanelResize = useCallback(
    (event: ReactMouseEvent<HTMLDivElement>) => {
      event.preventDefault()
      const startX = event.clientX
      const startWidth = setPanelWidth
      function onMove(moveEvent: MouseEvent) {
        setSetPanelWidth(clamp(startWidth + moveEvent.clientX - startX, 220, 520))
      }
      function onUp() {
        window.removeEventListener('mousemove', onMove)
        window.removeEventListener('mouseup', onUp)
      }
      window.addEventListener('mousemove', onMove)
      window.addEventListener('mouseup', onUp)
    },
    [setPanelWidth],
  )

  const beginSidePanelResize = useCallback(
    (event: ReactMouseEvent<HTMLDivElement>) => {
      event.preventDefault()
      const startX = event.clientX
      const startWidth = sidePanelWidth
      function onMove(moveEvent: MouseEvent) {
        setSidePanelWidth(clamp(startWidth - (moveEvent.clientX - startX), 300, 640))
      }
      function onUp() {
        window.removeEventListener('mousemove', onMove)
        window.removeEventListener('mouseup', onUp)
      }
      window.addEventListener('mousemove', onMove)
      window.addEventListener('mouseup', onUp)
    },
    [sidePanelWidth],
  )

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const target = event.target
      const isTyping = target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement
      const key = event.key.toLowerCase()
      const modifier = event.ctrlKey || event.metaKey

      if (modifier && key === 'b') {
        event.preventDefault()
        setShowSetPanel((value) => !value)
        return
      }
      if (modifier && key === 'e') {
        event.preventDefault()
        setShowEditor((value) => !value)
        setShowInfo(false)
        return
      }
      if (modifier && key === 'i') {
        event.preventDefault()
        setShowInfo((value) => !value)
        setShowEditor(false)
        return
      }
      if (modifier && (key === '-' || key === '_')) {
        event.preventDefault()
        changeTextScale(-0.08)
        return
      }
      if (modifier && (key === '=' || key === '+')) {
        event.preventDefault()
        changeTextScale(0.08)
        return
      }
      if (modifier && key === '0') {
        event.preventDefault()
        setTextScale(0.9)
        return
      }
      if (event.altKey && key === '[') {
        event.preventDefault()
        changeGlareLevel(-0.1)
        return
      }
      if (event.altKey && key === ']') {
        event.preventDefault()
        changeGlareLevel(0.1)
        return
      }
      if (key === 'escape' && confirmShutdown) {
        event.preventDefault()
        setConfirmShutdown(false)
        return
      }
      if (key === 'escape' && showQuestionPicker) {
        event.preventDefault()
        setShowQuestionPicker(false)
        return
      }
      if (isTyping) return
      if (key === '/') {
        event.preventDefault()
        setShowSetPanel(true)
        window.setTimeout(() => document.querySelector<HTMLInputElement>('[data-studyset-search]')?.focus(), 0)
        return
      }
      if (key === 'j' || key === ' ') {
        event.preventDefault()
        void toggleAnswer()
        return
      }
      if (key === 'k' || key === 'arrowright') {
        event.preventDefault()
        session.nextQuestion()
        return
      }
      if (key === '1') {
        event.preventDefault()
        void memorizeCurrent()
        return
      }
      if (key === 'r' && session.currentQuestion?.progress.memorized) {
        event.preventDefault()
        void restoreCurrent()
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [
    changeGlareLevel,
    changeTextScale,
    confirmShutdown,
    memorizeCurrent,
    restoreCurrent,
    session,
    showQuestionPicker,
    toggleAnswer,
  ])

  const progressText = session.total ? `${session.safeCursor + 1} / ${session.total}` : '0 / 0'
  const issues = payload?.issues ?? []

  return (
    <StudyWorkspace
      themeMode={themeMode}
      showSetPanel={showSetPanel}
      showSidePanel={showSidePanel}
      setPanelWidth={setPanelWidth}
      sidePanelWidth={sidePanelWidth}
      textScale={textScale}
      glareLevel={glareLevel}
      onSetPanelResizeStart={beginSetPanelResize}
      onSidePanelResizeStart={beginSidePanelResize}
      rail={
        <aside className="app-rail" aria-label="주 메뉴">
          <div className="brand-button" aria-label="Exam Study">
            ES
          </div>
          <button
            type="button"
            className="rail-button"
            title="문제 데이터 (Ctrl+B)"
            onClick={() => setShowSetPanel((value) => !value)}
          >
            <FileText size={19} />
          </button>
          <button
            type="button"
            className={showEditor ? 'rail-button active' : 'rail-button'}
            title="Markdown (Ctrl+E)"
            onClick={() => {
              setShowEditor((value) => !value)
              setShowInfo(false)
            }}
          >
            <Edit3 size={19} />
          </button>
          <button
            type="button"
            className={showInfo ? 'rail-button active' : 'rail-button'}
            title="검증 (Ctrl+I)"
            onClick={() => {
              setShowInfo((value) => !value)
              setShowEditor(false)
            }}
          >
            <Info size={19} />
          </button>
          <div className="rail-tool-pair" aria-label="글자 크기">
            <button
              type="button"
              className="rail-button compact"
              title={`글자 작게 (Ctrl+-) · ${Math.round(textScale * 100)}%`}
              onClick={() => changeTextScale(-0.08)}
            >
              <ZoomOut size={17} />
            </button>
            <button
              type="button"
              className="rail-button compact"
              title={`글자 크게 (Ctrl+=) · ${Math.round(textScale * 100)}%`}
              onClick={() => changeTextScale(0.08)}
            >
              <ZoomIn size={17} />
            </button>
          </div>
          <div className="rail-tool-pair" aria-label="눈부심 조절">
            <button
              type="button"
              className="rail-button compact"
              title={`밝기 + (Alt+[) · ${Math.round(glareLevel * 100)}%`}
              onClick={() => changeGlareLevel(-0.1)}
            >
              <span className="rail-mark">+</span>
              <SunMedium size={17} />
            </button>
            <button
              type="button"
              className="rail-button compact"
              title={`밝기 - (Alt+]) · ${Math.round(glareLevel * 100)}%`}
              onClick={() => changeGlareLevel(0.1)}
            >
              <span className="rail-mark">-</span>
              <SunDim size={17} />
            </button>
          </div>
          <button
            type="button"
            className="rail-button bottom"
            title={themeMode === 'dark' ? '라이트 모드' : '다크 모드'}
            onClick={() => setThemeMode((value) => (value === 'dark' ? 'light' : 'dark'))}
          >
            {themeMode === 'dark' ? <Sun size={19} /> : <Moon size={19} />}
          </button>
          <button
            type="button"
            className="rail-button danger"
            title="종료"
            onClick={() => {
              setConfirmShutdown(true)
            }}
          >
            <Power size={19} />
          </button>
        </aside>
      }
      setPanel={
        <StudySetPanel
          studysets={studysets}
          selectedId={selectedStudySetId}
          search={search}
          onSearch={setSearch}
          onSelect={handleSelectStudySet}
        />
      }
      sidePanel={
        showEditor ? (
          <MarkdownEditor
            markdown={markdownDraft}
            dirty={dirty}
            onChange={setMarkdownDraft}
            onSave={saveMarkdown}
            onUploadImage={uploadImage}
          />
        ) : (
          <ValidationPanel validation={validation} localIssues={issues} />
        )
      }
    >
      <aside className="study-control-rail" aria-label="학습 조작">
        <section className="study-set-summary">
          <button
            type="button"
            className="progress-pill progress-button"
            title="문제 목록"
            onClick={() => setShowQuestionPicker(true)}
            disabled={!session.total}
          >
            {progressText}
          </button>
          <button type="button" className="side-control-button" title="문제 섞기" onClick={session.reshuffle} disabled={!session.total}>
            <Shuffle size={18} />
          </button>
        </section>

        <footer className="study-composer">
          <button
            type="button"
            className="composer-button"
            title={session.showAnswer ? '정답 숨기기 (J)' : '정답 보기 (J)'}
            onClick={() => void toggleAnswer()}
            disabled={!session.currentQuestion}
          >
            {session.showAnswer ? <EyeOff size={18} /> : <Eye size={18} />}
            <kbd>J</kbd>
          </button>
          <button type="button" className="composer-button" title="다음 문제 (K)" onClick={session.nextQuestion} disabled={!session.currentQuestion}>
            <ChevronRight size={20} />
            <kbd>K</kbd>
          </button>
          {session.currentQuestion?.progress.memorized ? (
            <button type="button" className="composer-button restore" title="암기 완료 복구 (R)" onClick={() => void restoreCurrent()}>
              <RotateCcw size={18} />
              <kbd>R</kbd>
            </button>
          ) : (
            <button
              type="button"
              className="composer-button memorize"
              title="암기 완료 (1)"
              onClick={() => void memorizeCurrent()}
              disabled={!session.currentQuestion}
            >
              <Check size={18} />
              <kbd>1</kbd>
            </button>
          )}
        </footer>
      </aside>

      {error && <p className="error-banner">{error}</p>}

      <QuestionView
        question={session.currentQuestion}
        showAnswer={session.showAnswer}
        choiceShuffleKey={
          session.showAnswer && session.currentQuestion ? `${session.currentQuestion.id}:${choiceShuffleSeed}` : ''
        }
      />

      {showQuestionPicker && (
        <div className="picker-layer" role="presentation" onMouseDown={() => setShowQuestionPicker(false)}>
          <section
            className="question-picker"
            role="dialog"
            aria-modal="true"
            aria-label="문제 목록"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <header>
              <strong>문제 이동</strong>
              <button type="button" onClick={() => setShowQuestionPicker(false)}>
                닫기
              </button>
            </header>
            <div className="question-picker-grid">
              {session.orderedQuestions.map((question, index) => (
                <button
                  key={question.id}
                  type="button"
                  className={[
                    'question-picker-item',
                    question.id === session.currentQuestion?.id ? 'active' : '',
                    question.progress.memorized ? 'memorized' : '',
                    question.issues.length > 0 ? 'issue' : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                  title={question.title}
                  onClick={() => {
                    session.goToQuestion(question.id)
                    setShowQuestionPicker(false)
                  }}
                >
                  {index + 1}
                </button>
              ))}
            </div>
          </section>
        </div>
      )}

      {confirmShutdown && (
        <div className="confirm-layer" role="presentation" onMouseDown={() => setConfirmShutdown(false)}>
          <section
            className="confirm-dialog"
            role="dialog"
            aria-modal="true"
            aria-label="프로그램 종료 확인"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <p>프로그램을 종료할까요?</p>
            <div>
              <button type="button" className="composer-button" onClick={() => setConfirmShutdown(false)}>
                취소
              </button>
              <button type="button" className="composer-button danger-action" onClick={() => void shutdownApp()}>
                종료
              </button>
            </div>
          </section>
        </div>
      )}
    </StudyWorkspace>
  )
}

export default App
