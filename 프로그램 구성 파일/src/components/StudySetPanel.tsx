import { useCallback, useEffect, useRef, useState } from 'react'
import { Ellipsis, FileText, Pencil, Search } from 'lucide-react'
import type { StudySet } from '../types'

function StudySetRow({ studyset, selected, onSelect, onRename }: {
  studyset: StudySet
  selected: boolean
  onSelect: (id: string) => void
  onRename: (id: string, title: string) => Promise<void>
}) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const row = useRef<HTMLDivElement>(null)
  const actions = useRef<HTMLButtonElement>(null)
  const menuAction = useRef<HTMLButtonElement>(null)
  const submitting = useRef(false)
  const cancelled = useRef(false)
  const focusEditor = useCallback((input: HTMLInputElement | null) => {
    input?.focus()
    input?.select()
  }, [])

  useEffect(() => {
    if (!menuOpen) return
    menuAction.current?.focus()
    function onPointerDown(event: PointerEvent) {
      if (!row.current?.contains(event.target as Node)) setMenuOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [menuOpen])

  async function save(input: HTMLInputElement) {
    if (submitting.current || cancelled.current) return
    const title = input.value.trim()
    if (title === studyset.title) {
      setEditing(false)
      return
    }
    submitting.current = true
    setSaving(true)
    try {
      await onRename(studyset.id, title)
      setEditing(false)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '이름을 바꾸지 못했습니다. 다시 시도하세요.')
    } finally {
      submitting.current = false
      setSaving(false)
    }
  }

  return (
    <div className="studyset-row" ref={row}>
      {editing ? (
        <div className="studyset-item studyset-editing">
          <FileText size={16} />
          <input
            aria-label="문제 데이터 이름"
            aria-invalid={!!error}
            defaultValue={studyset.title}
            maxLength={160}
            readOnly={saving}
            ref={focusEditor}
            onChange={() => setError('')}
            onBlur={(event) => void save(event.currentTarget)}
            onKeyDown={(event) => {
              if (event.nativeEvent.isComposing || event.keyCode === 229) return
              if (event.key === 'Enter') {
                event.preventDefault()
                void save(event.currentTarget)
              }
              if (event.key === 'Escape' && !submitting.current) {
                event.stopPropagation()
                cancelled.current = true
                setEditing(false)
                setError('')
                requestAnimationFrame(() => actions.current?.focus())
              }
            }}
          />
        </div>
      ) : (
        <>
          <button
            type="button"
            className={selected ? 'studyset-item active' : 'studyset-item'}
            onClick={() => onSelect(studyset.id)}
            aria-current={selected ? 'true' : undefined}
          >
            <FileText size={16} />
            <span className="studyset-title" title={studyset.title}>{studyset.title}</span>
            <strong>{studyset.question_count ?? '...'}</strong>
          </button>
          <button
            type="button"
            className="studyset-actions"
            ref={actions}
            aria-label={`${studyset.title} 옵션`}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((value) => !value)}
            onKeyDown={(event) => { if (event.key === ' ') event.stopPropagation() }}
          >
            <Ellipsis size={18} aria-hidden="true" />
          </button>
        </>
      )}
      {menuOpen && (
        <div className="studyset-menu" onKeyDown={(event) => {
          if (event.key === ' ') event.stopPropagation()
          if (event.key === 'Escape') {
            event.stopPropagation()
            setMenuOpen(false)
            actions.current?.focus()
          }
        }}>
          <button
            type="button"
            ref={menuAction}
            onClick={() => {
              cancelled.current = false
              setMenuOpen(false)
              setEditing(true)
            }}
          >
            <Pencil size={14} aria-hidden="true" />
            이름 바꾸기
          </button>
        </div>
      )}
      {error && <p className="studyset-error" role="alert">{error}</p>}
    </div>
  )
}

export function StudySetPanel({
  studysets,
  selectedId,
  search,
  onSearch,
  onSelect,
  onRename,
}: {
  studysets: StudySet[]
  selectedId: string
  search: string
  onSearch: (value: string) => void
  onSelect: (id: string) => void
  onRename: (id: string, title: string) => Promise<void>
}) {
  const normalizedSearch = search.trim().toLowerCase()
  const visibleStudysets = normalizedSearch
    ? studysets.filter((studyset) => studyset.title.toLowerCase().includes(normalizedSearch))
    : studysets

  return (
    <aside className="set-panel">
      <div className="set-panel-header">
        <h1>Exam Study</h1>
      </div>

      <label className="search-box">
        <Search size={16} />
        <input
          data-studyset-search
          value={search}
          onChange={(event) => onSearch(event.target.value)}
          placeholder="문제 데이터 검색"
        />
      </label>

      <nav className="studyset-list" aria-label="문제 데이터">
        {visibleStudysets.map((studyset) => (
          <StudySetRow
            key={studyset.id}
            studyset={studyset}
            selected={selectedId === studyset.id}
            onSelect={onSelect}
            onRename={onRename}
          />
        ))}
      </nav>
    </aside>
  )
}
