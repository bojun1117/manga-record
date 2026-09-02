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
const isPlanToRead = computed(() => props.item.status === 'plan_to_read')
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
    class="group relative flex flex-col rounded-lg border border-neutral-200 bg-white px-5 py-4 transition-opacity"
    :class="{ 'opacity-75 hover:opacity-100': isDropped }"
  >
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

    <div class="mt-auto border-t border-neutral-200 pt-2.5">
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
