# Kubernetes Deployment Guide

## Prerequisites

- `kubectl` CLI
- Kubernetes cluster access (minikube, kind, or cloud)
- Docker images built

## Image Preparation

### Local Build

```bash
# Backend (CPU)
docker build -t saegim-backend:latest saegim-backend/

# Backend (GPU)
docker build -t saegim-backend:latest-gpu \
  --build-arg BASE_IMAGE=nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04 \
  --build-arg TORCH_EXTRA=cu130 \
  saegim-backend/

# Frontend (set API URL according to your cluster environment)
docker build -t saegim-frontend:latest \
  --build-arg VITE_API_URL=http://localhost:5000 \
  saegim-frontend/
```

### Registry Push (Optional)

```bash
# Tagging
docker tag saegim-backend:latest your-registry/saegim-backend:latest
docker tag saegim-frontend:latest your-registry/saegim-frontend:latest

# Push
docker push your-registry/saegim-backend:latest
docker push your-registry/saegim-frontend:latest
```

When using a registry, change the image names in the `images` section of `k8s/base/kustomization.yaml`.

## Deployment

### CPU Mode

#### 1. Create Migration SQL ConfigMap

```bash
kubectl create namespace saegim
kubectl create configmap migration-sql \
  --from-file=001_init.sql=saegim-backend/migrations/001_init.sql \
  -n saegim
```

#### 2. Deploy with Kustomize

```bash
kubectl apply -k k8s/overlays/cpu
```

### GPU Mode (with vLLM)

```bash
kubectl create namespace saegim
kubectl create configmap migration-sql \
  --from-file=001_init.sql=saegim-backend/migrations/001_init.sql \
  -n saegim
kubectl apply -k k8s/overlays/gpu
```

In GPU mode, the following resources are added on top of all CPU mode resources:

- vLLM Deployment + Service (GPU nodeSelector, tolerations)
- HuggingFace model cache PVC (50Gi)
- `VLLM_BASE_URL` ConfigMap patch

#### GPU Node Requirements

- NVIDIA GPU device plugin installed
- Node label: `nvidia.com/gpu.present: "true"`
- GPU toleration: `nvidia.com/gpu`

### Creating Secrets (Production)

In production environments, use actual passwords instead of the defaults in `k8s/base/secret.yaml`:

```bash
kubectl create secret generic saegim-secret \
  --from-literal=DATABASE_URL='postgresql://labeling:YOUR_PASSWORD@postgres:5432/labeling' \
  --from-literal=POSTGRES_PASSWORD='YOUR_PASSWORD' \
  -n saegim
```

### Verifying Deployment

```bash
# Check pod status (real-time)
kubectl get pods -n saegim -w

# Check all resources
kubectl get all -n saegim
```

Deployment order:

1. PostgreSQL StatefulSet starts -> readiness check
2. Migration Job runs -> SQL application completes
3. Backend Deployment starts (initContainer waits for DB) -> readiness check
4. Frontend Deployment starts
5. (GPU mode) vLLM Deployment starts -> waits for model loading

### Verifying Migrations

```bash
# Check Job completion
kubectl get jobs -n saegim

# Check logs
kubectl logs job/db-migration -n saegim
```

## Access Methods

### NodePort

The Frontend service is exposed via NodePort `30080`:

```bash
# Get node IP
kubectl get nodes -o wide

# Access
curl http://<NODE_IP>:30080
```

### Port-forward (For Development/Testing)

```bash
# Frontend
kubectl port-forward svc/frontend 3000:80 -n saegim

# Backend API
kubectl port-forward svc/backend 5000:5000 -n saegim

# PostgreSQL
kubectl port-forward svc/postgres 5432:5432 -n saegim

# vLLM (GPU mode)
kubectl port-forward svc/vllm 8000:8000 -n saegim
```

Access:

- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:5000/api/v1/health>

## Resource Summary

### CPU Mode

| Resource | Type | CPU Request/Limit | Memory Request/Limit | Storage |
| -------- | ------ | ------------- | ---------------- | --------- |
| PostgreSQL | StatefulSet | 250m / 1 | 256Mi / 1Gi | 10Gi PVC |
| Backend | Deployment | 250m / 2 | 512Mi / 2Gi | 20Gi PVC |
| Frontend | Deployment | 100m / 500m | 64Mi / 128Mi | - |

### GPU Mode (Additional)

| Resource | Type | CPU Request/Limit | Memory Request/Limit | GPU | Storage |
| -------- | ------ | ------------- | ---------------- | --- | --------- |
| vLLM | Deployment | 1 / 4 | 4Gi / 16Gi | 1 | 50Gi PVC |

## k8s Manifest Structure

```text
k8s/
├── base/                           # Common resources
│   ├── kustomization.yaml          # Kustomize entry point
│   ├── namespace.yaml              # saegim namespace
│   ├── configmap.yaml              # Non-sensitive configuration
│   ├── secret.yaml                 # Sensitive information (DB URL, passwords)
│   ├── postgres-pvc.yaml           # PostgreSQL data PVC (10Gi)
│   ├── storage-pvc.yaml            # Backend storage PVC (20Gi)
│   ├── postgres-statefulset.yaml   # PostgreSQL 18.2 StatefulSet + Service
│   ├── backend-deployment.yaml     # Backend Deployment + Service
│   ├── frontend-deployment.yaml    # Frontend Deployment + Service (NodePort)
│   └── migration-job.yaml          # DB migration Job
└── overlays/
    ├── cpu/
    │   └── kustomization.yaml      # References base only (CPU only)
    └── gpu/
        ├── kustomization.yaml      # base + vLLM + configmap patch
        ├── vllm-deployment.yaml    # vLLM Deployment + Service (GPU)
        ├── vllm-pvc.yaml           # HuggingFace model cache PVC (50Gi)
        └── configmap-patch.yaml    # Adds VLLM_BASE_URL
```

## Checking Logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n saegim

# PostgreSQL logs
kubectl logs -f statefulset/postgres -n saegim

# Frontend logs
kubectl logs -f deployment/frontend -n saegim

# vLLM logs (GPU mode)
kubectl logs -f deployment/vllm -n saegim
```

## Cleanup

```bash
# Delete CPU mode resources
kubectl delete -k k8s/overlays/cpu

# Delete GPU mode resources
kubectl delete -k k8s/overlays/gpu

# Delete migration ConfigMap
kubectl delete configmap migration-sql -n saegim

# Delete namespace (includes all resources)
kubectl delete namespace saegim
```

## Production Considerations

- **PostgreSQL**: Managed DB (RDS, Cloud SQL) recommended instead of StatefulSet
- **Ingress**: Ingress resource needed for external domain access
- **Image Registry**: Use registry + tag management instead of `imagePullPolicy: IfNotPresent`
- **Storage**: `ReadWriteMany` storage class required for multiple backend replicas (NFS, EFS, etc.)
- **Secret Management**: Use external secret managers (Vault, Sealed Secrets) instead of `stringData`
- **GPU Nodes**: Consider GPU node autoscaling, preemptible/spot instance configuration
