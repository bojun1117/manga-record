<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { RouterLink, useRouter } from 'vue-router'
import type { MangaCategory, ReadingStatus } from '@/types/manga'
import { useAuthStore } from '@/stores/auth'
import { useCollectionStore } from '@/stores/collection'
import MangaCard from '@/components/MangaCard.vue'
import AddMangaModal from '@/components/AddMangaModal.vue'
import AppToast from '@/components/AppToast.vue'
import { normalizeChinese } from '@/utils/chinese'
import { STATUS_OPTIONS, CATEGORY_OPTIONS } from '@/constants/manga'

const router = useRouter()
const auth = useAuthStore()
const store = useCollectionStore()
const { collections, loading, loaded, lastError } = storeToRefs(store)

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

const sortedCollections = computed(() =>
  [...collections.value].sort(
    (a, b) => new Date(b.lastReadAt).getTime() - new Date(a.lastReadAt).getTime(),
  ),
)

const normalizedQuery = computed(() => normalizeChinese(searchQuery.value.trim()))

function categoryOk(c: { category: MangaCategory }) {
  return activeCategory.value === 'all' || c.category === activeCategory.value
}

function queryOk(c: { title: string }) {
  return (
    normalizedQuery.value === '' || normalizeChinese(c.title).includes(normalizedQuery.value)
  )
}

const visibleCollections = computed(() =>
  sortedCollections.value.filter((c) => {
    const statusOk =
      activeStatus.value === 'all' ? c.status !== 'plan_to_read' : c.status === activeStatus.value
    return statusOk && categoryOk(c) && queryOk(c)
  }),
)

const planToReadCollections = computed(() =>
  sortedCollections.value.filter((c) => c.status === 'plan_to_read' && categoryOk(c) && queryOk(c)),
)

const stats = computed(() => {
  const total = collections.value.length
  const planToRead = collections.value.filter((c) => c.status === 'plan_to_read').length
  const reading = collections.value.filter((c) => c.status === 'reading').length
  const completed = collections.value.filter((c) => c.status === 'completed').length
  const dropped = collections.value.filter((c) => c.status === 'dropped').length
  return { total, planToRead, reading, completed, dropped }
})

onMounted(async () => {
  if (auth.isAuthenticated && !loaded.value) {
    try {
      await store.getAll()
    } catch {
      if (!auth.isAuthenticated) {
        router.replace({ name: 'login' })
      }
    }
  }
})

function logout() {
  auth.logout()
  store.reset()
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
      v-if="loading && !loaded"
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
        v-if="visibleCollections.length > 0"
        class="grid gap-3"
        style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))"
      >
        <MangaCard v-for="item in visibleCollections" :key="item.id" :item="item" />
      </div>
      <div
        v-else
        class="rounded-lg border border-dashed border-neutral-300 bg-white px-6 py-16 text-center"
      >
        <p v-if="collections.length === 0" class="text-sm text-neutral-500">
          還沒有任何漫畫,點右上「＋ 新增漫畫」開始記錄。
        </p>
        <p v-else-if="normalizedQuery !== ''" class="text-sm text-neutral-500">
          沒有符合「{{ searchQuery.trim() }}」的漫畫。
        </p>
        <p v-else class="text-sm text-neutral-500">這個篩選條件下沒有漫畫。</p>
      </div>

      <section v-if="stats.planToRead > 0" class="mt-8 border-t border-neutral-200 pt-5">
        <h2 class="mb-3 text-lg font-semibold text-neutral-800">
          待看清單
          <span class="text-[13px] font-normal text-neutral-400">
            ({{ planToReadCollections.length }})
          </span>
        </h2>
        <div
          v-if="planToReadCollections.length > 0"
          class="grid gap-3"
          style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))"
        >
          <MangaCard v-for="item in planToReadCollections" :key="item.id" :item="item" />
        </div>
        <p v-else class="text-sm text-neutral-500">這個篩選條件下沒有待看的漫畫。</p>
      </section>
    </template>

    <AddMangaModal :open="addModalOpen" @close="addModalOpen = false" @added="addModalOpen = false" />

    <AppToast :message="lastError" variant="error" @dismiss="store.clearError()" />
  </main>
</template>
