import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowDown, ArrowUp, Plus, Trash2 } from 'lucide-react'

import { apiSend } from '@/api/client'
import type { Label } from '@/api/types'

export function LabelEditor({ labels }: { labels: Label[] }) {
  const queryClient = useQueryClient()
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['labels'] })
    queryClient.invalidateQueries({ queryKey: ['games'] })
  }

  const create = useMutation({
    mutationFn: () => apiSend<Label>('/api/labels', 'POST', {}),
    onSuccess: invalidate,
  })
  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Record<string, unknown> }) =>
      apiSend<Label>(`/api/labels/${id}`, 'PATCH', body),
    onSuccess: invalidate,
  })
  const remove = useMutation({
    mutationFn: (id: number) => apiSend<void>(`/api/labels/${id}`, 'DELETE'),
    onSuccess: invalidate,
  })
  const reorder = useMutation({
    mutationFn: (ids: number[]) => apiSend<Label[]>('/api/labels/order', 'PUT', { ids }),
    onSuccess: invalidate,
  })

  const move = (index: number, offset: number) => {
    const ids = labels.map((label) => label.id)
    const target = index + offset
    if (target < 0 || target >= ids.length) return
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    reorder.mutate(ids)
  }

  const error = create.error ?? update.error ?? remove.error ?? reorder.error

  return (
    <section>
      <div className="mb-1 flex items-center justify-between">
        <h2 className="font-medium">Labels</h2>
        <button
          type="button"
          onClick={() => create.mutate()}
          disabled={create.isPending}
          className="flex items-center gap-1 rounded border border-neutral-700 px-2 py-1 text-xs hover:bg-neutral-800"
        >
          <Plus aria-hidden className="size-3.5" /> Add label
        </button>
      </div>
      {labels.length === 0 && <p className="text-sm text-neutral-500">No labels yet.</p>}
      <ul className="flex flex-col gap-1">
        {labels.map((label, index) => (
          <li key={label.id} className="flex items-center gap-1.5">
            <input
              type="color"
              aria-label={`Colour for ${label.name || 'label'}`}
              value={label.color || '#696969'}
              onChange={(event) => update.mutate({ id: label.id, body: { color: event.target.value } })}
              className="size-6 shrink-0 rounded border border-neutral-700 bg-transparent"
            />
            <input
              defaultValue={label.name}
              aria-label="Label name"
              onBlur={(event) => {
                if (event.target.value !== label.name) update.mutate({ id: label.id, body: { name: event.target.value } })
              }}
              className="min-w-0 flex-1 rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
            />
            <button
              type="button"
              aria-label="Move label up"
              disabled={index === 0}
              onClick={() => move(index, -1)}
              className="rounded border border-neutral-700 p-1 text-neutral-300 hover:bg-neutral-800 disabled:text-neutral-600"
            >
              <ArrowUp aria-hidden className="size-3.5" />
            </button>
            <button
              type="button"
              aria-label="Move label down"
              disabled={index === labels.length - 1}
              onClick={() => move(index, 1)}
              className="rounded border border-neutral-700 p-1 text-neutral-300 hover:bg-neutral-800 disabled:text-neutral-600"
            >
              <ArrowDown aria-hidden className="size-3.5" />
            </button>
            <button
              type="button"
              aria-label={`Delete label ${label.name}`}
              onClick={() => remove.mutate(label.id)}
              className="rounded border border-neutral-700 p-1 text-red-400 hover:bg-neutral-800"
            >
              <Trash2 aria-hidden className="size-3.5" />
            </button>
          </li>
        ))}
      </ul>
      {error && <p className="mt-1 text-xs text-red-400">{error.message}</p>}
    </section>
  )
}
