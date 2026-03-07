# PR2: Frontend 로그인 + Auth Guard

Closes #86

## Stage 1: Auth Store + JWT 유틸리티

**Goal**: 인증 상태 관리 스토어와 JWT 파싱 유틸리티 생성
**Tests**: jwt.test.ts, auth.test.ts
**Status**: Not Started

## Stage 2: Auth API 모듈

**Goal**: login/register API 호출 모듈 생성
**Tests**: auth-api.test.ts
**Status**: Not Started

## Stage 3: API Client Bearer 토큰 자동 주입

**Goal**: 모든 API 요청에 Authorization: Bearer 헤더 자동 삽입, 401 시 자동 로그아웃
**Tests**: client.test.ts
**Status**: Not Started

## Stage 4: Login + Register 페이지

**Goal**: /login, /register 라우트 및 UI 생성
**Status**: Not Started

## Stage 5: Route Guard

**Goal**: 미인증 시 /login 리다이렉트, 토큰 만료 주기적 체크
**Status**: Not Started

## Stage 6: Header 네비게이션 업데이트

**Goal**: 로그아웃 버튼 + admin 전용 "관리" 링크
**Status**: Not Started

## Stage 7: 백엔드 Auth Middleware 적용

**Goal**: 기존 API 라우트에 get_current_user dependency 추가
**Tests**: 기존 백엔드 테스트 수정
**Status**: Not Started

## Stage 8: 통합 검증

**Goal**: lint/check/test/build 전체 통과
**Status**: Not Started
