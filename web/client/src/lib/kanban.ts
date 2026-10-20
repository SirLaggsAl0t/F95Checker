import type { EnumItem, GameSummary, Label } from '@/api/types'

export type KanbanGroup = 'status' | 'type' | 'label'

export type KanbanColumn = {
  key: string
  title: string
  color?: string
  games: GameSummary[]
}

export type KanbanOptions = {
  statuses: EnumItem[]
  types: EnumItem[]
  labels: Label[]
}

// Columns are the groups that actually have games, so a 30-entry Type enum
// does not render 30 empty columns.
export function groupGames(games: GameSummary[], group: KanbanGroup, options: KanbanOptions): KanbanColumn[] {
  const columns = new Map<string, KanbanColumn>()

  if (group === 'label') {
    columns.set('none', { key: 'none', title: 'No label', games: [] })
    for (const label of [...options.labels].sort((a, b) => a.position - b.position)) {
      columns.set(String(label.id), { key: String(label.id), title: label.name || 'Unnamed', color: label.color, games: [] })
    }
    for (const game of games) {
      if (!game.labels.length) {
        columns.get('none')!.games.push(game)
        continue
      }
      for (const id of game.labels) {
        columns.get(String(id))?.games.push(game)
      }
    }
  } else {
    const entries = group === 'status' ? options.statuses : options.types
    for (const entry of entries) {
      columns.set(String(entry.value), {
        key: String(entry.value),
        title: entry.name,
        color: entry.color,
        games: [],
      })
    }
    for (const game of games) {
      const entry = group === 'status' ? game.status : game.type
      columns.get(String(entry?.value))?.games.push(game)
    }
  }

  return [...columns.values()].filter((column) => column.games.length > 0)
}
