// Student's weekly timetable (the "/schedule" route, student side — README
// card S2): every slot of every group the student belongs to, laid out on
// the shared week grid with previous/next/current week navigation. Slots
// are weekly recurring (no dates server-side), so switching weeks only
// relabels the columns' dates — the muted note says so explicitly.
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { apiErrorMessage } from '../../api/auth'
import { fetchMySchedule } from '../../api/schedule'

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

export default function StudentSchedulePage() {
  const scheduleQuery = useQuery({ queryKey: ['schedule_me'], queryFn: fetchMySchedule })
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
  // A student may belong to groups on several fields — list them so the
  // plan's scope is obvious without reading every tile.
  const groups = [...new Set(slots.map((slot) => `${slot.group_name} (${slot.field_name})`))]

  return (
    <section>
      <h1>Plan zajęć</h1>
      <p className="muted">
        {groups.length > 0 && <>Grupy: {groups.join(', ')}. </>}
        Zajęcia powtarzają się co tydzień według tego planu.
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
        <p className="muted">Twoje grupy nie mają jeszcze żadnych zajęć w planie.</p>
      )}
      {slots.length > 0 && <WeekGrid slots={slots} weekStart={weekStart} mode="student" />}
    </section>
  )
}
