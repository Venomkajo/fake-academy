// The messages view shared by students and teachers (README cards S3/W4):
// two tabs — private threads (left: thread list with unread dots, right:
// the conversation panel + reply) and group announcements (a flat list).
// The "new message" form adapts to the role: a student picks one of their
// teachers, a teacher picks a group (announcement) or one of its students
// (private message). Unread state lives server-side (read receipts); every
// open/reply/send invalidates the shared ['messages'] cache so the navbar
// badge and the lists stay in sync without websockets.
import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiErrorMessage, type Role } from '../../api/auth'
import {
  fetchAnnouncements,
  fetchContacts,
  fetchMessages,
  markMessageRead,
  sendMessage,
  type Message,
} from '../../api/messages'

/** One private thread: the other person + its messages (newest first). */
interface Thread {
  otherId: number
  otherName: string
  messages: Message[]
  unread: number
}

/** Group the flat message list into per-person threads, newest thread first. */
function groupThreads(callerId: number, messages: readonly Message[]): Thread[] {
  const byOther = new Map<number, Message[]>()
  for (const message of messages) {
    // The "other side" is the sender for received mail, the recipient for sent.
    const otherId = message.sender_id === callerId ? message.recipient_id : message.sender_id
    if (otherId === null) continue
    if (!byOther.has(otherId)) byOther.set(otherId, [])
    byOther.get(otherId)!.push(message)
  }

  const threads: Thread[] = []
  for (const [otherId, threadMessages] of byOther) {
    // Chronological order inside a thread: older first, so the reply lands
    // under the question. id asc is only the tie-break for identical
    // timestamps (rows seeded in one transaction share one created_at).
    const sorted = [...threadMessages].sort((a, b) => {
      if (a.created_at === b.created_at) return a.id - b.id
      return a.created_at.localeCompare(b.created_at)
    })
    const nameOf = (m: Message) =>
      m.sender_id === otherId
        ? `${m.sender_first_name} ${m.sender_last_name}`
        : `${m.recipient_first_name} ${m.recipient_last_name}`
    threads.push({
      otherId,
      otherName: nameOf(sorted[0]),
      messages: sorted,
      unread: sorted.filter((m) => m.sender_id !== callerId && !m.read_by_caller).length,
    })
  }
  // Most recently active threads on top.
  return threads.sort((a, b) => {
    const lastA = a.messages[a.messages.length - 1]?.created_at ?? ''
    const lastB = b.messages[b.messages.length - 1]?.created_at ?? ''
    return lastB.localeCompare(lastA)
  })
}

/** Timestamp → "dziś 14:30" / "5 lis 2026" style label. */
function formatWhen(iso: string): string {
  const date = new Date(iso)
  const today = new Date()
  const sameDay = date.toDateString() === today.toDateString()
  if (sameDay) {
    return `dziś ${date.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}`
  }
  return date.toLocaleDateString('pl-PL', { day: 'numeric', month: 'short', year: 'numeric' })
}

const inputStyle = {
  width: '100%',
  padding: '0.45rem 0.6rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius)',
  font: 'inherit',
} as const

interface Props {
  role: Role
  callerId: number
  callerName: string
}

export default function MessagesView({ role, callerId, callerName }: Props) {
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<'threads' | 'announcements'>('threads')
  const [activeOther, setActiveOther] = useState<number | null>(null)
  const [showCompose, setShowCompose] = useState(false)
  const [composeError, setComposeError] = useState<string | null>(null)

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['messages'] })

  const messagesQuery = useQuery({ queryKey: ['messages', 'threads'], queryFn: fetchMessages })
  const announcementsQuery = useQuery({
    queryKey: ['messages', 'announcements'],
    queryFn: fetchAnnouncements,
  })
  const contactsQuery = useQuery({ queryKey: ['messages', 'contacts'], queryFn: fetchContacts })
  const threads = useMemo(
    () => groupThreads(callerId, messagesQuery.data ?? []),
    [callerId, messagesQuery.data],
  )

  // Opening a thread marks its unread messages as read — receipts land
  // server-side, then the shared cache refetches (badge + dots update).
  const readMutation = useMutation({
    mutationFn: (messageId: number) => markMessageRead(messageId),
    onSuccess: invalidate,
  })
  const openThread = (thread: Thread) => {
    setActiveOther(thread.otherId)
    for (const message of thread.messages) {
      if (message.sender_id !== callerId && !message.read_by_caller) {
        readMutation.mutate(message.id)
      }
    }
  }

  // THE announcements-tab fix: opening the tab marks every visible unread
  // announcement as read (reading IS the only sensible "open" action there),
  // so the navbar badge can actually reach 0 — before, unread announcements
  // lingered forever, badge included.
  const markedAnnouncements = useRef<Set<number>>(new Set())
  useEffect(() => {
    if (tab !== 'announcements') return
    const unread = (announcementsQuery.data ?? []).filter(
      (message) => message.sender_id !== callerId && !message.read_by_caller,
    )
    for (const message of unread) {
      if (markedAnnouncements.current.has(message.id)) continue
      markedAnnouncements.current.add(message.id)
      readMutation.mutate(message.id)
    }
  }, [tab, announcementsQuery.data, callerId])

  const replyMutation = useMutation({
    mutationFn: ({ otherId, content }: { otherId: number; content: string }) =>
      // Chat replies carry no title — the backend drops titles on private
      // messages anyway, so the payload stays title-free.
      sendMessage({ content, recipient_id: otherId }),
    onSuccess: async () => {
      await invalidate()
      setContent('')
      setReplyError(null)
    },
    onError: (error) => setReplyError(apiErrorMessage(error)),
  })

  const composeMutation = useMutation({
    mutationFn: (payload: { title?: string; content: string; recipient_id?: number; group_id?: number }) =>
      sendMessage(payload),
    onSuccess: async () => {
      await invalidate()
      setShowCompose(false)
      setComposeError(null)
      setComposeTarget('')
      setComposeTitle('')
      setComposeContent('')
    },
    onError: (error) => setComposeError(apiErrorMessage(error)),
  })

  const [content, setContent] = useState('')
  const [replyError, setReplyError] = useState<string | null>(null)
  const [composeTarget, setComposeTarget] = useState('')
  const [composeTitle, setComposeTitle] = useState('')
  const [composeContent, setComposeContent] = useState('')

  const activeThread = threads.find((t) => t.otherId === activeOther) ?? null

  const handleReply = (event: FormEvent) => {
    event.preventDefault()
    if (activeOther === null) return
    if (!content.trim()) return
    replyMutation.mutate({ otherId: activeOther, content })
  }

  const handleCompose = (event: FormEvent) => {
    event.preventDefault()
    if (!composeTarget) {
      setComposeError(role === 'student' ? 'Wybierz wykładowcę.' : 'Wybierz odbiorcę.')
      return
    }
    if (!composeContent.trim()) return
    const payload: { title?: string; content: string; recipient_id?: number; group_id?: number } = {
      content: composeContent,
    }
    if (role === 'student') {
      payload.recipient_id = Number(composeTarget)
    } else if (composeTarget.startsWith('g:')) {
      // Group target = announcement: only announcements carry a title.
      payload.group_id = Number(composeTarget.slice(2))
      if (!composeTitle.trim()) {
        setComposeError('Ogłoszenie grupowe musi mieć tytuł.')
        return
      }
      payload.title = composeTitle
    } else {
      payload.recipient_id = Number(composeTarget)
    }
    composeMutation.mutate(payload)
  }

  const teachers = contactsQuery.data?.teachers ?? []
  const contactGroups = contactsQuery.data?.groups ?? []

  if (messagesQuery.isLoading) {
    return <p className="muted">Ładowanie…</p>
  }
  if (messagesQuery.isError) {
    return (
      <p role="alert" style={{ color: 'var(--color-danger)' }}>
        {apiErrorMessage(messagesQuery.error)}
      </p>
    )
  }

  return (
    <section>
      <h1>Wiadomości</h1>

      <div className="schedule-nav">
        <button
          type="button"
          className={tab === 'threads' ? 'btn' : 'btn btn-ghost'}
          onClick={() => setTab('threads')}
        >
          Wiadomości prywatne
        </button>
        <button
          type="button"
          className={tab === 'announcements' ? 'btn' : 'btn btn-ghost'}
          onClick={() => setTab('announcements')}
        >
          Ogłoszenia
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => {
            setShowCompose((previous) => !previous)
            setComposeError(null)
          }}
        >
          {showCompose ? 'Zamknij formularz' : role === 'student' ? 'Napisz do wykładowcy' : 'Nowa wiadomość / ogłoszenie'}
        </button>
      </div>

      {showCompose && (
        <form className="card messages-compose" onSubmit={handleCompose}>
          <label>
            {role === 'student' ? 'Wykładowca' : 'Odbiorca (grupa = ogłoszenie)'}
            <select
              value={composeTarget}
              onChange={(event) => setComposeTarget(event.target.value)}
              style={inputStyle}
            >
              <option value="">— wybierz —</option>
              {role === 'student' ? (
                teachers.map((teacher) => (
                  <option key={teacher.id} value={String(teacher.id)}>
                    {teacher.first_name} {teacher.last_name}
                  </option>
                ))
              ) : (
                <>
                  <optgroup label="Ogłoszenie do całej grupy">
                    {contactGroups.map((group) => (
                      <option key={`g-${group.group_id}`} value={`g:${group.group_id}`}>
                        {group.group_name} ({group.field_name})
                      </option>
                    ))}
                  </optgroup>
                  {contactGroups.map((group) => (
                    <optgroup key={group.group_id} label={`${group.group_name} — studenci`}>
                      {group.students.map((student) => (
                        <option key={student.id} value={String(student.id)}>
                          {student.first_name} {student.last_name}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </>
              )}
            </select>
          </label>
          {role !== 'student' && composeTarget.startsWith('g:') && (
            <label>
              Tytuł ogłoszenia
              <input
                type="text"
                value={composeTitle}
                onChange={(event) => setComposeTitle(event.target.value)}
                style={inputStyle}
                required
              />
            </label>
          )}
          <label>
            Treść
            <textarea
              value={composeContent}
              onChange={(event) => setComposeContent(event.target.value)}
              style={inputStyle}
              rows={4}
              required
            />
          </label>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button type="submit" className="btn" disabled={composeMutation.isPending}>
              {composeMutation.isPending ? 'Wysyłanie…' : 'Wyślij'}
            </button>
            <span className="muted">jako {callerName}</span>
          </div>
          {composeError && (
            <p role="alert" style={{ color: 'var(--color-danger)', margin: 0 }}>
              {composeError}
            </p>
          )}
        </form>
      )}

      {tab === 'threads' ? (
        <div className="messages-layout">
          <ul className="messages-list card">
            {threads.length === 0 && <li className="muted">Brak wiadomości prywatnych.</li>}
            {threads.map((thread) => {
              const last = thread.messages[thread.messages.length - 1]
              return (
                <li key={thread.otherId}>
                  <button
                    type="button"
                    className={`messages-thread${thread.otherId === activeOther ? ' is-active' : ''}`}
                    onClick={() => openThread(thread)}
                  >
                    <span className="messages-thread-name">{thread.otherName}</span>
                    <span className="muted messages-thread-last">
                      {(last?.title ?? last?.content.split('\n')[0]) ?? ''} ·{' '}
                      {last ? formatWhen(last.created_at) : ''}
                    </span>
                    {thread.unread > 0 && (
                      <span className="messages-unread">{thread.unread}</span>
                    )}
                  </button>
                </li>
              )
            })}
          </ul>

          <div className="messages-panel card">
            {activeThread ? (
              <>
                <h2 style={{ margin: '0 0 0.75rem' }}>{activeThread.otherName}</h2>
                <div className="messages-log">
                  {activeThread.messages.map((message) => (
                    <div
                      key={message.id}
                      className={`messages-bubble${message.sender_id === callerId ? ' is-own' : ''}`}
                    >
                      <div className="messages-bubble-meta muted">
                        {message.sender_id === callerId ? callerName : activeThread.otherName} ·{' '}
                        {formatWhen(message.created_at)}
                      </div>
                      {message.title && <strong>{message.title}</strong>}
                      <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{message.content}</p>
                    </div>
                  ))}
                </div>
                <form className="messages-reply" onSubmit={handleReply}>
                  <label>
                    Treść odpowiedzi
                    <textarea
                      value={content}
                      onChange={(event) => setContent(event.target.value)}
                      style={inputStyle}
                      rows={3}
                      required
                    />
                  </label>
                  <button type="submit" className="btn" disabled={replyMutation.isPending}>
                    {replyMutation.isPending ? 'Wysyłanie…' : 'Wyślij odpowiedź'}
                  </button>
                  {replyError && (
                    <p role="alert" style={{ color: 'var(--color-danger)', margin: 0 }}>
                      {replyError}
                    </p>
                  )}
                </form>
              </>
            ) : (
              <p className="muted">Wybierz wątek z listy, aby go przeczytać i odpowiedzieć.</p>
            )}
          </div>
        </div>
      ) : (
        <div className="messages-announcements">
          {announcementsQuery.isLoading && <p className="muted">Ładowanie…</p>}
          {announcementsQuery.isError && (
            <p role="alert" style={{ color: 'var(--color-danger)' }}>
              {apiErrorMessage(announcementsQuery.error)}
            </p>
          )}
          {(announcementsQuery.data ?? []).length === 0 && (
            <p className="muted">Brak ogłoszeń grupowych.</p>
          )}
          {(announcementsQuery.data ?? []).map((announcement) => (
            <article key={announcement.id} className="card messages-announcement">
              <h2 style={{ margin: '0 0 0.25rem' }}>{announcement.title ?? '(bez tytułu)'}</h2>
              <p className="muted" style={{ margin: '0 0 0.5rem' }}>
                {announcement.sender_first_name} {announcement.sender_last_name} ·{' '}
                {announcement.group_name} · {formatWhen(announcement.created_at)}
              </p>
              <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{announcement.content}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}