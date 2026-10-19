import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  )
}

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => ({
          ok: true,
          data_dir: 'C:/data/f95checker-web',
          db_path: 'C:/data/f95checker-web/db.sqlite3',
          shared_with_desktop: false,
        }),
      })),
    )
  })

  it('shows the server health', async () => {
    renderApp()
    expect(await screen.findByText('C:/data/f95checker-web')).toBeInTheDocument()
  })
})
