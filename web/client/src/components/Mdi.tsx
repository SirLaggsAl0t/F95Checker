import {
  mdiAccount,
  mdiAlertCircle,
  mdiAlertDecagram,
  mdiAlertOctagon,
  mdiAlertRhombus,
  mdiCheckboxMarkedCircle,
  mdiCloseCircle,
  mdiDotsHorizontalCircle,
  mdiDownload,
  mdiFlagCheckered,
  mdiInformation,
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
  mdiViewAgendaOutline,
  mdiViewGridOutline,
  mdiViewWeekOutline,
} from '@mdi/js'
import { Heart } from 'lucide-react'

import { cn } from '@/lib/utils'

// Names come from the vendored enums (DisplayMode, Status, TimelineEventType,
// MsgBox). Only these paths are bundled; anything else falls back to a heart.
const paths: Record<string, string> = {
  view_agenda_outline: mdiViewAgendaOutline,
  view_grid_outline: mdiViewGridOutline,
  view_week_outline: mdiViewWeekOutline,
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
  information: mdiInformation,
  alert_rhombus: mdiAlertRhombus,
  alert_octagon: mdiAlertOctagon,
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
