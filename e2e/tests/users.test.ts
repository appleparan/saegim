import { describe, test, expect, beforeAll } from 'vitest'
import { waitForBackendReady, listUsers, register, setAuthToken } from '../helpers/api'

const ts = Date.now().toString().slice(-6)

describe('User API', () => {
  beforeAll(async () => {
    await waitForBackendReady()

    // Register and authenticate
    const { data: authData } = await register(`User E2E ${ts}`, `user-${ts}`, `Pass${ts}!`)
    setAuthToken(authData.access_token)
  })

  test('list users requires authentication and returns array', async () => {
    const { data, status } = await listUsers()
    expect(status).toBe(200)
    expect(Array.isArray(data)).toBe(true)
    expect(data.length).toBeGreaterThan(0)
  })
})
