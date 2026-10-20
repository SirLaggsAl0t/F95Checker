import { describe, expect, it } from 'vitest'

import type { GameSummary, Label } from '@/api/types'
import { groupGames } from './kanban'

function game(overrides: Partial<GameSummary> = {}): GameSummary {
  return {
    id: 1,
    custom: false,
    name: 'Game',
    version: '',
    developer: '',
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

const statuses = [
  { value: 1, name: 'Normal' },
  { value: 2, name: 'Completed' },
]
const types = [
  { value: 14, name: 'RenPy' },
  { value: 19, name: 'Unity' },
]
const labels: Label[] = [
  { id: 3, name: 'Favourite', color: '#ff0000', position: 0 },
  { id: 4, name: 'Later', color: '#00ff00', position: 1 },
]
const games = [
  game({ id: 1, status: { value: 1, name: 'Normal' }, type: { value: 14, name: 'RenPy' }, labels: [3] }),
  game({ id: 2, status: { value: 2, name: 'Completed' }, type: { value: 19, name: 'Unity' }, labels: [] }),
  game({ id: 3, status: { value: 1, name: 'Normal' }, type: { value: 14, name: 'RenPy' }, labels: [3, 4] }),
]

describe('groupGames', () => {
  it('groups by status and drops empty groups', () => {
    const columns = groupGames(games, 'status', { statuses, types, labels })
    expect(columns.map((column) => column.title)).toEqual(['Normal', 'Completed'])
    expect(columns[0].games.map((item) => item.id)).toEqual([1, 3])
  })

  it('groups by type', () => {
    const columns = groupGames(games, 'type', { statuses, types, labels })
    expect(columns.map((column) => column.title)).toEqual(['RenPy', 'Unity'])
  })

  it('groups by label, with games appearing in every label and a no-label column', () => {
    const columns = groupGames(games, 'label', { statuses, types, labels })
    expect(columns.map((column) => column.key)).toEqual(['none', '3', '4'])
    expect(columns[0].games.map((item) => item.id)).toEqual([2])
    expect(columns[1].games.map((item) => item.id)).toEqual([1, 3])
    expect(columns[2].games.map((item) => item.id)).toEqual([3])
  })
})
