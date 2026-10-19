import { useQuery } from '@tanstack/react-query'
import { ArrowDownUp, LayoutGrid, List } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiGet } from '@/api/client'
import type { Enums, GameSummary, Label, Settings, Tab } from '@/api/types'
import { AddGameBar } from '@/components/AddGameBar'
import { CoverImage } from '@/components/CoverImage'
import { FilterSidebar } from '@/components/FilterSidebar'
import { LabelEditor } from '@/components/LabelEditor'
import { Mdi } from '@/components/Mdi'
import { RefreshButton } from '@/components/RefreshButton'
import { TabEditor } from '@/components/TabEditor'
import { TabIcon } from '@/components/TabIcon'
import type { LibraryPrefs, SortKey } from '@/lib/filters'
import { applyFilters, applySorts, loadPrefs, savePrefs } from '@/lib/filters'
import { formatDate, isFinished, isInstalled } from '@/lib/format'
import { cn } from '@/lib/utils'

function Badge({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={cn('rounded px-1.5 py-0.5 text-[11px] font-medium', className)}>{children}</span>
  )
}

function GameBadges({ game }: { game: GameSummary }) {
  return (
    <>
      {isInstalled(game.installed) && <Badge className="bg-emerald-900/60 text-emerald-300">Installed</Badge>}
      {isFinished(game.finished) && <Badge className="bg-sky-900/60 text-sky-300">Finished</Badge>}
      {game.updated && <Badge className="bg-amber-900/60 text-amber-300">Update</Badge>}
      {game.archived && <Badge className="bg-neutral-800 text-neutral-400">Archived</Badge>}
    </>
  )
}

function GameRow({ game, tab }: { game: GameSummary; tab?: Tab }) {
  return (
    <Link
      to={`/games/${game.id}`}
      className="flex gap-3 rounded-lg border border-neutral-800 bg-neutral-900/60 p-2 transition-colors hover:border-neutral-700 hover:bg-neutral-900 sm:gap-4 sm:p-3"
    >
      <CoverImage game={game} className="w-16 sm:w-20" />
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <h2 className="truncate font-medium">{game.name}</h2>
          <span className="flex shrink-0 items-center gap-1 text-xs text-neutral-400">
            {game.score ? <>{game.score.toFixed(1)}</> : null}
            {game.votes ? <span className="text-neutral-600">({game.votes})</span> : null}
            {game.rating ? <span aria-label={`Rating ${game.rating} of 5`}>★{game.rating}</span> : null}
          </span>
        </div>
        <p className="truncate text-sm text-neutral-400">
          {game.developer || 'Unknown developer'} · {game.version || 'Unknown version'}
          {game.type?.name ? ` · ${game.type.name}` : ''}
          {tab && tab.name ? ` · ${tab.name}` : ''}
        </p>
        <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
          <span className="flex items-center gap-1 text-xs" style={{ color: game.status?.color || undefined }}>
            <Mdi name={game.status?.icon ?? ''} />
            {game.status?.name}
          </span>
          <GameBadges game={game} />
          {game.added_on ? <span className="text-xs text-neutral-500">Added {formatDate(game.added_on)}</span> : null}
        </div>
      </div>
    </Link>
  )
}

function GameCard({ game }: { game: GameSummary }) {
  return (
    <Link
      to={`/games/${game.id}`}
      className="flex flex-col overflow-hidden rounded-lg border border-neutral-800 bg-neutral-900/60 transition-colors hover:border-neutral-700 hover:bg-neutral-900"
    >
      <CoverImage game={game} className="w-full" />
      <div className="flex min-w-0 flex-1 flex-col gap-1 p-2">
        <h2 className="truncate font-medium">{game.name}</h2>
        <p className="truncate text-xs text-neutral-400">
          {game.developer || 'Unknown developer'} · {game.version || 'Unknown version'}
        </p>
        <div className="mt-auto flex flex-wrap items-center gap-1 pt-1">
          <span className="flex items-center gap-1 text-xs" style={{ color: game.status?.color || undefined }}>
            <Mdi name={game.status?.icon ?? ''} />
          </span>
          <GameBadges game={game} />
          {game.rating ? <span className="ml-auto text-xs text-neutral-300">★{game.rating}</span> : null}
        </div>
      </div>
    </Link>
  )
}

const SORTS: { value: SortKey; label: string }[] = [
  { value: 'name', label: 'Name' },
  { value: 'added_on', label: 'Added' },
  { value: 'last_updated', label: 'Updated' },
  { value: 'score', label: 'Score' },
  { value: 'rating', label: 'Rating' },
  { value: 'votes', label: 'Votes' },
]

export function LibraryPage() {
  const [prefs, setPrefs] = useState<LibraryPrefs>(() => loadPrefs())

  const games = useQuery({ queryKey: ['games'], queryFn: () => apiGet<GameSummary[]>('/api/games') })
  const tabs = useQuery({ queryKey: ['tabs'], queryFn: () => apiGet<Tab[]>('/api/tabs') })
  const labels = useQuery({ queryKey: ['labels'], queryFn: () => apiGet<Label[]>('/api/labels') })
  const settings = useQuery({ queryKey: ['settings'], queryFn: () => apiGet<Settings>('/api/settings') })
  const enums = useQuery({ queryKey: ['enums'], queryFn: () => apiGet<Enums>('/api/enums') })

  useEffect(() => savePrefs(prefs), [prefs])

  const update = (patch: Partial<LibraryPrefs>) => setPrefs((current) => ({ ...current, ...patch }))
  const setFilters = (filters: LibraryPrefs['filters']) => update({ filters })

  const tabList = tabs.data ?? []
  const labelList = labels.data ?? []
  const defaultLabel = settings.data?.default_tab_is_new ? 'New' : 'Default'
  const sort = prefs.sorts[0] ?? { key: 'name' as SortKey, dir: 'asc' as const }

  const visible = useMemo(
    () => applySorts(applyFilters(games.data ?? [], prefs.filters), prefs.sorts),
    [games.data, prefs.filters, prefs.sorts],
  )

  const tabButton = (value: 'all' | number | null, label: string, glyph: string | null) => (
    <button
      key={value === null ? 'default' : String(value)}
      type="button"
      onClick={() => setFilters({ ...prefs.filters, tab: value })}
      className={cn(
        'flex shrink-0 items-center gap-1 rounded px-3 py-1.5 text-sm',
        prefs.filters.tab === value ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:bg-neutral-900',
      )}
    >
      {value === 'all' ? <LayoutGrid aria-hidden className="size-3.5" /> : <TabIcon glyph={glyph} />}
      {label}
    </button>
  )

  return (
    <main className="mx-auto max-w-5xl p-3 sm:p-6">
      <header className="mb-4 flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <img src="/brand/icon-32.png" alt="" className="size-8" />
          <h1 className="text-xl font-semibold">F95Checker</h1>
        </div>
        <RefreshButton />
      </header>

      <AddGameBar />

      <nav className="mb-3 flex gap-1 overflow-x-auto pb-1" aria-label="Tabs">
        {tabButton('all', 'All tabs', null)}
        {tabButton(null, defaultLabel, null)}
        {tabList.map((tab) => tabButton(tab.id, tab.name || 'Untitled', tab.icon))}
      </nav>

      <div className="mb-2 flex flex-wrap items-center gap-2">
        <label className="flex items-center gap-1 text-sm text-neutral-400">
          <ArrowDownUp aria-hidden className="size-3.5" />
          <select
            aria-label="Sort games"
            value={sort.key}
            onChange={(event) => update({ sorts: [{ key: event.target.value as SortKey, dir: sort.dir }] })}
            className="rounded border border-neutral-700 bg-neutral-900 px-1.5 py-1 text-sm"
          >
            {SORTS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          aria-label={sort.dir === 'asc' ? 'Sort descending' : 'Sort ascending'}
          onClick={() => update({ sorts: [{ ...sort, dir: sort.dir === 'asc' ? 'desc' : 'asc' }] })}
          className="rounded border border-neutral-700 px-2 py-1 text-sm text-neutral-300 hover:bg-neutral-800"
        >
          {sort.dir === 'asc' ? 'Ascending' : 'Descending'}
        </button>
        <div className="ml-auto flex rounded border border-neutral-700" role="group" aria-label="View mode">
          <button
            type="button"
            aria-label="List view"
            aria-pressed={prefs.view === 'list'}
            onClick={() => update({ view: 'list' })}
            className={cn('p-1.5', prefs.view === 'list' ? 'bg-neutral-800 text-white' : 'text-neutral-400')}
          >
            <List aria-hidden className="size-4" />
          </button>
          <button
            type="button"
            aria-label="Grid view"
            aria-pressed={prefs.view === 'grid'}
            onClick={() => update({ view: 'grid' })}
            className={cn('p-1.5', prefs.view === 'grid' ? 'bg-neutral-800 text-white' : 'text-neutral-400')}
          >
            <LayoutGrid aria-hidden className="size-4" />
          </button>
        </div>
      </div>

      <FilterSidebar
        filters={prefs.filters}
        onChange={setFilters}
        statuses={enums.data?.Status ?? []}
        types={enums.data?.Type ?? []}
        labels={labelList}
      />

      {games.isPending && <p className="text-neutral-400">Loading library…</p>}
      {games.isError && <p className="text-red-400">Could not load the library: {games.error.message}</p>}
      {games.isSuccess && games.data.length === 0 && (
        <p className="rounded border border-neutral-800 p-6 text-center text-neutral-400">The library is empty.</p>
      )}
      {games.isSuccess && games.data.length > 0 && visible.length === 0 && (
        <p className="rounded border border-neutral-800 p-6 text-center text-neutral-400">No games match these filters.</p>
      )}

      {prefs.view === 'grid' ? (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
          {visible.map((game) => (
            <GameCard key={game.id} game={game} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {visible.map((game) => (
            <GameRow key={game.id} game={game} tab={tabList.find((tab) => tab.id === game.tab)} />
          ))}
        </div>
      )}

      <details className="mt-6 rounded border border-neutral-800">
        <summary className="cursor-pointer px-3 py-2 text-sm text-neutral-300">Organize tabs and labels</summary>
        <div className="grid gap-4 border-t border-neutral-800 p-3 sm:grid-cols-2">
          <TabEditor tabs={tabList} />
          <LabelEditor labels={labelList} />
        </div>
      </details>
    </main>
  )
}
