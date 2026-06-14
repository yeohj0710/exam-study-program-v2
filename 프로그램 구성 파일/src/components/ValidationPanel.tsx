import { AlertTriangle, CheckCircle2 } from 'lucide-react'
import type { ValidationIssue, ValidationReport } from '../types'

function issueLabel(issue: ValidationIssue) {
  if (issue.line) return `${issue.code} · line ${issue.line}`
  return issue.code
}

export function ValidationPanel({
  validation,
  localIssues,
}: {
  validation: ValidationReport | null
  localIssues: ValidationIssue[]
}) {
  const final = validation?.final
  const issues = localIssues.length ? localIssues : final?.issues ?? []
  const ok = Boolean(final?.ok) && issues.every((issue) => issue.severity !== 'error')

  return (
    <section className="validation-panel">
      <header className="panel-title-row">
        <h2>검증</h2>
        {ok ? <CheckCircle2 className="ok-icon" size={20} /> : <AlertTriangle className="warn-icon" size={20} />}
      </header>

      <div className={ok ? 'validation-summary ok' : 'validation-summary'}>
        <span>{final?.studyset_count ?? 0}세트</span>
        <span>{final?.question_count ?? 0}문제</span>
        <span>{issues.length}이슈</span>
      </div>

      <div className="issue-list">
        {issues.length === 0 ? (
          <p>확인할 문제가 없습니다.</p>
        ) : (
          issues.map((issue, index) => (
            <article className={`issue-item ${issue.severity}`} key={`${issue.code}-${issue.question_id}-${index}`}>
              <strong>{issueLabel(issue)}</strong>
              <p>{issue.message}</p>
            </article>
          ))
        )}
      </div>
    </section>
  )
}
