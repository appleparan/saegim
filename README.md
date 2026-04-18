# saegim

> [Korean](README.ko.md) | **English**

A Human-in-the-Loop labeling platform for Korean document VLM benchmarks.

Upload PDF documents, automatically convert them into per-page images,
and label bounding boxes, categories, and attributes of layout elements
in a web-based editor to export as
[OmniDocBench](https://github.com/opendatalab/OmniDocBench)-standard JSON.

## Key Features

### Project Setup & PDF Upload

Create a project, configure an OCR engine, and upload PDFs to
automatically convert them into per-page images.

<img src="demo/output/Project-setup.gif" width="100%" alt="Project Setup">

### Label Editor

Review layout elements automatically extracted by AI OCR, and annotate
them using a variety of tools including bounding box drawing, element
index overlays, and reading order editing.

<img src="demo/output/Label-editor-extraction-annotation-overlays.gif" width="100%" alt="Project Setup">

### Project Overview & Export

Monitor progress on the task dashboard and export to
OmniDocBench-standard JSON.

<img src="demo/output/Project-overview-dashboard-and-export.gif" width="100%" alt="Project Setup">

## Detailed Features

- **PDF Conversion** — Automatically convert PDFs to high-resolution per-page PNGs
- **Multiple OCR Engines** — Register and manage engines per project
  (Gemini API, vLLM, Docling+OCR, pdfminer)
- **Automatic Attribute Classification** — Auto-classify page, table, text, and formula attributes
- **Canvas Editor** — Create, edit, and delete bounding boxes with zoom/pan and keyboard shortcuts
- **Reading Order Editor** — Drag-and-drop reordering with canvas overlay
- **Relation Tool** — Element relation CRUD with SVG arrow visualization
- **OmniDocBench Labeling** — 15 Block-level + 4 Span-level categories
- **Authentication & Authorization** — JWT-based auth with system roles
  (admin/annotator/reviewer)
- **Admin Dashboard** — User, project, and system statistics management
- **JSON Export** — Export in OmniDocBench-standard format

## Quickstart

### Docker Compose (Recommended)

Get started in 3 steps with just Docker installed.

```bash
# 1. Set up environment variables
cp .env.example .env

# 2. Build + run
make up
# or: docker compose up -d --build

# 3. Open in browser
#    Frontend: http://localhost:13000
#    API docs: http://localhost:15000/docs
```

If you need GPU mode, install NVIDIA Container Toolkit first:

```bash
make up-gpu
```

### Local Development

```bash
# Backend
cd saegim-backend
uv sync --group dev --group docs --extra cpu    # CPU (or --extra cu128)
uv run uvicorn saegim.app:app --reload --host 0.0.0.0 --port 5000

# Frontend
cd saegim-frontend
bun install && bun run dev
```

Local access: Frontend `http://localhost:5173` / API docs `http://localhost:5000/docs`

> For database setup, migrations, and other detailed guides, see
> [Backend Getting Started](docs/en/backend/guide/getting-started.md).

## Documentation

| Document | Description |
| ---- | ---- |
| [Architecture Overview](docs/en/architecture/README.md) | System structure, tech stack, authentication |
| [Backend Architecture](docs/en/backend/architecture/architecture.md) | Layered architecture, data flow |
| [Frontend Architecture](docs/en/frontend/architecture/architecture.md) | Component structure, state management |
| [API Guide](docs/en/backend/guide/api.md) | REST API endpoints |
| [Extraction Pipeline](docs/en/architecture/extraction-pipeline.md) | OCR engine architecture |
| [Data Schema](docs/en/architecture/data-schema.md) | DB structure, OmniDocBench format |
| [Multi-User Collaboration](docs/en/architecture/multi-user-collaboration.md) | Auth, roles, task workflow |
| [Deployment Guide](docs/en/deployment/quickstart.md) | Docker, Kubernetes |
| [Planning Guide](AGENTS.md) | Project vision, roadmap |

## Development

```bash
# Backend
uv run ruff format                  # Formatting
uv run ruff check --fix             # Lint
uv run ty check                     # Type check
uv run pytest --cov                 # Test + coverage

# Frontend
bun run check                       # Type check
bun run test                        # Test
bun run build                       # Production build
```

## License

Apache-2.0 License
