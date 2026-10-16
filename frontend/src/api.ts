// The ONE Axios instance every feature of the app will reuse.
// Central configuration means: base URL set once, auth attached once,
// 401-handling added once (later) — no per-component setup.

import axios from 'axios'

// Where the browser reaches the backend. This is the HOST port
// published in docker-compose.yml (8001), because the browser lives
// OUTSIDE the compose network and cannot see service names like
// "backend". Later this can become an env var (import.meta.env.VITE_*)
// if environments differ.
export const API_BASE_URL = 'http://localhost:8001'

export const api = axios.create({
  baseURL: API_BASE_URL,
})

// Request interceptor: runs before EVERY request sent through `api`.
// If a JWT sits in localStorage (put there by a future login page),
// attach it as Authorization: Bearer <token> — exactly the header
// get_current_user on the backend expects.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('fa_access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
