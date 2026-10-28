// Root component: auth gate + the routed app shell.
//
//   booting ──token?──▶ GET /auth/me (useQuery) ──ok──▶ logged in (Layout + routes)
//     │ no                      └─error─▶ clear token ─▶ login form
//     └──────────────────────────────────────────▶ login form
//
// The logged-in user is CACHED SERVER STATE (TanStack Query, key
// ['me']): the boot fetch is the query's initial load, login writes
// the fresh user into that cache, logout clears the whole cache —
// there is no duplicate user state in useState to keep in sync.
//
// After login the URL decides what renders inside the shared Layout.
// <Routes> is only reachable when `user` is set, so every route below
// is implicitly protected — you cannot deep-link into the app logged
// out. If individual guards are ever needed, move the gate into a
// <RequireAuth> wrapper route instead of relying on this single check.

import { useEffect } from 'react'
import { Route, Routes } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { clearToken, fetchCurrentUser, hasToken, type UserPublic } from './api/auth'
import Layout from './components/layout/Layout'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import PlaceholderPage from './pages/PlaceholderPage'

/** Cache key of the logged-in user's data (GET /auth/me). */
const ME_KEY = ['me'] as const

export default function App() {
  const queryClient = useQueryClient()

  // The boot-time /auth/me fetch as a query: one cached round-trip the
  // app can read anywhere via the same key.
  const meQuery = useQuery({
    queryKey: ME_KEY,
    queryFn: fetchCurrentUser,
    retry: false,
    enabled: hasToken(),
  })

  const user = meQuery.data ?? null

  useEffect(() => {
    if (meQuery.isError) clearToken()
  }, [meQuery.isError])

  // "Booting" = a token exists AND its /auth/me fetch is still in
  // flight. A disabled (logged-out) query is also status "pending",
  // but its fetchStatus is "idle" — that case means: show the login.
  const booting = meQuery.isPending && meQuery.fetchStatus !== 'idle'

  if (booting) {
    return <p className="muted" style={{ padding: '2rem' }}>Wczytywanie…</p>
  }

  if (!user) {
    return <LoginPage onLoggedIn={handleLoggedIn} />
  }

  // Login succeeded: LoginPage already stored the token and fetched the
  // fresh user — park it in the ['me'] cache so the query above (and
  // any other ['me'] reader) sees it without another round-trip.
  function handleLoggedIn(loggedIn: UserPublic) {
    queryClient.setQueryData(ME_KEY, loggedIn)
  }

  // Logout: drop the token and EVERY cached query in one go — one
  // user's data must never leak into the next login's session.
  function handleLogout() {
    clearToken()
    queryClient.clear()
  }

  return (
    <Routes>
      {/* Pathless "layout route": wraps every child below in the shared
          Header + Navbar + Footer shell (see components/layout/Layout.tsx). */}
      <Route element={<Layout user={user} onLogout={handleLogout} />}>
        {/* index = the "/" route (no path of its own) */}
        <Route index element={<DashboardPage user={user} />} />

        {/* Placeholder screens — replaced with real pages one by one.
            URL paths are English/ASCII; page titles stay Polish. */}
        <Route path="grades" element={<PlaceholderPage title="Oceny" />} />
        <Route path="schedule" element={<PlaceholderPage title="Plan zajęć" />} />
        <Route path="messages" element={<PlaceholderPage title="Wiadomości" />} />
        <Route path="materials" element={<PlaceholderPage title="Materiały" />} />

        <Route path="admin/users" element={<PlaceholderPage title="Użytkownicy" />} />
        <Route path="admin/structure" element={<PlaceholderPage title="Struktura uczelni" />} />
        <Route path="admin/schedule" element={<PlaceholderPage title="Edytor planu zajęć" />} />
        <Route path="admin/statistics" element={<PlaceholderPage title="Statystyki systemowe" />} />

        {/* Nothing matched the URL -> 404 instead of a blank page. */}
        <Route path="*" element={<PlaceholderPage title="404 — nie znaleziono strony" />} />
      </Route>
    </Routes>
  )
}

