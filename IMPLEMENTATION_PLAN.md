## Stage 1: Frontend Auth Flow Update
**Goal**: 로그인/회원가입을 `login_id` 기반으로 전환하고, 회원가입 ID 중복확인을 버튼 없이 실시간으로 처리한다.
**Success Criteria**: 로그인/회원가입 API 호출 스펙이 backend와 일치하고, 회원가입 화면에서 ID 입력 시 자동 중복확인이 동작한다.
**Tests**: frontend auth api/store/jwt 관련 단위 테스트.
**Status**: Complete

## Stage 2: Account Security UX
**Goal**: 계정 설정 화면에서 ID/비밀번호/이메일 변경을 지원하고 ID 중복을 실시간 검사한다.
**Success Criteria**: `/account/security`에서 현재 비밀번호 검증 기반 변경이 가능하고, must_change_password 유저가 이 화면으로 유도된다.
**Tests**: route 로직 테스트 및 auth store 연계 테스트.
**Status**: In Progress

## Stage 3: Quality Check & Commit
**Goal**: 프론트 품질 검증(format/lint/check/test) 후 스테이지별 커밋을 완료한다.
**Success Criteria**: 모든 품질 명령 통과, Stage 상태 갱신, 커밋 기록 완료.
**Tests**: `bun run format:check`, `bun run lint`, `bun run check`, `bun run test`.
**Status**: Not Started
