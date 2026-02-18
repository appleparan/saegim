import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/svelte'
import OcrSettingsPanel from '$lib/components/settings/OcrSettingsPanel.svelte'
import type { OcrConfigResponse } from '$lib/api/types'

describe('OcrSettingsPanel', () => {
  afterEach(() => {
    cleanup()
  })

  const defaultConfig: OcrConfigResponse = {
    layout_provider: 'pymupdf',
  }

  it('renders both layout provider options', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    expect(screen.getByText('PyMuPDF')).toBeTruthy()
    expect(screen.getByText('PP-StructureV3')).toBeTruthy()
  })

  it('does not show PP-StructureV3 config when PyMuPDF is selected', () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    expect(screen.queryByLabelText('API Key')).toBeNull()
    expect(screen.queryByText('OCR 프로바이더')).toBeNull()
  })

  it('shows PP-StructureV3 server config and OCR providers when selected', async () => {
    render(OcrSettingsPanel, { props: { config: defaultConfig } })

    const ppButton = screen.getByText('PP-StructureV3')
    await fireEvent.click(ppButton)

    // PP-StructureV3 server config
    expect(screen.getByLabelText('호스트')).toBeTruthy()
    expect(screen.getByLabelText('포트')).toBeTruthy()

    // OCR provider options
    expect(screen.getByText('PP-OCR (내장)')).toBeTruthy()
    expect(screen.getByText('Google Gemini')).toBeTruthy()
    expect(screen.getByText('OlmOCR')).toBeTruthy()
  })

  it('shows Gemini config when Gemini OCR provider is selected', async () => {
    const ppConfig: OcrConfigResponse = {
      layout_provider: 'ppstructure',
      ocr_provider: 'ppocr',
      ppstructure: { host: 'localhost', port: 18811 },
    }
    render(OcrSettingsPanel, { props: { config: ppConfig } })

    const geminiButton = screen.getByText('Google Gemini')
    await fireEvent.click(geminiButton)

    expect(screen.getByLabelText('API Key')).toBeTruthy()
  })

  it('shows OlmOCR (vLLM) config when OlmOCR is selected', async () => {
    const ppConfig: OcrConfigResponse = {
      layout_provider: 'ppstructure',
      ocr_provider: 'ppocr',
      ppstructure: { host: 'localhost', port: 18811 },
    }
    render(OcrSettingsPanel, { props: { config: ppConfig } })

    const olmButton = screen.getByText('OlmOCR')
    await fireEvent.click(olmButton)

    // vLLM settings should have multiple host/port fields
    const hosts = screen.getAllByLabelText('호스트')
    expect(hosts.length).toBe(2) // PP-StructureV3 + vLLM
  })

  it('calls onsave with correct ppstructure+gemini config', async () => {
    const onsave = vi.fn()
    const geminiConfig: OcrConfigResponse = {
      layout_provider: 'ppstructure',
      ocr_provider: 'gemini',
      ppstructure: { host: 'localhost', port: 18811 },
      gemini: { api_key: 'test-key', model: 'gemini-2.0-flash' },
    }
    render(OcrSettingsPanel, {
      props: { config: geminiConfig, onsave },
    })

    const saveButton = screen.getByText('설정 저장')
    await fireEvent.click(saveButton)

    expect(onsave).toHaveBeenCalledOnce()
    const saved = onsave.mock.calls[0][0]
    expect(saved.layout_provider).toBe('ppstructure')
    expect(saved.ocr_provider).toBe('gemini')
    expect(saved.gemini.api_key).toBe('test-key')
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
    expect(saved.layout_provider).toBe('pymupdf')
    expect(saved.ocr_provider).toBeUndefined()
  })

  it('disables save button when Gemini has no API key', async () => {
    const ppConfig: OcrConfigResponse = {
      layout_provider: 'ppstructure',
      ocr_provider: 'ppocr',
      ppstructure: { host: 'localhost', port: 18811 },
    }
    render(OcrSettingsPanel, { props: { config: ppConfig } })

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
