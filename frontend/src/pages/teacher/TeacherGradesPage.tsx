// Teacher's grading screen (the "/grades" route, teacher side — README cards
// W1/W2 in their early form): an assignment picker (subject × group), a
// categories panel (add/remove grading buckets with percentage weights) and
// the gradebook — one row per student of the group, one column per category.
// Each cell is a small inline editor: type a number (0–100, ',' or '.' as
// the decimal separator) or ZAL/NZAL, then Enter/blur saves it — POST
// /grades when the cell was empty, PATCH /grades/{id} when editing. Emptying
// a cell does nothing (no grade deletion in this early version); conflicts
// (grade already exists) and validation errors surface under the cell.
import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiErrorMessage } from '../../api/auth'
import {
  createGradeCategory,
  deleteGradeCategory,
  fetchGradeSheet,
  fetchMyTeaching,
  issueGrade,
  updateGrade,
  type GradeUpdatePayload,
  type SheetGrade,
  type TeachingAssignment,
} from '../../api/grades'

/** Result of parsing one gradebook cell's input. */
type ParsedCell =
  | { kind: 'empty' }
  | { kind: 'invalid' }
  | { kind: 'ok'; value: string | null; symbol: string | null }

/** Parse a cell's raw text into a {value, symbol} payload (or a verdict). */
function parseCellInput(raw: string): ParsedCell {
  const text = raw.trim().replace(',', '.')
  if (text === '') return { kind: 'empty' }
  const upper = text.toUpperCase()
  if (upper === 'ZAL' || upper === 'NZAL') return { kind: 'ok', value: null, symbol: upper }
  const numeric = Number(text)
  if (Number.isFinite(numeric) && numeric >= 0 && numeric <= 100) {
    // Sent as a string so the backend's Decimal parses it exactly.
    return { kind: 'ok', value: text, symbol: null }
  }
  return { kind: 'invalid' }
}

/** What the input shows for an existing grade (inverse of parseCellInput). */
function existingText(grade: SheetGrade): string {
  if (grade.symbol !== null) return grade.symbol
  if (grade.value !== null) return String(grade.value)
  return ''
}

interface GradeCellProps {
  assignmentId: number
  studentId: number
  categoryId: number
  grade: SheetGrade | null
}

/** One editable gradebook cell: draft input + save-on-Enter/blur mutation. */
function GradeCell({ assignmentId, studentId, categoryId, grade }: GradeCellProps) {
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState(grade ? existingText(grade) : '')
  const [error, setError] = useState<string | null>(null)

  const saveMutation = useMutation({
    mutationFn: (payload: GradeUpdatePayload) =>
      grade
        ? updateGrade(grade.id, payload)
        : issueGrade({ student_id: studentId, category_id: categoryId, ...payload }),
    onSuccess: async () => {
      setError(null)
      await queryClient.invalidateQueries({ queryKey: ['grades_sheet', assignmentId] })
    },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  function commit() {
    const parsed = parseCellInput(draft)
    if (parsed.kind === 'empty') {
      setError(null)
      return
    }
    if (parsed.kind === 'invalid') {
      setError('Liczba 0–100 albo ZAL/NZAL')
      return
    }
    const unchanged =
      grade !== null &&
      grade.symbol === parsed.symbol &&
      grade.value === (parsed.value !== null ? Number(parsed.value) : null)
    if (unchanged) {
      setError(null)
      return
    }
    saveMutation.mutate({ value: parsed.value, symbol: parsed.symbol })
  }

  return (
    <td className="num">
      <input
        className="grade-input"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') commit()
        }}
        disabled={saveMutation.isPending}
        placeholder="—"
        aria-label="Ocena"
      />
      {saveMutation.isPending && <span className="muted"> …</span>}
      {error && (
        <div role="alert" style={{ color: 'var(--color-danger)', fontSize: '0.75rem', margin: 0 }}>
          {error}
        </div>
      )}
    </td>
  )
}

/** Categories of one assignment: current list, add form, remove buttons. */
function CategoryPanel({ assignment }: { assignment: TeachingAssignment }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [weight, setWeight] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Categories feed both the tabs list and the gradebook header, so both
  // caches are invalidated after every category write.
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['grades_teaching'] })
    await queryClient.invalidateQueries({ queryKey: ['grades_sheet', assignment.id] })
  }

  const addMutation = useMutation({
    mutationFn: () =>
      createGradeCategory({
        assignment_id: assignment.id,
        name: name.trim(),
        weight: weight.trim().replace(',', '.'),
      }),
    onSuccess: async () => {
      setName('')
      setWeight('')
      setError(null)
      await invalidate()
    },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  const removeMutation = useMutation({
    mutationFn: (categoryId: number) => deleteGradeCategory(categoryId),
    onSuccess: async () => {
      setError(null)
      await invalidate()
    },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  function handleAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    // Light client-side check; the backend re-validates (0–100, uniqueness).
    const numeric = Number(weight.trim().replace(',', '.'))
    if (name.trim() === '' || !Number.isFinite(numeric) || numeric < 0 || numeric > 100) {
      setError('Podaj nazwę kategorii i wagę 0–100')
      return
    }
    addMutation.mutate()
  }

  return (
    <section className="card" style={{ marginTop: '1rem' }}>
      <h2 style={{ marginTop: 0 }}>Kategorie ocen</h2>

      {assignment.categories.length === 0 && (
        <p className="muted" style={{ marginTop: 0 }}>
          Brak kategorii — dodaj pierwszą (np. Egzamin, waga 60), żeby wystawiać oceny.
        </p>
      )}

      <ul style={{ margin: '0.5rem 0 1rem', padding: 0, listStyle: 'none' }}>
        {assignment.categories.map((category) => (
          <li key={category.id} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span>
              {category.name} — <strong>{category.weight}%</strong>
            </span>
            <button
              type="button"
              className="btn btn-danger"
              disabled={removeMutation.isPending}
              onClick={() => removeMutation.mutate(category.id)}
            >
              Usuń
            </button>
          </li>
        ))}
      </ul>

      <form onSubmit={handleAdd} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <label>
          Nazwa
          <input
            className="grade-input"
            style={{ width: '12rem', display: 'block' }}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <label>
          Waga (%)
          <input
            className="grade-input"
            style={{ width: '6rem', display: 'block' }}
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            inputMode="decimal"
          />
        </label>
        <button type="submit" className="btn" disabled={addMutation.isPending}>
          {addMutation.isPending ? 'Dodawanie…' : 'Dodaj kategorię'}
        </button>
      </form>

      {error && (
        <p role="alert" style={{ color: 'var(--color-danger)', margin: '0.5rem 0 0' }}>
          {error}
        </p>
      )}
    </section>
  )
}

export default function TeacherGradesPage() {
  const teachingQuery = useQuery({ queryKey: ['grades_teaching'], queryFn: fetchMyTeaching })
  // Explicit selection falls back to the first assignment; null until loaded.
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const assignments = teachingQuery.data ?? []
  const selected = assignments.find((a) => a.id === selectedId) ?? assignments[0] ?? null

  const sheetQuery = useQuery({
    queryKey: ['grades_sheet', selected?.id ?? 0],
    queryFn: () => fetchGradeSheet(selected!.id),
    enabled: selected !== null,
  })

  if (teachingQuery.isLoading) {
    return <p className="muted">Ładowanie…</p>
  }
  if (teachingQuery.isError) {
    return (
      <p role="alert" style={{ color: 'var(--color-danger)' }}>
        {apiErrorMessage(teachingQuery.error)}
      </p>
    )
  }

  const sheet = sheetQuery.data

  return (
    <section>
      <h1>Wystawianie ocen</h1>

      {assignments.length === 0 && (
        <p className="muted">Nie masz żadnych przypisań do przedmiotów i grup.</p>
      )}

      {/* Assignment picker — same tab-button pattern as the admin panels. */}
      {assignments.length > 0 && (
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {assignments.map((assignment) => (
            <button
              key={assignment.id}
              type="button"
              className={selected?.id === assignment.id ? 'btn' : 'btn btn-ghost'}
              onClick={() => setSelectedId(assignment.id)}
            >
              {assignment.subject_name} · {assignment.group_name}
            </button>
          ))}
        </div>
      )}

      {selected && (
        <>
          <p className="muted">
            {selected.subject_name} · grupa {selected.group_name} ({selected.field_name})
          </p>

          <CategoryPanel assignment={selected} />

          <h2>Dziennik ocen</h2>
          {selected.categories.length === 0 ? (
            <p className="muted">Dodaj kategorię, aby wystawiać oceny.</p>
          ) : sheetQuery.isLoading ? (
            <p className="muted">Ładowanie dziennika…</p>
          ) : sheetQuery.isError ? (
            <p role="alert" style={{ color: 'var(--color-danger)' }}>
              {apiErrorMessage(sheetQuery.error)}
            </p>
          ) : (sheet?.students.length ?? 0) === 0 ? (
            <p className="muted">Ta grupa nie ma jeszcze studentów.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Student</th>
                  {selected.categories.map((category) => (
                    <th key={category.id} className="num">
                      {category.name} ({category.weight}%)
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sheet!.students.map((student) => (
                  <tr key={student.id}>
                    <td>
                      {student.last_name} {student.first_name}
                    </td>
                    {selected.categories.map((category) => (
                      <GradeCell
                        key={category.id}
                        assignmentId={selected.id}
                        studentId={student.id}
                        categoryId={category.id}
                        grade={
                          sheet!.grades.find(
                            (g) => g.student_id === student.id && g.category_id === category.id,
                          ) ?? null
                        }
                      />
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p className="muted" style={{ fontSize: '0.85rem' }}>
            Wpisz liczbę (0–100) lub ZAL/NZAL i zatwierdź Enterem — zmiana zapisuje się od razu.
          </p>
        </>
      )}
    </section>
  )
}
