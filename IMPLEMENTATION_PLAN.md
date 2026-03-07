# PR2: Frontend 로그인 + Auth Guard

Closes #86

## Stage 1: Auth Store + JWT 유틸리티

**Goal**: 인증 상태 관리 스토어와 JWT 파싱 유틸리티 생성
**Tests**: jwt.test.ts (9 tests), auth.test.ts (10 tests)
**Status**: Complete
**Commit**: `0a249b9`

## Stage 2: Auth API 모듈

**Goal**: login/register API 호출 모듈 생성
**Tests**: auth-api.test.ts (4 tests)
**Status**: Complete
**Commit**: `8bc4f6a`

## Stage 3: API Client Bearer 토큰 자동 주입

**Goal**: 모든 API 요청에 Authorization: Bearer 헤더 자동 삽입, 401 시 자동 로그아웃
**Tests**: client.test.ts (5 tests)
**Status**: Complete
**Commit**: `5453c22`

## Stage 4: Login + Register 페이지

**Goal**: /login, /register 라우트 및 UI 생성
**Status**: Complete
**Commit**: `57014ea`

## Stage 5: Route Guard

**Goal**: 미인증 시 /login 리다이렉트, 토큰 만료 주기적 체크
**Status**: Complete
**Commit**: `4c3a9c7`

## Stage 6: Header 네비게이션 업데이트

**Goal**: 로그아웃 버튼 + admin 전용 "관리" 링크
**Status**: Complete
**Commit**: `ba57307`

## Stage 7: 백엔드 Auth Middleware 적용

**Goal**: 기존 API 라우트에 get_current_user dependency 추가
**Tests**: 기존 백엔드 테스트 수정 (conftest에 auth override 추가, admin 테스트 분리)
**Status**: Complete
**Commit**: `10c4a50`

## Stage 8: 통합 검증

**Goal**: lint/check/test/build 전체 통과
**Status**: Complete

**결과**:
- Frontend: oxlint 0 errors, svelte-check 0 errors, 202 tests passed, build OK
- Backend: ruff check passed, ruff format OK, 687 tests passed

## E2E 검증 (Chrome DevTools MCP)

10개 시나리오 전부 통과:

1. 미인증 시 `/` → `/login` 리다이렉트
2. 로그인 페이지 렌더링 (폼, 버튼, 링크)
3. 회원가입 페이지 렌더링 (4개 필드, 링크)
4. 회원가입 → 자동 로그인 → 메인 페이지
5. admin 사용자 "관리" 링크 표시
6. 로그아웃 → `/login` 리다이렉트
7. annotator 사용자 "관리" 링크 미표시
8. 기존 계정 로그인 → 메인 페이지
9. 잘못된 비밀번호 → 에러 메시지
10. 중복 이메일 회원가입 → 에러 메시지
