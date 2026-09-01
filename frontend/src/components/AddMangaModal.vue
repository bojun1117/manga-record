<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import type { MangaCategory, MangaSearchResult, ReadingStatus } from '@/types/manga'
import type { CreateCollectionInput } from '@/api/collections'
import { searchMangaApi } from '@/api/manga'
import { useAuthStore } from '@/stores/auth'
import { useCollectionStore } from '@/stores/collection'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
  added: []
}>()

const auth = useAuthStore()
const store = useCollectionStore()

const title = ref('')
const status = ref<ReadingStatus>('plan_to_read')
const category = ref<MangaCategory>('other')
// v-model 在 type="number" input 上會把字串 cast 成 number,
// 所以這兩個 ref 實際運行時可能是 string('') 或 number。
const volumeStr = ref<string | number>('')
const chapterStr = ref<string | number>('')
const rating = ref<number | null>(null)
const submitting = ref(false)

const STATUS_OPTIONS: ReadonlyArray<{ value: ReadingStatus; label: string }> = [
  { value: 'plan_to_read', label: '待看' },
  { value: 'reading', label: '追讀中' },
  { value: 'dropped', label: '棄坑' },
  { value: 'completed', label: '已追完' },
]

const CATEGORY_OPTIONS: ReadonlyArray<{ value: MangaCategory; label: string }> = [
  { value: 'hot_blooded', label: '熱血' },
  { value: 'mystery', label: '懸疑' },
  { value: 'adventure', label: '冒險' },
  { value: 'romance', label: '愛情' },
  { value: 'casual', label: '輕鬆' },
  { value: 'competition', label: '競技' },
  { value: 'revenge', label: '復仇' },
  { value: 'slice_of_life', label: '生活' },
  { value: 'other', label: '其他' },
]

// ─── 模糊搜尋自動完成 ─────────────────────────────────────
// 打字時打 /manga/search,選到既有漫畫就鎖住分類欄位(分類屬於漫畫本身,
// 新增收藏時不能改既有漫畫的分類,見 API.md §9)。
const searchResults = ref<MangaSearchResult[]>([])
const searchLoading = ref(false)
const showSuggestions = ref(false)
// 記錄目前鎖定分類欄位的是哪個標題;書名一旦被改掉就解除鎖定(代表要新建一部漫畫)
const matchedTitle = ref<string | null>(null)
let searchTimer: number | null = null

const categoryLocked = computed(
  () => matchedTitle.value !== null && matchedTitle.value === title.value,
)

watch(title, (newTitle) => {
  if (matchedTitle.value !== null && newTitle !== matchedTitle.value) {
    matchedTitle.value = null
  }

  if (searchTimer !== null) window.clearTimeout(searchTimer)
  const trimmed = newTitle.trim()
  if (trimmed.length === 0) {
    searchResults.value = []
    showSuggestions.value = false
    return
  }
  searchTimer = window.setTimeout(() => runSearch(trimmed), 300)
})

async function runSearch(q: string) {
  const token = auth.getToken()
  if (!token) return
  searchLoading.value = true
  try {
    searchResults.value = await searchMangaApi(q, token)
    showSuggestions.value = true
  } catch {
    // 搜尋失敗不影響主流程(使用者還是可以直接新增新漫畫),不特別顯示錯誤
    searchResults.value = []
  } finally {
    searchLoading.value = false
  }
}

function pickSuggestion(result: MangaSearchResult) {
  title.value = result.title
  category.value = result.category
  matchedTitle.value = result.title
  showSuggestions.value = false
}

function hideSuggestionsSoon() {
  // 延遲一點再關閉,不然點擊建議項目時 blur 會搶在 click 前面把清單關掉
  window.setTimeout(() => {
    showSuggestions.value = false
  }, 150)
}

function refocusSuggestions() {
  if (searchResults.value.length > 0 && !categoryLocked.value) {
    showSuggestions.value = true
  }
}

// ─── 表單邏輯 ─────────────────────────────────────────────

const isPlanToRead = computed(() => status.value === 'plan_to_read')
// 評分只在已追完(漫畫已完結)才顯示,API 本身不限制狀態,這是前端 UI 的限制
const isCompleted = computed(() => status.value === 'completed')
const titleTrimmed = computed(() => title.value.trim())
const canSubmit = computed(() => titleTrimmed.value.length > 0 && !submitting.value)

function reset() {
  title.value = ''
  status.value = 'plan_to_read'
  category.value = 'other'
  volumeStr.value = ''
  chapterStr.value = ''
  rating.value = null
  submitting.value = false
  searchResults.value = []
  showSuggestions.value = false
  matchedTitle.value = null
}

function close() {
  emit('close')
}

// v-model 在 <input type="number"> 上會把值自動轉成 number,空字串保留為 ''。
// 所以這裡同時要接 string 和 number。
function parseNumberOrNull(s: unknown): number | null {
  if (typeof s === 'number') {
    if (!Number.isFinite(s) || s < 0 || !Number.isInteger(s)) return null
    return s
  }
  const t = String(s ?? '').trim()
  if (t === '') return null
  const n = Number(t)
  if (!Number.isFinite(n) || n < 0 || !Number.isInteger(n)) return null
  return n
}

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true

  const input: CreateCollectionInput = {
    mangaName: titleTrimmed.value,
    category: category.value,
    status: status.value,
    currentVolume: isPlanToRead.value ? null : parseNumberOrNull(volumeStr.value),
    currentChapter: isPlanToRead.value ? null : parseNumberOrNull(chapterStr.value),
    rating: isCompleted.value ? rating.value : null,
  }

  try {
    await store.add(input)
    emit('added')
    reset()
    close()
  } catch (err) {
    console.error('add collection failed', err)
    submitting.value = false
  }
}

function onKeydown(e: KeyboardEvent) {
  if (!props.open) return
  if (e.key === 'Escape') {
    e.preventDefault()
    close()
  }
}

// 開啟時重置欄位
watch(
  () => props.open,
  (v) => {
    if (v) reset()
  },
)

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      @click.self="close"
    >
      <div
        role="dialog"
        aria-modal="true"
        class="w-full max-w-md rounded-lg border border-neutral-200 bg-white p-6 shadow-xl"
      >
        <h2 class="m-0 text-lg font-semibold text-neutral-900">新增漫畫</h2>

        <div class="mt-5 space-y-4">
          <!-- 書名 + 模糊搜尋自動完成 -->
          <div class="relative">
            <label for="add-title" class="block text-[13px] font-medium text-neutral-700">
              書名 <span class="text-red-500">*</span>
            </label>
            <input
              id="add-title"
              v-model="title"
              type="text"
              autofocus
              autocomplete="off"
              class="mt-1 w-full rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              placeholder="例如:進擊的巨人"
              @focus="refocusSuggestions"
              @blur="hideSuggestionsSoon"
            />
            <p v-if="categoryLocked" class="mt-1 text-[12px] text-neutral-500">
              已選擇現有漫畫,分類欄位鎖定(分類屬於漫畫本身)
            </p>
            <p v-else-if="searchLoading" class="mt-1 text-[12px] text-neutral-400">搜尋中…</p>

            <!-- 建議清單 -->
            <ul
              v-if="showSuggestions && searchResults.length > 0"
              class="absolute z-10 mt-1 w-full rounded-md border border-neutral-200 bg-white py-1 shadow-lg"
            >
              <li v-for="result in searchResults" :key="result.id">
                <button
                  type="button"
                  class="flex w-full items-center justify-between px-3 py-1.5 text-left text-[13px] text-neutral-700 hover:bg-neutral-50"
                  @mousedown.prevent="pickSuggestion(result)"
                >
                  <span>{{ result.title }}</span>
                </button>
              </li>
            </ul>
          </div>

          <!-- status -->
          <div>
            <label for="add-status" class="block text-[13px] font-medium text-neutral-700">
              狀態
            </label>
            <select
              id="add-status"
              v-model="status"
              class="mt-1 w-full rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            >
              <option v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>

          <!-- category -->
          <div>
            <label for="add-category" class="block text-[13px] font-medium text-neutral-700">
              分類
            </label>
            <select
              id="add-category"
              v-model="category"
              :disabled="categoryLocked"
              class="mt-1 w-full rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-neutral-100 disabled:text-neutral-400"
            >
              <option v-for="opt in CATEGORY_OPTIONS" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>

          <!-- 非待看:卷 / 話 -->
          <template v-if="!isPlanToRead">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label for="add-vol" class="block text-[13px] font-medium text-neutral-700">
                  卷(可空)
                </label>
                <input
                  id="add-vol"
                  v-model="volumeStr"
                  type="number"
                  min="0"
                  inputmode="numeric"
                  class="mt-1 w-full rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                  placeholder="—"
                />
              </div>
              <div>
                <label for="add-ch" class="block text-[13px] font-medium text-neutral-700">
                  話(可空)
                </label>
                <input
                  id="add-ch"
                  v-model="chapterStr"
                  type="number"
                  min="0"
                  inputmode="numeric"
                  class="mt-1 w-full rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                  placeholder="—"
                />
              </div>
            </div>
          </template>

          <!-- 評分只在已追完(漫畫已完結)才顯示 -->
          <div v-if="isCompleted">
            <label class="block text-[13px] font-medium text-neutral-700">
              推薦指數(可空)
            </label>
            <div class="mt-1 flex items-center gap-1 text-2xl tracking-[2px]">
              <button
                v-for="n in 5"
                :key="n"
                type="button"
                class="cursor-pointer leading-none transition-transform hover:scale-110"
                :class="rating !== null && n <= rating ? 'text-amber-500' : 'text-neutral-300'"
                :title="rating === n ? '再次點擊清除' : `評為 ${n} 顆星`"
                @click="rating = rating === n ? null : n"
              >
                {{ rating !== null && n <= rating ? '★' : '☆' }}
              </button>
              <span class="ml-2 text-xs text-neutral-400">
                {{ rating === null ? '未評分' : `${rating} 顆星` }}
              </span>
            </div>
          </div>
        </div>

        <div class="mt-6 flex justify-end gap-2">
          <button
            type="button"
            class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50"
            @click="close"
          >
            取消
          </button>
          <button
            type="button"
            class="rounded-md bg-neutral-900 px-3 py-1.5 text-[13px] font-medium text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!canSubmit"
            @click="submit"
          >
            新增
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
