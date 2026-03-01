import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/svelte'
import OcrSettingsPanel from '$lib/components/settings/OcrSettingsPanel.svelte'
import type { OcrConfigResponse } from '$lib/api/types'

describe('OcrSettingsPanel', () => {
  afterEach(() => {
    cleanup()
  })

  const defaultConfig: OcrConfigResponse = {
    engine_type: 'pdfminer',
  }

  it('renders all four engine type options', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    expect(screen.getByText('pdfminer')).toBeTruthy()
    expect(screen.getByText('Gemini API')).toBeTruthy()
    expect(screen.getByText('vLLM 서버')).toBeTruthy()
    expect(screen.getByText('Docling + OCR')).toBeTruthy()
  })

  it('does not show sub-config when pdfminer is selected', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    expect(screen.queryByLabelText('API Key')).toBeNull()
    expect(screen.queryByText('Google Gemini')).toBeNull()
    expect(screen.queryByText('OCR 프로바이더')).toBeNull()
  })

  it('shows commercial API config when selected', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const caButton = screen.getByText('Gemini API')
    await fireEvent.click(caButton)

    expect(screen.getByText('Google Gemini')).toBeTruthy()
    expect(screen.getByLabelText('API Key')).toBeTruthy()
    expect(screen.getByLabelText('모델')).toBeTruthy()
  })

  it('shows Gemini API key field when Gemini provider is selected', async () => {
    const caConfig: OcrConfigResponse = {
      engine_type: 'commercial_api',
      commercial_api: {
        provider: 'gemini',
        api_key: 'test-key',
        model: 'gemini-3-flash-preview',
      },
    }
    render(OcrSettingsPanel, { props: { config: caConfig } })

    expect(screen.getByLabelText('API Key')).toBeTruthy()
  })

  it('shows vLLM server config when selected', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const vllmButton = screen.getByText('vLLM 서버')
    await fireEvent.click(vllmButton)

    expect(screen.getByLabelText('호스트')).toBeTruthy()
    expect(screen.getByLabelText('포트')).toBeTruthy()
    expect(screen.getByLabelText('모델')).toBeTruthy()
  })

  it('shows split pipeline config when selected', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const spButton = screen.getByText('Docling + OCR')
    await fireEvent.click(spButton)

    expect(screen.getByLabelText('Docling 모델')).toBeTruthy()
    expect(screen.getByText('OCR 프로바이더')).toBeTruthy()
  })

  it('calls onsave with pdfminer config', async () => {
    const onsave = vi.fn()
    render(OcrSettingsPanel, {
      props: { config: defaultConfig, onsave },
    })

    const saveButton = screen.getByText('설정 저장')
    await fireEvent.click(saveButton)

    expect(onsave).toHaveBeenCalledOnce()
    const saved = onsave.mock.calls[0][0]
    expect(saved.engine_type).toBe('pdfminer')
    expect(saved.commercial_api).toBeUndefined()
  })

  it('calls onsave with correct commercial_api gemini config', async () => {
    const onsave = vi.fn()
    const caConfig: OcrConfigResponse = {
      engine_type: 'commercial_api',
      commercial_api: {
        provider: 'gemini',
        api_key: 'test-key',
        model: 'gemini-3-flash-preview',
      },
    }
    render(OcrSettingsPanel, {
      props: { config: caConfig, onsave },
    })

    const saveButton = screen.getByText('설정 저장')
    await fireEvent.click(saveButton)

    expect(onsave).toHaveBeenCalledOnce()
    const saved = onsave.mock.calls[0][0]
    expect(saved.engine_type).toBe('commercial_api')
    expect(saved.commercial_api.provider).toBe('gemini')
    expect(saved.commercial_api.api_key).toBe('test-key')
  })

  it('calls onsave with correct vllm config', async () => {
    const onsave = vi.fn()
    const vllmConfig: OcrConfigResponse = {
      engine_type: 'vllm',
      vllm: {
        host: 'myhost',
        port: 9999,
        model: 'datalab-to/chandra',
      },
    }
    render(OcrSettingsPanel, {
      props: { config: vllmConfig, onsave },
    })

    const saveButton = screen.getByText('설정 저장')
    await fireEvent.click(saveButton)

    expect(onsave).toHaveBeenCalledOnce()
    const saved = onsave.mock.calls[0][0]
    expect(saved.engine_type).toBe('vllm')
    expect(saved.vllm.host).toBe('myhost')
    expect(saved.vllm.port).toBe(9999)
    expect(saved.vllm.model).toBe('datalab-to/chandra')
  })

  it('disables save button when commercial_api Gemini has no API key', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const caButton = screen.getByText('Gemini API')
    await fireEvent.click(caButton)

    const saveButton = screen.getByText('설정 저장')
    expect(saveButton.hasAttribute('disabled')).toBe(true)
  })

  it('enables save button for pdfminer without extra config', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const saveButton = screen.getByText('설정 저장')
    expect(saveButton.hasAttribute('disabled')).toBe(false)
  })

  it('does not show connection test button for pdfminer', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    expect(screen.queryByText('연결 테스트')).toBeNull()
  })

  it('shows connection test button for non-pdfminer engines', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const caButton = screen.getByText('Gemini API')
    await fireEvent.click(caButton)

    expect(screen.getByText('연결 테스트')).toBeTruthy()
  })
})
