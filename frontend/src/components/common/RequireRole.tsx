// Route-level RBAC gate for role-specific subtrees (the /admin/* pages).
//
// App.tsx mounts this as a pathless wrapper route around the subtree; the
// wrapper reads the logged-in user from props (App owns it via ['me']) and
// either renders the subtree's <Outlet/> or an explicit "no access" note.
// Without it a wrong-role visitor would land on the page itself and watch
// its queries fail with raw 403s from the API — this way they get a plain
// Polish explanation inside the normal Layout instead.
import { Outlet } from 'react-router-dom'

import { ROLE_LABELS, type Role, type UserPublic } from '../../api/auth'

interface Props {
  /** Roles allowed into the subtree; everyone else sees the 403 note. */
  roles: readonly Role[]
  /** The logged-in user (App.tsx owns it via the ['me'] query). */
  user: UserPublic
}

export default function RequireRole({ roles, user }: Props) {
  if (!roles.includes(user.role)) {
    const allowed = roles.map((role) => ROLE_LABELS[role]).join(' lub ')
    return (
      <section>
        <h1>Brak dostępu</h1>
        <p>
          Ta sekcja jest przeznaczona dla roli: <strong>{allowed}</strong>.
        </p>
      </section>
    )
  }
  return <Outlet />
}