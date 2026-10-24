import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'

import { apiGet, apiSend } from '@/api/client'
import type { Enums, GameSummary, Settings } from '@/api/types'
import { Panel } from '@/components/Panel'

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
}) {
  return (
    <label className="flex items-center gap-1.5 text-sm">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="accent-sky-500" />
      {label}
    </label>
  )
}

export function SettingsPage({ onClose }: { onClose?: () => void } = {}) {
  const queryClient = useQueryClient()
  const settings = useQuery({ queryKey: ['settings'], queryFn: () => apiGet<Settings>('/api/settings') })
  const enums = useQuery({ queryKey: ['enums'], queryFn: () => apiGet<Enums>('/api/enums') })
  const games = useQuery({ queryKey: ['games'], queryFn: () => apiGet<GameSummary[]>('/api/games') })
  const [form, setForm] = useState<Settings | null>(null)

  useEffect(() => {
    if (settings.data) setForm(settings.data)
  }, [settings.data])

  const save = useMutation({
    mutationFn: (body: Settings) => apiSend<Settings>('/api/settings', 'PATCH', body),
    onSuccess: (data) => {
      setForm(data)
      queryClient.setQueryData(['settings'], data)
    },
  })

  const usedTags = useMemo(() => {
    const values = new Set((games.data ?? []).flatMap((game) => game.tags.map((tag) => tag.value)))
    return (enums.data?.Tag ?? []).filter((tag) => values.has(tag.value))
  }, [games.data, enums.data])

  if (!form) {
    return (
      <Panel title="Settings" onClose={onClose}>
        {settings.isError ? (
          <p className="text-red-400">Could not load settings: {settings.error.message}</p>
        ) : (
          <p className="text-neutral-400">Loading settings…</p>
        )}
      </Panel>
    )
  }

  const set = <K extends keyof Settings>(key: K, value: Settings[K]) =>
    setForm((current) => (current ? { ...current, [key]: value } : current))

  const setHighlight = (tag: number, value: string) => {
    const next = { ...form.tags_highlights }
    if (value) next[String(tag)] = Number(value)
    else delete next[String(tag)]
    set('tags_highlights', next)
  }

  return (
    <Panel title="Settings" onClose={onClose}>
      <form
        className="flex flex-col gap-4"
        onSubmit={(event) => {
          event.preventDefault()
          save.mutate(form)
        }}
      >
        <section className="rounded border border-neutral-800 p-3">
          <h2 className="mb-2 font-medium">Library</h2>
          <div className="grid gap-2 sm:grid-cols-2">
            <Toggle label="Previews" checked={form.previews_enabled} onChange={(value) => set('previews_enabled', value)} />
            <Toggle label="Check notifications" checked={form.check_notifs} onChange={(value) => set('check_notifs', value)} />
            <Toggle
              label="Mark installed after add"
              checked={form.mark_installed_after_add}
              onChange={(value) => set('mark_installed_after_add', value)}
            />
            <Toggle
              label="Confirm before removing"
              checked={form.confirm_on_remove}
              onChange={(value) => set('confirm_on_remove', value)}
            />
            <Toggle
              label="Refresh archived games"
              checked={form.refresh_archived_games}
              onChange={(value) => set('refresh_archived_games', value)}
            />
            <Toggle
              label="Refresh completed games"
              checked={form.refresh_completed_games}
              onChange={(value) => set('refresh_completed_games', value)}
            />
            <Toggle
              label="Default tab is new games"
              checked={form.default_tab_is_new}
              onChange={(value) => set('default_tab_is_new', value)}
            />
            <label className="flex items-center gap-1.5 text-sm">
              Background refresh (minutes, 0 = off)
              <input
                type="number"
                min={0}
                max={1440}
                value={form.bg_refresh_interval}
                onChange={(event) => set('bg_refresh_interval', Number(event.target.value))}
                aria-label="Background refresh interval"
                className="w-20 rounded border border-neutral-700 bg-neutral-900 px-1.5 py-1"
              />
            </label>
          </div>
        </section>

        <section className="rounded border border-neutral-800 p-3">
          <h2 className="mb-2 font-medium">Appearance</h2>
          <div className="grid gap-2 sm:grid-cols-2">
            {(
              [
                ['style_bg', 'Background'],
                ['style_text', 'Text'],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="flex items-center justify-between gap-2 text-sm">
                {label}
                <input
                  type="color"
                  value={form[key]}
                  onChange={(event) => set(key, event.target.value)}
                  aria-label={label}
                  className="h-7 w-12 rounded border border-neutral-700 bg-neutral-900"
                />
              </label>
            ))}
          </div>
        </section>

        <section className="rounded border border-neutral-800 p-3">
          <h2 className="mb-2 font-medium">Tag highlighting</h2>
          <Toggle label="Highlight tags" checked={form.highlight_tags} onChange={(value) => set('highlight_tags', value)} />
          {usedTags.length === 0 ? (
            <p className="mt-2 text-sm text-neutral-500">No tags in the library yet.</p>
          ) : (
            <div className="mt-2 grid max-h-64 gap-1 overflow-y-auto sm:grid-cols-2">
              {usedTags.map((tag) => (
                <label key={tag.value} className="flex items-center justify-between gap-2 text-sm">
                  <span className="truncate">{tag.text ?? tag.name}</span>
                  <select
                    aria-label={`Highlight ${tag.text ?? tag.name}`}
                    value={form.tags_highlights[String(tag.value)] ?? ''}
                    onChange={(event) => setHighlight(tag.value, event.target.value)}
                    className="rounded border border-neutral-700 bg-neutral-900 px-1 py-0.5 text-xs"
                  >
                    <option value="">None</option>
                    {(enums.data?.TagHighlight ?? []).map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.name}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
          )}
        </section>

        <section className="rounded border border-neutral-800 p-3">
          <h2 className="mb-2 font-medium">Timeline</h2>
          <div className="grid gap-1 sm:grid-cols-2">
            {(enums.data?.TimelineEventType ?? []).map((event) => (
              <Toggle
                key={event.value}
                label={event.display ?? event.name}
                checked={!form.hidden_timeline_events.includes(event.value)}
                onChange={(checked) =>
                  set(
                    'hidden_timeline_events',
                    checked
                      ? form.hidden_timeline_events.filter((value) => value !== event.value)
                      : [...form.hidden_timeline_events, event.value],
                  )
                }
              />
            ))}
          </div>
        </section>

        <section className="rounded border border-neutral-800 p-3">
          <h2 className="mb-2 font-medium">Proxy</h2>
          <div className="grid gap-2 sm:grid-cols-2">
            <label className="flex items-center justify-between gap-2 text-sm">
              Type
              <select
                value={form.proxy_type}
                onChange={(event) => set('proxy_type', Number(event.target.value))}
                aria-label="Proxy type"
                className="rounded border border-neutral-700 bg-neutral-900 px-1.5 py-1"
              >
                {(enums.data?.ProxyType ?? []).map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center justify-between gap-2 text-sm">
              Host
              <input
                value={form.proxy_host}
                onChange={(event) => set('proxy_host', event.target.value)}
                aria-label="Proxy host"
                className="w-40 rounded border border-neutral-700 bg-neutral-900 px-1.5 py-1"
              />
            </label>
            <label className="flex items-center justify-between gap-2 text-sm">
              Port
              <input
                type="number"
                min={0}
                max={65535}
                value={form.proxy_port}
                onChange={(event) => set('proxy_port', Number(event.target.value))}
                aria-label="Proxy port"
                className="w-24 rounded border border-neutral-700 bg-neutral-900 px-1.5 py-1"
              />
            </label>
            <Toggle label="Allow insecure SSL" checked={form.insecure_ssl} onChange={(value) => set('insecure_ssl', value)} />
          </div>
        </section>

        <div className="flex items-center gap-2">
          <button
            type="submit"
            disabled={save.isPending}
            className="rounded border border-neutral-700 px-3 py-1.5 text-sm text-neutral-200 hover:bg-neutral-800 disabled:text-neutral-500"
          >
            Save settings
          </button>
          {save.isSuccess && !save.isPending && <span className="text-xs text-emerald-400">Saved</span>}
          {save.isError && <span className="text-xs text-red-400">{save.error.message}</span>}
        </div>
      </form>
    </Panel>
  )
}
