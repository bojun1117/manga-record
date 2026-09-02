<script setup lang="ts">
import { ref } from 'vue'
import type { CollectionItem } from '@/types/manga'
import { useAuthStore } from '@/stores/auth'
import { queryAssistantApi } from '@/api/assistant'
import { ApiException } from '@/api/client'
import MangaCard from '@/components/MangaCard.vue'

const emit = defineEmits<{
  changed: []
}>()

const auth = useAuthStore()

const question = ref('')
const asking = ref(false)
const answer = ref<string | null>(null)
const items = ref<CollectionItem[]>([])
const errorMsg = ref<string | null>(null)

const EXAMPLES = ['我評分最高的 10 部漫畫', '找我還沒看完的漫畫', '我棄坑最多的分類是什麼']

async function ask() {
  const token = auth.getToken()
  const trimmed = question.value.trim()
  if (!token || !trimmed || asking.value) return

  asking.value = true
  errorMsg.value = null
  try {
    const res = await queryAssistantApi(trimmed, token)
    answer.value = res.answer
    items.value = res.items
  } catch (err) {
    answer.value = null
    items.value = []
    if (err instanceof ApiException && err.code === 'ASSISTANT_UNAVAILABLE') {
      errorMsg.value = 'AI 助理暫時無法回應，請稍後再試。'
    } else if (err instanceof ApiException) {
      errorMsg.value = err.message
    } else {
      errorMsg.value = '發生未預期的錯誤。'
    }
  } finally {
    asking.value = false
  }
}

function useExample(example: string) {
  question.value = example
  ask()
}

function onCardChanged() {
  emit('changed')
}
</script>

<template>
  <section class="mt-8 border-t border-neutral-200 pt-5">
    <h2 class="mb-3 text-lg font-semibold text-neutral-800">AI 助理</h2>

    <form class="flex gap-2" @submit.prevent="ask">
      <input
        v-model="question"
        type="text"
        placeholder="例如：我評分最高的 10 部漫畫"
        class="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
      />
      <button
        type="submit"
        class="flex-shrink-0 rounded-md bg-neutral-900 px-4 py-2 text-[13px] font-medium text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="asking || question.trim() === ''"
      >
        {{ asking ? '思考中…' : '送出' }}
      </button>
    </form>

    <div v-if="!answer && !asking && !errorMsg" class="mt-2 flex flex-wrap gap-2">
      <button
        v-for="example in EXAMPLES"
        :key="example"
        type="button"
        class="rounded-full border border-neutral-200 bg-white px-3 py-1 text-[12px] text-neutral-500 transition hover:bg-neutral-50"
        @click="useExample(example)"
      >
        {{ example }}
      </button>
    </div>

    <p v-if="errorMsg" class="mt-3 text-sm text-red-600">{{ errorMsg }}</p>

    <div v-if="answer" class="mt-4">
      <p class="text-sm text-neutral-700">💬 {{ answer }}</p>

      <div
        v-if="items.length > 0"
        class="mt-3 grid gap-3"
        style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))"
      >
        <MangaCard v-for="item in items" :key="item.id" :item="item" @changed="onCardChanged" />
      </div>
    </div>
  </section>
</template>
