export class ApiError extends Error {
  status: number
  title?: string
  more?: string

  constructor(status: number, message: string, title?: string, more?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.title = title
    this.more = more
  }
}

export function errorFromResponse(status: number, body: unknown): ApiError {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail
    if (typeof detail === 'string') return new ApiError(status, detail)
    if (detail && typeof detail === 'object') {
      const { title, msg, more } = detail as { title?: string; msg?: string; more?: string; [key: string]: unknown }
      return new ApiError(status, msg || title || `Request failed (${status})`, title, more)
    }
  }
  return new ApiError(status, `Request failed (${status})`)
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) {
    let body: unknown
    try {
      body = await res.json()
    } catch {
      body = null
    }
    throw errorFromResponse(res.status, body)
  }
  return res.json() as Promise<T>
}
