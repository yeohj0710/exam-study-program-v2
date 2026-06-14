import { useEffect, useRef } from 'react'
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
  const headingRef = useRef<HTMLElement | null>(null)
  const answerRef = useRef<HTMLElement | null>(null)
  const mountedRef = useRef(false)

  useEffect(() => {
    if (!question) return
    if (!mountedRef.current) {
      mountedRef.current = true
      return
    }

    const target = showAnswer ? answerRef.current : headingRef.current
    if (!target) return
    const scrollToTarget = () => {
      target.scrollIntoView({ behavior: 'smooth', block: showAnswer ? 'center' : 'start' })
    }
    const firstTimer = window.setTimeout(scrollToTarget, 40)
    const secondTimer = window.setTimeout(scrollToTarget, 320)
    return () => {
      window.clearTimeout(firstTimer)
      window.clearTimeout(secondTimer)
    }
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
      <header className="question-heading" ref={headingRef}>
        <span className="question-anchor" title={`문제 ${question.ordinal}`} aria-label={`문제 ${question.ordinal}`} />
        <h1>{question.title}</h1>
      </header>

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
