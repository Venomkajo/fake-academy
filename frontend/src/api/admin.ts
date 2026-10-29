import { api } from './client'
import { UserPublic } from './auth'

/** GET /admin/users — fetches all users. */
export async function fetchAllUsers(): Promise<UserPublic[]> {
  const response = await api.get<UserPublic[]>('/admin/users')
  return response.data
}

/** GET /admin/users/{userId} — fetches a user by ID. */
export async function fetchUserById(userId: number): Promise<UserPublic> {
  const response = await api.get<UserPublic>(`/admin/users/${userId}`)
  return response.data
}

/** PUT /admin/users/{userId} — updates a user's information. */
export async function updateUser(userId: number, updates: UserPublic): Promise<UserPublic> {
  const response = await api.put<UserPublic>(`/admin/users/${userId}`, updates)
  return response.data
}