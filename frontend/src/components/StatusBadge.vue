<script setup lang="ts">
import { computed } from 'vue'
import type { ReadingStatus } from '@/types/manga'
import { STATUS_LABELS } from '@/constants/manga'

const props = defineProps<{
  status: ReadingStatus
}>()

const STATUS_CLASS: Record<ReadingStatus, string> = {
  plan_to_read: 'bg-neutral-100 text-neutral-600',
  reading: 'bg-blue-50 text-blue-700',
  dropped: 'bg-red-50 text-red-700',
  completed: 'bg-green-50 text-green-700',
}

const label = computed(() => STATUS_LABELS[props.status])
const klass = computed(() => STATUS_CLASS[props.status])
</script>

<template>
  <span
    :class="klass"
    class="inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-medium"
  >
    {{ label }}
  </span>
</template>
