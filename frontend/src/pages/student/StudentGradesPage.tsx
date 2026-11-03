// Student's own grades (the "/grades" route, student side — README card S1,
// minus the AI panel which comes later): one collapsible card per subject,
// one row per grade with its category, weight and date, plus the weighted
// average per subject — Σ(value × weight) / Σ(weight) over the categories
// that have a numeric grade; symbol-only grades (ZAL/NZAL) never enter the
// average. The flat GET /grades/me list is grouped and averaged client-side.
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { apiErrorMessage } from '../../api/auth'
import { fetchMyGrades, type GradeForStudent } from '../../api/grades'

/** One subject card's content: everything shown between its <summary> rows. */
interface SubjectSection {
  key: string
  subject: string
  teacher: string
  group: string
  grades: GradeForStudent[]
  average: number | null
}

/** Group the flat grade list into per-subject sections with weighted averages. */
function groupBySubject(grades: GradeForStudent[]): SubjectSection[] {
  const sections = new Map<string, SubjectSection>()
  for (const grade of grades) {
    // Subject + group + teacher identifies one course block: the same
    // subject taught to another group/by another teacher is a separate card.
    const key = `${grade.subject_name}|${grade.group_name}|${grade.teacher_last_name}|${grade.teacher_first_name}`
    if (!sections.has(key)) {
      sections.set(key, {
        key,
        subject: grade.subject_name,
        teacher: `${grade.teacher_first_name} ${grade.teacher_last_name}`,
        group: grade.group_name,
        grades: [],
        average: null,
      })
    }
    sections.get(key)!.grades.push(grade)
  }

  for (const section of sections.values()) {
    // Weighted average over numeric grades only (README S1).
    let weightedSum = 0
    let weightSum = 0
    for (const grade of section.grades) {
      if (grade.value !== null) {
        weightedSum += grade.value * grade.category_weight
        weightSum += grade.category_weight
      }
    }
    section.average = weightSum > 0 ? weightedSum / weightSum : null
  }
  return [...sections.values()]
}

/** Format a grade cell: numeric values keep one decimal, symbols as-is. */
function gradeText(grade: GradeForStudent): string {
  if (grade.symbol !== null) return grade.symbol
  if (grade.value !== null) return Number.isInteger(grade.value) ? String(grade.value) : grade.value.toFixed(1)
  return '—'
}

export default function StudentGradesPage() {
  const gradesQuery = useQuery({ queryKey: ['grades_me'], queryFn: fetchMyGrades })
  const subjects = useMemo(() => groupBySubject(gradesQuery.data ?? []), [gradesQuery.data])

  if (gradesQuery.isLoading) {
    return <p className="muted">Ładowanie…</p>
  }
  if (gradesQuery.isError) {
    return (
      <p role="alert" style={{ color: 'var(--color-danger)' }}>
        {apiErrorMessage(gradesQuery.error)}
      </p>
    )
  }

  return (
    <section>
      <h1>Moje oceny</h1>

      {subjects.length === 0 && (
        <p className="muted">Nie masz jeszcze żadnych ocen.</p>
      )}

      {subjects.map((section) => (
        // open by default: the newest subject is what the student came for.
        <details key={section.key} className="card" open style={{ marginBottom: '1rem' }}>
          <summary style={{ cursor: 'pointer' }}>
            <strong>{section.subject}</strong>{' '}
            <span className="muted">
              · {section.group} · {section.teacher}
            </span>
            {section.average !== null && (
              <span style={{ float: 'right' }}>
                Średnia: <strong>{section.average.toFixed(2)}</strong>
              </span>
            )}
          </summary>

          <table className="data-table" style={{ marginTop: '0.75rem' }}>
            <thead>
              <tr>
                <th>Kategoria</th>
                <th className="num">Waga</th>
                <th className="num">Ocena</th>
                <th>Data wystawienia</th>
              </tr>
            </thead>
            <tbody>
              {section.grades.map((grade) => (
                <tr key={grade.id}>
                  <td>{grade.category_name}</td>
                  <td className="num">{grade.category_weight}%</td>
                  <td className="num">
                    <strong>{gradeText(grade)}</strong>
                  </td>
                  <td>{new Date(grade.created_at).toLocaleDateString('pl-PL')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      ))}
    </section>
  )
}
