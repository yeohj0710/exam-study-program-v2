import { useState } from 'react'
import { openSourceReference } from '../api'
import type { Question } from '../types'
import { MarkdownContent } from './MarkdownContent'

const SOURCE_LINE_RE = /^(?:출처|reference|source)\s*[:：]\s*/i
const IMAGE_LINE_RE = /^!\[[^\]]*]\([^)]+\)\s*$/
const IMAGE_PATH_RE = /!\[[^\]]*]\(([^)]+)\)/g
const SOURCE_PAGE_TOKEN_RE = /(?:p|page|쪽|페이지|slide|슬라이드)\.?\s*(\d+)/i
const SOURCE_PAGE_IMAGE_RE = (page: string) => new RegExp(`source-p0*${page}(?:\\D|$)`, 'i')
const NOTICE_LINE_RE = /^문제\s*출제\s*공지(?:\s*대응)?\s*[:：]/i
const SOURCE_CONTINUATION_RE = /^\s+\S/
const PROMPT_CHOICE_PREFIX_RE = /^(?:[\u2460-\u2473\u3251-\u325F]\s*[.)、:：-]?|\(?\d{1,2}\)?\s*(?:번)?[.)、:：-]?)\s*/
const ANSWER_LABEL_RE = /^(?:답|answer)\s*[:：]\s*/i
const EXPLICIT_REVIEW_RE = /^([Oo0○Xx×✕])\s*[:.)、-]?\s*(.+)$/
const REVIEW_ARROW_RE = /\s*(?:->|=>|→|⇒)\s*/
const REVIEW_NOTE_RE = /\s+\/\/\s+/
const NEGATIVE_QUESTION_RE = /(옳지\s*않|틀린|잘못된|바르지\s*않|해당하지\s*않|아닌|거리가\s*먼|관련이\s*없는|무관한)/
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

function splitOnFirstDelimiter(value: string, delimiter: RegExp) {
  const match = delimiter.exec(value)
  if (!match || match.index < 0) return [value] as const

  return [value.slice(0, match.index), value.slice(match.index + match[0].length)] as const
}

function parseExplicitReviewLine(line: string): ExplicitReviewItem | null {
  const match = line.match(EXPLICIT_REVIEW_RE)
  if (!match) return null

  const status: ChoiceReviewStatus = /[Oo0○]/.test(match[1]) ? 'correct' : 'incorrect'
  const body = match[2].trim()
  const [text, correction] =
    status === 'correct' ? splitOnFirstDelimiter(body, REVIEW_NOTE_RE) : splitOnFirstDelimiter(body, REVIEW_ARROW_RE)
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

function splitCorrectionForDisplay(correction: string) {
  const trimmed = correction.trim()
  const sentenceMatch = trimmed.match(/^(.+?[.!?。！？])\s+(.+)$/)
  if (!sentenceMatch) {
    return { fixedText: trimmed, noteText: '' }
  }

  return { fixedText: sentenceMatch[1], noteText: sentenceMatch[2] }
}

function RevealedChoiceSupplement({ status, supplement }: { status: ChoiceReviewStatus; supplement: string }) {
  if (status === 'correct') {
    return (
      <div className="revealed-choice-explanation">
        <p className="revealed-choice-note">{renderInlineReviewText(supplement)}</p>
      </div>
    )
  }

  const correction = supplement
  const { fixedText, noteText } = splitCorrectionForDisplay(correction)

  return (
    <div className="revealed-choice-correction">
      <p className="revealed-choice-fix">{renderInlineReviewText(fixedText)}</p>
      {noteText ? <p className="revealed-choice-note">{renderInlineReviewText(noteText)}</p> : null}
    </div>
  )
}

function classifyChoicesForReveal(
  promptMarkdown: string,
  answerMarkdown: string,
  options: { explicitOnly?: boolean } = {},
): ChoiceReview | null {
  const { stemMarkdown, choices } = splitPromptChoices(promptMarkdown)
  if (choices.length < 2) return null

  const { explicitItems, selectedAnswers, explanationLines } = splitAnswerParts(answerMarkdown, choices)
  const hasExplicitReview = explicitItems.length > 0
  const negativeQuestion = isNegativeQuestion(promptMarkdown)
  const hasSelectedChoice = choices.some((choice) => choiceMatchesSelectedAnswer(choice, selectedAnswers))
  if (!hasExplicitReview && !hasSelectedChoice) return null

  const choicesToReview = options.explicitOnly && hasExplicitReview
    ? choices.filter((choice) => explicitStatusForChoice(choice, explicitItems))
    : choices

  if (choicesToReview.length === 0) return null

  const reviewedChoices = choicesToReview.map((choice) => {
    const explicitItem = explicitStatusForChoice(choice, explicitItems)
    const selected = choiceMatchesSelectedAnswer(choice, selectedAnswers)
    const status = explicitItem?.status ?? (negativeQuestion ? (selected ? 'incorrect' : 'correct') : selected ? 'correct' : 'incorrect')
    const explicitSupplement = explicitItem?.correction ? [explicitItem.correction] : []

    return {
      ...choice,
      status,
      corrections: status === 'incorrect' ? correctionsForChoice(choice, explanationLines, explicitItem?.correction) : explicitSupplement,
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
              choice.corrections.map((correction) => (
                <RevealedChoiceSupplement status={choice.status} supplement={correction} key={correction} />
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

  return (
    <div className="revealed-prompt">
      <MarkdownContent markdown={groupedPromptMarkdown} />
    </div>
  )
}

function RevealedAnswer({ promptMarkdown, answerMarkdown }: { promptMarkdown: string; answerMarkdown: string }) {
  const review = classifyChoicesForReveal(promptMarkdown, answerMarkdown)
  if (!review) return <MarkdownContent markdown={answerMarkdown} stripLeadingAnswerPrefix answerMode />

  return <RevealedChoiceReview review={review} showCorrections />
}

function hasExplicitChoiceReview(markdown: string) {
  return markdown
    .split(/\r?\n/)
    .map((line) => line.trim())
    .some((line) => Boolean(parseExplicitReviewLine(line)))
}

function shouldPrioritizeChoiceExplanation(question: Question) {
  return hasExplicitChoiceReview(question.choice_explanation_markdown)
}

function shouldShowPrimaryAnswerLabel(question: Question) {
  return !shouldPrioritizeChoiceExplanation(question)
}

function StructuredChoiceExplanation({
  promptMarkdown,
  answerMarkdown,
  choiceExplanationMarkdown,
}: {
  promptMarkdown: string
  answerMarkdown: string
  choiceExplanationMarkdown: string
}) {
  if (!choiceExplanationMarkdown.trim()) return null

  const reviewMarkdown = [answerMarkdown, choiceExplanationMarkdown].filter(Boolean).join('\n')
  const review = hasExplicitChoiceReview(choiceExplanationMarkdown)
    ? classifyChoicesForReveal(promptMarkdown, reviewMarkdown, { explicitOnly: true })
    : null

  return (
    <section className="choice-explanation-section">
      <p className="markdown-answer-label">
        <span>보기 해설</span>
      </p>
      {review ? <RevealedChoiceReview review={review} showCorrections /> : <MarkdownContent markdown={choiceExplanationMarkdown} answerMode />}
    </section>
  )
}

function StructuredAnswer({ question }: { question: Question }) {
  const hasStructuredExplanation = Boolean(question.explanation_markdown.trim() || question.choice_explanation_markdown.trim())
  if (!hasStructuredExplanation) {
    return <RevealedAnswer promptMarkdown={question.prompt_markdown} answerMarkdown={question.answer_markdown} />
  }

  const directAnswer = question.answer_markdown.trim() || '답 없음'
  const shouldHideDirectAnswer = shouldPrioritizeChoiceExplanation(question)

  return (
    <>
      <StructuredChoiceExplanation
        promptMarkdown={question.prompt_markdown}
        answerMarkdown={question.answer_markdown}
        choiceExplanationMarkdown={question.choice_explanation_markdown}
      />
      {!shouldHideDirectAnswer && (
        <MarkdownContent markdown={directAnswer} stripLeadingAnswerPrefix answerMode />
      )}
      {question.explanation_markdown.trim() && (
        <section className="explanation-section">
          <p className="markdown-answer-label">
            <span>배경 설명</span>
          </p>
          <MarkdownContent markdown={question.explanation_markdown} answerMode />
        </section>
      )}
    </>
  )
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

    if (NOTICE_LINE_RE.test(normalized)) {
      flushReference()
      evidenceLines.push(line)
      continue
    }

    if (currentReference && SOURCE_CONTINUATION_RE.test(line) && normalized && !IMAGE_LINE_RE.test(normalized)) {
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

function isLocalFileReference(reference: string) {
  return /^[a-zA-Z]:\\/.test(reference) || /^\\\\/.test(reference)
}

function sourceAssetUrl(path: string) {
  if (/^[a-zA-Z]:\\/.test(path)) return `/api/external-asset?path=${encodeURIComponent(path)}`
  if (path.startsWith('assets/')) return `/${path.split('/').map(encodeURIComponent).join('/')}`
  return path
}

function sourceReferenceFallbackUrl(reference: string, evidenceMarkdown: string) {
  if (isLocalFileReference(reference)) return ''

  const imagePaths = Array.from(evidenceMarkdown.matchAll(IMAGE_PATH_RE), (match) => match[1]).filter(Boolean)
  if (!imagePaths.length) return ''

  const page = reference.match(SOURCE_PAGE_TOKEN_RE)?.[1]
  if (page) {
    const matchingPath = imagePaths.find((path) => SOURCE_PAGE_IMAGE_RE(page).test(path))
    if (matchingPath) return sourceAssetUrl(matchingPath)
  }

  return imagePaths.length === 1 ? sourceAssetUrl(imagePaths[0]) : ''
}

function SourceReferences({ markdown }: { markdown: string }) {
  const [opening, setOpening] = useState('')
  const { references: items, evidenceMarkdown } = splitSourceMarkdown(markdown)
  if (!items.length && !evidenceMarkdown) return null

  async function open(reference: string) {
    const fallbackUrl = sourceReferenceFallbackUrl(reference, evidenceMarkdown)
    if (fallbackUrl) {
      window.open(fallbackUrl, '_blank', 'noopener,noreferrer')
      return
    }

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
  if (!question) {
    return (
      <article className="question-view empty">
        <p>표시할 문제가 없습니다.</p>
      </article>
    )
  }

  return (
    <article className={question.progress.memorized ? 'question-view memorized' : 'question-view'}>
      <div className="question-scroll-anchor" aria-hidden="true">
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
          <section className="answer-section">
            {shouldShowPrimaryAnswerLabel(question) && (
              <p className="markdown-answer-label primary">
                <span>답</span>
              </p>
            )}
            <StructuredAnswer question={question} />
          </section>
          {question.source_markdown && <SourceReferences markdown={question.source_markdown} />}
        </>
      )}
    </article>
  )
}
