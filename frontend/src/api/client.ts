// 通用 API client。集中處理 base URL、JWT header、JSON、錯誤格式。
// API.md §1.4 的錯誤格式:{ error: { code, message, details } }

// 空字串是合法值：代表同源（dev 走 vite proxy，prod 走反向代理），不是漏設定。
// 只有整個 key 沒定義（undefined）才是真的忘記設。
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

if (import.meta.env.VITE_API_BASE_URL === undefined) {
  console.warn('VITE_API_BASE_URL is not set. Set it in .env.development or .env.local')
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

export class ApiException extends Error {
  status: number
  apiError: ApiError | null

  constructor(status: number, apiError: ApiError | null, message: string) {
    super(message)
    this.name = 'ApiException'
    this.status = status
    this.apiError = apiError
  }

  get code(): string {
    return this.apiError?.code ?? 'UNKNOWN_ERROR'
  }

  get isUnauthorized(): boolean {
    return this.status === 401
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  token?: string | null
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, token } = options

  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers['Authorization'] = `Bearer ${token}`

  const url = `${BASE_URL.replace(/\/$/, '')}${path}`

  let response: Response
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch (err) {
    throw new ApiException(0, null, `Network error: ${(err as Error).message}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  let data: unknown
  try {
    data = await response.json()
  } catch {
    if (!response.ok) {
      throw new ApiException(response.status, null, `HTTP ${response.status}`)
    }
    data = null
  }

  if (!response.ok) {
    const apiError = (data as { error?: ApiError })?.error ?? null
    const message = apiError?.message ?? `HTTP ${response.status}`
    throw new ApiException(response.status, apiError, message)
  }

  return data as T
}
