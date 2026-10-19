import { describe, expect, it } from 'vitest'

import { ApiError, errorFromResponse } from './client'

describe('errorFromResponse', () => {
  it('parses the Exc envelope', () => {
    const error = errorFromResponse(400, {
      detail: { title: 'Bad input', msg: 'URL is invalid', more: 'detail', level: 'error' },
    })
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(400)
    expect(error.message).toBe('URL is invalid')
    expect(error.title).toBe('Bad input')
    expect(error.more).toBe('detail')
  })

  it('falls back to a plain detail string', () => {
    expect(errorFromResponse(404, { detail: 'Game not found' }).message).toBe('Game not found')
  })

  it('falls back to a status message', () => {
    expect(errorFromResponse(502, null).message).toBe('Request failed (502)')
  })
})
