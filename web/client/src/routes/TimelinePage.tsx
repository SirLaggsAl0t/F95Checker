import { useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

import { apiGet } from '@/api/client'
import type { TimelineEntry } from '@/api/types'
import { Mdi } from '@/components/Mdi'
import { formatTimeline } from '@/lib/format'
import { groupByDay } from '@/lib/timeline'

export function TimelinePage() {
  const timeline = useQuery({ queryKey: ['timeline'], queryFn: () => apiGet<TimelineEntry[]>('/api/timeline') })
  const days = groupByDay(timeline.data ?? [])

  return (
    <main className="mx-auto max-w-3xl p-3 sm:p-6">
      <Link to="/" className="mb-4 inline-flex items-center gap-1 text-sm text-neutral-400 hover:text-white">
        <ArrowLeft aria-hidden className="size-4" /> Library
      </Link>
      <h1 className="mb-4 text-xl font-semibold">Timeline</h1>

      {timeline.isPending && <p className="text-neutral-400">Loading timeline…</p>}
      {timeline.isError && <p className="text-red-400">Could not load the timeline: {timeline.error.message}</p>}
      {timeline.isSuccess && days.length === 0 && (
        <p className="rounded border border-neutral-800 p-6 text-center text-neutral-400">No timeline events.</p>
      )}

      <div className="flex flex-col gap-5">
        {days.map((day) => (
          <section key={day.date}>
            <h2 className="mb-2 text-sm font-medium text-neutral-400">{day.date}</h2>
            <ul className="flex flex-col gap-1 text-sm">
              {day.events.map((event, index) => (
                <li key={`${event.game_id}-${event.timestamp}-${index}`} className="flex items-start gap-2">
                  <Mdi name={event.type.icon ?? ''} className="mt-0.5 size-4 shrink-0 text-neutral-400" />
                  <span className="flex-1 text-neutral-300">
                    <Link to={`/games/${event.game_id}`} className="font-medium hover:underline">
                      {event.game_name}
                    </Link>
                    {' — '}
                    {formatTimeline(event)}
                  </span>
                  <time className="shrink-0 text-xs text-neutral-500" dateTime={new Date(event.timestamp * 1000).toISOString()}>
                    {new Date(event.timestamp * 1000).toLocaleTimeString(undefined, {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </time>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </main>
  )
}
