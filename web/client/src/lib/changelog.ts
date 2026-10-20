export type ChangelogLine = { text: string; kind: 'add' | 'remove' | 'note' }
export type ChangelogSection = { version: string; lines: ChangelogLine[] }

const HEADER = /^(?:version\s*|v)\d+(?:\.\d+)*[a-z]?\b/i
const BARE_HEADER = /^\d+(?:\.\d+)+[a-z]?\s*(?:[-–—:(]|$)/i
const ADD = /^\[\+\]\s*/
const REMOVE = /^\[-\]\s*/
const BULLET = /^[-*•·]\s+/

function toLine(raw: string): ChangelogLine {
  if (ADD.test(raw)) return { text: raw.replace(ADD, ''), kind: 'add' }
  if (REMOVE.test(raw)) return { text: raw.replace(REMOVE, ''), kind: 'remove' }
  return { text: raw.replace(BULLET, ''), kind: 'note' }
}

export function parseChangelog(text: string): ChangelogSection[] {
  const sections: ChangelogSection[] = []
  let current: ChangelogSection | undefined

  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim()
    if (!line) continue
    if (HEADER.test(line) || BARE_HEADER.test(line)) {
      current = { version: line.replace(/[:\s]+$/, ''), lines: [] }
      sections.push(current)
    } else {
      if (!current) {
        current = { version: '', lines: [] }
        sections.push(current)
      }
      current.lines.push(toLine(line))
    }
  }

  return sections
}
