// Shared Axios instance every module talks to the backend through, plus
// the localStorage key the auth flow stores the JWT under. The request
// interceptor below attaches the token to every outgoing request.
import axios from 'axios'


// Where the browser reaches the backend. Set VITE_FASTAPI_BASE_URL in
// frontend/.env — Vite only exposes variables prefixed with VITE_ to
// the client (import.meta.env). Defaults to localhost:8001
export const API_BASE_URL = import.meta.env.VITE_FASTAPI_BASE_URL ?? 'http://localhost:8001'

export const TOKEN_KEY = 'fa_access_token'

export const api = axios.create({
  baseURL: API_BASE_URL,
})

// Request interceptor: runs before EVERY request sent through `api`.
// If a JWT sits in localStorage (put there by the login flow in
// auth.ts), attach it as Authorization: Bearer <token> — exactly the
// header get_current_user on the backend expects.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
