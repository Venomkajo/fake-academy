// Shared weekly timetable grid (README A3/S2 + the teacher plan): days as
// columns, the hour axis 7:00–21:00 as rows, lesson slots as tiles positioned
// by their start/end times. Purely presentational — all data arrives via
// props, fetching and mutations live in the pages. `mode` picks the tile
// footer (student: teacher name, teacher: group name, admin: both) and
// whether tiles/empty grid areas are clickable (admin editor loads the form).
// Overlapping slots in one day are laid out side by side, calendar-style,
// so a busy day stays readable. Saturday/Sunday columns render only when
// slots exist there.
import { useMemo, type KeyboardEvent, type MouseEvent } from 'react'

import type { LessonSlot } from '../../api/schedule'

/** Polish day labels, indexed by day_of_week (0 = Monday). */
export const DAY_LABELS = [
  'Poniedziałek',
  'Wtorek',
  'Środa',
  'Czwartek',
  'Piątek',
  'Sobota',
  'Niedziela',
] as const

/** The grid's hour window — keep in sync with .schedule-day's gradient in global.css. */
const DAY_START_MIN = 7 * 60
const DAY_END_MIN = 21 * 60
const DAY_SPAN_MIN = DAY_END_MIN - DAY_START_MIN
/** One hour = 60px of grid height, so a 90-minute block is comfortably readable. */
const PX_PER_MINUTE = 1

/** Parse an API time string ("HH:MM:SS" or "HH:MM") into minutes since midnight. */
export function timeToMinutes(time: string): number {
  const [hours, minutes] = time.split(':')
  return Number(hours) * 60 + Number(minutes)
}

/** Minutes since midnight → "HH:MM" (the shape <input type="time"> expects). */
export function minutesToTime(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  return `${String(hours).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`
}

/** The Monday 00:00 of the week containing `date`. */
export function mondayOf(date: Date): Date {
  const monday = new Date(date)
  monday.setHours(0, 0, 0, 0)
  // getDay() is Sunday-based (0 = Sunday); the timetable is Monday-based.
  const daysSinceMonday = (monday.getDay() + 6) % 7
  monday.setDate(monday.getDate() - daysSinceMonday)
  return monday
}

/** `date` plus `days` calendar days (keeps time-of-day). */
export function addDays(date: Date, days: number): Date {
  const result = new Date(date)
  result.setDate(result.getDate() + days)
  return result
}

/** A slot's horizontal placement inside its day column (percentages). */
interface SlotPlacement {
  left: number
  width: number
}

/**
 * Split one day's slots into side-by-side columns: overlapping slots share
 * a cluster, and each cluster's slots are greedily packed into the first
 * column free at their start time — same idea as calendar week views.
 */
function layoutDay(slots: readonly LessonSlot[]): Map<number, SlotPlacement> {
  const layout = new Map<number, SlotPlacement>()
  const sorted = [...slots].sort(
    (a, b) =>
      timeToMinutes(a.start_time) - timeToMinutes(b.start_time) ||
      timeToMinutes(a.end_time) - timeToMinutes(b.end_time),
  )

  let cluster: LessonSlot[] = []
  let clusterEnd = -1
  const flushCluster = () => {
    if (cluster.length === 0) return
    // Column ends: column c is free for a slot starting at or after its end.
    const columnEnds: number[] = []
    const placed = cluster.map((slot) => {
      const start = timeToMinutes(slot.start_time)
      const end = timeToMinutes(slot.end_time)
      let column = columnEnds.findIndex((columnEnd) => columnEnd <= start)
      if (column === -1) {
        columnEnds.push(end)
        column = columnEnds.length - 1
      } else {
        columnEnds[column] = end
      }
      return { slot, column }
    })
    for (const { slot, column } of placed) {
      layout.set(slot.id, {
        left: (column / columnEnds.length) * 100,
        width: 100 / columnEnds.length,
      })
    }
    cluster = []
  }

  for (const slot of sorted) {
    const start = timeToMinutes(slot.start_time)
    // No overlap with the running cluster → flush it and start a new one.
    if (cluster.length > 0 && start >= clusterEnd) flushCluster()
    cluster.push(slot)
    clusterEnd = Math.max(clusterEnd, timeToMinutes(slot.end_time))
  }
  flushCluster()
  return layout
}

/** Deterministic pastel index for a subject name, so a subject keeps its color. */
function tileClass(subject: string): string {
  let hash = 0
  for (let i = 0; i < subject.length; i++) {
    hash = (hash * 31 + subject.charCodeAt(i)) | 0
  }
  return `tile-${Math.abs(hash) % 6}`
}

interface Props {
  slots: readonly LessonSlot[]
  /** Monday 00:00 of the week to label the columns with. */
  weekStart: Date
  /** Tile footer content + admin interactions. */
  mode: 'student' | 'teacher' | 'admin'
  /** Admin only: load this slot into the editor form. */
  onSlotClick?: (slot: LessonSlot) => void
  /** Admin only: the clicked empty day/time as a prefill for a new slot. */
  onEmptyClick?: (day: number, time: string) => void
}

export default function WeekGrid({ slots, weekStart, mode, onSlotClick, onEmptyClick }: Props) {
  // Mon–Fri always; weekend columns only when something lives there.
  const days = useMemo(
    () => [0, 1, 2, 3, 4, ...(slots.some((slot) => slot.day_of_week > 4) ? [5, 6] : [])],
    [slots],
  )
  const byDay = useMemo(() => {
    const map = new Map<number, { slots: LessonSlot[]; layout: Map<number, SlotPlacement> }>()
    for (const day of days) {
      const daySlots = slots.filter((slot) => slot.day_of_week === day)
      map.set(day, { slots: daySlots, layout: layoutDay(daySlots) })
    }
    return map
  }, [slots, days])

  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const handleEmptyClick = (event: MouseEvent<HTMLDivElement>, day: number) => {
    if (mode !== 'admin' || !onEmptyClick) return
    const rect = event.currentTarget.getBoundingClientRect()
    // Click position → minutes from the day's top, rounded to the quarter hour.
    const ratio = Math.min(Math.max((event.clientY - rect.top) / rect.height, 0), 1)
    const minutes = DAY_START_MIN + Math.round((ratio * DAY_SPAN_MIN) / 15) * 15
    // Never later than 30 minutes before the window ends, so a tile stays visible.
    onEmptyClick(day, minutesToTime(Math.min(minutes, DAY_END_MIN - 30)))
  }

  const handleTileKey = (slot: LessonSlot) => (event: KeyboardEvent<HTMLDivElement>) => {
    if (mode !== 'admin' || !onSlotClick) return
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onSlotClick(slot)
    }
  }

  const footerOf = (slot: LessonSlot): string => {
    const teacher = `${slot.teacher_first_name} ${slot.teacher_last_name}`
    if (mode === 'student') return teacher
    if (mode === 'teacher') return `${slot.group_name} · ${slot.field_name}`
    return `${teacher} · ${slot.group_name}`
  }

  return (
    <div className="schedule">
      {/* Column headers: day label + the week's concrete date per column. */}
      <div className="schedule-head">
        <div className="schedule-corner" aria-hidden="true" />
        {days.map((day) => {
          const date = addDays(weekStart, day)
          const isToday = date.getTime() === today.getTime()
          return (
            <div key={day} className={`schedule-day-head${isToday ? ' is-today' : ''}`}>
              <span className="schedule-day-label">{DAY_LABELS[day]}</span>
              <span className="muted">
                {date.toLocaleDateString('pl-PL', { day: 'numeric', month: 'short' })}
              </span>
            </div>
          )
        })}
      </div>

      {/* The grid body: a fixed-height hour ruler + one relative column per day. */}
      <div className="schedule-body" style={{ height: `${DAY_SPAN_MIN * PX_PER_MINUTE}px` }}>
        <div className="schedule-ruler" aria-hidden="true">
          {Array.from({ length: DAY_SPAN_MIN / 60 }, (_, index) => DAY_START_MIN / 60 + index).map(
            (hour) => (
              <div
                key={hour}
                className="schedule-ruler-mark"
                style={{ top: `${((hour * 60 - DAY_START_MIN) / DAY_SPAN_MIN) * 100}%` }}
              >
                {minutesToTime(hour * 60)}
              </div>
            ),
          )}
        </div>

        {days.map((day) => {
          const dayData = byDay.get(day)!
          return (
            <div
              key={day}
              className={`schedule-day${mode === 'admin' ? ' is-clickable' : ''}`}
              onClick={mode === 'admin' ? (event) => handleEmptyClick(event, day) : undefined}
            >
              {dayData.slots.map((slot) => {
                const placement = dayData.layout.get(slot.id)!
                // Clamp into the window — a slot outside 7:00–21:00 still shows.
                const start = Math.max(timeToMinutes(slot.start_time), DAY_START_MIN)
                const end = Math.min(timeToMinutes(slot.end_time), DAY_END_MIN)
                const isAdmin = mode === 'admin'
                return (
                  <div
                    key={slot.id}
                    role={isAdmin ? 'button' : undefined}
                    tabIndex={isAdmin ? 0 : undefined}
                    className={`schedule-slot ${tileClass(slot.subject_name)}${isAdmin ? ' is-clickable' : ''}`}
                    style={{
                      top: `${((start - DAY_START_MIN) / DAY_SPAN_MIN) * 100}%`,
                      height: `${Math.max(((end - start) / DAY_SPAN_MIN) * 100, 3)}%`,
                      left: `${placement.left}%`,
                      width: `calc(${placement.width}% - 4px)`,
                    }}
                    onClick={
                      isAdmin && onSlotClick
                        ? (event) => {
                            // Tiles swallow the day column's empty-click handler.
                            event.stopPropagation()
                            onSlotClick(slot)
                          }
                        : undefined
                    }
                    onKeyDown={handleTileKey(slot)}
                  >
                    <span className="schedule-slot-subject">{slot.subject_name}</span>
                    <span className="schedule-slot-time">
                      {slot.start_time.slice(0, 5)}–{slot.end_time.slice(0, 5)}
                    </span>
                    <span className="schedule-slot-room">sala {slot.room}</span>
                    <span className="schedule-slot-foot muted">{footerOf(slot)}</span>
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>
    </div>
  )
}

