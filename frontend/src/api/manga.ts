import type { MangaSearchResult } from '@/types/manga'
import { apiRequest } from './client'

export function searchMangaApi(query: string, token: string): Promise<MangaSearchResult[]> {
  const q = encodeURIComponent(query)
  return apiRequest<MangaSearchResult[]>(`/manga/search?q=${q}`, { token })
}
