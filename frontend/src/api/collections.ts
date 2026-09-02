import type { CollectionItem, MangaCategory, ReadingStatus } from '@/types/manga'
import { apiRequest } from './client'

export interface CreateCollectionInput {
  mangaName: string
  category?: MangaCategory
  status: ReadingStatus
  currentVolume: number | null
  currentChapter: number | null
  rating: number | null
}

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
