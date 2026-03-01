import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  waitForBackendReady,
  createProject,
  uploadPdf,
  listPages,
  getPage,
  updateAnnotation,
  addRelation,
  deleteRelation,
  deleteDocument,
  deleteProject,
} from '../helpers/api'
import { ensureTestPdf, getTestPdfPath } from '../helpers/pdf'

describe('Relation CRUD', () => {
  let projectId: string
  let documentId: string
  let pageId: string

  beforeAll(async () => {
    await waitForBackendReady()
    await ensureTestPdf()

    // Create project, upload PDF, and set up annotation with two elements
    const { data: project } = await createProject(`Relation E2E ${Date.now()}`, 'Relation test')
    projectId = project.id

    const { data: doc } = await uploadPdf(projectId, getTestPdfPath())
    documentId = doc.id

    const { data: pages } = await listPages(documentId)
    pageId = pages[0].id

    // Seed annotation_data with two elements so we can create relations between them
    await updateAnnotation(pageId, {
      layout_dets: [
        {
          category_type: 'figure',
          poly: [100, 100, 400, 100, 400, 400, 100, 400],
          ignore: false,
          order: 0,
          anno_id: 0,
          text: '',
          attribute: {},
          line_with_spans: [],
          merge_list: [],
          latex: '',
          html: '',
        },
        {
          category_type: 'figure_caption',
          poly: [100, 410, 400, 410, 400, 450, 100, 450],
          ignore: false,
          order: 1,
          anno_id: 1,
          text: 'Figure 1: Test figure',
          attribute: {},
          line_with_spans: [],
          merge_list: [],
          latex: '',
          html: '',
        },
        {
          category_type: 'table',
          poly: [500, 100, 800, 100, 800, 400, 500, 400],
          ignore: false,
          order: 2,
          anno_id: 2,
          text: '',
          attribute: {},
          line_with_spans: [],
          merge_list: [],
          latex: '',
          html: '',
        },
      ],
      page_attribute: {
        data_source: 'academic_literature',
        language: 'en',
        layout: 'single_column',
        watermark: false,
        fuzzy_scan: false,
        colorful_background: false,
      },
      extra: { relation: [] },
    })
  })

  afterAll(async () => {
    if (documentId) await deleteDocument(documentId)
    if (projectId) await deleteProject(projectId)
  })

  test('add a figure_caption relation', async () => {
    const { data, status } = await addRelation(pageId, 0, 1, 'figure_caption')
    expect(status).toBe(201)

    const relations = (data.annotation_data as Record<string, unknown>).extra as Record<
      string,
      unknown
    >
    const relationList = (relations.relation ?? []) as Array<Record<string, unknown>>
    expect(relationList).toHaveLength(1)
    expect(relationList[0]).toMatchObject({
      source_anno_id: 0,
      target_anno_id: 1,
      relation_type: 'figure_caption',
    })
  })

  test('add a second relation (parent_son)', async () => {
    const { data, status } = await addRelation(pageId, 0, 2, 'parent_son')
    expect(status).toBe(201)

    const relations = (data.annotation_data as Record<string, unknown>).extra as Record<
      string,
      unknown
    >
    const relationList = (relations.relation ?? []) as Array<Record<string, unknown>>
    expect(relationList).toHaveLength(2)
  })

  test('duplicate relation returns 409', async () => {
    const { status } = await addRelation(pageId, 0, 1, 'figure_caption')
    expect(status).toBe(409)
  })

  test('self-referencing relation returns 409', async () => {
    const { status } = await addRelation(pageId, 0, 0, 'parent_son')
    expect(status).toBe(409)
  })

  test('relation with non-existent element returns 409', async () => {
    const { status } = await addRelation(pageId, 0, 999, 'parent_son')
    expect(status).toBe(409)
  })

  test('verify relations persisted via getPage', async () => {
    const { data } = await getPage(pageId)
    const extra = (data.annotation_data as Record<string, unknown>).extra as Record<
      string,
      unknown
    >
    const relationList = (extra.relation ?? []) as Array<Record<string, unknown>>
    expect(relationList).toHaveLength(2)
  })

  test('delete a relation', async () => {
    const { data, status } = await deleteRelation(pageId, 0, 1)
    expect(status).toBe(200)

    const extra = (data.annotation_data as Record<string, unknown>).extra as Record<
      string,
      unknown
    >
    const relationList = (extra.relation ?? []) as Array<Record<string, unknown>>
    expect(relationList).toHaveLength(1)
    expect(relationList[0]).toMatchObject({
      source_anno_id: 0,
      target_anno_id: 2,
      relation_type: 'parent_son',
    })
  })

  test('delete non-existent relation is idempotent (200)', async () => {
    const { data, status } = await deleteRelation(pageId, 0, 1)
    expect(status).toBe(200)

    // Relation array should still have 1 element (the parent_son one)
    const extra = (data.annotation_data as Record<string, unknown>).extra as Record<
      string,
      unknown
    >
    const relationList = (extra.relation ?? []) as Array<Record<string, unknown>>
    expect(relationList).toHaveLength(1)
  })

  test('delete remaining relation leaves empty array', async () => {
    const { data, status } = await deleteRelation(pageId, 0, 2)
    expect(status).toBe(200)

    const extra = (data.annotation_data as Record<string, unknown>).extra as Record<
      string,
      unknown
    >
    const relationList = (extra.relation ?? []) as Array<Record<string, unknown>>
    expect(relationList).toHaveLength(0)
  })
})
