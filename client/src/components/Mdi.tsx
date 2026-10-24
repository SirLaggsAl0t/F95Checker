import {
  mdiAccount,
  mdiAlertCircle,
  mdiAlertDecagram,
  mdiCheckboxMarkedCircle,
  mdiCloseCircle,
  mdiDotsHorizontalCircle,
  mdiDownload,
  mdiFlagCheckered,
  mdiLightningBolt,
  mdiLightningBoltCircle,
  mdiPauseCircle,
  mdiPlay,
  mdiReloadAlert,
  mdiShape,
  mdiSpellcheck,
  mdiStar,
  mdiTagMinus,
  mdiTagPlus,
  mdiThumbDown,
  mdiThumbUp,
  mdiTimerSync,
} from '@mdi/js'
import { Heart } from 'lucide-react'

import { cn } from '@/lib/utils'

// Names come from the vendored enums (Status, TimelineEventType). Only these
// paths are bundled; anything else falls back to a heart.
const paths: Record<string, string> = {
  lightning_bolt_circle: mdiLightningBoltCircle,
  checkbox_marked_circle: mdiCheckboxMarkedCircle,
  pause_circle: mdiPauseCircle,
  close_circle: mdiCloseCircle,
  alert_circle: mdiAlertCircle,
  dots_horizontal_circle: mdiDotsHorizontalCircle,
  alert_decagram: mdiAlertDecagram,
  play: mdiPlay,
  flag_checkered: mdiFlagCheckered,
  download: mdiDownload,
  spellcheck: mdiSpellcheck,
  lightning_bolt: mdiLightningBolt,
  star: mdiStar,
  account: mdiAccount,
  shape: mdiShape,
  tag_plus: mdiTagPlus,
  tag_minus: mdiTagMinus,
  thumb_up: mdiThumbUp,
  thumb_down: mdiThumbDown,
  timer_sync: mdiTimerSync,
  reload_alert: mdiReloadAlert,
}

export function iconPath(name: string): string | undefined {
  return paths[name]
}

export function Mdi({
  name,
  className,
  title,
}: {
  name: string
  className?: string
  title?: string
}) {
  const path = iconPath(name)
  if (!path) {
    return (
      <Heart
        className={cn('size-4', className)}
        aria-hidden={!title}
        aria-label={title}
        data-fallback="true"
      />
    )
  }
  return (
    <svg
      viewBox="0 0 24 24"
      className={cn('size-4 fill-current', className)}
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      <path d={path} />
    </svg>
  )
}
