import type { MangaSearchResult } from '@/types/manga'
import { apiRequest } from './client'

// API.md §7:查無結果回空陣列,不是錯誤——呼叫端用這個判斷「這是新漫畫」。
export function searchMangaApi(query: string, token: string): Promise<MangaSearchResult[]> {
  const q = encodeURIComponent(query)
  return apiRequest<MangaSearchResult[]>(`/manga/search?q=${q}`, { token })
}
