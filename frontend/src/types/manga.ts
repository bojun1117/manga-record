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

export interface CollectionItem {
  id: number
  mangaId: number
  title: string
  category: MangaCategory
  status: ReadingStatus
  currentVolume: number | null
  currentChapter: number | null
  rating: number | null
  lastReadAt: string
  createdAt: string
  updatedAt: string
}

export interface MangaSearchResult {
  id: number
  title: string
  category: MangaCategory
}

export interface MangaAdminItem {
  id: number
  title: string
  category: MangaCategory
  createdAt: string
  updatedAt: string
}
