import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TabIcon } from './TabIcon'

// U+F0001 is vector-square in the bundled MDI 7.4.47 font.
const VECTOR_SQUARE = '\u{F0001}'

describe('TabIcon', () => {
  it('renders a raw glyph char with the icon font', () => {
    const { container } = render(<TabIcon glyph={VECTOR_SQUARE} />)
    const glyph = container.querySelector('[data-mdi]')
    expect(glyph).toBeInTheDocument()
    expect(glyph).toHaveTextContent(VECTOR_SQUARE)
    expect(container.querySelector('[data-fallback]')).toBeNull()
  })

  it('falls back to a heart for non-glyph input', () => {
    const { container } = render(<TabIcon glyph="x" />)
    expect(container.querySelector('[data-fallback]')).toBeInTheDocument()
  })

  it('falls back to a heart for an empty icon', () => {
    const { container } = render(<TabIcon glyph="" />)
    expect(container.querySelector('[data-fallback]')).toBeInTheDocument()
  })
})
