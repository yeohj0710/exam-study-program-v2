import { useLayoutEffect, useRef, useState } from 'react'
import { openSourceReference } from '../api'
import type { Question } from '../types'
import { MarkdownContent } from './MarkdownContent'

const SOURCE_LINE_RE = /^(?:출처|reference|source)\s*[:：]\s*/i
const IMAGE_LINE_RE = /^!\[[^\]]*]\([^)]+\)\s*$/
const PROMPT_CHOICE_PREFIX_RE = /^(?:[\u2460-\u2473\u3251-\u325F]\s*[.)、:：-]?|\(?\d{1,2}\)?\s*(?:번)?[.)、:：-]?)\s*/
const ANSWER_LABEL_RE = /^(?:답|answer)\s*[:：]\s*/i
const EXPLICIT_REVIEW_RE = /^([Oo0○Xx×✕])\s*[:.)、-]?\s*(.+)$/
const NEGATIVE_QUESTION_RE = /(옳지\s*않|틀린|잘못된|바르지\s*않|해당하지\s*않)/
const TOKEN_RE = /[A-Za-z0-9가-힣]{2,}/g
const STOP_TOKENS = new Set([
  '것은',
  '것을',
  '으로',
  '에서',
  '에게',
  '된다',
  '한다',
  '있는',
  '없는',
  '경우',
  '사용',
  '대한',
  '관련',
  '다음',
  '중',
])

type PromptChoice = {
  order: number
  text: string
}

type ChoiceReviewStatus = 'correct' | 'incorrect'

type RevealedChoice = PromptChoice & {
  status: ChoiceReviewStatus
  corrections: string[]
}

type ChoiceReview = {
  stemMarkdown: string
  choices: RevealedChoice[]
}

type ExplicitReviewItem = {
  status: ChoiceReviewStatus
  text: string
  correction?: string
}

function isPromptChoiceLine(line: string) {
  return line.startsWith('- ')
}

function stripPromptChoicePrefix(text: string) {
  return text.replace(PROMPT_CHOICE_PREFIX_RE, '').trimStart()
}

function splitPromptChoices(markdown: string) {
  const lines = markdown.split(/\r?\n/)
  const stemLines: string[] = []
  const choices: PromptChoice[] = []
  let index = 0

  while (index < lines.length) {
    if (!isPromptChoiceLine(lines[index])) {
      if (choices.length === 0) stemLines.push(lines[index])
      index += 1
      continue
    }

    const firstLine = lines[index].slice(2).trim()
    choices.push({
      order: choices.length,
      text: stripPromptChoicePrefix(firstLine),
    })
    index += 1

    while (index < lines.length && !isPromptChoiceLine(lines[index])) {
      index += 1
    }
  }

  return { stemMarkdown: stemLines.join('\n').trim(), choices }
}

function normalizeForMatch(value: string) {
  return value
    .replace(/\*\*|==/g, '')
    .replace(/[^\p{L}\p{N}]+/gu, '')
    .toLowerCase()
}

function containsMatch(container: string, item: string) {
  const containerText = normalizeForMatch(container)
  const itemText = normalizeForMatch(item)
  if (!containerText || !itemText) return false
  return containerText === itemText || containerText.includes(itemText) || itemText.includes(containerText)
}

function answerLines(markdown: string) {
  return markdown
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !IMAGE_LINE_RE.test(line))
    .map((line) => line.replace(ANSWER_LABEL_RE, '').trim())
    .filter(Boolean)
}

function parseExplicitReviewLine(line: string): ExplicitReviewItem | null {
  const match = line.match(EXPLICIT_REVIEW_RE)
  if (!match) return null

  const status: ChoiceReviewStatus = /[Oo0○]/.test(match[1]) ? 'correct' : 'incorrect'
  const [text, correction] = match[2].split(/\s*(?:->|=>|→|⇒)\s*/, 2)
  return {
    status,
    text: text.trim(),
    correction: correction?.trim(),
  }
}

function lineMatchesAnyChoice(line: string, choices: PromptChoice[]) {
  return choices.some((choice) => containsMatch(line, choice.text))
}

function splitAnswerParts(markdown: string, choices: PromptChoice[]) {
  const lines = answerLines(markdown)
  const explicitItems: ExplicitReviewItem[] = []
  const selectedAnswers: string[] = []
  const explanationLines: string[] = []
  let scanningSelected = true
  let sawSelected = false

  for (const line of lines) {
    const explicitItem = parseExplicitReviewLine(line)
    if (explicitItem) {
      explicitItems.push(explicitItem)
      continue
    }

    if (scanningSelected) {
      if (!sawSelected || lineMatchesAnyChoice(line, choices)) {
        selectedAnswers.push(line)
        sawSelected = true
        continue
      }
      scanningSelected = false
    }

    explanationLines.push(line)
  }

  return { explicitItems, selectedAnswers, explanationLines }
}

function isNegativeQuestion(promptMarkdown: string) {
  return NEGATIVE_QUESTION_RE.test(promptMarkdown)
}

function choiceMatchesSelectedAnswer(choice: PromptChoice, selectedAnswers: string[]) {
  return selectedAnswers.some((answer) => containsMatch(answer, choice.text))
}

function explicitStatusForChoice(choice: PromptChoice, explicitItems: ExplicitReviewItem[]) {
  return explicitItems.find((item) => containsMatch(item.text, choice.text))
}

function tokensForCorrection(text: string) {
  const tokens = text.replace(/\*\*|==/g, '').match(TOKEN_RE) ?? []
  return Array.from(new Set(tokens.map((token) => token.toLowerCase()).filter((token) => !STOP_TOKENS.has(token))))
}

function correctionScore(choice: PromptChoice, line: string) {
  const lineText = normalizeForMatch(line)
  return tokensForCorrection(choice.text).filter((token) => lineText.includes(normalizeForMatch(token))).length
}

function correctionsForChoice(choice: PromptChoice, lines: string[], explicitCorrection?: string) {
  const corrections = explicitCorrection ? [explicitCorrection] : []

  for (const line of lines) {
    if (containsMatch(line, choice.text) || correctionScore(choice, line) >= 2) {
      corrections.push(line)
    }
  }

  return Array.from(new Set(corrections))
}

function renderInlineReviewText(text: string) {
  const parts = text.split(/(\*\*[^*]+?\*\*|==[^=]+?==)/g)
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith('==') && part.endsWith('==')) {
      return (
        <mark className="markdown-highlight" key={index}>
          {part.slice(2, -2)}
        </mark>
      )
    }
    return part
  })
}

function classifyChoicesForReveal(promptMarkdown: string, answerMarkdown: string): ChoiceReview | null {
  const { stemMarkdown, choices } = splitPromptChoices(promptMarkdown)
  if (choices.length < 2) return null

  const { explicitItems, selectedAnswers, explanationLines } = splitAnswerParts(answerMarkdown, choices)
  const hasExplicitReview = explicitItems.length > 0
  const negativeQuestion = isNegativeQuestion(promptMarkdown)
  const hasSelectedChoice = choices.some((choice) => choiceMatchesSelectedAnswer(choice, selectedAnswers))
  if (!hasExplicitReview && !hasSelectedChoice) return null

  const reviewedChoices = choices.map((choice) => {
    const explicitItem = explicitStatusForChoice(choice, explicitItems)
    const selected = choiceMatchesSelectedAnswer(choice, selectedAnswers)
    const status = explicitItem?.status ?? (negativeQuestion ? (selected ? 'incorrect' : 'correct') : selected ? 'correct' : 'incorrect')

    return {
      ...choice,
      status,
      corrections: status === 'incorrect' ? correctionsForChoice(choice, explanationLines, explicitItem?.correction) : [],
    }
  })

  return { stemMarkdown, choices: reviewedChoices }
}

function RevealedChoiceReview({ review, showCorrections = false }: { review: ChoiceReview; showCorrections?: boolean }) {
  const correctChoices = review.choices.filter((choice) => choice.status === 'correct')
  const incorrectChoices = review.choices.filter((choice) => choice.status === 'incorrect')
  const orderedChoices = [...correctChoices, ...incorrectChoices]

  return (
    <div className="revealed-choice-list">
      {orderedChoices.map((choice) => (
        <div className={`revealed-choice ${choice.status}`} key={`${choice.status}-${choice.order}-${choice.text}`}>
          <span className="revealed-choice-badge" aria-label={choice.status === 'correct' ? '맞는 보기' : '틀린 보기'}>
            {choice.status === 'correct' ? 'O' : 'X'}
          </span>
          <div className="revealed-choice-body">
            <p className="revealed-choice-text">{renderInlineReviewText(choice.text)}</p>
            {showCorrections &&
              choice.status === 'incorrect' &&
              choice.corrections.map((correction) => (
                <p className="revealed-choice-correction" key={correction}>
                  {renderInlineReviewText(correction)}
                </p>
              ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function RevealedPrompt({ promptMarkdown, answerMarkdown }: { promptMarkdown: string; answerMarkdown: string }) {
  const review = classifyChoicesForReveal(promptMarkdown, answerMarkdown)
  if (!review) return <MarkdownContent markdown={promptMarkdown} />

  const correctChoices = review.choices.filter((choice) => choice.status === 'correct')
  const incorrectChoices = review.choices.filter((choice) => choice.status === 'incorrect')
  const orderedChoices = [...correctChoices, ...incorrectChoices]
  const groupedPromptMarkdown = [
    review.stemMarkdown,
    ...orderedChoices.map((choice) => `- ${choice.text}`),
  ]
    .filter(Boolean)
    .join('\n')

  return <MarkdownContent markdown={groupedPromptMarkdown} />
}

function RevealedAnswer({ promptMarkdown, answerMarkdown }: { promptMarkdown: string; answerMarkdown: string }) {
  const review = classifyChoicesForReveal(promptMarkdown, answerMarkdown)
  if (!review) return <MarkdownContent markdown={answerMarkdown} stripLeadingAnswerPrefix />

  return <RevealedChoiceReview review={review} showCorrections />
}

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

      {question.prompt_markdown &&
        (showAnswer ? (
          <RevealedPrompt promptMarkdown={question.prompt_markdown} answerMarkdown={question.answer_markdown} />
        ) : (
          <MarkdownContent markdown={question.prompt_markdown} shuffleChoicesKey={choiceShuffleKey} />
        ))}

      {showAnswer && (
        <>
          <section className="answer-section" ref={answerRef}>
            <RevealedAnswer promptMarkdown={question.prompt_markdown} answerMarkdown={question.answer_markdown} />
          </section>
          {question.source_markdown && <SourceReferences markdown={question.source_markdown} />}
        </>
      )}
    </article>
  )
}
