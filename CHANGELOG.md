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

## [0.2.0] - 2026-02-23

### Bug Fixes

- Make E2E tests rendering-mode-aware for PDF.js and image fallback ([2f4008a](https://github.com/appleparan/saegim/commit/2f4008abe2f1e51931f4718faa9dd06ac1eecf90))
- Make E2E tests mode-agnostic without if/else branching ([676d304](https://github.com/appleparan/saegim/commit/676d3044da60edce140f86abd58a02d008caa431))
- Resolve all ty check diagnostics in test files ([8739925](https://github.com/appleparan/saegim/commit/8739925fc13284fece03fa2faa4a4f72d6ae1aa1))
- Improve healthcheck settings in docker-compose.yml ([8080ae4](https://github.com/appleparan/saegim/commit/8080ae477a6dce2515e88c0b56a53c76956df81f))
- Correct VITE_API_URL in .env.example files ([8819106](https://github.com/appleparan/saegim/commit/8819106220fccf29e65eeb21a6e55b14361a472d))

### Documentation

- Update documentation for pdfminer.six and pypdfium2 migration ([b0efdd0](https://github.com/appleparan/saegim/commit/b0efdd08d2265df6ca4e6273688d31af26caf84b))
- Add Apache License 2.0 ([1306ba9](https://github.com/appleparan/saegim/commit/1306ba93bf32510dd98032860ff61c7bfe5c2876))

### Features

- Add drag-and-drop PDF upload with overlay UI ([881b580](https://github.com/appleparan/saegim/commit/881b580653655389622d40749c3dd85e04d7004c))

### Refactor

- Replace PyMuPDF dependency with pdfminer.six and pypdfium2 ([52d6115](https://github.com/appleparan/saegim/commit/52d6115d99ab682bc16688157e047a3f6703174d))
- Replace fitz rendering with pypdfium2 and pdfminer.six extraction ([54fd4f0](https://github.com/appleparan/saegim/commit/54fd4f0b7b870951f2c2066ce5f1f5493a24f2a5))
- Update frontend and e2e tests for pdfminer engine type ([48ca206](https://github.com/appleparan/saegim/commit/48ca206d0d01552ed8787d81ddbb2d576b5d7bed))
- Remove pymupdf backward compatibility entirely ([7a55e8e](https://github.com/appleparan/saegim/commit/7a55e8e77172f704174203ab4849f3c2e9c4e06c))

### Styling

- Fix prettier formatting in types.ts ([13ebd61](https://github.com/appleparan/saegim/commit/13ebd618d8120eb00120db9c595d80d2c9e702e2))

### Testing

- Add drag-and-drop PDF upload tests ([2acfa2d](https://github.com/appleparan/saegim/commit/2acfa2de7bd0e5c8052533b903cc9acf09eebb03))

## [0.1.0] - 2026-02-22

### Bug Fixes

- Correct TestGetPageData mocks to use get_by_id_with_context ([4988262](https://github.com/appleparan/saegim/commit/4988262ed6dbf42941a9b2de7f759b52ab22e5ae))
- Resolve ruff check and ty check errors ([36fb85a](https://github.com/appleparan/saegim/commit/36fb85a266c27ad51a2d91bb92b8602168ce4846))
- Remove unused noqa directives and prefix unused variables ([44c0340](https://github.com/appleparan/saegim/commit/44c03401980633f3bf9f7eaf9b291888d8719265))
- Resolve markdownlint errors across markdown files ([150a8b3](https://github.com/appleparan/saegim/commit/150a8b391ee9944747199d27d68d431eacd8df6e))
- Update migration path and vllm gpu-memory-utilization in docker-compose ([912a956](https://github.com/appleparan/saegim/commit/912a9567188d4526fca5cea5d4402faa11c6181f))
- Fix postgres init.sql path and exclude gpu from default test ([6316c22](https://github.com/appleparan/saegim/commit/6316c22c2eca71cb82fc6800d6c8004b021148a3))
- Replace gemini-2.0-flash with gemini-3-flash-preview and add test-then-save ([55ce632](https://github.com/appleparan/saegim/commit/55ce632625ea543ab0c0795869ba3d7ccb63152e))
- Replace assert with RuntimeError, eliminate PT019 with new=MagicMock() ([3b1909e](https://github.com/appleparan/saegim/commit/3b1909e353000bd4f2626cc17e96048aa5f54faf))
- Register Celery task explicitly and handle vLLM JSON quirks ([2bb462a](https://github.com/appleparan/saegim/commit/2bb462a2cf57ce4a1a702dad1577718a48d750d6))
- Improve vLLM JSON parsing with partialjson for robust LLM output handling ([06c9016](https://github.com/appleparan/saegim/commit/06c9016d464d94da46dd5b76e6aad35c62a9f622))
- Simplify E2E test PDF to single page and fix path resolution ([0c4d940](https://github.com/appleparan/saegim/commit/0c4d9402bdcb69b3dea2f147cc2eb4f6e4e51ff6))
- Ensure canvas text overlay works in dark mode ([6570ca5](https://github.com/appleparan/saegim/commit/6570ca5f24019ebac213f1f5828dd3ad149f9a10))
- Make viewport updates atomic to fix bbox zoom alignment ([854e7b1](https://github.com/appleparan/saegim/commit/854e7b129a49f72f66a5ee3bf625db6a4f71f836))
- Add pdf_path to mock page record for labeling service tests ([aa744e9](https://github.com/appleparan/saegim/commit/aa744e9e3128195b989a00e22b36fc8f573e1056))
- Update E2E selector to use shadcn bg-muted class ([335c7d2](https://github.com/appleparan/saegim/commit/335c7d22c09c9afa24f1a7135cc675cfa7bc7a24))
- Cast mock pageProxy to PDFPageProxy type in HybridViewer test ([4af3117](https://github.com/appleparan/saegim/commit/4af31170a8803c642032cfd3a004377d56945d1e))
- Use robust selectors in E2E tests ([62c17db](https://github.com/appleparan/saegim/commit/62c17db011a847c5556c901a4469157080f82824))
- Ensure PDF.js vector rendering works correctly ([d86ea81](https://github.com/appleparan/saegim/commit/d86ea81936907a85f241f724438f2b0b1a1f02e2))
- Apply semantic theme tokens to PageNavigator for dark mode ([23b8ca9](https://github.com/appleparan/saegim/commit/23b8ca9abd721701dca4236926ec7e658adcec28))
- Improve OCR feedback and ExtractionPreview status handling ([608ec2f](https://github.com/appleparan/saegim/commit/608ec2fa3b69e20c3c1c588bc5ca3b7ca8c834dc))
- Update E2E selectors for icon-based toolbar buttons ([6442a6c](https://github.com/appleparan/saegim/commit/6442a6c02e5182028fbffcc3b800c4ed2d680ea7))
- Improve delete button visibility in dark mode ([422a583](https://github.com/appleparan/saegim/commit/422a5830d08a47911ca29a5f340a9315f42c5563))
- Make PageNavigator collapsible so ExtractionPreview stays visible ([fb1da6b](https://github.com/appleparan/saegim/commit/fb1da6b7ed131d922cf19c1d5f5e791bfef9de04))
- Apply viewport transform on BboxLayer init for correct bbox alignment ([f850224](https://github.com/appleparan/saegim/commit/f850224397fe22f419d71318a32f31db8e4bc3be))
- Use Vite ?url import for PDF.js worker path ([2f2148a](https://github.com/appleparan/saegim/commit/2f2148a43f8928b2883fe487aef8067311825f02))
- Keep ExtractionPreview visible in left panel ([aea76f8](https://github.com/appleparan/saegim/commit/aea76f8a5b04ab3d218b1d06e516493e2b04daec))
- Use non-minified PDF.js worker with new URL() pattern ([b3b848b](https://github.com/appleparan/saegim/commit/b3b848b5a7c26743490d7dfd53a25ea14c6ce3c3))
- Add .mjs MIME type to nginx for PDF.js worker loading ([83145de](https://github.com/appleparan/saegim/commit/83145de0071f81f9652d48873bf0ca5110a71192))

### Documentation

- Update documentation for PDF text/image extraction feature ([e35f921](https://github.com/appleparan/saegim/commit/e35f921d8bdc91fe408d8f141582f9952a1bc968))
- Update AGENTS.md for MinerU + Celery integration, add sample PDFs ([b0e6f09](https://github.com/appleparan/saegim/commit/b0e6f09a6cc8e044153e3a9325516cb29725cdd9))
- Update AGENTS.md for AGPL separation and fix pytest doctest conflict ([536dbde](https://github.com/appleparan/saegim/commit/536dbde249ccd51fdf73543366498ce56f7f1418))
- Update documentation for OCR provider feature ([#7](https://github.com/appleparan/saegim/issues/7)) ([4363d9c](https://github.com/appleparan/saegim/commit/4363d9c37d150aeb1610f01a98fb1a420196a704))
- Update documentation for 2-stage OCR pipeline ([#9](https://github.com/appleparan/saegim/issues/9)) ([32e7ef1](https://github.com/appleparan/saegim/commit/32e7ef17ae51644f0bf72fe9d6c1dd65a3fe1ccd))
- Remove stale MinerU references from frontend docs and AGENTS.md ([6069f99](https://github.com/appleparan/saegim/commit/6069f9941f402b2092f6a9ed828ed0833a7169fd))
- Consolidate docs into root docs/ by domain ([1440b41](https://github.com/appleparan/saegim/commit/1440b418bf2663f2c50530dc5142143315003c12))
- Update AGENTS.md for engine_type OCR architecture ([06a5d2b](https://github.com/appleparan/saegim/commit/06a5d2bbe54ca7eccf6bb8e2736a9833fc9f5f87))
- Add e2e README with test execution guide ([6f4b669](https://github.com/appleparan/saegim/commit/6f4b6691e7980098008397af03a1db037fb5f62a))
- Update documentation for engine_type OCR architecture ([f5fcb29](https://github.com/appleparan/saegim/commit/f5fcb29cf3c0955a95cc58120352e285903d8101))
- Update docs for shadcn-svelte + dark mode migration ([6137451](https://github.com/appleparan/saegim/commit/613745143e27134dffe7ec55c4f3e1890399a0eb))
- Fix markdownlint MD013 line-length in architecture.md ([7b59421](https://github.com/appleparan/saegim/commit/7b59421b25dd43a6641e2dde0123be59557f8279))
- Update architecture.md for SvelteKit migration ([2c8a1fb](https://github.com/appleparan/saegim/commit/2c8a1fbcdfcb70efae539a5233a4d17bfdc4e58f))
- Update frontend documentation to match code changes ([537903c](https://github.com/appleparan/saegim/commit/537903c9e260401b9a13f65d6983d4def382ba22))
- Fix markdownlint blanks-around-lists errors ([9ed5d84](https://github.com/appleparan/saegim/commit/9ed5d84affb575aa627b7e2a7554feb6b90543d5))
- Sync API docs and ignore e2e markdown artifacts ([0188aab](https://github.com/appleparan/saegim/commit/0188aab5217cb42c12b0e7a46ba63c45f16d3eea))

### Features

- Add PyMuPDF text/image extraction during PDF upload ([8275ca6](https://github.com/appleparan/saegim/commit/8275ca697d5de19494a7030ca7b925e5ace54262))
- Add accept-extraction API to copy auto_extracted_data to annotation ([19c137e](https://github.com/appleparan/saegim/commit/19c137eae3119cb92dc96b6d1bf4766fe2550ef1))
- Add ExtractionPreview UI for accepting auto-extracted elements ([e4d3f19](https://github.com/appleparan/saegim/commit/e4d3f19a1014c97830efa6c21c0ea9a0a2f4123d))
- Add MinerU extraction service with OmniDocBench conversion ([0680c01](https://github.com/appleparan/saegim/commit/0680c0128096bfe490fe5d336f619c78b0193ba4))
- Add Celery + Redis infrastructure for async MinerU extraction ([2bf88e8](https://github.com/appleparan/saegim/commit/2bf88e84cf70231be721f333bc674eeb00fb328d))
- Integrate upload flow with pymupdf/mineru extraction branching ([f59b8dc](https://github.com/appleparan/saegim/commit/f59b8dc9a8e633ed78cb0f36a5a358d147b681d5))
- Add extracting/extraction_failed status UI in frontend ([ef39e6a](https://github.com/appleparan/saegim/commit/ef39e6a381d51032aaa20e231924ee89972d1bd5))
- Add saegim-mineru standalone HTTP service for AGPL isolation ([dd40d4f](https://github.com/appleparan/saegim/commit/dd40d4ff25bfccb4172084b9aaceb230729c19e3))
- Add saegim-mineru service to docker-compose ([43016e3](https://github.com/appleparan/saegim/commit/43016e36d92128fd50497d0276a72f6d6a4dd96e))
- Add per-project OCR config schema and API endpoints ([#7](https://github.com/appleparan/saegim/issues/7)) ([b9d6a32](https://github.com/appleparan/saegim/commit/b9d6a32cbd5e13be5065e68e15c335e02a0c0e51))
- Add Gemini and vLLM OCR provider services ([#7](https://github.com/appleparan/saegim/issues/7)) ([092f5f7](https://github.com/appleparan/saegim/commit/092f5f723ffc77f008d553877cb1baeb5d4ea58f))
- Add OCR extraction Celery task and upload integration ([#7](https://github.com/appleparan/saegim/issues/7)) ([41ca564](https://github.com/appleparan/saegim/commit/41ca564d7d3f41ed71625197866ba46ab34ad47c))
- Add frontend OCR settings UI ([#7](https://github.com/appleparan/saegim/issues/7)) ([e979c17](https://github.com/appleparan/saegim/commit/e979c17bfb4cfc32fabf20d7b44187e4ef2bf421))
- Add OCR connection test endpoint and frontend integration ([#7](https://github.com/appleparan/saegim/issues/7)) ([e53930f](https://github.com/appleparan/saegim/commit/e53930f2ee43a0b1fd730b153cb6c8dc0d98615b))
- Add 2-stage OCR pipeline schema (layout + OCR providers) ([#9](https://github.com/appleparan/saegim/issues/9)) ([1c168a2](https://github.com/appleparan/saegim/commit/1c168a24af2013f38339d7ee8f43864e96c60dd1))
- Add PP-StructureV3 HTTP client and layout region parser ([#9](https://github.com/appleparan/saegim/issues/9)) ([e90401e](https://github.com/appleparan/saegim/commit/e90401e805262f90ed45e8bd6049af18bdc39ad7))
- Add text-only OCR providers for 2-stage pipeline ([#9](https://github.com/appleparan/saegim/issues/9)) ([cd40cec](https://github.com/appleparan/saegim/commit/cd40cec0546fd63038133a15a45a07a76b00d5b1))
- Add 2-stage OCR pipeline orchestrator ([#9](https://github.com/appleparan/saegim/issues/9)) ([d3ce45e](https://github.com/appleparan/saegim/commit/d3ce45e4956018afbac809d73c8164af973a0b21))
- Update Celery task to use 2-stage OCR pipeline ([#9](https://github.com/appleparan/saegim/issues/9)) ([d30fdeb](https://github.com/appleparan/saegim/commit/d30fdeb9fe0b83bdbc35827008bf868d3efc5fc1))
- Add PP-StructureV3 service to docker-compose ([#9](https://github.com/appleparan/saegim/issues/9)) ([4a7e0c9](https://github.com/appleparan/saegim/commit/4a7e0c9952e34ba851fc2115f3a139a67007ebae))
- IntegratedServerEngine supports both PP-StructureV3 and vLLM backends ([aa8e5b1](https://github.com/appleparan/saegim/commit/aa8e5b1c2c2bd9605478b75b189881dbecc89192))
- Add dark mode with mode-watcher ([c7f039a](https://github.com/appleparan/saegim/commit/c7f039a04b593aff4fc2e1c71c4083f6db7b6458))
- Add PDF file serving endpoint for frontend PDF.js rendering ([838a598](https://github.com/appleparan/saegim/commit/838a5980d75ba8deb51e15d850a10bba8f62bcd6))
- Add PDF.js integration with PdfStore and PdfRenderer component ([5a601e8](https://github.com/appleparan/saegim/commit/5a601e8f672352ccea361af72d42d5ea6b7d1c00))
- Add document-level page navigation with PageNavigator component ([350897a](https://github.com/appleparan/saegim/commit/350897ac95e02b7e0a4c304c33fd5a256fd9aea9))
- Add text selection to bbox mapping with highlight and auto-creation ([7cada13](https://github.com/appleparan/saegim/commit/7cada13499caf037ee33a86d8a922b17df58afd7))
- Integrate PDF.js TextLayer for native text selection ([c7209c9](https://github.com/appleparan/saegim/commit/c7209c9f07f14aa0f8625412c6f3b0abd7dd0abe))
- Add OCR trigger UI after drawing a new bbox ([0e0fb23](https://github.com/appleparan/saegim/commit/0e0fb2341e42ef457244984d735201c56d62906e))

### Miscellaneous Tasks

- Add test_storage to gitignore ([94696e9](https://github.com/appleparan/saegim/commit/94696e9012cac7650b2a2431e4748fa32c8bafa4))
- Remove --extra cpu from uv sync (torch extras removed) ([e211a0f](https://github.com/appleparan/saegim/commit/e211a0fb4972814fc3b0e08ebe4b841815e73e58))
- Remove .markdownlint.json ([14377d3](https://github.com/appleparan/saegim/commit/14377d382262ac3730cdfcdb0e97190e17ccd439))
- Update Pillow 11.2.1 → 12.1.1 for Python 3.14 support ([6477be1](https://github.com/appleparan/saegim/commit/6477be1fb46af4bd7e5e2bd7b7a339c6080c5889))
- Add commented vLLM service to docker-compose ([da850c0](https://github.com/appleparan/saegim/commit/da850c05c11e38c3dbb6734ec0353074ccdb1488))
- Split CI into backend and frontend workflows ([5adf10e](https://github.com/appleparan/saegim/commit/5adf10e122cd4ec7337aaaa05630af8fb33ede75))
- Bump redis image from 7-alpine to 8-alpine ([e04a253](https://github.com/appleparan/saegim/commit/e04a2533fd4fe6eb174ca856f0028bc72ca557b8))
- Always rebuild images on docker:up ([2afe06a](https://github.com/appleparan/saegim/commit/2afe06afc097da9881306cfeb0d77085a56f63d8))
- Add docker-compose.chandra.yml for vLLM + Chandra setup ([6f0d980](https://github.com/appleparan/saegim/commit/6f0d9807477bd92777fbfde035b945087b1204db))
- Suppress ERROR log noise in test output ([63a3f51](https://github.com/appleparan/saegim/commit/63a3f51bf954be18ae52ebf901389983e2bde4df))
- Add 4-page test PDF to speed up E2E GPU tests ([34d72f5](https://github.com/appleparan/saegim/commit/34d72f5a3db0f520eec5d4e6cccdab77f1faf9aa))
- Init shadcn-svelte with violet theme ([777a44e](https://github.com/appleparan/saegim/commit/777a44e1d2ee487651d436ddad0dcf9a10ec6ca0))
- Update Dockerfile for SvelteKit build output ([3adaeb4](https://github.com/appleparan/saegim/commit/3adaeb418c978984c49e3e8c18a1347bc0900af6))
- Add Prettier and ESLint configuration ([2d25e15](https://github.com/appleparan/saegim/commit/2d25e15d4eb9347a9a3e7eabfade2cab9a67a634))
- Add Prettier and ESLint checks to frontend CI ([db0c297](https://github.com/appleparan/saegim/commit/db0c297fa67c0617198da86593c804c6aa39f8e4))
- Fix all ESLint warnings (0 errors, 0 warnings) ([aee008f](https://github.com/appleparan/saegim/commit/aee008fb03fe0057a663f9d62f0785d7f9bc0c9c))
- Remove windows from CI matrix ([21ac015](https://github.com/appleparan/saegim/commit/21ac015ee5404c74263cfe8fcd9fdb2942d9b9a7))

### Performance

- Optimize PdfRenderer zoom by separating canvas and text layer rendering ([0ca25be](https://github.com/appleparan/saegim/commit/0ca25bea6cb00896bcd7d0313635386622e9e8b9))

### Refactor

- Replace MinerU direct import with HTTP client for AGPL isolation ([f842b7a](https://github.com/appleparan/saegim/commit/f842b7adb4ffc435eb37fa282820137990157be5))
- Consolidate migrations into single init.sql and fix E2E compose ([d6aabba](https://github.com/appleparan/saegim/commit/d6aabbac1ccacf7bd5822631c52f8b8f653f8cfa))
- Remove MinerU completely ([#9](https://github.com/appleparan/saegim/issues/9)) ([7f34678](https://github.com/appleparan/saegim/commit/7f34678b4dd9c48559b4efccace29c7f50aa90a7))
- Merge 002_ocr_config into 001_init.sql ([8c5a0ad](https://github.com/appleparan/saegim/commit/8c5a0ad19e40fd0da9b55368c4c4fc4ee3583064))
- Add BaseOCREngine ABC and PyMuPDF engine ([#11](https://github.com/appleparan/saegim/issues/11)) ([fb64d8b](https://github.com/appleparan/saegim/commit/fb64d8b619887640be50ea40cb9a6446ef72bfe5))
- Add CommercialApiEngine and IntegratedServerEngine ([#11](https://github.com/appleparan/saegim/issues/11)) ([0ffc187](https://github.com/appleparan/saegim/commit/0ffc18735ad84c4a500bb0d4ab6fc810a840fc4e))
- Add SplitPipelineEngine for layout + OCR separation ([#11](https://github.com/appleparan/saegim/issues/11)) ([f40bb9c](https://github.com/appleparan/saegim/commit/f40bb9cde53733824f2365213bf922926ea2440f))
- Add engine factory, update schema and backend to engine_type ([#11](https://github.com/appleparan/saegim/issues/11)) ([ee92925](https://github.com/appleparan/saegim/commit/ee929253357111882aa53ed1148f07a81d1d0c37))
- Update frontend to engine_type based OCR config ([#11](https://github.com/appleparan/saegim/issues/11)) ([f5203d1](https://github.com/appleparan/saegim/commit/f5203d18251c2d650614232df2d47043dc4c43cd))
- Remove old 2-axis OCR factories and protocols ([#11](https://github.com/appleparan/saegim/issues/11)) ([a3e6aef](https://github.com/appleparan/saegim/commit/a3e6aef71bc5a2679273affaca8f4be9d74755ff))
- Update OCR config schemas and engine defaults ([0419a0f](https://github.com/appleparan/saegim/commit/0419a0fd88968610d304b5524728e305d334c4e8))
- Replace Celery/Redis with asyncio background tasks for OCR extraction ([2e741a5](https://github.com/appleparan/saegim/commit/2e741a57b74ad09a9efd1f344b57d1fd3a09ebf4))
- Replace custom components with shadcn-svelte ([5f4d270](https://github.com/appleparan/saegim/commit/5f4d2705636d08acbfdaea0556564378812af188))
- Migrate hardcoded colors to semantic tokens ([a2c88af](https://github.com/appleparan/saegim/commit/a2c88af9cdad12a77d55519aeee646c3873a1630))
- Replace image-based rendering with PDF.js canvas in HybridViewer ([2c3556d](https://github.com/appleparan/saegim/commit/2c3556d558222b4bc3806dd5e323d5b2a3a4be84))
- Remove unused ImageViewer component ([042e3c5](https://github.com/appleparan/saegim/commit/042e3c52382429d6d69d27399f4052b2bdf298ef))
- Remove page navigation tests from GPU E2E suite ([13a96db](https://github.com/appleparan/saegim/commit/13a96db38e7d218801f026cd7ecd8005800d4e8f))
- Migrate from svelte-spa-router to SvelteKit ([6b29690](https://github.com/appleparan/saegim/commit/6b296901bdf30851ad6cd3d9436e0d1e6b9d8d9e))
- Simplify toolbar with icon-based compact design ([87e367d](https://github.com/appleparan/saegim/commit/87e367d31ba0a9b02360b244946b718b824c87b8))

### Styling

- Apply ruff format and auto-fix ([5bf08da](https://github.com/appleparan/saegim/commit/5bf08da455b131f98b907a192d046cad67a54fa6))
- Noqa PT019, fix ty check warnings, prettier frontend ([37f38aa](https://github.com/appleparan/saegim/commit/37f38aada93f2b782da7ae145b81bd024311cb10))
- Fix markdownlint errors across documentation ([5648f0e](https://github.com/appleparan/saegim/commit/5648f0e75d711f8cdb6ba209e939badc878ea73d))

### Testing

- Add extraction e2e tests and fix auto_extracted_data serialization ([de62538](https://github.com/appleparan/saegim/commit/de62538a1269666bd36ee8b8a7f9fbd97c25215e))
- Add tests for _dispatch_mineru_extraction and delete_with_files ([e90eddd](https://github.com/appleparan/saegim/commit/e90eddde399ab988e6218d311185b3b1bab49578))
- Add sample PDF integration tests for PyMuPDF and MinerU extraction ([c667b24](https://github.com/appleparan/saegim/commit/c667b2426fd3f7c02024c0f8ab09620871d85a49))
- Update sample PDF tests for HTTP-based MinerU extraction ([424c955](https://github.com/appleparan/saegim/commit/424c955fa8af94d01b1dbbec2f5685bbc5374dd2))
- Add E2E tests for 2-stage OCR config API ([#9](https://github.com/appleparan/saegim/issues/9)) ([7ff761c](https://github.com/appleparan/saegim/commit/7ff761c04d8b1df70babe05f7f188ac5120e4b7f))
- Update OCR config tests for engine_type architecture ([19a26dd](https://github.com/appleparan/saegim/commit/19a26ddeed11b3c774dc83e2a3e5d2110ff54f3c))
- Add vLLM + chandra GPU E2E tests ([fd004fa](https://github.com/appleparan/saegim/commit/fd004fadd162faba3bc695345d793ae3df877ede))
- Update E2E selectors for shadcn-svelte migration ([1772272](https://github.com/appleparan/saegim/commit/1772272cb98c05b54df96537d1cf88d2a4f9fc7f))
- Update E2E tests for PDF.js viewer and page navigation ([03543cb](https://github.com/appleparan/saegim/commit/03543cb03a003963c54fe4dbdce0869cc33dc317))
- Add GPU hybrid labeling E2E tests for bbox and zoom alignment ([4d8ab72](https://github.com/appleparan/saegim/commit/4d8ab72d580f6933b10294e0e536b8a9b4aa0278))
- Restore multi-page PDF E2E tests for CPU suite ([27dd707](https://github.com/appleparan/saegim/commit/27dd707e9e587dd1aa35103861c18d94ca1c8dd0))
- Update unit tests for SvelteKit compatibility ([6c79605](https://github.com/appleparan/saegim/commit/6c7960519abec6999263be5425b9dfd77ded6c99))
- Migrate E2E test URLs from hash-based to path-based routing ([98969fe](https://github.com/appleparan/saegim/commit/98969fe34e0261d9e48df13041859f794ab399a7))
- Add E2E tests for PDF.js rendering and OCR draw prompt ([28e5b50](https://github.com/appleparan/saegim/commit/28e5b50cf1fe121c49e991c0d0c7b64669f980a1))

### Backend

- Add document status endpoint for extraction progress ([562d6c1](https://github.com/appleparan/saegim/commit/562d6c1d78534fc1aa2051b476df80e6642fdb29))

### Frontend

- Resolve pdfjs asset URL for storage pdf ([140ea91](https://github.com/appleparan/saegim/commit/140ea91314e44a9e1ff2dafc1b1f1aa6da6fe1e1))

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
