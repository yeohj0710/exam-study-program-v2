import type {
  AssetUploadResponse,
  QuestionProgress,
  SourceOpenResponse,
  StudySet,
  StudySetPayload,
  ValidationReport,
} from './types'

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || response.statusText)
  }
  return (await response.json()) as T
}

export async function fetchStudySets(): Promise<StudySet[]> {
  const payload = await requestJson<{ studysets: StudySet[] }>('/api/studysets')
  return payload.studysets
}

export async function createStudySet(title: string): Promise<StudySet> {
  return requestJson<StudySet>('/api/studysets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
}

export async function fetchStudySet(studysetId: string): Promise<StudySetPayload> {
  return requestJson<StudySetPayload>(`/api/studysets/${encodeURIComponent(studysetId)}`)
}

export async function saveStudySet(studysetId: string, markdown: string): Promise<StudySetPayload> {
  return requestJson<StudySetPayload>(`/api/studysets/${encodeURIComponent(studysetId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ markdown }),
  })
}

export async function exportStudySetPdf(studysetId: string): Promise<{ blob: Blob; filename: string }> {
  const response = await fetch(`/api/studysets/${encodeURIComponent(studysetId)}/pdf`)
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || response.statusText)
  }
  const filename = filenameFromDisposition(response.headers.get('content-disposition'), `${studysetId}_문답.pdf`)
  return { blob: await response.blob(), filename }
}

function filenameFromDisposition(header: string | null, fallback: string) {
  if (!header) return fallback
  const encoded = header.match(/filename\*=utf-8''([^;]+)/i)
  if (encoded) {
    try {
      return decodeURIComponent(encoded[1])
    } catch {
      return fallback
    }
  }
  const quoted = header.match(/filename="?([^";]+)"?/i)
  return quoted?.[1] ?? fallback
}

export async function uploadStudySetAsset(
  studysetId: string,
  contentBase64: string,
  contentType: string,
  altText: string,
): Promise<AssetUploadResponse> {
  return requestJson<AssetUploadResponse>(`/api/studysets/${encodeURIComponent(studysetId)}/assets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content_base64: contentBase64,
      content_type: contentType,
      alt_text: altText,
    }),
  })
}

export async function patchQuestionProgress(
  questionId: string,
  action: 'seen' | 'reveal' | 'memorized',
): Promise<QuestionProgress> {
  const payload = await requestJson<{ progress: QuestionProgress }>(
    `/api/questions/${encodeURIComponent(questionId)}/progress`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    },
  )
  return payload.progress
}

export async function restoreQuestionProgress(questionId: string): Promise<QuestionProgress> {
  const payload = await requestJson<{ progress: QuestionProgress }>(
    `/api/questions/${encodeURIComponent(questionId)}/progress`,
    { method: 'DELETE' },
  )
  return payload.progress
}

export async function fetchValidation(): Promise<ValidationReport> {
  return requestJson<ValidationReport>('/api/validation')
}

export async function openSourceReference(reference: string): Promise<SourceOpenResponse> {
  return requestJson<SourceOpenResponse>('/api/source/resolve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reference }),
  })
}

export async function shutdownApp(): Promise<void> {
  await fetch('/api/shutdown', { method: 'POST' })
}
