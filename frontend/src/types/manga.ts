// 對應 DATA_MODEL.md 的列舉值。

export type ReadingStatus = 'plan_to_read' | 'reading' | 'dropped' | 'completed'

export type MangaCategory =
  | 'hot_blooded'
  | 'mystery'
  | 'adventure'
  | 'romance'
  | 'casual'
  | 'competition'
  | 'revenge'
  | 'slice_of_life'
  | 'other'

// API.md §3.1，GET/POST /collections 回傳的資源
export interface CollectionItem {
  id: number
  mangaId: number
  title: string
  category: MangaCategory
  status: ReadingStatus
  currentVolume: number | null
  currentChapter: number | null
  rating: number | null
  lastReadAt: string // ISO 8601 UTC
  createdAt: string
  updatedAt: string
}

// API.md §3.2，GET /manga/search 回傳
export interface MangaSearchResult {
  id: number
  title: string
  category: MangaCategory
}
