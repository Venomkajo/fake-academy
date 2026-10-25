import { isAxiosError } from 'axios'

import { api, TOKEN_KEY } from './client'

/** Account roles; mirror of the backend's UserRole enum (RBAC lives in app/deps.py). */
export type Role = 'student' | 'teacher' | 'admin'

/** User as the API returns it (/auth/me, /admin/users) — no password hash, ever. */
export interface UserPublic {
  id: number
  email: string
  first_name: string
  last_name: string
  role: Role
  is_active: boolean
}

/** Response body of POST /auth/login. */
export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

// --- token storage -------------------------------------------------------

/** Is an access token saved in localStorage? */
export function hasToken(): boolean {
  return localStorage.getItem(TOKEN_KEY) !== null
}

/** Forget the saved access token (logout). */
export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

// --- API calls -----------------------------------------------------------

/** POST /auth/login; on success stores the token and returns it. */
export async function login(email: string, password: string): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/auth/login', {
    email,
    password,
  })
  localStorage.setItem(TOKEN_KEY, response.data.access_token)
  return response.data
}

/** GET /auth/me — turns the stored token back into fresh user data. */
export async function fetchCurrentUser(): Promise<UserPublic> {
  const response = await api.get<UserPublic>('/auth/me')
  return response.data
}

// --- error translation ---------------------------------------------------

/** Translate any thrown error into a user-safe Polish message. */
export function apiErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const detail: unknown = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail.map((d) => (d as { msg?: string }).msg ?? '').join('; ')
    }
    return `Brak połączenia z serwerem (${error.message})`
  }
  return 'Nieoczekiwany błąd'
}
