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

| Method | Path | 설명 |
| -------- | ------ | ------ |
| `POST` | `/api/v1/auth/login` | 로그인 (JWT 발급) |
| `POST` | `/api/v1/auth/register` | 회원가입 |
| `GET` | `/api/v1/projects/:id/members` | 프로젝트 멤버 목록 |
| `POST` | `/api/v1/projects/:id/members` | 멤버 초대 |
| `DELETE` | `/api/v1/projects/:id/members/:user_id` | 멤버 제거 |

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

| 컴포넌트 | 설명 |
| ---------- | ------ |
| 로그인 페이지 | 이메일/비밀번호 인증 |
| 프로젝트 멤버 관리 | 초대, 역할 변경, 제거 |
| 태스크 대시보드 | 내 할당 목록, 진행률 |
| 검수 큐 | reviewer 전용, 승인/반려 UI |
| 작업 현황 보드 | 프로젝트 전체 진행률 (칸반 또는 테이블) |

## 리스크

| 리스크 | 완화 |
| -------- | ------ |
| 인증 보안 취약점 | bcrypt + JWT 표준 구현, OWASP 체크리스트 |
| 동시 편집 충돌 | 낙관적 락 + 타임아웃 자동 해제 |
| 역할 권한 복잡도 증가 | 미들웨어 기반 RBAC, 역할은 3종으로 제한 |

## 선행 조건

- Phase 2 (자동 추출) 기본 완료
- `users`, `task_history` 테이블은 이미 존재
