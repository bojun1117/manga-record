import { Converter } from 'opencc-js/t2cn'

const t2cn = Converter({ from: 'tw', to: 'cn' })

const cache = new Map<string, string>()

export function normalizeChinese(s: string): string {
  if (s === '') return s
  const cached = cache.get(s)
  if (cached !== undefined) return cached
  const out = t2cn(s).toLowerCase()
  cache.set(s, out)
  return out
}
