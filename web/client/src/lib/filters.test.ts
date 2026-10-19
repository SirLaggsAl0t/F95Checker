import { describe, expect, it } from 'vitest'

import type { GameSummary } from '@/api/types'
import {
  applyFilters,
  applySorts,
  defaultPrefs,
  loadPrefs,
  savePrefs,
  toggleValue,
} from './filters'

function game(overrides: Partial<GameSummary> = {}): GameSummary {
  return {
    id: 1,
    custom: false,
    name: 'Game',
    version: '1.0',
    developer: 'Dev',
    type: { value: 14, name: 'RenPy' },
    status: { value: 1, name: 'Normal' },
    url: '',
    added_on: 0,
    last_updated: 0,
    score: 0,
    votes: 0,
    rating: 0,
    finished: '',
    installed: '',
    updated: false,
    archived: false,
    labels: [],
    tab: null,
    image_url: '',
    image_version: '',
    tags: [],
    unknown_tags: [],
    unknown_tags_flag: false,
    has_image: false,
    ...overrides,
  }
}

const library = [
  game({ id: 1, name: 'Beta', developer: 'Ann', score: 4, rating: 2, labels: [1, 2], tab: null }),
  game({ id: 2, name: 'Alpha', developer: 'Bob', score: 5, rating: 5, installed: 'True', tab: 7 }),
  game({ id: 3, name: 'Gamma', developer: 'Ann', score: 5, rating: 0, archived: true, labels: [1], tab: 9 }),
]

describe('applyFilters', () => {
  it('keeps everything by default', () => {
    const filters = defaultPrefs().filters
    expect(applyFilters(library, filters).map((item) => item.id)).toEqual([1, 2, 3])
  })

  it('filters by text, tab, labels and state', () => {
    const filters = defaultPrefs().filters
    expect(applyFilters(library, { ...filters, query: 'ann' }).map((item) => item.id)).toEqual([1, 3])
    expect(applyFilters(library, { ...filters, tab: null }).map((item) => item.id)).toEqual([1])
    expect(applyFilters(library, { ...filters, tab: 7 }).map((item) => item.id)).toEqual([2])
    expect(applyFilters(library, { ...filters, labels: [1, 2] }).map((item) => item.id)).toEqual([1])
    expect(applyFilters(library, { ...filters, installed: 'yes' }).map((item) => item.id)).toEqual([2])
    expect(applyFilters(library, { ...filters, archived: 'hide' }).map((item) => item.id)).toEqual([1, 2])
    expect(applyFilters(library, { ...filters, archived: 'only' }).map((item) => item.id)).toEqual([3])
    expect(applyFilters(library, { ...filters, status: [1], type: [14] }).length).toBe(3)
    expect(applyFilters(library, { ...filters, status: [2] })).toEqual([])
  })
})

describe('applySorts', () => {
  it('sorts by one key and direction', () => {
    expect(applySorts(library, [{ key: 'name', dir: 'asc' }]).map((item) => item.name)).toEqual([
      'Alpha',
      'Beta',
      'Gamma',
    ])
    expect(applySorts(library, [{ key: 'score', dir: 'desc' }]).map((item) => item.id)).toEqual([2, 3, 1])
  })

  it('applies multiple keys in order', () => {
    const sorted = applySorts(library, [
      { key: 'developer', dir: 'asc' },
      { key: 'score', dir: 'desc' },
    ])
    expect(sorted.map((item) => item.id)).toEqual([3, 1, 2])
  })
})

describe('preferences', () => {
  it('toggles values without mutating the input', () => {
    expect(toggleValue([1, 2], 2)).toEqual([1])
    expect(toggleValue([1, 2], 3)).toEqual([1, 2, 3])
    expect(toggleValue([], 4)).toEqual([4])
  })

  it('round-trips through storage', () => {
    const data = new Map<string, string>()
    const storage = {
      getItem: (key: string) => data.get(key) ?? null,
      setItem: (key: string, value: string) => void data.set(key, value),
    }
    const prefs = defaultPrefs()
    prefs.view = 'grid'
    prefs.filters.query = 'test'
    savePrefs(prefs, storage)
    expect(loadPrefs(storage)).toEqual(prefs)
  })

  it('falls back to defaults for missing or broken data', () => {
    const storage = { getItem: () => 'not json', setItem: () => {} }
    expect(loadPrefs(storage)).toEqual(defaultPrefs())
    expect(loadPrefs({ getItem: () => null, setItem: () => {} })).toEqual(defaultPrefs())
  })
})
