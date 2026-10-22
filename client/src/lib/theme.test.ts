import { describe, expect, it } from 'vitest'

import { applyTheme } from './theme'

function fakeRoot() {
  const values = new Map<string, string>()
  const element = { style: { setProperty: (key: string, value: string) => values.set(key, value) } }
  return { element: element as unknown as HTMLElement, values }
}

describe('applyTheme', () => {
  it('maps style fields to CSS variables and skips empty values', () => {
    const { element, values } = fakeRoot()
    applyTheme(
      {
        style_bg: '#112233',
        style_accent: '',
        style_text: '#ffffff',
        style_corner_radius: 8,
        style_border: undefined as unknown as string,
      },
      element,
    )
    expect(values.get('--bg')).toBe('#112233')
    expect(values.get('--text')).toBe('#ffffff')
    expect(values.get('--radius')).toBe('8px')
    expect(values.has('--accent')).toBe(false)
    expect(values.has('--border')).toBe(false)
  })
})
