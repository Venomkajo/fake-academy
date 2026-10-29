import { api } from './client'
import { UserPublic } from './auth'

/** GET /admin/users — fetches all users. */
export async function fetchAllUsers(): Promise<UserPublic[]> {
  const response = await api.get<UserPublic[]>('/admin/users')
  return response.data
}