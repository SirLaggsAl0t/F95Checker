import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Star, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { apiSend } from '@/api/client'
import type { EnumItem, GameDetail, Label, Tab } from '@/api/types'
import { cn } from '@/lib/utils'

type Form = {
  name: string
  version: string
  developer: string
  type: number
  status: number
  rating: number
  installed: string
  finished: string
  archived: boolean
  tab: number | null
  labels: number[]
}

function fromGame(game: GameDetail): Form {
  return {
    name: game.name,
    version: game.version,
    developer: game.developer,
    type: game.type?.value ?? 0,
    status: game.status?.value ?? 0,
    rating: game.rating,
    installed: game.installed,
    finished: game.finished,
    archived: game.archived,
    tab: game.tab,
    labels: [...game.labels],
  }
}

function TriState({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div>
      <span className="text-xs uppercase tracking-wide text-neutral-500">{label}</span>
      <div className="mt-0.5 flex overflow-hidden rounded border border-neutral-700" role="group" aria-label={label}>
        {[
          { value: 'True', label: 'Yes' },
          { value: 'False', label: 'No' },
          { value: '', label: 'Unknown' },
        ].map((option) => (
          <button
            key={option.label}
            type="button"
            aria-pressed={value === option.value}
            onClick={() => onChange(option.value)}
            className={cn(
              'px-2 py-1 text-xs',
              value === option.value ? 'bg-neutral-700 text-white' : 'text-neutral-400 hover:bg-neutral-800',
            )}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function Rating({ value, onChange }: { value: number; onChange: (value: number) => void }) {
  return (
    <div>
      <span className="text-xs uppercase tracking-wide text-neutral-500">Rating</span>
      <div className="mt-0.5 flex items-center gap-0.5" role="group" aria-label="Rating">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            aria-label={`Rate ${star} star${star === 1 ? '' : 's'}`}
            aria-pressed={value === star}
            onClick={() => onChange(value === star ? 0 : star)}
            className={star <= value ? 'text-amber-400' : 'text-neutral-600 hover:text-neutral-400'}
          >
            <Star aria-hidden className="size-5" fill={star <= value ? 'currentColor' : 'none'} />
          </button>
        ))}
      </div>
    </div>
  )
}

export function GameEditPanel({
  game,
  labels,
  tabs,
  types,
  statuses,
  confirmOnRemove,
}: {
  game: GameDetail
  labels: Label[]
  tabs: Tab[]
  types: EnumItem[]
  statuses: EnumItem[]
  confirmOnRemove: boolean
}) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [form, setForm] = useState<Form>(() => fromGame(game))
  const [notes, setNotes] = useState(game.notes)

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['games'] })
    queryClient.invalidateQueries({ queryKey: ['game', String(game.id)] })
  }

  const save = useMutation({
    mutationFn: (body: Record<string, unknown>) => apiSend<GameDetail>(`/api/games/${game.id}`, 'PATCH', body),
    onSuccess: (data) => {
      setForm(fromGame(data))
      setNotes(data.notes)
      invalidate()
    },
  })

  const remove = useMutation({
    mutationFn: () => apiSend<void>(`/api/games/${game.id}`, 'DELETE'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['games'] })
      navigate('/')
    },
  })

  // Notes save themselves while typing; every other field needs Save.
  useEffect(() => {
    if (notes === game.notes) return
    const timer = setTimeout(() => save.mutate({ notes }), 600)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notes, game.notes])

  const set = (patch: Partial<Form>) => setForm((current) => ({ ...current, ...patch }))

  const onDelete = () => {
    if (confirmOnRemove && !window.confirm(`Remove ${game.name}? The cover and previews are deleted.`)) return
    remove.mutate()
  }

  const error = save.error ?? remove.error

  return (
    <details className="mt-4 rounded border border-neutral-800">
      <summary className="cursor-pointer px-3 py-2 text-sm text-neutral-300">Edit game</summary>
      <div className="grid gap-3 border-t border-neutral-800 p-3 sm:grid-cols-2">
        <label className="flex flex-col gap-0.5 text-sm">
          <span className="text-xs uppercase tracking-wide text-neutral-500">Name</span>
          <input
            value={form.name}
            onChange={(event) => set({ name: event.target.value })}
            aria-label="Name"
            className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1"
          />
        </label>
        <label className="flex flex-col gap-0.5 text-sm">
          <span className="text-xs uppercase tracking-wide text-neutral-500">Developer</span>
          <input
            value={form.developer}
            onChange={(event) => set({ developer: event.target.value })}
            aria-label="Developer"
            className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1"
          />
        </label>
        <label className="flex flex-col gap-0.5 text-sm">
          <span className="text-xs uppercase tracking-wide text-neutral-500">Version</span>
          <input
            value={form.version}
            onChange={(event) => set({ version: event.target.value })}
            aria-label="Version"
            className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1"
          />
        </label>
        <label className="flex flex-col gap-0.5 text-sm">
          <span className="text-xs uppercase tracking-wide text-neutral-500">Tab</span>
          <select
            value={form.tab === null ? '' : form.tab}
            aria-label="Tab"
            onChange={(event) => set({ tab: event.target.value === '' ? null : Number(event.target.value) })}
            className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1"
          >
            <option value="">Default</option>
            {tabs.map((tab) => (
              <option key={tab.id} value={tab.id}>
                {tab.name || 'Untitled'}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-0.5 text-sm">
          <span className="text-xs uppercase tracking-wide text-neutral-500">Type</span>
          <select
            value={form.type}
            aria-label="Type"
            onChange={(event) => set({ type: Number(event.target.value) })}
            className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1"
          >
            {types.map((type) => (
              <option key={type.value} value={type.value}>
                {type.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-0.5 text-sm">
          <span className="text-xs uppercase tracking-wide text-neutral-500">Status</span>
          <select
            value={form.status}
            aria-label="Status"
            onChange={(event) => set({ status: Number(event.target.value) })}
            className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1"
          >
            {statuses.map((status) => (
              <option key={status.value} value={status.value}>
                {status.name}
              </option>
            ))}
          </select>
        </label>

        <TriState label="Installed" value={form.installed} onChange={(installed) => set({ installed })} />
        <TriState label="Finished" value={form.finished} onChange={(finished) => set({ finished })} />

        <Rating value={form.rating} onChange={(rating) => set({ rating })} />

        <label className="flex items-center gap-1.5 self-end text-sm">
          <input
            type="checkbox"
            checked={form.archived}
            onChange={(event) => set({ archived: event.target.checked })}
            className="accent-sky-500"
          />
          Archived
        </label>

        {labels.length > 0 && (
          <fieldset className="sm:col-span-2">
            <legend className="text-xs uppercase tracking-wide text-neutral-500">Labels</legend>
            <div className="mt-1 flex flex-wrap gap-2">
              {labels.map((label) => (
                <label key={label.id} className="flex items-center gap-1 text-sm" style={{ color: label.color }}>
                  <input
                    type="checkbox"
                    checked={form.labels.includes(label.id)}
                    onChange={(event) =>
                      set({
                        labels: event.target.checked
                          ? [...form.labels, label.id]
                          : form.labels.filter((id) => id !== label.id),
                      })
                    }
                    className="accent-sky-500"
                  />
                  {label.name || 'Unnamed'}
                </label>
              ))}
            </div>
          </fieldset>
        )}

        <label className="flex flex-col gap-0.5 text-sm sm:col-span-2">
          <span className="text-xs uppercase tracking-wide text-neutral-500">Notes (saved automatically)</span>
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            aria-label="Notes"
            rows={3}
            className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1"
          />
        </label>

        <div className="flex items-center gap-2 sm:col-span-2">
          <button
            type="button"
            onClick={() => save.mutate({ ...form, notes })}
            disabled={save.isPending}
            className="rounded border border-neutral-700 px-3 py-1 text-sm text-neutral-200 hover:bg-neutral-800 disabled:text-neutral-500"
          >
            Save changes
          </button>
          <button
            type="button"
            onClick={() => {
              setForm(fromGame(game))
              setNotes(game.notes)
            }}
            className="rounded border border-neutral-700 px-3 py-1 text-sm text-neutral-300 hover:bg-neutral-800"
          >
            Reset
          </button>
          <button
            type="button"
            onClick={onDelete}
            disabled={remove.isPending}
            className="ml-auto flex items-center gap-1 rounded border border-red-900 px-3 py-1 text-sm text-red-400 hover:bg-red-950/40"
          >
            <Trash2 aria-hidden className="size-4" /> Delete game
          </button>
          {save.isSuccess && !save.isPending && <span className="text-xs text-emerald-400">Saved</span>}
        </div>
        {error && <p className="text-xs text-red-400 sm:col-span-2">{error.message}</p>}
      </div>
    </details>
  )
}
