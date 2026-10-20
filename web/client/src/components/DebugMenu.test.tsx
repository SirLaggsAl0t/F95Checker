import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { GameSummary } from '@/api/types'
import { onRefreshToast, type RefreshToast } from '@/lib/toast'
import { DebugMenu } from './DebugMenu'

const game = {
  id: 7,
  name: 'Test Game',
  updated: false,
} as GameSummary

function renderMenu(client: QueryClient) {
  client.setQueryData(['games'], [game])
  return render(
    <QueryClientProvider client={client}>
      <DebugMenu />
    </QueryClientProvider>,
  )
}

describe('DebugMenu', () => {
  it('marks the first game as updated in the query cache', () => {
    const client = new QueryClient()
    renderMenu(client)

    fireEvent.click(screen.getByRole('button', { name: 'Debug menu' }))
    fireEvent.click(screen.getByRole('menuitem', { name: 'Mark first game updated' }))

    expect(client.getQueryData<GameSummary[]>(['games'])?.[0].updated).toBe(true)
  })

  it('raises the refresh toast with game names', () => {
    const received: RefreshToast[] = []
    const off = onRefreshToast((toast) => received.push(toast))
    renderMenu(new QueryClient())

    fireEvent.click(screen.getByRole('button', { name: 'Debug menu' }))
    fireEvent.click(screen.getByRole('menuitem', { name: 'Show update toast (1 game)' }))
    off()

    expect(received).toEqual([{ count: 1, names: ['Test Game'] }])
  })
})
