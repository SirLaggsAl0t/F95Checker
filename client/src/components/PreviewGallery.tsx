import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { apiGet } from '@/api/client'
import type { Preview } from '@/api/types'
import { cn } from '@/lib/utils'

export function PreviewGallery({ gameId, enabled }: { gameId: number; enabled: boolean }) {
  const [selected, setSelected] = useState(0)
  const previews = useQuery({
    queryKey: ['previews', gameId],
    queryFn: () => apiGet<Preview[]>(`/api/games/${gameId}/previews`),
    enabled,
  })

  if (!enabled || !previews.data?.length) return null
  const current = previews.data[Math.min(selected, previews.data.length - 1)]

  return (
    <section className="mt-5">
      <h2 className="mb-1 font-medium">Previews</h2>
      <img
        src={current.url}
        alt={`Preview ${current.index + 1}`}
        loading="lazy"
        decoding="async"
        className="max-h-96 w-full rounded border border-neutral-800 object-contain"
      />
      <div className="mt-2 flex flex-wrap gap-2">
        {previews.data.map((preview) => (
          <button
            key={preview.index}
            type="button"
            aria-label={`Show preview ${preview.index + 1}`}
            aria-pressed={preview.index === current.index}
            onClick={() => setSelected(preview.index)}
            className={cn(
              'overflow-hidden rounded border',
              preview.index === current.index ? 'border-sky-500' : 'border-neutral-800 hover:border-neutral-600',
            )}
          >
            <img
              src={preview.url}
              alt=""
              loading="lazy"
              decoding="async"
              className="h-16 w-24 object-cover"
            />
          </button>
        ))}
      </div>
    </section>
  )
}
