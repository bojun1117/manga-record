<script setup lang="ts">
import { nextTick, ref } from 'vue'

const props = defineProps<{
  value: number | null
  label: '卷' | '話'
}>()

const emit = defineEmits<{
  update: [value: number | null]
}>()

const editing = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
// v-model 在 type="number" input 上會自動把字串 cast 成 number,所以 draft 可能是 string('') 或 number。
const draft = ref<string | number>('')
// 樂觀更新:UI 立刻反映,失敗時靠這個還原
const optimisticValue = ref<number | null>(null)
const useOptimistic = ref(false)

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

async function commit() {
  if (!editing.value) return

  const trimmed = String(draft.value ?? '').trim()
  let next: number | null

  if (trimmed === '') {
    next = null
  } else {
    const n = Number(trimmed)
    if (!Number.isFinite(n) || n < 0 || !Number.isInteger(n)) {
      cancel()
      return
    }
    next = n
  }

  if (next === props.value) {
    cancel()
    return
  }

  optimisticValue.value = next
  useOptimistic.value = true
  editing.value = false

  try {
    emit('update', next)
  } catch {
    useOptimistic.value = false
  } finally {
    nextTick(() => {
      useOptimistic.value = false
    })
  }
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
