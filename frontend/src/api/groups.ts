import { api } from './client'

/** One group the student belongs to (GET /groups/me), with its member count. */
export interface MyGroup {
  id: number
  name: string
  field_name: string
  member_count: number
}

/** One of the teacher's assignments (GET /groups/teaching): subject × group. */
export interface TaughtGroup {
  assignment_id: number
  subject_name: string
  group_id: number
  group_name: string
  field_name: string
}

/** GET /groups/me — the calling student's groups. */
export async function fetchMyGroups(): Promise<MyGroup[]> {
  const response = await api.get<MyGroup[]>('/groups/me')
  return response.data
}

/** GET /groups/teaching — the groups the calling teacher teaches. */
export async function fetchTaughtGroups(): Promise<TaughtGroup[]> {
  const response = await api.get<TaughtGroup[]>('/groups/teaching')
  return response.data
}