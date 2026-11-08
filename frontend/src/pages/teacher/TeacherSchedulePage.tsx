// Teacher's weekly timetable (the "/schedule" route, teacher side — the
// counterpart of README card S2): every slot of every assignment the teacher
// holds, on the shared week grid with week navigation. Tiles carry the
// subject, room, hours and the group (with its field) each lesson belongs
// to. Slots are weekly recurring (no dates server-side), so switching weeks
// only relabels the columns' dates.
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { apiErrorMessage } from '../../api/auth'
import { fetchTeachingSchedule } from '../../api/schedule'

import WeekGrid, { addDays, mondayOf } from '../../components/schedule/WeekGrid'

/** "3–9 listopada 2026" style label for one week, given its Monday. */
function formatWeek(weekStart: Date): string {
  const from = weekStart.toLocaleDateString('pl-PL', { day: 'numeric', month: 'long' })
  const to = addDays(weekStart, 6).toLocaleDateString('pl-PL', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
  return `${from} – ${to}`
}

export default function TeacherSchedulePage() {
  const scheduleQuery = useQuery({
    queryKey: ['schedule_teaching'],
    queryFn: fetchTeachingSchedule,
  })
  const [weekStart, setWeekStart] = useState(() => mondayOf(new Date()))

  if (scheduleQuery.isLoading) {
    return <p className="muted">Ładowanie…</p>
  }
  if (scheduleQuery.isError) {
    return (
      <p role="alert" style={{ color: 'var(--color-danger)' }}>
        {apiErrorMessage(scheduleQuery.error)}
      </p>
    )
  }

  const slots = scheduleQuery.data ?? []

  return (
    <section>
      <h1>Mój plan</h1>
      <p className="muted">
        Zajęcia powtarzają się co tydzień według tego planu — tydzień zmienia
        tylko daty w nagłówkach kolumn.
      </p>

      <div className="schedule-nav">
        <button type="button" className="btn btn-ghost" onClick={() => setWeekStart(addDays(weekStart, -7))}>
          ← Poprzedni tydzień
        </button>
        <strong>{formatWeek(weekStart)}</strong>
        <button type="button" className="btn btn-ghost" onClick={() => setWeekStart(addDays(weekStart, 7))}>
          Następny tydzień →
        </button>
        <button type="button" className="btn" onClick={() => setWeekStart(mondayOf(new Date()))}>
          Bieżący tydzień
        </button>
      </div>

      {slots.length === 0 && (
        <p className="muted">Nie prowadzisz jeszcze żadnych zajęć według planu.</p>
      )}
      {slots.length > 0 && <WeekGrid slots={slots} weekStart={weekStart} mode="teacher" />}
    </section>
  )
}
