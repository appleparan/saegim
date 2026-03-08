# Getting Started

## Prerequisites

- Python 3.13+
- PostgreSQL 15+
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

### 1. Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone the Project and Set Up

```bash
git clone https://github.com/appleparan/saegim
cd saegim/saegim-backend

# Install and pin Python
uv python install 3.14
uv python pin 3.14

# Install dependencies (dev + docs, CPU only)
uv sync --group dev --group docs --extra cpu

# For GPU usage, select the extra matching your CUDA version
uv sync --group dev --group docs --extra cu128   # CUDA 12.8
uv sync --group dev --group docs --extra cu126   # CUDA 12.6
uv sync --group dev --group docs --extra cu130   # CUDA 13.0
```

> **Note:** The `--extra` flag selects the PyTorch installation variant.
> Since OCR engines like Docling require PyTorch, you must select one.
>
> | Extra | Description | GPU Required |
> | ----- | ---- | -------- |
> | `cpu` | CPU only (lightweight) | No |
> | `cu126` | CUDA 12.6 | Yes |
> | `cu128` | CUDA 12.8 | Yes |
> | `cu130` | CUDA 13.0 | Yes |

### 3. Set Up PostgreSQL

Create the database and user:

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database
CREATE USER labeling WITH PASSWORD 'labeling';
CREATE DATABASE labeling OWNER labeling;
\q
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# .env
DATABASE_URL=postgresql://labeling:labeling@localhost:5432/labeling
API_HOST=0.0.0.0
API_PORT=5000
DEBUG=true
LOG_LEVEL=DEBUG
STORAGE_PATH=./storage
```

### 5. Run Migrations

```bash
# Run directly with psql
psql -U labeling -d labeling -f migrations/001_init.sql
```

### 6. Start the Server

```bash
uv run uvicorn saegim.app:app --reload --host 0.0.0.0 --port 5000
```

Once the server is running, you can verify it at the following addresses:

- API: `http://localhost:5000/api/v1/health`
- Swagger UI: `http://localhost:5000/docs` (when DEBUG=true)
- ReDoc: `http://localhost:5000/redoc` (when DEBUG=true)

## Verify Installation

```bash
# Health check
curl http://localhost:5000/api/v1/health

# Example response
# {"status": "healthy"}
```

## Testing

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov

# Specific test file
uv run pytest tests/api/test_projects.py -v
uv run pytest tests/services/test_labeling_service.py -v
```

## Development Tools

```bash
# Code formatting
uv run ruff format

# Lint check
uv run ruff check

# Type checking
uv run ty check

# Documentation local server
uv run mkdocs serve
```

## Docker (Optional)

```bash
# Build CPU image (production)
docker build -t saegim-backend .

# Build CPU image (development, includes dev dependencies)
docker build -t saegim-backend-dev --target development .

# Build GPU image (CUDA 13.0)
docker build -t saegim-backend-gpu \
  --build-arg BASE_IMAGE=nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04 \
  --build-arg TORCH_EXTRA=cu130 .

# Run
docker run -p 5000:5000 \
  -e DATABASE_URL=postgresql://labeling:labeling@host.docker.internal:5432/labeling \
  saegim-backend
```

## Next Steps

- [Architecture](../architecture/architecture.md) - Understand the system structure
- [API Endpoints](api.md) - API usage
- [Database](../architecture/database.md) - Schema structure
- [Development Guide](../dev/development.md) - How to contribute
