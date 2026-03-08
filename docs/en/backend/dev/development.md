# Development Guide

## Development Environment Setup

```bash
# Install dependencies (CPU only)
uv sync --group dev --group docs --extra cpu

# For GPU usage, select the extra matching your CUDA version
# uv sync --group dev --group docs --extra cu128

# Install pre-commit hooks
uvx pre-commit install
```

## Code Style

| Item | Rule |
| ------ | ------ |
| Python version | 3.13+ |
| Line length | 100 characters |
| Quotes | Single quotes (`'`) |
| Formatter | ruff format |
| Linter | ruff check |
| Type checker | ty check |
| Docstrings | Google convention |

### Commands

```bash
# Formatting
uv run ruff format

# Lint check
uv run ruff check

# Lint auto-fix
uv run ruff check --fix

# Type checking
uv run ty check
```

## Testing

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov

# Verbose output
uv run pytest -v

# Specific file
uv run pytest tests/services/test_labeling_service.py -v

# Specific test
uv run pytest tests/services/test_labeling_service.py::TestAddElement -v
```

### Test Structure

```text
tests/
├── conftest.py                        # Common fixtures
├── api/                               # API router tests
│   ├── test_app.py                    # App configuration
│   ├── test_health.py                 # Health check
│   ├── test_projects.py               # Project CRUD
│   ├── test_project_ocr_config.py     # OCR engine config API
│   ├── test_documents.py              # Document upload/view
│   ├── test_pages.py                  # Pages, reading order, relation CRUD
│   ├── test_users.py                  # User management
│   ├── test_export.py                 # Data export
│   └── test_settings.py              # Settings validation
├── services/                          # Service layer tests
│   ├── engines/                       # OCR engine tests
│   │   ├── test_base.py               # BaseOCREngine ABC
│   │   ├── test_factory.py            # build_engine() / build_engine_by_id() factory
│   │   ├── test_pdfminer_engine.py
│   │   ├── test_commercial_api_engine.py
│   │   ├── test_vllm_engine.py
│   │   └── test_split_pipeline_engine.py
│   ├── test_document_service.py       # PDF upload/conversion
│   ├── test_labeling_service.py       # Annotation, reading order, relations
│   ├── test_attribute_classifier.py   # Attribute auto-classification
│   ├── test_extraction_service.py     # Text extraction
│   ├── test_text_extraction_service.py  # Region OCR extraction
│   ├── test_docling_layout_service.py # Docling layout detection
│   ├── test_gemini_ocr_service.py     # Gemini VLM provider
│   ├── test_vllm_ocr_service.py       # vLLM provider
│   ├── test_ocr_provider.py           # OCR provider common
│   ├── test_ocr_pipeline.py           # Pipeline orchestrator
│   ├── test_sample_pdf_extraction.py  # Sample PDF extraction
│   └── test_export_service.py         # Export service
├── schemas/                           # Schema tests
│   └── test_page_schema.py            # PageResponse (URL calculation)
```

### Test Patterns

API tests use `FastAPI TestClient` and mock service/repository calls:

```python
class TestPageEndpoints:
    def test_get_page(self, client: TestClient, sample_page_record):
        with patch(
            'saegim.services.labeling_service.get_page_data',
            new_callable=AsyncMock,
            return_value=sample_page_record,
        ):
            response = client.get(f'/api/v1/pages/{page_id}')

        assert response.status_code == 200
```

Service tests mock repositories:

```python
class TestSaveAnnotation:
    @pytest.mark.asyncio
    async def test_saves_annotation(self, mock_pool, page_id, document_id):
        record = _make_page_record(page_id, document_id, annotation_data={...})

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.update_annotation = AsyncMock(return_value=record)
            result = await labeling_service.save_annotation(mock_pool, page_id, {})

        assert result['annotation_data'] == {...}
```

### Key Fixtures

Common fixtures defined in `tests/conftest.py`:

| Fixture | Description |
| -------- | ------ |
| `test_settings` | Test Settings (debug=True) |
| `mock_pool` | asyncpg Pool mock object |
| `app` | FastAPI app (with DB mock applied) |
| `client` | TestClient |
| `sample_project_record` | Sample project record |
| `sample_document_record` | Sample document record |
| `sample_page_record` | Sample page record (with annotations) |
| `sample_user_record` | Sample user record |

## Adding New Features Guide

### Adding a New API Endpoint

1. **Define schemas** - Add Pydantic models in `src/saegim/schemas/`
2. **Write repository** - Add raw SQL functions in `src/saegim/repositories/`
3. **Write service** - Add business logic in `src/saegim/services/` (OCR engines in `services/engines/`)
4. **Write router** - Add endpoints in `src/saegim/api/routes/`
5. **Register router** - Add `include_router` in `src/saegim/app.py`
6. **Write tests** - Add tests in `tests/api/` and `tests/services/`

### Adding a New Migration

1. Create a numbered file in the `migrations/` directory (e.g., `002_add_labels.sql`)
2. Write DDL (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE`, etc.)
3. Run with `psql -f migrations/002_add_labels.sql`

## Configuration

### Environment Variables

| Variable | Default | Description |
| ------ | -------- | ------ |
| `API_HOST` | `0.0.0.0` | API bind host |
| `API_PORT` | `5000` | API port |
| `DEBUG` | `false` | Debug mode (enables docs/redoc) |
| `LOG_LEVEL` | `INFO` | Log level |
| `DATABASE_URL` | `postgresql://labeling:labeling@localhost:5432/labeling` | DB connection URL |
| `DB_POOL_MIN_SIZE` | `2` | Minimum connections |
| `DB_POOL_MAX_SIZE` | `10` | Maximum connections |
| `STORAGE_PATH` | `./storage` | File storage path |
| `MAX_WORKERS` | `1` | Worker count |
| `CORS_ORIGINS` | `["http://localhost:3000", "http://localhost:5173"]` | Allowed CORS origins |

Environment variables can be set via a `.env` file or system environment variables.
`pydantic-settings` loads them automatically.

## Documentation Build

```bash
# Local server (live reload)
uv run mkdocs serve

# Static build
uv run mkdocs build
```

Built documentation is generated in the `site/` directory.
