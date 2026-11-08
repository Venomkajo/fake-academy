// Schedule screen (route "/schedule") — dispatches by role: students see
// the weekly plan of their groups (README S2), teachers their own timetable
// (slots of every subject they teach). Admins manage the timetable in
// /admin/schedule instead, so they get an explicit note rather than a broken
// view.
import type { Role } from '../api/auth'

import StudentSchedulePage from './student/StudentSchedulePage'
import TeacherSchedulePage from './teacher/TeacherSchedulePage'

interface Props {
  role: Role
}

export default function SchedulePage({ role }: Props) {
  if (role === 'teacher') {
    return <TeacherSchedulePage />
  }
  if (role === 'student') {
    return <StudentSchedulePage />
  }
  return (
    <section>
      <h1>Plan zajęć</h1>
      <p className="muted">
        Planem zajęć zarządza administrator w panelu „Edytor planu”.
      </p>
    </section>
  )
}
