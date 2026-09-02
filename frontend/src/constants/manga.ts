import type { MangaCategory, ReadingStatus } from '@/types/manga'

export const STATUS_LABELS: Record<ReadingStatus, string> = {
  plan_to_read: '待看',
  reading: '追讀中',
  dropped: '棄坑',
  completed: '已追完',
}

export const CATEGORY_LABELS: Record<MangaCategory, string> = {
  hot_blooded: '熱血',
  mystery: '懸疑',
  adventure: '冒險',
  romance: '愛情',
  casual: '輕鬆',
  competition: '競技',
  revenge: '復仇',
  slice_of_life: '生活',
  other: '其他',
}

function toOptions<T extends string>(labels: Record<T, string>): ReadonlyArray<{ value: T; label: string }> {
  return (Object.entries(labels) as [T, string][]).map(([value, label]) => ({ value, label }))
}

export const STATUS_OPTIONS = toOptions(STATUS_LABELS)
export const CATEGORY_OPTIONS = toOptions(CATEGORY_LABELS)
