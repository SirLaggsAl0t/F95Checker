import type { EnumItem, TimelineEvent } from '@/api/types'

export function formatDate(unix: number): string {
  if (!unix) return ''
  return new Date(unix * 1000).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function formatTimeline(event: TimelineEvent): string {
  const template = event.type.template
  if (!template) return event.type.display ?? event.type.name
  let index = 0
  return template.replace(/\{\}/g, () => event.arguments[index++] ?? '')
}

export function tagLabel(tag: EnumItem): string {
  return tag.text ?? tag.name
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase())
    .join('')
}

export function hueFor(name: string): number {
  let hash = 0
  for (const char of name) hash = (hash * 31 + char.charCodeAt(0)) % 360
  return hash
}

export function isInstalled(value: string): boolean {
  return value === 'True'
}

export function isFinished(value: string): boolean {
  return value === 'True'
}
