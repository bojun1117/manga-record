import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { loginApi, meApi, registerApi } from '@/api/auth'
import { ApiException } from '@/api/client'

const TOKEN_STORAGE_KEY = 'manga-record.token'

function readStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

function writeStoredToken(token: string | null): void {
  try {
    if (token === null) {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
    } else {
      localStorage.setItem(TOKEN_STORAGE_KEY, token)
    }
  } catch {
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(readStoredToken())
  const username = ref<string | null>(null)

  const isAuthenticated = computed(() => token.value !== null)

  async function register(usernameInput: string, password: string): Promise<void> {
    await registerApi(usernameInput, password)
    await login(usernameInput, password)
  }

  async function login(usernameInput: string, password: string): Promise<void> {
    const res = await loginApi(usernameInput, password)
    token.value = res.token
    writeStoredToken(res.token)
    username.value = usernameInput
  }

  function logout(): void {
    token.value = null
    username.value = null
    writeStoredToken(null)
  }

  function getToken(): string | null {
    return token.value
  }

  async function restoreSession(): Promise<void> {
    if (token.value === null) return
    try {
      const me = await meApi(token.value)
      username.value = me.username
    } catch (err) {
      if (err instanceof ApiException && err.isUnauthorized) {
        logout()
      }
    }
  }

  return {
    token,
    username,
    isAuthenticated,
    register,
    login,
    logout,
    getToken,
    restoreSession,
  }
})
