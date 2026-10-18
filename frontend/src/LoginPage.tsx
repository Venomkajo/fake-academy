import { useState } from 'react'

import { apiErrorMessage, fetchCurrentUser, login, type UserPublic } from './auth'

// Props: the ONLY way a parent (App) passes data/callbacks down.
// We don't store the user here — after success we HAND IT UP.
interface Props {
  onLoggedIn: (user: UserPublic) => void
}

export default function LoginPage({ onLoggedIn }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await login(email, password)
      const user = await fetchCurrentUser()
      onLoggedIn(user)
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main style={{ fontFamily: 'sans-serif', padding: '2rem', maxWidth: 480 }}>
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
            style={{ display: 'block', width: '100%', padding: '0.5rem', boxSizing: 'border-box' }}
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
            style={{ display: 'block', width: '100%', padding: '0.5rem', boxSizing: 'border-box' }}
          />
        </label>

        <button type="submit" disabled={busy} style={{ padding: '0.5rem 1.25rem' }}>
          {busy ? 'Logowanie…' : 'Zaloguj się'}
        </button>

        {/* role="alert" -> screen readers announce the error */}
        {error && (
          <p role="alert" style={{ color: 'crimson' }}>
            {error}
          </p>
        )}
      </form>

      <p style={{ color: '#666', fontSize: '0.85rem', marginTop: '2rem' }}>
        Konta deweloperskie: admin@fake.academy / admin123!, anna@fake.academy / teacher123!,
        kasia@fake.academy / student123!
      </p>
    </main>
  )
}
