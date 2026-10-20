import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { apiSend } from '@/api/client'
import type { ImportResult } from '@/api/types'
import { Panel } from '@/components/Panel'

const buttonClass =
  'rounded border border-neutral-700 px-2.5 py-1.5 text-sm text-neutral-200 hover:bg-neutral-800 disabled:text-neutral-500'

export function ImportPage({ onClose }: { onClose?: () => void } = {}) {
  const queryClient = useQueryClient()
  const [text, setText] = useState('')
  const [summary, setSummary] = useState<ImportResult | null>(null)

  const run = useMutation({
    mutationFn: ({ path, body }: { path: string; body?: unknown }) =>
      apiSend<ImportResult>(path, 'POST', body),
    onSuccess: (data) => {
      setSummary(data)
      queryClient.invalidateQueries({ queryKey: ['games'] })
      queryClient.invalidateQueries({ queryKey: ['refresh'] })
    },
  })

  const importFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    run.mutate({ path: '/api/imports/bookmarks', body: { html: await file.text() } })
  }

  return (
    <Panel title="Import games" onClose={onClose}>
      <section className="mb-4 rounded border border-neutral-800 p-3">
        <h2 className="mb-1 font-medium">Paste thread links</h2>
        <p className="mb-2 text-sm text-neutral-400">
          One or more f95zone.to thread links. Duplicates and games already in the library are skipped.
        </p>
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          aria-label="Thread links"
          rows={4}
          placeholder="https://f95zone.to/threads/game-name.12345/"
          className="w-full rounded border border-neutral-700 bg-neutral-900 px-2.5 py-1.5 font-mono text-xs placeholder:text-neutral-600"
        />
        <button
          type="button"
          onClick={() => run.mutate({ path: '/api/imports/threads', body: { text } })}
          disabled={run.isPending || !text.trim()}
          className={`mt-2 ${buttonClass}`}
        >
          Import thread links
        </button>
      </section>

      <section className="mb-4 rounded border border-neutral-800 p-3">
        <h2 className="mb-1 font-medium">Browser bookmarks</h2>
        <p className="mb-2 text-sm text-neutral-400">
          Export your browser bookmarks to an HTML file, then choose it here.
        </p>
        <input
          type="file"
          accept=".html,.htm,text/html"
          aria-label="Bookmarks HTML file"
          onChange={importFile}
          disabled={run.isPending}
          className="block text-sm text-neutral-300"
        />
      </section>

      <section className="rounded border border-neutral-800 p-3">
        <h2 className="mb-1 font-medium">F95zone account lists</h2>
        <p className="mb-2 text-sm text-neutral-400">
          Uses the saved cookies. Import your bookmarks or watched threads from F95zone.
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => run.mutate({ path: '/api/imports/f95-bookmarks' })}
            disabled={run.isPending}
            className={buttonClass}
          >
            Import F95 bookmarks
          </button>
          <button
            type="button"
            onClick={() => run.mutate({ path: '/api/imports/f95-watched' })}
            disabled={run.isPending}
            className={buttonClass}
          >
            Import watched threads
          </button>
        </div>
      </section>

      {run.isError && <p className="mt-3 text-sm text-red-400">{run.error.message}</p>}

      {summary && (
        <section className="mt-4 rounded border border-neutral-800 p-3 text-sm">
          <p>
            Found {summary.found}, added {summary.added.length}, skipped {summary.skipped.length}.
          </p>
          {summary.added.length > 0 && (
            <ul className="mt-2 list-disc pl-5 text-neutral-300">
              {summary.added.map((game) => (
                <li key={game.id}>
                  <Link to={`/games/${game.id}`} className="underline">
                    {game.name}
                  </Link>
                </li>
              ))}
            </ul>
          )}
          {summary.skipped.length > 0 && (
            <ul className="mt-2 list-disc pl-5 text-neutral-500">
              {summary.skipped.map((item) => (
                <li key={item.id}>
                  {item.id}: {item.reason}
                </li>
              ))}
            </ul>
          )}
          <p className="mt-2 text-xs text-neutral-500">Added games are queued for a background refresh.</p>
        </section>
      )}
    </Panel>
  )
}
