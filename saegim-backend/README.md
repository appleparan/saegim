# saegim-backend

Backend for the saegim labeling platform. Provides a FastAPI + asyncpg REST API server.

## Tech Stack

| Category | Technology |
| ---- | ---- |
| **Framework** | FastAPI |
| **DB Driver** | asyncpg (raw SQL) |
| **Database** | PostgreSQL 15+ (JSONB) |
| **Schema** | Pydantic |
| **PDF Processing** | pypdfium2 + pdfminer.six |
| **OCR** | 4-type Strategy pattern (Gemini API, vLLM, Layout+OCR, pdfminer) |
| **Formatter** | ruff format |
| **Linter** | ruff check |
| **Type Checker** | ty |
| **Tests** | pytest |
| **Package Management** | uv |

## Project Structure

```text
saegim-backend/
├── src/saegim/
│   ├── app.py                    # FastAPI app factory
│   ├── api/
│   │   └── routes/               # REST endpoints
│   ├── schemas/                  # Pydantic models (EngineType, OcrConfig, etc.)
│   ├── services/
│   │   ├── engines/              # OCR engine Strategy pattern
│   │   │   ├── base.py           # BaseOCREngine ABC
│   │   │   ├── factory.py        # build_engine_by_id() factory
│   │   │   ├── pdfminer_engine.py
│   │   │   ├── commercial_api_engine.py
│   │   │   ├── vllm_engine.py
│   │   │   └── split_pipeline_engine.py
│   │   ├── docir.py              # DocIR intermediate representation
│   │   ├── adapters/             # Model adapters (raw -> DocIR)
│   │   │   ├── base.py           # ModelAdapter Protocol
│   │   │   ├── resolver.py       # resolve_adapter() auto-selection
│   │   │   ├── chandra.py        # ChandraAdapter
│   │   │   ├── lightonocr.py     # LightOnOcrAdapter
│   │   │   └── paddleocr_vl.py   # PaddleOcrVlAdapter
│   │   ├── exporters/            # DocIR -> final output conversion
│   │   │   └── omnidocbench.py   # export_page(PageIR) -> OmniDocBench dict
│   │   ├── layout_types.py       # LayoutRegion, LayoutDetector Protocol
│   │   ├── docling_layout_service.py # Docling layout detection
│   │   ├── pp_doclayout_service.py   # PP-DocLayoutV3 layout detection
│   │   ├── gemini_ocr_service.py     # Gemini VLM provider
│   │   ├── vllm_ocr_service.py       # vLLM provider (Chandra, etc.)
│   │   └── ocr_pipeline.py           # 2-stage pipeline orchestrator
│   ├── repositories/             # Data access (raw SQL)
│   └── core/                     # DB connection pool and settings
├── migrations/                   # SQL migrations
├── tests/                        # pytest unit/integration tests
│   ├── api/                      # API route tests
│   ├── schemas/                  # Pydantic schema tests
│   └── services/                 # Service logic tests
├── docs/                         # MkDocs documentation
└── pyproject.toml                # Project settings (uv, ruff, ty, etc.)
```

## Development

```bash
cd saegim-backend

# Environment setup
uv python install 3.14
uv python pin 3.14
uv sync --group dev --group docs

# Run server
uv run uvicorn saegim.app:app --reload --host 0.0.0.0 --port 5000

# Code quality
uv run ruff format                  # Formatting
uv run ruff check --fix             # Lint
uv run ty check                     # Type check
uv run pytest --cov                 # Tests + coverage

# Docs
uv run mkdocs serve                 # Local docs server
uv run mkdocs build                 # Docs build
```

## Release

```bash
sh scripts/release.sh
```

`release.sh`:

1. Determines the next version with `git-cliff`
2. Generates `CHANGELOG.md` and `RELEASE.md`
3. Commits, tags, and pushes

---

*This project template was generated from [copier-modern-ml](https://github.com/appleparan/copier-modern-ml).*
