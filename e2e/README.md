# E2E Tests

> [Korean](README.ko.md) | **English**

End-to-end tests based on Vitest. Spins up the full stack (postgres, backend, frontend) via Docker Compose
and verifies the API.

## Prerequisites

```bash
cd e2e
bun install
```

## Basic Tests (No GPU Required)

The default profile runs only postgres + backend + frontend. It uses pdfminer.six fallback for OCR
extraction, so no GPU is needed.

```bash
# 1. Start services
bun run docker:up

# 2. Run tests
bun run test

# 3. Run individual tests
bun run test:health        # health check
bun run test:extraction    # pdfminer extraction -> accept workflow
bun run test:ocr-config    # OCR engine configuration API
bun run test:attribute     # attribute classifier
bun run test:reading-order # reading order CRUD
bun run test:relations     # relations CRUD
bun run test:re-extract    # document re-extraction + force accept
bun run test:benchmark     # API benchmark
bun run test:browser:mcp   # chrome-devtools MCP browser E2E (login/ID duplication check)

# 4. Cleanup
bun run docker:down
```

## GPU Tests (vLLM + Chandra)

The `gpu` profile adds a vLLM server on top of the default services. vLLM loads the
`prithivMLmods/chandra-FP8-Latest` model and requires a **24GB+ VRAM GPU**.

### Requirements

- NVIDIA GPU (24GB+ VRAM, e.g. RTX 4090, A5000, A6000)
- NVIDIA Container Toolkit (`nvidia-docker2`)
- First run downloads the model (~18GB)

### Running

```bash
# 1. Start services with GPU profile
bun run docker:gpu:up

# 2. Wait for vLLM model loading (10-30 min on first run including download)
#    Check progress via logs:
docker compose -f docker-compose.e2e.yml --profile gpu logs -f vllm

# 3. Run GPU tests
bun run test:gpu

# 4. Cleanup
bun run docker:gpu:down
```

### HuggingFace Cache

To persist model downloads, set the `HF_CACHE_DIR` environment variable:

```bash
# Default: ~/.cache/huggingface
export HF_CACHE_DIR=/data/models/huggingface
bun run docker:gpu:up
```

## Test Structure

```text
e2e/
├── docker-compose.e2e.yml    # Docker Compose (default + gpu profiles)
├── vitest.config.ts          # Vitest config (basic tests)
├── vitest.gpu.config.ts      # Vitest config (GPU tests)
├── package.json
├── helpers/
│   ├── api.ts                # API helpers (CRUD, OCR config, vLLM health)
│   ├── pdf.ts                # Test PDF download (attention.pdf)
│   └── timer.ts              # Benchmark timer
├── tests/
│   ├── health.test.ts              # Service health check
│   ├── extraction.test.ts          # pdfminer extraction -> accept workflow
│   ├── ocr-config.test.ts          # OCR engine config API (multi-instance CRUD + validation)
│   ├── attribute-classifier.test.ts  # Attribute classifier
│   ├── reading-order.test.ts       # Reading order CRUD + validation
│   ├── relations.test.ts           # Relations CRUD + conflict validation
│   ├── re-extract.test.ts          # Document re-extraction + force accept
│   ├── benchmark.test.ts           # API response time benchmark
│   └── gpu/
│       ├── vllm-extraction.test.ts       # vLLM chandra extraction (GPU only)
│       └── hybrid-labeling-gpu.test.ts   # Hybrid labeling (GPU only)
└── fixtures/
    └── attention.pdf         # Test PDF (auto-downloaded)
```

## Docker Compose Services

| Service | Profile | Port | Description |
| -------- | -------- | ----- | ---- |
| postgres | default | 25432 | PostgreSQL 18 |
| backend | default | 25000 | FastAPI server |
| frontend | default | 23000 | SvelteKit (Nginx) |
| vllm | gpu | 28000 | vLLM OpenAI API (prithivMLmods/chandra-FP8-Latest) |

## Environment Variables

| Variable | Default | Description |
| ---- | ---- | ---- |
| `E2E_BACKEND_URL` | `http://localhost:25000` | Backend API URL |
| `E2E_FRONTEND_URL` | `http://localhost:23000` | Frontend URL |
| `E2E_VLLM_URL` | `http://localhost:28000` | vLLM API URL |
| `HF_CACHE_DIR` | `~/.cache/huggingface` | HuggingFace model cache path |

## Vitest Configuration

| Config File | Match Pattern | Timeout | Description |
| ---- | ---- | ---- | ---- |
| `vitest.config.ts` | `tests/**/*.test.ts` (excluding gpu/) | 2 min | Basic tests |
| `vitest.gpu.config.ts` | `tests/gpu/**/*.test.ts` | 10 min | GPU only (vLLM extraction) |

`bun run test` runs with the default config, and `bun run test:gpu` runs with the GPU config.
