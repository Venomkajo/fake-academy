// The login screen — shown whenever the user is not authenticated.
//
// The whole login round-trip is a useMutation (TanStack Query's tool
// for commands that change server state): it exposes the isPending/
// error flags we used to store by hand in useState, and hands the
// fetched user UP to App in onSuccess. The page still owns only the
// two controlled form fields; no session state lives here.
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { apiErrorMessage, fetchCurrentUser, login, type UserPublic } from '../api/auth'

// Props: the ONLY way a parent (App) passes data/callbacks down.
interface Props {
  onLoggedIn: (user: UserPublic) => void
}

export default function LoginPage({ onLoggedIn }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  // Login is a COMMAND (POST /auth/login), not cacheable server state,
  // so a mutation, not a query. One async action covers both steps of
  // the round-trip: POST /auth/login (api/auth.ts stores the returned
  // token in localStorage), then GET /auth/me for the fresh user data.
  const loginMutation = useMutation({
    mutationFn: async (): Promise<UserPublic> => {
      await login(email, password)
      return fetchCurrentUser()
    },
    onSuccess: (user) => onLoggedIn(user),
  })

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    loginMutation.mutate()
  }

  // Derived, not stored: the mutation tracks busy/error, so
  // the render just reads them (v5 names the flag `isPending`).
  const busy = loginMutation.isPending
  const error = loginMutation.isError ? apiErrorMessage(loginMutation.error) : null

  return (
    <main className="app-main">
      <section className="card" style={{ maxWidth: 480 }}>
        <h1>Fake Academy</h1>
        <h2>Zaloguj się</h2>

        <form onSubmit={handleSubmit}>
          <label style={{ display: 'block', marginBottom: '0.75rem' }}>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              required
              style={{ display: 'block', width: '100%', padding: '0.5rem' }}
            />
          </label>

          <label style={{ display: 'block', marginBottom: '1rem' }}>
            Hasło
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              style={{ display: 'block', width: '100%', padding: '0.5rem' }}
            />
          </label>

          <button type="submit" className="btn" disabled={busy}>
            {busy ? 'Logowanie…' : 'Zaloguj się'}
          </button>

          {/* role="alert" -> screen readers announce the error */}
          {error && (
            <p role="alert" style={{ color: 'var(--color-danger)' }}>
              {error}
            </p>
          )}
        </form>

        <p className="muted" style={{ fontSize: '0.85rem', marginTop: '2rem' }}>
          Konta deweloperskie: admin@fake.academy / admin123!, anna@fake.academy / teacher123!,
          kasia@fake.academy / student123!
        </p>
      </section>
    </main>
  )
}
