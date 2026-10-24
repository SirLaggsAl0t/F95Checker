import type { Settings } from '@/api/types'

export type ThemeStyle = Pick<Settings, 'style_bg' | 'style_text'>

const VARIABLES: [keyof ThemeStyle, string][] = [
  ['style_bg', '--bg'],
  ['style_text', '--text'],
]

// Settings store colours as #rrggbb; the stylesheet consumes them as CSS vars.
export function applyTheme(style: Partial<ThemeStyle>, root: HTMLElement = document.documentElement): void {
  for (const [key, variable] of VARIABLES) {
    const value = style[key]
    if (value === undefined || value === null || value === '') continue
    root.style.setProperty(variable, value)
  }
}
