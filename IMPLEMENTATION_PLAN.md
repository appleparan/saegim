# PR4: 태스크 워크플로우 API (3-B 백엔드)

**브랜치**: `feat/task-workflow`
**이슈**: #85
**의존**: PR 1 (Backend Auth) — 완료됨

## 개요

페이지를 사용자에게 할당하고, 제출/검수 워크플로우를 운영하는 백엔드 API 구현.

```text
[미할당] → assigned → [작업 중] → submitted → [검수 대기]
                         ↑                        │
                         │                   ┌────┴────┐
                         │               approved   rejected
                         │                   │        │
                         │              [완료]    [재작업]
                         └────────────────────────────┘
```

## Stage 1: Schemas 생성

**Goal**: 태스크 워크플로우용 request/response 스키마 정의
**Status**: Not Started

### 파일

- `src/saegim/schemas/task.py` (신규)
  - `AssignRequest`: `user_id: UUID` — 할당 대상 유저
  - `ReviewAction(StrEnum)`: `APPROVED = 'approved'`, `REJECTED = 'rejected'`
  - `ReviewRequest`: `action: ReviewAction`, `comment: str | None = None`
  - `TaskResponse`: 내 할당 목록용 (page_id, page_no, document_filename, project_name, status, assigned_at)
  - `ReviewQueueItem`: 검수 대기 큐용 (page_id, page_no, document_filename, submitted_by_name, submitted_at)

### 테스트

- `tests/schemas/test_task_schema.py`: 스키마 validation 테스트

### Success Criteria

- 모든 스키마가 Pydantic validation 통과
- `uv run ruff check`, `uv run ruff format` 통과

---

## Stage 2: Task Repository 생성

**Goal**: 태스크 할당/제출/검수/락 관리 DB 함수
**Status**: Not Started

### 파일

- `src/saegim/repositories/task_repo.py` (신규)
  - `assign_page(pool, page_id, user_id, assigned_by_id)` → status=in_progress, assigned_to 설정, task_history 기록
  - `submit_page(pool, page_id, user_id)` → status=submitted, task_history 기록
  - `review_page(pool, page_id, reviewer_id, action, comment)` → approved→reviewed / rejected→in_progress, task_history 기록
  - `acquire_lock(pool, page_id, user_id)` → locked_at=NOW(), 다른 유저 락 시 None 반환
  - `release_lock(pool, page_id)` → locked_at=NULL
  - `get_user_tasks(pool, user_id)` → 내 할당 페이지 목록 (JOIN documents, projects)
  - `get_review_queue(pool, project_id)` → status=submitted인 페이지 목록
  - `record_history(pool, page_id, user_id, action, snapshot)` → task_history INSERT
  - `get_project_id_for_page(pool, page_id)` → page→document→project 조회
  - `get_project_member_role(pool, project_id, user_id)` → project_members에서 role 조회

### 핵심 로직

- `acquire_lock`: 30분 타임아웃 자동 해제 (locked_at + 30min < NOW()면 해제 가능)
- 상태 전이 검증: pending→in_progress (assign), in_progress→submitted (submit), submitted→reviewed/in_progress (review)

### Success Criteria

- 모든 DB 함수가 올바른 SQL 실행
- 상태 전이 규칙 강제

---

## Stage 3: Pages Routes 확장 + Tasks Routes 생성

**Goal**: API 엔드포인트 구현 + 라우트 내부 권한 검증
**Status**: Not Started

### 권한 검증 방식

라우트 내부에서 직접 권한 검증:
1. `get_current_user`로 인증된 유저 확보
2. `task_repo.get_project_id_for_page()`로 프로젝트 확인
3. `task_repo.get_project_member_role()`로 프로젝트 역할 확인
4. admin은 시스템 수준에서 오버라이드

### 파일

- `src/saegim/api/routes/pages.py` 확장
  - `POST /pages/{page_id}/assign` — owner/admin만
  - `POST /pages/{page_id}/submit` — assigned_to 본인만
  - `POST /pages/{page_id}/review` — reviewer/admin만

- `src/saegim/api/routes/tasks.py` (신규)
  - `GET /users/me/tasks` — 내 할당 목록
  - `GET /projects/{project_id}/review-queue` — 검수 대기 큐

- `src/saegim/app.py` 수정
  - tasks router 등록

### locked_at 관리

- assign 시 locked_at 미설정 (편집 시작 시 별도 설정)
- 다른 유저가 편집 중인 페이지 접근 시 409 Conflict
- 30분 타임아웃 자동 해제 (조회 시 체크)

### Success Criteria

- 모든 엔드포인트 정상 동작
- 권한 검증 정상 동작
- task_history 자동 기록

---

## Stage 4: 유닛/API 테스트

**Goal**: 모든 태스크 워크플로우 기능에 대한 유닛/API 테스트
**Status**: Not Started

### 테스트 파일

- `tests/schemas/test_task_schema.py` (신규)
  - 스키마 validation 테스트

- `tests/api/test_task_workflow.py` (신규)
  - 할당 → 상태 전이 (pending → in_progress)
  - 제출 → submitted, task_history 기록
  - 검수 승인 → reviewed
  - 검수 반려 → in_progress (재작업)
  - locked_at 충돌 → 409
  - 30분 타임아웃 후 다른 유저 접근 → 성공
  - 권한 검증: non-admin/non-owner assign → 403
  - 권한 검증: 비할당자 submit → 403
  - 권한 검증: non-reviewer review → 403
  - 잘못된 상태 전이 → 409

- `tests/api/test_tasks.py` (신규)
  - GET /users/me/tasks 정상 조회
  - GET /projects/:id/review-queue 정상 조회

### Success Criteria

- 모든 테스트 통과
- `uv run pytest --cov` 50% 이상
- `uv run ruff check` 통과
- `uv run ruff format` 통과

---

## 전체 Definition of Done

- [ ] 스키마 정의 완료 (schemas/task.py)
- [ ] Task repository 구현 (repositories/task_repo.py)
- [ ] Pages routes 확장 (assign, submit, review)
- [ ] Tasks routes 생성 (my-tasks, review-queue)
- [ ] 유닛 테스트 작성 및 통과
- [ ] ruff check / ruff format 통과
- [ ] 커밋 메시지 명확
- [ ] task_history 자동 기록 동작 확인
