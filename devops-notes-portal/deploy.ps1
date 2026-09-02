# =====================================================================
# 1-Click Setup & Deploy Script for Docker Desktop Kubernetes
# =====================================================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Building & Deploying DevOps Hub to K8s  " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Ensure directories exist
New-Item -ItemType Directory -Force -Path "app/templates" | Out-Null
New-Item -ItemType Directory -Force -Path "k8s" | Out-Null

# 2. Build Docker image locally
Write-Host "`n[1/3] Building multi-stage Docker image..." -ForegroundColor Yellow
docker build -t devops-hub:v4.8.0 -t devops-hub:latest .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed. Please verify Docker Desktop is running." -ForegroundColor Red
    exit 1
}

# 3. Apply Kubernetes Manifests
Write-Host "`n[2/3] Applying Kubernetes manifests..." -ForegroundColor Yellow
kubectl apply -f k8s/all-in-one.yaml

# 4. Wait for pod to be ready
Write-Host "`n[3/3] Waiting for Pod to start..." -ForegroundColor Yellow
kubectl rollout status deployment/devops-hub-deployment -n devops-hub --timeout=90s

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host " Deployment Successful! " -ForegroundColor Green
Write-Host " Access your website at: http://localhost:8000" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green