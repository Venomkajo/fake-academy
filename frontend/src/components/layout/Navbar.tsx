// Main navigation bar.
//
// NavLink (not <a>!) — it compares its `to` against the current URL and
// adds the .active class automatically, so the open page is highlighted
// with zero JavaScript on our side. Navigation is client-side: no full
// page reload.
import { NavLink } from 'react-router-dom'

// Single source of truth for the bar: add/remove items HERE,
// then create the matching route in App.tsx and page in src/pages/.
//
// TODO(you): make the list role-aware, e.g.
//   const links = LINKS.filter((l) => !l.roles || l.roles.includes(user.role))
// once Navbar receives the user (add a `user` prop, see Header).
const LINKS = [
  { to: '/', label: 'Pulpit' },
  { to: '/oceny', label: 'Oceny' },
  { to: '/plan', label: 'Plan zajęć' },
  { to: '/wiadomosci', label: 'Wiadomości' },
  { to: '/materialy', label: 'Materiały' },
] as const

export default function Navbar() {
  return (
    <nav className="app-nav" aria-label="Nawigacja główna">
      <div className="container nav-inner">
        {LINKS.map(({ to, label }) => (
          // end={true} on "/" => "Pulpit" is active ONLY on the exact
          // index route, not on every /oceny, /plan, ... URL too.
          <NavLink key={to} to={to} end={to === '/'} className="nav-link">
            {label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
