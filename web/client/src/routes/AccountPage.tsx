import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Bell, Mail, LogOut } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { apiGet, apiSend } from '@/api/client'
import type { AccountStatus, NotifCounts } from '@/api/types'
import { formatDate } from '@/lib/format'

export function AccountPage() {
  const queryClient = useQueryClient()
  const [text, setText] = useState('')

  const status = useQuery({
    queryKey: ['account'],
    queryFn: () => apiGet<AccountStatus>('/api/account/status'),
  })
  const notifs = useQuery({
    queryKey: ['notifs'],
    queryFn: () => apiGet<NotifCounts>('/api/account/notifs'),
    enabled: status.data?.logged_in === true,
  })

  const save = useMutation({
    mutationFn: (cookies: string) => apiSend<{ logged_in: boolean }>('/api/account/cookies', 'POST', { cookies }),
    onSuccess: () => {
      setText('')
      queryClient.invalidateQueries({ queryKey: ['account'] })
      queryClient.invalidateQueries({ queryKey: ['notifs'] })
    },
  })

  const signOut = useMutation({
    mutationFn: () => apiSend<void>('/api/account/cookies', 'DELETE'),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ['notifs'] })
      queryClient.invalidateQueries({ queryKey: ['account'] })
    },
  })

  return (
    <main className="mx-auto max-w-2xl p-3 sm:p-6">
      <Link to="/" className="mb-4 inline-flex items-center gap-1 text-sm text-neutral-400 hover:text-white">
        <ArrowLeft aria-hidden className="size-4" /> Library
      </Link>

      <h1 className="mb-1 text-xl font-semibold">F95zone account</h1>

      {status.isPending && <p className="text-sm text-neutral-400">Checking login…</p>}
      {status.isError && <p className="text-sm text-red-400">Could not check login: {status.error.message}</p>}
      {status.isSuccess && (
        <p className="mb-4 text-sm text-neutral-300">
          {status.data.logged_in ? 'Signed in to F95zone.' : 'Not signed in to F95zone.'}
        </p>
      )}

      {status.data?.logged_in && (
        <section className="mb-6 rounded border border-neutral-800 p-3">
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <span className="flex items-center gap-1.5">
              <Bell aria-hidden className="size-4 text-neutral-400" />
              Alerts: <strong>{notifs.data?.alerts ?? '…'}</strong>
            </span>
            <span className="flex items-center gap-1.5">
              <Mail aria-hidden className="size-4 text-neutral-400" />
              Inbox: <strong>{notifs.data?.inbox ?? '…'}</strong>
            </span>
            {notifs.data && (
              <span className="text-xs text-neutral-500">Checked {formatDate(notifs.data.checked_at)}</span>
            )}
          </div>
          {notifs.isError && <p className="mt-2 text-xs text-red-400">{notifs.error.message}</p>}
          <p className="mt-2 text-xs text-neutral-500">
            Counts only.{' '}
            <a href="https://f95zone.to/account/alerts/" target="_blank" rel="noreferrer" className="underline">
              Open alerts
            </a>{' '}
            or{' '}
            <a href="https://f95zone.to/conversations/" target="_blank" rel="noreferrer" className="underline">
              conversations
            </a>{' '}
            on F95zone.
          </p>
          <button
            type="button"
            onClick={() => signOut.mutate()}
            disabled={signOut.isPending}
            className="mt-3 flex items-center gap-1.5 rounded border border-neutral-700 px-2.5 py-1.5 text-sm text-neutral-200 hover:bg-neutral-800 disabled:text-neutral-500"
          >
            <LogOut aria-hidden className="size-4" /> Sign out
          </button>
          {signOut.isError && <p className="mt-2 text-xs text-red-400">{signOut.error.message}</p>}
        </section>
      )}

      <section className="rounded border border-neutral-800 p-3">
        <h2 className="mb-2 font-medium">Paste cookies</h2>
        <ol className="mb-3 list-decimal space-y-1 pl-5 text-sm text-neutral-400">
          <li>Log in to f95zone.to in your browser.</li>
          <li>Open the developer tools → Network, then reload the page.</li>
          <li>Copy the whole <code>Cookie</code> request header of the document request.</li>
          <li>Paste it below. It must contain the <code>xf_user</code> cookie.</li>
        </ol>
        <form
          onSubmit={(event) => {
            event.preventDefault()
            if (text.trim()) save.mutate(text.trim())
          }}
        >
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            aria-label="Cookie header"
            rows={4}
            placeholder="xf_user=...; xf_session=...;"
            className="w-full rounded border border-neutral-700 bg-neutral-900 px-2.5 py-1.5 font-mono text-xs placeholder:text-neutral-600"
          />
          <button
            type="submit"
            disabled={save.isPending || !text.trim()}
            className="mt-2 rounded border border-neutral-700 px-2.5 py-1.5 text-sm text-neutral-200 hover:bg-neutral-800 disabled:text-neutral-500"
          >
            Save cookies
          </button>
        </form>
        {save.isError && <p className="mt-2 text-xs text-red-400">{save.error.message}</p>}
        <p className="mt-2 text-xs text-neutral-500">
          Cookies stay on this server and are sent to F95zone over plain HTTP only if you entered the site that way.
        </p>
      </section>
    </main>
  )
}
