// Top bar: brand on the left, logged-in user + logout on the right.
//
// Presentational component: ALL data arrives via props (`user`,
// `onLogout`) — it owns no state and calls no API itself.
// Styling comes from global.css (.app-header, .brand, .user-chip).
import type { UserPublic } from '../../api/auth'

interface Props {
  user: UserPublic
  onLogout: () => void
}

export default function Header({ user, onLogout }: Props) {
  return (
    <header className="app-header">
      <div className="container app-header-inner">
        {/* TODO: swap the emoji for a logo/SVG when you have one. */}
        <span className="brand">🎓 Fake Academy</span>

        <div className="user-chip">
          {/* title = full email on hover, keeps the bar compact */}
          <span title={user.email}>
            {user.first_name} {user.last_name} · {user.role}
          </span>
          <button type="button" className="btn btn-ghost" onClick={onLogout}>
            Wyloguj się
          </button>
        </div>
      </div>
    </header>
  )
}
