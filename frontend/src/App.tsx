// Root component: a tiny three-state machine.
//
//   booting ──token?──▶ /auth/me ──ok──▶ logged in
//     │ no                   └─401─▶ clear token ─▶ login form
//     └───────────────────────────────────────────▶ login form

import { useEffect, useState } from 'react'

import LoginPage from './LoginPage'
import { clearToken, fetchCurrentUser, hasToken, type UserPublic } from './auth'

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
      // back to the login form. apiErrorMessage would tell us which,
      // but for the boot path the user action is the same either way.
      .catch(() => clearToken())
      .finally(() => setBooting(false))
  }, [])

  if (booting) {
    return <p style={{ fontFamily: 'sans-serif', padding: '2rem' }}>Wczytywanie…</p>
  }

  if (!user) {
    return <LoginPage onLoggedIn={setUser} />
  }

  return (
    <main style={{ fontFamily: 'sans-serif', padding: '2rem', maxWidth: 640 }}>
      <h1>Witaj, {user.first_name}! 👋</h1>
      <p>
        Zalogowany jako <strong>{user.email}</strong> (rola: {user.role}).
      </p>
      <button onClick={() => { clearToken(); setUser(null) }}>
        Wyloguj się
      </button>
    </main>
  )
}
