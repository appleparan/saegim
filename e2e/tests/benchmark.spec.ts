import { test, expect } from '@playwright/test'
import {
  waitForBackendReady,
  healthCheck,
  createProject,
  getProject,
  listProjects,
  uploadPdf,
  getDocument,
  listDocuments,
  listPages,
  getPage,
  updateAnnotation,
  updatePageAttributes,
  addElement,
  deleteElement,
  exportProject,
  deleteDocument,
  deleteProject,
} from '../helpers/api'
import { ensureTestPdf, getTestPdfPath } from '../helpers/pdf'
import { BenchmarkCollector } from '../helpers/timer'

const benchmark = new BenchmarkCollector()

test.describe.serial('API Benchmarks', () => {
  let projectId: string
  let documentId: string
  let pageId: string

  test.beforeAll(async () => {
    await waitForBackendReady()
    await ensureTestPdf()
  })

  test.afterAll(async () => {
    benchmark.printSummary()
    const path = benchmark.save()
    console.log(`Benchmark results saved to: ${path}`)
  })

  test('health check', async () => {
    const { status, duration } = await healthCheck()
    expect(status).toBe(200)
    benchmark.record('GET /health', duration)
  })

  test('create project', async () => {
    const { data, duration } = await createProject(
      `Benchmark ${Date.now()}`,
      'Benchmark test project',
    )
    expect(data.id).toBeTruthy()
    projectId = data.id
    benchmark.record('POST /projects', duration)
  })

  test('get project', async () => {
    const { data, duration } = await getProject(projectId)
    expect(data.id).toBe(projectId)
    benchmark.record('GET /projects/:id', duration)
  })

  test('list projects', async () => {
    const { data, duration } = await listProjects()
    expect(data.length).toBeGreaterThan(0)
    benchmark.record('GET /projects', duration)
  })

  test('upload PDF', async () => {
    const { data, duration } = await uploadPdf(projectId, getTestPdfPath())
    expect(data.id).toBeTruthy()
    expect(data.total_pages).toBeGreaterThan(0)
    documentId = data.id
    benchmark.record('POST /projects/:id/documents (PDF upload)', duration)
  })

  test('get document', async () => {
    const { data, duration } = await getDocument(documentId)
    expect(data.id).toBe(documentId)
    benchmark.record('GET /documents/:id', duration)
  })

  test('list documents', async () => {
    const { data, duration } = await listDocuments(projectId)
    expect(data.length).toBeGreaterThan(0)
    benchmark.record('GET /projects/:id/documents', duration)
  })

  test('list pages', async () => {
    const { data, duration } = await listPages(documentId)
    expect(data.length).toBeGreaterThan(0)
    pageId = data[0].id
    benchmark.record('GET /documents/:id/pages', duration)
  })

  test('get page', async () => {
    const { data, duration } = await getPage(pageId)
    expect(data.id).toBe(pageId)
    benchmark.record('GET /pages/:id', duration)
  })

  test('update annotation', async () => {
    const annotationData = {
      layout_dets: [
        {
          category_type: 'text_block',
          poly: [100, 100, 400, 100, 400, 300, 100, 300],
          ignore: false,
          order: 0,
          anno_id: 0,
          text: 'Benchmark test',
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
    }

    const { data, duration } = await updateAnnotation(pageId, annotationData)
    expect(data.annotation_data).toBeTruthy()
    benchmark.record('PUT /pages/:id (annotation)', duration)
  })

  test('update page attributes', async () => {
    const { data, duration } = await updatePageAttributes(pageId, {
      data_source: 'academic_literature',
      language: 'en',
      layout: 'double_column',
      watermark: false,
      fuzzy_scan: false,
      colorful_background: false,
    })
    expect(data.annotation_data).toBeTruthy()
    benchmark.record('PUT /pages/:id/attributes', duration)
  })

  test('add element', async () => {
    const { data, duration } = await addElement(pageId, {
      category_type: 'title',
      poly: [50, 50, 300, 50, 300, 100, 50, 100],
      text: 'Benchmark title',
    })
    const layoutDets = data.annotation_data.layout_dets as Array<Record<string, unknown>>
    expect(layoutDets.length).toBeGreaterThanOrEqual(2)
    benchmark.record('POST /pages/:id/elements', duration)
  })

  test('delete element', async () => {
    // Get current elements to find one to delete
    const { data: pageData } = await getPage(pageId)
    const layoutDets = pageData.annotation_data.layout_dets as Array<Record<string, unknown>>
    const lastElement = layoutDets[layoutDets.length - 1]
    const annoId = lastElement.anno_id as number

    const { duration } = await deleteElement(pageId, annoId)
    benchmark.record('DELETE /pages/:id/elements/:annoId', duration)
  })

  test('export project', async () => {
    const { data, duration } = await exportProject(projectId)
    expect(data.project_name).toBeTruthy()
    expect(data.total_pages).toBeGreaterThan(0)
    benchmark.record('POST /projects/:id/export', duration)
  })

  test('delete document', async () => {
    const { duration } = await deleteDocument(documentId)
    benchmark.record('DELETE /documents/:id', duration)
  })

  test('delete project', async () => {
    const { duration } = await deleteProject(projectId)
    benchmark.record('DELETE /projects/:id', duration)
  })
})
