<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { ApiException } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const submitting = ref(false)
const errorMsg = ref<string | null>(null)

const USERNAME_PATTERN = /^[a-zA-Z0-9_]+$/

const usernameError = computed(() => {
  if (username.value === '') return null
  if (username.value.length < 3 || username.value.length > 30) return '帳號長度需為 3–30 字元'
  if (!USERNAME_PATTERN.test(username.value)) return '帳號只能包含英數字與底線'
  return null
})

const passwordError = computed(() => {
  if (password.value === '') return null
  if (password.value.length < 8) return '密碼至少需要 8 個字元'
  return null
})

const confirmError = computed(() => {
  if (confirmPassword.value === '') return null
  if (confirmPassword.value !== password.value) return '兩次輸入的密碼不一致'
  return null
})

const canSubmit = computed(
  () =>
    username.value !== '' &&
    password.value !== '' &&
    confirmPassword.value !== '' &&
    usernameError.value === null &&
    passwordError.value === null &&
    confirmError.value === null &&
    !submitting.value,
)

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  errorMsg.value = null
  try {
    await auth.register(username.value, password.value)
    router.replace('/')
  } catch (err) {
    if (err instanceof ApiException) {
      if (err.code === 'USERNAME_TAKEN') {
        errorMsg.value = '這個帳號已經被註冊了,換一個試試。'
      } else if (err.code === 'VALIDATION_ERROR') {
        errorMsg.value = '帳號或密碼格式不符合規定。'
      } else {
        errorMsg.value = `註冊失敗:${err.message}`
      }
    } else {
      errorMsg.value = '註冊失敗,請稍後再試。'
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
      <p class="mt-1 text-center text-sm text-neutral-500">建立新帳號</p>

      <div class="mt-6 rounded-lg border border-neutral-200 bg-white p-5 shadow-sm">
        <label for="reg-username" class="block text-[13px] font-medium text-neutral-700">
          帳號
        </label>
        <input
          id="reg-username"
          v-model="username"
          type="text"
          autocomplete="username"
          autofocus
          placeholder="3–30 字元,英數字與底線"
          class="mt-1 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
        />
        <p v-if="usernameError" class="mt-1 text-[12px] text-red-600">{{ usernameError }}</p>

        <label for="reg-password" class="mt-3 block text-[13px] font-medium text-neutral-700">
          密碼
        </label>
        <input
          id="reg-password"
          v-model="password"
          type="password"
          autocomplete="new-password"
          placeholder="至少 8 個字元"
          class="mt-1 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
        />
        <p v-if="passwordError" class="mt-1 text-[12px] text-red-600">{{ passwordError }}</p>

        <label for="reg-confirm" class="mt-3 block text-[13px] font-medium text-neutral-700">
          確認密碼
        </label>
        <input
          id="reg-confirm"
          v-model="confirmPassword"
          type="password"
          autocomplete="new-password"
          class="mt-1 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
          @keydown.enter="submit"
        />
        <p v-if="confirmError" class="mt-1 text-[12px] text-red-600">{{ confirmError }}</p>

        <p v-if="errorMsg" class="mt-2 text-[13px] text-red-600">{{ errorMsg }}</p>

        <button
          type="button"
          class="mt-4 w-full rounded-md bg-neutral-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!canSubmit"
          @click="submit"
        >
          {{ submitting ? '註冊中…' : '註冊' }}
        </button>

        <p class="mt-4 text-center text-[13px] text-neutral-500">
          已經有帳號了?
          <RouterLink to="/login" class="font-medium text-neutral-900 underline">登入</RouterLink>
        </p>
      </div>
    </div>
  </main>
</template>
