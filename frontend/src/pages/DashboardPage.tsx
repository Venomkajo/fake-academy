// Home page (route "/"). PLACEHOLDER — replace with the real dashboard
// (announcements, latest grades, upcoming lessons, ...) when ready.
import { ROLE_LABELS, type UserPublic } from '../api/auth'

interface Props {
  user: UserPublic
}

export default function DashboardPage({ user }: Props) {
  return (
    <section>
      <h1>Witaj, {user.first_name}! 👋</h1>
      <p>
        Zalogowany jako <strong>{user.email}</strong> (rola: {ROLE_LABELS[user.role]}).
      </p>
      <p className="muted">
        Placeholder.
      </p>
    </section>
  )
}
