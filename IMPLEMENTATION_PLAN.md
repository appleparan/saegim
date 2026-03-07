## Stage 1: Auth Model Refactor
**Goal**: 인증 식별자를 `login_id`로 도입하고 auth 스키마/리포지토리/토큰 발급을 정리한다.
**Success Criteria**: 회원가입/로그인이 `login_id` 입력으로 동작하며 사용자 레코드에 `login_id`와 `must_change_password`가 반영된다.
**Tests**: backend schemas/auth API/repository 관련 단위 테스트.
**Status**: Complete

## Stage 2: Bootstrap Admin Account
**Goal**: DB가 비어있을 때 기본 관리자 `admin/admin`을 자동 생성하고 비밀번호 변경 필요 플래그를 세팅한다.
**Success Criteria**: 앱 시작 후 사용자 0건이면 admin 계정이 생성되고, 로그인 시 변경 필요 플래그가 토큰에 포함된다.
**Tests**: auth API 테스트(초기 로그인 플래그), 앱 시작 bootstrap 로직 테스트/검증.
**Status**: Complete

## Stage 3: Quality Check & Commit
**Goal**: 백엔드 품질 검증 후 PR A 커밋을 완료한다.
**Success Criteria**: format/lint/type/test 통과 및 스테이지 요약 반영.
**Tests**: `ruff format`, `ruff check`, `ty check`, `pytest`.
**Status**: Complete
