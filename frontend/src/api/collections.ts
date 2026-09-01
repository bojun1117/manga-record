import type { CollectionItem, MangaCategory, ReadingStatus } from '@/types/manga'
import { apiRequest } from './client'

// API.md §9:沒有 mangaId 欄位,一律靠 mangaName 由後端 get-or-create。
export interface CreateCollectionInput {
  mangaName: string
  category?: MangaCategory
  status: ReadingStatus
  currentVolume: number | null
  currentChapter: number | null
  rating: number | null
}

// PATCH 是 partial update:物件裡沒出現的 key 不會被送出(JSON.stringify 會自動略過 undefined 的欄位),
// 對應 API.md §1.3「key 不存在 = 不要動、null = 明確清空」的語意。
export interface UpdateCollectionInput {
  status?: ReadingStatus
  currentVolume?: number | null
  currentChapter?: number | null
  rating?: number | null
}

export function listCollectionsApi(token: string): Promise<CollectionItem[]> {
  return apiRequest<CollectionItem[]>('/collections', { token })
}

export function createCollectionApi(
  input: CreateCollectionInput,
  token: string,
): Promise<CollectionItem> {
  return apiRequest<CollectionItem>('/collections', { method: 'POST', body: input, token })
}

export function updateCollectionApi(
  id: number,
  patch: UpdateCollectionInput,
  token: string,
): Promise<CollectionItem> {
  return apiRequest<CollectionItem>(`/collections/${id}`, { method: 'PATCH', body: patch, token })
}

export function deleteCollectionApi(id: number, token: string): Promise<void> {
  return apiRequest<void>(`/collections/${id}`, { method: 'DELETE', token })
}
