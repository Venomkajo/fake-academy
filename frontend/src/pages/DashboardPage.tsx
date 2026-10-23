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
        To jest placeholder strony głównej — zastąp go prawdziwym pulpitem.
        Użyj nawigacji powyżej, aby zobaczyć kolejne podstrony.
      </p>
    </section>
  )
}
