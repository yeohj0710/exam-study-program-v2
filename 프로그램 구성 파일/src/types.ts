export type ThemeMode = 'light' | 'dark'

export type ValidationIssue = {
  severity: 'error' | 'warning'
  code: string
  message: string
  question_id?: string | null
  line?: number | null
}

export type QuestionProgress = {
  question_id: string
  memorized: boolean
  seen_count: number
  reveal_count: number
  last_seen_at?: number | null
  updated_at: number
}

export type Question = {
  id: string
  studyset_id: string
  ordinal: number
  title: string
  prompt_markdown: string
  answer_markdown: string
  source_markdown: string
  note_markdown: string
  asset_paths: string[]
  issues: ValidationIssue[]
  progress: QuestionProgress
}

export type StudySet = {
  id: string
  title: string
  slug: string
  path: string
  updated_at: number
  question_count: number
  issue_count: number
}

export type StudySetPayload = {
  id: string
  title: string
  markdown: string
  questions: Question[]
  issues: ValidationIssue[]
}

export type FinalValidationReport = {
  ok: boolean
  studyset_count: number
  question_count: number
  issue_count: number
  issues: ValidationIssue[]
}

export type ValidationReport = {
  ok: boolean
  card_count: number
  missing_asset_count: number
  missing_source_count: number
  issues: ValidationIssue[]
  final?: FinalValidationReport
}

export type AssetUploadResponse = {
  relative_path: string
  markdown: string
  path: string
  sha1: string
}

export type SourceOpenResponse = {
  ok: boolean
  path: string
  page?: number | null
}
