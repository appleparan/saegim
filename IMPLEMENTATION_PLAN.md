## Stage 1: Login ID Availability API
**Goal**: 회원가입/계정변경에서 재사용 가능한 ID 중복확인 API를 제공한다.
**Success Criteria**: `GET /api/v1/auth/check-login-id`가 사용 가능 여부를 안정적으로 반환한다.
**Tests**: auth API 테스트(available/unavailable).
**Status**: Complete

## Stage 2: Credential Update API (ID/Password/Email)
**Goal**: 로그인 유저가 본인 `login_id`, `password`, `email`을 변경할 수 있게 한다.
**Success Criteria**: `PATCH /api/v1/auth/me/credentials`에서 현재 비밀번호 검증, 중복 검사, 토큰 재발급, must_change_password 갱신이 동작한다.
**Tests**: auth API 테스트(성공/현재비밀번호오류/중복 ID/중복 이메일), schema/repository 테스트.
**Status**: Complete

## Stage 3: Quality Check & Commit
**Goal**: 백엔드 품질 검증 후 PR B 커밋을 완료한다.
**Success Criteria**: format/lint/type/test 통과.
**Tests**: `ruff format`, `ruff check`, `ty check(변경 범위)`, `pytest(변경 범위)`.
**Status**: Complete
