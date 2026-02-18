import { test, expect } from '@playwright/test'
import {
  waitForBackendReady,
  createProject,
  getOcrConfig,
  updateOcrConfig,
  testOcrConnection,
  deleteProject,
} from '../helpers/api'

let projectId: string

test.describe.serial('OCR Config API (2-stage pipeline)', () => {
  test.beforeAll(async () => {
    await waitForBackendReady()
    const { data } = await createProject(`OCR Config E2E ${Date.now()}`, 'OCR config test')
    projectId = data.id
  })

  test('01 - default OCR config is pymupdf', async () => {
    const { data, status } = await getOcrConfig(projectId)
    expect(status).toBe(200)
    expect(data.layout_provider).toBe('pymupdf')
    expect(data.ocr_provider).toBeNull()
  })

  test('02 - update to ppstructure + ppocr', async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      layout_provider: 'ppstructure',
      ocr_provider: 'ppocr',
      ppstructure: { host: 'localhost', port: 18811 },
    })
    expect(status).toBe(200)
    expect(data.layout_provider).toBe('ppstructure')
    expect(data.ocr_provider).toBe('ppocr')
    expect(data.ppstructure).toEqual({ host: 'localhost', port: 18811 })
  })

  test('03 - update to ppstructure + gemini', async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      layout_provider: 'ppstructure',
      ocr_provider: 'gemini',
      ppstructure: { host: 'localhost', port: 18811 },
      gemini: { api_key: 'test-key', model: 'gemini-2.0-flash' },
    })
    expect(status).toBe(200)
    expect(data.layout_provider).toBe('ppstructure')
    expect(data.ocr_provider).toBe('gemini')
    expect(data.gemini).toEqual({ api_key: 'test-key', model: 'gemini-2.0-flash' })
  })

  test('04 - update to ppstructure + olmocr', async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      layout_provider: 'ppstructure',
      ocr_provider: 'olmocr',
      ppstructure: { host: 'gpu-server', port: 18811 },
      vllm: { host: 'gpu-server', port: 8000, model: 'allenai/olmOCR-2-7B-1025' },
    })
    expect(status).toBe(200)
    expect(data.ocr_provider).toBe('olmocr')
    expect(data.vllm).toEqual({
      host: 'gpu-server',
      port: 8000,
      model: 'allenai/olmOCR-2-7B-1025',
    })
  })

  test('05 - revert to pymupdf', async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      layout_provider: 'pymupdf',
    })
    expect(status).toBe(200)
    expect(data.layout_provider).toBe('pymupdf')
    expect(data.ocr_provider).toBeUndefined()
  })

  test('06 - get config reflects last update', async () => {
    const { data } = await getOcrConfig(projectId)
    expect(data.layout_provider).toBe('pymupdf')
  })

  test('07 - validation: ppstructure without ocr_provider is 422', async () => {
    const { status } = await updateOcrConfig(projectId, {
      layout_provider: 'ppstructure',
      ppstructure: { host: 'localhost', port: 18811 },
    })
    expect(status).toBe(422)
  })

  test('08 - validation: ppstructure without ppstructure config is 422', async () => {
    const { status } = await updateOcrConfig(projectId, {
      layout_provider: 'ppstructure',
      ocr_provider: 'ppocr',
    })
    expect(status).toBe(422)
  })

  test('09 - validation: gemini without gemini config is 422', async () => {
    const { status } = await updateOcrConfig(projectId, {
      layout_provider: 'ppstructure',
      ocr_provider: 'gemini',
      ppstructure: { host: 'localhost', port: 18811 },
    })
    expect(status).toBe(422)
  })

  test('10 - validation: olmocr without vllm config is 422', async () => {
    const { status } = await updateOcrConfig(projectId, {
      layout_provider: 'ppstructure',
      ocr_provider: 'olmocr',
      ppstructure: { host: 'localhost', port: 18811 },
    })
    expect(status).toBe(422)
  })

  test('11 - connection test for pymupdf always succeeds', async () => {
    const { data, status } = await testOcrConnection(projectId, {
      layout_provider: 'pymupdf',
    })
    expect(status).toBe(200)
    expect(data.success).toBe(true)
  })

  test('12 - connection test for unreachable ppstructure fails', async () => {
    const { data, status } = await testOcrConnection(projectId, {
      layout_provider: 'ppstructure',
      ocr_provider: 'ppocr',
      ppstructure: { host: 'nonexistent-host', port: 18811 },
    })
    expect(status).toBe(200)
    expect(data.success).toBe(false)
    expect(data.message).toBeTruthy()
  })

  test.afterAll(async () => {
    try {
      await deleteProject(projectId)
    } catch {
      // Ignore cleanup errors
    }
  })
})
