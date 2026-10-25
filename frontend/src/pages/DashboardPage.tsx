import type { UserPublic } from '../api/auth'

// Home page (route "/"). PLACEHOLDER — replace with the real dashboard
// (announcements, latest grades, upcoming lessons, ...) when ready.
interface Props {
  user: UserPublic
}

export default function DashboardPage({ user }: Props) {
  return (
    <section>
      <h1>Witaj, {user.first_name}! 👋</h1>
      <p>
        Zalogowany jako <strong>{user.email}</strong> (rola: {user.role}).
      </p>
      <p className="muted">
        Placeholder.
      </p>
    </section>
  )
}
