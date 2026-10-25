// Root component: auth gate + the routed app shell.
//
//   booting ──token?──▶ /auth/me ──ok──▶ logged in (Layout + routes)
//     │ no                   └─401─▶ clear token ─▶ login form
//     └───────────────────────────────────────────▶ login form
//
// After login the URL decides what renders inside the shared Layout.
// <Routes> is only reachable when `user` is set, so every route below
// is implicitly protected — you cannot deep-link into the app logged
// out. If individual guards are ever needed, move the gate into a
// <RequireAuth> wrapper route instead of relying on this single check.

import { useEffect, useState } from 'react'
import { Route, Routes } from 'react-router-dom'

import { clearToken, fetchCurrentUser, hasToken, type UserPublic } from './api/auth'
import Layout from './components/layout/Layout'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import PlaceholderPage from './pages/PlaceholderPage'

export default function App() {
  const [user, setUser] = useState<UserPublic | null>(null)
  const [booting, setBooting] = useState(true)

  // useEffect with [] deps = run ONCE after the first render.
  useEffect(() => {
    if (!hasToken()) {
      setBooting(false)
      return
    }
    fetchCurrentUser()
      .then(setUser)
      // Token expired/invalid/deactivated account -> wipe it and fall
      // back to the login form.
      .catch(() => clearToken())
      // Regardless of success or failure, we're done booting and can render
      .finally(() => setBooting(false))
  }, [])

  function handleLogout() {
    clearToken()
    setUser(null)
  }

  if (booting) {
    return <p className="muted" style={{ padding: '2rem' }}>Wczytywanie…</p>
  }

  if (!user) {
    return <LoginPage onLoggedIn={setUser} />
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

        {/* Nothing matched the URL -> 404 instead of a blank page. */}
        <Route path="*" element={<PlaceholderPage title="404 — nie znaleziono strony" />} />
      </Route>
    </Routes>
  )
}

