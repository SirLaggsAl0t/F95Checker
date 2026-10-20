import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowDown,
  ArrowDownUp,
  ArrowUp,
  ChevronUp,
  Heart,
  LayoutGrid,
  Settings as SettingsIcon,
  Upload,
  User,
} from 'lucide-react'
import { useEffect, useLayoutEffect, useMemo, useState } from 'react'

import { apiGet, apiSend } from '@/api/client'
import type { Enums, GameSummary, Label, Tab } from '@/api/types'
import { AddGameBar } from '@/components/AddGameBar'
import { CoverImage } from '@/components/CoverImage'
import { FilterSidebar } from '@/components/FilterSidebar'
import { GameDetail } from '@/components/GameDetail'
import { Mdi } from '@/components/Mdi'
import { RefreshButton } from '@/components/RefreshButton'
import { TabIcon } from '@/components/TabIcon'
import type { LibraryPrefs, SortKey, TabFilter } from '@/lib/filters'
import { applyFilters, applySorts, loadPrefs, savePrefs } from '@/lib/filters'
import { formatDate, isFinished, isInstalled } from '@/lib/format'
import { cn } from '@/lib/utils'
import { AccountPage } from '@/routes/AccountPage'
import { ImportPage } from '@/routes/ImportPage'
import { SettingsPage } from '@/routes/SettingsPage'

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
      {game.archived && <Badge className="bg-neutral-800 text-neutral-400">Archived</Badge>}
    </>
  )
}

function FavouriteButton({
  game,
  onToggle,
  disabled,
}: {
  game: GameSummary
  onToggle: () => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      aria-label={game.favourite ? `Remove ${game.name} from favourites` : `Favourite ${game.name}`}
      aria-pressed={game.favourite}
      disabled={disabled}
      onClick={onToggle}
      className={cn(
        'shrink-0 self-start rounded p-2 disabled:opacity-50',
        game.favourite ? 'text-rose-400' : 'text-neutral-500 hover:text-neutral-300',
      )}
    >
      <Heart aria-hidden className="size-4" fill={game.favourite ? 'currentColor' : 'none'} />
    </button>
  )
}

function GameRow({
  game,
  tab,
  onOpen,
  onToggleFavourite,
  onDismissUpdate,
  favouritePending,
  updatePending,
}: {
  game: GameSummary
  tab?: Tab
  onOpen: () => void
  onToggleFavourite: () => void
  onDismissUpdate: () => void
  favouritePending: boolean
  updatePending: boolean
}) {
  return (
    <div
      data-game-id={game.id}
      className="flex rounded-lg border border-neutral-800 bg-neutral-900/60 transition-colors hover:border-neutral-700 hover:bg-neutral-900"
    >
      <button
        type="button"
        onClick={onOpen}
        className="flex min-w-0 flex-1 gap-3 p-2 text-left sm:gap-4 sm:p-3"
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
            {game.last_updated ? <span className="text-xs text-neutral-500">Updated {formatDate(game.last_updated)}</span> : null}
          </div>
        </div>
      </button>
      <div className="flex shrink-0 flex-col items-center gap-1">
        {game.updated && (
          <button
            type="button"
            onClick={onDismissUpdate}
            disabled={updatePending}
            aria-label={`Mark ${game.name} update as viewed`}
            title="Mark update as viewed"
            className="mt-2 rounded bg-amber-900/60 px-1.5 py-0.5 text-[11px] font-medium text-amber-300 hover:bg-amber-900 disabled:opacity-50"
          >
            Update
          </button>
        )}
        <FavouriteButton game={game} onToggle={onToggleFavourite} disabled={favouritePending} />
      </div>
    </div>
  )
}

// Full-screen overlay. The title bar stays pinned and only the panel scrolls.
function ExpandedGame({ game, onClose }: { game: GameSummary; onClose: () => void }) {
  return (
    <article className="fixed inset-0 z-20 overflow-y-auto bg-neutral-950/95 backdrop-blur">
      <button
        type="button"
        onClick={onClose}
        aria-expanded
        className="sticky top-0 z-10 flex w-full items-center justify-between gap-2 border-b border-neutral-800 bg-neutral-900/95 px-3 py-2.5 text-left backdrop-blur hover:text-white"
      >
        <h2 className="truncate font-medium">{game.name}</h2>
        <ChevronUp aria-hidden className="size-4 shrink-0 text-neutral-400" />
      </button>
      <div className="mx-auto max-w-3xl p-4 sm:p-6">
        <GameDetail id={game.id} showHeading={false} />
      </div>
    </article>
  )
}

// Module scope survives the unmount while a game detail page is open.
let savedScroll = 0

const SORTS: { value: SortKey; label: string }[] = [
  { value: 'name', label: 'Name' },
  { value: 'added_on', label: 'Added' },
  { value: 'last_updated', label: 'Updated' },
  { value: 'score', label: 'Score' },
  { value: 'rating', label: 'Rating' },
  { value: 'votes', label: 'Votes' },
]

const NAV = [
  { key: 'import', label: 'Import', Icon: Upload },
  { key: 'account', label: 'Account', Icon: User },
  { key: 'settings', label: 'Settings', Icon: SettingsIcon },
] as const

type PanelKey = (typeof NAV)[number]['key']

export function LibraryPage() {
  const queryClient = useQueryClient()
  const [prefs, setPrefs] = useState<LibraryPrefs>(() => loadPrefs())
  const [openId, setOpenId] = useState<number | null>(null)
  const [panel, setPanel] = useState<PanelKey | null>(null)

  const games = useQuery({ queryKey: ['games'], queryFn: () => apiGet<GameSummary[]>('/api/games') })
  const tabs = useQuery({ queryKey: ['tabs'], queryFn: () => apiGet<Tab[]>('/api/tabs') })
  const labels = useQuery({ queryKey: ['labels'], queryFn: () => apiGet<Label[]>('/api/labels') })
  const enums = useQuery({ queryKey: ['enums'], queryFn: () => apiGet<Enums>('/api/enums') })

  const favourite = useMutation({
    mutationFn: ({ id, value }: { id: number; value: boolean }) =>
      apiSend<GameSummary>(`/api/games/${id}`, 'PATCH', { favourite: value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['games'] })
      queryClient.invalidateQueries({ queryKey: ['game'] })
    },
  })

  const toggleFavourite = (game: GameSummary) => favourite.mutate({ id: game.id, value: !game.favourite })

  const dismissUpdate = useMutation({
    mutationFn: (id: number) => apiSend<GameSummary>(`/api/games/${id}`, 'PATCH', { updated: false }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['games'] })
      queryClient.invalidateQueries({ queryKey: ['game'] })
    },
  })

  useEffect(() => savePrefs(prefs), [prefs])

  // Lock the page while the detail overlay is open; only the overlay scrolls.
  useEffect(() => {
    if (openId === null) return
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previous
    }
  }, [openId])

  useEffect(() => {
    const onScroll = () => {
      savedScroll = window.scrollY
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  useLayoutEffect(() => {
    if (games.isSuccess) window.scrollTo(0, savedScroll)
  }, [games.isSuccess])

  const update = (patch: Partial<LibraryPrefs>) => setPrefs((current) => ({ ...current, ...patch }))
  const setFilters = (filters: LibraryPrefs['filters']) => update({ filters })

  const collapse = (id: number) => {
    setOpenId(null)
    // Put the shrunken row back in view after the tall panel is gone.
    requestAnimationFrame(() => {
      document.querySelector(`[data-game-id="${id}"]`)?.scrollIntoView({ block: 'center' })
    })
  }

  const tabList = tabs.data ?? []
  const labelList = labels.data ?? []
  const sort = prefs.sorts[0] ?? { key: 'name' as SortKey, dir: 'asc' as const }

  const visible = useMemo(
    () => applySorts(applyFilters(games.data ?? [], prefs.filters), prefs.sorts),
    [games.data, prefs.filters, prefs.sorts],
  )

  const tabButton = (value: TabFilter, label: string, glyph: string | null) => (
    <button
      key={String(value)}
      type="button"
      onClick={() => setFilters({ ...prefs.filters, tab: value })}
      className={cn(
        'flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm',
        prefs.filters.tab === value ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:bg-neutral-900',
      )}
    >
      {value === 'all' ? (
        <LayoutGrid aria-hidden className="size-3.5 shrink-0" />
      ) : value === 'favourites' ? (
        <Heart aria-hidden className="size-3.5 shrink-0" />
      ) : (
        <TabIcon glyph={glyph} className="shrink-0" />
      )}
      <span className="truncate">{label}</span>
    </button>
  )

  return (
    <div className="flex min-h-dvh flex-col lg:flex-row">
      <aside className="flex flex-col gap-3 border-neutral-800 p-3 lg:sticky lg:top-0 lg:h-dvh lg:w-72 lg:shrink-0 lg:overflow-y-auto lg:border-r">
        <div className="flex items-center gap-3">
          <img src="/brand/icon-32.png" alt="" className="size-8" />
          <h1 className="text-xl font-semibold">F95Checker</h1>
        </div>

        <nav className="grid grid-cols-3 gap-1" aria-label="Main">
          {NAV.map(({ key, label, Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setPanel(key)}
              className="flex flex-col items-center gap-1 rounded py-2 text-xs text-neutral-400 hover:bg-neutral-900 hover:text-white"
            >
              <Icon aria-hidden className="size-4" />
              {label}
            </button>
          ))}
        </nav>

        <AddGameBar />
        <RefreshButton />

        <nav className="flex max-h-64 shrink-0 flex-col gap-0.5 overflow-y-auto" aria-label="Tabs">
          {tabButton('all', 'All tabs', null)}
          {tabButton('favourites', 'Favourites', null)}
          {tabList.map((tab) => tabButton(tab.id, tab.name || 'Untitled', tab.icon))}
        </nav>

        <div className="flex items-center gap-1.5">
          <ArrowDownUp aria-hidden className="size-4 shrink-0 text-neutral-400" />
          <select
            aria-label="Sort games"
            value={sort.key}
            onChange={(event) => update({ sorts: [{ key: event.target.value as SortKey, dir: sort.dir }] })}
            className="min-w-0 flex-1 rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
          >
            {SORTS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            aria-label={sort.dir === 'asc' ? 'Sort descending' : 'Sort ascending'}
            title={sort.dir === 'asc' ? 'Sort descending' : 'Sort ascending'}
            onClick={() => update({ sorts: [{ ...sort, dir: sort.dir === 'asc' ? 'desc' : 'asc' }] })}
            className="shrink-0 rounded border border-neutral-700 p-1.5 text-neutral-300 hover:bg-neutral-800"
          >
            {sort.dir === 'asc' ? (
              <ArrowUp aria-hidden className="size-4" />
            ) : (
              <ArrowDown aria-hidden className="size-4" />
            )}
          </button>
        </div>

        <FilterSidebar
          filters={prefs.filters}
          onChange={setFilters}
          statuses={enums.data?.Status ?? []}
          types={enums.data?.Type ?? []}
          labels={labelList}
        />
      </aside>

      <main className="min-w-0 flex-1 p-3 sm:p-6">
        {games.isPending && <p className="text-neutral-400">Loading library…</p>}
        {games.isError && <p className="text-red-400">Could not load the library: {games.error.message}</p>}
        {games.isSuccess && games.data.length === 0 && (
          <p className="rounded border border-neutral-800 p-6 text-center text-neutral-400">The library is empty.</p>
        )}
        {games.isSuccess && games.data.length > 0 && visible.length === 0 && (
          <p className="rounded border border-neutral-800 p-6 text-center text-neutral-400">
            {prefs.filters.tab === 'favourites'
              ? 'No favourites yet. Open All tabs and tap a heart.'
              : 'No games match these filters.'}
          </p>
        )}

        <div className="flex flex-col gap-2">
          {visible.map((game) =>
            openId === game.id ? (
              <ExpandedGame key={game.id} game={game} onClose={() => collapse(game.id)} />
            ) : (
              <GameRow
                key={game.id}
                game={game}
                tab={tabList.find((tab) => tab.id === game.tab)}
                onOpen={() => setOpenId(game.id)}
                onToggleFavourite={() => toggleFavourite(game)}
                onDismissUpdate={() => dismissUpdate.mutate(game.id)}
                favouritePending={favourite.isPending}
                updatePending={dismissUpdate.isPending}
              />
            ),
          )}
        </div>
      </main>

      {panel === 'import' && <ImportPage onClose={() => setPanel(null)} />}
      {panel === 'account' && <AccountPage onClose={() => setPanel(null)} />}
      {panel === 'settings' && <SettingsPage onClose={() => setPanel(null)} />}
    </div>
  )
}
