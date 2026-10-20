import type { GameSummary } from '@/api/types'

export type Tri = 'any' | 'yes' | 'no'
export type ArchivedFilter = 'show' | 'hide' | 'only'
export type TabFilter = 'all' | 'favourites' | number
export type SortKey = 'name' | 'developer' | 'added_on' | 'last_updated' | 'score' | 'rating' | 'votes'
export type Sort = { key: SortKey; dir: 'asc' | 'desc' }

export type Filters = {
  query: string
  tab: TabFilter
  status: number[]
  type: number[]
  labels: number[]
  installed: Tri
  finished: Tri
  archived: ArchivedFilter
}

export type LibraryPrefs = {
  sorts: Sort[]
  filters: Filters
}

const STORAGE_KEY = 'f95checker.library.v2'

export function defaultPrefs(): LibraryPrefs {
  return {
    sorts: [{ key: 'name', dir: 'asc' }],
    filters: {
      query: '',
      tab: 'favourites',
      status: [],
      type: [],
      labels: [],
      installed: 'any',
      finished: 'any',
      archived: 'show',
    },
  }
}

function triMatches(value: string, want: Tri): boolean {
  if (want === 'any') return true
  if (want === 'yes') return value === 'True'
  return value === 'False'
}

export function applyFilters(games: GameSummary[], filters: Filters): GameSummary[] {
  const needle = filters.query.trim().toLowerCase()
  return games.filter((game) => {
    if (filters.tab === 'favourites' && !game.favourite) return false
    if (filters.tab !== 'all' && filters.tab !== 'favourites' && game.tab !== filters.tab) return false
    if (filters.archived === 'hide' && game.archived) return false
    if (filters.archived === 'only' && !game.archived) return false
    if (filters.status.length && !filters.status.includes(game.status?.value)) return false
    if (filters.type.length && !filters.type.includes(game.type?.value)) return false
    if (filters.labels.length && !filters.labels.every((id) => game.labels.includes(id))) return false
    if (!triMatches(game.installed, filters.installed)) return false
    if (!triMatches(game.finished, filters.finished)) return false
    if (needle) {
      const haystack = [game.name, game.developer, ...game.tags.map((tag) => tag.text ?? tag.name)]
        .join(' ')
        .toLowerCase()
      if (!haystack.includes(needle)) return false
    }
    return true
  })
}

function compare(a: GameSummary, b: GameSummary, key: SortKey): number {
  if (key === 'name' || key === 'developer') {
    return (a[key] ?? '').localeCompare(b[key] ?? '', undefined, { sensitivity: 'base' })
  }
  const left = Number(a[key] ?? 0)
  const right = Number(b[key] ?? 0)
  return left - right
}

export function applySorts(games: GameSummary[], sorts: Sort[]): GameSummary[] {
  if (!sorts.length) return games
  const result = [...games]
  // Stable sort applied from the last key to the first gives multi-key ordering.
  for (const sort of [...sorts].reverse()) {
    const direction = sort.dir === 'asc' ? 1 : -1
    result.sort((a, b) => compare(a, b, sort.key) * direction)
  }
  return result
}

export function toggleValue(list: number[], value: number): number[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value]
}

function isTab(value: unknown): value is TabFilter {
  return value === 'all' || value === 'favourites' || typeof value === 'number'
}

type StorageLike = Pick<Storage, 'getItem' | 'setItem'>

function isSort(value: unknown): value is Sort {
  if (!value || typeof value !== 'object') return false
  const sort = value as Sort
  const keys: SortKey[] = ['name', 'developer', 'added_on', 'last_updated', 'score', 'rating', 'votes']
  return keys.includes(sort.key) && (sort.dir === 'asc' || sort.dir === 'desc')
}

export function loadPrefs(storage?: StorageLike): LibraryPrefs {
  const fallback = defaultPrefs()
  try {
    const raw = (storage ?? globalThis.localStorage)?.getItem(STORAGE_KEY)
    if (!raw) return fallback
    const stored = JSON.parse(raw) as Partial<LibraryPrefs>
    const filters = { ...fallback.filters, ...(stored.filters ?? {}) }
    if (!isTab(filters.tab)) filters.tab = fallback.filters.tab
    return {
      sorts: Array.isArray(stored.sorts) && stored.sorts.length && stored.sorts.every(isSort)
        ? stored.sorts
        : fallback.sorts,
      filters,
    }
  } catch {
    return fallback
  }
}

export function savePrefs(prefs: LibraryPrefs, storage?: StorageLike): void {
  try {
    ;(storage ?? globalThis.localStorage)?.setItem(STORAGE_KEY, JSON.stringify(prefs))
  } catch {
    // Private mode or quota: preferences are a convenience, never an error.
  }
}
