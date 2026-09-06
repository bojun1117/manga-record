<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { parseNonNegativeInt } from '@/utils/number'

const props = defineProps<{
  value: number | null
  label: '卷' | '話'
}>()

const emit = defineEmits<{
  update: [value: number | null]
}>()

const editing = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
const draft = ref<string | number>('')
const optimisticValue = ref<number | null>(null)
const useOptimistic = ref(false)
let optimisticTimer: number | null = null

function clearOptimisticTimer() {
  if (optimisticTimer !== null) {
    window.clearTimeout(optimisticTimer)
    optimisticTimer = null
  }
}

// Drop the optimistic value once the real (server-confirmed) value catches up,
// instead of clearing it after a single tick — the update + list refresh can
// easily take longer than that, which was causing the UI to flash back to the
// old number and stay there until a manual page refresh.
watch(
  () => props.value,
  (v) => {
    if (useOptimistic.value && v === optimisticValue.value) {
      useOptimistic.value = false
      clearOptimisticTimer()
    }
  },
)

function displayValue(): number | null {
  return useOptimistic.value ? optimisticValue.value : props.value
}

async function startEdit() {
  draft.value = props.value === null ? '' : String(props.value)
  editing.value = true
  await nextTick()
  inputRef.value?.focus()
  inputRef.value?.select()
}

function cancel() {
  editing.value = false
  draft.value = ''
}

function commit() {
  if (!editing.value) return

  const next = parseNonNegativeInt(draft.value)
  if (next === undefined) {
    cancel()
    return
  }

  if (next === props.value) {
    cancel()
    return
  }

  optimisticValue.value = next
  useOptimistic.value = true
  editing.value = false

  emit('update', next)

  // Safety net: if the update never comes back (e.g. it failed), fall back to
  // showing the real value instead of the optimistic one forever.
  clearOptimisticTimer()
  optimisticTimer = window.setTimeout(() => {
    useOptimistic.value = false
  }, 8000)
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    commit()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    cancel()
  }
}
</script>

<template>
  <span v-if="editing">
    <input
      ref="inputRef"
      v-model="draft"
      type="number"
      inputmode="numeric"
      min="0"
      class="h-7 w-16 rounded border border-blue-400 bg-white px-1.5 text-[13px] font-medium text-neutral-900 outline-none focus:ring-2 focus:ring-blue-200"
      @keydown="onKeydown"
      @blur="commit"
    />
  </span>
  <span
    v-else-if="displayValue() !== null"
    class="cursor-text rounded bg-neutral-100 px-1.5 py-0.5 font-medium text-neutral-900 hover:bg-neutral-200"
    :title="`點擊編輯${label}`"
    @click="startEdit"
  >
    {{ displayValue() }}
  </span>
  <span
    v-else
    class="cursor-text px-1.5 py-0.5 text-neutral-400 hover:text-neutral-600"
    :title="`點擊填入${label}`"
    @click="startEdit"
  >
    —
  </span>
</template>
