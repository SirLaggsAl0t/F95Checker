import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useState } from 'react'

import { apiGet } from '@/api/client'
import type { GameSummary, Settings, Tab } from '@/api/types'
import { AddGameBar } from '@/components/AddGameBar'
import { CoverImage } from '@/components/CoverImage'
import { Mdi } from '@/components/Mdi'
import { RefreshButton } from '@/components/RefreshButton'
import { TabIcon } from '@/components/TabIcon'
import { formatDate, isFinished, isInstalled } from '@/lib/format'
import { cn } from '@/lib/utils'

function Badge({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={cn('rounded px-1.5 py-0.5 text-[11px] font-medium', className)}>{children}</span>
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
          {isInstalled(game.installed) && <Badge className="bg-emerald-900/60 text-emerald-300">Installed</Badge>}
          {isFinished(game.finished) && <Badge className="bg-sky-900/60 text-sky-300">Finished</Badge>}
          {game.updated && <Badge className="bg-amber-900/60 text-amber-300">Update</Badge>}
          {game.archived && <Badge className="bg-neutral-800 text-neutral-400">Archived</Badge>}
          {game.added_on ? <span className="text-xs text-neutral-500">Added {formatDate(game.added_on)}</span> : null}
        </div>
      </div>
    </Link>
  )
}

export function LibraryPage() {
  const [selectedTab, setSelectedTab] = useState<number | null>(null)

  const games = useQuery({ queryKey: ['games'], queryFn: () => apiGet<GameSummary[]>('/api/games') })
  const tabs = useQuery({ queryKey: ['tabs'], queryFn: () => apiGet<Tab[]>('/api/tabs') })
  const settings = useQuery({ queryKey: ['settings'], queryFn: () => apiGet<Settings>('/api/settings') })

  const defaultLabel = settings.data?.default_tab_is_new ? 'New' : 'Default'
  const visible = (games.data ?? []).filter((game) => game.tab === selectedTab)

  return (
    <main className="mx-auto max-w-4xl p-3 sm:p-6">
      <header className="mb-4 flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <img src="/brand/icon-32.png" alt="" className="size-8" />
          <h1 className="text-xl font-semibold">F95Checker</h1>
        </div>
        <RefreshButton />
      </header>

      <AddGameBar />

      <nav className="mb-4 flex gap-1 overflow-x-auto pb-1" aria-label="Tabs">
        <button
          type="button"
          onClick={() => setSelectedTab(null)}
          className={cn(
            'flex shrink-0 items-center gap-1 rounded px-3 py-1.5 text-sm',
            selectedTab === null ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:bg-neutral-900',
          )}
        >
          <TabIcon glyph={null} />
          {defaultLabel}
        </button>
        {(tabs.data ?? []).map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setSelectedTab(tab.id)}
            className={cn(
              'flex shrink-0 items-center gap-1 rounded px-3 py-1.5 text-sm',
              selectedTab === tab.id ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:bg-neutral-900',
            )}
            style={selectedTab === tab.id && tab.color ? { color: tab.color } : undefined}
          >
            <TabIcon glyph={tab.icon} />
            {tab.name}
          </button>
        ))}
      </nav>

      {games.isPending && <p className="text-neutral-400">Loading library…</p>}
      {games.isError && <p className="text-red-400">Could not load the library: {games.error.message}</p>}
      {games.isSuccess && games.data.length === 0 && (
        <p className="rounded border border-neutral-800 p-6 text-center text-neutral-400">The library is empty.</p>
      )}
      {games.isSuccess && games.data.length > 0 && visible.length === 0 && (
        <p className="rounded border border-neutral-800 p-6 text-center text-neutral-400">No games in this tab.</p>
      )}

      <div className="flex flex-col gap-2">
        {visible.map((game) => (
          <GameRow key={game.id} game={game} tab={(tabs.data ?? []).find((tab) => tab.id === game.tab)} />
        ))}
      </div>
    </main>
  )
}
