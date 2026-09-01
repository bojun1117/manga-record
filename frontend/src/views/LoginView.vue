<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { ApiException } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const submitting = ref(false)
const errorMsg = ref<string | null>(null)

async function submit() {
  if (!username.value || !password.value || submitting.value) return
  submitting.value = true
  errorMsg.value = null
  try {
    await auth.login(username.value, password.value)
    const redirect = (router.currentRoute.value.query.redirect as string) || '/'
    router.replace(redirect)
  } catch (err) {
    if (err instanceof ApiException) {
      errorMsg.value = err.status === 401 ? '帳號或密碼錯誤,請再試一次。' : `登入失敗:${err.message}`
    } else {
      errorMsg.value = '登入失敗,請稍後再試。'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center px-4">
    <div class="w-full max-w-sm">
      <h1 class="text-center text-2xl font-semibold text-neutral-900">Manga Record</h1>
      <p class="mt-1 text-center text-sm text-neutral-500">登入以繼續</p>

      <div class="mt-6 rounded-lg border border-neutral-200 bg-white p-5 shadow-sm">
        <label for="username" class="block text-[13px] font-medium text-neutral-700">
          帳號
        </label>
        <input
          id="username"
          v-model="username"
          type="text"
          autocomplete="username"
          autofocus
          class="mt-1 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
          @keydown.enter="submit"
        />

        <label for="password" class="mt-3 block text-[13px] font-medium text-neutral-700">
          密碼
        </label>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          class="mt-1 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
          @keydown.enter="submit"
        />

        <p v-if="errorMsg" class="mt-2 text-[13px] text-red-600">{{ errorMsg }}</p>

        <button
          type="button"
          class="mt-4 w-full rounded-md bg-neutral-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!username || !password || submitting"
          @click="submit"
        >
          {{ submitting ? '登入中…' : '登入' }}
        </button>

        <p class="mt-4 text-center text-[13px] text-neutral-500">
          還沒有帳號?
          <RouterLink to="/register" class="font-medium text-neutral-900 underline">
            註冊
          </RouterLink>
        </p>
      </div>
    </div>
  </main>
</template>
