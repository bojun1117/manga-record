export function parseNonNegativeInt(raw: unknown): number | null | undefined {
  if (typeof raw === 'number') {
    if (!Number.isFinite(raw) || raw < 0 || !Number.isInteger(raw)) return undefined
    return raw
  }
  const trimmed = String(raw ?? '').trim()
  if (trimmed === '') return null
  const n = Number(trimmed)
  if (!Number.isFinite(n) || n < 0 || !Number.isInteger(n)) return undefined
  return n
}
