import { api } from './client'
import { UserPublic } from './auth'

/** GET /admin/users — fetches all users. */
export async function fetchAllUsers(): Promise<UserPublic[]> {
  const response = await api.get<UserPublic[]>('/admin/users')
  return response.data
}

/** PUT /admin/users/{userId} — updates a user's information. */
export async function updateUser(userId: number, updates: UserPublic): Promise<UserPublic> {
  const response = await api.put<UserPublic>(`/admin/users/${userId}`, updates)
  return response.data
}

// --- structure (README A2) -------------------------------------------------
// Types mirror app/schemas/structure.py one to one; the aggregate GET
// payload carries only FK ids — names are resolved client-side.

/** A field of study, e.g. "Informatyka" (GET /admin/structure → fields). */
export type FieldOfStudy = {
  id: number
  name: string
}

/** A student group, e.g. "CS-2026-A"; `field_id` links it to its field. */
export type StudentGroup = {
  id: number
  name: string
  field_id: number
}

/** A taught subject with its optional free-form description. */
export type Subject = {
  id: number
  name: string
  description: string | null
}

/** Which teacher (users.id) teaches which subject to which student group. */
export type TeachingAssignment = {
  id: number
  subject_id: number
  teacher_id: number
  group_id: number
}

/** One student's (users.id) membership in one student group. */
export type GroupMembership = {
  id: number
  student_id: number
  group_id: number
}

/** Payload of GET /admin/structure: every structure entity in one shot. */
export type StructureResponse = {
  fields: FieldOfStudy[]
  groups: StudentGroup[]
  subjects: Subject[]
  teaching_assignments: TeachingAssignment[]
  group_memberships: GroupMembership[]
}

// Write payloads: every field optional so one shape serves both POST (all
// fields present) and PATCH (only what changes) — the backend applies
// PATCH bodies partially.

/** Create/update body for the /admin/fields endpoints. */
export type FieldOfStudyPayload = { name?: string }

/** Create/update body for the /admin/groups endpoints. */
export type StudentGroupPayload = { name?: string; field_id?: number }

/** Create/update body for the /admin/subjects endpoints. */
export type SubjectPayload = { name?: string; description?: string | null }

/** Create/update body for the /admin/teaching-assignments endpoints. */
export type TeachingAssignmentPayload = {
  subject_id?: number
  teacher_id?: number
  group_id?: number
}

/** Create/update body for the /admin/group-memberships endpoints. */
export type GroupMembershipPayload = { student_id?: number; group_id?: number }

/** GET /admin/structure — the whole university structure in one payload. */
export async function fetchStructure(): Promise<StructureResponse> {
  const response = await api.get<StructureResponse>('/admin/structure')
  return response.data
}

/** POST /admin/fields — create a field of study. */
export async function createFieldOfStudy(payload: FieldOfStudyPayload): Promise<FieldOfStudy> {
  const response = await api.post<FieldOfStudy>('/admin/fields', payload)
  return response.data
}

/** PATCH /admin/fields/{id} — rename a field of study. */
export async function updateFieldOfStudy(id: number, payload: FieldOfStudyPayload): Promise<FieldOfStudy> {
  const response = await api.patch<FieldOfStudy>(`/admin/fields/${id}`, payload)
  return response.data
}

/** POST /admin/groups — create a student group in a field. */
export async function createStudentGroup(payload: StudentGroupPayload): Promise<StudentGroup> {
  const response = await api.post<StudentGroup>('/admin/groups', payload)
  return response.data
}

/** PATCH /admin/groups/{id} — rename a group or move it to another field. */
export async function updateStudentGroup(id: number, payload: StudentGroupPayload): Promise<StudentGroup> {
  const response = await api.patch<StudentGroup>(`/admin/groups/${id}`, payload)
  return response.data
}

/** POST /admin/subjects — create a subject. */
export async function createSubject(payload: SubjectPayload): Promise<Subject> {
  const response = await api.post<Subject>('/admin/subjects', payload)
  return response.data
}

/** PATCH /admin/subjects/{id} — edit a subject (null clears the description). */
export async function updateSubject(id: number, payload: SubjectPayload): Promise<Subject> {
  const response = await api.patch<Subject>(`/admin/subjects/${id}`, payload)
  return response.data
}

/** POST /admin/teaching-assignments — assign a teacher to subject + group. */
export async function createTeachingAssignment(payload: TeachingAssignmentPayload): Promise<TeachingAssignment> {
  const response = await api.post<TeachingAssignment>('/admin/teaching-assignments', payload)
  return response.data
}

/** PATCH /admin/teaching-assignments/{id} — change an assignment's legs. */
export async function updateTeachingAssignment(id: number, payload: TeachingAssignmentPayload): Promise<TeachingAssignment> {
  const response = await api.patch<TeachingAssignment>(`/admin/teaching-assignments/${id}`, payload)
  return response.data
}

/** POST /admin/group-memberships — put a student into a group. */
export async function createGroupMembership(payload: GroupMembershipPayload): Promise<GroupMembership> {
  const response = await api.post<GroupMembership>('/admin/group-memberships', payload)
  return response.data
}

/** PATCH /admin/group-memberships/{id} — change a membership's student/group. */
export async function updateGroupMembership(id: number, payload: GroupMembershipPayload): Promise<GroupMembership> {
  const response = await api.patch<GroupMembership>(`/admin/group-memberships/${id}`, payload)
  return response.data
}