# 멀티유저 협업

## 현재 상태

DB 스키마에 멀티유저 기반이 이미 존재한다:

- `users` 테이블: admin / annotator / reviewer 역할
- `pages.assigned_to`: 페이지별 담당자 지정
- `pages.locked_at`: 동시 편집 방지용 락
- `task_history`: 할당 → 시작 → 저장 → 제출 → 승인/반려 워크플로우

백엔드에 기본 User CRUD API (`POST/GET /api/v1/users`)가 있으나,
인증/인가와 프로젝트-유저 관계는 구현되지 않았다.

## 목표

공용 인터페이스에서 벗어나 여러 사용자가 프로젝트를 공유하고,
역할 기반으로 레이블링 작업을 분담·검수하는 환경을 구축한다.

## 역할 체계 (2계층)

시스템 수준과 프로젝트 수준의 역할을 분리한다.

### 시스템 역할 (`users.role`)

| 역할 | 권한 |
| ---- | ---- |
| `admin` | 전체 사용자 관리 (CRUD, 역할 변경, 비활성화), 모든 프로젝트 접근, 시스템 설정 |
| `annotator` | 소속 프로젝트 내 작업 수행 |
| `reviewer` | 소속 프로젝트 내 검수 수행 |

### 프로젝트 역할 (`project_members.role`)

| 역할 | 권한 |
| ---- | ---- |
| `owner` | 프로젝트 설정 변경, 멤버 관리, 태스크 할당 |
| `annotator` | 할당된 페이지 레이블링 |
| `reviewer` | 제출된 페이지 검수 (승인/반려) |

**admin은 project_members에 없어도 모든 프로젝트에 접근 가능**하다 (시스템 수준 오버라이드).

### 최초 사용자 = admin

- 회원가입 시 `users` 테이블에 레코드가 0건이면 자동으로 `role = 'admin'` 부여
- 이후 가입자는 기본값 `role = 'annotator'`
- admin만 다른 사용자의 시스템 역할을 변경할 수 있다

## 구현 단계

### 3-A: 인증 및 프로젝트-유저 매핑

**목표**: 사용자가 로그인하고, 프로젝트별 접근 권한을 관리할 수 있다.

#### DB 변경

```sql
-- 프로젝트-유저 매핑 (N:M)
CREATE TABLE project_members (
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'annotator'
        CHECK (role IN ('owner', 'annotator', 'reviewer')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (project_id, user_id)
);

-- users 테이블에 인증 필드 추가
ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
```

#### API

| Method | Path | 설명 | 권한 |
| -------- | ------ | ------ | ------ |
| `POST` | `/api/v1/auth/login` | 로그인 (JWT 발급) | 공개 |
| `POST` | `/api/v1/auth/register` | 회원가입 (최초 유저 → admin) | 공개 |
| `GET` | `/api/v1/admin/users` | 전체 유저 목록 | admin |
| `PATCH` | `/api/v1/admin/users/:id` | 유저 역할 변경 / 비활성화 | admin |
| `GET` | `/api/v1/admin/projects` | 전체 프로젝트 목록 (통계 포함) | admin |
| `GET` | `/api/v1/projects/:id/members` | 프로젝트 멤버 목록 | 멤버 |
| `POST` | `/api/v1/projects/:id/members` | 멤버 초대 | owner / admin |
| `PATCH` | `/api/v1/projects/:id/members/:user_id` | 멤버 역할 변경 | owner / admin |
| `DELETE` | `/api/v1/projects/:id/members/:user_id` | 멤버 제거 | owner / admin |

#### 인증 방식 선택지

| 방식 | 장점 | 단점 |
| ------ | ------ | ------ |
| JWT (stateless) | 구현 간단, 수평 확장 용이 | 토큰 무효화 어려움 |
| Session + Redis | 즉시 무효화 가능 | 인프라 추가 (Redis) |
| OAuth2 (Google/GitHub) | 비밀번호 관리 불필요 | 외부 의존, 내부망 제한 |

권장: MVP에서는 JWT, 추후 필요 시 OAuth2 추가.

### 3-B: 태스크 할당 및 워크플로우

**목표**: 페이지를 사용자에게 할당하고, 제출/검수 워크플로우를 운영한다.

#### 워크플로우

```text
[미할당] → assigned → [작업 중] → submitted → [검수 대기]
                         ↑                        │
                         │                   ┌────┴────┐
                         │               approved   rejected
                         │                   │        │
                         │              [완료]    [재작업]
                         └────────────────────────────┘
```

#### API

| Method | Path | 설명 |
| -------- | ------ | ------ |
| `POST` | `/api/v1/pages/:id/assign` | 페이지 할당 |
| `POST` | `/api/v1/pages/:id/submit` | 검수 제출 |
| `POST` | `/api/v1/pages/:id/review` | 승인/반려 |
| `GET` | `/api/v1/users/:id/tasks` | 내 작업 목록 |
| `GET` | `/api/v1/projects/:id/review-queue` | 검수 대기 큐 |

#### 동시 편집 방지

기존 `pages.locked_at`을 활용한다:

- 페이지 편집 시작 시 `locked_at = NOW()`, `assigned_to = current_user`
- 다른 사용자가 접근하면 "편집 중" 표시
- 타임아웃 (예: 30분) 경과 시 자동 해제

### 3-C: 프론트엔드 협업 UI

**목표**: 할당 현황, 검수 큐, 작업 진행률을 시각적으로 제공한다.

#### 주요 컴포넌트

| 컴포넌트 | 설명 | 접근 권한 |
| ---------- | ------ | ---------- |
| 로그인 페이지 | 이메일/비밀번호 인증 | 공개 |
| 프로젝트 멤버 관리 | 초대, 역할 변경, 제거 | owner / admin |
| 태스크 대시보드 | 내 할당 목록, 진행률 | 인증된 유저 |
| 검수 큐 | reviewer 전용, 승인/반려 UI | reviewer / admin |
| 작업 현황 보드 | 프로젝트 전체 진행률 (칸반 또는 테이블) | 멤버 |
| **관리자 대시보드** | 아래 참조 | **admin** |

#### 관리자 대시보드 (`/admin`)

admin 전용 페이지. 시스템 전반을 관리한다.

| 탭 | 내용 |
| --- | ---- |
| 유저 관리 | 유저 목록, 역할 변경 (`admin`/`annotator`/`reviewer`), 비활성화 |
| 프로젝트 관리 | 전체 프로젝트 목록, 진행률 요약 (총 페이지 / 완료 / 검수 대기), 멤버 수 |
| 시스템 현황 | 전체 통계 (총 유저 수, 프로젝트 수, 완료율) |

- admin이 아닌 유저가 `/admin` 접근 시 403 또는 리다이렉트
- 프로젝트 관리 탭에서 개별 프로젝트 클릭 시 해당 프로젝트 상세로 이동

## 리스크

| 리스크 | 완화 |
| -------- | ------ |
| 인증 보안 취약점 | bcrypt + JWT 표준 구현, OWASP 체크리스트 |
| 동시 편집 충돌 | 낙관적 락 + 타임아웃 자동 해제 |
| 역할 권한 복잡도 증가 | 미들웨어 기반 RBAC, 시스템 3종 + 프로젝트 3종으로 제한 |
| admin 계정 탈취 | 최초 admin 생성 후 추가 admin 생성 제한, 비밀번호 강도 검증 |

## 선행 조건

- Phase 2 (자동 추출) 기본 완료
- `users`, `task_history` 테이블은 이미 존재
