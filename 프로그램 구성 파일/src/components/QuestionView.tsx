import { useLayoutEffect, useRef, useState } from 'react'
import { openSourceReference } from '../api'
import type { Question } from '../types'
import { MarkdownContent } from './MarkdownContent'

const SOURCE_LINE_RE = /^(?:출처|reference|source)\s*[:：]\s*/i
const IMAGE_LINE_RE = /^!\[[^\]]*]\([^)]+\)\s*$/

function splitSourceMarkdown(markdown: string) {
  const references: string[] = []
  const evidenceLines: string[] = []
  let currentReference = ''

  function flushReference() {
    if (!currentReference.trim()) return
    currentReference
      .split(/\s+\+\s+/)
      .map((item) => item.trim())
      .filter(Boolean)
      .forEach((item) => references.push(item))
    currentReference = ''
  }

  for (const line of markdown.split(/\r?\n/)) {
    const normalized = line.trim()
    if (SOURCE_LINE_RE.test(normalized)) {
      flushReference()
      currentReference = normalized.replace(SOURCE_LINE_RE, '').trim()
      continue
    }

    if (currentReference && normalized && !IMAGE_LINE_RE.test(normalized)) {
      currentReference = `${currentReference} ${normalized}`
      continue
    }

    flushReference()
    evidenceLines.push(line)
  }
  flushReference()

  return { references, evidenceMarkdown: sourceEvidenceMarkdown(evidenceLines.join('\n')) }
}

function sourceEvidenceMarkdown(markdown: string) {
  return markdown
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .join('\n')
    .trim()
}

function sourceLabel(reference: string) {
  const pathMatch = reference.match(/[A-Za-z]:\\([^+\n\r,]+?\.(?:pdf|pptx?|docx?|hwp|hwpx|png|jpe?g|webp))/i)
  const pageMatch = reference.match(/(?:p|page|쪽|페이지|slide|슬라이드)\.?\s*\d+/i)
  const fileName = pathMatch?.[1].split(/\\+/).pop()
  return [fileName ?? reference, pageMatch?.[0]].filter(Boolean).join(' · ')
}

function SourceReferences({ markdown }: { markdown: string }) {
  const [opening, setOpening] = useState('')
  const { references: items, evidenceMarkdown } = splitSourceMarkdown(markdown)
  if (!items.length && !evidenceMarkdown) return null

  async function open(reference: string) {
    setOpening(reference)
    try {
      const source = await openSourceReference(reference)
      if (!source.url) throw new Error('출처 URL을 만들 수 없습니다.')
      window.open(source.url, '_blank', 'noopener,noreferrer')
    } catch (error) {
      window.alert(error instanceof Error ? error.message : '출처를 열 수 없습니다.')
    } finally {
      setOpening('')
    }
  }

  return (
    <section className="source-section" aria-label="출처">
      {items.length > 0 && (
        <>
          <span>출처</span>
          <div>
            {items.map((item, index) => (
              <button
                type="button"
                className="source-button"
                key={`${item}-${index}`}
                title={item}
                disabled={opening === item}
                onClick={() => void open(item)}
              >
                {sourceLabel(item)}
              </button>
            ))}
          </div>
        </>
      )}
      {evidenceMarkdown && (
        <div className="source-evidence">
          <MarkdownContent markdown={evidenceMarkdown} />
        </div>
      )}
    </section>
  )
}

export function QuestionView({
  question,
  showAnswer,
  choiceShuffleKey,
}: {
  question: Question | null
  showAnswer: boolean
  choiceShuffleKey: string
}) {
  const headingRef = useRef<HTMLDivElement | null>(null)
  const answerRef = useRef<HTMLElement | null>(null)
  const mountedRef = useRef(false)

  useLayoutEffect(() => {
    if (!question) return
    if (!mountedRef.current) {
      mountedRef.current = true
      return
    }

    const target = showAnswer ? answerRef.current : headingRef.current
    if (!target) return
    const animationFrame = window.requestAnimationFrame(() => {
      target.scrollIntoView({ behavior: 'auto', block: 'start' })
    })
    return () => window.cancelAnimationFrame(animationFrame)
  }, [choiceShuffleKey, question, showAnswer])

  if (!question) {
    return (
      <article className="question-view empty">
        <p>표시할 문제가 없습니다.</p>
      </article>
    )
  }

  return (
    <article className={question.progress.memorized ? 'question-view memorized' : 'question-view'}>
      <div className="question-scroll-anchor" ref={headingRef} aria-hidden="true">
        <span className="question-anchor" title={`문제 ${question.ordinal}`} aria-label={`문제 ${question.ordinal}`} />
      </div>

      {question.progress.memorized && <div className="state-chip">암기 완료</div>}
      {question.issues.length > 0 && <div className="state-chip warn">{question.issues.length}개 확인 필요</div>}

      {question.prompt_markdown && <MarkdownContent markdown={question.prompt_markdown} shuffleChoicesKey={choiceShuffleKey} />}

      {showAnswer && (
        <>
          <section className="answer-section" ref={answerRef}>
            <MarkdownContent markdown={question.answer_markdown} />
          </section>
          {question.source_markdown && <SourceReferences markdown={question.source_markdown} />}
        </>
      )}
    </article>
  )
}
