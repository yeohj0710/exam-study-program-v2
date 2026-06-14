import { useLayoutEffect, useRef } from 'react'
import type { Question } from '../types'
import { MarkdownContent } from './MarkdownContent'

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
        <section className="answer-section" ref={answerRef}>
          <MarkdownContent markdown={question.answer_markdown} />
        </section>
      )}
    </article>
  )
}
