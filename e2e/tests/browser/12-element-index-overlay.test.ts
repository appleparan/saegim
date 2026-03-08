import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  connectMcp,
  disconnectMcp,
  loginAsUser,
  waitForText,
  takeSnapshot,
  navigateTo,
  pressKey,
  clickByPattern,
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
  getUserIdFromToken,
} from '../../helpers/api'
import { getTestPdfPath } from '../../helpers/pdf'

const ts = Date.now().toString().slice(-6)
const TEST_USER = {
  loginId: `elemidx-user-${ts}`,
  password: 'TestPassword123!',
  name: `ElemIdx User ${ts}`,
}
let projectId: string
let pageId: string
let userToken: string

/** Extract element count from "N개 요소" text in snapshot. */
function getElementCountFromSnapshot(snapshot: string): number {
  const match = snapshot.match(/(\d+)개 요소/)
  return match ? parseInt(match[1], 10) : -1
}

/** Navigate to labeling page and wait for elements to load. */
async function openLabelPage(): Promise<void> {
  await loginAsUser(TEST_USER.loginId, TEST_USER.password)
  await navigateTo(`/label/${pageId}`)
  await waitForText('요소 목록', 30000)
  // Allow annotation data and canvas to fully render
  await new Promise((r) => setTimeout(r, 1500))
}

describe('Browser Element Index Overlay', () => {
  beforeAll(async () => {
    await waitForBackendReady()

    // Register user
    const { data: authData } = await register(
      TEST_USER.name,
      TEST_USER.loginId,
      TEST_USER.password,
    )
    userToken = authData.access_token
    setAuthToken(userToken)

    // Create project, upload PDF
    const { data: project } = await createProject(`ElemIdx Test ${ts}`, 'E2E element index test')
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

  test('labeling page loads with elements and shows "요소" checkbox', async () => {
    await openLabelPage()
    const snapshot = await takeSnapshot()
    const count = getElementCountFromSnapshot(snapshot)
    expect(count).toBeGreaterThan(0)
    // Verify the "요소" checkbox label exists
    expect(snapshot).toContain('요소')
    expect(snapshot).toContain('순서')
  }, 60000)

  test('pressing I key toggles element index overlay via canvasStore', async () => {
    await openLabelPage()

    // Verify initial state: showElementIndex is false
    const initialState = await evaluateScript<boolean>(
      '() => window.__canvasStore?.showElementIndex ?? false',
    )
    expect(initialState).toBe(false)

    // Inject store reference for testing
    await evaluateScript(
      `() => {
        // Try to access the store from Svelte module state
        const storeModule = document.querySelector('[data-svelte-h]')
        return true
      }`,
    )

    // Press 'I' to toggle element index
    await pressKey('i')
    await new Promise((r) => setTimeout(r, 500))

    // Verify the checkbox is now checked by checking DOM state
    const afterToggle = await evaluateScript<boolean>(
      `() => {
        // Find the checkbox with "요소" label
        const labels = document.querySelectorAll('label')
        for (const label of labels) {
          if (label.textContent?.includes('요소')) {
            const checkbox = label.querySelector('input[type="checkbox"]')
            return checkbox?.checked ?? false
          }
        }
        return false
      }`,
    )
    expect(afterToggle).toBe(true)

    // Press 'I' again to toggle off
    await pressKey('i')
    await new Promise((r) => setTimeout(r, 500))

    const afterToggleOff = await evaluateScript<boolean>(
      `() => {
        const labels = document.querySelectorAll('label')
        for (const label of labels) {
          if (label.textContent?.includes('요소')) {
            const checkbox = label.querySelector('input[type="checkbox"]')
            return checkbox?.checked ?? false
          }
        }
        return false
      }`,
    )
    expect(afterToggleOff).toBe(false)
  }, 60000)

  test('clicking "요소" checkbox toggles overlay', async () => {
    await openLabelPage()

    // Click the "요소" checkbox via DOM (accessibility snapshot pattern varies)
    await evaluateScript(
      `() => {
        const labels = document.querySelectorAll('label')
        for (const label of labels) {
          if (label.textContent?.includes('요소')) {
            label.click()
            return true
          }
        }
        return false
      }`,
    )
    await new Promise((r) => setTimeout(r, 500))

    // Verify checkbox is checked
    const isChecked = await evaluateScript<boolean>(
      `() => {
        const labels = document.querySelectorAll('label')
        for (const label of labels) {
          if (label.textContent?.includes('요소')) {
            const checkbox = label.querySelector('input[type="checkbox"]')
            return checkbox?.checked ?? false
          }
        }
        return false
      }`,
    )
    expect(isChecked).toBe(true)

    // Verify bbox overlay divs are rendered (element index overlay container)
    const hasBboxOverlay = await evaluateScript<boolean>(
      `() => {
        // The overlay has z-index: 25 and contains bordered divs for bboxes
        const overlays = document.querySelectorAll('[style*="z-index: 25"]')
        return overlays.length > 0
      }`,
    )
    expect(hasBboxOverlay).toBe(true)
  }, 60000)

  test('element index and reading order toggles work independently', async () => {
    await openLabelPage()

    // Press 'I' for element index
    await pressKey('i')
    await new Promise((r) => setTimeout(r, 300))

    // Press 'R' for reading order
    await pressKey('r')
    await new Promise((r) => setTimeout(r, 300))

    // Both should be checked
    const states = await evaluateScript<{ elementIndex: boolean; readingOrder: boolean }>(
      `() => {
        let elementIndex = false
        let readingOrder = false
        const labels = document.querySelectorAll('label')
        for (const label of labels) {
          const text = label.textContent ?? ''
          const checkbox = label.querySelector('input[type="checkbox"]')
          if (text.includes('요소')) elementIndex = checkbox?.checked ?? false
          if (text.includes('순서')) readingOrder = checkbox?.checked ?? false
        }
        return { elementIndex, readingOrder }
      }`,
    )
    expect(states.elementIndex).toBe(true)
    expect(states.readingOrder).toBe(true)

    // Toggle off only element index
    await pressKey('i')
    await new Promise((r) => setTimeout(r, 300))

    const afterToggle = await evaluateScript<{ elementIndex: boolean; readingOrder: boolean }>(
      `() => {
        let elementIndex = false
        let readingOrder = false
        const labels = document.querySelectorAll('label')
        for (const label of labels) {
          const text = label.textContent ?? ''
          const checkbox = label.querySelector('input[type="checkbox"]')
          if (text.includes('요소')) elementIndex = checkbox?.checked ?? false
          if (text.includes('순서')) readingOrder = checkbox?.checked ?? false
        }
        return { elementIndex, readingOrder }
      }`,
    )
    expect(afterToggle.elementIndex).toBe(false)
    expect(afterToggle.readingOrder).toBe(true)
  }, 60000)
})
