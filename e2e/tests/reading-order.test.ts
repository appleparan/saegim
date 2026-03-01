import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  waitForBackendReady,
  createProject,
  uploadPdf,
  listDocuments,
  listPages,
  getPage,
  updateAnnotation,
  addElement,
  updateReadingOrder,
  deleteProject,
} from '../helpers/api'
import { ensureTestPdf, getTestPdfPath } from '../helpers/pdf'

describe('Reading Order', () => {
  let projectId: string
  let pageId: string

  beforeAll(async () => {
    await waitForBackendReady()
    await ensureTestPdf()

    const { data: project } = await createProject(
      `ReadingOrder ${Date.now()}`,
      'Reading order E2E test',
    )
    projectId = project.id

    const { data: upload } = await uploadPdf(projectId, getTestPdfPath())
    const documentId = upload.id

    // Wait for document to be ready
    const deadline = Date.now() + 120_000
    while (Date.now() < deadline) {
      const { data: docs } = await listDocuments(projectId)
      if (docs[0]?.status === 'ready') break
      await new Promise((r) => setTimeout(r, 2_000))
    }

    const { data: pages } = await listPages(documentId)
    pageId = pages[0].id

    // Set up initial annotation with 3 elements
    await updateAnnotation(pageId, {
      layout_dets: [
        {
          category_type: 'title',
          poly: [50, 50, 300, 50, 300, 100, 50, 100],
          ignore: false,
          order: 0,
          anno_id: 0,
          text: 'Title',
          attribute: {},
        },
        {
          category_type: 'text_block',
          poly: [50, 120, 300, 120, 300, 400, 50, 400],
          ignore: false,
          order: 1,
          anno_id: 1,
          text: 'Body text',
          attribute: {},
        },
        {
          category_type: 'figure',
          poly: [350, 120, 600, 120, 600, 400, 350, 400],
          ignore: false,
          order: 2,
          anno_id: 2,
          text: '',
          attribute: {},
        },
      ],
      page_attribute: {
        language: 'en',
        layout: 'single_column',
      },
      extra: { relation: [] },
    })
  })

  afterAll(async () => {
    try {
      await deleteProject(projectId)
    } catch {
      // cleanup best-effort
    }
  })

  test('01 - swap reading order of two elements', async () => {
    const { data, status } = await updateReadingOrder(pageId, { '0': 2, '2': 0 })

    expect(status).toBe(200)

    const layoutDets = data.annotation_data.layout_dets as Array<Record<string, unknown>>
    const el0 = layoutDets.find((el) => el.anno_id === 0)
    const el2 = layoutDets.find((el) => el.anno_id === 2)

    expect(el0?.order).toBe(2)
    expect(el2?.order).toBe(0)
  })

  test('02 - unchanged elements retain their order', async () => {
    const { data } = await getPage(pageId)
    const layoutDets = data.annotation_data.layout_dets as Array<Record<string, unknown>>
    const el1 = layoutDets.find((el) => el.anno_id === 1)

    expect(el1?.order).toBe(1)
  })

  test('03 - full reorder of all elements', async () => {
    const { data, status } = await updateReadingOrder(pageId, {
      '0': 1,
      '1': 2,
      '2': 0,
    })

    expect(status).toBe(200)

    const layoutDets = data.annotation_data.layout_dets as Array<Record<string, unknown>>
    const orders: Record<number, number> = {}
    for (const el of layoutDets) {
      orders[el.anno_id as number] = el.order as number
    }

    expect(orders).toEqual({ 0: 1, 1: 2, 2: 0 })
  })

  test('04 - reject duplicate order values (422)', async () => {
    const { status } = await updateReadingOrder(pageId, { '0': 1, '1': 1 })

    expect(status).toBe(422)
  })

  test('05 - reject negative order values (422)', async () => {
    const { status } = await updateReadingOrder(pageId, { '0': -1 })

    expect(status).toBe(422)
  })

  test('06 - reject non-existent anno_id (404)', async () => {
    const { status } = await updateReadingOrder(pageId, { '999': 0 })

    expect(status).toBe(404)
  })

  test('07 - order persists after adding new element', async () => {
    // Set known order first
    await updateReadingOrder(pageId, { '0': 0, '1': 1, '2': 2 })

    // Add a new element
    const { data } = await addElement(pageId, {
      category_type: 'table',
      poly: [50, 450, 600, 450, 600, 700, 50, 700],
      text: '',
    })

    const layoutDets = data.annotation_data.layout_dets as Array<Record<string, unknown>>

    // Original orders should be unchanged
    const el0 = layoutDets.find((el) => el.anno_id === 0)
    const el1 = layoutDets.find((el) => el.anno_id === 1)
    const el2 = layoutDets.find((el) => el.anno_id === 2)

    expect(el0?.order).toBe(0)
    expect(el1?.order).toBe(1)
    expect(el2?.order).toBe(2)

    // New element gets next order
    const newEl = layoutDets.find((el) => (el.anno_id as number) >= 3)
    expect(newEl).toBeTruthy()
    expect(newEl?.order).toBe(3)
  })

  test('08 - empty order_map is a valid no-op', async () => {
    const { data: before } = await getPage(pageId)
    const { status } = await updateReadingOrder(pageId, {})
    const { data: after } = await getPage(pageId)

    expect(status).toBe(200)

    const beforeDets = before.annotation_data.layout_dets as Array<Record<string, unknown>>
    const afterDets = after.annotation_data.layout_dets as Array<Record<string, unknown>>

    for (const bEl of beforeDets) {
      const aEl = afterDets.find((el) => el.anno_id === bEl.anno_id)
      expect(aEl?.order).toBe(bEl.order)
    }
  })
})
