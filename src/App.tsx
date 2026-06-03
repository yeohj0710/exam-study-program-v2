import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  Check,
  ChevronRight,
  Eye,
  FileText,
  Image as ImageIcon,
  Play,
  RefreshCw,
  Shuffle,
} from 'lucide-react'
import './App.css'

type AssetRole = 'front_image' | 'choice_image' | 'answer_image' | 'source_page' | 'page_crop'

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

const defaultSourceRoot = 'G:\\내 드라이브\\여형준님\\21 6-1'
const defaultLegacyRoot =
  'G:\\내 드라이브\\여형준님\\21 6-1\\족보 암기 프로그램\\중간고사'

function assetUrl(asset: Asset) {
  if (/^[a-zA-Z]:\\/.test(asset.path)) return `/api/external-asset?path=${encodeURIComponent(asset.path)}`
  return `/assets/${asset.path.split('/').map(encodeURIComponent).join('/')}`
}

function shuffleIds(cards: StudyCard[]) {
  return cards
    .map((card) => ({ card, sort: Math.random() }))
    .sort((a, b) => a.sort - b.sort)
    .map((item) => item.card.id)
}

function App() {
  const [library, setLibrary] = useState<Library | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedDeck, setSelectedDeck] = useState('')
  const [order, setOrder] = useState<string[]>([])
  const [cursor, setCursor] = useState(0)
  const [showAnswer, setShowAnswer] = useState(false)
  const [sourceRoot, setSourceRoot] = useState(defaultSourceRoot)
  const [legacyRoot, setLegacyRoot] = useState(defaultLegacyRoot)
  const [importing, setImporting] = useState(false)

  async function loadLibrary() {
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/library')
      if (!response.ok) throw new Error(response.status === 404 ? 'empty' : response.statusText)
      const payload = (await response.json()) as Library
      setLibrary(payload)
      setSelectedDeck((current) => current || payload.cards[0]?.deck || '')
    } catch (caught) {
      if (caught instanceof Error && caught.message !== 'empty') setError(caught.message)
      setLibrary(null)
    } finally {
      setLoading(false)
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
          source_root: sourceRoot || null,
          legacy_root: legacyRoot || null,
          include_lectures: false,
          copy_legacy_assets: false,
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
        setSelectedDeck(payload.cards[0]?.deck || '')
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

  const cardsById = useMemo(
    () => new Map(deckCards.map((card) => [card.id, card])),
    [deckCards],
  )
  const effectiveOrder = useMemo(() => {
    const isValidOrder = order.length === deckCards.length && order.every((id) => cardsById.has(id))
    return isValidOrder ? order : deckCards.map((card) => card.id)
  }, [cardsById, deckCards, order])
  const currentCard = cardsById.get(effectiveOrder[cursor]) ?? deckCards[0]
  const progressText = deckCards.length ? `${Math.min(cursor + 1, deckCards.length)} / ${deckCards.length}` : '0 / 0'

  function nextCard() {
    if (!deckCards.length) return
    setCursor((value) => (value + 1) % deckCards.length)
    setShowAnswer(false)
  }

  function reshuffle() {
    setOrder(shuffleIds(deckCards))
    setCursor(0)
    setShowAnswer(false)
  }

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.target instanceof HTMLInputElement) return
      if (event.key.toLowerCase() === 'j') setShowAnswer((value) => !value)
      if (event.key.toLowerCase() === 'k') nextCard()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  })

  const frontImages = currentCard?.assets.filter((asset) => asset.role === 'front_image') ?? []
  const choiceImages = currentCard?.assets.filter((asset) => asset.role === 'choice_image') ?? []
  const answerImages = currentCard?.assets.filter((asset) => asset.role === 'answer_image') ?? []
  const pageCrops = currentCard?.assets.filter((asset) => asset.role === 'page_crop') ?? []
  const sourcePages = currentCard?.assets.filter((asset) => asset.role === 'source_page') ?? []

  if (loading) {
    return (
      <main className="loading-screen">
        <RefreshCw className="spin" size={28} />
        <span>라이브러리 확인 중</span>
      </main>
    )
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">SF</div>
          <div>
            <h1>StudyForge</h1>
            <p>{library ? `${library.cards.length.toLocaleString()} cards` : 'local library'}</p>
          </div>
        </div>

        <nav className="deck-list" aria-label="Decks">
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

      <section className="study-surface">
        {!library ? (
          <section className="import-panel">
            <div className="panel-heading">
              <FileText size={22} />
              <h2>자료 가져오기</h2>
            </div>
            <label>
              PDF 루트
              <input value={sourceRoot} onChange={(event) => setSourceRoot(event.target.value)} />
            </label>
            <label>
              기존 캡처 뱅크
              <input value={legacyRoot} onChange={(event) => setLegacyRoot(event.target.value)} />
            </label>
            <button className="primary-action" type="button" onClick={runImport} disabled={importing}>
              {importing ? <RefreshCw className="spin" size={18} /> : <Play size={18} />}
              <span>{importing ? '가져오는 중' : '가져오기'}</span>
            </button>
            {error && <p className="error-text">{error}</p>}
          </section>
        ) : (
          <>
            <header className="study-header">
              <div>
                <p className="eyebrow">{currentCard?.subject ?? 'No deck'}</p>
                <h2>{selectedDeck || 'Deck'}</h2>
              </div>
              <div className="session-actions">
                <span className="progress-pill">{progressText}</span>
                <button type="button" onClick={reshuffle} title="Shuffle">
                  <Shuffle size={18} />
                </button>
              </div>
            </header>

            <article className="question-pane">
              {currentCard ? (
                <>
                  <div className="question-text">
                    <p>{currentCard.front_text}</p>
                  </div>
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
                </>
              ) : (
                <div className="empty-state">선택된 덱에 카드가 없습니다.</div>
              )}
            </article>

            <div className="study-controls">
              <button type="button" className="primary-action" onClick={() => setShowAnswer((value) => !value)}>
                <Eye size={18} />
                <span>{showAnswer ? '숨기기' : '정답'}</span>
              </button>
              <button type="button" className="secondary-action" onClick={nextCard}>
                <ChevronRight size={18} />
                <span>다음</span>
              </button>
            </div>
          </>
        )}
      </section>

      <aside className="inspector">
        <div className="status-row">
          <Check size={18} />
          <span>{library?.report.pdfs_imported ?? 0} PDF</span>
          <span>{library?.report.legacy_decks_imported ?? 0} legacy</span>
        </div>
        <div className="review-box">
          <div className="panel-heading">
            <AlertTriangle size={18} />
            <h2>검수</h2>
          </div>
          <strong>{library?.report.low_confidence_cards ?? 0}</strong>
          <span>low confidence</span>
        </div>
        {currentCard && (
          <div className="source-box">
            <div className="panel-heading">
              <ImageIcon size={18} />
              <h2>근거</h2>
            </div>
            <p>{currentCard.source_page ? `page ${currentCard.source_page}` : currentCard.source_item}</p>
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
              <p className="locked-note">정답 확인 후 원문 표시</p>
            )}
          </div>
        )}
      </aside>
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

export default App
