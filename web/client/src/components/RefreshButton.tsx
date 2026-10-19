import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import { useEffect, useRef } from 'react'

import { apiGet, apiSend } from '@/api/client'
import type { RefreshStatus } from '@/api/types'
import { cn } from '@/lib/utils'

export function RefreshButton() {
  const queryClient = useQueryClient()
  const status = useQuery({
    queryKey: ['refresh'],
    queryFn: () => apiGet<RefreshStatus>('/api/refresh/status'),
    refetchInterval: (query) => (query.state.data?.state === 'running' ? 1000 : false),
  })

  const start = useMutation({
    mutationFn: () => apiSend<{ queued: boolean }>('/api/refresh', 'POST'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['refresh'] }),
  })

  const wasRunning = useRef(false)
  const lastFinished = useRef<number | null>(null)
  useEffect(() => {
    const data = status.data
    if (!data) return
    const running = data.state === 'running'
    const finished = data.last_result?.finished_at ?? null
    if ((wasRunning.current && !running) || (lastFinished.current !== null && finished !== lastFinished.current)) {
      queryClient.invalidateQueries({ queryKey: ['games'] })
    }
    wasRunning.current = running
    lastFinished.current = finished
  }, [status.data, queryClient])

  const running = status.data?.state === 'running'
  const { progress = 0, total = 0, errors = [], missing_threads = [] } = status.data ?? {}

  return (
    <div className="flex flex-col items-end gap-1 text-right">
      <button
        type="button"
        onClick={() => start.mutate()}
        disabled={running || start.isPending}
        aria-label={running ? 'Refresh running' : 'Refresh library'}
        className={cn(
          'flex items-center gap-1.5 rounded border border-neutral-700 px-2.5 py-1.5 text-sm',
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
    </div>
  )
}
