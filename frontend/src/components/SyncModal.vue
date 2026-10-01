<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  SYNC_RAW_MAX_LENGTH,
  applySyncApi,
  previewSyncApi,
  type SyncApplyInput,
  type SyncApplyResult,
  type SyncPreviewResult,
} from '@/api/sync'
import { ApiException } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/StatusBadge.vue'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
  synced: [result: SyncApplyResult]
}>()

const auth = useAuthStore()

const RAW_PLACEHOLDER =
  '例如看漫畫的瀏覽紀錄：\n[{"bn":"恶女是提线木偶","cn":"第107话", ...}, {"bn":"BLUE LOCK","cn":"第351话", ...}]'

type Step = 'paste' | 'confirm'

const step = ref<Step>('paste')
const raw = ref('')
const loading = ref(false)
const errorMsg = ref<string | null>(null)

const preview = ref<SyncPreviewResult | null>(null)
const selectedMatched = ref<Set<number>>(new Set())

const rawLength = computed(() => raw.value.length)
const tooLong = computed(() => rawLength.value > SYNC_RAW_MAX_LENGTH)
const canParse = computed(() => raw.value.trim() !== '' && !tooLong.value && !loading.value)

const selectedCount = computed(() => selectedMatched.value.size)
const isEmptyPreview = computed(() => preview.value !== null && preview.value.matched.length === 0)

function reset() {
  step.value = 'paste'
  raw.value = ''
  loading.value = false
  errorMsg.value = null
  preview.value = null
  selectedMatched.value = new Set()
}

function close() {
  if (!loading.value) emit('close')
}

function formatProgress(volume: number | null, chapter: number | null): string {
  const parts: string[] = []
  if (volume !== null) parts.push(`第${volume}卷`)
  if (chapter !== null) parts.push(`第${chapter}話`)
  return parts.length > 0 ? parts.join(' ') : '尚未記錄'
}

function errorMessage(err: unknown): string {
  if (err instanceof ApiException) {
    if (err.code === 'ASSISTANT_UNAVAILABLE') return 'AI 暫時無法解析，請稍後再試。'
    if (err.code === 'VALIDATION_ERROR') {
      return `內容格式不正確或超過 ${SYNC_RAW_MAX_LENGTH.toLocaleString()} 字元，請確認只複製了閱讀紀錄。`
    }
    return err.message
  }
  return '發生未預期的錯誤。'
}

async function parse() {
  const token = auth.getToken()
  if (!token || !canParse.value) return
  loading.value = true
  errorMsg.value = null
  try {
    const result = await previewSyncApi(raw.value, token)
    preview.value = result
    selectedMatched.value = new Set(result.matched.map((item) => item.collectionId))
    step.value = 'confirm'
  } catch (err) {
    errorMsg.value = errorMessage(err)
  } finally {
    loading.value = false
  }
}

function toggleMatched(collectionId: number) {
  const next = new Set(selectedMatched.value)
  if (next.has(collectionId)) next.delete(collectionId)
  else next.add(collectionId)
  selectedMatched.value = next
}

async function submit() {
  const token = auth.getToken()
  if (!token || !preview.value || selectedCount.value === 0) return

  const input: SyncApplyInput = { updates: [] }
  for (const item of preview.value.matched) {
    if (!selectedMatched.value.has(item.collectionId)) continue
    input.updates.push({
      collectionId: item.collectionId,
      newVolume: item.newVolume,
      newChapter: item.newChapter,
    })
  }

  loading.value = true
  errorMsg.value = null
  try {
    const result = await applySyncApi(input, token)
    emit('synced', result)
  } catch (err) {
    errorMsg.value = errorMessage(err)
  } finally {
    loading.value = false
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
        class="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-lg border border-neutral-200 bg-white shadow-xl"
      >
        <div class="border-b border-neutral-200 px-6 py-4">
          <h2 class="m-0 text-lg font-semibold text-neutral-900">一鍵更新閱讀進度</h2>
          <p class="mt-1 text-[12px] text-neutral-500">
            {{ step === 'paste' ? '步驟 1 / 2：貼上閱讀紀錄' : '步驟 2 / 2：確認要更新的漫畫' }}
          </p>
        </div>

        <div class="flex-1 overflow-y-auto px-6 py-5">
          <template v-if="step === 'paste'">
            <label for="sync-raw" class="block text-[13px] font-medium text-neutral-700">
              閱讀紀錄
            </label>
            <p class="mt-0.5 mb-2 text-[12px] text-neutral-500">
              貼上漫畫網站的閱讀紀錄，JSON、HTML 或純文字都可以，AI
              會抓出書名和看到的話數、卷數，比對你的收藏。
            </p>
            <textarea
              id="sync-raw"
              v-model="raw"
              rows="8"
              :placeholder="RAW_PLACEHOLDER"
              class="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 font-mono text-[12px] text-neutral-800 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            ></textarea>
            <p
              class="mt-1 text-right text-[12px]"
              :class="tooLong ? 'text-red-600' : 'text-neutral-400'"
            >
              {{ rawLength.toLocaleString() }} / {{ SYNC_RAW_MAX_LENGTH.toLocaleString() }} 字元
            </p>
            <p v-if="tooLong" class="text-[13px] text-red-600">
              內容超過上限，請確認只貼上了閱讀紀錄。
            </p>
          </template>

          <template v-else-if="preview">
            <p v-if="isEmptyPreview" class="py-6 text-center text-sm text-neutral-500">
              沒有需要更新的漫畫：收藏裡比對得到的漫畫，進度都是最新的。
            </p>

            <section v-if="preview.matched.length > 0">
              <h3 class="mb-2 text-[14px] font-semibold text-neutral-800">
                收藏中，有新進度（{{ preview.matched.length }}）
              </h3>
              <ul class="divide-y divide-neutral-100 rounded-md border border-neutral-200">
                <li v-for="item in preview.matched" :key="item.collectionId">
                  <label
                    class="flex cursor-pointer items-start gap-3 px-3 py-2.5 hover:bg-neutral-50"
                  >
                    <input
                      type="checkbox"
                      class="mt-1"
                      :checked="selectedMatched.has(item.collectionId)"
                      @change="toggleMatched(item.collectionId)"
                    />
                    <div class="min-w-0 flex-1">
                      <div class="flex items-center gap-2">
                        <span class="truncate text-[14px] font-medium text-neutral-900">{{
                          item.title
                        }}</span>
                        <StatusBadge :status="item.status" />
                      </div>
                      <p class="mt-0.5 text-[13px] text-neutral-700">
                        {{ formatProgress(item.currentVolume, item.currentChapter) }}
                        <span class="mx-1 text-neutral-400">→</span>
                        <span class="font-medium text-blue-700">{{
                          formatProgress(
                            item.newVolume ?? item.currentVolume,
                            item.newChapter ?? item.currentChapter,
                          )
                        }}</span>
                      </p>
                      <p class="mt-0.5 truncate text-[12px] text-neutral-400">
                        看漫畫：{{ item.sourceTitle }} · {{ item.sourceText }}
                      </p>
                    </div>
                  </label>
                </li>
              </ul>
            </section>
          </template>

          <p v-if="errorMsg" class="mt-3 text-[13px] text-red-600">{{ errorMsg }}</p>
        </div>

        <div class="flex justify-end gap-2 border-t border-neutral-200 px-6 py-4">
          <button
            v-if="step === 'confirm'"
            type="button"
            class="mr-auto rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50 disabled:opacity-50"
            :disabled="loading"
            @click="step = 'paste'"
          >
            上一步
          </button>
          <button
            type="button"
            class="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium text-neutral-700 transition hover:bg-neutral-50 disabled:opacity-50"
            :disabled="loading"
            @click="close"
          >
            取消
          </button>
          <button
            v-if="step === 'paste'"
            type="button"
            class="rounded-md bg-neutral-900 px-3 py-1.5 text-[13px] font-medium text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!canParse"
            @click="parse"
          >
            {{ loading ? 'AI 解析中…' : '解析' }}
          </button>
          <button
            v-else
            type="button"
            class="rounded-md bg-neutral-900 px-3 py-1.5 text-[13px] font-medium text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="loading || selectedCount === 0"
            @click="submit"
          >
            {{ loading ? '更新中…' : `送出更新（${selectedCount}）` }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
