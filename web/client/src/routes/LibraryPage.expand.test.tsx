import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { LibraryPage } from './LibraryPage'

const game = {
  id: 1,
  custom: false,
  name: 'Test Game',
  version: '1.0',
  developer: 'Dev',
  type: { value: 14, name: 'RenPy', color: '#b069e8' },
  status: { value: 1, name: 'Normal', icon: 'lightning_bolt_circle', color: '#f2f2f2' },
  url: '',
  added_on: 1_700_000_000,
  last_updated: 1_700_000_000,
  score: 4.5,
  votes: 10,
  rating: 4,
  finished: '',
  installed: 'True',
  updated: true,
  archived: false,
  favourite: true,
  labels: [],
  tab: null,
  image_url: '',
  image_version: '',
  tags: [],
  unknown_tags: [],
  unknown_tags_flag: false,
  has_image: false,
}

const detail = {
  ...game,
  notes: '',
  description: 'A test game.',
  changelog: '',
  reviews_total: 0,
  reviews: [],
  previews_urls: [],
  timeline_events: [],
  last_check_version: '',
  last_full_check: 0,
  downloads: [],
}

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/']}>
        <LibraryPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('LibraryPage inline details', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input)
        const body = url === '/api/games/1'
          ? detail
          : url.startsWith('/api/games')
            ? [game]
            : url.startsWith('/api/tabs')
              ? []
              : url.startsWith('/api/labels')
                ? []
                : url.startsWith('/api/enums')
                  ? {}
                  : url.startsWith('/api/refresh/status')
                    ? { state: 'idle', progress: 0, total: 0, errors: [], missing_threads: [], last_result: null }
                    : url.startsWith('/api/settings')
                      ? { default_tab_is_new: false }
                      : {}
        return { ok: true, json: async () => body }
      }),
    )
  })

  it('expands the game inline and collapses from the title', async () => {
    renderApp()
    fireEvent.click(await screen.findByText('Test Game'))

    expect(await screen.findByText('A test game.')).toBeInTheDocument()
    const title = screen.getByRole('button', { name: 'Test Game' })
    expect(title).toHaveAttribute('aria-expanded')

    fireEvent.click(title)
    expect(screen.queryByText('A test game.')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Test Game/, expanded: true })).not.toBeInTheDocument()
  })
})
