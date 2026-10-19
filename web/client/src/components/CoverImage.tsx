import { useState } from 'react'

import type { GameSummary } from '@/api/types'
import { hueFor, initials } from '@/lib/format'
import { cn } from '@/lib/utils'

type Props = {
  game: Pick<GameSummary, 'id' | 'name' | 'has_image' | 'image_version'>
  className?: string
  width?: 320 | 640
}

// One cover component for rows and the detail page. Fixed aspect box prevents
// layout shift; the placeholder is pure CSS with a deterministic hue.
export function CoverImage({ game, className, width = 320 }: Props) {
  const [failed, setFailed] = useState(false)
  const showImage = game.has_image && !failed
  const hue = hueFor(game.name)

  return (
    <div
      className={cn('relative aspect-[3/4] shrink-0 overflow-hidden rounded bg-neutral-800', className)}
      style={{ backgroundColor: `hsl(${hue} 25% 18%)` }}
      data-testid="cover"
    >
      {showImage ? (
        <img
          src={`/api/images/${game.id}?w=${width}`}
          srcSet={`/api/images/${game.id}?w=320 320w, /api/images/${game.id}?w=640 640w`}
          sizes="(max-width: 640px) 96px, 128px"
          alt=""
          loading="lazy"
          decoding="async"
          className="size-full object-cover"
          onError={() => setFailed(true)}
        />
      ) : (
        <div
          className="flex size-full items-center justify-center text-lg font-semibold text-neutral-300"
          style={{ color: `hsl(${hue} 60% 75%)` }}
          aria-hidden
        >
          {initials(game.name) || '?'}
        </div>
      )}
    </div>
  )
}
