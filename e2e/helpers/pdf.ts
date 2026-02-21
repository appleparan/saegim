import { copyFileSync, existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const FIXTURES_DIR = resolve(process.cwd(), 'fixtures')
const PDF_PATH = resolve(FIXTURES_DIR, 'attention.pdf')
const SAMPLE_PDF = resolve(process.cwd(), 'sample_data', '1706.03762v7_4p.pdf')
const PDF_URL = 'https://arxiv.org/pdf/1706.03762v7'

export function getTestPdfPath(): string {
  return PDF_PATH
}

export async function ensureTestPdf(): Promise<string> {
  if (existsSync(PDF_PATH)) {
    console.log(`PDF already cached: ${PDF_PATH}`)
    return PDF_PATH
  }

  mkdirSync(FIXTURES_DIR, { recursive: true })

  // Use local sample PDF (4 pages) if available — much faster than downloading
  if (existsSync(SAMPLE_PDF)) {
    copyFileSync(SAMPLE_PDF, PDF_PATH)
    console.log(`PDF copied from sample_data: ${PDF_PATH}`)
    return PDF_PATH
  }

  // Fallback: download full paper from arxiv
  console.log(`Downloading test PDF from ${PDF_URL}...`)
  const response = await fetch(PDF_URL, {
    headers: {
      'User-Agent': 'saegim-e2e-tests/1.0',
    },
    redirect: 'follow',
  })

  if (!response.ok) {
    throw new Error(`Failed to download PDF: ${response.status} ${response.statusText}`)
  }

  const buffer = Buffer.from(await response.arrayBuffer())
  writeFileSync(PDF_PATH, buffer)
  console.log(`PDF saved: ${PDF_PATH} (${(buffer.length / 1024 / 1024).toFixed(1)} MB)`)

  return PDF_PATH
}

// CLI entrypoint: npx tsx helpers/pdf.ts
const scriptPath = process.argv[1]
if (scriptPath && resolve(scriptPath).includes('helpers/pdf')) {
  ensureTestPdf().catch((err) => {
    console.error('Failed to download PDF:', err)
    process.exit(1)
  })
}
