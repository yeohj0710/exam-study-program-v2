import { FileText, Search } from 'lucide-react'
import type { StudySet } from '../types'

export function StudySetPanel({
  studysets,
  selectedId,
  search,
  onSearch,
  onSelect,
}: {
  studysets: StudySet[]
  selectedId: string
  search: string
  onSearch: (value: string) => void
  onSelect: (id: string) => void
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
          <button
            key={studyset.id}
            type="button"
            className={selectedId === studyset.id ? 'studyset-item active' : 'studyset-item'}
            onClick={() => onSelect(studyset.id)}
          >
            <FileText size={16} />
            <span>{studyset.title}</span>
            <strong>{studyset.question_count ?? '...'}</strong>
          </button>
        ))}
      </nav>
    </aside>
  )
}
