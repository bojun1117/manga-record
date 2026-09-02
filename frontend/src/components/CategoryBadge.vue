<script setup lang="ts">
import { computed } from 'vue'
import type { MangaCategory } from '@/types/manga'
import { CATEGORY_LABELS } from '@/constants/manga'

const props = defineProps<{
  category: MangaCategory
}>()

const CATEGORY_CLASS: Record<MangaCategory, string> = {
  hot_blooded: 'bg-orange-50 text-orange-700',
  mystery: 'bg-violet-50 text-violet-700',
  adventure: 'bg-emerald-50 text-emerald-700',
  romance: 'bg-pink-50 text-pink-700',
  casual: 'bg-sky-50 text-sky-700',
  competition: 'bg-amber-50 text-amber-700',
  revenge: 'bg-rose-50 text-rose-700',
  slice_of_life: 'bg-teal-50 text-teal-700',
  other: 'bg-neutral-100 text-neutral-600',
}

const label = computed(() => CATEGORY_LABELS[props.category])
const klass = computed(() => CATEGORY_CLASS[props.category])
</script>

<template>
  <span
    :class="klass"
    class="inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-medium"
  >
    {{ label }}
  </span>
</template>
