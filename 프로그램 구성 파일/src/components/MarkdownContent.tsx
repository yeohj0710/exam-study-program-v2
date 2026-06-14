import { useState } from 'react'

function imageUrl(path: string) {
  if (/^[a-zA-Z]:\\/.test(path)) return `/api/external-asset?path=${encodeURIComponent(path)}`
  if (path.startsWith('assets/')) return `/${path.split('/').map(encodeURIComponent).join('/')}`
  return path
}

function renderInline(text: string) {
  const parts = text.split(/(\*\*[^*]+?\*\*)/g)
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>
    }
    return part
  })
}

function seededScore(value: string) {
  let hash = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

function isChoiceStart(line: string) {
  return line.startsWith('- ')
}

function shuffleBlocks(blocks: string[][], key: string | undefined) {
  if (!key || blocks.length < 2) return blocks
  return [...blocks].sort((a, b) => seededScore(`${key}:${a.join('\n')}`) - seededScore(`${key}:${b.join('\n')}`))
}

function trimEmptyEdges(block: string[]) {
  let start = 0
  let end = block.length
  while (start < end && !block[start].trim()) start += 1
  while (end > start && !block[end - 1].trim()) end -= 1
  return block.slice(start, end)
}

function renderLine(line: string, key: string) {
  const normalized = line.trimStart()
  const image = normalized.match(/^!\[([^\]]*)]\(([^)]+)\)\s*$/)
  if (image) {
    return <MarkdownImage key={key} alt={image[1]} path={image[2]} />
  }
  if (!normalized.trim()) return <div className="markdown-space" key={key} />
  if (/^(?:출처|reference|source)\s*[:：]/i.test(normalized)) {
    return (
      <p className="markdown-source" key={key}>
        {renderInline(normalized)}
      </p>
    )
  }
  if (normalized.startsWith('### ')) return <h3 key={key}>{renderInline(normalized.slice(4))}</h3>
  if (normalized.startsWith('## ')) return <h2 key={key}>{renderInline(normalized.slice(3))}</h2>
  if (normalized.startsWith('# ')) return <h1 key={key}>{renderInline(normalized.slice(2))}</h1>
  return <p key={key}>{renderInline(normalized)}</p>
}

function MarkdownImage({ alt, path }: { alt: string; path: string }) {
  const [failed, setFailed] = useState(false)
  const src = imageUrl(path)
  const title = alt || path

  if (failed) {
    return (
      <figure className="markdown-image broken" title={path}>
        <div>
          <strong>이미지를 불러올 수 없습니다.</strong>
        </div>
      </figure>
    )
  }

  return (
    <figure className="markdown-image" title={title}>
      <img src={src} alt={alt} loading="lazy" onError={() => setFailed(true)} />
    </figure>
  )
}

function renderChoiceBlock(block: string[], key: string) {
  const [firstLine, ...rest] = trimEmptyEdges(block)
  if (!firstLine) return null

  return (
    <div className="markdown-choice" key={key}>
      <p>{renderInline(firstLine.slice(2).trim())}</p>
      {rest.map((line, index) => renderLine(line, `${key}-${index}`))}
    </div>
  )
}

function renderLines(lines: string[], shuffleChoicesKey?: string) {
  const output = []
  let index = 0
  while (index < lines.length) {
    if (!isChoiceStart(lines[index])) {
      output.push(renderLine(lines[index], `${index}-${lines[index]}`))
      index += 1
      continue
    }

    const group: string[][] = []
    while (index < lines.length && isChoiceStart(lines[index])) {
      const block = [lines[index]]
      index += 1
      while (index < lines.length && !isChoiceStart(lines[index])) {
        block.push(lines[index])
        index += 1
      }
      group.push(block)
    }

    shuffleBlocks(group, shuffleChoicesKey).forEach((block, blockIndex) => {
      output.push(renderChoiceBlock(block, `choice-${index}-${blockIndex}-${block[0]}`))
    })
  }
  return output
}

export function MarkdownContent({ markdown, shuffleChoicesKey }: { markdown: string; shuffleChoicesKey?: string }) {
  const lines = markdown.split(/\r?\n/)
  return <div className="markdown-content">{renderLines(lines, shuffleChoicesKey)}</div>
}
