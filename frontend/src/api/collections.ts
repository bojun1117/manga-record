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

export interface ListCollectionsParams {
  status: ReadingStatus[]
  category?: MangaCategory
  q?: string
  page: number
}

export interface CollectionListResult {
  items: CollectionItem[]
  page: number
  pageSize: number
  total: number
}

export interface CollectionStats {
  total: number
  planToRead: number
  reading: number
  completed: number
  dropped: number
}

export function listCollectionsApi(
  params: ListCollectionsParams,
  token: string,
): Promise<CollectionListResult> {
  const usp = new URLSearchParams()
  for (const s of params.status) usp.append('status', s)
  if (params.category) usp.set('category', params.category)
  if (params.q) usp.set('q', params.q)
  usp.set('page', String(params.page))
  return apiRequest<CollectionListResult>(`/collections?${usp.toString()}`, { token })
}

export function getCollectionStatsApi(token: string): Promise<CollectionStats> {
  return apiRequest<CollectionStats>('/collections/stats', { token })
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
