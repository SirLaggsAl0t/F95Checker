export type RefreshToast = { count: number; names: string[] }

const listeners = new Set<(toast: RefreshToast) => void>()

export const showRefreshToast = (toast: RefreshToast) => listeners.forEach((listener) => listener(toast))

export function onRefreshToast(listener: (toast: RefreshToast) => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}
