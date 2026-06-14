import { Clipboard, Save } from 'lucide-react'
import { useRef, useState } from 'react'

export function MarkdownEditor({
  markdown,
  dirty,
  onChange,
  onSave,
  onUploadImage,
}: {
  markdown: string
  dirty: boolean
  onChange: (value: string) => void
  onSave: () => Promise<void>
  onUploadImage: (file: File) => Promise<string>
}) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  async function save() {
    setSaving(true)
    setMessage('')
    try {
      await onSave()
      setMessage('저장됨')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '저장하지 못했습니다.')
    } finally {
      setSaving(false)
    }
  }

  async function insertImage(file: File) {
    setUploading(true)
    setMessage('')
    try {
      const link = await onUploadImage(file)
      const textarea = textareaRef.current
      if (!textarea) {
        onChange(`${markdown}\n${link}\n`)
        return
      }

      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const prefix = markdown.slice(0, start)
      const suffix = markdown.slice(end)
      const needsLeadingBreak = prefix.length > 0 && !prefix.endsWith('\n')
      const needsTrailingBreak = suffix.length > 0 && !suffix.startsWith('\n')
      const insert = `${needsLeadingBreak ? '\n' : ''}${link}${needsTrailingBreak ? '\n' : ''}`
      const next = `${prefix}${insert}${suffix}`

      onChange(next)
      window.setTimeout(() => {
        const cursor = start + insert.length
        textarea.focus()
        textarea.selectionStart = cursor
        textarea.selectionEnd = cursor
      }, 0)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '이미지를 추가하지 못했습니다.')
    } finally {
      setUploading(false)
    }
  }

  function firstImageFromFiles(files: FileList | null) {
    return Array.from(files ?? []).find((file) => file.type.startsWith('image/')) ?? null
  }

  return (
    <section className="editor-panel">
      <header className="panel-title-row">
        <h2>Markdown</h2>
        <button type="button" className="primary-button" onClick={() => void save()} disabled={saving || !dirty}>
          <Save size={16} />
          <span>{saving ? '저장 중' : '저장'}</span>
        </button>
      </header>

      <textarea
        ref={textareaRef}
        value={markdown}
        onChange={(event) => onChange(event.target.value)}
        onPaste={(event) => {
          const file = firstImageFromFiles(event.clipboardData.files)
          if (!file) return
          event.preventDefault()
          void insertImage(file)
        }}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          const file = firstImageFromFiles(event.dataTransfer.files)
          if (!file) return
          event.preventDefault()
          void insertImage(file)
        }}
        spellCheck={false}
      />

      <div className="editor-hint">
        <Clipboard size={15} />
        <span>{uploading ? '이미지 저장 중' : message || (dirty ? '저장하지 않은 수정' : '이미지를 붙여넣거나 드롭할 수 있습니다.')}</span>
      </div>
    </section>
  )
}
