import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  connectMcp,
  disconnectMcp,
  loginAsUser,
  waitForText,
  takeSnapshot,
  navigateTo,
  pressKey,
  callTool,
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
  getUserIdFromToken,
} from '../../helpers/api'
import { getTestPdfPath } from '../../helpers/pdf'

const ts = Date.now().toString().slice(-6)
const TEST_USER = {
  loginId: `undo-user-${ts}`,
  password: 'TestPassword123!',
  name: `Undo User ${ts}`,
}
let projectId: string
let pageId: string
let userToken: string

/** Extract element count from "N개 요소" text in snapshot. */
function getElementCountFromSnapshot(snapshot: string): number {
  const match = snapshot.match(/(\d+)개 요소/)
  return match ? parseInt(match[1], 10) : -1
}

/** Find the first delete button uid from the element list in snapshot. */
function findFirstDeleteButtonUid(snapshot: string): string | null {
  // Delete buttons appear as: button "삭제" with uid=...
  for (const line of snapshot.split('\n')) {
    if (/button "삭제"/.test(line) && /uid=/.test(line)) {
      const match = line.match(/uid=([^\s]+)/)
      if (match) return match[1]
    }
  }
  return null
}

/** Navigate to labeling page and wait for elements to load. */
async function openLabelPage(): Promise<void> {
  await loginAsUser(TEST_USER.loginId, TEST_USER.password)
  await navigateTo(`/label/${pageId}`)
  await waitForText('요소 목록', 30000)
  // Allow annotation data and canvas to fully render
  await new Promise((r) => setTimeout(r, 1500))
}

describe('Browser Labeling Undo/Redo', () => {
  beforeAll(async () => {
    await waitForBackendReady()

    // Register user
    const { data: authData } = await register(TEST_USER.name, TEST_USER.loginId, TEST_USER.password)
    userToken = authData.access_token
    setAuthToken(userToken)

    // Create project, upload PDF
    const { data: project } = await createProject(`Undo Test ${ts}`, 'E2E undo/redo test')
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

    // Get first page, accept extraction so annotation_data is populated
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

  test('labeling page loads with elements from extraction', async () => {
    await openLabelPage()
    const snapshot = await takeSnapshot()
    const count = getElementCountFromSnapshot(snapshot)
    // Auto-extraction should produce at least 1 element
    expect(count).toBeGreaterThan(0)
  }, 60000)

  test('shortcut help shows undo/redo entries', async () => {
    await openLabelPage()

    // Open shortcut help with backtick key
    await pressKey('`')
    await new Promise((r) => setTimeout(r, 500))

    const snapshot = await takeSnapshot()
    expect(snapshot).toContain('실행 취소')
    expect(snapshot).toContain('다시 실행')

    // Close shortcut help
    await pressKey('`')
  }, 60000)

  test('undo/redo does not crash when history is empty', async () => {
    await openLabelPage()

    // Press Ctrl+Z and Ctrl+Shift+Z with empty history — should be no-ops
    await pressKey('Control+z')
    await new Promise((r) => setTimeout(r, 300))
    await pressKey('Control+Shift+z')
    await new Promise((r) => setTimeout(r, 300))

    // Page should still be functional
    const snapshot = await takeSnapshot()
    expect(snapshot).toContain('요소 목록')
  }, 60000)

  test('delete element via delete button then undo with Ctrl+Z restores it', async () => {
    await openLabelPage()

    // Get initial element count
    let snapshot = await takeSnapshot()
    const initialCount = getElementCountFromSnapshot(snapshot)
    if (initialCount <= 0) return // Skip if no elements

    // Find the first delete button and click it to remove the element
    const deleteUid = findFirstDeleteButtonUid(snapshot)
    if (!deleteUid) return // Skip if can't find delete button
    await callTool('click', { uid: deleteUid })
    await new Promise((r) => setTimeout(r, 500))

    // Verify element was deleted
    snapshot = await takeSnapshot()
    const afterDeleteCount = getElementCountFromSnapshot(snapshot)
    expect(afterDeleteCount).toBe(initialCount - 1)

    // Undo with Ctrl+Z
    await pressKey('Control+z')
    await new Promise((r) => setTimeout(r, 500))

    // Verify element was restored
    snapshot = await takeSnapshot()
    const afterUndoCount = getElementCountFromSnapshot(snapshot)
    expect(afterUndoCount).toBe(initialCount)
  }, 90000)

  test('redo with Ctrl+Shift+Z re-applies the undone action', async () => {
    await openLabelPage()

    let snapshot = await takeSnapshot()
    const initialCount = getElementCountFromSnapshot(snapshot)
    if (initialCount <= 0) return

    // Delete via delete button
    const deleteUid = findFirstDeleteButtonUid(snapshot)
    if (!deleteUid) return
    await callTool('click', { uid: deleteUid })
    await new Promise((r) => setTimeout(r, 500))

    // Undo
    await pressKey('Control+z')
    await new Promise((r) => setTimeout(r, 500))

    // Redo
    await pressKey('Control+Shift+z')
    await new Promise((r) => setTimeout(r, 500))

    // Element should be deleted again (redo re-applied delete)
    snapshot = await takeSnapshot()
    const afterRedoCount = getElementCountFromSnapshot(snapshot)
    expect(afterRedoCount).toBe(initialCount - 1)

    // Undo again to restore for next tests
    await pressKey('Control+z')
  }, 90000)
})
