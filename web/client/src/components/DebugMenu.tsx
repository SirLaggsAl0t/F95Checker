import { useQueryClient } from '@tanstack/react-query'
import { Bug } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import type { GameSummary } from '@/api/types'
import { showRefreshToast } from '@/lib/toast'

// Local-only triggers for UI states that normally need a real refresh.
export function DebugMenu() {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    const onPointerDown = (event: MouseEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    window.addEventListener('mousedown', onPointerDown)
    return () => {
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('mousedown', onPointerDown)
    }
  }, [open])

  const games = () => queryClient.getQueryData<GameSummary[]>(['games']) ?? []

  const fireToast = (count: number) => {
    const names = games().slice(0, count).map((game) => game.name)
    if (names.length) showRefreshToast({ count: names.length, names })
    setOpen(false)
  }

  const setFirstUpdated = (updated: boolean) => {
    const first = games()[0]
    if (first) {
      queryClient.setQueryData<GameSummary[]>(['games'], (list) =>
        list?.map((game) => (game.id === first.id ? { ...game, updated } : game)),
      )
    }
    setOpen(false)
  }

  const actions = [
    { label: 'Show update toast (1 game)', run: () => fireToast(1) },
    { label: 'Show update toast (3 games)', run: () => fireToast(3) },
    { label: 'Mark first game updated', run: () => setFirstUpdated(true) },
    { label: 'Clear update badges', run: () => setFirstUpdated(false) },
  ]

  return (
    <div ref={root} className="relative ml-auto">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-label="Debug menu"
        aria-haspopup="menu"
        aria-expanded={open}
        className="rounded p-1.5 text-neutral-400 hover:bg-neutral-900 hover:text-white"
      >
        <Bug aria-hidden className="size-4" />
      </button>

      {open && (
        <div
          role="menu"
          aria-label="Debug actions"
          className="absolute right-0 top-full z-20 mt-1 w-56 rounded border border-neutral-700 bg-neutral-900 p-1 shadow-lg"
        >
          {actions.map((action) => (
            <button
              key={action.label}
              type="button"
              role="menuitem"
              onClick={action.run}
              className="block w-full rounded px-2 py-1.5 text-left text-sm text-neutral-300 hover:bg-neutral-800 hover:text-white"
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
