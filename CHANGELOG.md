## [0.0.0] - 2026-02-15

### Bug Fixes

- Correct Dockerfile HEALTHCHECK endpoint paths ([d55dae2](https://github.com/appleparan/saegim/commit/d55dae2276e043d316ebbdc3735043358016830a))
- Update postgres volume mount for postgres 18+ compatibility ([8e7ad1a](https://github.com/appleparan/saegim/commit/8e7ad1ae0f99bd19da20af235f5f62e6cbb31f5b))
- Generate en_US.UTF-8 locale in Dockerfiles ([67bae52](https://github.com/appleparan/saegim/commit/67bae52de48970b95608469ecd54de0d489b78a8))
- Align frontend API paths with backend /api/v1 prefix ([f1deddb](https://github.com/appleparan/saegim/commit/f1deddb2f8ce630880459a1b1a309b09e475fd57))
- Resolve svelte-check type errors in App.svelte ([5529f7e](https://github.com/appleparan/saegim/commit/5529f7e7ec1d1a2df0528976437367a1c06492c4))
- Handle 204 No Content in API client, add Docker Compose docs to README ([d882eb7](https://github.com/appleparan/saegim/commit/d882eb708cef43e24ddd618676d9c3ed3d91c59c))
- Prevent effect_update_depth_exceeded infinite loop ([18bb7eb](https://github.com/appleparan/saegim/commit/18bb7eb9b4f2e5c0cef95714a50614069844f31b))
- Update test selectors and helpers for Playwright CJS compatibility ([3cce53a](https://github.com/appleparan/saegim/commit/3cce53a4256706c961202037e69ab0dc29406560))
- Resolve effect_update_depth_exceeded and sidebar tab switching ([ebd9e9d](https://github.com/appleparan/saegim/commit/ebd9e9de77d88c436e5486e2c67fed8fb6e87bd0))
- Resolve ruff and ty check lint errors in test files ([f41a61a](https://github.com/appleparan/saegim/commit/f41a61abc9efdd5307cbccbf588ccba0df605d38))
- Toolbar z-index above text overlay and health test locator ([28873cd](https://github.com/appleparan/saegim/commit/28873cd751062838023333970be623f2cb9409f5))
- Correct Korean name in README and fix release script shebang ([99cc84e](https://github.com/appleparan/saegim/commit/99cc84eae6e937598765f3172c3d5c99bdeb7412))

### Documentation

- Fix markdownlint errors in AGENTS.md ([9b0b151](https://github.com/appleparan/saegim/commit/9b0b1517e580f88c1cbaca16e9c472d72b9a0582))
- Rewrite documentation for backend MVP ([2ed8e83](https://github.com/appleparan/saegim/commit/2ed8e8388c406e61b4ee50c980f1aeb909313812))
- Add frontend documentation ([27e436f](https://github.com/appleparan/saegim/commit/27e436fc58557e0de26fff87b5317b8b9dcc94e0))
- Add project README with architecture and setup guide ([99ee226](https://github.com/appleparan/saegim/commit/99ee226151a8c54e0afda510f375317aa70b6820))
- Reorganize docs into guide/design/dev directories ([4657afc](https://github.com/appleparan/saegim/commit/4657afc7b103e3956ac80e5ddaf840ce93a31cd7))
- Add root-level quickstart and deployment guides ([ec393ae](https://github.com/appleparan/saegim/commit/ec393ae446dd9d339ce59065b30d7ee83a776203))
- Add analysis_data schema, expand Phase 4 roadmap, fix markdownlint ([b2e0a43](https://github.com/appleparan/saegim/commit/b2e0a438ac045f545aa13257fa9319a73c7af06a))

### Features

- Add saegim-backend project ([911f161](https://github.com/appleparan/saegim/commit/911f1613e2f7a880b21d067a4023fe82d58414b0))
- Add saegim-frontend project ([ca5cf2c](https://github.com/appleparan/saegim/commit/ca5cf2cb1824699fc32c1b6277bf266a98dae99e))
- Add core database infrastructure and migration SQL ([53ce018](https://github.com/appleparan/saegim/commit/53ce01859f0eb51df60033840f3b36dd101f711e))
- Add Pydantic schemas for API request/response validation ([98cb45c](https://github.com/appleparan/saegim/commit/98cb45c0a5e91822c5e53f17fefed21ea42cee40))
- Add repository layer with raw SQL queries ([6fb81d4](https://github.com/appleparan/saegim/commit/6fb81d468eb65fbd373bf80e35035b6df0ccdbf7))
- Add service layer for business logic ([db72112](https://github.com/appleparan/saegim/commit/db72112f1318262d03bbd4aa9f92a755523b1eea))
- Add API routers and update app.py with DB lifespan ([8b91831](https://github.com/appleparan/saegim/commit/8b918318192fc2a76e72e12b546a5171d5ec0b42))
- Merge backend MVP implementation ([2fda365](https://github.com/appleparan/saegim/commit/2fda36548747d804a31bebba13b31171c9f88453))
- Setup frontend project with Tailwind CSS 4, svelte-spa-router, and Konva.js ([83d321e](https://github.com/appleparan/saegim/commit/83d321ee900dc8bbc295baa930d7f14f9c55b882))
- Add OmniDocBench type definitions ([bcd32b3](https://github.com/appleparan/saegim/commit/bcd32b344d0ff7ccc482ed9004500cd8b63d3f2a))
- Add utility functions with tests ([fb54746](https://github.com/appleparan/saegim/commit/fb547464de20dedc621e010ac8e82f91c84b4027))
- Add API client layer for all backend endpoints ([e204d11](https://github.com/appleparan/saegim/commit/e204d11b983cdc90ffd83fd78fd3f673b4a0973f))
- Add Svelte 5 rune-based state stores ([fd9cd96](https://github.com/appleparan/saegim/commit/fd9cd96093d2a69277013663cbd4ecff900dac0a))
- Add common UI components and layout ([362bcf4](https://github.com/appleparan/saegim/commit/362bcf42ef0983df7d14c5ceea766be6dea090eb))
- Implement page shells (ProjectList, DocumentList, LabelingPage) ([931ce16](https://github.com/appleparan/saegim/commit/931ce161cbc232ccffee06d6394c6b74ff51cb35))
- Implement Canvas + Bbox editing with Konva.js ([b80931a](https://github.com/appleparan/saegim/commit/b80931a5522be34a445de26e889eb8fb75c58af5))
- Implement side panel components ([606d4e2](https://github.com/appleparan/saegim/commit/606d4e2a8e35725cf586ce7fd6b2cb0d075e7e13))
- Add keyboard shortcuts and unsaved changes warning ([8054183](https://github.com/appleparan/saegim/commit/80541832c0f059b439555e93075b0f11812d234a))
- Merge frontend MVP implementation ([69f7f8c](https://github.com/appleparan/saegim/commit/69f7f8c8990574f5e2c0e9c1565f07af99f1be4e))
- Add docker-compose with CPU/GPU profiles ([c890c50](https://github.com/appleparan/saegim/commit/c890c50719ab2243b20adb1940ae4bcc14f1b87f))
- Improve docker-compose with networks, healthchecks, restart policies ([928c93f](https://github.com/appleparan/saegim/commit/928c93f84226491a26fccd0322f9afd12169df61))
- Add Kubernetes deployment manifests ([30aa8ce](https://github.com/appleparan/saegim/commit/30aa8ce2213006314225719ffa7747bc6bbc8c59))
- Adopt gosu + entrypoint pattern for appuser handling ([57ffd3d](https://github.com/appleparan/saegim/commit/57ffd3db2cc74a1c5f29c1305f3d42f8676eb55b))
- Add GET /projects/{id}/documents endpoint ([5033e6b](https://github.com/appleparan/saegim/commit/5033e6be7a98b87e8563609644d33f2ae9fde91d))
- Add delete APIs for projects and documents ([aeac5cd](https://github.com/appleparan/saegim/commit/aeac5cd2016f6e2832e5b23f4951fab2ca41fd42))
- Add Playwright e2e tests with separate Docker Compose ([bdd6165](https://github.com/appleparan/saegim/commit/bdd6165e825f57980c2a2c7122967abe71b2f263))
- Fix PDF image display, add labeling navigation, modernize UI ([07ec167](https://github.com/appleparan/saegim/commit/07ec167696f956d857ef228713d4ee26d38e1f28))
- Add category grouping constants and text layout utilities ([1c5c016](https://github.com/appleparan/saegim/commit/1c5c01603b913eb49f83fa568e45d67ba9ceeee5))
- Implement hybrid 3-layer labeling with tests ([05c22d5](https://github.com/appleparan/saegim/commit/05c22d5902c12fba0de8e7e5bc7057c0180b6e0e))

### Miscellaneous Tasks

- Add PyMuPDF dependency for PDF to image conversion ([cea0fd0](https://github.com/appleparan/saegim/commit/cea0fd0de5cf60ca99a26b71514a92e585b60451))
- Fix lint issues and formatting ([b5d050f](https://github.com/appleparan/saegim/commit/b5d050f1f3192650e400b4da61a95889bacc7da8))
- Upgrade postgres image to 18.2-trixie ([bb6b6d5](https://github.com/appleparan/saegim/commit/bb6b6d5c432ceaef582996d9195742c88ac66ade))
- Comment out backend-gpu service in docker-compose ([889f6e7](https://github.com/appleparan/saegim/commit/889f6e77dbd81a180ba0bd71f004835f31ea2ab5))
- Change default host ports to avoid conflicts ([e6127e7](https://github.com/appleparan/saegim/commit/e6127e72f1cdb5a3c27b56076b727d10c546d28b))
- Add root .gitignore for storage and .env ([d235105](https://github.com/appleparan/saegim/commit/d235105aba14da944abfe84e2a56b25de95c2e55))
- Add markdownlint configs and fix markdown lint errors ([3579e12](https://github.com/appleparan/saegim/commit/3579e1223b61a0f228805b6c305d19b342a37e66))

### Refactor

- Remove demo predict endpoint and related code ([e817900](https://github.com/appleparan/saegim/commit/e81790029d684648a48d7affdffe2cba3dff7315))
- Move release script and GitHub workflows to monorepo root ([52f57a4](https://github.com/appleparan/saegim/commit/52f57a47c92775b1dc865942364ac1329c42f433))

### Testing

- Add tests for all new API endpoints ([7235b44](https://github.com/appleparan/saegim/commit/7235b44f1de1d726b7cd08ae60c6403ad10c93b1))
- Add service layer tests ([78d1b57](https://github.com/appleparan/saegim/commit/78d1b57fed9f72c339b6807aeeb7e4f0d8319265))

<!-- generated by git-cliff -->
