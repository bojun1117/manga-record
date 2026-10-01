import type { ReadingStatus } from '@/types/manga'
import { apiRequest } from './client'

export const SYNC_RAW_MAX_LENGTH = 50_000

export interface SyncMatchedItem {
  collectionId: number
  title: string
  status: ReadingStatus
  sourceTitle: string
  sourceText: string
  currentVolume: number | null
  currentChapter: number | null
  newVolume: number | null
  newChapter: number | null
}

export interface SyncPreviewResult {
  matched: SyncMatchedItem[]
}

export interface SyncApplyInput {
  updates: { collectionId: number; newVolume: number | null; newChapter: number | null }[]
}

export interface SyncApplyResult {
  updated: number
}

export function previewSyncApi(raw: string, token: string): Promise<SyncPreviewResult> {
  return apiRequest<SyncPreviewResult>('/collections/sync/preview', {
    method: 'POST',
    body: { raw },
    token,
  })
}

export function applySyncApi(input: SyncApplyInput, token: string): Promise<SyncApplyResult> {
  return apiRequest<SyncApplyResult>('/collections/sync/apply', {
    method: 'POST',
    body: input,
    token,
  })
}
