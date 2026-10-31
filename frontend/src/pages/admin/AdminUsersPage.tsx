// Admin users screen (route "/admin/users", README card A1): the account
// list with inline editing, rendered by the same generic EntitySection
// the structure panel uses. Roles and the active flag become selects
// ('ref' fields over fixed options); saving is PUT /admin/users/{id} via
// a useMutation invalidating the ['admin_users'] cache. Account creation
// has no endpoint yet, so the form only appears while editing a row.
import { useQuery } from '@tanstack/react-query'

import { fetchAllUsers, updateUser } from '../../api/admin'
import { apiErrorMessage, type Role } from '../../api/auth'

import EntitySection, { type EntityFieldDef } from '../../components/admin/EntitySection'

/** Fixed options of the role column/select. */
const ROLE_OPTIONS = [
  { value: 'student', label: 'Student' },
  { value: 'teacher', label: 'Nauczyciel' },
  { value: 'admin', label: 'Administrator' },
]

/** Fixed options of the active-flag column/select. */
const ACTIVE_OPTIONS = [
  { value: 'true', label: 'Aktywny' },
  { value: 'false', label: 'Dezaktywowany' },
]

export default function AdminUsersPage() {
  const usersQuery = useQuery({
    queryKey: ['admin_users'],
    queryFn: fetchAllUsers,
  })

  // Adapt UserPublic rows for the generic table: the is_active boolean
  // becomes the string ('true'/'false') its select deals in.
  const rows = (usersQuery.data ?? []).map((user) => ({
    id: user.id,
    first_name: user.first_name,
    last_name: user.last_name,
    email: user.email,
    role: user.role,
    is_active: user.is_active ? 'true' : 'false',
  }))

  const fields: readonly EntityFieldDef[] = [
    { key: 'first_name', label: 'Imię', kind: 'text' },
    { key: 'last_name', label: 'Nazwisko', kind: 'text' },
    { key: 'email', label: 'Email', kind: 'text' },
    { key: 'role', label: 'Rola', kind: 'ref', options: ROLE_OPTIONS },
    { key: 'is_active', label: 'Status', kind: 'ref', options: ACTIVE_OPTIONS },
  ]

  if (usersQuery.isLoading) {
    return <p className="muted">Ładowanie…</p>
  }
  if (usersQuery.isError) {
    return (
      <p role="alert" style={{ color: 'var(--color-danger)' }}>
        {apiErrorMessage(usersQuery.error)}
      </p>
    )
  }

  return (
    <section>
      <h1>Lista użytkowników</h1>
      <p className="muted">{rows.length} użytkowników</p>
      <EntitySection
        title="Konta"
        fields={fields}
        rows={rows}
        cacheKey={['admin_users']}
        update={(id, v) =>
          updateUser(id, {
            id,
            first_name: v.first_name.trim(),
            last_name: v.last_name.trim(),
            email: v.email.trim(),
            role: v.role as Role,
            is_active: v.is_active === 'true',
          })
        }
      />
    </section>
  )
}
