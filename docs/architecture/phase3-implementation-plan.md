# Phase 3 구현 계획 (PR 분할)

Phase 3 (멀티유저 협업)을 6개 PR로 분할하여 점진적으로 구현한다.
상세 스펙: [multi-user-collaboration.md](multi-user-collaboration.md)

## 의존 관계

```text
PR 1 (Backend Auth)
 ├── PR 2 (Frontend Login + Auth Guard)
 │    ├── PR 3 (Project Members)
 │    ├── PR 5 (Task Dashboard + Review Queue UI)  ← PR 4도 필요
 │    └── PR 6 (Admin Dashboard)
 └── PR 4 (Task Workflow API)
```

- PR 1 → PR 4: 병렬 진행 가능 (PR 4는 백엔드만이라 프론트 로그인 없이 테스트 가능)
- PR 5, PR 6: 병렬 진행 가능 (서로 독립)

## PR 1: Backend Auth 기반 (3-A 백엔드)

**브랜치**: `feat/auth-backend`

### 범위

- `uv add pyjwt bcrypt`
- `001_init.sql`에 `password_hash` 컬럼과 `project_members` 테이블 통합 (DB 새로 생성)
- `schemas/auth.py`: LoginRequest, RegisterRequest, TokenResponse
- `repositories/user_repo.py` 확장: `get_by_email()`, password hash 처리
- `api/routes/auth.py`: `POST /auth/register`, `POST /auth/login`
  - register: users 레코드 0건이면 `role = 'admin'` 자동 부여
- `api/deps.py`: `get_current_user` FastAPI Depends
- `api/routes/admin.py`: `GET /admin/users`, `PATCH /admin/users/:id`, `GET /admin/projects`
  - `require_admin` dependency로 admin 전용 보호
- `api/settings.py`에 `SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE` 추가
- **기존 라우트는 아직 보호하지 않음** (하위 호환성 유지)

### 테스트

- [x] 회원가입 (최초 유저 → admin, 이후 유저 → annotator)
- [x] 로그인 → JWT 발급 → 토큰 디코딩 검증
- [x] 잘못된 비밀번호 → 401
- [x] `get_current_user` dependency 동작 확인
- [x] admin API 권한 검증 (non-admin → 403)

## PR 2: Frontend 로그인 + Auth Guard (3-A 프론트엔드)

**브랜치**: `feat/auth-frontend`
**의존**: PR 1

### 범위

- `src/lib/stores/auth.svelte.ts`: 토큰, 현재 유저 상태 (role 포함)
- `src/lib/api/auth.ts`: login/register API 호출
- `src/lib/api/client.ts`: `Authorization: Bearer` 헤더 자동 주입
- `/login` 페이지
- `+layout.ts`에 route guard (미인증 → `/login` 리다이렉트)
- admin 유저일 때 네비게이션에 `/admin` 링크 표시
- **이 PR 머지 후 기존 백엔드 라우트에 auth middleware 적용**

### 테스트

- [ ] 미인증 상태에서 보호된 페이지 접근 → `/login` 리다이렉트
- [ ] 로그인 → 토큰 저장 → API 호출 시 헤더 포함
- [ ] 토큰 만료 → 자동 로그아웃
- [ ] admin 유저: `/admin` 링크 표시, non-admin: 미표시

## PR 3: 프로젝트 멤버 관리 (3-A 멤버)

**브랜치**: `feat/project-members`
**의존**: PR 1 + PR 2

### 범위

- `repositories/project_member_repo.py`: CRUD
- `api/routes/projects.py` 확장: 멤버 관리 엔드포인트
  - `GET/POST/PATCH/DELETE /projects/:id/members`
  - owner / admin만 멤버 관리 가능
- 프로젝트 접근 시 멤버십 체크 미들웨어 (`require_project_member`)
  - admin은 멤버십 없이도 접근 가능
- 프로젝트 생성 시 생성자를 자동으로 `owner`로 등록
- 프론트엔드: `/projects/[id]/settings`에 멤버 관리 탭 추가

### 테스트

- [ ] 멤버 추가/제거/역할 변경
- [ ] 비멤버가 프로젝트 접근 → 403
- [ ] admin이 비멤버 상태에서 프로젝트 접근 → 200
- [ ] 프로젝트 생성 시 owner 자동 등록

## PR 4: 태스크 워크플로우 API (3-B 백엔드)

**브랜치**: `feat/task-workflow`
**의존**: PR 1 (PR 2 없이 API 단독 구현 가능)

### 범위

- `repositories/task_repo.py`: 할당/제출/검수 로직
- `api/routes/pages.py` 확장:
  - `POST /pages/:id/assign` — owner/admin만
  - `POST /pages/:id/submit` — assigned_to 본인만
  - `POST /pages/:id/review` — reviewer/admin만 (body: `{action: 'approved' | 'rejected', comment?}`)
- `locked_at` 관리:
  - 페이지 편집 시작 → `locked_at = NOW()`
  - 다른 유저 접근 → 409 Conflict
  - 30분 타임아웃 자동 해제 (조회 시 체크)
- `api/routes/tasks.py`:
  - `GET /users/me/tasks` — 내 할당 목록
  - `GET /projects/:id/review-queue` — 검수 대기 큐
- `task_history` 자동 기록

### 테스트

- [ ] 할당 → 상태 전이 (pending → in_progress)
- [ ] 제출 → submitted, task_history 기록
- [ ] 검수 승인 → reviewed, 검수 반려 → in_progress (재작업)
- [ ] locked_at 충돌 → 409
- [ ] 30분 타임아웃 후 다른 유저 접근 → 성공

## PR 5: 태스크 대시보드 + 검수 큐 UI (3-C)

**브랜치**: `feat/task-dashboard`
**의존**: PR 2 + PR 4

### 범위

- `/tasks` 페이지: 내 할당 목록, 상태별 필터, 진행률
- `/projects/[id]/review` 페이지: reviewer 전용 검수 큐
  - 승인/반려 버튼 + 코멘트 입력
- 레이블링 UI (`/label/[pageId]`)에 상태 표시:
  - 현재 상태 배지 (in_progress, submitted 등)
  - locked 표시 (다른 유저 편집 중)
  - 제출 버튼

### 테스트

- [ ] 태스크 대시보드 렌더링 + 필터링
- [ ] 검수 큐에서 승인/반려 동작
- [ ] 레이블링 UI에서 제출 → 상태 변경 확인

## PR 6: 관리자 대시보드 (3-C admin)

**브랜치**: `feat/admin-dashboard`
**의존**: PR 2 (+ PR 1의 admin API)

### 범위

- `/admin` 페이지 (탭 구조):
  - **유저 관리**: 유저 목록 테이블, 역할 변경 드롭다운, 비활성화 토글
  - **프로젝트 관리**: 전체 프로젝트 목록, 진행률 (총 페이지/완료/검수 대기), 멤버 수
  - **시스템 현황**: 통계 카드 (총 유저, 총 프로젝트, 전체 완료율)
- admin route guard (non-admin → `/` 리다이렉트)
- `src/lib/api/admin.ts`: admin API 호출 모듈

### 테스트

- [ ] non-admin → `/admin` 접근 시 리다이렉트
- [ ] 유저 역할 변경 → API 호출 → 목록 갱신
- [ ] 프로젝트 목록 + 통계 렌더링

## 구현 순서 (권장)

```text
Week 1: PR 1 (Backend Auth) ──────────────────────┐
Week 2: PR 2 (Frontend Login) + PR 4 (Task API)   │ 병렬
Week 3: PR 3 (Project Members)                     │
Week 4: PR 5 (Task Dashboard) + PR 6 (Admin)      │ 병렬
```
