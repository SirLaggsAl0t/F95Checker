import { useQuery } from '@tanstack/react-query'

type Health = {
  ok: boolean
  data_dir: string
  db_path: string
  shared_with_desktop: boolean
}

function App() {
  const health = useQuery<Health>({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await fetch('/api/health')
      if (!res.ok) throw new Error(`Health check failed (${res.status})`)
      return res.json()
    },
  })

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="text-2xl font-semibold">F95Checker Web</h1>
      {health.isLoading && <p className="mt-2 text-neutral-400">Connecting…</p>}
      {health.isError && (
        <p className="mt-2 text-red-400">Cannot reach the server: {health.error.message}</p>
      )}
      {health.data && (
        <dl className="mt-4 grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1 text-sm">
          <dt className="text-neutral-400">Status</dt>
          <dd>{health.data.ok ? 'ok' : 'error'}</dd>
          <dt className="text-neutral-400">Data dir</dt>
          <dd className="break-all">{health.data.data_dir}</dd>
          <dt className="text-neutral-400">Database</dt>
          <dd className="break-all">{health.data.db_path}</dd>
          {health.data.shared_with_desktop && (
            <dd className="col-span-2 text-amber-400">
              This is the desktop app's data directory. Stop the desktop app while the
              web server is running.
            </dd>
          )}
        </dl>
      )}
    </main>
  )
}

export default App
