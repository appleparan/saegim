import { existsSync } from 'node:fs'
import { resolve } from 'node:path'

const SAMPLE_PDF = resolve(__dirname, '..', 'sample_data', '1706.03762v7_4p.pdf')
const MULTIPAGE_PDF = resolve(__dirname, '..', 'sample_data', '1706.03762v7_7p_9p.pdf')

export function getTestPdfPath(): string {
  if (!existsSync(SAMPLE_PDF)) {
    throw new Error(`Test PDF not found: ${SAMPLE_PDF}`)
  }
  return SAMPLE_PDF
}

export function getMultipagePdfPath(): string {
  if (!existsSync(MULTIPAGE_PDF)) {
    throw new Error(`Multi-page test PDF not found: ${MULTIPAGE_PDF}`)
  }
  return MULTIPAGE_PDF
}

export async function ensureTestPdf(): Promise<string> {
  return getTestPdfPath()
}

export async function ensureMultipagePdf(): Promise<string> {
  return getMultipagePdfPath()
}
