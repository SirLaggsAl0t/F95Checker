import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Mdi, iconPath } from './Mdi'

describe('Mdi', () => {
  it('resolves enum icon names to paths', () => {
    expect(iconPath('lightning_bolt_circle')).toMatch(/^M/)
  })

  it('renders an svg for a known icon', () => {
    const { container } = render(<Mdi name="play" />)
    expect(container.querySelector('svg path')).toBeInTheDocument()
  })

  it('falls back for unknown names', () => {
    const { container } = render(<Mdi name="not_a_real_icon" />)
    expect(container.querySelector('svg')).toBeInTheDocument()
    expect(container.querySelector('[data-fallback]')).toBeInTheDocument()
  })
})
