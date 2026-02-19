import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/svelte'
import OcrSettingsPanel from '$lib/components/settings/OcrSettingsPanel.svelte'
import type { OcrConfigResponse } from '$lib/api/types'

describe('OcrSettingsPanel', () => {
  afterEach(() => {
    cleanup()
  })

  const defaultConfig: OcrConfigResponse = {
    engine_type: 'pymupdf',
  }

  it('renders all four engine type options', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    expect(screen.getByText('PyMuPDF')).toBeTruthy()
    expect(screen.getByText('상업용 VLM API')).toBeTruthy()
    expect(screen.getByText('통합 파이프라인 서버')).toBeTruthy()
    expect(screen.getByText('분리 파이프라인')).toBeTruthy()
  })

  it('does not show sub-config when PyMuPDF is selected', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    expect(screen.queryByLabelText('API Key')).toBeNull()
    expect(screen.queryByText('Google Gemini')).toBeNull()
    expect(screen.queryByText('OCR 프로바이더')).toBeNull()
  })

  it('shows commercial API config when selected', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const caButton = screen.getByText('상업용 VLM API')
    await fireEvent.click(caButton)

    expect(screen.getByText('Google Gemini')).toBeTruthy()
    expect(screen.getByLabelText('API Key')).toBeTruthy()
    expect(screen.getByLabelText('모델')).toBeTruthy()
  })

  it('shows Gemini API key field when Gemini provider is selected', async () => {
    const caConfig: OcrConfigResponse = {
      engine_type: 'commercial_api',
      commercial_api: { provider: 'gemini', api_key: 'test-key', model: 'gemini-3-flash-preview' },
    }
    render(OcrSettingsPanel, { props: { config: caConfig } })

    expect(screen.getByLabelText('API Key')).toBeTruthy()
  })

  it('shows integrated server config when selected', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const isButton = screen.getByText('통합 파이프라인 서버')
    await fireEvent.click(isButton)

    expect(screen.getByLabelText('호스트')).toBeTruthy()
    expect(screen.getByLabelText('포트')).toBeTruthy()
    expect(screen.getByLabelText('모델')).toBeTruthy()
  })

  it('shows split pipeline config when selected', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const spButton = screen.getByText('분리 파이프라인')
    await fireEvent.click(spButton)

    expect(screen.getByLabelText('레이아웃 서버 URL')).toBeTruthy()
    expect(screen.getByText('OCR 프로바이더')).toBeTruthy()
  })

  it('calls onsave with pymupdf config', async () => {
    const onsave = vi.fn()
    render(OcrSettingsPanel, {
      props: { config: defaultConfig, onsave },
    })

    const saveButton = screen.getByText('설정 저장')
    await fireEvent.click(saveButton)

    expect(onsave).toHaveBeenCalledOnce()
    const saved = onsave.mock.calls[0][0]
    expect(saved.engine_type).toBe('pymupdf')
    expect(saved.commercial_api).toBeUndefined()
  })

  it('calls onsave with correct commercial_api gemini config', async () => {
    const onsave = vi.fn()
    const caConfig: OcrConfigResponse = {
      engine_type: 'commercial_api',
      commercial_api: { provider: 'gemini', api_key: 'test-key', model: 'gemini-3-flash-preview' },
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

  it('calls onsave with correct integrated_server config', async () => {
    const onsave = vi.fn()
    const isConfig: OcrConfigResponse = {
      engine_type: 'integrated_server',
      integrated_server: { host: 'myhost', port: 9999, model: 'datalab-to/chandra' },
    }
    render(OcrSettingsPanel, {
      props: { config: isConfig, onsave },
    })

    const saveButton = screen.getByText('설정 저장')
    await fireEvent.click(saveButton)

    expect(onsave).toHaveBeenCalledOnce()
    const saved = onsave.mock.calls[0][0]
    expect(saved.engine_type).toBe('integrated_server')
    expect(saved.integrated_server.host).toBe('myhost')
    expect(saved.integrated_server.port).toBe(9999)
    expect(saved.integrated_server.model).toBe('datalab-to/chandra')
  })

  it('disables save button when commercial_api Gemini has no API key', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const caButton = screen.getByText('상업용 VLM API')
    await fireEvent.click(caButton)

    const saveButton = screen.getByText('설정 저장')
    expect(saveButton.hasAttribute('disabled')).toBe(true)
  })

  it('enables save button for PyMuPDF without extra config', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const saveButton = screen.getByText('설정 저장')
    expect(saveButton.hasAttribute('disabled')).toBe(false)
  })

  it('does not show connection test button for PyMuPDF', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    expect(screen.queryByText('연결 테스트')).toBeNull()
  })

  it('shows connection test button for non-pymupdf engines', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const caButton = screen.getByText('상업용 VLM API')
    await fireEvent.click(caButton)

    expect(screen.getByText('연결 테스트')).toBeTruthy()
  })
})
