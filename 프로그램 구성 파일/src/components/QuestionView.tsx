import { useLayoutEffect, useRef, useState } from 'react'
import { openSourceReference } from '../api'
import type { Question } from '../types'
import { MarkdownContent } from './MarkdownContent'

function sourceItems(markdown: string) {
  return markdown
    .split(/\r?\n/)
    .flatMap((line) =>
      line
        .replace(/^(?:출처|reference|source)\s*[:：]\s*/i, '')
        .split(/\s+\+\s+/)
        .map((item) => item.trim())
        .filter(Boolean),
    )
}

function sourceLabel(reference: string) {
  const pathMatch = reference.match(/[A-Za-z]:\\([^+\n\r,]+?\.(?:pdf|pptx?|docx?|hwp|hwpx|png|jpe?g|webp))/i)
  const pageMatch = reference.match(/(?:p|page|쪽|페이지|slide|슬라이드)\.?\s*\d+/i)
  const fileName = pathMatch?.[1].split(/\\+/).pop()
  return [fileName ?? reference, pageMatch?.[0]].filter(Boolean).join(' · ')
}

function SourceReferences({ markdown }: { markdown: string }) {
  const [opening, setOpening] = useState('')
  const items = sourceItems(markdown)
  if (!items.length) return null

  async function open(reference: string) {
    setOpening(reference)
    try {
      await openSourceReference(reference)
    } catch (error) {
      window.alert(error instanceof Error ? error.message : '출처를 열 수 없습니다.')
    } finally {
      setOpening('')
    }
  }

  return (
    <section className="source-section" aria-label="출처">
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
