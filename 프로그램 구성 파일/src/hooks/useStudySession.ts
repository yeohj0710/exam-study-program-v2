import { useCallback, useMemo, useState } from 'react'
import type { Question } from '../types'

type StoredOrder = {
  studysetId: string
  signature: string
  orderIds: string[]
  cursor: number
  round: number
}

const emptyOrder: StoredOrder = {
  studysetId: '',
  signature: '',
  orderIds: [],
  cursor: 0,
  round: 0,
}

function storageKey(studysetId: string) {
  return `exam-study.order.v1.${studysetId}`
}

function questionSignature(questions: Question[]) {
  return questions.map((question) => question.id).join('\u001f')
}

function seededScore(value: string, seed: number) {
  let hash = 2166136261 ^ seed
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

function shuffledIds(questions: Question[], round: number) {
  return questions
    .map((question) => ({ id: question.id, sort: seededScore(`${question.id}:${round}`, round + 1) }))
    .sort((a, b) => a.sort - b.sort)
    .map((item) => item.id)
}

function boundaryCooldownSize(size: number) {
  if (size <= 1) return 0
  if (size <= 3) return 1
  return Math.min(Math.floor(size / 2), Math.max(2, Math.ceil(size * 0.2)))
}

function keepRecentTailAwayFromNextHead(previousOrderIds: string[], nextOrderIds: string[]) {
  const size = nextOrderIds.length
  const cooldownSize = Math.min(boundaryCooldownSize(size), previousOrderIds.length)
  if (cooldownSize === 0) return nextOrderIds

  const recentTail = new Set(previousOrderIds.slice(-cooldownSize))
  const next = [...nextOrderIds]
  for (let headIndex = 0; headIndex < cooldownSize; headIndex += 1) {
    if (!recentTail.has(next[headIndex])) continue
    const swapIndex = next.findIndex((id, index) => index >= cooldownSize && !recentTail.has(id))
    if (swapIndex < 0) continue
    const current = next[headIndex]
    next[headIndex] = next[swapIndex]
    next[swapIndex] = current
  }

  return next
}

function shuffledIdsForNextRound(questions: Question[], round: number, previousOrderIds: string[]) {
  return keepRecentTailAwayFromNextHead(previousOrderIds, shuffledIds(questions, round))
}

function isValidOrder(orderIds: string[], questions: Question[]) {
  const ids = new Set(questions.map((question) => question.id))
  return orderIds.length === questions.length && orderIds.every((id) => ids.has(id))
}

function normalizeOrder(order: StoredOrder, studysetId: string, questions: Question[]): StoredOrder {
  if (!studysetId || questions.length === 0) return { ...emptyOrder, studysetId }

  const signature = questionSignature(questions)
  if (order.studysetId === studysetId && order.signature === signature && isValidOrder(order.orderIds, questions)) {
    return {
      ...order,
      cursor: Math.min(order.cursor, Math.max(order.orderIds.length - 1, 0)),
    }
  }

  try {
    const raw = window.localStorage.getItem(storageKey(studysetId))
    if (raw) {
      const parsed = JSON.parse(raw) as StoredOrder
      if (parsed.signature === signature && isValidOrder(parsed.orderIds, questions)) {
        return {
          ...parsed,
          studysetId,
          cursor: Math.min(parsed.cursor, Math.max(parsed.orderIds.length - 1, 0)),
          round: Number.isFinite(parsed.round) ? parsed.round : 0,
        }
      }
    }
  } catch {
    // Ignore corrupted session order and rebuild below.
  }

  return {
    studysetId,
    signature,
    orderIds: shuffledIds(questions, 0),
    cursor: 0,
    round: 0,
  }
}

function saveOrder(order: StoredOrder) {
  if (!order.studysetId) return
  window.localStorage.setItem(storageKey(order.studysetId), JSON.stringify(order))
}

export function useStudySession(studysetId: string, questions: Question[]) {
  const [storedOrder, setStoredOrder] = useState<StoredOrder>(emptyOrder)
  const [showAnswer, setShowAnswer] = useState(false)

  const order = useMemo(() => normalizeOrder(storedOrder, studysetId, questions), [questions, storedOrder, studysetId])
  const questionsById = useMemo(() => new Map(questions.map((question) => [question.id, question])), [questions])
  const orderedQuestions = useMemo(
    () => order.orderIds.map((id) => questionsById.get(id)).filter((question): question is Question => Boolean(question)),
    [order.orderIds, questionsById],
  )
  const currentQuestion = orderedQuestions[order.cursor] ?? null

  const commitOrder = useCallback((nextOrder: StoredOrder) => {
    saveOrder(nextOrder)
    setStoredOrder(nextOrder)
  }, [])

  const nextQuestion = useCallback(() => {
    if (!orderedQuestions.length) return
    const isLast = order.cursor >= orderedQuestions.length - 1
    if (isLast) {
      const nextOrder = {
        studysetId,
        signature: questionSignature(questions),
        orderIds: shuffledIdsForNextRound(questions, order.round + 1, order.orderIds),
        cursor: 0,
        round: order.round + 1,
      }
      commitOrder(nextOrder)
    } else {
      commitOrder({ ...order, cursor: order.cursor + 1 })
    }
    setShowAnswer(false)
  }, [commitOrder, order, orderedQuestions.length, questions, studysetId])

  const reshuffle = useCallback(() => {
    const nextOrder = {
      studysetId,
      signature: questionSignature(questions),
      orderIds: shuffledIdsForNextRound(questions, order.round + 1, order.orderIds),
      cursor: 0,
      round: order.round + 1,
    }
    commitOrder(nextOrder)
    setShowAnswer(false)
  }, [commitOrder, order.orderIds, order.round, questions, studysetId])

  const goToQuestion = useCallback(
    (questionId: string) => {
      const index = orderedQuestions.findIndex((question) => question.id === questionId)
      if (index >= 0) {
        commitOrder({ ...order, cursor: index })
        setShowAnswer(false)
      }
    },
    [commitOrder, order, orderedQuestions],
  )

  return {
    showAnswer,
    setShowAnswer,
    currentQuestion,
    orderedQuestions,
    safeCursor: order.cursor,
    total: orderedQuestions.length,
    nextQuestion,
    reshuffle,
    goToQuestion,
  }
}
