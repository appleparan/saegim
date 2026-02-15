import { writeFileSync, existsSync, readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const RESULTS_PATH = resolve(__dirname, '..', 'fixtures', 'benchmark_results.json')

export interface BenchmarkEntry {
  name: string
  duration_ms: number
  timestamp: string
}

export interface BenchmarkReport {
  run_at: string
  entries: BenchmarkEntry[]
  summary: {
    total_entries: number
    total_duration_ms: number
    avg_duration_ms: number
    max_duration_ms: number
    min_duration_ms: number
  }
}

export class BenchmarkCollector {
  private entries: BenchmarkEntry[] = []

  record(name: string, durationMs: number): void {
    this.entries.push({
      name,
      duration_ms: Math.round(durationMs * 100) / 100,
      timestamp: new Date().toISOString(),
    })
  }

  getEntries(): BenchmarkEntry[] {
    return [...this.entries]
  }

  save(): string {
    const durations = this.entries.map((e) => e.duration_ms)
    const report: BenchmarkReport = {
      run_at: new Date().toISOString(),
      entries: this.entries,
      summary: {
        total_entries: this.entries.length,
        total_duration_ms: Math.round(durations.reduce((a, b) => a + b, 0) * 100) / 100,
        avg_duration_ms:
          Math.round((durations.reduce((a, b) => a + b, 0) / durations.length) * 100) / 100,
        max_duration_ms: Math.max(...durations),
        min_duration_ms: Math.min(...durations),
      },
    }

    // Append to history if exists
    let history: BenchmarkReport[] = []
    if (existsSync(RESULTS_PATH)) {
      try {
        const raw = readFileSync(RESULTS_PATH, 'utf-8')
        history = JSON.parse(raw)
      } catch {
        history = []
      }
    }
    history.push(report)

    // Keep last 20 runs
    if (history.length > 20) {
      history = history.slice(-20)
    }

    writeFileSync(RESULTS_PATH, JSON.stringify(history, null, 2))
    return RESULTS_PATH
  }

  printSummary(): void {
    console.log('\n=== Benchmark Results ===')
    for (const entry of this.entries) {
      const bar = '█'.repeat(Math.min(Math.round(entry.duration_ms / 100), 50))
      console.log(`  ${entry.name.padEnd(35)} ${entry.duration_ms.toFixed(1).padStart(8)}ms ${bar}`)
    }
    const total = this.entries.reduce((a, e) => a + e.duration_ms, 0)
    console.log(`${'  TOTAL'.padEnd(35)} ${total.toFixed(1).padStart(8)}ms`)
    console.log('========================\n')
  }
}
