import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  type CreateCollectionInput,
  type UpdateCollectionInput,
  createCollectionApi,
  deleteCollectionApi,
  updateCollectionApi,
} from '@/api/collections'
import { ApiException } from '@/api/client'
import type { CollectionItem } from '@/types/manga'
import { useAuthStore } from './auth'

export const useCollectionStore = defineStore('collection', () => {
  const lastError = ref<string | null>(null)

  function getToken(): string {
    const auth = useAuthStore()
    const t = auth.getToken()
    if (!t) throw new ApiException(401, null, 'not authenticated')
    return t
  }

  function recordError(err: unknown): void {
    if (err instanceof ApiException) {
      lastError.value = err.message
      if (err.isUnauthorized) {
        const auth = useAuthStore()
        auth.logout()
      }
    } else if (err instanceof Error) {
      lastError.value = err.message
    } else {
      lastError.value = String(err)
    }
  }

  function clearError(): void {
    lastError.value = null
  }

  async function add(input: CreateCollectionInput): Promise<CollectionItem> {
    try {
      return await createCollectionApi(input, getToken())
    } catch (err) {
      recordError(err)
      throw err
    }
  }

  async function update(id: number, patch: UpdateCollectionInput): Promise<CollectionItem> {
    try {
      return await updateCollectionApi(id, patch, getToken())
    } catch (err) {
      recordError(err)
      throw err
    }
  }

  async function remove(id: number): Promise<void> {
    try {
      await deleteCollectionApi(id, getToken())
    } catch (err) {
      recordError(err)
      throw err
    }
  }

  return {
    lastError,
    add,
    update,
    remove,
    clearError,
  }
})
