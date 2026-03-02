import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import {
  waitForBackendReady,
  createProject,
  getOcrConfig,
  addEngine,
  updateEngine,
  deleteEngine,
  setDefaultEngine,
  testOcrConnection,
  getAvailableEngines,
  deleteProject,
} from '../helpers/api'

let projectId: string

describe('OCR Config API (multi-instance engines)', () => {
  beforeAll(async () => {
    await waitForBackendReady()
    const { data } = await createProject(`OCR Config E2E ${Date.now()}`, 'OCR config test')
    projectId = data.id
  })

  // --- GET OCR Config (initial state) ---

  test('01 - new project has empty engines and null default', async () => {
    const { data, status } = await getOcrConfig(projectId)
    expect(status).toBe(200)
    expect(data.default_engine_id).toBeNull()
    expect(data.engines).toEqual({})
  })

  // --- Add Engine ---

  test('02 - add commercial_api engine (Gemini)', async () => {
    const { data, status } = await addEngine(projectId, {
      engine_type: 'commercial_api',
      name: 'Gemini Flash',
      config: {
        provider: 'gemini',
        api_key: 'test-key-gemini',
        model: 'gemini-3-flash-preview',
      },
    })
    expect(status).toBe(201)
    expect(data.engines['gemini-flash']).toBeDefined()
    expect(data.engines['gemini-flash'].engine_type).toBe('commercial_api')
    expect(data.engines['gemini-flash'].name).toBe('Gemini Flash')
    expect(data.engines['gemini-flash'].config).toMatchObject({
      provider: 'gemini',
      api_key: 'test-key-gemini',
      model: 'gemini-3-flash-preview',
    })
    // First engine becomes default automatically
    expect(data.default_engine_id).toBe('gemini-flash')
  })

  test('03 - add vllm engine with custom engine_id', async () => {
    const { data, status } = await addEngine(projectId, {
      engine_id: 'vllm-chandra',
      engine_type: 'vllm',
      name: 'vLLM Chandra',
      config: { host: 'gpu-server-1', port: 8000, model: 'datalab-to/chandra' },
    })
    expect(status).toBe(201)
    expect(data.engines['vllm-chandra']).toBeDefined()
    expect(data.engines['vllm-chandra'].engine_type).toBe('vllm')
    // Default unchanged (first engine stays default)
    expect(data.default_engine_id).toBe('gemini-flash')
  })

  test('04 - add second vllm engine (same type, different instance)', async () => {
    const { data, status } = await addEngine(projectId, {
      engine_id: 'vllm-olmocr',
      engine_type: 'vllm',
      name: 'vLLM olmOCR',
      config: { host: 'gpu-server-2', port: 8000, model: 'allenai/olmOCR-2-7B-1025-FP8' },
    })
    expect(status).toBe(201)
    expect(Object.keys(data.engines)).toHaveLength(3)
    expect(data.engines['vllm-olmocr'].engine_type).toBe('vllm')
  })

  test('05 - add split_pipeline engine', async () => {
    const { data, status } = await addEngine(projectId, {
      engine_type: 'split_pipeline',
      name: 'Docling + Gemini',
      config: {
        docling_model_name: 'ibm-granite/granite-docling-258M',
        ocr_provider: 'gemini',
        ocr_api_key: 'test-key-split',
        ocr_model: 'gemini-3-flash-preview',
      },
    })
    expect(status).toBe(201)
    expect(Object.keys(data.engines)).toHaveLength(4)
    expect(data.engines['docling-gemini']).toBeDefined()
  })

  // --- Add Engine validation ---

  test('06 - add engine with duplicate engine_id returns 409', async () => {
    const { status } = await addEngine(projectId, {
      engine_id: 'vllm-chandra',
      engine_type: 'vllm',
      name: 'Duplicate',
      config: { host: 'x', port: 9999 },
    })
    expect(status).toBe(409)
  })

  test('07 - add engine with invalid engine_type returns 422', async () => {
    const { status } = await addEngine(projectId, {
      engine_type: 'nonexistent' as 'vllm',
      name: 'Bad',
      config: {},
    })
    expect(status).toBe(422)
  })

  // --- GET OCR Config (after adds) ---

  test('08 - get config reflects all engines', async () => {
    const { data, status } = await getOcrConfig(projectId)
    expect(status).toBe(200)
    expect(data.default_engine_id).toBe('gemini-flash')
    expect(Object.keys(data.engines)).toHaveLength(4)
  })

  // --- Update Engine ---

  test('09 - update engine name', async () => {
    const { data, status } = await updateEngine(projectId, 'vllm-chandra', {
      name: 'vLLM Chandra (updated)',
    })
    expect(status).toBe(200)
    expect(data.engines['vllm-chandra'].name).toBe('vLLM Chandra (updated)')
    // engine_type unchanged
    expect(data.engines['vllm-chandra'].engine_type).toBe('vllm')
  })

  test('10 - update engine config', async () => {
    const { data, status } = await updateEngine(projectId, 'vllm-chandra', {
      config: { host: 'gpu-server-1-new', port: 8001, model: 'datalab-to/chandra' },
    })
    expect(status).toBe(200)
    expect(data.engines['vllm-chandra'].config).toMatchObject({
      host: 'gpu-server-1-new',
      port: 8001,
    })
  })

  test('11 - update non-existent engine returns 404', async () => {
    const { status } = await updateEngine(projectId, 'no-such-engine', {
      name: 'X',
    })
    expect(status).toBe(404)
  })

  // --- Set Default Engine ---

  test('12 - set default engine to vllm-chandra', async () => {
    const { data, status } = await setDefaultEngine(projectId, 'vllm-chandra')
    expect(status).toBe(200)
    expect(data.default_engine_id).toBe('vllm-chandra')
  })

  test('13 - set default to null (pdfminer fallback)', async () => {
    const { data, status } = await setDefaultEngine(projectId, null)
    expect(status).toBe(200)
    expect(data.default_engine_id).toBeNull()
  })

  test('14 - set default to non-existent engine returns 404', async () => {
    const { status } = await setDefaultEngine(projectId, 'no-such-engine')
    expect(status).toBe(404)
  })

  // Restore default for subsequent tests
  test('15 - restore default to gemini-flash', async () => {
    const { data, status } = await setDefaultEngine(projectId, 'gemini-flash')
    expect(status).toBe(200)
    expect(data.default_engine_id).toBe('gemini-flash')
  })

  // --- Connection Test ---

  test('16 - connection test for unreachable vllm fails gracefully', async () => {
    const { data, status } = await testOcrConnection(projectId, 'vllm-chandra')
    expect(status).toBe(200)
    expect(data.success).toBe(false)
    expect(data.message).toBeTruthy()
  })

  test('17 - connection test for non-existent engine returns 404', async () => {
    const { status } = await testOcrConnection(projectId, 'no-such-engine')
    expect(status).toBe(404)
  })

  // --- Available Engines ---

  test('18 - available-engines returns all registered engines', async () => {
    const { data, status } = await getAvailableEngines(projectId)
    expect(status).toBe(200)
    expect(data.engines.length).toBe(4)
    const ids = data.engines.map((e) => e.engine_id)
    expect(ids).toContain('gemini-flash')
    expect(ids).toContain('vllm-chandra')
    expect(ids).toContain('vllm-olmocr')
    expect(ids).toContain('docling-gemini')
  })

  test('19 - available-engines includes engine_id and name', async () => {
    const { data } = await getAvailableEngines(projectId)
    const gemini = data.engines.find((e) => e.engine_id === 'gemini-flash')
    expect(gemini).toBeDefined()
    expect(gemini!.engine_type).toBe('commercial_api')
    expect(gemini!.name).toBe('Gemini Flash')
  })

  // --- Delete Engine ---

  test('20 - delete non-default engine', async () => {
    const { data, status } = await deleteEngine(projectId, 'vllm-olmocr')
    expect(status).toBe(200)
    expect(data.engines['vllm-olmocr']).toBeUndefined()
    expect(Object.keys(data.engines)).toHaveLength(3)
    // Default unchanged
    expect(data.default_engine_id).toBe('gemini-flash')
  })

  test('21 - delete default engine clears default_engine_id', async () => {
    const { data, status } = await deleteEngine(projectId, 'gemini-flash')
    expect(status).toBe(200)
    expect(data.engines['gemini-flash']).toBeUndefined()
    expect(data.default_engine_id).toBeNull()
  })

  test('22 - delete non-existent engine returns 404', async () => {
    const { status } = await deleteEngine(projectId, 'no-such-engine')
    expect(status).toBe(404)
  })

  // --- Available Engines after deletes ---

  test('23 - available-engines reflects deletions', async () => {
    const { data, status } = await getAvailableEngines(projectId)
    expect(status).toBe(200)
    expect(data.engines).toHaveLength(2)
    const ids = data.engines.map((e) => e.engine_id)
    expect(ids).toContain('vllm-chandra')
    expect(ids).toContain('docling-gemini')
    expect(ids).not.toContain('gemini-flash')
    expect(ids).not.toContain('vllm-olmocr')
  })

  // --- Empty project ---

  test('24 - available-engines empty when no engines registered', async () => {
    // Delete remaining engines
    await deleteEngine(projectId, 'vllm-chandra')
    await deleteEngine(projectId, 'docling-gemini')

    const { data, status } = await getAvailableEngines(projectId)
    expect(status).toBe(200)
    expect(data.engines).toHaveLength(0)
  })

  test('25 - final config has empty engines and null default', async () => {
    const { data } = await getOcrConfig(projectId)
    expect(data.default_engine_id).toBeNull()
    expect(data.engines).toEqual({})
  })

  afterAll(async () => {
    try {
      await deleteProject(projectId)
    } catch {
      // Ignore cleanup errors
    }
  })
})
