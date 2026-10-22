import type { EnumItem, Enums } from './types'

// The server derives these from the vendored enums; the client only looks them up.
export function enumEntry(enums: Enums | undefined, enumName: string, value: number): EnumItem | undefined {
  return enums?.[enumName]?.find((entry) => entry.value === value)
}

export function iconFor(enums: Enums | undefined, enumName: string, value: number, fallback: string) {
  return enumEntry(enums, enumName, value)?.icon ?? fallback
}
