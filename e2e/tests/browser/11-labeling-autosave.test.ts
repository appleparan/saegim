import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  connectMcp,
  disconnectMcp,
  loginAsUser,
  waitForText,
  takeSnapshot,
  navigateTo,
  callTool,
  uidFromSnapshot,
  evaluateScript,
} from '../../helpers/mcp'
import {
  waitForBackendReady,
  register,
  setAuthToken,
  createProject,
  uploadPdf,
  listDocuments,
  listPages,
  assignPage,
  forceAcceptExtraction,
  deleteProject,
  getDocument,
  getPage,
  getUserIdFromToken,
} from '../../helpers/api'
import { getTestPdfPath } from '../../helpers/pdf'

const ts = Date.now().toString().slice(-6)
const TEST_USER = {
  loginId: `autosave-user-${ts}`,
  password: 'TestPassword123!',
  name: `Autosave User ${ts}`,
}
let projectId: string
let pageId: string
let userToken: string

/** Navigate to labeling page and wait for elements to load. */
async function openLabelPage(): Promise<void> {
  await loginAsUser(TEST_USER.loginId, TEST_USER.password)
  await navigateTo(`/label/${pageId}`)
  await waitForText('요소 목록', 30000)
  // Allow annotation data and canvas to fully render
  await new Promise((r) => setTimeout(r, 1500))
}

/** Find the first delete button uid from the element list in snapshot. */
function findFirstDeleteButtonUid(snapshot: string): string | null {
  for (const line of snapshot.split('\n')) {
    if (/button "삭제"/.test(line) && /uid=/.test(line)) {
      const match = line.match(/uid=([^\s]+)/)
      if (match) return match[1]
    }
  }
  return null
}

describe('Browser Labeling Auto-save', () => {
  beforeAll(async () => {
    await waitForBackendReady()

    // Register user
    const { data: authData } = await register(TEST_USER.name, TEST_USER.loginId, TEST_USER.password)
    userToken = authData.access_token
    setAuthToken(userToken)

    // Create project, upload PDF
    const { data: project } = await createProject(`Autosave Test ${ts}`, 'E2E auto-save test')
    projectId = project.id
    const { data: docData } = await uploadPdf(projectId, getTestPdfPath())

    // Wait for document processing
    let docReady = false
    for (let i = 0; i < 30; i++) {
      const { data: doc } = await getDocument(docData.id)
      if (doc.status === 'ready') {
        docReady = true
        break
      }
      await new Promise((r) => setTimeout(r, 3000))
    }
    if (!docReady) throw new Error('Document processing timed out')

    // Get first page, accept extraction, assign to user
    const { data: docs } = await listDocuments(projectId)
    const { data: pages } = await listPages(docs[0].id)
    pageId = pages[0].id
    const userId = getUserIdFromToken(userToken)

    await forceAcceptExtraction(pageId)
    await assignPage(pageId, userId)

    await connectMcp()
  }, 120000)

  afterAll(async () => {
    await disconnectMcp()
    try {
      setAuthToken(userToken)
      await deleteProject(projectId)
    } catch {
      // cleanup best-effort
    }
  })

  test('auto-save toggle is visible on labeling page', async () => {
    await openLabelPage()
    const snapshot = await takeSnapshot()
    expect(snapshot).toContain('자동 저장')
    expect(snapshot).toMatch(/switch "자동 저장"/)
  }, 60000)

  test('auto-save toggle can be enabled and shows checked state', async () => {
    await openLabelPage()

    // Find and click the auto-save switch
    let snapshot = await takeSnapshot()
    const switchUid = uidFromSnapshot(snapshot, /switch "자동 저장"/)
    await callTool('click', { uid: switchUid })
    await new Promise((r) => setTimeout(r, 300))

    // Verify switch is now checked
    snapshot = await takeSnapshot()
    expect(snapshot).toMatch(/switch "자동 저장" checked/)
  }, 60000)

  test('auto-save persists enabled state across page reload', async () => {
    await openLabelPage()

    // Enable auto-save
    let snapshot = await takeSnapshot()
    if (!snapshot.includes('switch "자동 저장" checked')) {
      const switchUid = uidFromSnapshot(snapshot, /switch "자동 저장"/)
      await callTool('click', { uid: switchUid })
      await new Promise((r) => setTimeout(r, 300))
    }

    // Verify localStorage was set
    const stored = await evaluateScript<string>(
      '() => localStorage.getItem("saegim:autosave:enabled")',
    )
    expect(stored).toBe('true')

    // Reload page
    await navigateTo(`/label/${pageId}`)
    await waitForText('요소 목록', 30000)
    await new Promise((r) => setTimeout(r, 1500))

    // Verify auto-save is still enabled after reload
    snapshot = await takeSnapshot()
    expect(snapshot).toMatch(/switch "자동 저장" checked/)
  }, 60000)

  test('auto-save saves dirty data within 30 seconds', async () => {
    await openLabelPage()

    // Enable auto-save if not already
    let snapshot = await takeSnapshot()
    if (!snapshot.includes('switch "자동 저장" checked')) {
      const switchUid = uidFromSnapshot(snapshot, /switch "자동 저장"/)
      await callTool('click', { uid: switchUid })
      await new Promise((r) => setTimeout(r, 300))
    }

    // Get initial element count
    snapshot = await takeSnapshot()
    const initialMatch = snapshot.match(/(\d+)개 요소/)
    const initialCount = initialMatch ? parseInt(initialMatch[1], 10) : 0
    if (initialCount <= 0) return // Skip if no elements

    // Delete an element to make dirty
    const deleteUid = findFirstDeleteButtonUid(snapshot)
    if (!deleteUid) return
    await callTool('click', { uid: deleteUid })
    await new Promise((r) => setTimeout(r, 500))

    // Verify element was deleted (dirty state)
    snapshot = await takeSnapshot()
    const afterDeleteMatch = snapshot.match(/(\d+)개 요소/)
    const afterDeleteCount = afterDeleteMatch ? parseInt(afterDeleteMatch[1], 10) : 0
    expect(afterDeleteCount).toBe(initialCount - 1)

    // Wait for auto-save (up to 35 seconds to account for interval timing)
    let saved = false
    for (let i = 0; i < 7; i++) {
      await new Promise((r) => setTimeout(r, 5000))
      snapshot = await takeSnapshot()
      // Check for last saved timestamp (HH:MM format in Korean)
      if (/\d{1,2}:\d{2}/.test(snapshot) && snapshot.includes('switch "자동 저장" checked')) {
        // Verify data was actually saved via API
        setAuthToken(userToken)
        const { data: pageData } = await getPage(pageId)
        const savedElementCount = pageData.annotation_data?.layout_dets?.length ?? 0
        if (savedElementCount === afterDeleteCount) {
          saved = true
          break
        }
      }
    }

    expect(saved).toBe(true)
  }, 60000)

  test('auto-save toggle can be disabled', async () => {
    await openLabelPage()

    // Enable auto-save first
    let snapshot = await takeSnapshot()
    if (!snapshot.includes('switch "자동 저장" checked')) {
      const switchUid = uidFromSnapshot(snapshot, /switch "자동 저장"/)
      await callTool('click', { uid: switchUid })
      await new Promise((r) => setTimeout(r, 300))
    }

    // Disable auto-save
    snapshot = await takeSnapshot()
    const switchUid = uidFromSnapshot(snapshot, /switch "자동 저장" checked/)
    await callTool('click', { uid: switchUid })
    await new Promise((r) => setTimeout(r, 300))

    // Verify switch is unchecked
    snapshot = await takeSnapshot()
    expect(snapshot).not.toMatch(/switch "자동 저장" checked/)

    // Verify localStorage was updated
    const stored = await evaluateScript<string>(
      '() => localStorage.getItem("saegim:autosave:enabled")',
    )
    expect(stored).toBe('false')
  }, 60000)
})
