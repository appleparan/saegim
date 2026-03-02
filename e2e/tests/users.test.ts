import { describe, test, expect, beforeAll } from 'vitest'
import { waitForBackendReady, createUser, listUsers } from '../helpers/api'

describe('User CRUD', () => {
  beforeAll(async () => {
    await waitForBackendReady()
  })

  const uniqueEmail = `e2e-user-${Date.now()}@test.com`

  test('create a new user with default role', async () => {
    const { data, status } = await createUser('E2E Test User', uniqueEmail)
    expect(status).toBe(201)
    expect(data.id).toBeTruthy()
    expect(data.name).toBe('E2E Test User')
    expect(data.email).toBe(uniqueEmail)
    expect(data.role).toBe('annotator')
    expect(data.created_at).toBeTruthy()
  })

  test('create a user with explicit role', async () => {
    const email = `e2e-admin-${Date.now()}@test.com`
    const { data, status } = await createUser('E2E Admin', email, 'admin')
    expect(status).toBe(201)
    expect(data.role).toBe('admin')
  })

  test('duplicate email returns 409', async () => {
    const { status } = await createUser('Duplicate User', uniqueEmail)
    expect(status).toBe(409)
  })

  test('list users includes created users', async () => {
    const { data, status } = await listUsers()
    expect(status).toBe(200)
    expect(Array.isArray(data)).toBe(true)

    const found = data.find((u) => u.email === uniqueEmail)
    expect(found).toBeTruthy()
    expect(found!.name).toBe('E2E Test User')
  })
})
