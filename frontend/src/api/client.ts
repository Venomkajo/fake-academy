// Shared Axios instance every module talks to the backend through, plus
// the localStorage key the auth flow stores the JWT under. Two
// interceptors: the request one attaches the token to every outgoing
// request; the response one watches for 401s — an expired/invalid token
// means the session is dead, so it drops the token and force-reloads the
// app instead of letting every page fill up with 401 error messages.
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

// Response interceptor: the expired-session guard.
//
// A 401 on a request that CARRIED our token = the token expired or is
// invalid — the session is over. Rather than surfacing "Token has
// expired" errors on every open page, clear the token and hard-reload
// to "/": the fresh boot finds no token and shows the login form (the
// same rule the logout button follows in App.tsx). A 401 on a request
// WITHOUT a token — i.e. POST /auth/login with bad credentials — is a
// normal form error and must NOT reload, or the login form would eat
// its own error message.
//
// The flag keeps parallel 401 failures (several queries in flight when
// the token dies) from triggering more than one reload.
let handlingExpiredSession = false

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const sentOurToken = Boolean(error.config?.headers?.Authorization)
    if (error.response?.status === 401 && sentOurToken && !handlingExpiredSession) {
      handlingExpiredSession = true
      localStorage.removeItem(TOKEN_KEY)
      window.location.assign('/')
    }
    return Promise.reject(error)
  },
)
