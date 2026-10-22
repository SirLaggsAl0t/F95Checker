import type { Settings } from '@/api/types'

export type ThemeStyle = Pick<
  Settings,
  'style_accent' | 'style_alt_bg' | 'style_bg' | 'style_border' | 'style_corner_radius' | 'style_text' | 'style_text_dim'
>

export type ThemePreset = { name: string; style: ThemeStyle }

export const THEME_PRESETS: ThemePreset[] = [
  {
    name: 'Midnight',
    style: {
      style_bg: '#0a0a0a',
      style_alt_bg: '#171717',
      style_border: '#2e2e2e',
      style_text: '#f2f2f2',
      style_text_dim: '#a3a3a3',
      style_accent: '#38bdf8',
      style_corner_radius: 6,
    },
  },
  {
    name: 'Nord',
    style: {
      style_bg: '#1b2430',
      style_alt_bg: '#242f3d',
      style_border: '#3b4a5c',
      style_text: '#eceff4',
      style_text_dim: '#a3b1c2',
      style_accent: '#88c0d0',
      style_corner_radius: 4,
    },
  },
  {
    name: 'Ember',
    style: {
      style_bg: '#120d0b',
      style_alt_bg: '#1f1613',
      style_border: '#3a2a23',
      style_text: '#f5ece5',
      style_text_dim: '#b8a296',
      style_accent: '#fb923c',
      style_corner_radius: 10,
    },
  },
]

const VARIABLES: [keyof ThemeStyle, string][] = [
  ['style_bg', '--bg'],
  ['style_alt_bg', '--alt-bg'],
  ['style_border', '--border'],
  ['style_text', '--text'],
  ['style_text_dim', '--text-dim'],
  ['style_accent', '--accent'],
  ['style_corner_radius', '--radius'],
]

// Settings store colours as #rrggbb; the stylesheet consumes them as CSS vars.
export function applyTheme(style: Partial<ThemeStyle>, root: HTMLElement = document.documentElement): void {
  for (const [key, variable] of VARIABLES) {
    const value = style[key]
    if (value === undefined || value === null || value === '') continue
    root.style.setProperty(variable, typeof value === 'number' ? `${value}px` : value)
  }
}
