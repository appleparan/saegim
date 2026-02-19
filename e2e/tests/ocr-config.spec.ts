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

test.describe.serial('OCR Config API (engine_type based)', () => {
  test.beforeAll(async () => {
    await waitForBackendReady()
    const { data } = await createProject(`OCR Config E2E ${Date.now()}`, 'OCR config test')
    projectId = data.id
  })

  test('01 - default OCR config is pymupdf', async () => {
    const { data, status } = await getOcrConfig(projectId)
    expect(status).toBe(200)
    expect(data.engine_type).toBe('pymupdf')
  })

  test('02 - update to commercial_api with gemini', async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      engine_type: 'commercial_api',
      commercial_api: { provider: 'gemini', api_key: 'test-key', model: 'gemini-2.0-flash' },
    })
    expect(status).toBe(200)
    expect(data.engine_type).toBe('commercial_api')
    expect(data.commercial_api).toEqual({
      provider: 'gemini',
      api_key: 'test-key',
      model: 'gemini-2.0-flash',
    })
  })

  test('03 - update to commercial_api with vllm', async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      engine_type: 'commercial_api',
      commercial_api: {
        provider: 'vllm',
        host: 'gpu-server',
        port: 8000,
        model: 'allenai/olmOCR-2-7B-1025',
      },
    })
    expect(status).toBe(200)
    expect(data.engine_type).toBe('commercial_api')
    expect(data.commercial_api).toEqual({
      provider: 'vllm',
      host: 'gpu-server',
      port: 8000,
      model: 'allenai/olmOCR-2-7B-1025',
    })
  })

  test('04 - update to integrated_server', async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      engine_type: 'integrated_server',
      integrated_server: { url: 'http://localhost:18811' },
    })
    expect(status).toBe(200)
    expect(data.engine_type).toBe('integrated_server')
    expect(data.integrated_server).toEqual({ url: 'http://localhost:18811' })
  })

  test('05 - update to split_pipeline with gemini OCR', async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      engine_type: 'split_pipeline',
      split_pipeline: {
        layout_server_url: 'http://localhost:18811',
        ocr_provider: 'gemini',
        ocr_api_key: 'test-key',
        ocr_model: 'gemini-2.0-flash',
      },
    })
    expect(status).toBe(200)
    expect(data.engine_type).toBe('split_pipeline')
    expect(data.split_pipeline).toEqual({
      layout_server_url: 'http://localhost:18811',
      ocr_provider: 'gemini',
      ocr_api_key: 'test-key',
      ocr_model: 'gemini-2.0-flash',
    })
  })

  test('06 - revert to pymupdf', async () => {
    const { data, status } = await updateOcrConfig(projectId, {
      engine_type: 'pymupdf',
    })
    expect(status).toBe(200)
    expect(data.engine_type).toBe('pymupdf')
  })

  test('07 - get config reflects last update', async () => {
    const { data } = await getOcrConfig(projectId)
    expect(data.engine_type).toBe('pymupdf')
  })

  test('08 - validation: commercial_api without sub-config is 422', async () => {
    const { status } = await updateOcrConfig(projectId, {
      engine_type: 'commercial_api',
    })
    expect(status).toBe(422)
  })

  test('09 - validation: integrated_server without sub-config is 422', async () => {
    const { status } = await updateOcrConfig(projectId, {
      engine_type: 'integrated_server',
    })
    expect(status).toBe(422)
  })

  test('10 - validation: split_pipeline without sub-config is 422', async () => {
    const { status } = await updateOcrConfig(projectId, {
      engine_type: 'split_pipeline',
    })
    expect(status).toBe(422)
  })

  test('11 - connection test for pymupdf always succeeds', async () => {
    const { data, status } = await testOcrConnection(projectId, {
      engine_type: 'pymupdf',
    })
    expect(status).toBe(200)
    expect(data.success).toBe(true)
  })

  test('12 - connection test for unreachable integrated_server fails', async () => {
    const { data, status } = await testOcrConnection(projectId, {
      engine_type: 'integrated_server',
      integrated_server: { url: 'http://nonexistent-host:18811' },
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
