## [0.3.0] - 2026-03-02

### Bug Fixes

- Handle empty annotation_data in draw tool and improve OCR error messages ([e60a75e](https://github.com/appleparan/saegim/commit/e60a75e554e73b6a75601faf0a937f315443240c))
- Account for devicePixelRatio in PDF canvas rendering ([c9a7c0d](https://github.com/appleparan/saegim/commit/c9a7c0dfbcbadcc5569d1d39729eb56d19a39792))
- Address code review issues and migrate to AutoModelForImageTextToText ([5dfc3fb](https://github.com/appleparan/saegim/commit/5dfc3fb5c64045449e85cfdfc889a7ee2e6d6009))
- Use full paper PDF for attribute classifier E2E test ([58010b4](https://github.com/appleparan/saegim/commit/58010b45965733581df56e3720a34ae5010db24f))
- Resolve all ty check and ruff lint/format errors ([d6e02b6](https://github.com/appleparan/saegim/commit/d6e02b691754777f87225e9f63c2d114472d7347))
- Resolve lint errors (RUF043 raw strings, oxfmt format) ([297ba94](https://github.com/appleparan/saegim/commit/297ba94a185474c07d5179336a8c07a9bfc45469))
- Apply ruff format after rebase ([24b0eac](https://github.com/appleparan/saegim/commit/24b0eac33cea05b0e2e15cebee4b0099f00dd537))
- Remove unused svelte-ignore comment in ElementList ([36b3c47](https://github.com/appleparan/saegim/commit/36b3c47cbca087ee347bca7a8186b469e31e14ff))
- Install curl before uv installer in Dockerfile ([63252d8](https://github.com/appleparan/saegim/commit/63252d849c6cea3454378a3e8f5065c244f054f3))
- Improve ExtractionPreview banner visibility after accept/re-extract ([6fc25bd](https://github.com/appleparan/saegim/commit/6fc25bd6faa3b1d9ed05e8fb6edf4d0543e5ec18))
- Add missing props to ExtractionPreview test cases ([ff319d9](https://github.com/appleparan/saegim/commit/ff319d9589e603d02657ac4e62dbbc63773e4f3b))
- Remove remaining integrated_server references from text extraction service ([37396f7](https://github.com/appleparan/saegim/commit/37396f72bd90cd956b904dcfab2b5dbb887a4fc4))
- Update toolbar button labels to match new shortcut keys ([042d110](https://github.com/appleparan/saegim/commit/042d110b1072845ed6ece47ee96a6e624c6039be))
- Avoid Svelte $effect infinite loop in OcrSettingsPanel ([cbc958c](https://github.com/appleparan/saegim/commit/cbc958c75463a8e6186bde44d1a1fec78799b78c))
- Remove unused vi import from OcrSettingsPanel test ([e3be774](https://github.com/appleparan/saegim/commit/e3be774756031bd63145c594bbddc571d0856e86))
- Add None guard for text field in docling layout test ([3d1335a](https://github.com/appleparan/saegim/commit/3d1335a292772f4610d155c163e3ce9870556470))

### Documentation

- Add architecture docs for data schema, extraction, labeling ([6a1d7e3](https://github.com/appleparan/saegim/commit/6a1d7e3ed9fb6c97818d69923519e9a0dab61939))
- Merge AGENTS.md details into backend docs ([7c3f9a4](https://github.com/appleparan/saegim/commit/7c3f9a4f1eac1acb7618ee6030f66359160e5a43))
- Slim down AGENTS.md to planning-only guide ([fbac59a](https://github.com/appleparan/saegim/commit/fbac59ae0e66e4fcd739de0b885dc448e3234a75))
- Rename index.md to README.md for GitHub browsing ([cbc9285](https://github.com/appleparan/saegim/commit/cbc9285996c1400b319f7502c17e76475e02e075))
- Replace ASCII architecture diagram with Mermaid ([48702e5](https://github.com/appleparan/saegim/commit/48702e5b6f365008010d6d62a8fe8ba3e172c23d))
- Add Phase 3 (multi-user) and Phase 4 (data curation) roadmap ([e45049e](https://github.com/appleparan/saegim/commit/e45049e65cba3e4e4db6e2d3fced1929a2b67804))
- Update AGENTS.md Phase 2 status and OCR engine count ([e6c5123](https://github.com/appleparan/saegim/commit/e6c5123ae49fb543ef2e27eb59d32333ede9466f))
- Update documentation to reflect Phase 2 completion ([5b6030c](https://github.com/appleparan/saegim/commit/5b6030c2aeb71efd64723c751a54bae5cb115d45))
- Update root README.md to reflect Phase 2 completion ([46d3920](https://github.com/appleparan/saegim/commit/46d3920fe817b092ac5b915834141d838b6eae4d))
- Add missing API endpoints to backend guide ([06119bf](https://github.com/appleparan/saegim/commit/06119bf1ee0d93b666248bf3bc3e74457f4f2150))
- Add PyTorch --extra flags to installation guides ([82afced](https://github.com/appleparan/saegim/commit/82afced435d7d3621dd3b3146917714de5c81b41))
- Add reading-order and relations E2E tests to e2e docs ([4d96168](https://github.com/appleparan/saegim/commit/4d96168839b2691b658bf583b8003caecf55feca))
- Update development guide with --extra flags and full test tree ([56e3862](https://github.com/appleparan/saegim/commit/56e38622b4fc2a2ca16b33397f00f7037993db75))
- Update deployment docs for unified Dockerfile and k8s overlays ([58b0f4a](https://github.com/appleparan/saegim/commit/58b0f4a62bc21f3e2cbe8442bac8b7927094ce1b))
- Update documentation for OCR engine consolidation ([1c0679a](https://github.com/appleparan/saegim/commit/1c0679a3c3375cab49b1fb3f7b56189f36516d18))
- Update documentation for per-element OCR engine selection ([12ef4db](https://github.com/appleparan/saegim/commit/12ef4db52201a13dbf20a2b94af0ce4feeedb699))
- Update documentation for multi-instance OCR engine architecture ([205c899](https://github.com/appleparan/saegim/commit/205c8997a8f01361c623462abd3851fc768dd284))
- Add prompt field to Gemini config examples ([70b87ce](https://github.com/appleparan/saegim/commit/70b87cee341320bd376f84da26578bd977b34e38))

### Features

- Add ExtractTextRequest/Response schemas for region OCR ([0c18ab8](https://github.com/appleparan/saegim/commit/0c18ab8a1c8811cfb89209ed40396d1dbcf98f0b))
- Add text extraction service for region OCR ([9ba4623](https://github.com/appleparan/saegim/commit/9ba4623dc990d4745d997304f7dd00c2741f7fe2))
- Add POST /pages/{page_id}/extract-text endpoint ([11856c5](https://github.com/appleparan/saegim/commit/11856c59244128f37de90d74f919912056b6a989))
- Add auto attribute classifier service ([8483f43](https://github.com/appleparan/saegim/commit/8483f43b0d4293f1aac533fe60e207d3a7d76180))
- Integrate attribute classifier into extraction pipeline ([f7d74f6](https://github.com/appleparan/saegim/commit/f7d74f6ea3e7e26668fc90d8a0081224876a262e))
- Add vitest config and replace playwright dependency ([b497526](https://github.com/appleparan/saegim/commit/b49752619563985780baee444763ef9ac439c0d5))
- Convert API-only tests to vitest ([133a2c1](https://github.com/appleparan/saegim/commit/133a2c17041e740107d74f7a341da6d82f25fd0f))
- Convert health and extraction tests to vitest ([53c8014](https://github.com/appleparan/saegim/commit/53c80140c0af71a9601e49ca274440bb886f6441))
- Convert GPU tests to vitest ([7c4aaed](https://github.com/appleparan/saegim/commit/7c4aaedd4b517e8df661e7409779e2396b266696))
- Add DoclingEngine for document layout detection ([db9a69c](https://github.com/appleparan/saegim/commit/db9a69c282f1a637b58d4647a7cdb1c75f96030c))
- Register docling engine type in factory ([a68d687](https://github.com/appleparan/saegim/commit/a68d687009ccad36cbe6b8116bccf45582de5dbc))
- Add docling to EngineType schema and API config ([ac5bb89](https://github.com/appleparan/saegim/commit/ac5bb89da2ffca1876b185e40da407cf185da070))
- Add docling engine UI and torch to Dockerfile ([4f1ec82](https://github.com/appleparan/saegim/commit/4f1ec822d41c793e43d2fcdd64e508ee5f89765c))
- Add Relation CRUD API endpoints ([8a97306](https://github.com/appleparan/saegim/commit/8a973069849da886ac3b863c0ee2f28caa8e12c7))
- Add Relation tool UI with panel and canvas overlay ([57cdc64](https://github.com/appleparan/saegim/commit/57cdc6407059cc8049364c85c1444f55f327d7fa))
- Add reading order update API endpoint ([da89134](https://github.com/appleparan/saegim/commit/da891343fb06ef02743da2b8a8c41e66416f694f))
- Add reading order store methods and API client ([4201c5d](https://github.com/appleparan/saegim/commit/4201c5dc15152d81d6d071f9885b7e42feec3801))
- Add drag-and-drop reordering to ElementList ([d7fb27b](https://github.com/appleparan/saegim/commit/d7fb27bac8c86fdbcb097509796eb0845d77c3d5))
- Add reading order overlay on canvas with toggle ([062783e](https://github.com/appleparan/saegim/commit/062783ede2480a4258c206a54c8fcf97bb26b666))
- Add keyboard shortcut help popover to labeling editor ([e8237f8](https://github.com/appleparan/saegim/commit/e8237f87c0e028c5c8b95bb0bfe990bb0ff7c8fc))
- Add document re-extract and force-accept functionality ([4994a0a](https://github.com/appleparan/saegim/commit/4994a0a18cdbd7b2f73d7b7f9c13d542d2564fe8))
- Update frontend, e2e tests, and API for new OCR engine types ([da9d1ac](https://github.com/appleparan/saegim/commit/da9d1aca37ce19864282012ffbab2371906c953d))
- Add OCR engine badge to labeling page breadcrumb ([2b72a0f](https://github.com/appleparan/saegim/commit/2b72a0f00c2c7c729a27c69208c2a0d76104cbd2))
- Add backend support for per-element OCR engine selection ([f0068ab](https://github.com/appleparan/saegim/commit/f0068ab8ff30ab5aa84af79a85d5a1a74e36b5aa))
- Add multi-engine settings UI with visual enabled/disabled states ([a74fe6e](https://github.com/appleparan/saegim/commit/a74fe6ec4f061cd7cdc2a108a3fff131e3fcb5b5))
- Add engine selector to OCR popup in labeling page ([76b1483](https://github.com/appleparan/saegim/commit/76b148307b055599ff9e599828db9778f610a26b))
- Add default engine indicator to labeling page breadcrumb badge ([0c6b7a0](https://github.com/appleparan/saegim/commit/0c6b7a02948dc75711dfbcb8f18b576505c776b1))
- Add multi-instance OCR engine schemas and config normalization ([5ba4848](https://github.com/appleparan/saegim/commit/5ba4848df698032c08e456f9553fc6ffa0303aa6))
- Add build_engine_by_id and engine_id support across services ([2076534](https://github.com/appleparan/saegim/commit/20765341b1dec345f7d04c7f2397abb6be9f028f))
- Rewrite OCR config API with engine CRUD endpoints ([0669c5a](https://github.com/appleparan/saegim/commit/0669c5ac269958843b1c536b77339b37ec835d40))
- Update frontend types and API for multi-instance engines ([508f1d9](https://github.com/appleparan/saegim/commit/508f1d944808a4dfff729b165a0d9d4cd66970e5))
- Rewrite settings UI with multi-instance engine cards ([394b021](https://github.com/appleparan/saegim/commit/394b021de32d4a04a2760334b103d60b47172142))
- Add custom prompt support to Gemini OCR backend ([c8007bb](https://github.com/appleparan/saegim/commit/c8007bbf262eca88db1955d645f7cdc000bcb777))
- Add prompt input and update model list in Gemini UI ([434c7d1](https://github.com/appleparan/saegim/commit/434c7d1b5ea840cbb33c83a96a621f43e45d0867))

### Miscellaneous Tasks

- Remove playwright and fix formatting ([e3dfb32](https://github.com/appleparan/saegim/commit/e3dfb329705f714e8ed5bf4dfecc85dcb6175c91))
- Rewrite README to reflect Vitest migration ([26afa61](https://github.com/appleparan/saegim/commit/26afa615e94cbfb6abea38d5e33006faafe4e08b))
- Update root README — fix tech stack and Playwright refs ([6e09a2d](https://github.com/appleparan/saegim/commit/6e09a2d99ac4d06270948dad8eec781cb2faf1a0))
- Rewrite frontend README to document actual project ([6f78414](https://github.com/appleparan/saegim/commit/6f78414b486987cec5fbb09c409c21a2fb28a82f))
- Rewrite backend README to document actual project ([5cce64b](https://github.com/appleparan/saegim/commit/5cce64b8bb37df14000514f32687aafe98871e3e))
- Clean up Playwright/Prettier refs from config files ([df97564](https://github.com/appleparan/saegim/commit/df9756446f370a19becf32944c7ef161dcb65298))
- Simplify AGENTS.md — remove Phase 3+ roadmap and collaboration features ([8eadb27](https://github.com/appleparan/saegim/commit/8eadb2796bf7699139748ec2f66e5d7ed942be21))
- Upgrade dependencies and add torch/torchvision optional extras ([a2652ce](https://github.com/appleparan/saegim/commit/a2652ce0b2c96507491614bd18d8a4802b3e2e91))
- Update bun.lock configVersion field ([c45f81b](https://github.com/appleparan/saegim/commit/c45f81b3b3bb9b88605d746599e27267f805bc65))
- Fix kustomize commonLabels deprecation warning ([601c704](https://github.com/appleparan/saegim/commit/601c7048667774f07b7a9f2e27934b9ec22e6e40))
- Remove ppstructure service from docker-compose ([e27ce91](https://github.com/appleparan/saegim/commit/e27ce911fc1ccbc8b2c1d4265ec23d18d0bdd0be))
- Update vLLM default model to prithivMLmods/chandra-FP8-Latest ([05020fd](https://github.com/appleparan/saegim/commit/05020fdeebc9430f01b4a5355039c762b52e265c))
- Fix all oxlint warnings in frontend ([2df7423](https://github.com/appleparan/saegim/commit/2df74237128ebe8a1ac145e9765e89076dbbc5d5))
- Migrate frontend linting from eslint to oxlint ([a365811](https://github.com/appleparan/saegim/commit/a365811f2d7e2de813ab01962551834457c47f9a))
- Add DB migration for engine type renames ([da1ebe8](https://github.com/appleparan/saegim/commit/da1ebe817c8b33c296a8b396bbce7120b6f424cc))
- Remove unnecessary migration file ([9783f2a](https://github.com/appleparan/saegim/commit/9783f2af8cbd0f1cbc22b4c4c4da9628373658b9))
- Remove IMPLEMENTATION_PLAN.md after PR creation ([2bb4680](https://github.com/appleparan/saegim/commit/2bb46803174927de4ad8ca8be7a963e73b42f81c))
- Remove dead legacy OCR schemas and unused utils ([e66c6f5](https://github.com/appleparan/saegim/commit/e66c6f58718af091d11a15d9822e1ea29577dd99))
- Pin @types/node to LTS version in e2e ([814f447](https://github.com/appleparan/saegim/commit/814f44741908bb4b6487a449fd2f0488b675f611))

### Refactor

- Reorganize docs design/ to architecture/ ([3fbfa9e](https://github.com/appleparan/saegim/commit/3fbfa9e8a836c53fb62ec824ffeafef4e9bfc1ae))
- Simplify Dockerfile to two independent stages ([fa89877](https://github.com/appleparan/saegim/commit/fa89877c310ca5d096417938a70534859fc5335e))
- Simplify relation display with compact arrow notation and hover tooltip ([07c0512](https://github.com/appleparan/saegim/commit/07c05121dc5d267f8c2d85e024e803f5f30414f9))
- Consolidate OCR engines from 5 to 4 types ([22b2470](https://github.com/appleparan/saegim/commit/22b2470ea0456da93371880a19328ef69a114208))
- Optimize keyboard shortcuts for left-hand operation ([edc4198](https://github.com/appleparan/saegim/commit/edc41982a29ee0bd9ce7752208e3f0744f032030))

### Styling

- Fix linting and formatting in attribute classifier tests ([fc76052](https://github.com/appleparan/saegim/commit/fc76052048aba785d15aafb13b6126c7d30f5738))
- Fix oxfmt formatting in PdfRenderer test ([7114ec5](https://github.com/appleparan/saegim/commit/7114ec57d061c9f8462522f19adfa277bb4b8c13))
- Apply oxfmt formatting to pages.ts and projects.ts ([b91aa12](https://github.com/appleparan/saegim/commit/b91aa1247d1f7833bf4645cc540065da3211f2f7))
- Apply oxfmt formatting to projects.ts ([e7c4d7a](https://github.com/appleparan/saegim/commit/e7c4d7acc7b0a291be3c99579727558fe5b73123))
- Add type-ignore comments for intentional validation tests ([a4d2bd3](https://github.com/appleparan/saegim/commit/a4d2bd3ffdf1d9d943bcdf4770144c151d4d95e8))

### Testing

- Add unit tests for text extraction service ([ca435be](https://github.com/appleparan/saegim/commit/ca435beafaf90010c3b6a5b5a4bb29ec0377ca2a))
- Add unit tests for attribute classifier ([721661e](https://github.com/appleparan/saegim/commit/721661e26a3ba70984221d383a2b2293703bb11f))
- Add e2e tests for auto attribute classifier ([45df2af](https://github.com/appleparan/saegim/commit/45df2af449e3d5b09b15a6f3acb703457104c612))
- Add unit tests for DPR-aware PDF rendering ([54b8c6d](https://github.com/appleparan/saegim/commit/54b8c6de1c94078ab7df47be46310171a1cc8dee))
- Add OTSL-to-HTML tests and expand valid category types ([f8ed3b3](https://github.com/appleparan/saegim/commit/f8ed3b3cb5ccb6b541030b1feb86158108cfb724))
- Add E2E tests for Relation CRUD API ([7d25d81](https://github.com/appleparan/saegim/commit/7d25d81e6aac6866d5c17bf8d4b0eb28e497f68a))
- Add reading order E2E tests ([bcb81c6](https://github.com/appleparan/saegim/commit/bcb81c69c6d7d6a383a4039810cde97653d53940))
- Add unit tests for per-element OCR engine selection ([19e30f8](https://github.com/appleparan/saegim/commit/19e30f8d1851b3cafa1a7197b61e882c25de9ae2))
- Add E2E tests for enabled_engines and available-engines API ([7a9e9bd](https://github.com/appleparan/saegim/commit/7a9e9bdf6350a4a40a63d17034da147e62fc2b2a))
- Rewrite E2E tests for multi-instance OCR engine APIs ([2d31170](https://github.com/appleparan/saegim/commit/2d311706943353ab6a92d39ee6daa538031c0232))
- Add unit tests for Gemini custom prompt ([138f183](https://github.com/appleparan/saegim/commit/138f18310c72bba720f654a2067077d5d5c6ecdb))
- Update E2E tests for Gemini prompt and model changes ([98253a0](https://github.com/appleparan/saegim/commit/98253a09015ea11ec75c2a01c9a02b214834ede4))

### Build

- Replace Prettier with oxfmt for faster formatting ([54538ef](https://github.com/appleparan/saegim/commit/54538ef1d76bc8cee81f70ea158fad085913ebcf))

### Infra

- Unify backend Dockerfiles with ARG-based CPU/GPU switching ([2e7537b](https://github.com/appleparan/saegim/commit/2e7537b3c362659d7e010b2a309409ecb5e475ed))
- Unify docker-compose with profile-based GPU services ([8ec3e3f](https://github.com/appleparan/saegim/commit/8ec3e3f2b424f41243bd5f36647f3715f82acf4e))
- Add Makefile, .env.gpu, and update .env.example ([b572888](https://github.com/appleparan/saegim/commit/b572888791f97a9ad0cc84bbd1d28b67cf919957))
- Restructure k8s to base/overlay with GPU support ([5f0edbe](https://github.com/appleparan/saegim/commit/5f0edbe8fb72dcb47da9069b1dcd0f75388d9d69))

<!-- generated by git-cliff -->
