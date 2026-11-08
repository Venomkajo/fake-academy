import { api } from './client'

/** A person's identity as message listings show it (never the email). */
export interface UserBrief {
  id: number
  first_name: string
  last_name: string
}

/** One private message or announcement, flattened with names + the caller's receipt. */
export interface Message {
  id: number
  sender_id: number
  sender_first_name: string
  sender_last_name: string
  sender_role: string
  recipient_id: number | null
  recipient_first_name: string | null
  recipient_last_name: string | null
  group_id: number | null
  group_name: string | null
  title: string | null
  content: string
  created_at: string
  read_by_caller: boolean
}

/** One of the caller's teaching groups with its student members (teacher selector). */
export interface GroupWithMembers {
  group_id: number
  group_name: string
  field_name: string
  students: UserBrief[]
}

/** Payload of GET /messages/contacts: who the caller may write to. */
export interface Contacts {
  teachers: UserBrief[]
  groups: GroupWithMembers[]
}

/** Body of POST /messages — exactly one target: a recipient or a group. */
export type MessagePayload = {
  title?: string | null
  content: string
  recipient_id?: number
  group_id?: number
}

/** GET /messages — private messages the caller sent or received, newest first. */
export async function fetchMessages(): Promise<Message[]> {
  const response = await api.get<Message[]>('/messages')
  return response.data
}

/** GET /messages/announcements — announcements of the caller's groups. */
export async function fetchAnnouncements(): Promise<Message[]> {
  const response = await api.get<Message[]>('/messages/announcements')
  return response.data
}

/** GET /messages/contacts — teachers (student side) or groups with members (teacher side). */
export async function fetchContacts(): Promise<Contacts> {
  const response = await api.get<Contacts>('/messages/contacts')
  return response.data
}

/** GET /messages/unread-count — the number for the navbar badge. */
export async function fetchUnreadCount(): Promise<number> {
  const response = await api.get<number>('/messages/unread-count')
  return response.data
}

/** POST /messages — send a private message or publish a group announcement. */
export async function sendMessage(payload: MessagePayload): Promise<Message> {
  const response = await api.post<Message>('/messages', payload)
  return response.data
}

/** POST /messages/{id}/read — record a read receipt; idempotent. */
export async function markMessageRead(id: number): Promise<void> {
  await api.post(`/messages/${id}/read`)
}