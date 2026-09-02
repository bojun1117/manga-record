import type { MangaAdminItem, MangaCategory, MangaSearchResult } from '@/types/manga'
import { apiRequest } from './client'

export interface UpdateMangaInput {
  title?: string
  category?: MangaCategory
}

export interface MangaListResult {
  items: MangaSearchResult[]
  page: number
  pageSize: number
  total: number
}

export function searchMangaApi(query: string, token: string): Promise<MangaSearchResult[]> {
  const q = encodeURIComponent(query)
  return apiRequest<MangaSearchResult[]>(`/manga/search?q=${q}`, { token })
}

export function listMangaApi(
  page: number,
  pageSize: number,
  token: string,
): Promise<MangaListResult> {
  return apiRequest<MangaListResult>(`/manga?page=${page}&pageSize=${pageSize}`, { token })
}

export function updateMangaApi(
  id: number,
  input: UpdateMangaInput,
  token: string,
): Promise<MangaAdminItem> {
  return apiRequest<MangaAdminItem>(`/manga/${id}`, { method: 'PATCH', body: input, token })
}
