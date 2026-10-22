import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { CoverImage } from './CoverImage'

const base = { id: 1, name: 'My Game', image_version: '' }

describe('CoverImage', () => {
  it('shows initials when the game has no cover', () => {
    render(<CoverImage game={{ ...base, has_image: false }} />)
    expect(screen.getByText('MG')).toBeInTheDocument()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })

  it('renders both thumbnail widths when a cover exists', () => {
    const { container } = render(<CoverImage game={{ ...base, has_image: true }} />)
    const image = container.querySelector('img')
    expect(image).not.toBeNull()
    expect(image?.getAttribute('src')).toBe('/api/images/1?w=320')
    expect(image?.getAttribute('srcset')).toContain('/api/images/1?w=640 640w')
    expect(image?.getAttribute('loading')).toBe('lazy')
  })
})
