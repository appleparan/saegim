/**
 * User API calls.
 */

import { api } from './client'

export interface UserListItem {
  readonly id: string
  readonly name: string
  readonly email: string
  readonly role: string
  readonly created_at: string
}

export async function listUsers(): Promise<readonly UserListItem[]> {
  return api.get<UserListItem[]>('/api/v1/users')
}
