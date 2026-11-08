// Admin statistics dashboard (route "/admin/statistics", README card A4):
// counter cards for the platform's usage metrics plus one simple CSS bar
// chart of accounts per role — the darker segment of each bar is the
// active accounts, the lighter one the deactivated. Everything comes from
// a single GET /admin/stats round-trip; the "Odśwież" button refetches on
// demand (TanStack invalidation), so the counters always match the DB.
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { fetchAdminStats } from '../../api/admin'
import { apiErrorMessage } from '../../api/auth'

/** Polish labels for the roles as the API returns them. */
const ROLE_LABELS: Record<string, string> = {
  student: 'Studenci',
  teacher: 'Wykładowcy',
  admin: 'Administratorzy',
}

/** One counter card: a big number with its label and an optional hint line. */
interface StatCard {
  label: string
  value: number
  hint?: string
}

/** Render one group of counter cards under its heading. */
function StatCardGrid({ cards }: { cards: StatCard[] }) {
  return (
    <div className="stats-cards">
      {cards.map((card) => (
        <div key={card.label} className="stats-card">
          <div className="stats-value">{card.value}</div>
          <div className="stats-label">{card.label}</div>
          {card.hint && <div className="stats-hint muted">{card.hint}</div>}
        </div>
      ))}
    </div>
  )
}

export default function AdminStatisticsPage() {
  const queryClient = useQueryClient()
  const statsQuery = useQuery({ queryKey: ['admin_stats'], queryFn: fetchAdminStats })

  if (statsQuery.isLoading) {
    return <p className="muted">Ładowanie…</p>
  }
  if (statsQuery.isError) {
    return (
      <p role="alert" style={{ color: 'var(--color-danger)' }}>
        {apiErrorMessage(statsQuery.error)}
      </p>
    )
  }

  const stats = statsQuery.data!
  const activityCards: StatCard[] = [
    {
      label: 'Użytkownicy',
      value: stats.users_total,
      hint: `${stats.users_active} aktywnych, ${stats.users_total - stats.users_active} wyłączonych`,
    },
    { label: 'Oceny', value: stats.grades },
    { label: 'Wiadomości', value: stats.messages },
    { label: 'Opinie o zajęciach', value: stats.feedback },
    { label: 'Materiały', value: stats.materials },
    { label: 'Zajęcia w planie', value: stats.lesson_slots },
  ]
  const structureCards: StatCard[] = [
    { label: 'Kierunki', value: stats.fields_of_study },
    { label: 'Grupy studenckie', value: stats.student_groups },
    { label: 'Przedmioty', value: stats.subjects },
    { label: 'Przypisania wykładowców', value: stats.teaching_assignments },
    { label: 'Członkostwa grup', value: stats.group_memberships },
  ]

  // Longest bar = the biggest role; widths are relative to it.
  const maxRole = Math.max(...stats.users_by_role.map((role) => role.total), 1)

  return (
    <section>
      <h1>Statystyki systemowe</h1>
      <p className="muted">
        Liczniki zgodne ze stanem bazy na moment ostatniego odpytania.
      </p>

      <button
        type="button"
        className="btn"
        style={{ margin: '0.5rem 0 1.5rem' }}
        disabled={statsQuery.isFetching}
        onClick={() => queryClient.invalidateQueries({ queryKey: ['admin_stats'] })}
      >
        {statsQuery.isFetching ? 'Odświeżanie…' : 'Odśwież'}
      </button>

      <h2>Aktywność platformy</h2>
      <StatCardGrid cards={activityCards} />

      <h2>Konta według roli</h2>
      <p className="muted">
        Ciemniejsza część słupka to konta aktywne, jaśniejsza — wyłączone.
      </p>
      <div className="stats-chart">
        {stats.users_by_role.map((role) => (
          <div key={role.role} className="stats-bar-row">
            <span>{ROLE_LABELS[role.role] ?? role.role}</span>
            <div
              className="stats-bar-track"
              title={`${role.active} aktywnych z ${role.total}`}
            >
              <div className="stats-bar-fill">
                <span
                  className="is-active"
                  style={{ width: `${(role.active / maxRole) * 100}%` }}
                />
                <span
                  className="is-inactive"
                  style={{ width: `${((role.total - role.active) / maxRole) * 100}%` }}
                />
              </div>
            </div>
            <span className="stats-bar-value">
              <strong>{role.total}</strong>
              {role.total !== role.active && (
                <span className="muted"> ({role.active} akt.)</span>
              )}
            </span>
          </div>
        ))}
      </div>

      <h2>Struktura uczelni</h2>
      <StatCardGrid cards={structureCards} />
    </section>
  )
}
