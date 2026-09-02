import { apiRequest } from './client'

interface RegisterResponse {
  id: number
  username: string
}

interface LoginResponse {
  token: string
}

interface MeResponse {
  id: number
  username: string
  isAdmin: boolean
}

export function registerApi(username: string, password: string): Promise<RegisterResponse> {
  return apiRequest<RegisterResponse>('/auth/register', {
    method: 'POST',
    body: { username, password },
  })
}

export function loginApi(username: string, password: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>('/auth/login', {
    method: 'POST',
    body: { username, password },
  })
}

export function meApi(token: string): Promise<MeResponse> {
  return apiRequest<MeResponse>('/auth/me', { token })
}
