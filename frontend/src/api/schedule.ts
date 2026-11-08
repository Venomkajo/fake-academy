import { api } from './client'

/**
 * One weekly recurring timetable slot as the API flattens it: the slot row
 * itself plus the subject/group/field/teacher names its grid tile shows.
 * Times are "HH:MM:SS" strings; day_of_week: 0 = Monday .. 6 = Sunday.
 */
export interface LessonSlot {
  id: number
  assignment_id: number
  subject_name: string
  group_name: string
  field_name: string
  teacher_first_name: string
  teacher_last_name: string
  day_of_week: number
  start_time: string
  end_time: string
  room: string
}

/**
 * Body of POST/PATCH /admin/lesson-slots. Every field optional so one shape
 * serves both POST (all fields) and PATCH (only what changes); the backend
 * applies PATCH bodies partially and checks conflicts on the effective pair.
 */
export type LessonSlotPayload = {
  assignment_id?: number
  day_of_week?: number
  start_time?: string
  end_time?: string
  room?: string
}

/** GET /schedule/me — the calling student's groups' slots, flattened with names. */
export async function fetchMySchedule(): Promise<LessonSlot[]> {
  const response = await api.get<LessonSlot[]>('/schedule/me')
  return response.data
}

/** GET /schedule/teaching — the calling teacher's own slots, flattened with names. */
export async function fetchTeachingSchedule(): Promise<LessonSlot[]> {
  const response = await api.get<LessonSlot[]>('/schedule/teaching')
  return response.data
}

/** GET /admin/lesson-slots — every slot in the university, flattened with names. */
export async function fetchAllLessonSlots(): Promise<LessonSlot[]> {
  const response = await api.get<LessonSlot[]>('/admin/lesson-slots')
  return response.data
}

/** POST /admin/lesson-slots — add a slot; a room/group/teacher clash gives 409. */
export async function createLessonSlot(payload: LessonSlotPayload): Promise<LessonSlot> {
  const response = await api.post<LessonSlot>('/admin/lesson-slots', payload)
  return response.data
}

/** PATCH /admin/lesson-slots/{id} — change any leg of a slot (assignment/day/time/room). */
export async function updateLessonSlot(id: number, payload: LessonSlotPayload): Promise<LessonSlot> {
  const response = await api.patch<LessonSlot>(`/admin/lesson-slots/${id}`, payload)
  return response.data
}

/** DELETE /admin/lesson-slots/{id} — remove a slot from the timetable. */
export async function deleteLessonSlot(id: number): Promise<void> {
  await api.delete(`/admin/lesson-slots/${id}`)
}
