<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import type { MangaCategory, MangaSearchResult, ReadingStatus } from '@/types/manga'
import type { CreateCollectionInput } from '@/api/collections'
import { searchMangaApi } from '@/api/manga'
import { useAuthStore } from '@/stores/auth'
import { useCollectionStore } from '@/stores/collection'
import { STATUS_OPTIONS, CATEGORY_OPTIONS } from '@/constants/manga'
import { parseNonNegativeInt } from '@/utils/number'

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
const volumeStr = ref<string | number>('')
const chapterStr = ref<string | number>('')
const rating = ref<number | null>(null)
const submitting = ref(false)

const searchResults = ref<MangaSearchResult[]>([])
const searchLoading = ref(false)
const showSuggestions = ref(false)
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
  window.setTimeout(() => {
    showSuggestions.value = false
  }, 150)
}

function refocusSuggestions() {
  if (searchResults.value.length > 0 && !categoryLocked.value) {
    showSuggestions.value = true
  }
}

const isPlanToRead = computed(() => status.value === 'plan_to_read')
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

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true

  const input: CreateCollectionInput = {
    mangaName: titleTrimmed.value,
    category: category.value,
    status: status.value,
    currentVolume: isPlanToRead.value ? null : (parseNonNegativeInt(volumeStr.value) ?? null),
    currentChapter: isPlanToRead.value ? null : (parseNonNegativeInt(chapterStr.value) ?? null),
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
