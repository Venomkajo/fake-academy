// Grades screen (route "/grades") — dispatches by role: students see their
// own grades (README S1, AI panel later), teachers the issuing panel
// (README W1/W2-lite). Admins have no grades at all, so they get an
// explicit note instead of a broken student view.
import type { Role } from '../api/auth'

import StudentGradesPage from './student/StudentGradesPage'
import TeacherGradesPage from './teacher/TeacherGradesPage'

interface Props {
  role: Role
}

export default function GradesPage({ role }: Props) {
  if (role === 'teacher') {
    return <TeacherGradesPage />
  }
  if (role === 'student') {
    return <StudentGradesPage />
  }
  return (
    <section>
      <h1>Oceny</h1>
      <p className="muted">Oceny nie dotyczą konta administratora.</p>
    </section>
  )
}
