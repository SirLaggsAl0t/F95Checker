import { ArrowLeft, X } from 'lucide-react'
import { useEffect } from 'react'
import { Link } from 'react-router-dom'

// Renders as a dialog when onClose is given, otherwise as a standalone page.
export function Panel({ title, onClose, children }: { title: string; onClose?: () => void; children: React.ReactNode }) {
  useEffect(() => {
    if (!onClose) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  if (!onClose) {
    return (
      <main className="mx-auto max-w-3xl p-3 sm:p-6">
        <Link to="/" className="mb-4 inline-flex items-center gap-1 text-sm text-neutral-400 hover:text-white">
          <ArrowLeft aria-hidden className="size-4" /> Library
        </Link>
        <h1 className="mb-4 text-xl font-semibold">{title}</h1>
        {children}
      </main>
    )
  }

  return (
    <div className="fixed inset-0 z-30 overflow-y-auto bg-black/70 p-2 backdrop-blur-sm sm:p-6" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(event) => event.stopPropagation()}
        className="mx-auto w-full max-w-3xl rounded-lg border border-neutral-800 bg-neutral-950 shadow-xl"
      >
        <div className="sticky top-0 z-10 flex items-center justify-between gap-2 rounded-t-lg border-b border-neutral-800 bg-neutral-950/95 px-4 py-2.5 backdrop-blur">
          <h1 className="truncate font-medium">{title}</h1>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded p-1 text-neutral-400 hover:bg-neutral-800 hover:text-white"
          >
            <X aria-hidden className="size-4" />
          </button>
        </div>
        <div className="p-3 sm:p-4">{children}</div>
      </div>
    </div>
  )
}
