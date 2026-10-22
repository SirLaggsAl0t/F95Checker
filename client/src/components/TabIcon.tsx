import { Heart } from 'lucide-react'

import { cn } from '@/lib/utils'

// Tab.icon is a raw glyph char from the MDI font (U+F0000..U+FFFFF), not a name.
// Rendering it with the bundled font avoids shipping a glyph-to-icon lookup.
export function TabIcon({ glyph, className }: { glyph?: string | null; className?: string }) {
  const codePoint = glyph?.codePointAt(0) ?? 0
  if (codePoint < 0xf0000 || codePoint > 0xfffff) {
    return <Heart className={cn('size-4', className)} aria-hidden data-fallback="true" />
  }
  return (
    <span className={cn('mdi-glyph text-base leading-none', className)} aria-hidden data-mdi="true">
      {glyph}
    </span>
  )
}
