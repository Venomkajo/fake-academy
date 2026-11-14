// Admin users screen (route "/admin/users", README card A1): the account
// list with inline editing, rendered by the same generic EntitySection
// the structure panel uses. Roles and the active flag become selects
// ('ref' fields over fixed options); saving is PATCH /admin/users/{id} via
// a useMutation invalidating the ['admin_users'] cache. Account creation
// has no endpoint yet, so the form only appears while editing a row.
// Above the table: a search box (any text fragment) + a role filter; the
// own account row is NOT editable — self-deactivation/self-demotion from
// this list would lock the admin out (README A1's safety requirement).
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { fetchAllUsers, updateUser } from '../../api/admin'
import { ROLE_LABELS, type Role, type UserPublic } from '../../api/auth'

import EntitySection, { type EntityFieldDef } from '../../components/admin/EntitySection'
import { ErrorMessage, QueryStatus } from '../../components/common/QueryStatus'

/**
 * Select options of the role column/select, derived from the shared
 * ROLE_LABELS map (api/auth.ts) — one source of the Polish labels, so no
 * page re-spells them locally. Iteration order = the map's insertion order.
 */
const ROLE_OPTIONS = Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }))

/** Fixed options of the active-flag column/select. */
const ACTIVE_OPTIONS = [
  { value: 'true', label: 'Aktywny' },
  { value: 'false', label: 'Dezaktywowany' },
]

/** Shared look of the search box / role select above the table. */
const inputStyle = {
  display: 'block',
  padding: '0.45rem 0.6rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  font: 'inherit',
} as const

export default function AdminUsersPage({ me }: { me: UserPublic }) {
  const usersQuery = useQuery({
    queryKey: ['admin_users'],
    queryFn: fetchAllUsers,
  })
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')

  // Client-side search: a case-insensitive fragment across name + email,
  // narrowed further by the role select ('' = every role).
  const users = usersQuery.data ?? []
  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase()
    return users.filter((user) => {
      if (roleFilter !== '' && user.role !== roleFilter) return false
      if (needle === '') return true
      const haystack = `${user.first_name} ${user.last_name} ${user.email}`.toLowerCase()
      return haystack.includes(needle)
    })
  }, [users, search, roleFilter])

  // Adapt UserPublic rows for the generic table: the is_active boolean
  // becomes the string ('true'/'false') its select deals in.
  const rows = filtered.map((user) => ({
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
    return <QueryStatus isLoading />
  }
  if (usersQuery.isError) {
    return <ErrorMessage error={usersQuery.error} />
  }

  return (
    <section>
      <h1>Lista użytkowników</h1>
      <p className="muted">
        {users.length} użytkowników
        {filtered.length !== users.length && ` — wyświetlanych: ${filtered.length}`}
      </p>

      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', margin: '0.5rem 0 1rem' }}>
        <label>
          Szukaj
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Imię, nazwisko lub e-mail"
            style={inputStyle}
          />
        </label>
        <label>
          Rola
          <select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)} style={inputStyle}>
            <option value="">Wszystkie</option>
            {ROLE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <EntitySection
        title="Konta"
        fields={fields}
        rows={rows}
        cacheKey={['admin_users']}
        isRowEditable={(id) => id !== me.id}
        update={(id, v) =>
          updateUser(id, {
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
