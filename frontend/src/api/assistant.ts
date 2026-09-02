import type { CollectionItem } from '@/types/manga'
import { apiRequest } from './client'

export interface AssistantQueryResult {
  answer: string
  items: CollectionItem[]
}

export function queryAssistantApi(question: string, token: string): Promise<AssistantQueryResult> {
  return apiRequest<AssistantQueryResult>('/assistant/query', {
    method: 'POST',
    body: { question },
    token,
  })
}
