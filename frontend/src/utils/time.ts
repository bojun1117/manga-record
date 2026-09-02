export function formatRelativeTime(iso: string, now: Date = new Date()): string {
  const then = new Date(iso)
  const diffMs = now.getTime() - then.getTime()

  if (diffMs < 0) return '剛剛'

  const seconds = Math.floor(diffMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (minutes < 1) return '剛剛'
  if (hours < 1) return `${minutes} 分鐘前`
  if (days < 1) return `${hours} 小時前`
  if (days < 2) return '昨天'
  if (days < 30) return `${days} 天前`

  const months = Math.floor(days / 30)
  if (months < 12) return `${months} 個月前`

  return `${then.getFullYear()} 年`
}
