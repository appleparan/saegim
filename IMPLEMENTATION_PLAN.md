## Stage 1: Auth Initialization Race Fix
**Goal**: 로그인 직후 `authStore.initialize()`가 토큰을 덮어쓰는 레이스를 제거한다.
**Success Criteria**: 초기화/로그인 동시 상황에서도 `authStore.token`이 유효 토큰으로 유지되고 강제 로그아웃이 발생하지 않는다.
**Tests**: `saegim-frontend/tests/lib/stores/auth.test.ts`에 레이스 회귀 테스트 추가 후 통과.
**Status**: In Progress

## Stage 2: Admin Dashboard E2E Stabilization
**Goal**: admin-dashboard 브라우저 E2E가 기본 admin 계정 상태(`must_change_password`)에 의존하지 않도록 보강한다.
**Success Criteria**: 새로 빌드한 Docker E2E 환경에서 `07-admin-dashboard.test.ts`가 안정적으로 통과한다.
**Tests**: `e2e/tests/browser/07-admin-dashboard.test.ts` 및 관련 헬퍼/준비 로직 검증.
**Status**: Complete

## Stage 3: Full Quality Verification (Fresh Build)
**Goal**: 변경 영역의 포맷/린트/타입/테스트를 실행하고, Docker E2E 새 빌드 기준으로 결과를 확인한다.
**Success Criteria**: 정해진 품질 게이트를 모두 통과하고 실패 원인이 재현되지 않는다.
**Tests**:
- `saegim-frontend`: format check, lint, type check, unit tests
- `e2e`: fresh build 후 admin dashboard browser test
**Status**: Complete
