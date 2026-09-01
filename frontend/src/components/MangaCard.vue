<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CollectionItem, ReadingStatus } from '@/types/manga'
import StatusBadge from '@/components/StatusBadge.vue'
import CategoryBadge from '@/components/CategoryBadge.vue'
import MangaCardEditableNumber from '@/components/MangaCardEditableNumber.vue'
import MangaCardRating from '@/components/MangaCardRating.vue'
import MangaCardActions from '@/components/MangaCardActions.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useCollectionStore } from '@/stores/collection'
import { formatRelativeTime } from '@/utils/time'

const props = defineProps<{
  item: CollectionItem
}>()

const store = useCollectionStore()

const isDropped = computed(() => props.item.status === 'dropped')
// 待看還沒開始追,不顯示進度區塊;其他三個狀態都顯示
const isPlanToRead = computed(() => props.item.status === 'plan_to_read')
// 評分只在已追完(漫畫已完結)才顯示,API 本身不限制狀態,這是前端 UI 的限制
const isCompleted = computed(() => props.item.status === 'completed')

const relativeTime = computed(() => formatRelativeTime(props.item.lastReadAt))

const confirmDeleteOpen = ref(false)

async function updateVolume(next: number | null) {
  await store.update(props.item.id, { currentVolume: next })
}

async function updateChapter(next: number | null) {
  await store.update(props.item.id, { currentChapter: next })
}

async function updateRating(next: number | null) {
  await store.update(props.item.id, { rating: next })
}

async function changeStatus(next: ReadingStatus) {
  // 切 status 不影響其他欄位(進度、評分原封不動)
  await store.update(props.item.id, { status: next })
}

function askDelete() {
  confirmDeleteOpen.value = true
}

async function confirmDelete() {
  confirmDeleteOpen.value = false
  await store.remove(props.item.id)
}
</script>

<template>
  <div
    class="group relative rounded-lg border border-neutral-200 bg-white px-5 py-4 transition-opacity"
    :class="{ 'opacity-75 hover:opacity-100': isDropped }"
  >
    <!-- 標題列 + badge + actions -->
    <div class="mb-3 flex items-start justify-between gap-2">
      <p class="m-0 text-[15px] font-medium leading-tight text-neutral-900">
        {{ item.title }}
      </p>
      <div class="flex items-center gap-1">
        <CategoryBadge :category="item.category" />
        <StatusBadge :status="item.status" />
        <MangaCardActions
          :current-status="item.status"
          @change-status="changeStatus"
          @delete="askDelete"
        />
      </div>
    </div>

    <!-- 中段:待看不顯示;其他狀態顯示卷/話,已追完才顯示評分 -->
    <template v-if="!isPlanToRead">
      <div class="mb-2.5 flex min-h-[56px] flex-col gap-1.5">
        <div class="flex items-center gap-4 text-[13px]">
          <div class="flex items-center gap-2">
            <span class="text-neutral-500">卷</span>
            <MangaCardEditableNumber :value="item.currentVolume" label="卷" @update="updateVolume" />
          </div>
          <div class="flex items-center gap-2">
            <span class="text-neutral-500">話</span>
            <MangaCardEditableNumber
              :value="item.currentChapter"
              label="話"
              @update="updateChapter"
            />
          </div>
        </div>
        <div v-if="isCompleted" class="flex items-center gap-2">
          <span class="text-xs text-neutral-500">評分</span>
          <MangaCardRating :rating="item.rating" @update="updateRating" />
        </div>
      </div>
    </template>

    <!-- 底部 -->
    <div class="border-t border-neutral-200 pt-2.5">
      <span class="text-xs text-neutral-500">{{ relativeTime }}</span>
    </div>

    <ConfirmDialog
      :open="confirmDeleteOpen"
      title="刪除確認"
      :message="`確定刪除《${item.title}》?`"
      confirm-label="刪除"
      variant="danger"
      @confirm="confirmDelete"
      @cancel="confirmDeleteOpen = false"
    />
  </div>
</template>
