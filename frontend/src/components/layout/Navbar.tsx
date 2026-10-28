// Main navigation bar.
//
// NavLink (not <a>!) — it compares its `to` against the current URL and
// adds the .active class automatically, so the open page is highlighted
// with zero JavaScript on our side. Navigation is client-side: no full
// page reload.
import { NavLink } from 'react-router-dom'

import type { Role, UserPublic } from '../../api/auth'

/** One bar entry; `roles` restricts who sees it (omit = everyone). */
interface NavItem {
  to: string
  label: string
  roles?: readonly Role[]
}

// Single source of truth for the bar: add/remove items HERE,
// then create the matching route in App.tsx and page in src/pages/.
//
// `roles` mirrors the backend RBAC (Role in api/auth.ts): students and
// teachers use the learning views (README S*/W* cards), the admin uses
// the management views (README A1–A4) — an admin has no grades or
// messages of their own, so those links stay hidden.
const LINKS: readonly NavItem[] = [
  { to: '/', label: 'Pulpit' },
  { to: '/grades', label: 'Oceny', roles: ['student', 'teacher'] },
  { to: '/schedule', label: 'Plan zajęć', roles: ['student', 'teacher'] },
  { to: '/messages', label: 'Wiadomości', roles: ['student', 'teacher'] },
  { to: '/materials', label: 'Materiały', roles: ['student', 'teacher'] },
  { to: '/admin/users', label: 'Użytkownicy', roles: ['admin'] },
  { to: '/admin/structure', label: 'Struktura uczelni', roles: ['admin'] },
  { to: '/admin/schedule', label: 'Edytor planu', roles: ['admin'] },
  { to: '/admin/statistics', label: 'Statystyki', roles: ['admin'] },
]

// Presentational like Header: ALL data arrives via props (`user`) — it
// owns no state and calls no API itself, it just filters LINKS by role.
interface Props {
  user: UserPublic
}

export default function Navbar({ user }: Props) {
  // A link without `roles` is role-agnostic (everyone); otherwise the
  // logged-in user's role must be listed to see it.
  const links = LINKS.filter((l) => !l.roles || l.roles.includes(user.role))

  return (
    <nav className="app-nav" aria-label="Nawigacja główna">
      <div className="container nav-inner">
        {links.map(({ to, label }) => (
          <NavLink key={to} to={to} end={to === '/'} className="nav-link">
            {label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
