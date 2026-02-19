# Kubernetes 배포 가이드

## 사전 요구사항

- `kubectl` CLI
- Kubernetes 클러스터 접근 (minikube, kind, 또는 클라우드)
- Docker 이미지 빌드 완료

## 이미지 준비

### 로컬 빌드

```bash
# 백엔드
docker build -t saegim-backend:latest \
  -f saegim-backend/Dockerfile \
  saegim-backend/

# 프론트엔드 (API URL은 클러스터 환경에 맞게 설정)
docker build -t saegim-frontend:latest \
  --build-arg VITE_API_URL=http://localhost:5000 \
  saegim-frontend/
```

### 레지스트리 Push (선택)

```bash
# 태깅
docker tag saegim-backend:latest your-registry/saegim-backend:latest
docker tag saegim-frontend:latest your-registry/saegim-frontend:latest

# Push
docker push your-registry/saegim-backend:latest
docker push your-registry/saegim-frontend:latest
```

레지스트리를 사용하는 경우 `k8s/kustomization.yaml`의 `images` 섹션에서 이미지 이름을 변경합니다.

## 배포

### 1. 네임스페이스 생성

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Secret 생성

프로덕션 환경에서는 `k8s/secret.yaml`의 기본값 대신 실제 비밀번호를 사용합니다:

```bash
kubectl create secret generic saegim-secret \
  --from-literal=DATABASE_URL='postgresql://labeling:YOUR_PASSWORD@postgres:5432/labeling' \
  --from-literal=POSTGRES_PASSWORD='YOUR_PASSWORD' \
  -n saegim
```

또는 기본값 그대로 사용하려면:

```bash
kubectl apply -f k8s/secret.yaml
```

### 3. 마이그레이션 SQL ConfigMap 생성

```bash
kubectl create configmap migration-sql \
  --from-file=001_init.sql=saegim-backend/migrations/001_init.sql \
  -n saegim
```

### 4. Kustomize 배포

```bash
kubectl apply -k k8s/
```

### 5. 배포 확인

```bash
# Pod 상태 확인 (실시간)
kubectl get pods -n saegim -w

# 전체 리소스 확인
kubectl get all -n saegim
```

배포 순서:

1. PostgreSQL StatefulSet 시작 → readiness 확인
2. Migration Job 실행 → SQL 적용 완료
3. Backend Deployment 시작 (initContainer에서 DB 대기) → readiness 확인
4. Frontend Deployment 시작

### 6. 마이그레이션 확인

```bash
# Job 완료 확인
kubectl get jobs -n saegim

# 로그 확인
kubectl logs job/db-migration -n saegim
```

## 접속 방법

### NodePort

Frontend 서비스는 NodePort `30080`으로 노출됩니다:

```bash
# 노드 IP 확인
kubectl get nodes -o wide

# 접속
curl http://<NODE_IP>:30080
```

### Port-forward (개발/테스트용)

```bash
# 프론트엔드
kubectl port-forward svc/frontend 3000:80 -n saegim

# 백엔드 API
kubectl port-forward svc/backend 5000:5000 -n saegim

# PostgreSQL
kubectl port-forward svc/postgres 5432:5432 -n saegim
```

접속:

- 프론트엔드: <http://localhost:3000>
- 백엔드 API: <http://localhost:5000/api/v1/health>

## 리소스 요약

| 리소스 | 타입 | CPU 요청/제한 | 메모리 요청/제한 | 스토리지 |
| -------- | ------ | ------------- | ---------------- | --------- |
| PostgreSQL | StatefulSet | 250m / 1 | 256Mi / 1Gi | 10Gi PVC |
| Backend | Deployment | 250m / 2 | 512Mi / 2Gi | 20Gi PVC |
| Frontend | Deployment | 100m / 500m | 64Mi / 128Mi | - |

## k8s 매니페스트 구조

```text
k8s/
├── kustomization.yaml          # Kustomize 엔트리포인트
├── namespace.yaml              # saegim 네임스페이스
├── configmap.yaml              # 비민감 설정값
├── secret.yaml                 # 민감 정보 (DB URL, 비밀번호)
├── postgres-pvc.yaml           # PostgreSQL 데이터 PVC (10Gi)
├── storage-pvc.yaml            # 백엔드 스토리지 PVC (20Gi)
├── postgres-statefulset.yaml   # PostgreSQL StatefulSet + Service
├── backend-deployment.yaml     # Backend Deployment + Service
├── frontend-deployment.yaml    # Frontend Deployment + Service (NodePort)
└── migration-job.yaml          # DB 마이그레이션 Job
```

## 로그 확인

```bash
# 백엔드 로그
kubectl logs -f deployment/backend -n saegim

# PostgreSQL 로그
kubectl logs -f statefulset/postgres -n saegim

# 프론트엔드 로그
kubectl logs -f deployment/frontend -n saegim
```

## 정리

```bash
# 전체 리소스 삭제
kubectl delete -k k8s/

# 마이그레이션 ConfigMap 삭제
kubectl delete configmap migration-sql -n saegim

# 네임스페이스 삭제 (모든 리소스 포함)
kubectl delete namespace saegim
```

## 프로덕션 고려사항

- **PostgreSQL**: StatefulSet 대신 관리형 DB (RDS, Cloud SQL) 권장
- **Ingress**: 외부 도메인 연결 시 Ingress 리소스 추가 필요
- **이미지 레지스트리**: `imagePullPolicy: IfNotPresent` 대신 레지스트리 + 태그 관리
- **스토리지**: 다중 백엔드 replicas 시 `ReadWriteMany` 스토리지 클래스 필요 (NFS, EFS 등)
- **Secret 관리**: `stringData` 대신 외부 시크릿 매니저 (Vault, Sealed Secrets) 사용 권장
