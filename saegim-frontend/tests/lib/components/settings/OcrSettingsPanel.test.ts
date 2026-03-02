import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/svelte'
import OcrSettingsPanel from '$lib/components/settings/OcrSettingsPanel.svelte'
import type { OcrConfigResponse } from '$lib/api/types'

describe('OcrSettingsPanel', () => {
  afterEach(() => {
    cleanup()
  })

  const emptyConfig: OcrConfigResponse = {
    default_engine_id: null,
    engines: {},
  }

  const configWithEngines: OcrConfigResponse = {
    default_engine_id: 'gemini-flash',
    engines: {
      'gemini-flash': {
        engine_type: 'commercial_api',
        name: 'Gemini Flash',
        config: { provider: 'gemini', api_key: 'test-key', model: 'gemini-3-flash-preview' },
      },
      'vllm-lightonocr': {
        engine_type: 'vllm',
        name: 'vLLM LightOnOCR',
        config: { host: 'gpu-server', port: 8000, model: 'lightonai/LightOnOCR-2-1B-bbox-soup' },
      },
    },
  }

  it('renders empty state when no engines registered', () => {
    render(OcrSettingsPanel, { props: { config: emptyConfig } })

    expect(screen.getByText('등록된 엔진이 없습니다.')).toBeTruthy()
  })

  it('renders engine cards when engines exist', () => {
    render(OcrSettingsPanel, { props: { config: configWithEngines } })

    expect(screen.getByText('Gemini Flash')).toBeTruthy()
    expect(screen.getByText('vLLM LightOnOCR')).toBeTruthy()
  })

  it('shows add engine button', () => {
    render(OcrSettingsPanel, { props: { config: emptyConfig } })

    expect(screen.getByText('엔진 추가')).toBeTruthy()
  })

  it('shows pdfminer fallback note', () => {
    render(OcrSettingsPanel, { props: { config: emptyConfig } })

    expect(screen.getByText('pdfminer')).toBeTruthy()
  })

  it('shows header with description', () => {
    render(OcrSettingsPanel, { props: { config: emptyConfig } })

    expect(screen.getByText('OCR 엔진 관리')).toBeTruthy()
  })
})
