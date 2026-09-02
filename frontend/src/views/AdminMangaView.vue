<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { MangaCategory } from '@/types/manga'
import { useAuthStore } from '@/stores/auth'
import { listMangaApi, searchMangaApi, updateMangaApi } from '@/api/manga'
import { ApiException } from '@/api/client'
import { CATEGORY_OPTIONS } from '@/constants/manga'
import CategoryBadge from '@/components/CategoryBadge.vue'
import AppToast from '@/components/AppToast.vue'

interface MangaRow {
  id: number
  title: string
  category: MangaCategory
}

const router = useRouter()
const auth = useAuthStore()

const searchQuery = ref('')
const results = ref<MangaRow[]>([])
const loading = ref(false)
let searchTimer: number | null = null

const page = ref(1)
const total = ref(0)
const PAGE_SIZE = 20

const editingId = ref<number | null>(null)
const draftTitle = ref('')
const draftCategory = ref<MangaCategory>('other')
const saving = ref(false)
const errorMsg = ref<string | null>(null)

const browsing = (): boolean => searchQuery.value.trim() === ''

watch(searchQuery, (q) => {
  if (searchTimer !== null) window.clearTimeout(searchTimer)
  const trimmed = q.trim()
  if (trimmed.length === 0) {
    loadPage(1)
    return
  }
  searchTimer = window.setTimeout(() => runSearch(trimmed), 300)
})

onMounted(() => {
  loadPage(1)
})

async function loadPage(nextPage: number) {
  const token = auth.getToken()
  if (!token) return
  loading.value = true
  try {
    const res = await listMangaApi(nextPage, token)
    results.value = res.items
    page.value = res.page
    total.value = res.total
  } catch (err) {
    errorMsg.value = err instanceof ApiException ? err.message : '載入失敗'
  } finally {
    loading.value = false
  }
}

async function runSearch(q: string) {
  const token = auth.getToken()
  if (!token) return
  loading.value = true
  try {
    results.value = await searchMangaApi(q, token)
  } catch (err) {
    errorMsg.value = err instanceof ApiException ? err.message : '搜尋失敗'
  } finally {
    loading.value = false
  }
}

function prevPage() {
  if (page.value > 1) loadPage(page.value - 1)
}

function nextPage() {
  if (page.value * PAGE_SIZE < total.value) loadPage(page.value + 1)
}

function startEdit(row: MangaRow) {
  editingId.value = row.id
  draftTitle.value = row.title
  draftCategory.value = row.category
}

function cancelEdit() {
  editingId.value = null
}

async function saveEdit(row: MangaRow) {
  const token = auth.getToken()
  if (!token) return
  const trimmed = draftTitle.value.trim()
  if (trimmed.length === 0) return

  saving.value = true
  try {
    const updated = await updateMangaApi(
      row.id,
      { title: trimmed, category: draftCategory.value },
      token,
    )
    const idx = results.value.findIndex((r) => r.id === row.id)
    if (idx !== -1) {
      results.value[idx] = { id: updated.id, title: updated.title, category: updated.category }
    }
    editingId.value = null
  } catch (err) {
    if (err instanceof ApiException && err.code === 'DUPLICATE_TITLE') {
      errorMsg.value = '這個書名已經被另一部漫畫使用了'
    } else if (err instanceof ApiException) {
      errorMsg.value = err.message
    } else {
      errorMsg.value = '更新失敗'
    }
  } finally {
    saving.value = false
  }
}

function back() {
  router.push({ name: 'home' })
}
</script>

<template>
  <main class="mx-auto max-w-3xl px-4 py-8">
    <div class="mb-6 flex items-center justify-between gap-4">
      <h1 class="m-0 text-2xl font-semibold text-neutral-900">漫畫目錄管理</h1>
      <button
        type="button"
        class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50"
        @click="back"
      >
        返回
      </button>
    </div>

    <div class="mb-4">
      <input
        v-model="searchQuery"
        type="search"
        placeholder="搜尋漫畫名稱..."
        aria-label="搜尋漫畫名稱"
        class="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
      />
      <p v-if="loading" class="mt-1 text-[12px] text-neutral-400">載入中…</p>
    </div>

    <ul v-if="results.length > 0" class="space-y-2">
      <li
        v-for="row in results"
        :key="row.id"
        class="rounded-lg border border-neutral-200 bg-white px-4 py-3"
      >
        <template v-if="editingId === row.id">
          <div class="flex flex-col gap-2">
            <input
              v-model="draftTitle"
              type="text"
              class="w-full rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            />
            <select
              v-model="draftCategory"
              class="w-full rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            >
              <option v-for="opt in CATEGORY_OPTIONS" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
            <div class="flex justify-end gap-2">
              <button
                type="button"
                class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50"
                :disabled="saving"
                @click="cancelEdit"
              >
                取消
              </button>
              <button
                type="button"
                class="rounded-md bg-neutral-900 px-3 py-1.5 text-[13px] font-medium text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="saving"
                @click="saveEdit(row)"
              >
                儲存
              </button>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <p class="m-0 text-sm font-medium text-neutral-900">{{ row.title }}</p>
              <CategoryBadge :category="row.category" />
            </div>
            <button
              type="button"
              class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50"
              @click="startEdit(row)"
            >
              編輯
            </button>
          </div>
        </template>
      </li>
    </ul>
    <p v-else-if="!loading" class="text-sm text-neutral-500">
      {{ searchQuery.trim() !== '' ? '沒有符合的漫畫。' : '目前沒有任何漫畫。' }}
    </p>

    <div v-if="browsing() && total > PAGE_SIZE" class="mt-4 flex items-center justify-center gap-3">
      <button
        type="button"
        class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="page <= 1 || loading"
        @click="prevPage"
      >
        上一頁
      </button>
      <span class="text-[13px] text-neutral-500">
        第 {{ page }} 頁 · 共 {{ Math.ceil(total / PAGE_SIZE) }} 頁（{{ total }} 筆）
      </span>
      <button
        type="button"
        class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="page * PAGE_SIZE >= total || loading"
        @click="nextPage"
      >
        下一頁
      </button>
    </div>

    <AppToast :message="errorMsg" variant="error" @dismiss="errorMsg = null" />
  </main>
</template>
