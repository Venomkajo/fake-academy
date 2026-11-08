// Messages screen (route "/messages") — dispatches by role: students and
// teachers get the shared MessagesView (README cards S3/W4), admins have
// no mailbox of their own so they get an explicit note instead.
import type { UserPublic } from '../api/auth'

import MessagesView from '../components/messages/MessagesView'

interface Props {
  user: UserPublic
}

export default function MessagesPage({ user }: Props) {
  if (user.role === 'student' || user.role === 'teacher') {
    return (
      <MessagesView
        role={user.role}
        callerId={user.id}
        callerName={`${user.first_name} ${user.last_name}`}
      />
    )
  }
  return (
    <section>
      <h1>Wiadomości</h1>
      <p className="muted">Wiadomości nie dotyczą konta administratora.</p>
    </section>
  )
}
