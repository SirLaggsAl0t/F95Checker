import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowDown, ArrowUp, Plus, Trash2 } from 'lucide-react'

import { apiSend } from '@/api/client'
import type { Tab } from '@/api/types'
import { TabIcon } from '@/components/TabIcon'

export function TabEditor({ tabs }: { tabs: Tab[] }) {
  const queryClient = useQueryClient()
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['tabs'] })
    queryClient.invalidateQueries({ queryKey: ['games'] })
  }

  const create = useMutation({
    mutationFn: () => apiSend<Tab>('/api/tabs', 'POST', {}),
    onSuccess: invalidate,
  })
  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Record<string, unknown> }) =>
      apiSend<Tab>(`/api/tabs/${id}`, 'PATCH', body),
    onSuccess: invalidate,
  })
  const remove = useMutation({
    mutationFn: (id: number) => apiSend<void>(`/api/tabs/${id}`, 'DELETE'),
    onSuccess: invalidate,
  })
  const reorder = useMutation({
    mutationFn: (ids: number[]) => apiSend<Tab[]>('/api/tabs/order', 'PUT', { ids }),
    onSuccess: invalidate,
  })

  const move = (index: number, offset: number) => {
    const ids = tabs.map((tab) => tab.id)
    const target = index + offset
    if (target < 0 || target >= ids.length) return
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    reorder.mutate(ids)
  }

  const error = create.error ?? update.error ?? remove.error ?? reorder.error

  return (
    <section>
      <div className="mb-1 flex items-center justify-between">
        <h2 className="font-medium">Tabs</h2>
        <button
          type="button"
          onClick={() => create.mutate()}
          disabled={create.isPending}
          className="flex items-center gap-1 rounded border border-neutral-700 px-2 py-1 text-xs hover:bg-neutral-800"
        >
          <Plus aria-hidden className="size-3.5" /> Add tab
        </button>
      </div>
      {tabs.length === 0 && <p className="text-sm text-neutral-500">Only the default tab exists.</p>}
      <ul className="flex flex-col gap-1">
        {tabs.map((tab, index) => (
          <li key={tab.id} className="flex items-center gap-1.5">
            <input
              type="color"
              aria-label={`Colour for ${tab.name || 'tab'}`}
              value={tab.color || '#696969'}
              onChange={(event) => update.mutate({ id: tab.id, body: { color: event.target.value } })}
              className="size-6 shrink-0 rounded border border-neutral-700 bg-transparent"
            />
            <input
              defaultValue={tab.name}
              aria-label="Tab name"
              onBlur={(event) => {
                if (event.target.value !== tab.name) update.mutate({ id: tab.id, body: { name: event.target.value } })
              }}
              className="min-w-0 flex-1 rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
            />
            <input
              defaultValue={tab.icon}
              aria-label="Tab icon glyph"
              onBlur={(event) => {
                if (event.target.value !== tab.icon) update.mutate({ id: tab.id, body: { icon: event.target.value } })
              }}
              className="w-12 shrink-0 rounded border border-neutral-700 bg-neutral-900 px-1 py-1 text-center text-sm"
            />
            <span className="shrink-0 text-neutral-300">
              <TabIcon glyph={tab.icon} />
            </span>
            <button
              type="button"
              aria-label="Move tab up"
              disabled={index === 0}
              onClick={() => move(index, -1)}
              className="rounded border border-neutral-700 p-1 text-neutral-300 hover:bg-neutral-800 disabled:text-neutral-600"
            >
              <ArrowUp aria-hidden className="size-3.5" />
            </button>
            <button
              type="button"
              aria-label="Move tab down"
              disabled={index === tabs.length - 1}
              onClick={() => move(index, 1)}
              className="rounded border border-neutral-700 p-1 text-neutral-300 hover:bg-neutral-800 disabled:text-neutral-600"
            >
              <ArrowDown aria-hidden className="size-3.5" />
            </button>
            <button
              type="button"
              aria-label={`Delete tab ${tab.name}`}
              onClick={() => remove.mutate(tab.id)}
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
