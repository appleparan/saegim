import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/svelte'
import OcrSettingsPanel from '$lib/components/settings/OcrSettingsPanel.svelte'
import type { OcrConfigResponse } from '$lib/api/types'

describe('OcrSettingsPanel', () => {
  afterEach(() => {
    cleanup()
  })

  const defaultConfig: OcrConfigResponse = {
    provider: 'pymupdf',
  }

  it('renders all three provider options', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    expect(screen.getByText('PyMuPDF')).toBeTruthy()
    expect(screen.getByText('Google Gemini')).toBeTruthy()
    expect(screen.getByText('vLLM')).toBeTruthy()
  })

  it('does not show Gemini or vLLM config sections by default', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    expect(screen.queryByLabelText('API Key')).toBeNull()
    expect(screen.queryByLabelText('호스트')).toBeNull()
  })

  it('shows Gemini config when Gemini provider is selected', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const geminiButton = screen.getByText('Google Gemini')
    await fireEvent.click(geminiButton)

    expect(screen.getByLabelText('API Key')).toBeTruthy()
    expect(screen.getByLabelText('모델')).toBeTruthy()
  })

  it('shows vLLM config when vLLM provider is selected', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const vllmButton = screen.getByText('vLLM')
    await fireEvent.click(vllmButton)

    expect(screen.getByLabelText('호스트')).toBeTruthy()
    expect(screen.getByLabelText('포트')).toBeTruthy()
    expect(screen.getByLabelText('모델')).toBeTruthy()
  })

  it('calls onsave with correct config for Gemini', async () => {
    const onsave = vi.fn()
    const geminiConfig: OcrConfigResponse = {
      provider: 'gemini',
      gemini: { api_key: 'test-key', model: 'gemini-2.0-flash' },
    }
    render(OcrSettingsPanel, {
      props: { config: geminiConfig, onsave },
    })

    const saveButton = screen.getByText('설정 저장')
    await fireEvent.click(saveButton)

    expect(onsave).toHaveBeenCalledOnce()
    const saved = onsave.mock.calls[0][0]
    expect(saved.provider).toBe('gemini')
    expect(saved.gemini.api_key).toBe('test-key')
    expect(saved.gemini.model).toBe('gemini-2.0-flash')
  })

  it('calls onsave with correct config for vLLM', async () => {
    const onsave = vi.fn()
    const vllmConfig: OcrConfigResponse = {
      provider: 'vllm',
      vllm: { host: 'gpu-server', port: 9000, model: 'test-model' },
    }
    render(OcrSettingsPanel, {
      props: { config: vllmConfig, onsave },
    })

    const saveButton = screen.getByText('설정 저장')
    await fireEvent.click(saveButton)

    expect(onsave).toHaveBeenCalledOnce()
    const saved = onsave.mock.calls[0][0]
    expect(saved.provider).toBe('vllm')
    expect(saved.vllm.host).toBe('gpu-server')
    expect(saved.vllm.port).toBe(9000)
    expect(saved.vllm.model).toBe('test-model')
  })

  it('disables save button when Gemini has no API key', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const geminiButton = screen.getByText('Google Gemini')
    await fireEvent.click(geminiButton)

    const saveButton = screen.getByText('설정 저장')
    expect(saveButton.hasAttribute('disabled')).toBe(true)
  })

  it('enables save button for PyMuPDF without extra config', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const saveButton = screen.getByText('설정 저장')
    expect(saveButton.hasAttribute('disabled')).toBe(false)
  })
})
