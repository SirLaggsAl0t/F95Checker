import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { apiGet } from '@/api/client'
import type { Enums, GameDetail, Label, Settings, Tab } from '@/api/types'
import { CoverImage } from '@/components/CoverImage'
import { GameEditPanel } from '@/components/GameEditPanel'
import { Mdi } from '@/components/Mdi'
import { PreviewGallery } from '@/components/PreviewGallery'
import { TagHighlightChip } from '@/components/TagChip'
import { formatDate, formatTimeline, isFinished, isInstalled, tagLabel } from '@/lib/format'

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-neutral-500">{label}</dt>
      <dd className="text-sm">{children || <span className="text-neutral-600">—</span>}</dd>
    </div>
  )
}

function TextBlock({ title, text, className }: { title: string; text: string; className?: string }) {
  if (!text) return null
  return (
    <section className={className}>
      <h2 className="mb-1 font-medium">{title}</h2>
      <p className="whitespace-pre-wrap break-words text-sm text-neutral-300">{text}</p>
    </section>
  )
}

export function GameDetailPage() {
  const { id } = useParams()
  const query = useQuery({
    queryKey: ['game', id],
    queryFn: () => apiGet<GameDetail>(`/api/games/${id}`),
    enabled: Boolean(id),
  })
  const labels = useQuery({ queryKey: ['labels'], queryFn: () => apiGet<Label[]>('/api/labels') })
  const tabs = useQuery({ queryKey: ['tabs'], queryFn: () => apiGet<Tab[]>('/api/tabs') })
  const settings = useQuery({ queryKey: ['settings'], queryFn: () => apiGet<Settings>('/api/settings') })
  const enums = useQuery({ queryKey: ['enums'], queryFn: () => apiGet<Enums>('/api/enums') })

  if (query.isPending) return <main className="mx-auto max-w-3xl p-4 text-neutral-400">Loading game…</main>
  if (query.isError) {
    return (
      <main className="mx-auto max-w-3xl p-4">
        <Link to="/" className="mb-3 inline-flex items-center gap-1 text-sm text-neutral-400 hover:text-white">
          <ArrowLeft className="size-4" /> Library
        </Link>
        <p className="text-red-400">Could not load this game: {query.error.message}</p>
      </main>
    )
  }

  const game = query.data
  const tags = [...(game.tags ?? []).map(tagLabel), ...(game.unknown_tags ?? [])]
  const hiddenEvents = new Set(settings.data?.hidden_timeline_events ?? [])
  const timelineEvents = game.timeline_events.filter((event) => !hiddenEvents.has(event.type.value))

  return (
    <main className="mx-auto max-w-3xl p-4 sm:p-6">
      <Link to="/" className="mb-4 inline-flex items-center gap-1 text-sm text-neutral-400 hover:text-white">
        <ArrowLeft className="size-4" /> Library
      </Link>

      <div className="flex flex-col gap-4 sm:flex-row">
        <CoverImage game={game} className="w-40 sm:w-48" width={640} />
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-semibold">{game.name}</h1>
          <p className="mt-0.5 text-sm text-neutral-400">
            {game.developer || 'Unknown developer'} · {game.version || 'Unknown version'} · {game.type?.name}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span className="flex items-center gap-1 text-sm" style={{ color: game.status?.color || undefined }}>
              <Mdi name={game.status?.icon ?? ''} />
              {game.status?.name}
            </span>
            {isInstalled(game.installed) && <span className="text-xs text-emerald-300">Installed</span>}
            {isFinished(game.finished) && <span className="text-xs text-sky-300">Finished</span>}
            {game.updated && <span className="text-xs text-amber-300">Update available</span>}
            {game.archived && <span className="text-xs text-neutral-400">Archived</span>}
          </div>
          {game.url && (
            <a
              href={game.url}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-flex items-center gap-1 text-sm text-sky-400 hover:underline"
            >
              F95zone thread <ExternalLink className="size-3.5" />
            </a>
          )}
        </div>
      </div>

      <GameEditPanel
        key={game.id}
        game={game}
        labels={labels.data ?? []}
        tabs={tabs.data ?? []}
        types={enums.data?.Type ?? []}
        statuses={enums.data?.Status ?? []}
        confirmOnRemove={settings.data?.confirm_on_remove ?? true}
      />

      <dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Field label="Score">{game.score ? game.score.toFixed(2) : ''}</Field>
        <Field label="Votes">{game.votes || ''}</Field>
        <Field label="My rating">{game.rating ? `${game.rating} / 5` : ''}</Field>
        <Field label="Added">{formatDate(game.added_on)}</Field>
        <Field label="Last updated">{formatDate(game.last_updated)}</Field>
        <Field label="Last checked">{game.last_check_version || ''}</Field>
        <Field label="F95 type">{game.type?.name}</Field>
        <Field label="Status">{game.status?.name}</Field>
      </dl>

      {tags.length > 0 && (
        <section className="mt-5">
          <h2 className="mb-1 font-medium">Tags</h2>
          <div className="flex flex-wrap gap-1">
            {game.tags.map((tag) => (
              <TagHighlightChip key={tag.value} tag={tag} settings={settings.data} enums={enums.data} />
            ))}
            {game.unknown_tags.map((tag, index) => (
              <span key={`${tag}-${index}`} className="rounded bg-neutral-800 px-1.5 py-0.5 text-xs text-neutral-300">
                {tag}
              </span>
            ))}
          </div>
        </section>
      )}

      <TextBlock title="Notes" text={game.notes} className="mt-5" />

      {game.downloads.length > 0 && (
        <section className="mt-5">
          <h2 className="mb-1 font-medium">Downloads</h2>
          <div className="flex flex-col gap-1.5">
            {game.downloads.map((host) => (
              <div key={host.name} className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
                <span className="text-neutral-400">{host.name}</span>
                {host.links.map((link, index) =>
                  link.url ? (
                    <a
                      key={`${link.name}-${index}`}
                      href={link.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sky-400 hover:underline"
                    >
                      {link.name || 'Link'}
                    </a>
                  ) : (
                    <span key={`${link.name}-${index}`} className="text-neutral-500">
                      {link.name}
                    </span>
                  ),
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <TextBlock title="Description" text={game.description} className="mt-5" />

      <PreviewGallery gameId={game.id} enabled={settings.data?.previews_enabled ?? false} />

      <TextBlock title="Changelog" text={game.changelog} className="mt-5" />

      {game.reviews.length > 0 && (
        <section className="mt-5">
          <h2 className="mb-1 font-medium">
            Reviews <span className="text-sm text-neutral-500">({game.reviews_total})</span>
          </h2>
          <ul className="flex flex-col gap-2">
            {game.reviews.map((review, index) => (
              <li key={`${review.user}-${index}`} className="rounded border border-neutral-800 p-3 text-sm">
                <div className="flex items-center justify-between gap-2 text-xs text-neutral-400">
                  <span>
                    {review.user} · ★{review.score}
                  </span>
                  <span>{formatDate(review.timestamp)}</span>
                </div>
                <p className="mt-1 whitespace-pre-wrap break-words text-neutral-300">{review.message}</p>
                {review.likes ? <p className="mt-1 text-xs text-neutral-500">{review.likes} likes</p> : null}
              </li>
            ))}
          </ul>
        </section>
      )}

      {timelineEvents.length > 0 && (
        <section className="mt-5">
          <h2 className="mb-1 font-medium">Timeline</h2>
          <ul className="flex flex-col gap-1 text-sm">
            {timelineEvents.map((event, index) => (
              <li key={`${event.timestamp}-${index}`} className="flex items-start gap-2">
                <Mdi name={event.type.icon ?? ''} className="mt-0.5 size-4 shrink-0 text-neutral-400" />
                <span className="flex-1 text-neutral-300">{formatTimeline(event)}</span>
                <span className="shrink-0 text-xs text-neutral-500">{formatDate(event.timestamp)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  )
}
