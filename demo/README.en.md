# saegim Demo Recording

> [한국어](README.md) | **English**

Automatically demonstrates key features using Playwright and converts them to GIFs.

## Prerequisites

```bash
# 1. Start services with Docker Compose
cd .. && make up

# 2. Verify service health check
curl -f http://localhost:15000/api/v1/health

# 3. Install Playwright
cd demo
bun install
bunx playwright install chromium
```

## Recording

### Per-feature recording (recommended)

A separate video is generated for each feature. Login/setup steps are not included in the videos.

```bash
# Full feature demo (setup -> project-setup -> labeling -> overview)
bunx playwright test --project=setup --project=demo-project-setup --project=demo-labeling --project=demo-overview

# Record individual features
bunx playwright test --project=setup --project=demo-project-setup   # Project creation + OCR + upload
bunx playwright test --project=setup --project=demo-labeling        # Label editor
bunx playwright test --project=setup --project=demo-overview        # Project overview + export
```

### All-in-one recording (legacy)

Records the entire flow as a single video (including login).

```bash
bunx playwright test --project=demo
```

Videos are saved as `.webm` files in the `test-results/` directory (1920x1080).

## Demo Project Structure

| File | Description | Video |
| ------ | ------ | ------ |
| `auth-setup.ts` | Login + dark mode + save storageState | None |
| `demo-project-setup.spec.ts` | Create project -> OCR setup -> PDF upload | Yes |
| `demo-labeling.spec.ts` | Accept OCR extraction -> inspect elements -> element index -> bbox -> reading order -> save | Yes |
| `demo-overview.spec.ts` | Task status dashboard -> export | Yes |
| `record-demo.ts` | All-in-one legacy (full flow) | Yes |
| `helpers.ts` | Common utilities + API helpers | - |

## GIF Conversion

```bash
bash convert-to-gif.sh                              # test-results/ -> output/ (preserve names, 800px, 12fps)
bash convert-to-gif.sh output/                       # webm in output/ -> gif in the same directory
bash convert-to-gif.sh video.webm                    # Convert a single file
bash convert-to-gif.sh test-results/ gifs/ 640 8     # Smaller files (for GitHub)
bash convert-to-gif.sh test-results/ gifs/ 1280 15   # High quality
```

## Customization

- **Speed control**: Adjust `PAUSE_*` constants in `helpers.ts` and `slowMo` in `playwright.config.ts`
- **Add scenarios**: Add `test.step()` blocks in each spec file

## Environment Variables

| Variable | Default | Description |
| ------ | -------- | ------ |
| `BASE_URL` | `http://localhost:13000` | Frontend URL |
| `API_URL` | `http://localhost:15000` | Backend API URL |
| `ADMIN_PASSWORD` | (auto-detect) | Admin password |
| `GEMINI_API_KEY` | (from .env) | Gemini API key |
