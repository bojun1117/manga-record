import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  type CreateCollectionInput,
  type UpdateCollectionInput,
  createCollectionApi,
  deleteCollectionApi,
  listCollectionsApi,
  updateCollectionApi,
} from '@/api/collections'
import { ApiException } from '@/api/client'
import type { CollectionItem } from '@/types/manga'
import { useAuthStore } from './auth'

export const useCollectionStore = defineStore('collection', () => {
  const collections = ref<CollectionItem[]>([])
  const loading = ref(false)
  const loaded = ref(false)
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

  async function getAll(): Promise<CollectionItem[]> {
    loading.value = true
    try {
      const list = await listCollectionsApi(getToken())
      collections.value = list
      loaded.value = true
      return list.map((c) => ({ ...c }))
    } catch (err) {
      recordError(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function add(input: CreateCollectionInput): Promise<CollectionItem> {
    try {
      const created = await createCollectionApi(input, getToken())
      collections.value.push(created)
      return { ...created }
    } catch (err) {
      recordError(err)
      throw err
    }
  }

  async function update(id: number, patch: UpdateCollectionInput): Promise<CollectionItem> {
    const idx = collections.value.findIndex((c) => c.id === id)
    if (idx === -1) {
      const e = new Error(`Collection entry not found locally: ${id}`)
      recordError(e)
      throw e
    }

    const original = collections.value[idx]!
    const optimistic: CollectionItem = {
      ...original,
      ...patch,
      id: original.id,
      mangaId: original.mangaId,
      title: original.title,
      category: original.category,
      createdAt: original.createdAt,
    }
    collections.value[idx] = optimistic

    try {
      const updated = await updateCollectionApi(id, patch, getToken())
      collections.value[idx] = updated
      return { ...updated }
    } catch (err) {
      collections.value[idx] = original
      recordError(err)
      throw err
    }
  }

  async function remove(id: number): Promise<void> {
    const idx = collections.value.findIndex((c) => c.id === id)
    if (idx === -1) {
      const e = new Error(`Collection entry not found locally: ${id}`)
      recordError(e)
      throw e
    }

    const removed = collections.value[idx]!
    collections.value.splice(idx, 1)

    try {
      await deleteCollectionApi(id, getToken())
    } catch (err) {
      collections.value.splice(idx, 0, removed)
      recordError(err)
      throw err
    }
  }

  function reset(): void {
    collections.value = []
    loading.value = false
    loaded.value = false
    lastError.value = null
  }

  return {
    collections,
    loading,
    loaded,
    lastError,
    getAll,
    add,
    update,
    remove,
    clearError,
    reset,
  }
})
