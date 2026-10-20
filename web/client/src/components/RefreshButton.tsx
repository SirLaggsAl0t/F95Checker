import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { apiGet, apiSend } from '@/api/client'
import type { GameSummary, RefreshStatus } from '@/api/types'
import { onRefreshToast, showRefreshToast, type RefreshToast } from '@/lib/toast'
import { cn } from '@/lib/utils'

export function RefreshButton() {
  const queryClient = useQueryClient()
  const [toast, setToast] = useState<RefreshToast | null>(null)

  // Debug menu and any other caller can raise the same completion toast.
  useEffect(() => onRefreshToast(setToast), [])
  const status = useQuery({
    queryKey: ['refresh'],
    queryFn: () => apiGet<RefreshStatus>('/api/refresh/status'),
    refetchInterval: (query) => (query.state.data?.state === 'running' ? 1000 : false),
  })

  const start = useMutation({
    mutationFn: () => apiSend<{ queued: boolean }>('/api/refresh', 'POST'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['refresh'] }),
  })

  // Kick off a refresh once per page load, unless one is already running.
  const autoStarted = useRef(false)
  useEffect(() => {
    if (autoStarted.current || !status.data) return
    autoStarted.current = true
    if (status.data.state !== 'running') start.mutate()
  }, [status.data, start])

  const wasRunning = useRef(false)
  const lastFinished = useRef<number | null>(null)
  useEffect(() => {
    const data = status.data
    if (!data) return
    const running = data.state === 'running'
    const finished = data.last_result?.finished_at ?? null
    const newlyFinished = lastFinished.current !== null && finished !== lastFinished.current
    if ((wasRunning.current && !running) || newlyFinished) {
      queryClient.invalidateQueries({ queryKey: ['games'] })
    }
    if (newlyFinished && !running) {
      const updated = data.last_result?.updated ?? []
      if (updated.length) {
        const games = queryClient.getQueryData<GameSummary[]>(['games']) ?? []
        const names = updated.map((id) => games.find((game) => game.id === id)?.name ?? `#${id}`)
        showRefreshToast({ count: updated.length, names })
      }
    }
    wasRunning.current = running
    lastFinished.current = finished
  }, [status.data, queryClient])

  // The toast is a completion notice, not a log: dismiss it on its own.
  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => setToast(null), 8000)
    return () => clearTimeout(timer)
  }, [toast])

  const running = status.data?.state === 'running'
  const { progress = 0, total = 0, errors = [], missing_threads = [] } = status.data ?? {}
  const lastRefresh = status.data?.last_successful_refresh

  return (
    <div className="flex flex-col gap-1">
      <button
        type="button"
        onClick={() => start.mutate()}
        disabled={running || start.isPending}
        aria-label={running ? 'Refresh running' : 'Refresh library'}
        className={cn(
          'flex items-center justify-center gap-1.5 rounded border border-neutral-700 px-2.5 py-1.5 text-sm',
          running ? 'text-neutral-400' : 'text-neutral-200 hover:bg-neutral-800',
        )}
      >
        <RefreshCw aria-hidden className={cn('size-4', running && 'animate-spin')} />
        {running ? 'Refreshing' : 'Refresh'}
      </button>
      {running && total > 0 && (
        <span className="text-xs text-neutral-400">
          {progress}/{total}
        </span>
      )}
      {!running && lastRefresh ? (
        <span className="text-xs text-neutral-500">Last refresh: {new Date(lastRefresh * 1000).toLocaleString()}</span>
      ) : null}
      {start.isError && <span className="text-xs text-red-400">{start.error.message}</span>}
      {!running && errors.length > 0 && (
        <ul className="max-w-64 space-y-0.5 text-xs text-red-400">
          {errors.map((error) => (
            <li key={`${error.game_id ?? 'job'}-${error.msg}`}>
              {error.name ? `${error.name}: ` : ''}
              {error.msg}
            </li>
          ))}
        </ul>
      )}
      {!running && missing_threads.length > 0 && (
        <span className="text-xs text-amber-400">Missing threads: {missing_threads.join(', ')}</span>
      )}

      {toast && (
        <div
          role="status"
          className="fixed bottom-4 right-4 z-50 max-w-xs rounded border border-neutral-700 bg-neutral-900 p-3 text-left text-sm shadow-lg"
        >
          <div className="flex items-start justify-between gap-3">
            <span>
              Refresh finished: {toast.count} game{toast.count === 1 ? '' : 's'} updated
            </span>
            <button type="button" aria-label="Dismiss" onClick={() => setToast(null)} className="text-neutral-400 hover:text-white">
              <X aria-hidden className="size-4" />
            </button>
          </div>
          <ul className="mt-1 space-y-0.5 text-xs text-neutral-300">
            {toast.names.slice(0, 5).map((name, index) => (
              <li key={`${name}-${index}`} className="truncate">
                {name}
              </li>
            ))}
            {toast.names.length > 5 && <li>and {toast.names.length - 5} more</li>}
          </ul>
        </div>
      )}
    </div>
  )
}
