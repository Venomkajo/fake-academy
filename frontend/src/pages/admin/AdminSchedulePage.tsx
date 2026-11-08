// Admin timetable editor (route "/admin/schedule", README card A3): the
// whole university's week grid plus add/edit/delete of lesson slots. A slot
// tile loads into the form (assignment × day × hours × room); clicking an
// empty day area prefills that day+hour for a new slot. The view filter
// narrows the grid to one teacher or one group ("całość" shows everything)
// — the admin's equivalent of the personal student/teacher plans. Conflicts
// (room/group/teacher already busy) are rejected by the backend with a 409
// naming the clashing lesson; that message is shown verbatim.
import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  createLessonSlot,
  deleteLessonSlot,
  fetchAllLessonSlots,
  updateLessonSlot,
  type LessonSlot,
} from '../../api/schedule'
import { apiErrorMessage } from '../../api/auth'
import { fetchAllUsers, fetchStructure } from '../../api/admin'

import WeekGrid, {
  DAY_LABELS,
  minutesToTime,
  mondayOf,
  timeToMinutes,
} from '../../components/schedule/WeekGrid'

/** Values of the slot form — inputs/selects are strings, like EntitySection. */
interface SlotFormValues {
  assignment_id: string
  day_of_week: string
  start_time: string
  end_time: string
  room: string
}

const EMPTY_FORM: SlotFormValues = {
  assignment_id: '',
  day_of_week: '0',
  start_time: '08:00',
  end_time: '09:30',
  room: '',
}

const inputStyle = {
  width: '100%',
  padding: '0.45rem 0.6rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  font: 'inherit',
} as const

export default function AdminSchedulePage() {
  const queryClient = useQueryClient()

  const slotsQuery = useQuery({
    queryKey: ['admin_lesson_slots'],
    queryFn: fetchAllLessonSlots,
  })
  // Structure + users resolve the assignment ids into readable select labels.
  const structureQuery = useQuery({ queryKey: ['admin_structure'], queryFn: fetchStructure })
  const usersQuery = useQuery({ queryKey: ['admin_users'], queryFn: fetchAllUsers })

  const [form, setForm] = useState<SlotFormValues>(EMPTY_FORM)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [view, setView] = useState('')

  const setField = (key: keyof SlotFormValues, value: string) =>
    setForm((previous) => ({ ...previous, [key]: value }))

  const startAdd = (day: number, time: string) => {
    // Empty-grid click: prefill day + clicked hour, default 90-minute block.
    setForm({
      ...EMPTY_FORM,
      day_of_week: String(day),
      start_time: time,
      end_time: minutesToTime(timeToMinutes(time) + 90),
    })
    setEditingId(null)
    setError(null)
  }

  const startEdit = (slot: LessonSlot) => {
    setForm({
      assignment_id: String(slot.assignment_id),
      day_of_week: String(slot.day_of_week),
      start_time: slot.start_time.slice(0, 5),
      end_time: slot.end_time.slice(0, 5),
      room: slot.room,
    })
    setEditingId(slot.id)
    setError(null)
  }

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload = {
        assignment_id: Number(form.assignment_id),
        day_of_week: Number(form.day_of_week),
        start_time: form.start_time,
        end_time: form.end_time,
        room: form.room.trim(),
      }
      return editingId === null
        ? createLessonSlot(payload)
        : updateLessonSlot(editingId, payload)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin_lesson_slots'] })
      setForm(EMPTY_FORM)
      setEditingId(null)
      setError(null)
    },
    onError: (mutationError) => setError(apiErrorMessage(mutationError)),
  })

  const removeMutation = useMutation({
    mutationFn: (slotId: number) => deleteLessonSlot(slotId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin_lesson_slots'] })
      setForm(EMPTY_FORM)
      setEditingId(null)
      setError(null)
    },
    onError: (mutationError) => setError(apiErrorMessage(mutationError)),
  })

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!form.assignment_id) {
      setError('Wybierz przypisanie (przedmiot, wykładowca, grupa).')
      return
    }
    if (!form.room.trim()) {
      setError('Podaj salę.')
      return
    }
    saveMutation.mutate()
  }

  const handleRemove = () => {
    if (editingId === null) return
    if (window.confirm('Usunąć te zajęcia z planu?')) removeMutation.mutate(editingId)
  }

  const structure = structureQuery.data
  const users = usersQuery.data ?? []

  const userLabel = (id: number) => {
    const user = users.find((candidate) => candidate.id === id)
    return user ? `${user.first_name} ${user.last_name}` : `#${id}`
  }

  // One option per teaching assignment: "przedmiot — wykładowca — grupa (kierunek)".
  const assignmentOptions = (structure?.teaching_assignments ?? []).map((assignment) => {
    const subject = structure?.subjects.find((s) => s.id === assignment.subject_id)
    const group = structure?.groups.find((g) => g.id === assignment.group_id)
    const field = structure?.fields.find((f) => f.id === group?.field_id)
    return {
      value: String(assignment.id),
      label: `${subject?.name ?? `#${assignment.subject_id}`} — ${userLabel(
        assignment.teacher_id,
      )} — ${group?.name ?? `#${assignment.group_id}`}${field ? ` (${field.name})` : ''}`,
    }
  })

  // View filter: everything, or one teacher's / one group's slice of the plan.
  const viewOptions = [
    { value: '', label: 'Całość (wszyscy)' },
    ...users
      .filter((user) => user.role === 'teacher')
      .map((user) => ({ value: `teacher:${user.id}`, label: `Wykładowca: ${userLabel(user.id)}` })),
    ...(structure?.groups ?? []).map((group) => ({
      value: `group:${group.id}`,
      label: `Grupa: ${group.name}`,
    })),
  ]

  const slots = slotsQuery.data ?? []
  const visibleSlots = slots.filter((slot) => {
    if (view === '') return true
    const [kind, rawId] = view.split(':')
    const id = Number(rawId)
    const assignment = structure?.teaching_assignments.find(
      (candidate) => candidate.id === slot.assignment_id,
    )
    if (kind === 'teacher') return assignment?.teacher_id === id
    return assignment?.group_id === id
  })

  if (slotsQuery.isLoading) {
    return <p className="muted">Ładowanie…</p>
  }
  if (slotsQuery.isError) {
    return (
      <p role="alert" style={{ color: 'var(--color-danger)' }}>
        {apiErrorMessage(slotsQuery.error)}
      </p>
    )
  }

  return (
    <section>
      <h1>Edytor planu zajęć</h1>
      <p className="muted">
        Kliknij kafelek, aby edytować zajęcia, lub puste pole w dniu, aby dodać
        nowe. Zajęcia powtarzają się co tydzień.
      </p>

      <div className="schedule-nav">
        <label className="schedule-view-label">
          Widok planu{' '}
          <select value={view} onChange={(event) => setView(event.target.value)} style={inputStyle}>
            {viewOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <WeekGrid
        slots={visibleSlots}
        weekStart={mondayOf(new Date())}
        mode="admin"
        onSlotClick={startEdit}
        onEmptyClick={startAdd}
      />

      <form className="card schedule-form" onSubmit={handleSubmit}>
        <h2 style={{ margin: 0, gridColumn: '1 / -1', fontSize: '1.1rem' }}>
          {editingId === null ? 'Nowe zajęcia' : 'Edycja zajęć'}
        </h2>

        <label className="span-2">
          Przypisanie (przedmiot — wykładowca — grupa)
          <select
            value={form.assignment_id}
            onChange={(event) => setField('assignment_id', event.target.value)}
            style={inputStyle}
          >
            <option value="">— wybierz —</option>
            {assignmentOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Dzień tygodnia
          <select
            value={form.day_of_week}
            onChange={(event) => setField('day_of_week', event.target.value)}
            style={inputStyle}
          >
            {DAY_LABELS.map((label, day) => (
              <option key={label} value={String(day)}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Sala
          <input
            type="text"
            value={form.room}
            onChange={(event) => setField('room', event.target.value)}
            placeholder="np. A-3.14"
            style={inputStyle}
          />
        </label>

        <label>
          Godzina rozpoczęcia
          <input
            type="time"
            value={form.start_time}
            onChange={(event) => setField('start_time', event.target.value)}
            style={inputStyle}
            required
          />
        </label>

        <label>
          Godzina zakończenia
          <input
            type="time"
            value={form.end_time}
            onChange={(event) => setField('end_time', event.target.value)}
            style={inputStyle}
            required
          />
        </label>

        <div className="span-2" style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button type="submit" className="btn" disabled={saveMutation.isPending}>
            {saveMutation.isPending
              ? 'Zapisywanie…'
              : editingId === null
                ? 'Dodaj zajęcia'
                : 'Zapisz zmiany'}
          </button>
          {editingId !== null && (
            <>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  setForm(EMPTY_FORM)
                  setEditingId(null)
                  setError(null)
                }}
              >
                Anuluj
              </button>
              <button
                type="button"
                className="btn btn-danger"
                disabled={removeMutation.isPending}
                onClick={handleRemove}
              >
                Usuń
              </button>
            </>
          )}
        </div>

        {error && (
          <p role="alert" className="span-2" style={{ color: 'var(--color-danger)', margin: 0 }}>
            {error}
          </p>
        )}
      </form>
    </section>
  )
}

