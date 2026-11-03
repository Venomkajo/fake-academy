// Groups screen (route "/groups") — role-aware, the early "whose groups"
// view: students see the groups they belong to (name, field of study,
// member count — GET /groups/me), teachers see the groups they teach as
// one row per teaching assignment (subject × group × field — GET
// /groups/teaching). Admins manage groups in /admin/structure instead,
// so they get an explicit note. Only the role-specific query runs
// (TanStack `enabled`), so a teacher never fires the student endpoint.
import { useQuery } from '@tanstack/react-query'

import type { Role } from '../api/auth'
import { apiErrorMessage } from '../api/auth'
import { fetchMyGroups, fetchTaughtGroups } from '../api/groups'

interface Props {
  role: Role
}

export default function GroupsPage({ role }: Props) {
  const isStudent = role === 'student'
  const isTeacher = role === 'teacher'

  const studentQuery = useQuery({
    queryKey: ['groups_me'],
    queryFn: fetchMyGroups,
    enabled: isStudent,
  })
  const teacherQuery = useQuery({
    queryKey: ['groups_teaching'],
    queryFn: fetchTaughtGroups,
    enabled: isTeacher,
  })

  if (!isStudent && !isTeacher) {
    return (
      <section>
        <h1>Grupy</h1>
        <p className="muted">
          Grupami zarządza administrator w paneli „Struktura uczelni".
        </p>
      </section>
    )
  }

  const query = isStudent ? studentQuery : teacherQuery

  return (
    <section>
      <h1>{isStudent ? 'Moje grupy' : 'Prowadzone grupy'}</h1>
      <p className="muted">
        {isStudent
          ? 'Grupy, do których należysz.'
          : 'Przedmioty prowadzone w poszczególnych grupach.'}
      </p>

      {query.isLoading && <p className="muted">Ładowanie…</p>}
      {query.isError && (
        <p role="alert" style={{ color: 'var(--color-danger)' }}>
          {apiErrorMessage(query.error)}
        </p>
      )}

      {query.isSuccess && isStudent && (
        <>
          {(studentQuery.data?.length ?? 0) === 0 && (
            <p className="muted">Nie należysz jeszcze do żadnej grupy.</p>
          )}
          {(studentQuery.data?.length ?? 0) > 0 && (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Grupa</th>
                  <th>Kierunek</th>
                  <th className="num">Liczba studentów</th>
                </tr>
              </thead>
              <tbody>
                {studentQuery.data!.map((group) => (
                  <tr key={group.id}>
                    <td>{group.name}</td>
                    <td>{group.field_name}</td>
                    <td className="num">{group.member_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}

      {query.isSuccess && isTeacher && (
        <>
          {(teacherQuery.data?.length ?? 0) === 0 && (
            <p className="muted">Nie prowadzisz jeszcze żadnych zajęć.</p>
          )}
          {(teacherQuery.data?.length ?? 0) > 0 && (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Przedmiot</th>
                  <th>Grupa</th>
                  <th>Kierunek</th>
                </tr>
              </thead>
              <tbody>
                {teacherQuery.data!.map((row) => (
                  <tr key={row.assignment_id}>
                    <td>{row.subject_name}</td>
                    <td>{row.group_name}</td>
                    <td>{row.field_name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </section>
  )
}
