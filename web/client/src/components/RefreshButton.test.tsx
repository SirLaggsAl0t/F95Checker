import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { RefreshButton } from './RefreshButton'

describe('RefreshButton', () => {
  it('shows the last run errors and missing threads', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        status: 200,
        json: async () => ({
          state: 'idle',
          progress: 3,
          total: 3,
          started: 1,
          errors: [{ game_id: 7, name: 'Bad Game', msg: 'RuntimeError: boom' }],
          missing_threads: [9],
          last_result: { updated: [], finished_at: 2 },
          last_successful_refresh: 1,
        }),
      })),
    )
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={client}>
        <RefreshButton />
      </QueryClientProvider>,
    )

    expect(await screen.findByText('Bad Game: RuntimeError: boom')).toBeInTheDocument()
    expect(screen.getByText('Missing threads: 9')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /refresh library/i })).toBeEnabled()
  })
})
