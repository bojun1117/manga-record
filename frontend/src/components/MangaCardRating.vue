<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  rating: number | null
}>()

const emit = defineEmits<{
  update: [rating: number | null]
}>()

const expanded = ref(false)
const hoverValue = ref<number | null>(null)

function pick(n: number) {
  if (props.rating === n) {
    emit('update', null)
  } else {
    emit('update', n)
  }
  expanded.value = false
  hoverValue.value = null
}

function expand() {
  expanded.value = true
}

function shouldFill(n: number): boolean {
  if (hoverValue.value !== null) return n <= hoverValue.value
  if (props.rating !== null) return n <= props.rating
  return false
}
</script>

<template>
  <div
    v-if="rating !== null"
    class="flex items-center gap-0.5 text-lg tracking-[2px]"
    @mouseleave="hoverValue = null"
  >
    <button
      v-for="n in 5"
      :key="n"
      type="button"
      class="cursor-pointer leading-none transition-transform hover:scale-110"
      :class="shouldFill(n) ? 'text-amber-500' : 'text-neutral-300'"
      :title="rating === n ? '再次點擊清除評分' : `評為 ${n} 顆星`"
      @mouseenter="hoverValue = n"
      @click="pick(n)"
    >
      {{ shouldFill(n) ? '★' : '☆' }}
    </button>
  </div>

  <div
    v-else-if="expanded"
    class="flex items-center gap-0.5 text-lg tracking-[2px]"
    @mouseleave="hoverValue = null"
  >
    <button
      v-for="n in 5"
      :key="n"
      type="button"
      class="cursor-pointer leading-none transition-transform hover:scale-110"
      :class="hoverValue !== null && n <= hoverValue ? 'text-amber-500' : 'text-neutral-300'"
      :title="`評為 ${n} 顆星`"
      @mouseenter="hoverValue = n"
      @click="pick(n)"
    >
      {{ hoverValue !== null && n <= hoverValue ? '★' : '☆' }}
    </button>
  </div>

  <button
    v-else
    type="button"
    class="cursor-pointer text-[13px] text-neutral-400 underline decoration-dotted hover:text-neutral-600"
    @click="expand"
  >
    點此評分
  </button>
</template>
