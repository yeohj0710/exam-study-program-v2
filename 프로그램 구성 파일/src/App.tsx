import { type CSSProperties, useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  Check,
  ChevronRight,
  Eye,
  FileText,
  Image as ImageIcon,
  List,
  Moon,
  Play,
  Power,
  RefreshCw,
  RotateCcw,
  Shuffle,
  SlidersHorizontal,
  Sun,
  ZoomIn,
  ZoomOut,
} from 'lucide-react'
import './App.css'

type AssetRole = 'front_image' | 'choice_image' | 'answer_image' | 'source_page' | 'page_crop'
type StudyRating = 'new' | 'again' | 'hard' | 'good' | 'easy'
type FilterMode = 'all' | 'due' | 'new' | 'low' | 'needs_work' | 'mastered'
type ThemeMode = 'light' | 'dark'

type Asset = {
  id: string
  role: AssetRole
  path: string
  source_path?: string
  width?: number
  height?: number
}

type StudyCard = {
  id: string
  subject: string
  deck: string
  source: 'pdf' | 'legacy_capture' | 'manual' | 'page_fallback'
  source_path: string
  source_page?: number
  source_item?: string
  front_text: string
  back_text: string
  confidence: number
  review_flags: string[]
  review_status: 'unreviewed' | 'approved' | 'needs_work'
  review_note: string
  study_seen_count: number
  study_correct_count: number
  study_wrong_count: number
  study_streak: number
  study_interval_days: number
  study_due_at: number
  study_last_studied_at?: number
  study_last_rating: StudyRating
  assets: Asset[]
  tags: string[]
}

type Library = {
  cards: StudyCard[]
  report: {
    warnings: string[]
    cards_created: number
    low_confidence_cards: number
    pdfs_imported: number
    legacy_decks_imported: number
  }
}

type ValidationReport = {
  ok: boolean
  source_count: number
  card_count: number
  asset_count: number
  missing_asset_count: number
  missing_source_count: number
  duplicate_card_count: number
  orphan_review_count: number
  orphan_progress_count: number
  pdf_cards_missing_front_count: number
  pdf_cards_missing_crop_count: number
  legacy_cards_missing_front_count: number
  legacy_cards_missing_answer_count: number
  issues: Array<{ severity: 'error' | 'warning'; code: string; message: string }>
}

type PersistedSession = {
  selectedDeck: string
  filterMode: FilterMode
  order: string[]
  cursor: number
  showDecks: boolean
  showInspector: boolean
  showQuestionList: boolean
  showFilters: boolean
  viewScale: number
  themeMode: ThemeMode
}

const defaultPdfPaths = ''
const defaultLegacyRoot =
  'G:\\내 드라이브\\여형준님\\21 6-1\\족보 암기 프로그램\\중간고사'
const sessionStorageKey = 'exam-memory-app.session.v1'
const minViewScale = 0.8
const maxViewScale = 1.2
const viewScaleStep = 0.05

const filterLabels: Record<FilterMode, string> = {
  all: '남은 카드',
  due: '다시 볼 카드',
  new: '신규',
  low: '검수',
  needs_work: '보류',
  mastered: '외운 카드',
}

function isFilterMode(value: unknown): value is FilterMode {
  return typeof value === 'string' && value in filterLabels
}

function clampViewScale(value: number) {
  return Math.min(maxViewScale, Math.max(minViewScale, Math.round(value * 100) / 100))
}

function defaultViewScale() {
  if (typeof window === 'undefined') return 1
  if (window.innerWidth <= 760) return 0.9
  if (window.innerWidth <= 1180) return 0.95
  return 1
}

function defaultThemeMode(): ThemeMode {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function isThemeMode(value: unknown): value is ThemeMode {
  return value === 'light' || value === 'dark'
}

function readSessionState(): Partial<PersistedSession> {
  if (typeof window === 'undefined') return {}
  try {
    const raw = window.localStorage.getItem(sessionStorageKey)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as Partial<PersistedSession>
    return {
      selectedDeck: typeof parsed.selectedDeck === 'string' ? parsed.selectedDeck : '',
      filterMode: isFilterMode(parsed.filterMode) ? parsed.filterMode : 'all',
      order: Array.isArray(parsed.order) ? parsed.order.filter((item) => typeof item === 'string') : [],
      cursor: typeof parsed.cursor === 'number' && parsed.cursor >= 0 ? parsed.cursor : 0,
      showDecks: typeof parsed.showDecks === 'boolean' ? parsed.showDecks : true,
      showInspector: typeof parsed.showInspector === 'boolean' ? parsed.showInspector : false,
      showQuestionList: typeof parsed.showQuestionList === 'boolean' ? parsed.showQuestionList : false,
      showFilters: typeof parsed.showFilters === 'boolean' ? parsed.showFilters : false,
      viewScale: typeof parsed.viewScale === 'number' ? clampViewScale(parsed.viewScale) : undefined,
      themeMode: isThemeMode(parsed.themeMode) ? parsed.themeMode : undefined,
    }
  } catch {
    return {}
  }
}

function writeSessionState(state: PersistedSession) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(sessionStorageKey, JSON.stringify(state))
}

function assetUrl(asset: Asset) {
  if (/^[a-zA-Z]:\\/.test(asset.path)) return `/api/external-asset?path=${encodeURIComponent(asset.path)}`
  return `/assets/${asset.path.split('/').map(encodeURIComponent).join('/')}`
}

function previewAsset(card: StudyCard) {
  return (
    card.assets.find((asset) => asset.role === 'front_image') ??
    card.assets.find((asset) => asset.role === 'page_crop') ??
    card.assets.find((asset) => asset.role === 'source_page')
  )
}

function listPrimaryText(card: StudyCard) {
  if (card.source === 'legacy_capture') return card.deck
  return card.front_text || card.source_item || card.deck
}

function shuffleIds(cards: StudyCard[]) {
  return cards
    .map((card) => ({ card, sort: Math.random() }))
    .sort((a, b) => a.sort - b.sort)
    .map((item) => item.card.id)
}

function labelReviewStatus(status: StudyCard['review_status']) {
  if (status === 'approved') return '승인됨'
  if (status === 'needs_work') return '보류'
  return '미검수'
}

function labelRating(rating: StudyRating) {
  if (rating === 'again') return '다시 보기'
  if (rating === 'easy') return '외움'
  if (rating === 'hard' || rating === 'good') return '진행 중'
  return '처음'
}

function isMastered(card: StudyCard) {
  return card.study_last_rating === 'easy'
}

function selectExistingDeck(library: Library, current: string) {
  if (current && library.cards.some((card) => card.deck === current)) return current
  return library.cards[0]?.deck || ''
}

function App() {
  const savedSession = useMemo(readSessionState, [])
  const [library, setLibrary] = useState<Library | null>(null)
  const [validation, setValidation] = useState<ValidationReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedDeck, setSelectedDeck] = useState(savedSession.selectedDeck ?? '')
  const [order, setOrder] = useState<string[]>(savedSession.order ?? [])
  const [cursor, setCursor] = useState(savedSession.cursor ?? 0)
  const [showAnswer, setShowAnswer] = useState(false)
  const [filterMode, setFilterMode] = useState<FilterMode>(savedSession.filterMode ?? 'all')
  const [showDecks, setShowDecks] = useState(savedSession.showDecks ?? false)
  const [showInspector, setShowInspector] = useState(savedSession.showInspector ?? false)
  const [showQuestionList, setShowQuestionList] = useState(savedSession.showQuestionList ?? false)
  const [showFilters, setShowFilters] = useState(savedSession.showFilters ?? false)
  const [nowSeconds, setNowSeconds] = useState(0)
  const [pdfPaths, setPdfPaths] = useState(defaultPdfPaths)
  const [legacyRoot, setLegacyRoot] = useState(defaultLegacyRoot)
  const [importing, setImporting] = useState(false)
  const [stoppingServer, setStoppingServer] = useState(false)
  const [viewScale, setViewScale] = useState(savedSession.viewScale ?? defaultViewScale())
  const [themeMode, setThemeMode] = useState<ThemeMode>(savedSession.themeMode ?? defaultThemeMode())

  async function loadLibrary() {
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/library')
      if (!response.ok) throw new Error(response.status === 404 ? 'empty' : response.statusText)
      const payload = (await response.json()) as Library
      setLibrary(payload)
      setSelectedDeck((current) => selectExistingDeck(payload, current))
      await loadValidation()
    } catch (caught) {
      if (caught instanceof Error && caught.message !== 'empty') setError(caught.message)
      setLibrary(null)
    } finally {
      setLoading(false)
    }
  }

  async function loadValidation() {
    try {
      const response = await fetch('/api/validation')
      if (!response.ok) throw new Error(response.statusText)
      setValidation((await response.json()) as ValidationReport)
    } catch {
      setValidation(null)
    }
  }

  async function runImport() {
    setImporting(true)
    setError('')
    try {
      const response = await fetch('/api/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pdf_paths: pdfPaths
            .split(/\r?\n/)
            .map((path) => path.trim())
            .filter(Boolean),
          legacy_root: legacyRoot || null,
          include_lectures: false,
          copy_legacy_assets: true,
          render_pdf_pages: true,
        }),
      })
      if (!response.ok) throw new Error(await response.text())
      await loadLibrary()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Import failed')
    } finally {
      setImporting(false)
    }
  }

  async function shutdownApp() {
    if (!window.confirm('시험 자료 암기 프로그램을 종료할까요?')) return
    setStoppingServer(true)
    try {
      await fetch('/api/shutdown', { method: 'POST' })
      setError('프로그램이 종료되었습니다. 이 탭을 닫아도 됩니다.')
      window.setTimeout(() => window.close(), 300)
    } catch {
      setError('프로그램이 종료되었습니다. 이 탭을 닫아도 됩니다.')
    }
  }

  async function saveReview(card: StudyCard, status: StudyCard['review_status'], form?: HTMLFormElement) {
    const formData = form ? new FormData(form) : null
    const body = {
      status,
      front_text: formData ? String(formData.get('front_text') ?? card.front_text) : card.front_text,
      back_text: formData ? String(formData.get('back_text') ?? card.back_text) : card.back_text,
      note: formData ? String(formData.get('note') ?? '') : card.review_note,
    }
    const response = await fetch(`/api/cards/${card.id}/review`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!response.ok) throw new Error(await response.text())
    const payload = (await response.json()) as { card: StudyCard }
    setLibrary((current) => {
      if (!current) return current
      const cards = current.cards.map((item) => (item.id === payload.card.id ? payload.card : item))
      const unresolvedLowConfidence = cards.filter(
        (item) => item.confidence < 0.55 && item.review_status !== 'approved',
      ).length
      return {
        ...current,
        cards,
        report: { ...current.report, low_confidence_cards: unresolvedLowConfidence },
      }
    })
  }

  async function saveStudy(card: StudyCard, rating: 'easy') {
    const response = await fetch(`/api/cards/${card.id}/study`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating }),
    })
    if (!response.ok) throw new Error(await response.text())
    const payload = (await response.json()) as { card: StudyCard }
    setLibrary((current) => {
      if (!current) return current
      return {
        ...current,
        cards: current.cards.map((item) => (item.id === payload.card.id ? payload.card : item)),
      }
    })
    setShowAnswer(false)
  }

  async function restoreStudy(card: StudyCard) {
    const response = await fetch(`/api/cards/${card.id}/study`, { method: 'DELETE' })
    if (!response.ok) throw new Error(await response.text())
    const payload = (await response.json()) as { card: StudyCard }
    setLibrary((current) => {
      if (!current) return current
      return {
        ...current,
        cards: current.cards.map((item) => (item.id === payload.card.id ? payload.card : item)),
      }
    })
    setShowAnswer(false)
  }

  useEffect(() => {
    let cancelled = false
    fetch('/api/library')
      .then((response) => {
        if (!response.ok) throw new Error(response.status === 404 ? 'empty' : response.statusText)
        return response.json() as Promise<Library>
      })
      .then((payload) => {
        if (cancelled) return
        setLibrary(payload)
        setSelectedDeck((current) => selectExistingDeck(payload, current))
        window.setTimeout(() => void loadValidation(), 0)
      })
      .catch((caught) => {
        if (cancelled) return
        if (caught instanceof Error && caught.message !== 'empty') setError(caught.message)
        setLibrary(null)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const updateNow = () => setNowSeconds(Date.now() / 1000)
    const timeout = window.setTimeout(updateNow, 0)
    const interval = window.setInterval(updateNow, 60_000)
    return () => {
      window.clearTimeout(timeout)
      window.clearInterval(interval)
    }
  }, [])

  const decks = useMemo(() => {
    const grouped = new Map<string, StudyCard[]>()
    for (const card of library?.cards ?? []) {
      grouped.set(card.deck, [...(grouped.get(card.deck) ?? []), card])
    }
    return [...grouped.entries()].sort((a, b) => a[0].localeCompare(b[0], 'ko'))
  }, [library])

  const deckCards = useMemo(
    () => library?.cards.filter((card) => card.deck === selectedDeck) ?? [],
    [library, selectedDeck],
  )
  const deckStats = useMemo(
    () => ({
      all: deckCards.filter((card) => !isMastered(card)).length,
      due: deckCards.filter(
        (card) => !isMastered(card) && card.study_seen_count > 0 && card.study_due_at <= nowSeconds,
      ).length,
      new: deckCards.filter((card) => !isMastered(card) && card.study_seen_count === 0).length,
      low: deckCards.filter(
        (card) => !isMastered(card) && card.confidence < 0.55 && card.review_status !== 'approved',
      ).length,
      needs_work: deckCards.filter((card) => !isMastered(card) && card.review_status === 'needs_work').length,
      mastered: deckCards.filter((card) => isMastered(card)).length,
    }),
    [deckCards, nowSeconds],
  )
  const sessionCards = useMemo(
    () =>
      deckCards.filter((card) => {
        if (filterMode === 'mastered') return isMastered(card)
        if (isMastered(card)) return false
        if (filterMode === 'due') return card.study_seen_count > 0 && card.study_due_at <= nowSeconds
        if (filterMode === 'new') return card.study_seen_count === 0
        if (filterMode === 'low') return card.confidence < 0.55 && card.review_status !== 'approved'
        if (filterMode === 'needs_work') return card.review_status === 'needs_work'
        return true
      }),
    [deckCards, filterMode, nowSeconds],
  )

  const cardsById = useMemo(
    () => new Map(sessionCards.map((card) => [card.id, card])),
    [sessionCards],
  )
  const effectiveOrder = useMemo(() => {
    const isValidOrder = order.length === sessionCards.length && order.every((id) => cardsById.has(id))
    return isValidOrder ? order : sessionCards.map((card) => card.id)
  }, [cardsById, sessionCards, order])
  const orderForPersistence = useMemo(() => {
    const isValidOrder = order.length === sessionCards.length && order.every((id) => cardsById.has(id))
    return isValidOrder ? order : []
  }, [cardsById, sessionCards, order])
  const orderedCards = useMemo(
    () => effectiveOrder.map((id) => cardsById.get(id)).filter((card): card is StudyCard => Boolean(card)),
    [cardsById, effectiveOrder],
  )
  const safeCursor = Math.min(cursor, Math.max(sessionCards.length - 1, 0))
  const currentCard = cardsById.get(effectiveOrder[safeCursor]) ?? sessionCards[0]
  const progressText = sessionCards.length
    ? `${safeCursor + 1} / ${sessionCards.length}`
    : '0 / 0'

  useEffect(() => {
    writeSessionState({
      selectedDeck,
      filterMode,
      order: orderForPersistence,
      cursor: safeCursor,
      showDecks,
      showInspector,
      showQuestionList,
      showFilters,
      viewScale,
      themeMode,
    })
  }, [
    selectedDeck,
    filterMode,
    orderForPersistence,
    safeCursor,
    showDecks,
    showInspector,
    showQuestionList,
    showFilters,
    viewScale,
    themeMode,
  ])

  function nextCard() {
    if (!sessionCards.length) return
    setCursor((value) => (Math.min(value, sessionCards.length - 1) + 1) % sessionCards.length)
    setShowAnswer(false)
  }

  function goToCard(index: number) {
    setCursor(index)
    setShowAnswer(false)
  }

  function reshuffle() {
    setOrder(shuffleIds(sessionCards))
    setCursor(0)
    setShowAnswer(false)
  }

  function setFilter(nextMode: FilterMode) {
    setFilterMode(nextMode)
    setOrder([])
    setCursor(0)
    setShowAnswer(false)
  }

  function changeViewScale(delta: number) {
    setViewScale((value) => clampViewScale(value + delta))
  }

  function resetViewScale() {
    setViewScale(1)
  }

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const isTextInput = event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement
      const key = event.key.toLowerCase()
      const isModifierShortcut = event.ctrlKey || event.metaKey

      if (library && isModifierShortcut && !event.altKey && key === 'b') {
        event.preventDefault()
        setShowDecks((value) => !value)
        return
      }
      if (library && isModifierShortcut && !event.altKey && key === 'p') {
        event.preventDefault()
        setShowQuestionList((value) => !value)
        return
      }
      if (library && isModifierShortcut && !event.altKey && key === 'i') {
        event.preventDefault()
        setShowInspector((value) => !value)
        return
      }
      if (library && isModifierShortcut && !event.altKey && key === 'f') {
        event.preventDefault()
        setShowFilters((value) => !value)
        return
      }
      if (isModifierShortcut && !event.altKey && (key === '-' || key === '_')) {
        event.preventDefault()
        changeViewScale(-viewScaleStep)
        return
      }
      if (isModifierShortcut && !event.altKey && (key === '=' || key === '+')) {
        event.preventDefault()
        changeViewScale(viewScaleStep)
        return
      }
      if (isModifierShortcut && !event.altKey && key === '0') {
        event.preventDefault()
        resetViewScale()
        return
      }

      if (isTextInput) return

      if (key === ' ' || key === 'j') {
        event.preventDefault()
        setShowAnswer((value) => !value)
      }
      if (key === 'k' || key === 'arrowright') {
        event.preventDefault()
        nextCard()
      }
      if (key === 'i') setShowInspector((value) => !value)
      if (key === 'r' && currentCard && isMastered(currentCard)) void restoreStudy(currentCard)
      if (showAnswer && currentCard && !isMastered(currentCard)) {
        if (event.key === '1') void saveStudy(currentCard, 'easy')
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  })

  const frontImages = currentCard?.assets.filter((asset) => asset.role === 'front_image') ?? []
  const choiceImages = currentCard?.assets.filter((asset) => asset.role === 'choice_image') ?? []
  const answerImages = currentCard?.assets.filter((asset) => asset.role === 'answer_image') ?? []
  const pageCrops = currentCard?.assets.filter((asset) => asset.role === 'page_crop') ?? []
  const sourcePages = currentCard?.assets.filter((asset) => asset.role === 'source_page') ?? []

  const shellClass = [
    'app-shell',
    `theme-${themeMode}`,
    library ? 'has-library' : '',
    loading && !library ? 'is-booting' : '',
    library && showDecks ? 'with-decks' : '',
    library && showInspector ? 'with-inspector' : '',
  ]
    .filter(Boolean)
    .join(' ')
  const shellStyle = { '--view-scale': viewScale.toFixed(2) } as CSSProperties

  return (
    <main className={shellClass} style={shellStyle}>
      <aside className="app-rail" aria-label="앱 메뉴">
        <button type="button" className="rail-brand" title="StudyForge" aria-label="StudyForge">
          <BrandMark />
        </button>
        <button
          type="button"
          className={showDecks ? 'rail-button active' : 'rail-button'}
          title="문제셋"
          aria-label="문제셋"
          onClick={() => setShowDecks((value) => !value)}
          disabled={!library}
        >
          <FileText size={18} />
        </button>
        <button
          type="button"
          className={showQuestionList ? 'rail-button active' : 'rail-button'}
          title="문항 목록"
          aria-label="문항 목록"
          onClick={() => setShowQuestionList((value) => !value)}
          disabled={!library}
        >
          <List size={18} />
        </button>
        <button
          type="button"
          className={showInspector ? 'rail-button active' : 'rail-button'}
          title="검수"
          aria-label="검수"
          onClick={() => setShowInspector((value) => !value)}
          disabled={!library}
        >
          <Check size={18} />
        </button>
        <button
          type="button"
          className={showFilters ? 'rail-button active' : 'rail-button'}
          title="학습 도구"
          aria-label="학습 도구"
          onClick={() => setShowFilters((value) => !value)}
          disabled={!library}
        >
          <SlidersHorizontal size={18} />
        </button>
        <button
          type="button"
          className="rail-button"
          title={themeMode === 'dark' ? '밝은 모드' : '어두운 모드'}
          aria-label={themeMode === 'dark' ? '밝은 모드' : '어두운 모드'}
          onClick={() => setThemeMode((value) => (value === 'dark' ? 'light' : 'dark'))}
        >
          {themeMode === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <button
          type="button"
          className="rail-button danger-action"
          title="종료"
          aria-label="종료"
          onClick={() => void shutdownApp()}
          disabled={stoppingServer}
        >
          <Power size={18} />
        </button>
      </aside>

      {library && showDecks && (
        <aside className="sidebar">
          <div className="sidebar-head">
            <div className="brand-block">
              <BrandMark />
              <div>
                <h1>StudyForge</h1>
                <p>시험 자료 암기 · {library.cards.length.toLocaleString()}개</p>
              </div>
            </div>
            <button
              type="button"
              className="sidebar-toggle"
              title="문제셋 접기"
              aria-label="문제셋 접기"
              onClick={() => setShowDecks(false)}
            >
              <ChevronRight className="collapse-icon" size={18} />
              <span>접기</span>
              <ShortcutHint keys="Ctrl+B" />
            </button>
          </div>

          <nav className="deck-list" aria-label="문제셋">
            {decks.map(([deck, cards]) => (
              <button
                key={deck}
                type="button"
                className={deck === selectedDeck ? 'deck-button active' : 'deck-button'}
                onClick={() => {
                  setSelectedDeck(deck)
                  setOrder([])
                  setCursor(0)
                  setShowAnswer(false)
                }}
              >
                <span>{deck}</span>
                <small>{cards.length}</small>
              </button>
            ))}
          </nav>
        </aside>
      )}

      <section className={library ? 'study-surface' : 'study-surface import-mode'}>
        {!library ? (
          <section className="import-panel">
            <div className="brand-block import-brand">
              <BrandMark />
              <div>
                <h1>StudyForge</h1>
                <p>{loading ? '라이브러리를 확인하는 중입니다.' : '분류된 캡처 자료를 카드로 가져옵니다.'}</p>
              </div>
            </div>
            {loading && (
              <div className="boot-status">
                <RefreshCw className="spin" size={18} />
                <span>앱을 먼저 열고 자료는 뒤에서 불러오는 중입니다.</span>
              </div>
            )}
            {!loading && (
              <>
                <div className="panel-heading">
                  <FileText size={22} />
                  <h2>처음 설정</h2>
                </div>
                <label>
                  기존 캡처 폴더
                  <input value={legacyRoot} onChange={(event) => setLegacyRoot(event.target.value)} />
                </label>
                <label>
                  PDF 직접 가공
                  <textarea
                    value={pdfPaths}
                    onChange={(event) => setPdfPaths(event.target.value)}
                    placeholder="가공할 PDF 파일 경로를 한 줄에 하나씩 입력"
                    rows={3}
                  />
                </label>
                <button className="primary-action" type="button" onClick={runImport} disabled={importing}>
                  {importing ? <RefreshCw className="spin" size={18} /> : <Play size={18} />}
                  <span>{importing ? '가져오는 중' : '자료 가져오기'}</span>
                </button>
                <button className="secondary-action" type="button" onClick={() => void shutdownApp()} disabled={stoppingServer}>
                  <Power size={18} />
                  <span>{stoppingServer ? '종료 중' : '종료'}</span>
                </button>
              </>
            )}
            {error && <p className="error-text">{error}</p>}
          </section>
        ) : (
          <>
            <header className="study-header">
              <div className="deck-title">
                <p className="eyebrow">{currentCard?.subject ?? '문제셋 없음'}</p>
                <h2>{selectedDeck || '문제셋'}</h2>
              </div>
              <div className="topbar-actions">
                <span className="progress-pill">{progressText}</span>
              </div>
            </header>

            {showFilters && (
              <section className="study-tool-panel" aria-label="학습 도구">
                <div className="filter-bar" role="tablist" aria-label="학습 범위">
                  <FilterButton label={filterLabels.all} count={deckStats.all} active={filterMode === 'all'} onClick={() => setFilter('all')} />
                  <FilterButton label={filterLabels.due} count={deckStats.due} active={filterMode === 'due'} onClick={() => setFilter('due')} />
                  <FilterButton label={filterLabels.new} count={deckStats.new} active={filterMode === 'new'} onClick={() => setFilter('new')} />
                  <FilterButton label={filterLabels.low} count={deckStats.low} active={filterMode === 'low'} onClick={() => setFilter('low')} />
                  <FilterButton
                    label={filterLabels.mastered}
                    count={deckStats.mastered}
                    active={filterMode === 'mastered'}
                    onClick={() => setFilter('mastered')}
                  />
                  <FilterButton
                    label={filterLabels.needs_work}
                    count={deckStats.needs_work}
                    active={filterMode === 'needs_work'}
                    onClick={() => setFilter('needs_work')}
                  />
                </div>
                <div className="study-tool-row">
                  <div className="view-scale-controls" aria-label="화면 배율">
                    <button
                      type="button"
                      title="화면 축소 (Ctrl+-)"
                      aria-label="화면 축소"
                      onClick={() => changeViewScale(-viewScaleStep)}
                      disabled={viewScale <= minViewScale}
                    >
                      <ZoomOut size={16} />
                      <ShortcutHint keys="Ctrl+-" />
                    </button>
                    <button
                      type="button"
                      className="view-scale-value"
                      title="기본 배율로 되돌리기 (Ctrl+0)"
                      aria-label="기본 배율"
                      onClick={resetViewScale}
                    >
                      {Math.round(viewScale * 100)}%
                      <ShortcutHint keys="Ctrl+0" />
                    </button>
                    <button
                      type="button"
                      title="화면 확대 (Ctrl+=)"
                      aria-label="화면 확대"
                      onClick={() => changeViewScale(viewScaleStep)}
                      disabled={viewScale >= maxViewScale}
                    >
                      <ZoomIn size={16} />
                      <ShortcutHint keys="Ctrl+=" />
                    </button>
                  </div>
                  <button type="button" className="secondary-action" onClick={reshuffle}>
                    <Shuffle size={17} />
                    <span>섞기</span>
                  </button>
                  <button type="button" className="secondary-action" onClick={() => setShowFilters(false)}>
                    <span>닫기</span>
                    <ShortcutHint keys="Ctrl+F" />
                  </button>
                </div>
              </section>
            )}

            <section
              className={showQuestionList ? 'question-list-panel expanded' : 'question-list-panel collapsed'}
              aria-label="현재 문제 목록"
            >
              <div className="question-list-heading">
                <div>
                  <strong>문항 바로가기</strong>
                  <span>{filterLabels[filterMode]} · {orderedCards.length.toLocaleString()}개</span>
                </div>
                <button type="button" className="inline-toggle" onClick={() => setShowQuestionList((value) => !value)}>
                  {showQuestionList ? '접기' : '펼치기'}
                  <ShortcutHint keys="Ctrl+P" />
                </button>
              </div>
              {showQuestionList && (
                <div className="question-list">
                  {orderedCards.map((card, index) => {
                    const preview = previewAsset(card)
                    return (
                      <button
                        key={card.id}
                        type="button"
                        className={card.id === currentCard?.id ? 'question-list-item active' : 'question-list-item'}
                        onClick={() => goToCard(index)}
                      >
                        <span className="question-list-number">{index + 1}</span>
                        <div className="question-list-thumb">
                          {preview ? <img src={assetUrl(preview)} alt="" loading="lazy" /> : <span>텍스트</span>}
                        </div>
                        <div className="question-list-copy">
                          <strong>{listPrimaryText(card)}</strong>
                          <small>
                            #{card.source_item ?? index + 1} · {labelReviewStatus(card.review_status)}
                          </small>
                        </div>
                      </button>
                    )
                  })}
                </div>
              )}
            </section>

            <article className="question-pane">
              {currentCard ? (
                <div className="question-content">
                  {currentCard.source === 'legacy_capture' ? (
                    <p className="question-card-label">{currentCard.front_text}</p>
                  ) : (
                    <div className="question-text">
                      <p>{currentCard.front_text}</p>
                    </div>
                  )}
                  <ImageStrip assets={[...frontImages, ...choiceImages]} />
                  {showAnswer && (
                    <div className="answer-zone">
                      {currentCard.back_text && <p>{currentCard.back_text}</p>}
                      {pageCrops.length > 0 && (
                        <div className="evidence-block">
                          <span>원문 영역</span>
                          <ImageStrip assets={pageCrops} />
                        </div>
                      )}
                      <ImageStrip assets={answerImages} />
                    </div>
                  )}
                </div>
              ) : (
                <div className="card-empty-state">선택된 범위에 카드가 없습니다.</div>
              )}
            </article>

            <div className="study-composer" aria-label="학습 동작">
              <button
                type="button"
                className="composer-action answer-action"
                onClick={() => setShowAnswer((value) => !value)}
                disabled={!currentCard}
              >
                <Eye size={18} />
                <span>{showAnswer ? '정답 숨기기' : '정답 보기'}</span>
                <ShortcutHint keys="Space/J" />
              </button>
              <button
                type="button"
                className="composer-action"
                title="외움 상태를 기록하지 않고 다음 카드로 넘깁니다."
                onClick={nextCard}
                disabled={!currentCard}
              >
                <ChevronRight size={18} />
                <span>건너뛰기</span>
                <ShortcutHint keys="K/→" />
              </button>
              {showAnswer && currentCard && !isMastered(currentCard) && (
                <button
                  type="button"
                  className="composer-action mark-action"
                  title="외운 카드로 처리하고 기본 학습 목록에서 제외합니다."
                  onClick={() => void saveStudy(currentCard, 'easy')}
                >
                  <Check size={18} />
                  <span>외움·제외</span>
                  <ShortcutHint keys="1" />
                </button>
              )}
              {currentCard && isMastered(currentCard) && (
                <button
                  type="button"
                  className="composer-action restore-action"
                  title="외움·제외 기록을 지우고 다시 학습 목록에 넣습니다."
                  onClick={() => void restoreStudy(currentCard)}
                >
                  <RotateCcw size={18} />
                  <span>다시 복구</span>
                  <ShortcutHint keys="R" />
                </button>
              )}
            </div>
          </>
        )}
      </section>

      {library && showInspector && (
        <aside className="inspector">
          <div className="status-row">
            <Check size={18} />
            <span>{library.report.pdfs_imported} PDF</span>
            <span>{library.report.legacy_decks_imported} 기존 자료</span>
          </div>

          <details className="inspector-section" open>
            <summary>
              <span>무결성</span>
              <strong>{validation?.ok ? 'OK' : `${validation?.issues.length ?? 0}`}</strong>
            </summary>
            <div className={validation?.ok ? 'validation-box ok' : 'validation-box'}>
              <span>누락 이미지 {validation?.missing_asset_count ?? 0}</span>
              <span>누락 원본 {validation?.missing_source_count ?? 0}</span>
            </div>
          </details>

          <details className="inspector-section" open>
            <summary>
              <span>PDF 자동 생성</span>
              <strong>{library.report.pdfs_imported}</strong>
            </summary>
            <div className="validation-box">
              <span>생성 카드 {library.report.cards_created.toLocaleString()}</span>
              <span>검수 필요 {library.report.low_confidence_cards.toLocaleString()}</span>
              <span>앞면 crop 누락 {validation?.pdf_cards_missing_front_count ?? 0}</span>
              <span>원문 crop 누락 {validation?.pdf_cards_missing_crop_count ?? 0}</span>
              {library.report.warnings.slice(0, 3).map((warning) => (
                <small key={warning}>{warning}</small>
              ))}
            </div>
          </details>

            <details className="inspector-section">
              <summary>
                <span>자료 갱신</span>
                <RefreshCw size={16} />
              </summary>
              <div className="reimport-box">
                <label>
                  기존 캡처 폴더
                  <input value={legacyRoot} onChange={(event) => setLegacyRoot(event.target.value)} />
                </label>
                <label>
                  PDF 직접 가공
                  <textarea
                    value={pdfPaths}
                    onChange={(event) => setPdfPaths(event.target.value)}
                    placeholder="가공할 PDF 파일 경로를 한 줄에 하나씩 입력"
                    rows={3}
                  />
                </label>
                <button className="secondary-action" type="button" onClick={runImport} disabled={importing}>
                {importing ? <RefreshCw className="spin" size={16} /> : <Play size={16} />}
                <span>{importing ? '가져오는 중' : '다시 가져오기'}</span>
              </button>
            </div>
          </details>

          <details className="inspector-section">
            <summary>
              <span>학습 현황</span>
              <strong>{currentCard?.study_seen_count ?? 0}</strong>
            </summary>
            <div className="study-stats">
              <span>{deckStats.new} 신규</span>
              <span>{deckStats.due} 복습</span>
              <span>{labelRating(currentCard?.study_last_rating ?? 'new')}</span>
            </div>
          </details>

          <details className="inspector-section">
            <summary>
              <span>검수</span>
              <strong>{library.report.low_confidence_cards}</strong>
            </summary>
            <div className="review-box">
              <span>자동 추출 신뢰도가 낮은 카드</span>
            </div>
          </details>

          {currentCard && (
            <>
              <details className="inspector-section">
                <summary>
                  <span>근거</span>
                  <ImageIcon size={16} />
                </summary>
                <div className="source-box">
                  <p>{currentCard.source_page ? `p.${currentCard.source_page}` : currentCard.source_item}</p>
                  <span className={`review-status ${currentCard.review_status}`}>{labelReviewStatus(currentCard.review_status)}</span>
                  <span className="review-status">{labelRating(currentCard.study_last_rating)}</span>
                  {currentCard.review_flags.length > 0 && (
                    <ul className="flag-list">
                      {currentCard.review_flags.slice(0, 4).map((flag) => (
                        <li key={flag}>{flag}</li>
                      ))}
                    </ul>
                  )}
                  {showAnswer ? (
                    <ImageStrip assets={[...pageCrops, ...sourcePages].slice(0, 1)} compact />
                  ) : (
                    <p className="locked-note">정답 확인 후 표시</p>
                  )}
                </div>
              </details>

              <details className="inspector-section">
                <summary>
                  <span>카드 편집</span>
                  <Check size={16} />
                </summary>
                <form
                  key={currentCard.id}
                  className="review-editor"
                  onSubmit={(event) => {
                    event.preventDefault()
                    void saveReview(currentCard, 'approved', event.currentTarget)
                  }}
                >
                  <label>
                    앞면
                    <textarea name="front_text" defaultValue={currentCard.front_text} rows={4} />
                  </label>
                  <label>
                    뒷면
                    <textarea name="back_text" defaultValue={currentCard.back_text} rows={5} />
                  </label>
                  <label>
                    메모
                    <textarea name="note" defaultValue={currentCard.review_note} rows={3} />
                  </label>
                  <div className="review-actions">
                    <button type="submit" className="primary-action">
                      <Check size={16} />
                      <span>승인 저장</span>
                    </button>
                    <button
                      type="button"
                      className="secondary-action"
                      onClick={(event) => {
                        const form = event.currentTarget.closest('form')
                        if (form) void saveReview(currentCard, 'needs_work', form)
                      }}
                    >
                      <AlertTriangle size={16} />
                      <span>보류 저장</span>
                    </button>
                  </div>
                </form>
              </details>
            </>
          )}
        </aside>
      )}
    </main>
  )
}

function ImageStrip({ assets, compact = false }: { assets: Asset[]; compact?: boolean }) {
  if (!assets.length) return null
  return (
    <div className={compact ? 'image-strip compact' : 'image-strip'}>
      {assets.map((asset) => (
        <img
          key={asset.id}
          src={assetUrl(asset)}
          width={asset.width}
          height={asset.height}
          alt=""
          loading="lazy"
        />
      ))}
    </div>
  )
}

function BrandMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <span className="brand-page" />
      <span className="brand-check" />
    </div>
  )
}

function FilterButton({
  label,
  count,
  active,
  onClick,
}: {
  label: string
  count: number
  active: boolean
  onClick: () => void
}) {
  return (
    <button type="button" className={active ? 'filter-button active' : 'filter-button'} onClick={onClick}>
      <span>{label}</span>
      <strong>{count}</strong>
    </button>
  )
}

function ShortcutHint({ keys }: { keys: string }) {
  return <span className="shortcut-hint">({keys})</span>
}

export default App
