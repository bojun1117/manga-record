<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { RouterLink, useRouter } from 'vue-router'
import type { CollectionItem, MangaCategory, ReadingStatus } from '@/types/manga'
import { useAuthStore } from '@/stores/auth'
import { useCollectionStore } from '@/stores/collection'
import { getCollectionStatsApi, listCollectionsApi, type CollectionStats } from '@/api/collections'
import { ApiException } from '@/api/client'
import MangaCard from '@/components/MangaCard.vue'
import AddMangaModal from '@/components/AddMangaModal.vue'
import AppToast from '@/components/AppToast.vue'
import { STATUS_OPTIONS, CATEGORY_OPTIONS } from '@/constants/manga'

const PAGE_SIZE = 30

const router = useRouter()
const auth = useAuthStore()
const store = useCollectionStore()
const { lastError } = storeToRefs(store)

const addModalOpen = ref(false)

type StatusFilter = 'all' | ReadingStatus
type CategoryFilter = 'all' | MangaCategory

const activeStatus = ref<StatusFilter>('all')
const activeCategory = ref<CategoryFilter>('all')
const searchQuery = ref('')

const STATUS_FILTERS: ReadonlyArray<{ value: StatusFilter; label: string }> = [
  { value: 'all', label: '全部' },
  ...STATUS_OPTIONS.filter((o) => o.value !== 'plan_to_read'),
]

const CATEGORY_FILTERS: ReadonlyArray<{ value: CategoryFilter; label: string }> = [
  { value: 'all', label: '全部' },
  ...CATEGORY_OPTIONS,
]

const stats = ref<CollectionStats>({
  total: 0,
  planToRead: 0,
  reading: 0,
  completed: 0,
  dropped: 0,
})

const mainItems = ref<CollectionItem[]>([])
const mainPage = ref(1)
const mainTotal = ref(0)
const mainLoading = ref(false)
const mainLoaded = ref(false)

const planItems = ref<CollectionItem[]>([])
const planPage = ref(1)
const planTotal = ref(0)
const planLoading = ref(false)

let searchTimer: number | null = null

function mainStatuses(): ReadingStatus[] {
  if (activeStatus.value === 'all') return ['reading', 'dropped', 'completed']
  return [activeStatus.value]
}

function handleLoadError(err: unknown) {
  if (err instanceof ApiException) {
    if (err.isUnauthorized) {
      auth.logout()
      router.replace({ name: 'login' })
      return
    }
    lastError.value = err.message
  } else if (err instanceof Error) {
    lastError.value = err.message
  }
}

async function loadStats() {
  const token = auth.getToken()
  if (!token) return
  try {
    stats.value = await getCollectionStatsApi(token)
  } catch (err) {
    handleLoadError(err)
  }
}

async function loadMain() {
  const token = auth.getToken()
  if (!token) return
  mainLoading.value = true
  try {
    const res = await listCollectionsApi(
      {
        status: mainStatuses(),
        category: activeCategory.value === 'all' ? undefined : activeCategory.value,
        q: searchQuery.value.trim() || undefined,
        page: mainPage.value,
      },
      token,
    )
    mainItems.value = res.items
    mainTotal.value = res.total
  } catch (err) {
    handleLoadError(err)
  } finally {
    mainLoading.value = false
    mainLoaded.value = true
  }
}

async function loadPlanToRead() {
  const token = auth.getToken()
  if (!token) return
  planLoading.value = true
  try {
    const res = await listCollectionsApi(
      {
        status: ['plan_to_read'],
        category: activeCategory.value === 'all' ? undefined : activeCategory.value,
        q: searchQuery.value.trim() || undefined,
        page: planPage.value,
      },
      token,
    )
    planItems.value = res.items
    planTotal.value = res.total
  } catch (err) {
    handleLoadError(err)
  } finally {
    planLoading.value = false
  }
}

function loadAll() {
  loadStats()
  loadMain()
  loadPlanToRead()
}

function resetAndReload() {
  mainPage.value = 1
  planPage.value = 1
  loadAll()
}

watch([activeStatus, activeCategory], resetAndReload)

watch(searchQuery, () => {
  if (searchTimer !== null) window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(resetAndReload, 300)
})

function mainPrevPage() {
  if (mainPage.value > 1) {
    mainPage.value -= 1
    loadMain()
  }
}

function mainNextPage() {
  if (mainPage.value * PAGE_SIZE < mainTotal.value) {
    mainPage.value += 1
    loadMain()
  }
}

function planPrevPage() {
  if (planPage.value > 1) {
    planPage.value -= 1
    loadPlanToRead()
  }
}

function planNextPage() {
  if (planPage.value * PAGE_SIZE < planTotal.value) {
    planPage.value += 1
    loadPlanToRead()
  }
}

onMounted(() => {
  if (auth.isAuthenticated) {
    loadAll()
  }
})

function onCardChanged() {
  loadAll()
}

function onAdded() {
  addModalOpen.value = false
  resetAndReload()
}

function logout() {
  auth.logout()
  router.replace({ name: 'login' })
}
</script>

<template>
  <main class="mx-auto max-w-6xl px-4 py-8">
    <div class="mb-6 flex items-center justify-between gap-4">
      <div>
        <h1 class="m-0 text-2xl font-semibold text-neutral-900">我的漫畫</h1>
        <p class="mt-1 text-[13px] text-neutral-500">
          共 {{ stats.total }} 部 · 待看 {{ stats.planToRead }} · 追讀中 {{ stats.reading }} ·
          已追完 {{ stats.completed }} · 棄坑 {{ stats.dropped }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50"
          @click="addModalOpen = true"
        >
          ＋ 新增漫畫
        </button>
        <RouterLink
          v-if="auth.isAdmin"
          :to="{ name: 'admin-manga' }"
          class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50"
        >
          管理目錄
        </RouterLink>
        <button
          type="button"
          class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-500 transition hover:bg-neutral-50"
          @click="logout"
        >
          登出
        </button>
      </div>
    </div>

    <div class="mb-3">
      <label class="relative block">
        <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400">
          🔍
        </span>
        <input
          v-model="searchQuery"
          type="search"
          placeholder="搜尋漫畫名稱..."
          aria-label="搜尋漫畫名稱"
          class="w-full rounded-md border border-neutral-300 bg-white py-2 pl-9 pr-9 text-[14px] text-neutral-800 placeholder-neutral-400 transition focus:border-neutral-500 focus:outline-none focus:ring-1 focus:ring-neutral-500"
        />
        <button
          v-if="searchQuery"
          type="button"
          aria-label="清除搜尋"
          class="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-neutral-400 transition hover:bg-neutral-100 hover:text-neutral-600"
          @click="searchQuery = ''"
        >
          ✕
        </button>
      </label>
    </div>

    <div class="mb-2 flex flex-wrap items-center gap-2">
      <span class="text-[12px] text-neutral-400">狀態</span>
      <button
        v-for="f in STATUS_FILTERS"
        :key="f.value"
        type="button"
        class="rounded-full border px-3 py-1 text-[13px] transition"
        :class="
          activeStatus === f.value
            ? 'border-neutral-900 bg-neutral-900 text-white'
            : 'border-neutral-200 bg-white text-neutral-600 hover:bg-neutral-50'
        "
        @click="activeStatus = f.value"
      >
        {{ f.label }}
      </button>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-2">
      <span class="text-[12px] text-neutral-400">分類</span>
      <button
        v-for="f in CATEGORY_FILTERS"
        :key="f.value"
        type="button"
        class="rounded-full border px-3 py-1 text-[13px] transition"
        :class="
          activeCategory === f.value
            ? 'border-neutral-900 bg-neutral-900 text-white'
            : 'border-neutral-200 bg-white text-neutral-600 hover:bg-neutral-50'
        "
        @click="activeCategory = f.value"
      >
        {{ f.label }}
      </button>
    </div>

    <div
      v-if="mainLoading && !mainLoaded"
      class="grid gap-3"
      style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))"
    >
      <div
        v-for="i in 6"
        :key="i"
        class="h-[160px] animate-pulse rounded-lg border border-neutral-200 bg-neutral-100"
      ></div>
    </div>

    <template v-else>
      <div
        v-if="mainItems.length > 0"
        class="grid gap-3"
        style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))"
      >
        <MangaCard v-for="item in mainItems" :key="item.id" :item="item" @changed="onCardChanged" />
      </div>
      <div
        v-else
        class="rounded-lg border border-dashed border-neutral-300 bg-white px-6 py-16 text-center"
      >
        <p v-if="stats.total === 0" class="text-sm text-neutral-500">
          還沒有任何漫畫,點右上「＋ 新增漫畫」開始記錄。
        </p>
        <p v-else-if="searchQuery.trim() !== ''" class="text-sm text-neutral-500">
          沒有符合「{{ searchQuery.trim() }}」的漫畫。
        </p>
        <p v-else class="text-sm text-neutral-500">這個篩選條件下沒有漫畫。</p>
      </div>

      <div v-if="mainTotal > PAGE_SIZE" class="mt-4 flex items-center justify-center gap-3">
        <button
          type="button"
          class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="mainPage <= 1 || mainLoading"
          @click="mainPrevPage"
        >
          上一頁
        </button>
        <span class="text-[13px] text-neutral-500">
          第 {{ mainPage }} 頁 · 共 {{ Math.ceil(mainTotal / PAGE_SIZE) }} 頁（{{ mainTotal }} 筆）
        </span>
        <button
          type="button"
          class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="mainPage * PAGE_SIZE >= mainTotal || mainLoading"
          @click="mainNextPage"
        >
          下一頁
        </button>
      </div>

      <section v-if="stats.planToRead > 0" class="mt-8 border-t border-neutral-200 pt-5">
        <h2 class="mb-3 text-lg font-semibold text-neutral-800">
          待看清單
          <span class="text-[13px] font-normal text-neutral-400">({{ stats.planToRead }})</span>
        </h2>
        <div
          v-if="planItems.length > 0"
          class="grid gap-3"
          style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))"
        >
          <MangaCard v-for="item in planItems" :key="item.id" :item="item" @changed="onCardChanged" />
        </div>
        <p v-else-if="!planLoading" class="text-sm text-neutral-500">
          這個篩選條件下沒有待看的漫畫。
        </p>

        <div v-if="planTotal > PAGE_SIZE" class="mt-4 flex items-center justify-center gap-3">
          <button
            type="button"
            class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="planPage <= 1 || planLoading"
            @click="planPrevPage"
          >
            上一頁
          </button>
          <span class="text-[13px] text-neutral-500">
            第 {{ planPage }} 頁 · 共 {{ Math.ceil(planTotal / PAGE_SIZE) }} 頁（{{ planTotal }} 筆）
          </span>
          <button
            type="button"
            class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="planPage * PAGE_SIZE >= planTotal || planLoading"
            @click="planNextPage"
          >
            下一頁
          </button>
        </div>
      </section>
    </template>

    <AddMangaModal :open="addModalOpen" @close="addModalOpen = false" @added="onAdded" />

    <AppToast :message="lastError" variant="error" @dismiss="store.clearError()" />
  </main>
</template>
