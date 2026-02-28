# saegim-frontend

saegim 레이블링 플랫폼의 프론트엔드. SvelteKit + Svelte 5 Runes 기반 SPA.

## 기술 스택

| 분류 | 기술 |
| ---- | ---- |
| **프레임워크** | SvelteKit (adapter-static SPA) + Svelte 5 (Runes) |
| **빌드** | Vite 7, TypeScript |
| **스타일** | Tailwind CSS 4, shadcn-svelte, 다크모드 (mode-watcher) |
| **캔버스** | PDF.js (PDF 렌더링) + Konva.js (바운딩 박스 에디터) |
| **포맷터** | oxfmt |
| **린터** | ESLint |
| **테스트** | Vitest + Testing Library |

## 개발

```bash
bun install

bun run dev           # 개발 서버 (localhost:5173)
bun run build         # 프로덕션 빌드
bun run preview       # 빌드 결과 미리보기
bun run check         # svelte-check 타입 체크
bun run test          # Vitest 테스트
bun run format        # oxfmt 포맷팅
bun run format:check  # 포맷 검사
bun run lint          # ESLint 검사
bun run lint:fix      # ESLint 자동 수정
```

## 프로젝트 구조

```text
src/
├── routes/                   # SvelteKit 파일 기반 라우팅
│   ├── +layout.svelte        # 루트 레이아웃
│   ├── +page.svelte          # 홈 (프로젝트 목록)
│   ├── projects/             # 프로젝트 상세
│   └── label/                # 레이블링 에디터
├── lib/
│   ├── api/                  # HTTP 클라이언트 (백엔드 REST API)
│   ├── components/
│   │   ├── ui/               # shadcn-svelte 기본 UI 컴포넌트
│   │   ├── canvas/           # PDF.js + Konva.js 캔버스 에디터
│   │   ├── panels/           # 사이드 패널 (속성, 카테고리 등)
│   │   ├── layout/           # 레이아웃 컴포넌트
│   │   ├── settings/         # 설정 관련 컴포넌트
│   │   └── common/           # 공통 컴포넌트
│   ├── stores/               # Svelte 5 Runes 상태 관리
│   ├── types/                # OmniDocBench 타입 정의
│   └── utils/                # 유틸리티 함수
└── tests/                    # Vitest 유닛 테스트
```
