import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search } from 'lucide-react'
import { useState } from 'react'

import { apiGet, apiSend } from '@/api/client'
import type { AddGamesResponse, SearchResult } from '@/api/types'

const THREAD_URL = /threads\/(?:[^./]*\.)?\d+/

export function AddGameBar() {
  const queryClient = useQueryClient()
  const [text, setText] = useState('')
  const [results, setResults] = useState<SearchResult[] | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const added = (data: AddGamesResponse) => {
    setResults(null)
    setText('')
    setMessage(
      `${data.added.length} added${data.skipped.length ? `, ${data.skipped.length} skipped` : ''}`,
    )
    queryClient.invalidateQueries({ queryKey: ['games'] })
    queryClient.invalidateQueries({ queryKey: ['refresh'] })
  }

  const add = useMutation({
    mutationFn: (body: { url?: string; id?: number }) =>
      apiSend<AddGamesResponse>('/api/games', 'POST', body),
    onSuccess: added,
  })

  const search = useMutation({
    mutationFn: (query: string) =>
      apiGet<SearchResult[]>(`/api/search?q=${encodeURIComponent(query)}`),
    onSuccess: setResults,
  })

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    const value = text.trim()
    if (!value) return
    setMessage(null)
    if (THREAD_URL.test(value)) add.mutate({ url: value })
    else search.mutate(value)
  }

  const pending = add.isPending || search.isPending
  const error = add.error ?? search.error

  return (
    <form onSubmit={submit} className="mb-3">
      <div className="flex gap-1.5">
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Paste a thread URL or search by name"
          aria-label="Thread URL or game name"
          className="min-w-0 flex-1 rounded border border-neutral-700 bg-neutral-900 px-2.5 py-1.5 text-sm placeholder:text-neutral-500"
        />
        <button
          type="submit"
          disabled={pending || !text.trim()}
          aria-label={THREAD_URL.test(text) ? 'Add game' : 'Search games'}
          className="flex items-center gap-1.5 rounded border border-neutral-700 px-2.5 py-1.5 text-sm text-neutral-200 hover:bg-neutral-800 disabled:text-neutral-500"
        >
          {THREAD_URL.test(text) ? <Plus aria-hidden className="size-4" /> : <Search aria-hidden className="size-4" />}
        </button>
      </div>

      {message && <p className="mt-1.5 text-xs text-neutral-400">{message}</p>}
      {error && <p className="mt-1.5 text-xs text-red-400">{error.message}</p>}

      {results && (
        <ul className="mt-2 divide-y divide-neutral-800 rounded border border-neutral-800">
          {results.length === 0 && <li className="p-2 text-sm text-neutral-400">No results.</li>}
          {results.map((result) => (
            <li key={result.id} className="flex items-center justify-between gap-2 p-2">
              <div className="min-w-0">
                <p className="truncate text-sm">{result.title}</p>
                <p className="truncate text-xs text-neutral-500">{result.creator}</p>
              </div>
              <button
                type="button"
                disabled={result.in_list || add.isPending}
                onClick={() => add.mutate({ id: result.id })}
                className="shrink-0 rounded border border-neutral-700 px-2 py-1 text-xs text-neutral-200 hover:bg-neutral-800 disabled:text-neutral-500"
              >
                {result.in_list ? 'In library' : 'Add'}
              </button>
            </li>
          ))}
        </ul>
      )}
    </form>
  )
}
