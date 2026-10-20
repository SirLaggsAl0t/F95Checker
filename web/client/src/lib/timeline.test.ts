import { describe, expect, it } from 'vitest'

import type { TimelineEntry } from '@/api/types'
import { groupByDay } from './timeline'

function entry(timestamp: number, game_id = 1): TimelineEntry {
  return {
    game_id,
    game_name: `Game ${game_id}`,
    timestamp,
    arguments: [],
    type: { value: 1, name: 'GameAdded' },
  }
}

describe('groupByDay', () => {
  it('keeps consecutive same-day events together', () => {
    const day = Math.floor(Date.now() / 1000 / 86400) * 86400
    const groups = groupByDay([entry(day + 300), entry(day + 100, 2), entry(day - 86400)])
    expect(groups).toHaveLength(2)
    expect(groups[0].events.map((event) => event.game_id)).toEqual([1, 2])
    expect(groups[1].events).toHaveLength(1)
  })
})
