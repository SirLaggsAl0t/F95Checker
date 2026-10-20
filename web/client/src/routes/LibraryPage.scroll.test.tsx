import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom'
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
  labels: [],
  tab: null,
  image_url: '',
  image_version: '',
  tags: [],
  unknown_tags: [],
  unknown_tags_flag: false,
  has_image: false,
}

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<LibraryPage />} />
          <Route
            path="/games/:id"
            element={
              <Link to="/" replace>
                Library
              </Link>
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('LibraryPage scroll memory', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'scrollY', { value: 0, configurable: true })
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input)
        const body = url.startsWith('/api/games')
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

  it('restores the scroll position when the library mounts again', async () => {
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
    renderApp()
    await screen.findByText('Test Game')
    Object.defineProperty(window, 'scrollY', { value: 640, configurable: true })
    fireEvent.scroll(window)
    fireEvent.click(screen.getByText('Test Game'))

    Object.defineProperty(window, 'scrollY', { value: 0, configurable: true })
    fireEvent.click(screen.getByText('Library'))

    expect(await screen.findByText('Test Game')).toBeInTheDocument()
    expect(scrollTo).toHaveBeenLastCalledWith(0, 640)
  })
})
