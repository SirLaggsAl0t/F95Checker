import { describe, expect, it } from 'vitest'

import { parseChangelog } from './changelog'

describe('parseChangelog', () => {
  it('splits versions and classifies changes', () => {
    const sections = parseChangelog(
      ['Changelog:', 'v0.2.0', '[+] New scene', '[-] Removed bug', '- Fixed typo', '', '0.1.0:', '* Initial release'].join(
        '\n',
      ),
    )
    expect(sections.map((section) => section.version)).toEqual(['', 'v0.2.0', '0.1.0'])
    expect(sections[1].lines).toEqual([
      { text: 'New scene', kind: 'add' },
      { text: 'Removed bug', kind: 'remove' },
      { text: 'Fixed typo', kind: 'note' },
    ])
    expect(sections[2].lines).toEqual([{ text: 'Initial release', kind: 'note' }])
  })

  it('does not treat ordinary numbers as versions', () => {
    const sections = parseChangelog('1.5x speed boost\n- 2.0x damage')
    expect(sections).toHaveLength(1)
    expect(sections[0].version).toBe('')
    expect(sections[0].lines).toHaveLength(2)
  })
})
