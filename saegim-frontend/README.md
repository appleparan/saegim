# saegim-frontend

Frontend for the saegim labeling platform. Built as a SvelteKit SPA with Svelte 5 Runes.

## Tech Stack

| Category | Technology |
| ---- | ---- |
| **Framework** | SvelteKit (adapter-static SPA) + Svelte 5 (Runes) |
| **Build** | Vite 7, TypeScript |
| **Styling** | Tailwind CSS 4, shadcn-svelte, dark mode via mode-watcher |
| **Canvas** | PDF.js (PDF rendering) + Konva.js (bounding box editor) |
| **Formatter** | oxfmt |
| **Linter** | ESLint |
| **Tests** | Vitest + Testing Library |

## Development

```bash
cd saegim-frontend
bun install

bun run dev           # Development server (localhost:5173)
bun run build         # Production build
bun run preview       # Preview production build
bun run check         # svelte-check type check
bun run test          # Vitest tests
bun run format        # oxfmt formatting
bun run format:check  # Format check
bun run lint          # ESLint check
bun run lint:fix      # Auto-fix ESLint issues
```

## Project Structure

```text
src/
├── routes/                   # SvelteKit file-based routing
│   ├── +layout.svelte        # Root layout
│   ├── +page.svelte          # Home (project list)
│   ├── projects/             # Project detail pages
│   └── label/                # Labeling editor
└── lib/
    ├── api/                  # HTTP client for backend REST API
    ├── components/
    │   ├── ui/               # shadcn-svelte base UI components
    │   ├── canvas/           # PDF.js + Konva.js canvas editor
    │   ├── panels/           # Side panels (attributes, categories, etc.)
    │   ├── layout/           # Layout components
    │   ├── settings/         # Settings components
    │   └── common/           # Shared components
    ├── stores/               # Svelte 5 Runes state management
    ├── types/                # OmniDocBench type definitions
    └── utils/                # Utility functions
tests/                        # Vitest unit tests
```
