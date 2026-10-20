import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { apiSend } from '@/api/client'
import type { EnumItem, GameSummary, Label } from '@/api/types'
import { CoverImage } from '@/components/CoverImage'
import type { KanbanGroup } from '@/lib/kanban'
import { groupGames } from '@/lib/kanban'

const GROUPS: { value: KanbanGroup; label: string }[] = [
  { value: 'status', label: 'Status' },
  { value: 'type', label: 'Type' },
  { value: 'label', label: 'Label' },
]

export function KanbanBoard({
  games,
  group,
  onGroupChange,
  statuses,
  types,
  labels,
}: {
  games: GameSummary[]
  group: KanbanGroup
  onGroupChange: (group: KanbanGroup) => void
  statuses: EnumItem[]
  types: EnumItem[]
  labels: Label[]
}) {
  const queryClient = useQueryClient()
  const move = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Record<string, unknown> }) =>
      apiSend<GameSummary>(`/api/games/${id}`, 'PATCH', body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['games'] }),
  })

  const columns = groupGames(games, group, { statuses, types, labels })

  return (
    <div>
      <label className="mb-2 flex items-center gap-1 text-sm text-neutral-400">
        Group by
        <select
          aria-label="Group by"
          value={group}
          onChange={(event) => onGroupChange(event.target.value as KanbanGroup)}
          className="rounded border border-neutral-700 bg-neutral-900 px-1.5 py-1 text-sm"
        >
          {GROUPS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      {columns.length === 0 && <p className="text-neutral-400">No games match these filters.</p>}

      <div className="flex gap-2 overflow-x-auto pb-2">
        {columns.map((column) => (
          <section
            key={column.key}
            aria-label={column.title}
            className="flex w-60 shrink-0 flex-col gap-2 rounded border border-neutral-800 bg-neutral-950/40 p-2"
          >
            <h2 className="flex items-center justify-between text-sm font-medium" style={{ color: column.color }}>
              <span className="truncate">{column.title}</span>
              <span className="text-xs text-neutral-500">{column.games.length}</span>
            </h2>

            {column.games.map((game) => (
              <article key={game.id} className="rounded border border-neutral-800 bg-neutral-900/70 p-2">
                <Link to={`/games/${game.id}`} className="flex gap-2">
                  <CoverImage game={game} className="w-10" />
                  <span className="min-w-0 flex-1 truncate text-sm">{game.name}</span>
                </Link>
                <details className="mt-1">
                  <summary className="cursor-pointer text-xs text-neutral-500">Move</summary>
                  {group === 'label' ? (
                    <div className="mt-1 flex flex-col gap-1">
                      {labels.map((label) => (
                        <label key={label.id} className="flex items-center gap-1 text-xs" style={{ color: label.color }}>
                          <input
                            type="checkbox"
                            checked={game.labels.includes(label.id)}
                            onChange={(event) => {
                              const next = event.target.checked
                                ? [...game.labels, label.id]
                                : game.labels.filter((id) => id !== label.id)
                              move.mutate({ id: game.id, body: { labels: next } })
                            }}
                            className="accent-sky-500"
                          />
                          {label.name || 'Unnamed'}
                        </label>
                      ))}
                    </div>
                  ) : (
                    <select
                      aria-label={`Move ${game.name}`}
                      value={group === 'status' ? game.status?.value : game.type?.value}
                      onChange={(event) =>
                        move.mutate({ id: game.id, body: { [group]: Number(event.target.value) } })
                      }
                      className="mt-1 w-full rounded border border-neutral-700 bg-neutral-900 px-1 py-0.5 text-xs"
                    >
                      {(group === 'status' ? statuses : types).map((entry) => (
                        <option key={entry.value} value={entry.value}>
                          {entry.name}
                        </option>
                      ))}
                    </select>
                  )}
                </details>
              </article>
            ))}
          </section>
        ))}
      </div>
      {move.isError && <p className="text-xs text-red-400">{move.error.message}</p>}
    </div>
  )
}
