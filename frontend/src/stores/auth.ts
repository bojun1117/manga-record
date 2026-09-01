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
    // localStorage 不能用(隱私瀏覽 / 配額爆) → 退回記憶體
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(readStoredToken())
  const username = ref<string | null>(null)

  const isAuthenticated = computed(() => token.value !== null)

  async function register(usernameInput: string, password: string): Promise<void> {
    await registerApi(usernameInput, password)
    // 註冊 endpoint 不回 token(見 API.md §5),註冊成功直接幫使用者登入一次,不用再手動填一次密碼
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

  // 給其他 store / API 客戶端用
  function getToken(): string | null {
    return token.value
  }

  // App 啟動時如果本地已經有 token(例如重新整理頁面),打 /auth/me 補回 username,
  // 順便驗證這個 token 是否還有效(過期/被旋轉 secret 都會讓這裡回 401)。
  async function restoreSession(): Promise<void> {
    if (token.value === null) return
    try {
      const me = await meApi(token.value)
      username.value = me.username
    } catch (err) {
      if (err instanceof ApiException && err.isUnauthorized) {
        logout()
      }
      // 其他錯誤(暫時性網路問題等)先不登出,之後操作觸發的 401 會處理
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
