import type { TimelineEntry } from '@/api/types'
import { formatDate } from '@/lib/format'

export type TimelineDay = { date: string; events: TimelineEntry[] }

export function groupByDay(events: TimelineEntry[]): TimelineDay[] {
  const days: TimelineDay[] = []
  for (const event of events) {
    const date = formatDate(event.timestamp) || 'Unknown date'
    const current = days.at(-1)
    if (current?.date === date) current.events.push(event)
    else days.push({ date, events: [event] })
  }
  return days
}
