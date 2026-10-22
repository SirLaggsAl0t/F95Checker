import type { Enums, EnumItem, Settings } from '@/api/types'

export function TagHighlightChip({
  tag,
  settings,
  enums,
}: {
  tag: EnumItem
  settings?: Settings
  enums?: Enums
}) {
  const highlight = settings?.highlight_tags ? settings.tags_highlights[String(tag.value)] : undefined
  const color = highlight ? enums?.TagHighlight?.find((entry) => entry.value === highlight)?.color : undefined

  return (
    <span
      className="rounded border border-transparent bg-neutral-800 px-1.5 py-0.5 text-xs text-neutral-300"
      style={color ? { color, borderColor: color, backgroundColor: `${color}22` } : undefined}
    >
      {tag.text ?? tag.name}
    </span>
  )
}
