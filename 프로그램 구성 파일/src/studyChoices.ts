export function isChoiceStart(line: string) {
  return line.startsWith('- ')
}

export function readChoiceBlocks(lines: string[], start: number) {
  const blocks: string[][] = []
  let index = start
  while (index < lines.length && isChoiceStart(lines[index])) {
    const block = [lines[index]]
    index += 1
    while (index < lines.length && !isChoiceStart(lines[index])) {
      block.push(lines[index])
      index += 1
    }
    blocks.push(block)
  }
  return { blocks, end: index }
}

function seededScore(value: string) {
  let hash = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

export function shufflePromptChoices(markdown: string, key: string) {
  const lines = markdown.split(/\r?\n/)
  const start = lines.findIndex(isChoiceStart)
  if (start < 0) return markdown
  const { blocks } = readChoiceBlocks(lines, start)
  const shuffled = blocks.sort((a, b) => seededScore(`${key}:${a.join('\n')}`) - seededScore(`${key}:${b.join('\n')}`))
  return [...lines.slice(0, start), ...shuffled.flat()].join('\n')
}
