import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const FIXTURES_DIR = resolve(__dirname, '..', 'fixtures')
const PDF_PATH = resolve(FIXTURES_DIR, 'attention.pdf')
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
if (process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))) {
  ensureTestPdf().catch((err) => {
    console.error('Failed to download PDF:', err)
    process.exit(1)
  })
}
