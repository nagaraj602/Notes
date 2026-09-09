<details open>
<summary><h2>🏢 Azentio</h2></summary>

<details open>
<summary><h3>HackerRank Assessment</h3></summary>

*Date: 04-08-2026 09:40 PM*

#### 【 CI/CD 】

<details>
<summary><strong>● Given a scenario where a company mandates Windows OS for software builds and maintains a 24/7 cloud-based Windows server for live operations, with a Jenkins server listening on port 8080 in a private VPC behind a load balancer that restricts access to specific IP addresses and forwards port 8080 traffic to HTTPS, how should the Windows build agent be configured to connect to the Jenkins master?</strong></summary>

**Answer:**
In this enterprise architecture, the Jenkins Controller runs on port `8080` inside a private VPC behind an Application Load Balancer (ALB) terminating SSL/TLS (listening on port `443`) and forwarding traffic internally to port `8080`. Connecting a remote Windows build agent under these constraints requires configuring an **Inbound Agent (formerly JNLP) via WebSocket over HTTPS (WSS)**, which is the modern production standard.

### 1. Architectural Strategy: Why WebSocket over HTTPS?
- **Load Balancer Compatibility:** Traditional Jenkins inbound agents communicate via TCP on port `50000`. Standard AWS Application Load Balancers (ALB) only proxy HTTP/HTTPS (Layer 7) and cannot proxy raw Layer 4 TCP port `50000` traffic without deploying a separate Network Load Balancer (NLB) or configuring VPC Peering/VPN.
- **WebSocket Solution:** Since Jenkins 2.217+, Jenkins supports running inbound agent communication over WebSockets (`-webSocket` flag). WebSocket connections originate as standard HTTPS requests over port `443`, pass through the ALB seamlessly, and upgrade the connection.
- **Firewall & IP Restrictions:** The Windows agent needs outbound access over port `443` only, and its public IP must be whitelisted in the ALB's security group/WAF.

### 2. Jenkins Controller Configuration
1. Navigate to **Manage Jenkins -> Nodes -> New Node**.
2. Set **Node Name** (e.g., `windows-build-agent-01`), choose **Permanent Agent**.
3. Configure Remote root directory: `C:\jenkins`.
4. In **Launch method**, select **Launch agent by connecting it to the controller**.
5. Enable the checkbox **Use WebSocket**.
6. Save the node. Jenkins will display the secret token and agent launch command.

### 3. Windows Agent Host Setup
1. **Prerequisites:** Install Java (Temurin OpenJDK 17 or 21) and Git for Windows.
2. **Download Agent JAR:**
   ```powershell
   New-Item -ItemType Directory -Path "C:\jenkins" -Force
   Invoke-WebRequest -Uri "https://<jenkins-alb-domain>/jnlpmac/agent.jar" -OutFile "C:\jenkins\agent.jar"
   ```
3. **Verify Connectivity:**
   ```powershell
   java -jar C:\jenkins\agent.jar `
     -url https://<jenkins-alb-domain>/ `
     -secret <AGENT_SECRET_KEY> `
     -name windows-build-agent-01 `
     -webSocket `
     -workDir "C:\jenkins"
   ```

### 4. Running as a Resilient Windows Service
To ensure the build agent runs 24/7 across Windows reboots, wrap it as a Windows Service using **WinSW (Windows Service Wrapper)**:
```xml
<!-- C:\jenkins\jenkins-agent.xml -->
<service>
  <id>JenkinsAgent</id>
  <name>Jenkins Inbound Build Agent</name>
  <description>Jenkins Inbound Windows Build Agent over WebSocket</description>
  <executable>C:\Program Files\Eclipse Adoptium\jdk-17\bin\java.exe</executable>
  <arguments>-jar C:\jenkins\agent.jar -url https://<jenkins-alb-domain>/ -secret <AGENT_SECRET_KEY> -name windows-build-agent-01 -webSocket -workDir "C:\jenkins"</arguments>
  <logmode>rotate</logmode>
  <onfailure action="restart" delay="10 sec"/>
</service>
```
Install and start the service:
```powershell
C:\jenkins\WinSW.exe install
C:\jenkins\WinSW.exe start
```
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● Write a complete Dockerfile that: uses '134148934511.dkr.ecr.us-east-1.amazonaws.com/hr/python:3.9' as the base image; copies all application files from the 'app' folder in the build context into a directory inside the container; uses pip to install the required Python packages listed in a requirements.txt file; exposes port 8000 to allow external access to the application; and sets the default command to run the application using 'python /path/to/app.py'.</strong></summary>

**Answer:**
Below is the complete, production-grade `Dockerfile` satisfying all requirements:

```dockerfile
# 1. Base Image from private AWS ECR repository
FROM 134148934511.dkr.ecr.us-east-1.amazonaws.com/hr/python:3.9

# 2. Set environment variables for Python runtime optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Define the working directory inside the container
WORKDIR /app

# 4. Copy requirements file first to leverage Docker layer caching
COPY app/requirements.txt /app/requirements.txt

# 5. Install Python dependencies using pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# 6. Copy all remaining application files from the 'app' directory into container
COPY app/ /app/

# Optional: Create symlink if strict path '/path/to/app.py' is required by test runners
RUN mkdir -p /path/to && ln -s /app/app.py /path/to/app.py

# 7. Expose application network port
EXPOSE 8000

# 8. Set default execution command
CMD ["python", "/path/to/app.py"]
```

**Key Senior Engineering Practices Applied:**
- **Layer Caching:** `requirements.txt` is copied and installed prior to copying the full source code. This prevents re-downloading Python packages on every minor code edit.
- **`--no-cache-dir`:** Avoids storing cached `.whl` files in the container filesystem, reducing the image size by ~40-60%.
- **`PYTHONUNBUFFERED=1`:** Ensures application stdout/stderr logs are flushed directly to container logs (CloudWatch / FluentBit) without buffering delays.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Write a complete hpa.yaml manifest that creates a new HorizontalPodAutoscaler (using API version 'autoscaling/v2beta2') named 'application' in the namespace 'hacker-company', referencing the existing Deployment 'application', such that: the maximum number of replicas is limited to 4; scale-up behavior uses a Percent policy configured to scale as fast as possible; scale-up behavior also uses a Pods policy configured to scale very gradually (1 pod every 2 minutes); and scale-down behavior has a stabilization window of 60 seconds.</strong></summary>

**Answer:**
Below is the complete `hpa.yaml` manifest using `autoscaling/v2beta2`:

```yaml
apiVersion: autoscaling/v2beta2
kind: HorizontalPodAutoscaler
metadata:
  name: application
  namespace: hacker-company
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: application
  minReplicas: 1
  maxReplicas: 4
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleUp:
      selectPolicy: Max
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 1
        periodSeconds: 120
    scaleDown:
      stabilizationWindowSeconds: 60
      selectPolicy: Min
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

**Manifest Breakdown:**
- **`scaleTargetRef`:** Targets Deployment `application` in namespace `hacker-company`.
- **`maxReplicas: 4`:** Caps the maximum number of running pods at 4.
- **`scaleUp.selectPolicy: Max`:** Ensures that when scaling up, Kubernetes selects the policy that produces the highest number of pods (fastest possible scale-up).
- **`Percent: 100` over `15s`:** Doubles the replica count every 15 seconds (aggressive burst protection).
- **`Pods: 1` over `120s`:** A gradual pod policy adding 1 pod every 2 minutes.
- **`scaleDown.stabilizationWindowSeconds: 60`:** Prevents flapping ("thrashing") by evaluating metrics over a 60-second cooldown window before downscaling.
</details>

<details>
<summary><strong>● Create a Kubernetes Ingress resource using the 'traefik' ingress class, named 'frontend', in the existing namespace 'hacker-company', with the following rules: requests to host 'api.hacker-company.com' at path '/v1' should route to port 80 of the 'nginx-api-v1' Service, and requests to host 'api.hacker-company.com' at path '/v2' should route to port 80 of the 'nginx-api-v2' Service.</strong></summary>

**Answer:**
Below is the standard Kubernetes Ingress manifest conforming to `networking.k8s.io/v1`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend
  namespace: hacker-company
  annotations:
    kubernetes.io/ingress.class: "traefik"
    traefik.ingress.kubernetes.io/router.entrypoints: "web,websecure"
spec:
  ingressClassName: traefik
  rules:
  - host: api.hacker-company.com
    http:
      paths:
      - path: /v1
        pathType: Prefix
        backend:
          service:
            name: nginx-api-v1
            port:
              number: 80
      - path: /v2
        pathType: Prefix
        backend:
          service:
            name: nginx-api-v2
            port:
              number: 80
```

**Technical Notes:**
- **`ingressClassName: traefik`:** Standardized field since Kubernetes 1.18+ indicating the ingress controller implementation. The annotation `kubernetes.io/ingress.class` is retained for backward compatibility.
- **`pathType: Prefix`:** Matches any request starting with `/v1` (e.g., `/v1/users`, `/v1/health`) and routes it to `nginx-api-v1:80`, and requests starting with `/v2` to `nginx-api-v2:80`.
</details>

<details>
<summary><strong>● Given an existing StatefulSet managing a MongoDB database, modify its manifest to: (a) identify/confirm the StatefulSet managing the MongoDB database; (b) add a livenessProbe that runs the command 'mongo \--eval db.adminCommand("ping")' every 10 seconds, with an initial delay of 30 seconds, a timeout of 5 seconds per execution, and triggers a pod restart after 3 consecutive failures; (c) scale the StatefulSet to 3 replicas for improved availability and redundancy; (d) expose/forward TCP port 27017 for database connectivity; and (e) use the container image 'public.ecr.aws/docker/library/mongo:latest'.</strong></summary>

**Answer:**
Below is the updated and modified `StatefulSet` manifest implementing all requested changes (a) through (e):

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb-database          # (a) StatefulSet managing MongoDB
  namespace: default
  labels:
    app.kubernetes.io/name: mongodb
spec:
  serviceName: "mongodb-headless"
  replicas: 3                     # (c) Scaled to 3 replicas for HA
  selector:
    matchLabels:
      app.kubernetes.io/name: mongodb
  template:
    metadata:
      labels:
        app.kubernetes.io/name: mongodb
    spec:
      containers:
      - name: mongodb
        image: public.ecr.aws/docker/library/mongo:latest  # (e) Specified image
        imagePullPolicy: IfNotPresent
        ports:
        - name: mongodb
          containerPort: 27017    # (d) Exposed TCP port 27017
          protocol: TCP
        # (b) Configured Liveness Probe
        livenessProbe:
          exec:
            command:
            - mongo
            - --eval
            - 'db.adminCommand("ping")'
          initialDelaySeconds: 30 # 30 seconds before first execution
          periodSeconds: 10       # Runs every 10 seconds
          timeoutSeconds: 5       # 5 seconds per execution timeout
          failureThreshold: 3     # Restarts pod after 3 consecutive failures
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "2Gi"
        volumeMounts:
        - name: mongodb-data
          mountPath: /data/db
  volumeClaimTemplates:
  - metadata:
      name: mongodb-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 20Gi
```

**Verification Commands:**
```bash
# Confirm StatefulSet rollout status
kubectl rollout status statefulset/mongodb-database

# Inspect liveness probe execution
kubectl describe statefulset mongodb-database | grep -A 8 Liveness
```
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Using the AWS CLI, write a command (or set of commands) to update the 'gallery-secondary' S3 bucket so that it mirrors the 'gallery-primary' S3 bucket, given the following requirements: only graphic-type files (.png, .jpg, .gif) should be synced from gallery-primary to gallery-secondary; any '.unknown' files in either bucket must remain untouched; the gallery-primary bucket must remain unmodified; and any graphic-type files that exist only in gallery-secondary (not in gallery-primary) should be deleted from gallery-secondary.</strong></summary>

**Answer:**
Below is the single, idempotent AWS CLI command meeting all specified constraints:

```bash
aws s3 sync s3://gallery-primary s3://gallery-secondary \
  --exclude "*" \
  --include "*.png" \
  --include "*.jpg" \
  --include "*.gif" \
  --exclude "*.unknown" \
  --delete
```

**Explanation of Flags and Order of Evaluation:**
1. **Source & Destination (`s3://gallery-primary s3://gallery-secondary`):** Copies from primary to secondary. The primary bucket is read-only during sync operations and remains completely unmodified.
2. **Order of Filters (`--exclude` and `--include`):** The AWS CLI processes include/exclude parameters in sequential order from left to right:
   - `--exclude "*"`: First excludes all files in the bucket.
   - `--include "*.png" --include "*.jpg" --include "*.gif"`: Whitelists only graphic files.
   - `--exclude "*.unknown"`: Explicitly ensures that any `.unknown` files (even if named like `image.png.unknown`) are excluded and untouched.
3. **`--delete` Flag:** Deletes files in the destination (`gallery-secondary`) that do not exist in the source (`gallery-primary`). Because `--delete` strictly honors the include/exclude filters, it **only deletes orphaned `.png`, `.jpg`, and `.gif` files** in secondary. Any existing `.unknown` files in `gallery-secondary` remain untouched and will never be deleted.
4. **Safety Check (Dry Run):**
   ```bash
   aws s3 sync s3://gallery-primary s3://gallery-secondary --exclude "*" --include "*.png" --include "*.jpg" --include "*.gif" --exclude "*.unknown" --delete --dryrun
   ```
</details>

#### 【 SECURITY 】

<details>
<summary><strong>● A company needs to enhance security for its Jenkins system by creating a highly protected login process, while also setting up a system that precisely controls which developers can access specific pipelines based on their roles/requirements. What is the most suitable and effective approach to address both of these challenges?</strong></summary>

**Answer:**
To resolve both challenges at an enterprise tier, implement a unified **Zero-Trust Identity Federation (SSO + MFA)** combined with **Fine-Grained Role-Based Access Control (RBAC) and Folder Authorization**:

### Challenge 1: Highly Protected Login Process (Authentication)
1. **Enterprise Identity Federation (SSO):**
   - Delegate Jenkins authentication to an enterprise Identity Provider (IdP) such as **Microsoft Entra ID (Azure AD)**, **Okta**, or **Keycloak** using **SAML 2.0** or **OpenID Connect (OIDC)** via plugins (`saml-plugin` or `oic-auth-plugin`).
   - Disable Jenkins internal local user databases (except for a secured, vault-stored break-glass admin credential).
2. **Adaptive Multi-Factor Authentication (MFA):**
   - Enforce mandatory hardware-based MFA (FIDO2/WebAuthn, YubiKey) or TOTP at the IdP level.
   - Configure conditional access policies: restrict Jenkins access to corporate VPN IP ranges or managed zero-trust devices (Zscaler / Cloudflare Access).
3. **Session Hardening:** Configure idle session timeouts (e.g., 15 minutes) and enforce HTTPS TLS 1.3 encryption across all controller traffic.

### Challenge 2: Granular Pipeline Access Control (Authorization)
1. **Role-Based Authorization Strategy (Role-Strategy Plugin):**
   - Enable the **Role-based Authorization Strategy** under *Manage Jenkins -> Security*.
   - Define **Global Roles**: e.g., `Read-Only` (allows all authenticated users to see Jenkins root, but not execute or view secrets).
   - Define **Item / Pattern Roles**:
     - `frontend-dev-role`: Grants Job/Read, Job/Build, Job/Cancel matching pattern `frontend-.*` or `frontend/.*`.
     - `payment-dev-role`: Grants Job/Read, Job/Build, Job/Configure matching pattern `payments/.*`.
     - `production-deployer`: Restricted to senior leads for triggering release pipelines.
2. **Jenkins Folders Architecture with Folder-Based Authorization:**
   - Organize pipelines into team-based hierarchies using the **CloudBees Folders Plugin**:
     ```
     ├── Core-Banking/
     │   ├── payment-service (Restricted to Core-Banking Team)
     │   └── account-service
     ├── Customer-Portal/
     │   └── frontend-web (Restricted to Frontend Team)
     ```
   - Store team-specific credentials (SSH keys, AWS tokens, SonarQube secrets) inside the respective Jenkins **Folder Scope**, ensuring developers from other teams cannot inspect or bind foreign credentials.
3. **Automated Group-to-Role Mapping:**
   - Map IdP groups directly to Jenkins roles (e.g., Okta group `devops-platform-engineers` -> `Jenkins-Admin`; `frontend-engineers` -> `frontend-dev-role`), eliminating manual permission maintenance.
</details>
</details>

</details>

<details open>
<summary><h2>🏢 CitiusTech</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 04-08-2026 10:26 PM*

#### 【 LINUX 】

<details>
<summary><strong>● Do you have experience with Bash and Python scripting?</strong></summary>

**Answer:**
Yes, I have over 6 years of daily, production-level experience with both **Bash** and **Python** scripting across Linux infrastructure, cloud automation, and CI/CD pipelines:

- **Bash Scripting:** Used for OS-level automation, system bootstrapping (cloud-init / user data), log rotation, container entrypoints, pipeline glue code, and rapid system diagnostics. I adhere to production best practices including `set -euo pipefail`, structured error traps, idempotency, and modular functions.
- **Python Scripting:** Used when logic requires complex data manipulation, JSON/YAML parsing, API orchestration, and cloud SDK interaction. I frequently write Python automation using **`boto3`** (AWS resource auditing, automated AMI cleanup, cost-optimization scripts), **`requests`** (calling Jira, Slack, SonarQube, and Argo CD REST APIs), and **`psutil`** for detailed systems monitoring.
</details>

<details>
<summary><strong>● Can you write a shell script that monitors disk usage and sends an alert if a defined usage threshold is exceeded?</strong></summary>

**Answer:**
Below is a robust, production-grade Bash monitoring script that checks all mounted physical filesystems, identifies partitions exceeding a threshold, and dispatches an alert via a Slack/Teams webhook or email:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Configuration
THRESHOLD=80
WEBHOOK_URL="https://hooks.slack.com/services/T00/B00/XXXXX"
HOSTNAME=$(hostname -f)
ALERT_FLAG=0
ALERT_BODY=""

# Process df output, excluding virtual, loop, and temp filesystems
while read -r line; do
    USAGE=$(echo "$line" | awk '{print $5}' | tr -d '%')
    MOUNT=$(echo "$line" | awk '{print $6}')
    FILESYSTEM=$(echo "$line" | awk '{print $1}')
    
    if [ "$USAGE" -ge "$THRESHOLD" ]; then
        ALERT_FLAG=1
        ALERT_BODY+="- *Mount:* \`${MOUNT}\` (*${FILESYSTEM}*) is at *${USAGE}%* (Threshold: ${THRESHOLD}%)\n"
    fi
done < <(df -Ph | grep -vE '^Filesystem|tmpfs|cdrom|overlay|shm|udev|loop')

# Dispatch webhook if threshold breached
if [ "$ALERT_FLAG" -eq 1 ]; then
    PAYLOAD=$(cat <<EOF
{
  "text": ":rotating_light: *DISK USAGE ALERT on ${HOSTNAME}*",
  "attachments": [
    {
      "color": "danger",
      "text": "${ALERT_BODY}",
      "footer": "Linux Ops Monitoring | $(date '+%Y-%m-%d %H:%M:%S UTC')"
    }
  ]
}
EOF
)
    curl -s -X POST -H 'Content-type: application/json' --data "$PAYLOAD" "$WEBHOOK_URL"
    echo "[$(date)] Disk alert sent for ${HOSTNAME}"
else
    echo "[$(date)] All partitions healthy (below ${THRESHOLD}%) on ${HOSTNAME}"
fi
```

**Key Features:**
- **`df -Ph` (POSIX standard format):** Prevents line wrapping on long device names (e.g., LVM paths or EBS volumes).
- **Process Substitution (`< <(...)`):** Avoids subshell pipeline scoping issues where variable state (`ALERT_FLAG`) is lost outside the loop.
- **Webhook Alerting:** Formats an actionable JSON alert payload for modern incident response channels.
</details>

<details>
<summary><strong>↳ Follow-up: You also mentioned you have experience with Python — is that correct?</strong></summary>

**Answer:**
Yes, that is correct. I have extensive experience building Python automation for infrastructure operations and DevOps tooling. My day-to-day Python usage includes:

1. **Cloud Automation via `boto3`:** Automating snapshot lifecycles, detecting unattached EBS volumes, auditing IAM role usage, and triggering EKS cluster rolling upgrades.
2. **CI/CD & API Integrations:** Writing Python scripts to parse SAST/DAST report outputs (Trivy, SonarQube), enforce quality gates, and post summary comments to GitHub Pull Requests.
3. **Data & Config Processing:** Building scripts to validate, merge, and convert multi-environment YAML/JSON manifests and Helm values files.
</details>

<details>
<summary><strong>● Can you write a Python script to take a backup of a folder or file and store it in a destination location?</strong></summary>

**Answer:**
Below is an enterprise-ready Python script that creates a timestamped, gzip-compressed tar archive of a source directory, verifies the archive integrity, calculates an SHA256 checksum, enforces a local retention policy (pruning backups older than 7 days), and optionally uploads it to an AWS S3 bucket:

```python
#!/usr/bin/env python3
import os
import sys
import tarfile
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def compute_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of the created archive."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def prune_old_backups(dest_dir: Path, retention_days: int = 7):
    """Delete backups older than retention_days."""
    cutoff_time = datetime.now() - timedelta(days=retention_days)
    for archive in dest_dir.glob("backup_*.tar.gz"):
        file_mtime = datetime.fromtimestamp(archive.stat().st_mtime)
        if file_mtime < cutoff_time:
            archive.unlink()
            logging.info(f"Pruned expired backup: {archive.name}")

def backup_folder(source_dir: str, destination_dir: str, retention_days: int = 7):
    src = Path(source_dir).resolve()
    dest = Path(destination_dir).resolve()

    if not src.exists():
        logging.error(f"Source path does not exist: {src}")
        sys.exit(1)

    dest.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"backup_{src.name}_{timestamp}.tar.gz"
    archive_path = dest / archive_name

    logging.info(f"Starting backup of '{src}' to '{archive_path}'...")

    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(src, arcname=src.name)
        
        checksum = compute_sha256(archive_path)
        archive_size_mb = archive_path.stat().st_size / (1024 * 1024)
        logging.info(f"Backup created successfully: {archive_name} ({archive_size_mb:.2f} MB)")
        logging.info(f"SHA256 Checksum: {checksum}")

        # Enforce retention policy
        prune_old_backups(dest, retention_days)

    except Exception as e:
        logging.error(f"Backup failed due to exception: {e}")
        if archive_path.exists():
            archive_path.unlink()  # Clean up incomplete archive
        sys.exit(1)

if __name__ == "__main__":
    SRC = "/var/www/html"
    DEST = "/mnt/backups"
    backup_folder(SRC, DEST, retention_days=7)
```
</details>

<details>
<summary><strong>↳ Follow-up: Can you write the same folder backup task as a shell script instead of Python?</strong></summary>

**Answer:**
Below is the equivalent production-grade Bash script implementing compression, integrity verification, and retention pruning:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Parameters
SOURCE_DIR="${1:-/var/www/html}"
BACKUP_DIR="${2:-/mnt/backups}"
RETENTION_DAYS=7
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FOLDER_NAME=$(basename "$SOURCE_DIR")
ARCHIVE_NAME="backup_${FOLDER_NAME}_${TIMESTAMP}.tar.gz"
TARGET_FILE="${BACKUP_DIR}/${ARCHIVE_NAME}"

# Pre-checks
if [ ! -d "$SOURCE_DIR" ]; then
    echo "ERROR: Source directory '$SOURCE_DIR' does not exist." >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup of '$SOURCE_DIR' to '$TARGET_FILE'..."

# Create compressed tarball
tar -czf "$TARGET_FILE" -C "$(dirname "$SOURCE_DIR")" "$FOLDER_NAME"

# Verify tar archive integrity
if tar -tzf "$TARGET_FILE" >/dev/null 2>&1; then
    CHECKSUM=$(sha256sum "$TARGET_FILE" | awk '{print $1}')
    SIZE=$(du -h "$TARGET_FILE" | awk '{print $1}')
    echo "[$(date)] SUCCESS: Backup created ($SIZE). SHA256: $CHECKSUM"
else
    echo "[$(date)] ERROR: Archive corrupted! Removing failed file." >&2
    rm -f "$TARGET_FILE"
    exit 1
fi

# Retention policy: remove backups older than 7 days
echo "[$(date)] Pruning archives older than ${RETENTION_DAYS} days in '$BACKUP_DIR'..."
find "$BACKUP_DIR" -name "backup_${FOLDER_NAME}_*.tar.gz" -type f -mtime +"$RETENTION_DAYS" -exec rm -v {} \;

echo "[$(date)] Backup process completed."
```
</details>

<details>
<summary><strong>● How would you troubleshoot a Linux system when disk usage and memory usage are exceeding acceptable limits?</strong></summary>

**Answer:**
When a production Linux node experiences simultaneous disk and memory exhaustion, I execute a structured, non-destructive troubleshooting runbook:

### 1. High Memory Exhaustion Troubleshooting
1. **Assess System Impact:**
   ```bash
   free -m
   vmstat 1 5
   ```
   - Check `available` memory rather than `free` (as buffers/cache are reclaimable).
   - Check `si` (swap in) and `so` (swap out) columns in `vmstat`. High `so` means the kernel is swapping aggressively, causing severe I/O lag.
2. **Identify Top Memory Consumers:**
   ```bash
   ps aux --sort=-%mem | head -n 11
   # Or using top sorted by memory: Shift + M
   ```
3. **Inspect Kernel OOM (Out of Memory) Killer Events:**
   ```bash
   dmesg -T | grep -E -i "oom|killed process"
   journalctl -k -g oom
   ```
4. **Inspect Shared Memory / Leaks:**
   - Check tmpfs usage: `df -h /dev/shm`
   - Check slab memory usage: `slabtop -s c` or `cat /proc/meminfo | grep -i slab`
5. **Mitigation:**
   - Restart the leaking service safely (`systemctl reload/restart <service>`).
   - If memory cache is locking up the system temporarily: `sync; echo 3 > /proc/sys/vm/drop_caches` (used cautiously in emergencies).
   - Adjust JVM `-Xmx` heap limits or configure systemd `MemoryMax` limits to prevent single-process host starvation.

---

### 2. High Disk Usage Exhaustion Troubleshooting
1. **Locate Full Filesystem:**
   ```bash
   df -hT
   df -i    # Check inode exhaustion! A 100% full inode table prevents writes even if GBs remain.
   ```
2. **Find Largest Directories and Files:**
   ```bash
   du -ahx / | sort -rh | head -n 20
   # Or inspect specific mount point:
   du -sh /var/log/* /var/lib/* 2>/dev/null | sort -rh | head -n 10
   ```
3. **Identify Deleted Files Held Open by Processes (Ghost Space):**
   When a log file is deleted while a process is still writing to it, the disk blocks cannot be freed until the file descriptor closes:
   ```bash
   lsof +L1
   # Or: lsof | grep deleted | grep -E '\.(log|txt|out)'
   ```
   - **Fix:** Truncate the file descriptor without restarting the service:
     ```bash
     > /proc/<PID>/fd/<FD_NUM>
     ```
4. **Log Rotation & Cleanups:**
   - Vacuum systemd journal logs: `journalctl --vacuum-size=500M`
   - Clean package manager caches: `yum clean all` / `apt-get clean`
   - Clean Docker assets: `docker system prune -af --volumes`
</details>

<details>
<summary><strong>↳ Follow-up: How do you check whether the Jenkins service is currently running on a Linux server?</strong></summary>

**Answer:**
Multiple commands can verify the service state across process, port, and service manager layers:

1. **Systemd Service Status (Primary):**
   ```bash
   systemctl status jenkins
   # Or programmatic exit code check:
   systemctl is-active --quiet jenkins && echo "Jenkins is running" || echo "Jenkins is NOT running"
   ```
2. **Process Table Inspection:**
   ```bash
   ps aux | grep -i '[j]enkins'
   # Or by process name:
   pgrep -a -f "jenkins.war"
   ```
3. **Listening Port Verification (Default port 8080):**
   ```bash
   ss -tulpn | grep ':8080'
   ```
4. **HTTP Health Check:**
   ```bash
   curl -s -I http://localhost:8080/login | head -n 1
   # Expect: HTTP/1.1 200 OK
   ```
</details>

<details>
<summary><strong>↳ Follow-up: How do you check whether Jenkins is installed on a server?</strong></summary>

**Answer:**
Depending on the Linux distribution and installation method:

1. **On RHEL / CentOS / Amazon Linux (RPM-based):**
   ```bash
   rpm -qa | grep -i jenkins
   # Or query package repository:
   yum list installed jenkins
   ```
2. **On Ubuntu / Debian (DEB-based):**
   ```bash
   dpkg -l | grep -i jenkins
   ```
3. **Check System Binaries & CLI:**
   ```bash
   which jenkins 2>/dev/null || echo "Jenkins binary not in PATH"
   ```
4. **Inspect Filesystem & War Locations:**
   - Standard home directory: `ls -ld /var/lib/jenkins`
   - War file location: `ls -l /usr/share/java/jenkins.war` or `/opt/jenkins/jenkins.war`
   - Systemd unit configuration: `ls -l /etc/systemd/system/jenkins.service` or `/lib/systemd/system/jenkins.service`
</details>

<details>
<summary><strong>↳ Follow-up: How do you check which ports are open on a Linux server?</strong></summary>

**Answer:**
Modern Linux administration uses the following diagnostic tools:

1. **`ss` (Socket Statistics - Modern Replacement for `netstat`):**
   ```bash
   ss -tulpn
   ```
   - `-t`: TCP sockets
   - `-u`: UDP sockets
   - `-l`: Only listening sockets
   - `-p`: Show process name and PID
   - `-n`: Numeric addresses and ports (prevents slow DNS lookups)

2. **`lsof` (List Open Files):**
   ```bash
   lsof -iTCP -sTCP:LISTEN -P -n
   # Check a specific port:
   lsof -i :8080
   ```

3. **`netstat` (Legacy systems):**
   ```bash
   netstat -tulpn
   ```

4. **External/Internal Port Scan via `nmap` or `nc`:**
   ```bash
   # Test local port via netcat:
   nc -zv 127.0.0.1 8080
   ```
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● You mentioned you have experience with Jenkins for CI/CD — is that correct?</strong></summary>

**Answer:**
Yes, that is correct. I have extensive hands-on experience architecting, managing, and optimizing enterprise Jenkins setups:

- **Distributed Master-Agent Architecture:** Running Jenkins controllers on AWS EC2 or EKS, leveraging dynamic containerized Kubernetes agents to scale build capacity from zero to hundreds of concurrent jobs.
- **Pipeline as Code (Jenkinsfile):** Developing Declarative and Scripted pipelines with modular Jenkins Shared Libraries stored in Git to enforce standardized build, test, and deployment stages across 50+ microservices.
- **Integrations:** Deeply integrated with GitHub/GitLab, SonarQube, Nexus/JFrog Artifactory, AWS ECR, Trivy, HashiCorp Vault, and Argo CD.
- **Operational Administration:** Plugin lifecycle management, backup/restore using S3 plugins or EBS snapshots, security hardening (RBAC, SSO/OIDC), and system tuning.
</details>

<details>
<summary><strong>↳ Follow-up: Do you also have experience with GitHub Actions, GitLab CI, or Azure Pipelines?</strong></summary>

**Answer:**
Yes, I have worked with **GitHub Actions** and **GitLab CI/CD** extensively in addition to Jenkins:

- **GitHub Actions:**
  - Designed multi-stage YAML workflows (`.github/workflows/deploy.yml`) utilizing matrix builds, environment protection rules, and OIDC federation with AWS IAM (eliminating long-lived IAM user keys via `aws-actions/configure-aws-credentials`).
  - Created reusable composite actions for common steps (e.g., automated semantic versioning, container security scanning).
  - Managed self-hosted runner scale sets (ARC - Actions Runner Controller) on Kubernetes.
- **GitLab CI/CD:**
  - Authored `.gitlab-ci.yml` pipelines with `stages`, `rules`, `cache`, and `artifacts`.
  - Configured GitLab Runners with Docker and Kubernetes executors.
- **Azure Pipelines:**
  - Configured multi-stage YAML pipelines using variable groups, Azure Key Vault integration, and environment deployment gates.
</details>

<details>
<summary><strong>● If you were given a task to create a multi-stage CI/CD pipeline to deploy an application, what stages/steps would you include in that pipeline?</strong></summary>

**Answer:**
A production-grade, secure, multi-stage CI/CD pipeline spans 10 distinct phases:

```
[ Git Checkout ] -> [ Compile & Unit Tests ] -> [ SAST & Quality Gate (SonarQube) ]
       |
       v
[ Dependency Scan (OWASP) ] -> [ Docker Multi-Stage Build ] -> [ Container Vulnerability Scan (Trivy) ]
       |
       v
[ Push to ECR / Registry ] -> [ GitOps Sync / Deploy to Staging ] -> [ Smoke / Integration Tests ]
       |
       v
[ Manual Approval Gate ] -> [ Canary / Blue-Green Deploy to Prod ] -> [ Post-Deploy Health Check & Alert ]
```

1. **Checkout Stage:** Clones the repository using ephemeral SSH deploy keys or GitHub App token; validates the commit SHA.
2. **Compile & Unit Test:** Compiles source code (e.g., `mvn clean test` or `npm test`), generating JUnit test XML and code coverage reports (JaCoCo).
3. **Static Code Analysis (SAST):** Runs SonarQube scanner; triggers a hard quality gate stop if coverage < 80% or any critical vulnerabilities are detected.
4. **Software Composition Analysis (SCA):** Scans open-source libraries for CVEs using Snyk or OWASP Dependency-Check.
5. **Container Build:** Builds an immutable container image using a multi-stage Dockerfile; tags the image with the Git commit SHA: `${IMAGE_REPO}:${GIT_COMMIT}`.
6. **Container Security Scanning:** Runs **Trivy** to scan the local image for OS and package CVEs (`--exit-code 1 --severity CRITICAL`).
7. **Artifact Publishing:** Authenticates and pushes the scanned image to AWS ECR / Nexus Artifactory.
8. **Continuous Delivery (CD) to Non-Prod:** Updates the Helm values or Kustomize repository via Git commit. Argo CD synchronizes changes into `qa`/`staging`.
9. **Automated Testing:** Runs smoke, API contract, and integration tests against staging.
10. **Production Release with Approvals:** Promotes the image tag to production via Canary deployment (Argo Rollouts) with automated Prometheus metrics analysis and rollback on breach.
</details>

<details>
<summary><strong>↳ Follow-up: What tool do you use for code compilation as part of your CI/CD pipeline?</strong></summary>

**Answer:**
The compilation tool depends on the language stack of the microservice:

- **Java / Kotlin:** **Apache Maven** (`mvn clean compile` / `mvn package -DskipTests`) or **Gradle** (`./gradlew assemble`).
- **Node.js / TypeScript:** **npm** (`npm run build`) or **yarn** / **pnpm**.
- **Go:** Built-in Go compiler (`CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server .`).
- **Python:** While interpreted, we run **`py_compile`** or linting/formatting checks (`flake8`, `ruff`) and package using **`pip-tools`** / **`poetry build`**.
- **.NET:** **dotnet CLI** (`dotnet publish -c Release -o ./out`).
</details>

<details>
<summary><strong>↳ Follow-up: How do you integrate Maven into your CI/CD pipeline?</strong></summary>

**Answer:**
In Jenkins, Maven is integrated using either the Jenkins **`withMaven`** step or via a containerized agent running the official Maven Docker image:

### Method 1: Containerized Pipeline Agent (Best Practice)
```groovy
pipeline {
    agent {
        docker {
            image 'maven:3.9.6-eclipse-temurin-17-alpine'
            args '-v /var/cache/m2:/root/.m2:rw' // Cache local repo across builds
        }
    }
    stages {
        stage('Compile & Test') {
            steps {
                sh 'mvn clean verify -s settings.xml'
            }
        }
    }
}
```

### Method 2: Jenkins Tool Configuration & `withMaven`
1. Configure Maven under *Manage Jenkins -> Global Tool Configuration -> Maven*.
2. In the `Jenkinsfile`:
   ```groovy
   stage('Build with Maven') {
       steps {
           withMaven(maven: 'Maven-3.9.6', mavenSettingsConfig: 'central-nexus-settings') {
               sh 'mvn clean package'
           }
       }
   }
   ```
</details>

<details>
<summary><strong>↳ Follow-up: What quality/code-coverage threshold do you configure in SonarQube?</strong></summary>

**Answer:**
In our production quality gates, we adhere to the **Clean as You Code** paradigm with strict, non-negotiable thresholds:

| Metric | New Code Threshold | Overall Code Threshold |
| :--- | :--- | :--- |
| **Code Coverage** | **>= 80%** | >= 75% |
| **Security Vulnerabilities** | **0 (Blocker / Critical)** | 0 Critical |
| **Bugs** | **0 Blocker / Critical** | <= 5 Minor |
| **Security Hotspots Reviewed**| **100%** | 100% |
| **Technical Debt Ratio** | **< 5%** (Maintainability Rating A) | < 5% |
| **Duplicated Lines Density** | **< 3%** | < 5% |

If any of these metrics are breached on the Pull Request or build branch, the SonarQube Quality Gate status returns `ERROR`, and the pipeline fails immediately.
</details>

<details>
<summary><strong>● How do you integrate SonarQube into your Jenkins CI/CD pipeline?</strong></summary>

**Answer:**
Integrating SonarQube into Jenkins requires three main components:

1. **Jenkins System Setup:**
   - Install the **SonarQube Scanner** plugin.
   - Under *Manage Jenkins -> System -> SonarQube servers*, add the SonarQube server URL and bind a SonarQube Authentication Token stored in Jenkins Credentials.
2. **SonarQube Webhook Setup:**
   - In SonarQube (*Administration -> Configuration -> Webhooks*), create a webhook pointing to:
     `https://<jenkins-url>/sonarqube-webhook/`
   - This notifies Jenkins asynchronously as soon as analysis computation completes.
3. **Jenkinsfile Implementation:**
   ```groovy
   stage('SonarQube Analysis') {
       steps {
           withSonarQubeEnv('SonarQube-Server') {
               sh '''
                   mvn sonar:sonar \
                     -Dsonar.projectKey=payment-service \
                     -Dsonar.projectName="Payment Service" \
                     -Dsonar.java.binaries=target/classes
               '''
           }
       }
   }
   stage('Quality Gate') {
       steps {
           timeout(time: 5, unit: 'MINUTES') {
               script {
                   def qg = waitForQualityGate()
                   if (qg.status != 'OK') {
                       error "Pipeline aborted: SonarQube Quality Gate failed with status ${qg.status}"
                   }
               }
           }
       }
   }
   ```
</details>

<details>
<summary><strong>↳ Follow-up: How do you integrate the ECR (Elastic Container Registry) into your Jenkins CI/CD pipeline?</strong></summary>

**Answer:**
In modern AWS architectures, ECR authentication is handled via **IAM Roles (IRSA or EC2 Instance Profile)** rather than static access keys:

### 1. IAM Permissions
The Jenkins agent's IAM role must possess:
```json
{
  "Effect": "Allow",
  "Action": [
    "ecr:GetAuthorizationToken",
    "ecr:BatchCheckLayerAvailability",
    "ecr:GetDownloadUrlForLayer",
    "ecr:BatchGetImage",
    "ecr:PutImage",
    "ecr:InitiateLayerUpload",
    "ecr:UploadLayerPart",
    "ecr:CompleteLayerUpload"
  ],
  "Resource": "*"
}
```

### 2. Jenkinsfile Integration
```groovy
environment {
    AWS_REGION = 'us-east-1'
    ECR_ACCOUNT_ID = '123456789012'
    ECR_REGISTRY = "${ECR_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    IMAGE_NAME = 'payment-service'
    IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(8)}"
}
stages {
    stage('Docker Build & Push to ECR') {
        steps {
            script {
                // Authenticate Docker with ECR without writing credentials to disk
                sh """
                    aws ecr get-login-password --region ${AWS_REGION} | \
                    docker login --username AWS --password-stdin ${ECR_REGISTRY}
                """
                
                // Build and tag
                sh """
                    docker build -t ${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} -t ${ECR_REGISTRY}/${IMAGE_NAME}:latest .
                    docker push ${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${ECR_REGISTRY}/${IMAGE_NAME}:latest
                """
            }
        }
    }
}
```
</details>

<details>
<summary><strong>● How do you implement rollback mechanisms in your CI/CD pipeline?</strong></summary>

**Answer:**
We architect rollback mechanisms across three distinct levels to achieve rapid Mean Time to Recovery (MTTR):

### 1. Kubernetes & GitOps Level (Argo CD / Helm)
- **GitOps Rollback:** Because Kubernetes manifests are stored in Git, rolling back involves reverting the image tag commit in the Git repository (`git revert HEAD && git push`). Argo CD automatically detects the revert and redeploys the known-good revision.
- **Native Kubernetes Rollback:**
  ```bash
  kubectl rollout undo deployment/payment-service --to-revision=3
  ```
- **Helm Rollback:**
  ```bash
  helm rollback payment-service 4
  ```

### 2. Automated Canary Rollbacks (Argo Rollouts / Prometheus)
- With **Argo Rollouts**, releases are routed through a Canary strategy (e.g., 10% traffic for 15 minutes).
- Automated Analysis templates continuously evaluate Prometheus queries (e.g., HTTP 5xx error rate > 0.5% or P99 latency > 300ms).
- If metrics breach the threshold, Argo Rollouts automatically aborts the rollout, restores 100% traffic to the stable replica set, and marks the deployment as failed.

### 3. Pipeline-Level Failure Traps
In the Jenkinsfile, the `post { failure { ... } }` block triggers an automated rollback script and sends critical alerts:
```groovy
post {
    failure {
        script {
            slackSend channel: '#prod-alerts', color: 'danger', message: "Deployment failed for ${env.JOB_NAME}. Initiating automated rollback..."
            sh './scripts/rollback.sh ${PREVIOUS_STABLE_TAG}'
        }
    }
}
```
</details>

#### 【 SECURITY 】

<details>
<summary><strong>● How do you manage secrets within your CI/CD pipeline?</strong></summary>

**Answer:**
Managing secrets in enterprise CI/CD requires a **Zero-Hardcoded-Secrets** policy backed by dynamic retrieval and least-privilege scoping:

1. **Centralized Secret Stores:**
   - **HashiCorp Vault / AWS Secrets Manager / AWS Systems Manager Parameter Store:** Secrets (database passwords, third-party API keys) reside in centralized, encrypted vaults—never in Git repositories or `.env` files.
2. **Dynamic In-Pipeline Injection:**
   - In Jenkins, secrets are bound at runtime using `withCredentials`:
     ```groovy
     withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
         sh 'mvn sonar:sonar -Dsonar.login=$SONAR_TOKEN'
     }
     ```
   - Jenkins automatically masks bound credential values in console output logs (`****`).
3. **Secret Scanning in Pre-commit and CI:**
   - Pre-commit hooks run **`trufflehog`** or **`detect-secrets`** to block developers from accidentally committing credentials.
   - Pipelines include automated repository secret scans as part of SAST.
4. **Kubernetes Secret Delivery:**
   - We utilize **External Secrets Operator (ESO)**: Kubernetes secrets are synchronized dynamically from AWS Secrets Manager or Vault into Kubernetes `Secret` resources, completely decoupling secrets from CI/CD pipeline definitions.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you please introduce yourself and walk me through your background and experience?
</details>
</details>

<details open>
<summary><h2>🏢 Tenarai</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 04-08-2026 10:42 PM*

#### 【 CI/CD 】

<details>
<summary><strong>● Do you also manage or have experience with Argo CD?</strong></summary>

**Answer:**
Yes, I have deep production experience implementing and managing **Argo CD** as our primary GitOps continuous delivery engine on AWS EKS:

- **GitOps Architecture:** We maintain an environment manifest repository (Helm & Kustomize) completely decoupled from application source code. Committing a new image tag to Git triggers Argo CD to reconcile desired state with live cluster state.
- **ApplicationSets:** We leverage **Argo CD ApplicationSets** with Git generator to dynamically discover and deploy 40+ microservices across multiple clusters (Dev, Staging, Prod) without duplicating boilerplate YAML.
- **Argo Rollouts Integration:** Configured advanced deployment strategies (Canary and Blue/Green) using Argo Rollouts CRDs, with automated analysis runs evaluating Prometheus metrics (error rate and latency) before promoting traffic.
- **Operations & Security:** Configured automated sync policies with self-heal, sync windows to prevent out-of-hours production deployments, and integrated SSO with Okta via Dex for role-based cluster access.
</details>

<details>
<summary><strong>● In your setup, what kind of Jenkins agents are you using to run pipelines \- static or dynamic?</strong></summary>

**Answer:**
In our production setup, we exclusively use **Dynamic Jenkins Agents running on Kubernetes (AWS EKS)** via the **Jenkins Kubernetes Plugin**, completely deprecating legacy static EC2 agents.

**Why Dynamic Kubernetes Agents?**
1. **Zero Idle Resource Costs:** Agents are ephemeral pods provisioned on-demand when a build is queued and automatically terminated upon job completion.
2. **Hermetic & Isolated Environments:** Each build runs in a brand-new container with dedicated dependencies, preventing build workspace contamination, dirty state, or dependency collisions between jobs.
3. **Multi-Container Pod Templates:** A single build pod can run specialized sidecar containers (e.g., Maven container for Java build, Kaniko container for rootless containerization, SonarQube scanner container, and AWS CLI container).
4. **Elastic Scaling:** Coupled with **Karpenter** on EKS, our cluster dynamically scales EC2 Spot instances from 0 to 50+ nodes during peak sprint release cycles and scales back down to baseline automatically.
</details>

<details>
<summary><strong>↳ Follow-up: Suppose a Jenkins agent shows offline for some reason and the pipeline gets stuck \- what steps would you take to troubleshoot this issue?</strong></summary>

**Answer:**
When a dynamic or static Jenkins agent goes offline and hangs the build queue, I execute the following troubleshooting sequence:

1. **Check Jenkins Controller Node Status:**
   - Navigate to `Manage Jenkins -> Nodes -> <Agent_Name> -> Log`.
   - Inspect the connection trace: Look for connection resets, JNLP handshake timeouts, or agent secret mismatch errors.
2. **Inspect Ephemeral Agent Pods (Kubernetes):**
   ```bash
   # Check pod lifecycle status in Jenkins namespace
   kubectl get pods -n jenkins -l jenkins=agent -o wide
   
   # Inspect events if pod is stuck in Pending, CrashLoopBackOff, or ImagePullBackOff
   kubectl describe pod <agent-pod-name> -n jenkins
   ```
   - **Pending:** Indicates cluster capacity exhaustion or taint/toleration mismatch. Check if Karpenter/Cluster Autoscaler is failing to launch new EC2 instances.
   - **ImagePullBackOff:** Check ECR authentication token expiry or VPC endpoint connectivity.
   - **CrashLoopBackOff:** Inspect container logs: `kubectl logs <agent-pod-name> -n jenkins -c jnlp`.
3. **Inspect Network & Firewall Rules:**
   - Verify TCP port `50000` (or WebSocket `443`) connectivity between agent subnet and Jenkins controller:
     ```bash
     nc -zvw3 <jenkins-master-ip> 50000
     ```
   - Ensure Security Groups allow inbound traffic from the worker node security group to the master on the agent listener port.
4. **Resource Constraints & OOM:**
   - Check if the agent pod was terminated by the Linux kernel Out-Of-Memory killer:
     ```bash
     kubectl get pod <agent-pod-name> -n jenkins -o jsonpath='{.status.containerStatuses[*].lastState.terminated.reason}'
     ```
</details>

<details>
<summary><strong>↳ Follow-up: If the console output doesn't clearly show error messages, how would you further troubleshoot the stuck Jenkins pipeline?</strong></summary>

**Answer:**
When standard pipeline console output provides no error logs, I diagnose through underlying engine diagnostics:

1. **Capture Pipeline Thread Dump:**
   - Navigate to `https://<jenkins-url>/job/<job-name>/<build-number>/threadDump`.
   - Identifies whether the Groovy CPS execution engine is blocked waiting on an external network I/O, waiting on a locked resource, or hung inside an unhandled loop.
2. **Inspect Jenkins Master System Logs:**
   - Go to *Manage Jenkins -> System Log*. Create a dedicated Logger for `org.csanchez.jenkins.plugins.kubernetes` at `ALL` or `FINE` level to trace Kubernetes API communication.
   - Check master log files directly: `/var/log/jenkins/jenkins.log`.
3. **Identify Resource Lock & Concurrency Blocks:**
   - Check if the job is waiting on a **Lockable Resource** (e.g., shared test database or environment deployment lock).
   - Check if the pipeline is blocked at an interactive **`input` step** awaiting manual user confirmation.
4. **Node-Level System Logs:**
   - SSH to the Kubernetes worker node hosting the pod and check kubelet and container runtime logs:
     ```bash
     journalctl -u kubelet -e --no-pager
     journalctl -u containerd -e --no-pager
     ```
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Have you worked with Kubernetes?</strong></summary>

**Answer:**
Yes, I have extensive production experience managing Kubernetes clusters primarily on **AWS EKS** as well as self-hosted bare-metal clusters using `kubeadm`:

- **Platform Core:** Deploying and maintaining ingress controllers (Ingress-Nginx, Traefik, AWS Load Balancer Controller), TLS cert automation (**cert-manager**), service mesh (**Istio**), and cluster autoscaling (**Karpenter**).
- **Security & RBAC:** Enforcing least privilege using IAM Roles for Service Accounts (**IRSA** / EKS Pod Identity), network segmentation via Calico **NetworkPolicies**, and policy guardrails using **Kyverno**.
- **Observability:** Deploying Prometheus Operator (Kube-Prometheus-Stack), Grafana dashboards, Loki/FluentBit log forwarders, and Jaeger tracing.
</details>

<details>
<summary><strong>● Which Kubernetes cluster version are you currently using?</strong></summary>

**Answer:**
In our production environment, we are currently running **Kubernetes version 1.29** on AWS EKS, and we are currently executing our qualification testing to upgrade to **1.30**.

**Our Production Upgrade Runbook:**
1. **API Deprecation Audit:** Run `pluto` or `kubent` against our Helm charts and Git repos to detect deprecated or removed API versions prior to upgrading.
2. **Add-on Upgrades:** Upgrade cluster managed add-ons (VPC CNI, CoreDNS, kube-proxy, AWS EBS CSI Driver) to versions compatible with the target minor release.
3. **Control Plane Upgrade:** Execute Terraform to update the EKS control plane version (`cluster_version = "1.30"`). EKS performs zero-downtime rolling upgrades of API servers and etcd.
4. **Worker Node Rolling Upgrade:** Use Karpenter node drift detection or managed node group rolling updates with **PodDisruptionBudgets (PDBs)** to ensure high availability during node draining.
</details>

<details>
<summary><strong>↳ Follow-up: Is your EKS cluster an Auto Mode (Autopilot) cluster or a traditional EKS cluster?</strong></summary>

**Answer:**
Our established production workloads run on **traditional EKS clusters** leveraging **Karpenter** for dynamic node autoscaling and AWS-managed node groups. However, following AWS re:Invent 2024, we have actively evaluated and set up proof-of-concept environments on **EKS Auto Mode**.

EKS Auto Mode is AWS's direct counterpart to Google GKE Autopilot, where AWS manages the underlying EC2 compute infrastructure, OS lifecycle, storage provisioning, and network add-ons natively.
</details>

<details>
<summary><strong>↳ Follow-up: What is the difference between a traditional EKS cluster and an EKS Auto Mode cluster, and why are organizations switching to Auto Mode now?</strong></summary>

**Answer:**
The architectural and operational differences between Traditional EKS and EKS Auto Mode are substantial:

| Feature / Dimension | Traditional EKS | EKS Auto Mode (New) |
| :--- | :--- | :--- |
| **Compute Management** | Customer manages EC2 instances, ASGs, Karpenter/CAS, and custom AMI patching | Fully AWS-managed compute. AWS automatically provisions, patches, and right-sizes EC2 nodes using built-in Karpenter |
| **OS & Security Patching** | Customer must continuously rebuild/update node AMIs for CVEs and kernel updates | AWS automatically handles zero-downtime OS and kernel security patching |
| **Storage (EBS)** | Customer must deploy and maintain the AWS EBS CSI Driver add-on and IAM roles | AWS natively provisions and manages EBS volumes dynamically when PVCs are requested |
| **Networking (VPC CNI)** | Customer manages CNI configuration, IP prefix delegation, and ENI limits | AWS natively manages pod networking and ENI attachments with optimized IP consumption |
| **Operational Overhead** | High (Day-2 operations, AMI lifecycle, add-on compatibility across upgrades) | Very Low (Serverless-like simplicity while preserving standard Kubernetes API compatibility) |

**Why Organizations Are Switching:**
1. **Massive Reduction in Operational Toil:** Eliminates the ongoing burden of building custom AMIs, tracking Linux kernel CVEs, and troubleshooting add-on version incompatibilities during EKS minor version upgrades.
2. **Built-in Karpenter Optimization:** Delivers fast sub-minute node provisioning and bin-packing out-of-the-box, significantly lowering compute waste.
3. **Preserved Kubernetes API Access:** Unlike AWS ECS or Fargate, Auto Mode maintains 100% full Kubernetes API fidelity, DaemonSet support, and standard tooling compatibility.
</details>

<details>
<summary><strong>● What kind of tasks have you performed in Kubernetes \- was it limited to deploying applications?</strong></summary>

**Answer:**
My responsibilities span comprehensive platform engineering and cluster administration, well beyond basic application deployments:

1. **Infrastructure as Code (IaC):** Provisioned EKS clusters, VPC subnets, transit gateways, and IAM role bindings using Terraform and Terragrunt.
2. **Cluster Security & Governance:**
   - Implemented **IRSA (IAM Roles for Service Accounts)** and migrated to **EKS Pod Identity**.
   - Enforced strict CIS Kubernetes Benchmarks using **Kyverno** admission controllers (disallowing root containers, enforcing read-only root filesystems, requiring memory/CPU limits).
   - Configured Calico NetworkPolicies for microsegmentation.
3. **High Availability & Autoscaling:** Configured **Horizontal Pod Autoscalers (HPA)** using custom Prometheus metrics (e.g., SQS queue depth, request latency) and integrated **Karpenter** for automated EC2 node provisioning.
4. **Storage & State Management:** Configured AWS EBS CSI and EFS CSI storage classes with volume snapshot automation.
5. **Disaster Recovery & Upgrades:** Executed multi-version cluster upgrades with zero downtime and established cluster backup and restore procedures using **Velero**.
</details>

<details>
<summary><strong>● In Helm deployments, what is the difference between the templates folder and the values.yaml file?</strong></summary>

**Answer:**
In a Helm chart, `templates/` and `values.yaml` serve as the **logic engine** and the **configuration data layer**, respectively:

### 1. `values.yaml` (The Configuration Data Layer)
- Stores default configuration values and input parameters for the chart.
- Simple, human-readable YAML defining variables like replica counts, container images, resource requests/limits, ingress hosts, and environment variables:
  ```yaml
  replicaCount: 3
  image:
    repository: 123456789012.dkr.ecr.us-east-1.amazonaws.com/payment-service
    tag: "v1.2.0"
  resources:
    limits:
      memory: "1Gi"
  ```
- Can be overridden per environment using hierarchy files (`values-dev.yaml`, `values-prod.yaml`) or command line flags (`--set image.tag=v1.3.0`).

### 2. `templates/` (The Logic & Manifest Engine)
- Contains Kubernetes manifest templates (e.g., `deployment.yaml`, `service.yaml`, `ingress.yaml`, `hpa.yaml`) embedded with **Go template syntax** (`{{ .Values.replicaCount }}`).
- Includes helper templates (`_helpers.tpl`) that define reusable template blocks, standard labels, and naming conventions.
- Executes conditional logic (`{{ if .Values.ingress.enabled }}`), loops (`{{ range .Values.env }}`), and template functions (`{{ default "latest" .Values.image.tag }}` or `{{ toYaml .Values.resources | indent 10 }}`).
</details>

#### 【 IAC 】

<details>
<summary><strong>↳ Follow-up: Did you set up the EKS Auto Mode cluster using Terraform, or did you just use an existing cluster?</strong></summary>

**Answer:**
We set up and provisioned the EKS Auto Mode cluster programmatically using **Terraform** leveraging the official AWS EKS module (`terraform-aws-modules/eks/aws` v20+):

```hcl
module "eks_auto_mode" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.31"

  cluster_name    = "prod-eks-auto"
  cluster_version = "1.30"

  cluster_endpoint_public_access  = false
  cluster_endpoint_private_access = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Enabling EKS Auto Mode configuration
  cluster_compute_config = {
    enabled    = true
    node_pools = ["general-purpose", "system"]
  }

  # Auto Mode automatically manages node IAM and capabilities
  enable_cluster_creator_admin_permissions = true

  tags = {
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}
```
This Terraform configuration provisions the cluster, activates EKS Auto Mode compute configuration, and binds the necessary AWS-managed node pools without having to manually define EC2 launch templates, auto-scaling groups, or Karpenter CRDs.
</details>

#### 【 NETWORKING 】

<details>
<summary><strong>● In your project architecture, how many load balancers are there and what are they used for?</strong></summary>

**Answer:**
In our production microservices platform, we deploy **three distinct tiers of AWS Load Balancers**, each mapped to specific security boundaries and traffic characteristics:

```
[ Public Internet ]
        |
        v  (HTTPS / 443)
+-------------------------------------------------------------+
| 1. Public External Application Load Balancer (ALB)          |
|    - AWS WAF Protected, SSL Termination, Public Ingress    |
+-------------------------------------------------------------+
        |
        v
[ EKS Cluster (Frontend & Public API Gateways) ]
        |
        v  (Internal VPC / Private Subnets)
+-------------------------------------------------------------+
| 2. Internal Private Application Load Balancer (Internal ALB)|
|    - Handles East-West Microservice Inter-Service Calls     |
|    - Private Hosted Zone (Route 53) Routing                 |
+-------------------------------------------------------------+
        |
        v
[ Core Backend Banking Services & Databases ]

+-------------------------------------------------------------+
| 3. Network Load Balancer (NLB)                              |
|    - Layer 4 Ultra-Low Latency                              |
|    - Static Elastic IPs for Third-Party Payment Gateways    |
|    - High-throughput Kafka Stream Ingestion                 |
+-------------------------------------------------------------+
```

1. **Public Application Load Balancer (External ALB):**
   - Managed automatically via the **AWS Load Balancer Controller** in EKS.
   - Fronted by **AWS WAF** (blocking OWASP Top 10, bot control, rate limiting).
   - Terminates public TLS using AWS Certificate Manager (ACM) certificates and routes ingress traffic to frontend pods and API gateway services.
2. **Internal Application Load Balancer (Private ALB):**
   - Resides strictly in private subnets, completely inaccessible from the internet.
   - Used for secure intra-VPC and cross-VPC microservice communication (e.g., Billing and Audit services calling Core Ledger services).
3. **Network Load Balancer (NLB):**
   - Layer 4 load balancer providing static Elastic IPs required by external financial partners for IP whitelisting.
   - Used for high-throughput, latency-critical TCP connections (e.g., real-time WebSocket feeds and Kafka messaging).
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>↳ Follow-up: Can you describe your project architecture and the workflow for deploying your microservices application?</strong></summary>

**Answer:**
Our platform architecture is built around a resilient, multi-AZ, microservices-based financial platform on AWS:

### 1. Architectural Infrastructure
- **Network Topology:** Multi-AZ AWS VPC across 3 Availability Zones (public subnets for NAT Gateways/ALBs, private subnets for EKS worker nodes, and isolated database subnets for RDS/ElastiCache).
- **Compute:** AWS EKS cluster running 50+ microservices on Karpenter-managed Spot and On-Demand EC2 instances.
- **Data Stores:** Amazon Aurora PostgreSQL (Multi-AZ with Read Replicas), Amazon ElastiCache (Redis) for distributed caching, and Amazon MSK (Kafka) for event streaming.
- **Observability:** Centralized Prometheus, Grafana, OpenTelemetry, and CloudWatch.

### 2. End-to-End Deployment Workflow
1. **Code Commit & PR:** A developer submits a Pull Request in GitHub. Automated GitHub Actions run unit tests, check linting, and enforce branch policies.
2. **CI Pipeline (Jenkins):**
   - Merging to `main` triggers an ephemeral Jenkins Kubernetes build pod.
   - Executes Maven compilation, JaCoCo code coverage, and SonarQube SAST analysis.
   - Executes a multi-stage Docker build, generating a hardened distroless image.
   - Scans image with **Trivy** for CVEs; on passing, pushes to **Amazon ECR** tagged with `${GIT_COMMIT}`.
3. **GitOps CD Pipeline (Argo CD):**
   - Jenkins commits the updated image tag into the dedicated GitOps manifests repository.
   - **Argo CD** detects the Git change and initiates an automated sync to the target Kubernetes namespace.
   - **Argo Rollouts** executes a **Canary release**: shifts 10% traffic to the new revision, evaluates Prometheus error rates and latency for 10 minutes, and automatically rolls forward to 100% or rolls back immediately on anomalies.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you tell me about your technical background and the tools and technologies you have mainly worked on?

● **Candidate Introduction:** How many total years of experience do you have?
</details>

<details open>
<summary><h3>Manager</h3></summary>

*Date: 04-08-2026 10:54 PM*

#### 【 CI/CD 】

<details>
<summary><strong>● Do you have experience with Jenkins?</strong></summary>

**Answer:**
Yes, I have extensive experience operating Jenkins as a core enterprise continuous integration platform across on-premise and AWS cloud environments. My experience covers managing distributed controller-agent architectures, authoring multi-branch declarative pipelines with Jenkins Shared Libraries, securing controllers with SAML/OIDC and RBAC, and integrating Jenkins with SonarQube, Trivy, Artifactory, AWS ECR, and GitOps tools like Argo CD.
</details>

<details>
<summary><strong>↳ Follow-up: In your Jenkins usage, did you create the CI/CD pipelines yourself or were they already set up when you joined?</strong></summary>

**Answer:**
I have done both. When joining established environments, I initially maintained, refactored, and optimized existing legacy scripted pipelines—migrating them to modern Declarative `Jenkinsfile` standards and implementing Jenkins Shared Libraries to eliminate duplicate code. 

Furthermore, I have architected brand-new CI/CD pipelines from scratch for greenfield microservices and cloud migration projects, setting up the complete pipeline lifecycle from git triggers, static analysis, containerization, and security scanning, to GitOps deployment manifests.
</details>

<details>
<summary><strong>↳ Follow-up: What type of Jenkins pipeline did you use, and did you write custom logic using Groovy?</strong></summary>

**Answer:**
We primarily use **Declarative Pipelines (`pipeline { ... }`)** for standardized, readable, and lintable pipeline definitions across our application repositories. 

Whenever custom business logic, dynamic loops, or complex orchestration were required, we encapsulated that logic into a centralized **Jenkins Shared Library** written in **Groovy**:
- **`vars/` (Custom Steps):** Created reusable global DSL steps, such as `buildAndScanDockerImage()`, `notifySlack()`, and `runSonarAnalysis()`, allowing developers to write 15-line standard `Jenkinsfile` configurations.
- **`src/` (Object-Oriented Utilities):** Authored Groovy helper classes for parsing JSON API payloads, querying Vault secrets, validating semantic versioning, and computing dynamic Git commit tags.
</details>

<details>
<summary><strong>● Suppose your organization has 600 microservices and 2,000 developers, and at one point 300 developers commit code simultaneously (triggering 300 builds) — how would your Jenkins infrastructure scale to handle this load?</strong></summary>

**Answer:**
Scaling Jenkins to handle 300 simultaneous builds across 600 microservices requires a **decoupled, containerized, elastic architecture**:

```
[ 300 Concurrent Webhook Commits ]
                |
                v
+-------------------------------------------------------------+
| Jenkins Controller (High-Availability / High-Memory JVM)    |
| - Pure Orchestrator (0 build executors on controller)       |
| - Offloads build execution to Kubernetes Plugin             |
+-------------------------------------------------------------+
                |
                v  (Kubernetes API - Pod Scheduling)
+-------------------------------------------------------------+
| AWS EKS Build Cluster with Karpenter Node Autoscaler        |
| - Rapidly scales EC2 Spot instances from 5 to 40+ nodes     |
| - Spins up 300 ephemeral Pod agents in parallel             |
| - Pods terminate and release capacity instantly when done   |
+-------------------------------------------------------------+
```

1. **Pure Orchestrator Controller (Zero Master Executors):**
   - Set executors on the master node to `0`. The Jenkins controller must never run build workloads. Its memory (JVM 16GB-32GB with G1GC garbage collection) is dedicated entirely to pipeline state management, webhooks, and plugin orchestration.
2. **Dynamic Ephemeral Kubernetes Agents:**
   - The Jenkins **Kubernetes Plugin** receives the build requests and immediately schedules 300 isolated Pod agents in an EKS cluster.
3. **Karpenter Cloud Auto-scaling:**
   - As 300 pods enter the `Pending` state, **Karpenter** evaluates aggregate CPU/memory demand and launches right-sized EC2 Spot instances (e.g., `c6i.4xlarge`, `c5.9xlarge`) within 30 to 45 seconds.
4. **Queue Throttling & Priority:**
   - Use the **Priority Sorter Plugin** to prioritize production hotfixes and PR builds over nightly batch regressions to ensure critical pipelines execute with zero delay.
</details>

<details>
<summary><strong>↳ Follow-up: Would you provision that many Jenkins agents to handle 300 simultaneous builds?</strong></summary>

**Answer:**
Yes, but **only ephemerally as on-demand container pods**, never as static EC2 instances:
- Provisioning 300 static EC2 instances would result in massive financial waste ($10,000s/month) during off-peak hours and weekends when utilization drops to near zero.
- With **ephemeral Kubernetes Pods running on EC2 Spot instances managed by Karpenter**, 300 agents spin up in parallel across a dynamically expanded compute pool, execute for the 5-10 minute duration of the build, and immediately terminate. We only pay for the exact compute seconds consumed.
</details>

<details>
<summary><strong>↳ Follow-up: How do you auto-scale your Jenkins build agents?</strong></summary>

**Answer:**
Auto-scaling Jenkins build agents involves a two-layer scaling mechanism:

1. **Layer 1: Jenkins Kubernetes Plugin (Pod Level):**
   - Jenkins monitors its build queue. When 300 jobs arrive with label `k8s-agent`, the plugin makes batch API calls to the Kubernetes API server (`/api/v1/namespaces/jenkins/pods`) to create 300 agent pods.
2. **Layer 2: Karpenter / Cluster Autoscaler (Infrastructure Level):**
   - As agent pods enter `Pending` state due to insufficient CPU/memory on existing worker nodes, **Karpenter** intercepts the pending pod scheduling events.
   - Karpenter evaluates pod resource requests, groups them, and provisions the optimal blend of diverse EC2 Spot instance types across multiple Availability Zones in under 45 seconds.
   - When builds complete, agent pods exit and are deleted. Karpenter detects underutilized nodes and terminates the idle EC2 instances (consolidation feature) within 5 minutes.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>↳ Follow-up: Is your primary focus deployment on AWS EKS?</strong></summary>

**Answer:**
Yes, AWS EKS serves as our primary production compute backbone. All customer-facing microservices, internal data processing workers, API gateways, and CI/CD agent infrastructure are architected and deployed on AWS EKS across multiple regions and multi-AZ environments.
</details>

<details>
<summary><strong>↳ Follow-up: How would you scale Jenkins build agents using Kubernetes pods instead of EC2-based agents?</strong></summary>

**Answer:**
In the Jenkinsfile, we define a declarative **`podTemplate`** containing lightweight containers for each tool required by the pipeline:

```groovy
pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    role: jenkins-agent
spec:
  containers:
  - name: maven
    image: maven:3.9.6-eclipse-temurin-17-alpine
    command: ['cat']
    tty: true
    resources:
      requests:
        cpu: "1000m"
        memory: "2Gi"
      limits:
        cpu: "2000m"
        memory: "4Gi"
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command: ['cat']
    tty: true
"""
        }
    }
    stages {
        stage('Build with Maven') {
            steps {
                container('maven') {
                    sh 'mvn clean package -DskipTests'
                }
            }
        }
    }
}
```
When this pipeline triggers, Jenkins creates this Pod on EKS. The build runs inside the container, and Jenkins terminates the pod as soon as the pipeline exits.
</details>

<details>
<summary><strong>↳ Follow-up: If your autoscaling criteria are met and 300 pods need to be created, each pod requires an IP address — how would you handle IP allocation for that many pods?</strong></summary>

**Answer:**
Under the standard AWS VPC CNI on EKS, every pod receives a native private IP address directly from the VPC subnet CIDR block. Allocating 300 IPs rapidly requires two key architectural configurations:

1. **Enable AWS VPC CNI Prefix Delegation (`ENABLE_PREFIX_DELEGATION=true`):**
   - Instead of allocating individual `/32` IP addresses to Elastic Network Interfaces (ENIs), Prefix Delegation assigns an entire `/28` IPv4 subnet prefix (16 IP addresses) to each available ENI slot.
   - This dramatically accelerates IP allocation speed, reduces API throttling from AWS EC2 ENI attachment calls, and allows nodes to support up to 110 pods per instance.
2. **Pre-warm Warm IP and Prefix Targets:**
   - Configure `WARM_PREFIX_TARGET=1` and `MINIMUM_IP_TARGET=30` in the `aws-node` DaemonSet environment variables. This ensures the CNI maintains an idle pool of warm IPs ready for immediate pod binding without waiting for ENI attachment during burst scaling.
</details>

<details>
<summary><strong>↳ Follow-up: If your subnet only has 100 available IP addresses but you need to create 300 pods, is that possible?</strong></summary>

**Answer:**
Under default AWS VPC CNI behavior within that single subnet: **No, it is impossible directly.** The first 100 pods will receive IP addresses, while the remaining 200 pods will remain stuck in `Pending` or `ContainerCreating` with the error:
`FailedCreatePodSandBox: no IP addresses available in subnet`.

### Production Solutions to Overcome Subnet IP Exhaustion:
1. **EKS Custom Networking (Recommended Production Solution):**
   - Associate a secondary, non-overlapping CIDR block to the VPC (e.g., from the Carrier-Grade NAT space `100.64.0.0/16` or private `10.200.0.0/16`).
   - Create large dedicated subnets (e.g., `/19` giving 8,192 IPs) in this secondary CIDR.
   - Enable `AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG=true` and define `ENIConfig` CRDs per Availability Zone.
   - Pods are automatically assigned secondary IP addresses from the large secondary subnet pool, while EC2 worker nodes retain primary IPs in the original subnet.
2. **Adopt an Overlay CNI (e.g., Cilium or Calico with VXLAN/Geneve):**
   - Overlay networking decouples pod IP allocation completely from the underlying AWS VPC subnets by assigning internal private virtual IPs (e.g., `172.16.0.0/12`) to pods, routing traffic through eBPF/VXLAN tunnels.
</details>

<details>
<summary><strong>↳ Follow-up: If you don't know the exact scaling requirements in advance, how would you decide on the size of the CIDR block to allocate for pod IPs?</strong></summary>

**Answer:**
When scaling demands are unpredictable, we follow an architectural sizing formula and leverage **RFC 6598 Carrier-Grade NAT Space (`100.64.0.0/10`)**:

### Sizing Formula:
$$\text{Total IPs Needed} = (\text{Peak Nodes} \times \text{Max Pods Per Node}) \times \text{Buffer (2.5x)}$$

- **Buffer Considerations:**
  - **Surge Capacity for Rolling Upgrades:** Node upgrades spin up new replacement nodes and pods before terminating old ones, requiring up to 100% additional IP headroom.
  - **Ephemeral Burst Workloads:** Dynamic CI/CD agents and batch processing jobs.
  - **AWS Reserved IPs:** AWS reserves 5 IPs in every subnet.

### Best-Practice Approach:
- Do not constrain your cluster to small `/24` subnets (251 usable IPs).
- Associate a secondary CIDR of **`/16` (65,536 IPs)** or **`/18` (16,384 IPs)** from `100.64.0.0/10` to the VPC dedicated solely for Pod IP allocation via EKS Custom Networking. Because this IP space is non-routable over the public internet, it prevents depleting valuable corporate RFC 1918 private IP space while providing virtually limitless scaling capacity.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Can you describe your day-to-day activities and what level of technical expertise you have in AWS specifically?</strong></summary>

**Answer:**
I operate at a **Senior / Principal DevOps & Platform Engineer** level in AWS, backed by extensive production administration across core services:

- **Core Focus Areas:**
  - **Compute & Orchestration:** EKS cluster architecture, Karpenter autoscaling, EC2 launch templates, Auto Scaling Groups, and AWS Lambda event-driven workers.
  - **Networking & Security:** Multi-AZ VPC design, Transit Gateway, Route 53 private zones, AWS WAF, Security Groups, IAM (IRSA, Permission Boundaries, SCPs), and KMS encryption.
  - **Storage & Databases:** Amazon S3 lifecycle and replication policies, EBS CSI volume management, Amazon Aurora PostgreSQL, and DynamoDB.
  - **Observability & Automation:** CloudWatch Log Groups, Metric Alarms, CloudTrail audits, and infrastructure provisioning via Terraform and Terragrunt.
</details>

<details>
<summary><strong>● What other AWS services or tasks do you work with besides EKS?</strong></summary>

**Answer:**
Outside of EKS, my daily infrastructure responsibilities cover:
- **IAM & Security:** Enforcing least privilege, implementing AWS IAM Identity Center (SSO), rotating IAM credentials, and managing KMS keys with automated annual key rotation.
- **Data & Caching:** Provisioning and maintaining Amazon Aurora PostgreSQL Multi-AZ clusters and Amazon ElastiCache (Redis) clusters with automated snapshot lifecycles.
- **Messaging & Streaming:** Managing Amazon MSK (Managed Streaming for Apache Kafka) and Amazon SQS/SNS for decoupled asynchronous microservice architectures.
- **Edge & CDN:** Configuring Amazon CloudFront distributions with custom SSL certificates (ACM) and AWS WAF rate-limiting rules.
- **Serverless:** Authoring Python-based AWS Lambda functions for infrastructure housekeeping and Slack incident notifications.
</details>

<details>
<summary><strong>● Suppose one service (A) creates files in an S3 bucket and another service (B) processes and deletes those files. If asked to verify that service A created 1,000 files and service B processed and deleted all 1,000 within a given timeline, how would you determine this?</strong></summary>

**Answer:**
To verify and audit this asynchronous file lifecycle without impacting running workloads, I utilize **Amazon S3 Server Access Logs or AWS CloudTrail Data Events analyzed via Amazon Athena**:

### Step-by-Step Audit via Athena & S3 Access Logs:
1. **Query S3 Access Logs via Amazon Athena:**
   Run an SQL query against the access logs bucket filtering for the specific time window and bucket:
   ```sql
   SELECT 
       requestdatetime,
       operation,
       key,
       httpstatus
   FROM "s3_access_logs_db"."bucket_logs"
   WHERE bucket_name = 'production-exchange-bucket'
     AND parse_datetime(requestdatetime, 'dd/MMM/yyyy:HH:mm:ss Z') 
         BETWEEN timestamp '2026-08-04 10:00:00' AND timestamp '2026-08-04 12:00:00'
     AND operation IN ('REST.PUT.OBJECT', 'REST.DELETE.OBJECT');
   ```
2. **Reconcile Counts:**
   ```sql
   SELECT 
       operation, 
       COUNT(DISTINCT key) as total_unique_files
   FROM "s3_access_logs_db"."bucket_logs"
   WHERE bucket_name = 'production-exchange-bucket'
     AND operation IN ('REST.PUT.OBJECT', 'REST.DELETE.OBJECT')
   GROUP BY operation;
   ```
   - If `REST.PUT.OBJECT` = 1,000 and `REST.DELETE.OBJECT` = 1,000, and a `LEFT JOIN` on `key` reveals zero unmatched PUT keys, this confirms 100% processing and deletion.
</details>

<details>
<summary><strong>↳ Follow-up: Besides enabling CloudTrail data events, what other methods could you use to track file creation and processing activity in S3?</strong></summary>

**Answer:**
Beyond CloudTrail data events, several robust architectures track S3 activity:

1. **S3 Event Notifications with Amazon EventBridge / SQS (Best Practice):**
   - Configure S3 to emit `s3:ObjectCreated:*` and `s3:ObjectRemoved:Delete` events to an SQS audit queue or Amazon EventBridge.
   - CloudWatch metrics automatically track `NumberOfMessagesSent` vs `NumberOfMessagesDeleted`.
2. **S3 Server Access Logging:** Detailed access records written to a target bucket, analyzed via Amazon Athena.
3. **Amazon S3 Inventory Reports:** Generates scheduled CSV/Parquet reports of all bucket objects and metadata to detect lingering files.
4. **CloudWatch Storage Metrics & Request Metrics:** Enabling **S3 Request Metrics** provides real-time CloudWatch graphs for `PutRequests` and `DeleteRequests`.
</details>

<details>
<summary><strong>↳ Follow-up: Have you heard of S3 server access logs as a way to track bucket activity?</strong></summary>

**Answer:**
Yes, absolutely. **S3 Server Access Logging** provides detailed records for every request made against a bucket. 

**Key Characteristics:**
- Records requester IP, bucket name, request time, action (`REST.PUT.OBJECT`, `REST.GET.OBJECT`, `REST.DELETE.OBJECT`), HTTP status, and error codes.
- It is delivered on a best-effort basis to a designated target logging bucket.
- **Cost-Effective:** Unlike CloudTrail data events (which cost $0.10 per 100,000 events), S3 Server Access Logging incurs no request fees—you only pay for the storage of the log files in the target bucket, making it the preferred choice for high-volume audit logging analyzed via Athena.
</details>

<details>
<summary><strong>● What do you use EC2 for in your projects — are you hosting applications directly on EC2, or only using it to support EKS deployments?</strong></summary>

**Answer:**
In our modern cloud architecture, **90% of our EC2 usage supports EKS deployments** as container worker nodes managed via Karpenter and Managed Node Groups. 

However, we do maintain specialized EC2 instances for:
1. **Secure Bastion / Jump Hosts:** Hardened instances inside private subnets accessed strictly via **AWS Systems Manager (SSM) Session Manager** with zero open inbound ports.
2. **Dedicated Stateful / Heavy Caching Appliances:** Legacy licensed database engines or high-memory caching servers that are not yet containerized.
3. **Self-Hosted CI/CD Specialized Runners:** Heavy GPU or hardware-specific build machines for complex compilation workloads.
</details>

<details>
<summary><strong>● What is an AMI (Amazon Machine Image)?</strong></summary>

**Answer:**
An **AMI (Amazon Machine Image)** is a packaged, immutable master image containing the complete operating environment required to launch an EC2 instance. It includes:
- A **Root Volume Template:** Snapshot of the OS, software packages, configuration files, and runtime binaries.
- **Launch Permissions:** Dictates which AWS accounts have authority to launch instances from the AMI.
- **Block Device Mapping:** Configures attached EBS volumes and instance store volumes.
</details>

<details>
<summary><strong>↳ Follow-up: How do you go about creating an AMI?</strong></summary>

**Answer:**
In production, we adhere to **Golden Image Pipelines** using automated Infrastructure-as-Code rather than manual console snapshots:

1. **HashiCorp Packer Automation (Recommended Production Standard):**
   - Write a Packer template (`hcl`):
     ```hcl
     source "amazon-ebs" "golden_ami" {
       ami_name      = "golden-linux-2026-{{timestamp}}"
       instance_type = "t3.medium"
       region        = "us-east-1"
       source_ami_filter {
         filters = {
           name                = "al2023-ami-2023.*-x86_64"
           virtualization-type = "hvm"
         }
         owners      = ["amazon"]
         most_recent = true
       }
       ssh_username = "ec2-user"
     }
     build {
       sources = ["source.amazon-ebs.golden_ami"]
       provisioner "ansible" {
         playbooks = ["./playbooks/cis-hardening.yml", "./playbooks/install-agents.yml"]
       }
     }
     ```
   - Packer boots an ephemeral instance, applies Ansible plays (CIS Linux hardening, installs SSM Agent, CloudWatch agent, Falcon sensor), stops the instance, creates the AMI, and terminates the build instance.
2. **AWS EC2 Image Builder:** An AWS-native pipeline service that automates image build, security tests, and multi-region sharing.
3. **Manual CLI (Ad-hoc):**
   ```bash
   aws ec2 create-image --instance-id i-0123456789abcdef0 --name "backup-ami" --no-reboot
   ```
</details>

<details>
<summary><strong>● If you use an AMI with a user data script to launch hundreds of EC2 instances and the user data script fails on some of them, what is a scalable way to debug this issue without having to log into each instance individually?</strong></summary>

**Answer:**
Logging into hundreds of instances via SSH is anti-pattern and unscalable. We debug this centrally using **AWS Systems Manager (SSM) and CloudWatch Logs**:

1. **Pre-configured Centralized CloudWatch Agent in Golden AMI:**
   - The golden AMI's CloudWatch configuration automatically tails and streams `/var/log/cloud-init-output.log` and `/var/log/user-data.log` into CloudWatch Logs (`/aws/ec2/userdata`).
   - In CloudWatch Logs Insights, run a single query across all instances:
     ```
     fields @timestamp, @logStream, @message
     | filter @message like /error/ or @message like /failed/ or @message like /exit status/
     | sort @timestamp desc
     | limit 100
     ```
2. **AWS Systems Manager (SSM) Run Command:**
   - Execute an SSM command across the entire Auto Scaling Group or tag group (`aws:autoscaling:groupName`):
     ```bash
     aws ssm send-command \
       --targets "Key=tag:Environment,Values=production" \
       --document-name "AWS-RunShellScript" \
       --parameters 'commands=["grep -Ei \"error|failed|fatal\" /var/log/cloud-init-output.log | tail -n 20"]' \
       --output-s3-bucket-name "my-central-audit-bucket"
     ```
   - Review consolidated outputs aggregated in S3 or the SSM Console.
</details>

<details>
<summary><strong>↳ Follow-up: If, out of hundreds of EC2 instances, 15 failed to get the expected user data configuration, how would you debug this at scale, given that logging into each instance individually is not feasible?</strong></summary>

**Answer:**
To isolate and debug the 15 failing instances at scale:

1. **Identify the 15 Instance IDs via SSM Compliance:**
   - Query SSM State Manager or Run Command execution status to list instances with status `Failed`:
     ```bash
     aws ssm list-command-invocations \
       --command-id "<COMMAND_ID>" \
       --details \
       --query "CommandInvocations[?Status=='Failed'].[InstanceId,StatusDetails]" \
       --output table
     ```
2. **Capture Instance Console Outputs via AWS CLI:**
   - Write a quick shell one-liner to dump system console logs for just those 15 instances:
     ```bash
     for id in $(cat failing_instances.txt); do
       echo "=== Instance: $id ==="
       aws ec2 get-console-output --instance-id "$id" --output text | grep -E -A 5 -B 5 "cloud-init.*fail"
     done
     ```
3. **Root Cause Pattern Analysis:**
   - Correlate commonalities across the 15 failures: Are they all located in a specific Availability Zone (indicating a missing subnet route table or full NAT Gateway)? Did they experience transient network timeout reaching external package repositories?
</details>

<details>
<summary><strong>↳ Follow-up: Is there any other way, apart from checking user data logs, that you could use to investigate this kind of failure?</strong></summary>

**Answer:**
Yes, several complementary diagnostic channels identify failure causes:

1. **VPC Flow Logs & NAT Gateway Metrics:**
   - Check VPC Flow Logs for the failing instances' private IPs. Look for `REJECT` records on port 443, indicating Security Group, Network ACL, or routing misconfigurations blocking outbound yum/apt repository access.
2. **Instance Metadata & IAM Role Verification:**
   - Check whether the instance failed because it could not retrieve AWS credentials:
     ```bash
     aws ec2 describe-instances --instance-ids <id> --query "Reservations[].Instances[].IamInstanceProfile"
     ```
3. **AWS Systems Manager State Manager Association:**
   - Use SSM State Manager compliance dashboards to identify which exact configuration association drifted or errored out.
4. **EC2 Instance Status Checks:**
   - Check if `StatusCheckFailed_System` or `StatusCheckFailed_Instance` fired due to underlying hardware degradation or memory starvation during boot.
</details>

<details>
<summary><strong>● If you have created hundreds of EC2 instances and need to domain-join all of them, how would you do that?</strong></summary>

**Answer:**
Domain-joining hundreds of EC2 instances (Windows or Linux) is achieved through automated, zero-touch orchestration using **AWS Systems Manager (SSM) Seamless Domain Join**:

1. **AWS Directory Service Integration:**
   - Utilize AWS Managed Microsoft AD or AD Connector.
2. **SSM Document (`AWS-JoinDirectoryServiceDomain`):**
   - Create an **SSM State Manager Association** targeting instances by tag (e.g., `DomainJoin = true`):
     ```bash
     aws ssm create-association \
       --name "AWS-JoinDirectoryServiceDomain" \
       --targets "Key=tag:JoinDomain,Values=true" \
       --parameters '{
         "directoryId": ["d-90670xxxxx"],
         "directoryName": ["corp.company.com"],
         "dnsIpAddresses": ["10.0.10.15", "10.0.20.15"]
       }'
     ```
3. **Launch Automation via Terraform / Launch Template:**
   - Ensure the EC2 Instance Profile includes the AWS-managed policy **`AmazonSSMDirectoryServiceAccess`**.
   - As instances launch, the SSM agent executes the domain-join document automatically, provisions computer objects in Active Directory, reboots if necessary, and marks compliance in SSM.
</details>

<details>
<summary><strong>● Have you worked with AWS Lambda?</strong></summary>

**Answer:**
Yes, I have extensive experience developing and deploying AWS Lambda functions for infrastructure automation, event-driven integration, and security enforcement:

- **Operational Automation:** Lambda functions (Python 3.11 with `boto3`) to stop non-production RDS and EC2 instances outside business hours, saving ~40% on non-prod cloud spend.
- **Security & Compliance Remediation:** EventBridge-triggered Lambdas that detect unencrypted S3 buckets or public security group ingress (`0.0.0.0/0`) and automatically revoke the rule or apply bucket encryption.
- **CI/CD Event Handlers:** Processing webhook events from GitHub/Bitbucket to trigger ephemeral container workflows.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● Have you worked with Amazon CloudWatch?</strong></summary>

**Answer:**
Yes, I use Amazon CloudWatch daily as the native observability and alerting plane across our AWS estate:
- **CloudWatch Logs:** Ingesting, aggregating, and retaining application and system logs using Unified CloudWatch Agent and FluentBit; running log analytics via **Logs Insights**.
- **CloudWatch Metrics & Alarms:** Creating high-resolution (1-second / 10-second) metric alarms with composite alarm logic (e.g., alerting only when high CPU coincides with high 5xx error rates) routed to PagerDuty/Slack via Amazon SNS.
- **CloudWatch Dashboards:** Building real-time operational single-pane-of-glass dashboards for executives and on-call engineers.
- **CloudWatch Container Insights:** Monitoring cluster, node, pod, and container resource metrics on EKS.
</details>

<details>
<summary><strong>● Suppose you have an application hosted on EC2 that generates logs containing errors. How would you ship those logs to a CloudWatch Log Group?</strong></summary>

**Answer:**
The standard, production-grade method is deploying and configuring the **Unified Amazon CloudWatch Agent**:

### 1. IAM Instance Profile Permission
Attach an IAM role to the EC2 instance containing the AWS-managed policy:
**`CloudWatchAgentServerPolicy`** (grants `logs:CreateLogStream`, `logs:PutLogEvents`, `logs:DescribeLogStreams`).

### 2. Install CloudWatch Agent (via User Data, Ansible, or SSM)
```bash
sudo yum install -y amazon-cloudwatch-agent
# Or on Ubuntu:
# wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
# dpkg -i -E ./amazon-cloudwatch-agent.deb
```

### 3. Agent Configuration File (`/opt/aws/amazon-cloudwatch-agent/bin/config.json`)
```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/application/*.log",
            "log_group_name": "/aws/ec2/production/application",
            "log_stream_name": "{instance_id}",
            "timestamp_format": "%Y-%m-%d %H:%M:%S",
            "timezone": "UTC",
            "multi_line_start_pattern": "{datetime_format}"
          }
        ]
      }
    }
  }
}
```

### 4. Start & Verify Agent
```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json

# Check running status
systemctl status amazon-cloudwatch-agent
```

### 5. Automated Metric Filter for Errors
In CloudWatch Logs, configure a Metric Filter on the log group:
- **Filter Pattern:** `[timestamp, level = "ERROR" || level = "FATAL", message]`
- Publish metric `AppErrorCount` to namespace `CustomApp/Metrics` and trigger a CloudWatch Alarm if `AppErrorCount > 5` over 1 minute.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you explain what your current role and responsibilities are?
</details>

</details>

<details open>
<summary><h2>🏢 CitiusTech</h2></summary>

<details open>
<summary><h3>Manager</h3></summary>

*Date: 04-08-2026 11:25 PM*

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Can you describe the project you are currently working on, including its overall architecture?</strong></summary>

**Answer:**
I am currently working on an enterprise **Healthcare Data Interoperability & Analytics Platform** designed to ingest, process, and normalize electronic health records (EHR / HL7 / FHIR data) for clinical analytics and insurance claims adjudication:

```
[ Healthcare Providers / External EHRs ]
                   |
                   v (HTTPS / TLS 1.3)
      [ Route 53 + AWS WAF ]
                   |
                   v
   [ External Application Load Balancer ]
                   |
                   v
+-------------------------------------------------------------------+
| AWS EKS Cluster (Private Multi-AZ VPC across 3 AZs)              |
|                                                                   |
| [ Ingress-Nginx Controller with Cert-Manager ]                   |
|       |                                                           |
|       +--> [ FHIR Ingestion Gateway Pods (Spring Boot) ]         |
|                   |                                               |
|                   v (Kafka Producer)                              |
|          [ Amazon MSK (Kafka Cluster) ]                           |
|                   |                                               |
|                   v (Kafka Consumer Stream)                       |
|       +--> [ Claims Validation & Normalization Engine ]           |
|       +--> [ Patient Master Index Service ]                       |
|       +--> [ Audit & Compliance Logging Service ]                 |
+-------------------------------------------------------------------+
       |                    |                    |
       v                    v                    v
[ Amazon Aurora PG ]   [ ElastiCache Redis ]  [ S3 Compliant Data Lake ]
  (Multi-AZ HIPAA)       (Session / Token)       (KMS Encrypted WORM)
```

### Architectural Key Pillars:
1. **Network & Ingress Security:**
   - Isolated Multi-AZ VPC across 3 Availability Zones. All EKS worker nodes, databases, and message brokers reside in strictly private subnets.
   - Ingress is fronted by **AWS WAF** (rate limiting, geo-fencing, SQLi/XSS filtering) and an AWS Application Load Balancer terminating mutual TLS (mTLS).
2. **Compute & Scalability:**
   - Containerized microservices running on **AWS EKS 1.29**, autoscaled using **Karpenter** on EC2 Spot and On-Demand instances.
   - In-cluster traffic is encrypted in transit using **Istio Service Mesh** with strict mTLS between microservices.
3. **Data & Messaging Tier:**
   - **Amazon MSK (Apache Kafka):** Handles decoupled, asynchronous event-driven streaming of patient events with at-least-once delivery guarantees.
   - **Amazon Aurora PostgreSQL Multi-AZ:** Stores normalized clinical records with transparent data encryption (TDE via AWS KMS).
   - **Amazon S3 with Object Lock:** Long-term archival of raw immutable medical logs compliant with HIPAA and HITRUST requirements.
4. **GitOps CI/CD:**
   - Centralized multi-branch pipelines in Jenkins (CI) publishing container images to private Amazon ECR.
   - Continuous deployment managed through **Argo CD** and **Argo Rollouts** using automated Canary verification.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you tell me about yourself, including your roles and responsibilities in your current or past positions?

↳ **Candidate Introduction:** What is the business domain of the project you described, and what other projects have you worked on previously?

↳ **Candidate Introduction:** Have you worked on any client-facing projects?

↳ **Candidate Introduction:** Who are the end users of the project or system you worked on?

● **Candidate Introduction:** Do you have any questions for me?
</details>

<details open>
<summary><h3>Level 2</h3></summary>

*Date: 05-08-2026 12:42 AM*

#### 【 CI/CD 】

<details>
<summary><strong>● Can you explain your CI/CD workflow end to end?</strong></summary>

**Answer:**
Our end-to-end CI/CD workflow follows a rigorous **GitOps-driven, Trunk-Based Development** model with automated security gates at every stage:

1. **Feature Development & Peer Review:**
   - Developers branch off `main` (`feature/JIRA-1234-auth-fix`).
   - On opening a Pull Request (PR), automated GitHub Actions run fast unit tests (`mvn test`), linting checks, and pre-commit secret scans (`detect-secrets`).
2. **Continuous Integration (CI via Jenkins):**
   - Merging the PR into `main` triggers an ephemeral Jenkins Kubernetes build agent pod.
   - **Static Analysis:** SonarQube analyzes code quality; pipeline enforces a blocking Quality Gate (80% coverage, 0 critical bugs).
   - **Compilation & Containerization:** Multi-stage Docker build compiles the application and produces an immutable, distroless runtime container image.
   - **Security Scanning:** **Trivy** scans the newly created image for OS and package CVEs. The build fails if any fixable `CRITICAL` vulnerability exists.
   - **Publish Artifact:** The image is pushed to **Amazon ECR** tagged with the immutable commit SHA: `${ECR_REGISTRY}/${SERVICE_NAME}:${GIT_COMMIT}`.
3. **Continuous Delivery (CD via Argo CD):**
   - Jenkins executes a bot commit updating the image tag in our dedicated GitOps configuration repository (`helm/values-staging.yaml`).
   - **Argo CD** running inside the EKS cluster detects the commit within 60 seconds and synchronizes the desired state to the `staging` namespace.
   - Automated integration and smoke tests execute against staging.
4. **Production Release (Argo Rollouts):**
   - Promoting to production requires an approved release tag and change ticket sign-off.
   - **Argo Rollouts** executes a Canary deployment: routes 10% traffic to the new revision, evaluates Prometheus metrics (HTTP 5xx rate < 0.1%, p99 latency < 250ms), and progressively shifts traffic to 100% over 20 minutes, with immediate automated rollback on anomaly detection.
</details>

<details>
<summary><strong>↳ Follow-up: Can you list out the exact sequence of stages in your CI/CD pipeline \- what is the first stage, what is the second stage, and so on?</strong></summary>

**Answer:**
Below is the precise sequence of the 10 stages executed in our production `Jenkinsfile`:

1. **Stage 1: Checkout SCM:** Clones the repository using ephemeral SSH deploy keys; validates the Git commit hash and branch metadata.
2. **Stage 2: Code Linting & Formatting:** Verifies code styling standards (Checkstyle / Spotless / ESLint) to ensure code maintainability.
3. **Stage 3: Unit Testing & JaCoCo Coverage:** Runs automated unit tests and generates XML test results and code coverage metrics.
4. **Stage 4: SonarQube SAST & Quality Gate:** Executes `mvn sonar:sonar` within `withSonarQubeEnv` and waits for webhook callback with `waitForQualityGate()`.
5. **Stage 5: Dependency & License Scanning:** Scans application dependencies for known open-source CVEs and licensing violations using OWASP Dependency-Check.
6. **Stage 6: Docker Multi-Stage Build:** Builds the hardened, minimal container image and tags it with the Git commit SHA.
7. **Stage 7: Trivy Vulnerability Scan:** Runs container security scan locally on the newly built image (`trivy image --exit-code 1 --severity CRITICAL`).
8. **Stage 8: Push to Amazon ECR:** Authenticates via AWS IAM and pushes the validated image to Amazon ECR.
9. **Stage 9: Update GitOps Repository:** Commits the new image tag into the Helm manifests Git repository to trigger Argo CD.
10. **Stage 10: Post-Build Notification & Slack Webhook:** Sends build status notification (Pass/Fail, duration, SonarQube report link) to the team Slack channel.
</details>

<details>
<summary><strong>↳ Follow-up: Does every one of your 15 microservices trigger its own complete CI/CD pipeline?</strong></summary>

**Answer:**
**Yes, absolutely.** Every single microservice maintains its own dedicated Git repository and its own independent CI/CD pipeline.

**Why Independent Pipelines?**
1. **Decoupled Release Lifecycles:** Microservices architecture is designed around independent deployability. A bug fix or feature addition in the `patient-service` must never trigger unnecessary builds, tests, or deployments of the `claims-service` or `billing-service`.
2. **Minimized Blast Radius:** A failure in one microservice's CI pipeline (e.g., failed unit test or SonarQube breach) only blocks that specific service, allowing the remaining 14 microservices to continue shipping code uninterrupted.
3. **Optimized Build Times:** Builds complete in 3 to 5 minutes rather than 45 minutes for a monolithic build.
4. **Standardization via Shared Libraries:** Although each repository has its own `Jenkinsfile`, all 15 pipelines call a single, centralized **Jenkins Shared Library** (`buildMicroservicePipeline()`), guaranteeing 100% uniformity in security, testing, and deployment standards across all services.
</details>

<details>
<summary><strong>↳ Follow-up: When you trigger the pipeline multiple times from the same branch, how do you ensure each resulting artifact/image is stored uniquely in ECR without being overwritten?</strong></summary>

**Answer:**
We prevent image overwriting through **dual tagging strategies** combined with **ECR Repository Immutability**:

1. **Tagging with Immutable Unique Identifiers:**
   - We never tag production images solely with mutable identifiers like `develop`, `staging`, or `latest`.
   - Instead, every build tags the image with a composite identifier containing the unique Jenkins Build Number and Git Commit Hash:
     ```
     ${SERVICE_NAME}:build-${BUILD_NUMBER}-${GIT_COMMIT_SHORT}
     # Example: payment-service:build-142-a7f9b3c
     ```
   - Even if triggered 10 times consecutively on the same `main` branch without new commits, `${BUILD_NUMBER}` increments (`build-142`, `build-143`), guaranteeing a distinct, unique tag in ECR.

2. **Enabling ECR Image Tag Immutability:**
   - In Terraform, we enable `image_tag_mutability = "IMMUTABLE"` on all ECR repositories:
     ```hcl
     resource "aws_ecr_repository" "microservice" {
       name                 = "payment-service"
       image_tag_mutability = "IMMUTABLE"
       image_scanning_configuration {
         scan_on_push = true
       }
     }
     ```
   - If a build accidentally attempts to push an existing tag, ECR rejects the push with `ImageTagAlreadyExistsException`, preventing accidental overwrites of tested artifacts.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>↳ Follow-up: Why do you check the Kubernetes (EKS) cluster status as part of your daily routine? Can you give me some reasons?</strong></summary>

**Answer:**
Checking the EKS cluster status at the beginning of each workday is essential for **proactive platform reliability, security posture, and cost control**:

1. **Node Health & Condition Checks:**
   - Execute `kubectl get nodes` to detect any nodes in `NotReady` state or suffering from kernel issues, disk pressure, memory pressure, or PID exhaustion.
2. **Pod Health & Crash Detection:**
   - Check for failing or flapping pods:
     ```bash
     kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded
     ```
   - Identifies silent application degradation: pods stuck in `CrashLoopBackOff`, `ImagePullBackOff`, or `Pending`.
3. **Autoscaler & Capacity Monitoring:**
   - Inspect **Karpenter / Cluster Autoscaler** logs and metrics. Verify whether nodes scaled down as expected overnight to consolidate idle resources and control cloud costs.
4. **Storage & PV/PVC Health:**
   - Check for unbound PVCs or stuck AWS EBS volume attachments (`kubectl get pvc -A | grep -v Bound`).
5. **Control Plane & Add-On Observability:**
   - Check CloudWatch Container Insights / Prometheus dashboards for CoreDNS latency, AWS VPC CNI IP pool exhaustion, and API server request latencies.
</details>

#### 【 SECURITY 】

<details>
<summary><strong>↳ Follow-up: How did you integrate Trivy into your CI/CD pipelines? What were the steps involved?</strong></summary>

**Answer:**
We integrated Trivy into our pipelines as a containerized security gate right after the Docker build stage:

### Step-by-Step Integration:
1. **Standardized Shared Library Step:**
   We authored a reusable function `runTrivyScan(imageName)` in our Jenkins Shared Library.
2. **Execution via Ephemeral Container Agent:**
   The scan executes inside a lightweight Trivy container running in the Jenkins build pod:
   ```groovy
   stage('Trivy Security Scan') {
       steps {
           container('trivy') {
               sh """
                   # 1. Generate human-readable table output for console
                   trivy image --severity HIGH,CRITICAL --format table ${IMAGE_NAME}:${IMAGE_TAG}
                   
                   # 2. Generate machine-readable JSON / JUnit report for artifact archiving
                   trivy image --format template --template '@/contrib/junit.tpl' \
                               --output trivy-report.xml ${IMAGE_NAME}:${IMAGE_TAG}
                   
                   # 3. Enforce blocking failure on CRITICAL fixable CVEs
                   trivy image --exit-code 1 --severity CRITICAL --ignore-unfixed ${IMAGE_NAME}:${IMAGE_TAG}
               """
           }
       }
       post {
           always {
               junit 'trivy-report.xml'
           }
       }
   }
   ```
3. **Persistent Cache Mounting:**
   Mounted an EFS/EBS persistent volume at `/root/.cache/trivy` to cache the vulnerability database across builds, reducing scan durations from 90 seconds to under 10 seconds.
</details>

<details>
<summary><strong>↳ Follow-up: Do you have a dedicated machine or VM for running Trivy scans?</strong></summary>

**Answer:**
**No, we do not maintain dedicated VMs for Trivy.** Maintaining static VMs for scanning creates idle resource waste and maintenance overhead. 

Instead, Trivy runs **ephemerally as a container step inside our dynamic Kubernetes build pod** on EKS. By mounting a shared cache directory (via Kubernetes Persistent Volume Claim or local hostPath), Trivy caches its vulnerability database locally, enabling fast, isolated, multi-threaded scans that scale horizontally with our build volume.
</details>

<details>
<summary><strong>↳ Follow-up: When the Trivy scan stage runs right after the Docker build, what happens on the backend/DevOps side? How do you initialize the Trivy scan, and what do the resulting logs look like?</strong></summary>

**Answer:**
### What Happens on the Backend:
1. **DB Sync:** Trivy checks its local database cache (`metadata.json`). If older than 12 hours, it downloads incremental differential updates from GitHub container registry (`ghcr.io/aquasecurity/trivy-db`).
2. **Image Layer Unpacking & Static Analysis:** Trivy analyzes the local Docker daemon image tarball. It walks through each filesystem layer, extracting OS package metadata (`dpkg`, `rpm`, `apk`) and application dependency lockfiles (`pom.xml`, `package-lock.json`, `Pipfile.lock`).
3. **Vulnerability Correlation:** It queries the local DB for matching CVE IDs, CVSS scores, and fixed package versions.
4. **Policy Evaluation:** If `--exit-code 1` is specified and matching vulnerabilities are found, Trivy terminates with exit code 1, causing Jenkins to immediately fail the stage.

### What the Resulting Logs Look Like:
```
2026-08-05T00:45:12.124Z  INFO  Need to update DB
2026-08-05T00:45:14.301Z  INFO  Vulnerability DB update was successful
2026-08-05T00:45:15.892Z  INFO  Detecting Alpine vulnerabilities...
2026-08-05T00:45:16.104Z  INFO  Number of language-specific files: 1
2026-08-05T00:45:16.105Z  INFO  Detecting jar-pom-properties vulnerabilities...

payment-service:build-142-a7f9b3c (alpine 3.19.1)
=================================================
Total: 2 (HIGH: 1, CRITICAL: 1)

┌──────────────┬────────────────┬──────────┬──────────────┬───────────────────┬──────────────────────────────────────────┐
│   Library    │ Vulnerability  │ Severity │ Status       │ Installed Version │ Fixed Version                            │
├──────────────┼────────────────┼──────────┼──────────────┼───────────────────┼──────────────────────────────────────────┤
│ openssl      │ CVE-2024-XXXXX │ CRITICAL │ fixed        │ 3.1.4-r1          │ 3.1.4-r2                                 │
│ libcrypto3   │ CVE-2024-YYYYY │ HIGH     │ fixed        │ 3.1.4-r1          │ 3.1.4-r2                                 │
└──────────────┴────────────────┴──────────┴──────────────┴───────────────────┴──────────────────────────────────────────┘

ERROR: Trivy found 1 CRITICAL vulnerability! Pipeline aborted.
script returned exit code 1
```
</details>

<details>
<summary><strong>↳ Follow-up: What types of vulnerabilities does Trivy report when scanning your images?</strong></summary>

**Answer:**
Trivy provides comprehensive vulnerability and posture detection across four primary categories:

1. **OS Package Vulnerabilities:** Known CVEs in underlying base image operating system packages (e.g., vulnerabilities in `glibc`, `openssl`, `busybox`, `curl`, `ca-certificates`).
2. **Language-Specific Application Dependencies:** CVEs in application libraries across ecosystems:
   - Java (`pom.xml`, `build.gradle` - e.g., Log4Shell, Jackson deserialization bugs)
   - Python (`requirements.txt`, `Pipfile.lock`)
   - Node.js (`package-lock.json`, `yarn.lock`)
   - Go (`go.mod`)
3. **Container Misconfigurations:** Scans Dockerfiles and Kubernetes manifests for security anti-patterns:
   - Running container as `root` user (`UID 0`)
   - Container missing memory or CPU resource limits
   - Privileged mode execution (`privileged: true`)
   - Missing health checks or writable root filesystems
4. **Exposed Secrets & Sensitive Data:** Detects accidentally committed private keys, AWS access keys, GitHub personal access tokens, or database passwords embedded in image layers.
</details>

<details>
<summary><strong>↳ Follow-up: If Trivy is only being used to catch a single type of issue, why would you want a full organization-level integration of this scanning tool?</strong></summary>

**Answer:**
Trivy is **not a single-purpose tool**—it is a unified security scanner. Implementing it across the entire organization achieves critical business and security objectives:

1. **True Shift-Left Security:** Catching CVEs and misconfigurations during developer CI builds costs 10x less time and effort than remediating vulnerabilities discovered by security audits in production.
2. **Regulatory & Compliance Mandates:** Meeting strict regulatory standards (**SOC 2 Type II, HIPAA, PCI-DSS 4.0, ISO 27001**) that legally mandate continuous automated vulnerability scanning of all containerized assets.
3. **Software Supply Chain Security:** Generates comprehensive Software Bill of Materials (**SBOM**) in CycloneDX or SPDX formats to track third-party library lineage.
4. **Consistent Security Baseline:** Prevents individual engineering teams from bypassing security standards by enforcing uniform, automated guardrails across all pipelines.
</details>

<details>
<summary><strong>↳ Follow-up: Does every microservice's CI/CD pipeline include a Trivy vulnerability scan stage?</strong></summary>

**Answer:**
**Yes.** Every single microservice pipeline enforces a mandatory Trivy vulnerability scan stage. Because our CI/CD pipelines are authored through a centralized Jenkins Shared Library, the Trivy scanning stage is automatically inherited and cannot be commented out or bypassed by individual application developers.
</details>

<details>
<summary><strong>↳ Follow-up: Does every microservice image have to pass through the Trivy scan before it is pushed to the artifact registry?</strong></summary>

**Answer:**
**Yes.** The Trivy scan is an absolute prerequisite gating step. The Docker image is built on the local agent filesystem and scanned immediately. Only if Trivy exits with code `0` (zero blocking vulnerabilities) does the pipeline advance to the `docker push` stage. If Trivy finds blocking vulnerabilities, the image is discarded locally and never reaches Amazon ECR.
</details>

<details>
<summary><strong>↳ Follow-up: Can you clarify exactly what kind of scan Trivy performs \- does it only check whether the container is running as a root user?</strong></summary>

**Answer:**
No, checking for root user is merely **one sub-check** within Trivy's broader misconfiguration detection suite. Trivy's primary function is deep static analysis across:
- **CVE Database Matching:** Querying over 10 global CVE advisories (NVD, Red Hat, Debian, GitHub Advisory Database) for all OS and application packages.
- **Deep Software Dependency Traversal:** Inspecting nested sub-dependencies (transitive dependencies) in Java, Python, and Node.js.
- **Secrets Detection:** Scanning all image layers for exposed API tokens, private SSH keys, and credentials.
- **Dockerfile & IaC Misconfiguration:** Checking CIS Docker Benchmark controls (including non-root user, read-only root filesystems, and health check instructions).
</details>

<details>
<summary><strong>↳ Follow-up: If Trivy finds vulnerabilities, do you stop the pipeline at that stage, or does it proceed further?</strong></summary>

**Answer:**
Our pipeline follows a **strict, risk-tiered gating policy**:

1. **Critical Vulnerabilities with an Available Fix (`--exit-code 1 --severity CRITICAL --ignore-unfixed`):**
   - **Immediately STOP the pipeline.** The build fails, deployment is blocked, and the image is never pushed to ECR.
2. **High Severity Vulnerabilities:**
   - In production release branches (`main`), **High** severity vulnerabilities with available fixes also block the pipeline.
   - In development branches, High severity generates a warning and logs an automated ticket in Jira for developer remediation within a 14-day SLA.
3. **Medium / Low / Unfixed Vulnerabilities:**
   - The pipeline **proceeds**. The vulnerabilities are aggregated into the daily security posture dashboard. Unfixed zero-day vulnerabilities (where upstream maintainers have not released a patch) are tracked by SecOps with compensating controls (WAF rules or network policies) rather than needlessly blocking developer delivery.
</details>

<details>
<summary><strong>↳ Follow-up: Does Trivy's log output show the categorization of vulnerabilities as critical or high severity?</strong></summary>

**Answer:**
**Yes, clearly and prominently.** Trivy generates a structured summary table that categorizes every detected issue by severity:
- It lists total counts at the top: `Total: 5 (UNKNOWN: 0, LOW: 1, MEDIUM: 2, HIGH: 1, CRITICAL: 1)`.
- In the table columns, each finding displays: `Library`, `Vulnerability ID` (e.g., CVE-2024-XXXX), **`Severity`** (color-coded red for CRITICAL, orange for HIGH, yellow for MEDIUM), `Installed Version`, and `Fixed Version`.
</details>

<details>
<summary><strong>↳ Follow-up: Do you know how Trivy categorizes/prioritizes vulnerabilities into severity levels such as critical or high?</strong></summary>

**Answer:**
Trivy assigns severity levels based on the **Common Vulnerability Scoring System (CVSS)** scores provided by authoritative security databases:

1. **Primary Source (Vendor Security Advisories):**
   - Trivy prioritizes official OS distribution advisories (e.g., Red Hat Security Advisories, Debian Security Tracker, Ubuntu CVE Tracker, Alpine SecDB) because vendors often backport patches or assess real exploitability differently than generic NVD scores.
2. **Secondary Source (NVD / CVSS v3.x Vector):**
   - When vendor-specific severity is absent, Trivy maps the CVSS v3 base score:
     - **CRITICAL:** CVSS Base Score **9.0 - 10.0** (remotely exploitable, zero privileges required, total compromise).
     - **HIGH:** CVSS Base Score **7.0 - 8.9** (significant impact, may require user interaction or privileges).
     - **MEDIUM:** CVSS Base Score **4.0 - 6.9** (limited impact or high attack complexity).
     - **LOW:** CVSS Base Score **0.1 - 3.9** (minimal impact, local access required).
</details>

<details>
<summary><strong>↳ Follow-up: Do you recall the specific predefined or custom rules you configured for prioritizing vulnerability severity in Trivy?</strong></summary>

**Answer:**
Yes, we configured Trivy using a centralized configuration file (`trivy.yaml`) and command-line flags:

1. **Filter Unfixed Vulnerabilities (`--ignore-unfixed`):**
   - Prevents blocking pipelines on CVEs where OS maintainers have not yet released a patch, avoiding developer friction.
2. **Threshold-Based Gating:**
   - `--severity CRITICAL,HIGH` combined with `--exit-code 1` ensures only actionable, severe risks fail the build.
3. **The `.trivyignore` Exception File:**
   - For audited, false-positive, or accepted-risk vulnerabilities approved by the Security Architecture Review Board, we add the CVE ID to `.trivyignore` accompanied by an expiration date and ticket reference:
     ```
     # JIRA-4521: Accepted transient risk in test utility, patch pending upstream
     CVE-2023-99999 exp:2026-09-01
     ```
4. **Custom Rego Policies for Container Hardening:**
   - Custom Open Policy Agent (OPA/Rego) rules checking that container images explicitly set `USER nonroot` and do not expose insecure ports (e.g., SSH port 22 or Telnet 23).
</details>

#### 【 BEHAVIORAL 】

<details>
<summary><strong>● Can you walk me through how your typical workday starts as a DevOps engineer?</strong></summary>

**Answer:**
My typical workday as a senior platform/DevOps engineer starts with a disciplined operational routine to ensure platform stability and developer velocity:

1. **08:30 – 09:00: Production Health & Incident Triage:**
   - Review PagerDuty / Slack `#prod-alerts` channel for overnight incidents, automated canary rollbacks, or threshold warnings.
   - Inspect primary **Grafana & CloudWatch Dashboards**: verify cluster CPU/memory saturation, HTTP 5xx error rates, API gateway latency (p95/p99), and database connection pool health across all production regions.
   - Check nightly backup completion logs (Velero cluster state, AWS RDS automated snapshots).
2. **09:00 – 09:30: CI/CD Health & Platform Queue Review:**
   - Check Jenkins and GitHub Actions runner pools: verify that build queues are clear, no ephemeral agents are stuck in `Pending` or `CrashLoopBackOff`, and master pipelines are green.
3. **09:30 – 10:00: Platform Standup & Cross-Functional Alignment:**
   - Attend the daily platform engineering standup to discuss sprint deliverables (e.g., Karpenter migration, Terraform module refactoring, cluster upgrades) and identify developer blockers.
4. **10:00 Onwards: Deep Engineering Work & Developer Enablement:**
   - Focus on Infrastructure as Code (Terraform), pipeline optimizations, security hardening, and reviewing PRs submitted by product teams for shared Helm charts and infrastructure modules.
</details>

<details>
<summary><strong>↳ Follow-up: As a platform team member, why would you be concerned about deployments made by the engineering team? Is monitoring their deployments part of your job responsibilities?</strong></summary>

**Answer:**
Yes, absolutely. In a modern **Platform Engineering & Shared Responsibility Model**, while application engineering teams own their functional business logic, the platform team owns the **foundational runtime stability, blast radius containment, and shared infrastructure availability**:

1. **Shared Cluster Resource Protection (Blast Radius):**
   - Microservices run in a multi-tenant EKS cluster. If an application team rolls out an un-profiled release with a memory leak or missing CPU requests, it can trigger node OOM cascades, evict neighboring microservices, exhaust subnet IP addresses, or saturate database connection pools.
2. **Validating Automated Guardrails:**
   - As platform engineers, we monitor deployments to verify that our automated safety mechanisms—such as **PodDisruptionBudgets (PDBs)**, Horizontal Pod Autoscalers (HPA), and Argo Rollouts canary health checks—trigger correctly during real-world production traffic shifts.
3. **Error Budgets & SLO Governance:**
   - We track deployment frequency and failure rates (DORA metrics) to ensure product deployments do not burn shared platform error budgets or violate organizational SLAs.
</details>

<details>
<summary><strong>↳ Follow-up: How many engineering teams does your DevOps team support \- i.e., how many teams are you providing CI/CD pipelines for?</strong></summary>

**Answer:**
Our platform engineering team consists of **5 engineers**, and we support **12 product engineering squads** comprising approximately **120 developers** across **45 microservices**.

### How We Scale Without Becoming a Bottleneck:
- **Self-Service Internal Developer Platform (IDP):** We do not manually write or maintain individual pipelines for each team via support tickets. Instead, we build **standardized "Golden Paths"**.
- We maintain centralized, modular **Jenkins Shared Libraries** and **reusable Terraform modules**. When a new team spins up a microservice, they consume a cookiecutter template that comes pre-wired with CI/CD, Trivy scanning, SonarQube quality gates, Helm charts, and Argo CD GitOps definitions.
- This allows our 5-person team to maintain high security, compliance, and reliability standards across 12 product teams without being on the critical path of daily feature delivery.
</details>
</details>

</details>

<details open>
<summary><h2>🏢 Investcloud</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 05-08-2026 06:13 AM*

#### 【 LINUX 】

<details>
<summary><strong>● What scripting and automation skills do you have (e.g., Python, Go, Bash), for what purposes have you used them, and how would you rate your proficiency on a scale of 1 to 10?</strong></summary>

**Answer:**
I work primarily with **Bash** and **Python** for systems engineering, cloud automation, and pipeline orchestration:

- **Bash Scripting (8.5/10):** Daily production driver for Linux systems administration, container entrypoints, systemd automation, log rotation, and CI/CD pipeline automation. Adheres strictly to defensive scripting patterns (`set -euo pipefail`, signal traps, and exit code propagation).
- **Python (7.5/10):** Used for complex API interactions, AWS SDK automation via **`boto3`** (e.g., automated EBS snapshot lifecycles, orphaned resource detection, EKS node drainage), and manipulating structured data (JSON/YAML) in CI/CD pipelines.
- **Go (Conceptual / Intermediate 5/10):** Reading and modifying Kubernetes controllers, Helm plugins, and writing basic CLI tools using the Kubernetes `client-go` library.
</details>

<details>
<summary><strong>↳ Follow-up: Given you rate yourself 5-6 out of 10 in scripting, what exactly do you do in practice \- do you write scripts yourself or rely on GUI tools?</strong></summary>

**Answer:**
In production DevOps, **I never rely on GUI tools** for operational tasks because GUIs introduce manual human error, lack auditability, and cannot be version-controlled. 

In practice:
1. **Self-Authored Automation:** I write all operational and automation scripts directly from scratch using standard IDEs (VS Code / Neovim) following modular coding principles.
2. **Standard Libraries & CLI Tools:** I leverage purpose-built CLI utilities (e.g., `jq`, `yq`, `awk`, `sed`, `curl`, `envsubst`) rather than overengineering complex scripts when standard Unix pipelines achieve the goal with higher reliability and zero external dependencies.
3. **Version Control:** 100% of automation scripts are maintained in Git, linted with `shellcheck` or `flake8`, and peer-reviewed through Pull Requests before being promoted into production.
</details>

<details>
<summary><strong>↳ Follow-up: Since scripting is often required in this role, how do you manage tasks that need scripting given your skill level?</strong></summary>

**Answer:**
I approach any scripting requirement through a structured, engineering-first methodology:

1. **Requirement Decomposition:** Break down the automation goal into discrete logical steps: Input parsing -> Validation -> Execution logic -> Error handling -> Output/Alerting.
2. **Leveraging Battle-Tested Modules & SDKs:** Rather than reinventing low-level networking or authentication protocols, I utilize robust, industry-standard SDKs like AWS `boto3` or Python `requests`.
3. **Defensive Coding & Testing:** Develop and test scripts in isolated lower environments (sandbox/development) with mock inputs, asserting proper handling of edge cases, API rate limits (exponential backoff), and timeouts.
4. **Documentation & Maintenance:** Include clear docstrings, command-line argument parsing (`argparse`), and structured logging (`INFO`, `WARNING`, `ERROR`) so that the script can be maintained by any platform team member.
</details>

<details>
<summary><strong>↳ Follow-up: If a requirement came up needing scripts for a complex task or data extraction, how would you manage it, and are you actively working to improve your scripting skills?</strong></summary>

**Answer:**
For complex scripting or large-scale data extraction tasks:
- **Design & Architecture:** I select Python as the optimal tool due to its rich ecosystem (`pandas` for structured tabular data, `csv`/`json` streaming modules for memory efficiency, and `concurrent.futures` for parallel API polling).
- **Chunking & Memory Optimization:** Implement generator-based chunking to process data in streaming batches, preventing memory exhaustion when extracting gigabytes of log or database records.
- **Active Improvement:** I continuously sharpen my skills by building custom Kubernetes operators in Go, solving algorithmic challenges on LeetCode/HackerRank, and studying open-source platform repositories (e.g., Karpenter and Prometheus Operator implementations).
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● Do you have experience working with Jenkins?</strong></summary>

**Answer:**
Yes, I have extensive experience operating Jenkins in enterprise production environments, managing distributed architectures where the Jenkins Controller schedules dynamic, ephemeral agent pods on AWS EKS via the Kubernetes plugin. I author modular declarative pipelines utilizing custom Jenkins Shared Libraries in Groovy, and integrate pipelines with SonarQube, Trivy, HashiCorp Vault, and AWS ECR.
</details>

<details>
<summary><strong>● If a client asked you to design a modern CI/CD pipeline for microservices with security and rollback capabilities built in, how would you approach it?</strong></summary>

**Answer:**
I would architect a modern **GitOps-driven, Shift-Left CI/CD Pipeline** combining **GitHub Actions / Jenkins (CI)** with **Argo CD & Argo Rollouts (CD)** on **AWS EKS**:

```
[ Developer PR ] ---> [ Automated CI Security Gate ]
                              |
       +----------------------+----------------------+
       |                      |                      |
[ SonarQube SAST ]     [ Trivy Container ]    [ Git Commit Check ]
(Coverage >= 80%)      (0 Critical CVEs)      (Signed Commits)
                              |
                              v (Pass)
                    [ Push to AWS ECR ]
                   (Immutable Image Tag)
                              |
                              v
             [ Git Commit to GitOps Manifests ]
                              |
                              v
+-------------------------------------------------------------+
| Argo CD & Argo Rollouts (On-Cluster GitOps Controller)      |
|                                                             |
| 1. Synchronizes desired state to EKS namespace              |
| 2. Initiates 10% Canary traffic split                       |
| 3. Prometheus Analysis evaluates 5xx rate and latency       |
| 4. Automatic Rollback if metrics breach error budget       |
+-------------------------------------------------------------+
```

### 1. Continuous Integration (CI) Security Gates
- **Static Analysis (SAST):** SonarQube quality gate halts the build if code coverage < 80% or any security vulnerability is found.
- **Secret Scanning:** Scans commits via Trufflehog / Gitleaks to prevent credential leakage.
- **Container Scanning:** Trivy runs on the built image; builds fail on fixable `CRITICAL` or `HIGH` CVEs.
- **Immutable Artifacts:** Images are pushed to ECR with strict tag immutability enabled.

### 2. Built-in Automated Rollback Capabilities
- **Automated Canary Analysis (Argo Rollouts):** Releases route 10% of traffic to the canary revision. A Prometheus `AnalysisTemplate` continuously checks:
  ```yaml
  metrics:
  - name: success-rate
    interval: 30s
    successCondition: result[0] >= 0.999
    provider:
      prometheus:
        address: http://prometheus-server.monitoring:9090
        query: sum(rate(http_requests_total{status!~"5.*"}[2m])) / sum(rate(http_requests_total[2m]))
  ```
  If the success rate drops below 99.9%, Argo Rollouts aborts the release within 30 seconds and restores 100% traffic to stable pods.
- **GitOps Rollback:** Reverting the Git commit in the manifests repository triggers Argo CD to immediately revert the cluster state.
</details>

<details>
<summary><strong>● Do you have experience using GitHub Actions?</strong></summary>

**Answer:**
Yes, I have designed and deployed enterprise GitHub Actions workflows:
- **Workflows as Code:** Configured multi-job workflows (`.github/workflows/*.yml`) utilizing matrix builds, branch protection rules, and environment secrets.
- **OIDC Cloud Federation:** Configured AWS IAM OpenID Connect (OIDC) federation, allowing GitHub Actions runners to assume short-lived AWS IAM roles dynamically without storing long-lived AWS Access Keys in repository secrets.
- **Self-Hosted Runners (ARC):** Deployed and scaled Actions Runner Controller (ARC) on AWS EKS to run workflows inside private corporate VPCs with access to internal artifact registries.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Do you have hands-on experience with Kubernetes?</strong></summary>

**Answer:**
Yes, I have over 5 years of daily hands-on experience managing Kubernetes clusters in production, primarily on **AWS EKS** as well as bare-metal on-premise clusters. My focus encompasses cluster provisioning via Terraform, ingress controller routing, cert-manager TLS automation, network segmentation via Calico, Karpenter autoscaling, and stateful storage with EBS/EFS CSI drivers.
</details>

<details>
<summary><strong>↳ Follow-up: Do you also have hands-on experience with Helm?</strong></summary>

**Answer:**
Yes, Helm is our primary packaging and templating tool for Kubernetes applications:
- **Custom Chart Architecture:** Authored reusable, generic corporate Helm charts used by 30+ Java/Node.js microservices.
- **Release Management:** Managing Helm deployments via CI/CD pipelines and declarative Argo CD Helm integrations (`Application` CRD with custom `valuesObject`).
- **Private OCI Registries:** Packaging, versioning (Semantic Versioning 2.0.0), and publishing Helm charts to Amazon ECR as OCI artifacts (`helm push mychart-1.2.0.tgz oci://<account>.dkr.ecr.us-east-1.amazonaws.com/helm`).
</details>

<details>
<summary><strong>● Can you give an example of a large Kubernetes deployment you designed and deployed, and explain how you used Helm in that scenario?</strong></summary>

**Answer:**
In our financial services platform, I architected the deployment of a **Real-Time Payment Processing & Fraud Evaluation Engine** running on AWS EKS:

- **Workload Scale:** 40+ microservices spanning over 350 pod replicas running across 25 EC2 instances (`m6i.4xlarge` and `c6i.4xlarge`) distributed across 3 Availability Zones.
- **How Helm Was Used:**
  - Designed an **Enterprise Base Helm Chart** (Library Chart) containing standardized configurations for Deployments, HorizontalPodAutoscalers, PodDisruptionBudgets, ServiceMonitors (Prometheus), and Istio VirtualServices.
  - Individual microservice charts inherited from this base chart. Each microservice repository contained only a lightweight `Chart.yaml` and environment-specific values files (`values-dev.yaml`, `values-qa.yaml`, `values-prod.yaml`).
  - Helm dynamically rendered environment-specific resource requests, database connection strings, replica counts, and ingress hosts, eliminating over 10,000 lines of duplicate raw Kubernetes YAML across teams.
</details>

<details>
<summary><strong>↳ Follow-up: Was this Kubernetes/Helm deployment a greenfield (brand new) deployment or built on top of existing infrastructure?</strong></summary>

**Answer:**
It was a **hybrid greenfield migration**:
- The **Kubernetes infrastructure was completely greenfield**: We provisioned brand-new AWS EKS clusters using modular Terraform code, setting up fresh VPCs, Karpenter autoscalers, Istio service mesh, and GitOps pipelines.
- The **backend application workloads were migrated** from legacy, static EC2 instance deployments. We containerized the applications using multi-stage Dockerfiles, decoupled external database connections, and deployed the refactored services onto the new EKS cluster using our Helm charts.
</details>

<details>
<summary><strong>↳ Follow-up: How many nodes were used in this Kubernetes cluster in production?</strong></summary>

**Answer:**
In production, our cluster operates on an **elastic node pool ranging from 20 to 45 EC2 instances**:
- **Baseline Load:** ~20 nodes running a mix of compute-optimized (`c6i.4xlarge`) and general-purpose (`m6i.2xlarge`) instances across 3 Availability Zones.
- **Peak / Burst Scaling:** Under high-volume market trading and end-of-day batch settlement processing, **Karpenter** dynamically scales the cluster up to 40–45 nodes in response to pending pod scheduling events and consolidates back down to baseline once jobs complete.
</details>

<details>
<summary><strong>↳ Follow-up: What was your specific role in this Kubernetes/Helm deployment project \- were you actively implementing it, or mostly observing others?</strong></summary>

**Answer:**
I was a **lead hands-on implementer and platform architect**:
1. Personally authored the Terraform modules provisioning the VPC, subnets, and EKS 1.29 cluster.
2. Authored the generic, enterprise-wide Helm chart templates and implemented the Argo CD GitOps pipelines.
3. Configured the AWS Load Balancer Controller, cert-manager, external-dns, and Prometheus Operator.
4. Partnered with the development leads to tune container resource requests/limits, configure liveness/readiness probes, and establish zero-downtime rolling update parameters.
</details>

<details>
<summary><strong>↳ Follow-up: What were the biggest operational challenges you faced with this or similar Kubernetes deployments when using Helm?</strong></summary>

**Answer:**
The three primary operational challenges were:

1. **State Drift & Out-of-Band Modifications:**
   - Developers or on-call engineers manually editing running workloads via `kubectl edit` or `kubectl patch` during incidents caused silent drift that Helm was blind to during subsequent releases.
   - **Solution:** Enforced strict GitOps using **Argo CD** with automated self-healing (`selfHeal: true`), overriding manual cluster changes and mandating that all updates be committed through Git.
2. **Chart Versioning & Dependency Hell:**
   - Managing shared sub-charts across 40 microservices created breaking changes when shared helper templates were updated.
   - **Solution:** Enforced strict Semantic Versioning (`MAJOR.MINOR.PATCH`) on Helm charts and hosted charts as version-locked OCI packages in Amazon ECR.
3. **CRD Lifecycle Management:**
   - Helm does not automatically upgrade Custom Resource Definitions (CRDs) placed in the `crds/` folder during `helm upgrade`.
   - **Solution:** Decoupled operator CRDs (Cert-Manager, Prometheus, Argo Rollouts) and managed them via dedicated Terraform steps or raw Kustomize manifests.
</details>

<details>
<summary><strong>↳ Follow-up: Can you elaborate further on the specific challenges you encountered while configuring Helm and integrating secrets into Kubernetes pods?</strong></summary>

**Answer:**
Integrating secrets securely without exposing sensitive credentials in plain-text Git repositories was a critical challenge:

### The Problem:
- Helm values files (`values.yaml`) are committed to Git. Storing raw API tokens or database passwords in `values.yaml` violates security compliance.
- Plain Kubernetes `Secret` manifests are merely Base64-encoded, not encrypted.

### The Production Solution:
We implemented **External Secrets Operator (ESO)** integrated with **AWS Secrets Manager**:
1. Sensitive values are stored and rotated inside AWS Secrets Manager encrypted with KMS.
2. The Helm chart defines an `ExternalSecret` custom resource referencing the remote AWS Secret:
   ```yaml
   apiVersion: external-secrets.io/v1beta1
   kind: ExternalSecret
   metadata:
     name: payment-db-secret
   spec:
     secretStoreRef:
       name: aws-secrets-manager
       kind: ClusterSecretStore
     target:
       name: payment-db-secret # Target Kubernetes Secret
     data:
     - secretKey: DB_PASSWORD
       remoteRef:
         key: prod/payment/database
         property: password
   ```
3. Pods mount the dynamically generated Kubernetes secret as environment variables via `secretKeyRef`.
4. Secret values never touch Helm templates, Git repositories, or CI/CD logs.
</details>

<details>
<summary><strong>↳ Follow-up: Did you work on handling Kubernetes failure modes?</strong></summary>

**Answer:**
Yes, architecting for failure is a foundational SRE and platform engineering responsibility. We engineered resilience against all standard failure modes:
- **Worker Node Termination / Spot Interruptions:** Configured the AWS Node Termination Handler and Karpenter disruption controllers to intercept AWS EC2 2-minute Spot interruption notices, gracefully cordoning and draining nodes.
- **Availability Zone Outages:** Pods are distributed evenly across 3 AZs using `topologySpreadConstraints`.
- **Application Crashing:** Configured fine-tuned `livenessProbe` and `readinessProbe` parameters to prevent sending traffic to uninitialized or failing containers.
- **Cascading Failures:** Configured **PodDisruptionBudgets (PDBs)** (`minAvailable: 75%`) ensuring rolling upgrades and node drains never drop pod capacity below operational thresholds.
</details>

<details>
<summary><strong>↳ Follow-up: Have you dealt with Kubernetes crash loop backoff errors and image pull failures?</strong></summary>

**Answer:**
Yes, these are two of the most frequent failure states encountered in Kubernetes operations:

- **CrashLoopBackOff:** Occurs when a container starts, executes, but repeatedly crashes and exits with a non-zero exit code. Kubernetes applies exponential backoff delays (10s, 20s, 40s... up to 5 mins) before restarting the container.
- **ImagePullBackOff:** Occurs when the kubelet on the worker node fails to download the container image from the registry after multiple attempts, entering an exponential backoff retry loop.
</details>

<details>
<summary><strong>↳ Follow-up: Specifically, did you encounter image pull failures in Kubernetes, and what caused them?</strong></summary>

**Answer:**
Yes, I have diagnosed and resolved image pull failures stemming from multiple root causes:

1. **ECR IAM Authentication Token Expiry / Missing IAM Role:**
   - **Cause:** Kubelet could not authenticate with Amazon ECR because the EC2 node IAM role was missing `ecr:GetAuthorizationToken` or the IRSA service account mapping was incorrect.
   - **Resolution:** Attached proper IAM permissions and verified AWS VPC CNI / EKS Pod Identity configuration.
2. **Missing Image Tag / Typo:**
   - **Cause:** A typo in the Helm values file (e.g., `payment-service:v1.2.0-bld14` instead of `bld142`), or the deployment triggered before the CI build finished pushing the image to ECR.
   - **Resolution:** Synced CI/CD pipeline ordering so GitOps manifests are only updated after `docker push` completes with verified exit code 0.
3. **Docker Hub Rate Limiting (HTTP 429 Too Many Requests):**
   - **Cause:** Public base images pulled without authentication exceeded Docker Hub's 100 pulls / 6 hours anonymous limit.
   - **Resolution:** Re-hosted all base images into private Amazon ECR repositories and configured `imagePullSecrets`.
4. **VPC Endpoint / Network Routing Issues:**
   - **Cause:** Nodes in strictly private subnets lacking NAT Gateway routing could not reach public ECR endpoints.
   - **Resolution:** Deployed **AWS PrivateLink VPC Endpoints** for ECR (`com.amazonaws.region.ecr.dkr` and `com.amazonaws.region.ecr.api`), keeping all image traffic inside the private AWS backbone.
</details>

#### 【 IAC 】

<details>
<summary><strong>↳ Follow-up: Do you use Terraform for provisioning your AWS and Azure infrastructure?</strong></summary>

**Answer:**
Yes, **Terraform** is our primary Infrastructure as Code (IaC) engine for multi-cloud provisioning:
- **AWS (Primary):** Provisioned VPCs, EKS clusters, RDS Aurora, ElastiCache, S3 buckets, Transit Gateways, and IAM roles using the AWS Provider.
- **Azure (Secondary / Disaster Recovery):** Provisioned Azure Resource Groups, Virtual Networks, Azure Key Vault, and Azure Kubernetes Service (AKS) using the `azurerm` provider.
- We structure Terraform configurations into reusable, modular blueprints versioned in Git.
</details>

<details>
<summary><strong>↳ Follow-up: Were the Terraform templates you used designed by you, or did you deploy templates designed by someone else?</strong></summary>

**Answer:**
I have personally designed, authored, and published production Terraform modules from scratch, while also incorporating well-tested open-source community modules (such as `terraform-aws-modules/vpc` and `terraform-aws-modules/eks`):
- For organizational standards, I built custom internal wrapper modules (e.g., `terraform-aws-secure-s3`, `terraform-aws-microservice-infra`) that embed our company's mandatory security guardrails (KMS encryption, private access, default tags, CloudWatch log export).
- I maintain our live environment configurations across Dev, QA, Staging, and Production.
</details>

<details>
<summary><strong>● How do you structure Terraform for managing multiple environments, including how you handle state, modules, secrets, and configuration drift?</strong></summary>

**Answer:**
We structure Terraform following enterprise modular principles to ensure isolation, security, and scalability:

### 1. Directory Structure (Terragrunt / Modular Approach)
We strictly separate environments by directory to isolate state files and limit blast radius:
```
terraform-infrastructure/
├── modules/                      # Reusable Child Modules
│   ├── networking/
│   ├── eks-cluster/
│   └── database/
└── environments/                 # Root Modules per Environment
    ├── dev/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── terraform.tfvars
    ├── staging/
    └── prod/
        ├── backend.tf
        ├── main.tf
        └── terraform.tfvars
```

### 2. State Management & Locking
- **Remote State in Amazon S3:** State files are stored in an encrypted private S3 bucket with versioning enabled.
- **State Locking via DynamoDB:** Prevents concurrent `terraform apply` operations from corrupting state.
- **Environment State Isolation:** Dev, Staging, and Prod have dedicated, isolated state keys (`env:/prod/eks.tfstate`).

### 3. Secrets Management
- **Zero Plain-Text Secrets in Code:** Passwords, private keys, and API tokens are never defined in `.tf` or `.tfvars` files.
- We retrieve secrets dynamically at runtime using Terraform data sources querying **AWS Secrets Manager** or **HashiCorp Vault**:
  ```hcl
  data "aws_secretsmanager_secret_version" "db_creds" {
    secret_id = "prod/aurora/credentials"
  }
  ```

### 4. Handling Configuration Drift
- **Automated Drift Detection Pipelines:** Scheduled nightly CI/CD jobs execute `terraform plan -detailed-exitcode`. If drift is detected (exit code 2), an alert is dispatched to the platform team.
- **Remediation:** Investigate whether the drift was a manual emergency fix (which must be backported into Terraform code) or unauthorized change (which is overwritten and reconciled by running `terraform apply`).
</details>

<details>
<summary><strong>↳ Follow-up: Do you build tagging standards and other conventions so that Terraform changes can be promoted safely through CI/CD?</strong></summary>

**Answer:**
Yes, standardizing tagging and resource conventions is essential for cost allocation, security compliance, and safe promotion:

1. **Mandatory Default Tags via AWS Provider:**
   ```hcl
   provider "aws" {
     region = var.aws_region
     default_tags {
       tags = {
         Environment        = var.environment
         ManagedBy          = "Terraform"
         Repository         = "github.com/company/infra-core"
         Owner              = var.team_owner
         CostCenter         = var.cost_center
         DataClassification = "Confidential-HIPAA"
       }
     }
   }
   ```
2. **Promotion via GitOps Pipelines:**
   - Terraform code moves through a Git branching model: Changes are applied to `dev` first upon PR creation, validated in `staging`, and require manual senior peer review and approval before `terraform apply` runs in `prod`.
   - Continuous compliance scanning runs **Checkov** or **Tfsec** on every pull request to enforce tagging and security benchmarks prior to merging.
</details>

<details>
<summary><strong>● Do you have experience using Ansible?</strong></summary>

**Answer:**
Yes, I have over 5 years of experience using Ansible for configuration management, OS provisioning, and server hardening:
- **Modular Ansible Roles:** Authored roles structured with `tasks/`, `handlers/`, `templates/` (Jinja2), and `vars/`.
- **CIS Security Baselining:** Created automated playbooks to harden Linux servers according to CIS Level 1 benchmarks (disabling legacy filesystems, configuring SSH key-only access, setting up auditd).
- **Dynamic Inventories:** Configured dynamic cloud inventory plugins (`aws_ec2`) to target EC2 instances automatically by tags (`tag:Role_Webserver`) without managing static IP lists.
- **Ansible Vault:** Encrypted sensitive variables and credentials within playbooks.
</details>

<details>
<summary><strong>● Have you ever designed a Terraform/infrastructure-as-code approach from scratch, starting from a requirement, rather than implementing an existing design?</strong></summary>

**Answer:**
Yes. When our organization initiated a cloud migration from an on-premise datacenter to AWS, I was tasked with designing the complete Infrastructure-as-Code architecture from scratch:
1. **Requirements Gathering:** Met with security, database, and application leads to identify network topologies (CIDRs, subnets, peering), high availability needs (Multi-AZ), and compliance mandates (HIPAA/PCI).
2. **Modular Architecture Design:** Designed a multi-tier Terraform module library following DRY principles: base VPC networking, shared security groups, IAM role policies, EKS cluster blueprints, and Aurora database modules.
3. **CI/CD Automation:** Built GitHub Actions workflows to automate `terraform fmt`, `tflint`, `checkov` security scanning, and automated plan execution with PR comments.
</details>

<details>
<summary><strong>↳ Follow-up: Can you give an example where you decided which infrastructure-as-code tools to use for a project?</strong></summary>

**Answer:**
During a project requiring infrastructure provisioning and configuration management across 300 EC2 instances and an EKS cluster, there was a debate on whether to use Ansible for everything or Terraform for everything.

**My Architectural Decision:**
- **Terraform for Infrastructure Provisioning (Immutable Infrastructure):** Provisioning cloud resources (VPCs, Subnets, Route Tables, EKS, RDS, Security Groups, IAM) is declarative and stateful. Terraform is the undisputed industry leader for lifecycle state management and dependency graph computation.
- **Ansible for Configuration Management & Golden Images:** Managing software inside virtual machines (configuring systemd services, installing agents, patching) is procedural configuration. I decided to use Ansible strictly as a provisioner inside **HashiCorp Packer** to bake immutable Golden AMIs, which Terraform then deployed.
- **Kubernetes / Helm for Containerized Applications:** Applications were packaged as Helm charts rather than using Ansible to deploy containers.

This tool separation eliminated configuration drift and maximized operational efficiency.
</details>

<details>
<summary><strong>↳ Follow-up: Before provisioning infrastructure, don't you need to strategize and develop a roadmap or plan based on the requirements \- have you done that kind of planning?</strong></summary>

**Answer:**
Yes, absolutely. Writing Terraform code without a structured architectural roadmap leads to costly redesigns and security vulnerabilities. My planning process involves four structured phases:

1. **Architectural Blueprint & RFC (Request for Comments):** Author a technical design document covering network topology (VPC CIDR allocation, public vs private subnets), security boundaries, and disaster recovery RTO/RPO targets.
2. **Security & Threat Modeling:** Review the design with SecOps to identify IAM boundaries, encryption requirements (KMS keys), and network ingress choke points.
3. **Cost Estimation (AWS Pricing Calculator / Infracost):** Model projected monthly compute, storage, and networking data transfer costs before provisioning.
4. **Phased Rollout Milestones:**
   - Phase 1: Foundational Networking & Security (VPC, IAM, Transit Gateway).
   - Phase 2: Core Platform Services (EKS, Aurora, Kafka).
   - Phase 3: CI/CD & Observability (Pipelines, Prometheus, CloudWatch).
   - Phase 4: Non-prod Validation -> Production Go-Live.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Do you have knowledge of or hands-on exposure to AWS?</strong></summary>

**Answer:**
Yes, I possess deep, comprehensive hands-on exposure to AWS across architectural design, CLI automation, and infrastructure operations. I manage large-scale multi-account environments orchestrated via AWS Organizations, implementing workloads across EKS, EC2, VPC, IAM, S3, RDS, CloudFront, Route 53, and CloudWatch.
</details>

<details>
<summary><strong>↳ Follow-up: Do you hold any AWS certifications?</strong></summary>

**Answer:**
Yes, I hold the **AWS Certified Solutions Architect – Associate** and the **AWS Certified DevOps Engineer – Professional** certifications, reflecting validated expertise in designing resilient, scalable, and automated cloud systems.
</details>

<details>
<summary><strong>↳ Follow-up: Aside from Terraform, do you have hands-on experience working directly with AWS through the console at an architectural/administrative level?</strong></summary>

**Answer:**
Yes. While Infrastructure as Code is the mandate for production deployments, I regularly use the **AWS Management Console and AWS CLI** for:
- Initial architectural exploration and rapid prototyping in sandbox accounts.
- Live incident triage, reviewing CloudWatch metrics, Container Insights, and CloudTrail event histories during production troubleshooting.
- Cost exploration via **AWS Cost Explorer** and AWS Compute Optimizer.
- Managing AWS Organizations, Service Control Policies (SCPs), and IAM Identity Center (SSO).
</details>

<details>
<summary><strong>● Which AWS services do you use most frequently?</strong></summary>

**Answer:**
My most frequently utilized services include:
1. **Compute & Orchestration:** **Amazon EKS**, **EC2**, and **AWS Lambda**.
2. **Networking & Security:** **Amazon VPC**, **AWS WAF**, **IAM (Roles, Policies, OIDC)**, **Route 53**, and **AWS KMS**.
3. **Storage & Databases:** **Amazon S3**, **Amazon EBS**, and **Amazon Aurora (PostgreSQL)**.
4. **Messaging & Caching:** **Amazon MSK (Kafka)**, **Amazon SQS**, and **Amazon ElastiCache (Redis)**.
5. **Observability:** **Amazon CloudWatch (Logs, Metrics, Alarms)** and **AWS CloudTrail**.
</details>

<details>
<summary><strong>↳ Follow-up: Have you worked with AWS IAM or network configuration?</strong></summary>

**Answer:**
Yes, extensively:
- **IAM:** Architected least-privilege permission models using IAM Roles for Service Accounts (**IRSA**) and **EKS Pod Identity**, configured cross-account role assumption with External IDs, authored strict Permission Boundaries, and managed Service Control Policies (SCPs).
- **Networking:** Designed multi-AZ VPC architectures with public, private, and database subnets, configured NAT Gateways, Internet Gateways, Route Tables, VPC Peering, Transit Gateways, and deployed **AWS PrivateLink VPC Endpoints** (Interface and Gateway endpoints) to keep intra-AWS traffic off the public internet.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● Do you have experience handling production incidents?</strong></summary>

**Answer:**
Yes, I have served as a primary on-call platform engineer on PagerDuty rotations for over 5 years. I have managed and resolved high-severity production incidents (Sev-1 and Sev-2) involving cluster-wide service outages, database failovers, network degradation, and high-traffic DDoS attacks.
</details>

<details>
<summary><strong>↳ Follow-up: In the event of a production incident, how would you detect it, triage it, restore service, and prevent recurrence?</strong></summary>

**Answer:**
I execute a disciplined SRE incident response lifecycle:

```
[ 1. Detection ] ---> [ 2. Triage & Containment ] ---> [ 3. Service Restoration ] ---> [ 4. Post-Mortem & Prevention ]
(Alarms / SLOs)       (Bridge / Isolate Blast)        (Rollback / Failover)            (Blameless Root Cause)
```

1. **Detection (0–2 mins):** Automated alerts via PagerDuty triggered by CloudWatch Alarms or Prometheus Alertmanager detecting breaches in Golden Signals (Latency, Traffic, Errors, Saturation).
2. **Triage & Incident Command (2–10 mins):**
   - Acknowledge alert, declare incident severity (e.g., Sev-1), and spin up a dedicated incident bridge (Zoom/Slack).
   - Check deployment history: Did a deployment or config change occur in the last 30 minutes?
   - Check infrastructure dashboards: Is the issue isolated to a specific microservice, database, or AWS Availability Zone?
3. **Restoration of Service (Mitigation First, Root Cause Second):**
   - **Rollback:** If triggered by a bad deployment, immediately execute an automated rollback (`kubectl rollout undo` / Argo CD Git revert).
   - **Scale:** If caused by unexpected traffic surges, scale out replicas or nodes.
   - **Traffic Reroute:** If an entire AZ or upstream third-party API is degraded, adjust Route 53 health checks or trigger circuit breakers.
4. **Post-Mortem & Prevent Recurrence:**
   - Conduct a blameless post-incident review with engineering leads.
   - Author a formal RCA document detailing timeline, root cause, and action items (adding missing alerts, implementing rate-limiting, fixing memory leaks).
</details>

<details>
<summary><strong>↳ Follow-up: Do you have hands-on experience using Prometheus, Grafana, and the EFK stack for monitoring?</strong></summary>

**Answer:**
Yes, this is our core observability stack:
- **Prometheus:** Deployed via **Kube-Prometheus-Stack**. Configured ServiceMonitors and PodMonitors to scrape application metrics, recorded custom PromQL rules, and configured Alertmanager routing.
- **Grafana:** Built centralized operational dashboards tracking RED (Rate, Errors, Duration) metrics, cluster node utilization, and business transaction throughput.
- **EFK / PLG Stack:** Experience deploying **Elasticsearch, FluentBit, and Kibana** (EFK) as well as **Prometheus, Loki, and Grafana** (PLG) for high-throughput, structured log aggregation and trace correlation.
</details>

<details>
<summary><strong>↳ Follow-up: Are you able to develop monitoring dashboards yourself using tools like Grafana?</strong></summary>

**Answer:**
Yes, I build production Grafana dashboards from scratch:
- Authored custom PromQL and LogQL queries using dynamic template variables (e.g., `$namespace`, `$service`, `$environment`) allowing seamless filtering.
- Visualized Golden Signals: P50/P95/P99 latency percentiles (`histogram_quantile`), request rates, error rates (5xx vs 4xx), JVM heap memory usage, and container CPU throttling.
- Packaged dashboards as **Dashboards-as-Code** (JSON in ConfigMaps) deployed automatically via Helm and GitOps.
</details>

<details>
<summary><strong>● Have you worked on Site Reliability Engineering (SRE) responsibilities such as monitoring, disaster recovery, and backups?</strong></summary>

**Answer:**
Yes, SRE principles are deeply embedded in my day-to-day role:
- **SLIs, SLOs, and Error Budgets:** Defined Service Level Objectives (e.g., 99.95% availability) and automated alerting tied to error budget burn rates rather than noisy static thresholds.
- **Disaster Recovery (DR):** Designed Active-Passive and Multi-Region DR architectures targeting RPO < 15 minutes and RTO < 30 minutes.
- **Automated Backups:** Automated daily backups of Kubernetes cluster state and persistent volumes using **Velero**, combined with AWS Backup policies for RDS Aurora and DynamoDB continuous point-in-time recovery (PITR).
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Have you ever proposed or worked on cloud/DevOps best practices, strategy, or architecture, including orchestration or service mesh implementations?</strong></summary>

**Answer:**
Yes. A key strategic contribution was proposing and leading the implementation of **Istio Service Mesh on our AWS EKS clusters**:

### Problem Before Implementation:
- Microservices communicated via plain HTTP inside the cluster, violating financial data compliance mandates.
- Developers struggled with managing circuit breakers, retries, and distributed tracing inside application code.

### Proposed Architecture & Solution:
1. **Zero-Trust Mutual TLS (mTLS):** Enforced strict peer authentication (`STRICT` mode), automatically encrypting 100% of east-west pod traffic with ephemeral TLS certificates rotated automatically by Istio Citadel.
2. **Traffic Management & Resilience:** Offloaded circuit breaking, request timeouts, and exponential retry logic from application code into Istio `VirtualService` and `DestinationRule` CRDs.
3. **Distributed Tracing:** Automated trace header propagation (B3/W3C) integrated with Jaeger, providing end-to-end distributed latency visibility across microservice call chains.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Have you seen the job description for this senior platform engineer role?

● **Candidate Introduction:** Are you currently working with Informatica?

● **Candidate Introduction:** You've been with Informatica since 2020 \- why are you looking to leave now?

↳ **Candidate Introduction:** At which organization did you write and provision these Terraform configurations?

● **Candidate Introduction:** Are you currently serving your notice period?

↳ **Candidate Introduction:** Have you already received a job offer from another company?

↳ **Candidate Introduction:** What is your remaining notice period at Informatica?

↳ **Candidate Introduction:** What is the exact date of your last working day?

↳ **Candidate Introduction:** Given your notice period is ending very soon, what is your plan regarding job offers?

● **Candidate Introduction:** Who do you typically interact with in your current role \- are there senior stakeholders or engineers you work with?

↳ **Candidate Introduction:** Is Informatica your end client rather than your direct employer?
</details>

<details open>
<summary><h3>Level 2</h3></summary>

*Date: 05-08-2026 09:55 AM*

#### 【 KUBERNETES 】

<details>
<summary><strong>● Do you have experience configuring auto-scaling on EKS clusters?</strong></summary>

**Answer:**
Yes, I have extensive production experience configuring end-to-end auto-scaling across both the **pod layer** and the **underlying infrastructure compute layer** on AWS EKS:

1. **Pod-Level Autoscaling (HPA & KEDA):**
   - Configured **Horizontal Pod Autoscalers (HPA)** targeting CPU/Memory utilization via Metrics Server.
   - Deployed **KEDA (Kubernetes Event-driven Autoscaling)** to scale microservices based on external cloud events, such as Amazon SQS queue depth, Kafka lag, or HTTP request rates.
2. **Node-Level Autoscaling (Karpenter):**
   - Migrated legacy Cluster Autoscaler implementations to **Karpenter**.
   - Karpenter observes unschedulable pod resource requirements and schedules right-sized EC2 Spot and On-Demand instances directly via AWS fleet APIs, cutting node provisioning times from 4 minutes to under 45 seconds while optimizing compute costs via automated node consolidation.
</details>

<details>
<summary><strong>↳ Follow-up: In a scenario where you have two node groups on a cluster (one CPU-optimized, one memory-optimized) and you need microservice A to only run on Node Group A and microservice B to only run on Node Group B, what Kubernetes configuration options would you use to define where each pod is scheduled?</strong></summary>

**Answer:**
To achieve strict, mutual workload isolation between Node Group A and Node Group B, the enterprise production standard requires combining **Node Affinity** with **Taints and Tolerations**:

```
[ Microservice A Pod ] ---> Tolerates 'workload=cpu:NoSchedule' + NodeAffinity 'workload=cpu'
                                        |
                                        v
                          +-----------------------------+
                          | Node Group A (CPU-Optimized)|
                          | - Taint: workload=cpu       |
                          | - Label: workload=cpu       |
                          +-----------------------------+

[ Microservice B Pod ] ---> Tolerates 'workload=mem:NoSchedule' + NodeAffinity 'workload=mem'
                                        |
                                        v
                          +-----------------------------+
                          | Node Group B (Mem-Optimized)|
                          | - Taint: workload=mem       |
                          | - Label: workload=mem       |
                          +-----------------------------+
```

### 1. Step 1: Label and Taint the Node Groups (via Terraform / Launch Template)
- **Node Group A (CPU):**
  - Label: `workload=cpu-optimized`
  - Taint: `workload=cpu-optimized:NoSchedule`
- **Node Group B (Memory):**
  - Label: `workload=memory-optimized`
  - Taint: `workload=memory-optimized:NoSchedule`

*Why Taints?* A taint repels any generic pod that does not explicitly tolerate it, ensuring generic microservices never accidentally schedule onto these specialized nodes.

### 2. Step 2: Configure Microservice A Pod Spec
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: microservice-a
spec:
  template:
    spec:
      # 1. Toleration allows pod to land on tainted Node Group A
      tolerations:
      - key: "workload"
        operator: "Equal"
        value: "cpu-optimized"
        effect: "NoSchedule"
      # 2. Affinity forces pod to ONLY land on Node Group A
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: workload
                operator: In
                values:
                - cpu-optimized
```

### 3. Step 3: Configure Microservice B Pod Spec
Follow the exact same pattern for Microservice B, specifying `value: "memory-optimized"` for both the toleration and the `nodeAffinity` match expression.

This dual configuration guarantees 100% strict isolation: Service A can never land on Node Group B, Service B can never land on Node Group A, and standard workloads are completely blocked from both.
</details>

<details>
<summary><strong>● What is your experience with configuring resource requests and limits in Kubernetes? Can you explain the different resource configuration options available for a pod?</strong></summary>

**Answer:**
Resource requests and limits are fundamental to cluster stability, bin-packing efficiency, and preventing "noisy neighbor" resource starvation:

### 1. Resource Requests vs. Limits
- **`requests` (Guaranteed Reservation):**
  - Used by the **kube-scheduler** during pod scheduling. The scheduler filters out any node whose remaining allocatable CPU or memory is less than the requested amount.
  - Once placed, requests guarantee that the pod has access to at least this baseline capacity.
- **`limits` (Enforced Hard Ceiling):**
  - Monitored and enforced at runtime by the container runtime via **Linux cgroups**:
    - **CPU Limit:** Enforced via the Linux CFS (Completely Fair Scheduler) quota. If a container exceeds its CPU limit, it is **throttled**, but never killed.
    - **Memory Limit:** Enforced strictly. If a container attempts to allocate memory beyond its limit, the Linux kernel terminates the process immediately with an **OOMKilled (Out of Memory - exit code 137)** error.

### 2. Quality of Service (QoS) Classes
Kubernetes automatically assigns one of three QoS classes based on how requests and limits are configured:
1. **Guaranteed (Highest Priority):**
   - Every container in the pod has `requests == limits` for both CPU and Memory.
   - Top-tier stability; these pods are the very last to be evicted during node resource pressure. Ideal for critical core databases and payment microservices.
2. **Burstable (Standard):**
   - Pod has requests and limits configured, but `requests < limits`.
   - Allows pods to burst into spare capacity during spikes. Evicted before Guaranteed pods if the node runs low on memory.
3. **BestEffort (Lowest Priority):**
   - Pod has zero requests and zero limits set.
   - First to be terminated and evicted when a node experiences memory pressure. Suitable only for non-critical development jobs or transient background batch tasks.
</details>

#### 【 IAC 】

<details>
<summary><strong>● How recently and how extensively have you been working with Ansible and Terraform?</strong></summary>

**Answer:**
I have worked extensively with both **Terraform** and **Ansible** on a daily basis for over 5 years, right up to my current production assignments:
- **Terraform:** Daily primary tool used to architect, provision, and maintain cloud infrastructure (VPCs, EKS 1.29 clusters, RDS Aurora, IAM policies, and S3). All infrastructure changes are codified into version-controlled modules and deployed through CI/CD pipelines.
- **Ansible:** Used for configuration management, OS security hardening (CIS Benchmarks), and building immutable Golden AMIs via HashiCorp Packer pipelines.
</details>

<details>
<summary><strong>↳ Follow-up: Are you familiar with the basic fundamental concepts of Ansible, such as inventories, playbooks, and roles? Can you explain them?</strong></summary>

**Answer:**
Yes, these form the foundational hierarchy of Ansible automation:

1. **Inventories:**
   - Define the target managed hosts and groupings (e.g., `[webservers]`, `[dbservers]`, `[production]`).
   - Can be **static** (INI/YAML file) or **dynamic** (plugins like `aws_ec2` querying cloud APIs in real-time).
2. **Playbooks:**
   - YAML files that declare the desired state and workflow.
   - Map host groups to specific lists of tasks (e.g., install packages, deploy configuration files, restart services) using Ansible modules (`ansible.builtin.yum`, `ansible.builtin.systemd`).
3. **Roles:**
   - The modular, reusable packaging format for playbooks following a standardized directory convention:
     ```
     roles/common/
     ├── tasks/      # Main list of tasks executed
     ├── handlers/   # Handlers triggered by notify (e.g., service restart)
     ├── templates/  # Jinja2 template configuration files
     ├── files/      # Static files copied to target
     ├── vars/       # High-priority role variables
     ├── defaults/   # Default low-priority variables
     └── meta/       # Role dependencies and author info
     ```
</details>

<details>
<summary><strong>↳ Follow-up: When working with dynamic inventories in Ansible, have you done that using Ansible Tower/AWX, or only via the CLI?</strong></summary>

**Answer:**
I have hands-on experience using both **Ansible CLI** and **Ansible Tower / AWX**:
- **Via CLI:** Configured the native `amazon.aws.aws_ec2` inventory plugin with YAML configuration files, integrating CLI runs directly into Jenkins CI/CD automation pipelines.
- **Via AWX / Tower:** Configured Dynamic Inventory Sources with AWS credentials stored as encrypted Machine Credentials, setting up automated inventory sync schedules, job templates, and role-based access controls for development teams.
</details>

<details>
<summary><strong>↳ Follow-up: When using a dynamic inventory in Ansible without Tower or AWX, how do you configure it to synchronize with and point at your AWS hosts?</strong></summary>

**Answer:**
Configuring dynamic inventory via the CLI without Tower/AWX involves three simple steps:

### 1. Enable the `amazon.aws.aws_ec2` Plugin in `ansible.cfg`
```ini
[defaults]
inventory = ./inventories/aws_ec2.yml

[inventory]
enable_plugins = amazon.aws.aws_ec2
```

### 2. Configure the Inventory Definition (`inventories/aws_ec2.yml`)
The file must end in `aws_ec2.yml` or `aws_ec2.yaml`:
```yaml
plugin: amazon.aws.aws_ec2
regions:
  - us-east-1
  - us-east-2

# Filter only running EC2 instances
filters:
  instance-state-name: running

# Group instances dynamically by AWS tags and VPC ID
keyed_groups:
  - key: tags.Environment
    prefix: env
  - key: tags.Role
    prefix: role

# Hostname preference: use private IP address inside VPC
hostnames:
  - private-ip-address

# Compose variables
compose:
  ansible_host: private_ip_address
```

### 3. Verify and Execute
```bash
# Verify inventory discovery graph
ansible-inventory -i inventories/aws_ec2.yml --graph

# Run playbook targeting the dynamic group
ansible-playbook -i inventories/aws_ec2.yml site.yml -l env_production
```
</details>

<details>
<summary><strong>↳ Follow-up: How do you manage the credentials needed for Ansible's dynamic inventory to authenticate with your cloud provider (AWS)?</strong></summary>

**Answer:**
We manage AWS credentials following standard AWS security best practices, strictly avoiding hardcoded access keys:

1. **IAM Roles (Best Practice):**
   - When running Ansible from an EC2 bastion, Jenkins agent, or runner, the host assumes an **EC2 IAM Instance Profile** or **EKS Pod Identity / IRSA role** granting `ec2:DescribeInstances` permissions. The `aws_ec2` plugin automatically discovers and uses these temporary STS credentials.
2. **Environment Variables via Secret Stores:**
   - In CI/CD pipelines, credentials are dynamically injected as masked environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) fetched at runtime from HashiCorp Vault or AWS Secrets Manager.
3. **AWS Named Profiles:**
   - For local developer execution, developers use `aws-vault` or IAM Identity Center SSO profiles (`~/.aws/config`), setting `AWS_PROFILE=prod-read` during playbook execution.
</details>

<details>
<summary><strong>● In Terraform, what is your idea of best practice when it comes to creating and consuming modules?</strong></summary>

**Answer:**
My architectural best practices for creating and consuming Terraform modules follow software engineering design principles:

### Best Practices for Creating Modules:
1. **Single Responsibility Principle (SRP):** A module should do one thing well (e.g., manage a VPC or an EKS cluster, not both in one massive module).
2. **Explicit Input Validation:** Use `validation` blocks with descriptive error messages inside `variables.tf`:
   ```hcl
   variable "environment" {
     type        = string
     description = "Deployment environment"
     validation {
       condition     = contains(["dev", "staging", "prod"], var.environment)
       error_message = "Environment must be one of: dev, staging, prod."
     }
   }
   ```
3. **Comprehensive Outputs:** Output resource IDs, ARNs, and security group IDs required by downstream modules, accompanied by clear descriptions.
4. **Avoid Embedded Providers:** Never declare `provider` blocks inside reusable child modules; providers must always be configured at the root caller module level.

### Best Practices for Consuming Modules:
1. **Pin Exact Semantic Versions:** Always pin the module source to a specific immutable tag (`?ref=v2.1.0`), never pointing to a branch like `main`.
2. **Limit Blast Radius:** Consume modules in isolated environment state files (`environments/dev`, `environments/prod`), preventing changes in non-prod from ever touching production state.
</details>

<details>
<summary><strong>↳ Follow-up: Where do you store your Terraform modules (the actual module code)?</strong></summary>

**Answer:**
We store our Terraform module source code in **dedicated, version-controlled Git repositories** within our enterprise GitHub organization (e.g., `github.com/org/terraform-aws-eks`):
- Each module has its own independent repository containing automated linting (`tflint`, `terraform fmt`), security scanning (`checkov`), documentation generators (`terraform-docs`), and integration tests (`terratest`).
- Modules are tagged with **Semantic Version tags** (e.g., `v1.0.0`, `v1.1.0`, `v2.0.0`).
- For higher-tier distribution, modules are published to an internal **Private Terraform Registry** (Terraform Cloud / Enterprise or GitLab Infrastructure Registry).
</details>

<details>
<summary><strong>↳ Follow-up: Suppose you and I built a Terraform module to create EKS clusters and used it to create 5 EKS clusters. If we now need to add a new plugin/change to that module, at a high level, how would you go about getting that change from concept into production?</strong></summary>

**Answer:**
I would execute a structured, non-breaking **Semantic Version Promotion Workflow**:

```
[ Concept / Feature Branch ] ---> [ Automated CI Testing (Terratest) ] ---> [ Merge to Main ]
                                                                                   |
                                                                                   v
[ Tag New SemVer: v2.1.0 ] <-------------------------------------------------------+
        |
        +---> [ Upgrade Sandbox / Dev Cluster to v2.1.0 ] ---> Validate Live
        |
        +---> [ Upgrade Staging Cluster to v2.1.0 ]      ---> Smoke Tests
        |
        +---> [ Production Promotion Approval ]           ---> Planned Maintenance Apply
```

1. **Branching & Implementation:** Create a feature branch (`feature/add-karpenter-plugin`) in the `terraform-aws-eks` module repo. Add the feature with backwards-compatible defaults (`enable_plugin = false` by default).
2. **Local & Automated Testing:** Spin up a temporary sandbox cluster using `terratest` to verify that the module compiles, provisions, and destroys cleanly.
3. **Code Review & Release Tagging:** Merge the PR into `main` and publish a new semantic version tag: **`v2.1.0`**.
4. **Zero Impact on Existing Clusters:** The 5 existing clusters remain pinned to `v2.0.0`. They continue running completely untouched with zero risk.
5. **Systematic Environment Promotion:**
   - Update Cluster 1 (Dev) to point to `ref=v2.1.0`. Run `terraform plan`, apply, and validate cluster stability.
   - Promote to Cluster 2 & 3 (QA and Staging).
   - Once validated, schedule a maintenance window, submit a change request, and promote Cluster 4 & 5 (Production).
</details>

<details>
<summary><strong>↳ Follow-up: Where is your Terraform source code stored (e.g., GitHub, GitLab)?</strong></summary>

**Answer:**
Our Terraform source code—both our reusable module repositories and our live environment orchestration repositories—is hosted on **GitHub Enterprise** with branch protection rules enforcing mandatory code reviews, signed commits, and passing CI status checks before any code can be merged.
</details>

<details>
<summary><strong>↳ Follow-up: If you needed to change a Terraform module stored in source control (e.g., an EKS module) without impacting the existing production clusters built from it, what would your workflow be? Would you use a feature branch, versioning, or tags to ensure safety?</strong></summary>

**Answer:**
I would use a combination of **Feature Branches AND Git Semantic Version Tags**:

1. **Feature Branch for Development:** All modifications occur on an isolated feature branch (`feature/upgrade-cni`). Developers test against isolated test states.
2. **Git Version Tags for Immutable Referencing:**
   - In Terraform, our production root modules reference the module via an explicit Git tag:
     ```hcl
     module "prod_eks" {
       source = "git::https://github.com/company/terraform-aws-eks.git?ref=v1.4.0"
       ...
     }
     ```
   - Because production is locked to `v1.4.0`, I can make changes, merge to `main`, and create `v1.5.0` without impacting production.
   - Even if `terraform apply` runs in production, Terraform will strictly evaluate the immutable `v1.4.0` ref. Production is completely insulated until an engineer explicitly edits `ref=v1.4.0` to `ref=v1.5.0` in the production repository.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Given the tools and platforms the team uses (GitLab CI/CD, Ansible, Terraform, Kubernetes, AWS, and VMware vSphere for self-hosted data centers), which of these do you have the least experience with?</strong></summary>

**Answer:**
Among that stack, I have the least experience with **VMware vSphere for self-hosted data centers**.

My core career trajectory has been focused on hyperscale cloud platforms (**AWS**) and cloud-native container orchestration (**Kubernetes**). While I have fundamental familiarity with virtualization concepts (ESXi hypervisors, vCenter management, VM templates, and using the Terraform `vsphere` provider for VM provisioning), my deepest, day-to-day production expertise lies in AWS, Terraform, Kubernetes, Ansible, and modern CI/CD automation. I am comfortable bridging any on-premise vSphere gap quickly due to my strong Linux systems and infrastructure-as-code foundation.
</details>

<details>
<summary><strong>↳ Follow-up: Can you give an example of something you've implemented in AWS that provides fault tolerance, and explain how the mechanism works?</strong></summary>

**Answer:**
A prime implementation is our **Multi-AZ Fault-Tolerant EKS & Amazon Aurora Architecture**:

```
                 [ Route 53 / AWS WAF ]
                           |
                           v
        [ Multi-AZ Application Load Balancer ]
        /                  |                 \
       v                   v                  v
+--------------+    +--------------+    +--------------+
|   AZ us-east-1a   |   AZ us-east-1b   |   AZ us-east-1c   |
| [ EKS Node ] |    | [ EKS Node ] |    | [ EKS Node ] |
|  (Pod Rep 1) |    |  (Pod Rep 2) |    |  (Pod Rep 3) |
+--------------+    +--------------+    +--------------+
        \                  |                  /
         v                 v                 v
+------------------------------------------------------+
| Amazon Aurora PostgreSQL (Multi-AZ Shared Storage)    |
| - Primary Writer (AZ-1a)                             |
| - Read Replica / Auto-Failover Target (AZ-1b)        |
| - 6-way storage replication across 3 AZs             |
+------------------------------------------------------+
```

### How the Fault Tolerance Mechanism Works:
1. **Compute Fault Tolerance:**
   - Pod replicas are distributed across 3 Availability Zones using `topologySpreadConstraints`:
     ```yaml
     topologySpreadConstraints:
     - maxSkew: 1
       topologyKey: topology.kubernetes.io/zone
       whenUnsatisfiable: DoNotSchedule
       labelSelector:
         matchLabels:
           app: payment-service
     ```
   - If an entire AWS Availability Zone experiences a catastrophic power outage or hardware failure, the ALB and Kubernetes immediately detect missing heartbeats.
   - Healthy pods in the remaining two AZs continue processing 100% of customer traffic. Karpenter automatically launches replacement nodes in the surviving zones.
2. **Database Fault Tolerance:**
   - Aurora automatically maintains 6 copies of data across 3 AZs.
   - If the primary database instance in AZ-a fails, Aurora detects the failure and promotes the Read Replica in AZ-b to primary writer within **under 30 seconds**. The Cluster DNS endpoint automatically updates to point to the new writer without requiring application restarts.
</details>

<details>
<summary><strong>↳ Follow-up: When you lose an availability zone and traffic shifts to another AZ, what mechanism inside the load balancer manages that failover, and how does it determine which AZ traffic goes to?</strong></summary>

**Answer:**
Failover across Availability Zones is orchestrated through two coordinated mechanisms: **Active Target Health Checks** and **Cross-Zone Load Balancing**:

```
[ Incoming Client Request ]
             |
             v
[ Route 53 DNS ] ---> Resolves to ALB IP nodes in all 3 AZs
             |
             v
+-------------------------------------------------------------+
| Application Load Balancer Nodes (Cross-Zone Enabled)       |
|                                                             |
| ALB Node AZ-a                ALB Node AZ-b                  |
| (Targets failed)             (Targets healthy)              |
|        \                            /                       |
|         \                          /                        |
+----------\------------------------/-------------------------+
            \                      /
             v                    v
      [ Healthy Targets in Surviving AZ-b and AZ-c ]
```

### 1. Active Target Health Checks:
- The ALB continuously dispatches HTTP/HTTPS probes (e.g., `GET /healthz`) to all registered target instances/pods at a configured interval (e.g., every 5 seconds).
- When AZ-a goes down, targets in AZ-a fail to respond. Once consecutive failed health checks reach the `UnhealthyThresholdCount` (e.g., 2 consecutive failures), the ALB marks all targets in AZ-a as **`Unhealthy`**.

### 2. Cross-Zone Load Balancing:
- With **Cross-Zone Load Balancing enabled**, each individual ALB node in any AZ distributes traffic evenly across **all healthy registered targets in all enabled Availability Zones**.
- When targets in AZ-a become `Unhealthy`, the ALB nodes immediately cease routing traffic to AZ-a targets and route 100% of requests to the remaining healthy targets in AZ-b and AZ-c.
- Even if DNS continues resolving to an ALB IP in AZ-a for a short duration, that ALB node in AZ-a proxies incoming requests directly to the healthy targets in AZ-b and AZ-c over the AWS internal network!
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● What makes a platform well-designed versus badly-designed? What factors do you consider when building new infrastructure/platforms?</strong></summary>

**Answer:**
A well-designed platform empowers application teams with velocity and autonomy while enforcing reliability, security, and cost control as invisible guardrails.

| Dimension | Well-Designed Platform | Badly-Designed Platform |
| :--- | :--- | :--- |
| **Team Topology & Workflow** | **Self-Service "Golden Paths"**: Developers deploy independently via standardized templates and automated GitOps pipelines. | **Ticket-Ops Bottleneck**: DevOps acts as a gatekeeper; developers submit Jira tickets for simple DB passwords, DNS records, or deployments. |
| **Infrastructure Management** | **100% Immutable Infrastructure as Code**: Everything codified in Terraform/Helm, versioned, and peer-reviewed. Zero snowflake servers. | **Manual ClickOps**: Resources created manually in the AWS Console. High configuration drift, unknown dependencies, and missing documentation. |
| **Failure & Resilience** | **Designed for Failure**: Multi-AZ by default, automated Canary rollouts, self-healing pods, circuit breakers, and tested DR playbooks. | **Fragile Single Points of Failure (SPOF)**: Single-AZ dependencies, manual rollback procedures, and long recovery times (high MTTR). |
| **Security Posture** | **Zero-Trust & Shift-Left**: Least privilege IAM (IRSA), automatic secret rotation, container scanning in CI, mTLS encryption in transit. | **Permissive & Hardcoded**: Long-lived access keys, plain-text secrets in Git repos, root containers, and open security groups (`0.0.0.0/0`). |
| **Observability** | **Golden Signals & Contextual Tracing**: Standardized Prometheus metrics, distributed tracing (Jaeger), structured JSON logging, and actionable alerts. | **Opaque & Alert-Fatigued**: No clear metrics, siloed text log files, thousands of noisy alerts ignored by engineers. |

### Core Factors I Consider When Building New Platforms:
1. **Developer Experience (DevEx):** Time-to-first-commit and deployment latency. Platforms must reduce cognitive load for software engineers.
2. **Blast Radius Minimization:** Strict tenant isolation, network microsegmentation, and fault-domain boundaries (multi-AZ/multi-region).
3. **Reproducibility & Idempotency:** Any environment (Dev, Staging, DR) must be fully rebuildable from code within an hour.
4. **FinOps & Cost Governance:** Resource tagging standards, automated rightsizing (Karpenter), and auto-stopping idle lower environments.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you tell me what you understand this role is looking for, based on the job description?

● **Candidate Introduction:** Do you have any questions for me about the role or the team?
</details>

</details>

<details open>
<summary><h2>🏢 Worklife Tech</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>
*Date: 05-08-2026 10:33 AM*

#### 【 GIT 】

<details>
<summary><strong>● Can you explain the Git branching strategy you use or have used in your projects?</strong></summary>

**Answer:**
In modern enterprise environments, branching strategies must strike a balance between deployment velocity, release stability, and code quality. In production cloud-native microservices, I primarily use **Trunk-Based Development** (supplemented with short-lived feature branches), while having extensive experience with **GitFlow** for legacy release-driven applications.

```
--- Trunk-Based Development with Short-Lived Feature Branches ---

main   ●───────●──────────●──────────● (Production Deployable)
        \     /          /          /
feature  ●───● (PR #101)/          /
                         \        /
feature                   ●──────● (PR #102)
```

##### 1. Trunk-Based Development (Preferred for CI/CD & Microservices)
* **Core Principle:** All developers merge small, frequent updates into a single central branch (`main` or `trunk`) at least once or twice daily.
* **Feature Branches:** Branches (`feature/PROJ-1234-auth-api`) are short-lived (typically living less than 24–48 hours) to prevent painful merge conflicts.
* **Feature Flags / Toggles:** Incomplete features are wrapped in runtime feature flags (e.g., LaunchDarkly, Unleash, or ConfigMaps), allowing code to be safely merged into `main` and deployed to production in a dormant state.
* **Release Branching:** When a major version milestone is required, a lightweight release branch (`release/v2.4.0`) is cut from `main`. Only critical cherry-picked hotfixes enter this branch, and fixes are merged back into `main`.

##### 2. GitFlow (For Scheduled Milestone / Regulated Releases)
* `main`: Reflects production-ready state; only updated via merges from `release` or `hotfix` branches with tagged versions.
* `develop`: Integration branch where all completed features gather for the next release.
* `feature/*`: Branched from `develop`, merged back to `develop` via pull requests.
* `release/*`: Branched from `develop` when preparing for a formal UAT/QA cycle. Only bug fixes and metadata updates occur here.
* `hotfix/*`: Branched directly from `main` to address critical production outages, then merged into both `main` and `develop`.

##### Branch Protection & Governance Standards
To enforce quality, our repository branches (`main`, `release/*`) enforce strict automated branch protection rules:
1. **Mandatory Peer Reviews:** Minimum of 2 approved code reviews, including at least one designated Code Owner (`CODEOWNERS`).
2. **Passing CI Status Checks:** Required green pipeline runs including unit tests, SonarQube quality gate (minimum 80% coverage, 0 critical security vulnerabilities), and Trivy container vulnerability scan.
3. **Linear History:** Squash and merge or rebase merge enforced to maintain a clean, bisectable commit history.
4. **Cryptographic Signing:** GPG-signed commits enforced to verify committer identity.
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● Can you explain the CI/CD automation setup you have worked with?</strong></summary>

**Answer:**
Our automated CI/CD ecosystem is designed around an end-to-end event-driven architecture connecting **GitHub Enterprise**, **Jenkins (running on AWS EKS)**, **SonarQube**, **HashiCorp Vault**, **AWS ECR**, and **ArgoCD (GitOps)** for Kubernetes delivery.

```
+----------+      Webhook       +---------------------+     Static Analysis     +------------+
|  GitHub  | -----------------> | Jenkins Pipeline on | ----------------------> | SonarQube  |
|  Repo    |                    | Kubernetes Agents   |                         +------------+
+----------+                    +---------------------+
                                     |               |
                       Docker Build  |               | Fetch Secrets
                             & Scan  v               v
                        +-------------+        +-------------+
                        | AWS ECR     |        | HashiCorp   |
                        | (Immutable) |        | Vault       |
                        +-------------+        +-------------+
                                     |
                       Update GitOps |
                                     v
                        +----------------------+
                        | GitOps Manifest Repo |
                        +----------------------+
                                     |
                       Reconciliation| Loop
                                     v
                        +----------------------+
                        | ArgoCD on AWS EKS    |
                        +----------------------+
```

##### 1. Continuous Integration (CI) Workflow
1. **Trigger:** A developer opens or updates a Pull Request against `main`. GitHub triggers a webhook to the Jenkins master.
2. **Dynamic Agent Provisioning:** Jenkins uses the Kubernetes Plugin to dynamically spawn an ephemeral pod agent on the EKS cluster containing isolated build containers (e.g., Maven/JDK 17, Docker CLI, Trivy).
3. **Code Quality & Security Gate:**
   * Unit and integration tests run with JUnit reporting.
   * SonarScanner sends static analysis metrics to SonarQube; if security hotspots, code smells, or coverage drop below thresholds, the build breaks immediately.
   * Dependency-Check / Snyk scans application libraries for known CVEs.
4. **Containerization & Image Security:**
   * A multi-stage Docker build produces a lean runtime image.
   * Trivy scans the local image filesystem for OS package and language-level vulnerabilities; images with `CRITICAL` or unpatched vulnerabilities are rejected.
5. **Publishing:**
   * Jenkins authenticates against AWS ECR using IRSA (IAM Roles for Service Accounts) and pushes the image tagged with both the Git SHA (`app:a1b2c3d`) and build number (`app:v1.2.0-b45`). Image tag immutability is strictly enforced in ECR.

##### 2. Continuous Delivery / Deployment (CD) Workflow
1. **GitOps Trigger:** Instead of Jenkins pushing directly to Kubernetes, the CI pipeline creates a PR or directly commits the new image tag into the GitOps deployment repository (`config/environments/prod/values.yaml`).
2. **ArgoCD Automated Sync:** The ArgoCD controller running inside EKS detects the state drift between the Git repository and the live cluster state.
3. **Deployment Strategies:**
   * **Canary Deployment (via Argo Rollouts):** 10% traffic routed to the new version for 15 minutes; automated analysis checks Prometheus metrics (HTTP 5xx rate < 0.5%, latency p99 < 200ms). If healthy, traffic steps up to 50%, then 100%.
   * **Automated Rollback:** If error rates spike during canary phases, Argo Rollouts aborts and rolls back immediately without manual intervention.
</details>

<details>
<summary><strong>● Can you write a Jenkins pipeline that builds the application, runs tests, builds a Docker image, pushes it to AWS ECR, and deploys it to an EKS cluster?</strong></summary>

**Answer:**
Below is a production-grade, declarative Jenkinsfile utilizing dynamic Kubernetes pod agents, multi-stage Docker builds, AWS IAM Roles for Service Accounts (IRSA) authentication, and zero-downtime deployment to Amazon EKS:

```groovy
pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins-agent: ci-cd-agent
spec:
  serviceAccountName: jenkins-agent-irsa-sa
  containers:
  - name: maven
    image: maven:3.9.6-eclipse-temurin-17
    command: ['cat']
    tty: true
  - name: docker
    image: docker:25.0-cli
    command: ['cat']
    tty: true
    volumeMounts:
    - mountPath: /var/run/docker.sock
      name: docker-sock
  - name: aws-kubectl
    image: amazon/aws-cli:2.15.15
    command: ['cat']
    tty: true
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
'''
        }
    }

    environment {
        AWS_REGION        = 'us-east-1'
        AWS_ACCOUNT_ID    = '123456789012'
        ECR_REPOSITORY    = 'worklife-order-service'
        EKS_CLUSTER_NAME  = 'worklife-prod-eks'
        KUBE_NAMESPACE    = 'production'
        DEPLOYMENT_NAME   = 'order-service'
        IMAGE_TAG         = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
        ECR_REGISTRY_URL  = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    }

    options {
        timeout(time: 45, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '30'))
        disableConcurrentBuilds()
        ansiColor('xterm')
    }

    stages {
        stage('Checkout Source') {
            steps {
                checkout scm
            }
        }

        stage('Compile & Test') {
            steps {
                container('maven') {
                    sh '''
                        echo "===> Running Unit Tests and Package..."
                        mvn clean package -DskipTests=false
                    '''
                }
            }
            post {
                always {
                    junit 'target/surefire-reports/*.xml'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                container('docker') {
                    sh '''
                        echo "===> Building Docker image: ${ECR_REGISTRY_URL}/${ECR_REPOSITORY}:${IMAGE_TAG}"
                        docker build \
                            --file Dockerfile \
                            --tag ${ECR_REGISTRY_URL}/${ECR_REPOSITORY}:${IMAGE_TAG} \
                            --tag ${ECR_REGISTRY_URL}/${ECR_REPOSITORY}:latest .
                    '''
                }
            }
        }

        stage('Push Image to AWS ECR') {
            steps {
                container('docker') {
                    sh '''
                        echo "===> Authenticating with Amazon ECR..."
                        # AWS credentials inherited transparently via IRSA
                        aws ecr get-login-password --region ${AWS_REGION} | \
                            docker login --username AWS --password-stdin ${ECR_REGISTRY_URL}

                        echo "===> Pushing image to ECR..."
                        docker push ${ECR_REGISTRY_URL}/${ECR_REPOSITORY}:${IMAGE_TAG}
                        docker push ${ECR_REGISTRY_URL}/${ECR_REPOSITORY}:latest
                    '''
                }
            }
        }

        stage('Deploy to Amazon EKS') {
            steps {
                container('aws-kubectl') {
                    sh '''
                        echo "===> Updating kubeconfig for EKS Cluster..."
                        aws eks update-kubeconfig --region ${AWS_REGION} --name ${EKS_CLUSTER_NAME}

                        echo "===> Applying rolling update to deployment..."
                        kubectl set image deployment/${DEPLOYMENT_NAME} \
                            ${DEPLOYMENT_NAME}=${ECR_REGISTRY_URL}/${ECR_REPOSITORY}:${IMAGE_TAG} \
                            --namespace ${KUBE_NAMESPACE}

                        echo "===> Monitoring rollout status..."
                        kubectl rollout status deployment/${DEPLOYMENT_NAME} \
                            --namespace ${KUBE_NAMESPACE} \
                            --timeout=300s
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "CI/CD Pipeline succeeded! Image ${IMAGE_TAG} successfully deployed to ${EKS_CLUSTER_NAME}."
        }
        failure {
            echo "Pipeline failed! Sending alert notification to team Slack channel..."
        }
        always {
            cleanWs deleteDirs: true, notFailBuild: true
        }
    }
}
```
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● If your CI/CD pipeline fails at the Docker image build stage with an 'insufficient space' error, how would you troubleshoot and resolve this issue?</strong></summary>

**Answer:**
An `insufficient space` or `no space left on device` error during `docker build` indicates that either the filesystem backing Docker's storage driver (`/var/lib/docker`) is full or the filesystem has exhausted its available **inodes**.

##### 1. Immediate Root Cause Identification (Live Troubleshooting)
Log into the CI runner host or node executing the Docker daemon:
1. **Verify Block Storage Usage:**
   ```bash
   df -h /var/lib/docker
   ```
   Checks if the volume has hit 100% capacity due to dangling images, stopped containers, build cache, or runaway container log files.
2. **Verify Inode Usage:**
   ```bash
   df -i /var/lib/docker
   ```
   Filesystem block space may be only 40% full, but running thousands of micro-builds (e.g., millions of tiny `node_modules` or `.git` files) can exhaust inodes completely.
3. **Inspect Docker Disk Consumption:**
   ```bash
   docker system df
   docker system df -v
   ```
   Provides a breakdown of space consumed by Active Containers, Images, Local Volumes, and Build Cache.

##### 2. Immediate Remediation (Restoring Pipeline Flow)
1. **Prune Dangling and Unused Objects:**
   ```bash
   # Remove all stopped containers, dangling images, unused networks, and build cache
   docker system prune -f

   # Deep clean: remove ALL unused images (not just dangling ones) and unused volumes
   docker system prune -a --volumes --force
   ```
2. **Clean BuildKit Cache:**
   ```bash
   docker builder prune -a --force
   ```
3. **Check and Truncate Leaking Container Logs:**
   ```bash
   find /var/lib/docker/containers/ -name "*-json.log" -size +1G -exec truncate -s 0 {} +
   ```

##### 3. Permanent Architectural Prevention
* **Automated Periodic Housekeeping:**
  Configure a systemd timer or cron job on persistent CI runners:
  ```bash
  # Run daily at 02:00 AM to remove images unreferenced for > 72 hours
  0 2 * * * /usr/bin/docker image prune -a --filter "until=72h" -f
  ```
* **Configure Docker Logging Limits:**
  Prevent runaway logs by configuring `/etc/docker/daemon.json`:
  ```json
  {
    "log-driver": "json-file",
    "log-opts": {
      "max-size": "50m",
      "max-file": "3"
    }
  }
  ```
* **Dedicated EBS Volume / LVM for Docker Data:**
  Mount a separate, dedicated high-performance disk directly to `/var/lib/docker` (or set `"data-root": "/mnt/docker-data"` in `daemon.json`) so Docker builds never consume the OS root filesystem (`/`).
* **Ephemeral Kubernetes CI Agents (Kaniko / Buildah):**
  Transition away from persistent Docker hosts sharing `/var/run/docker.sock`. Use daemonless build tools like **Kaniko** running inside isolated Kubernetes pods with ephemeral local volume storage that terminates and cleanly discards build scratch space upon completion.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● What AWS resources have you used in your projects, and for what purposes do you use each of them?</strong></summary>

**Answer:**
Across production cloud architectures, I utilize AWS services categorized by architectural layer:

| Domain | AWS Service | Production Purpose & Use Case |
| :--- | :--- | :--- |
| **Compute** | **Amazon EKS** | Managed Kubernetes cluster running containerized microservices across multi-AZ managed node groups. |
| | **AWS EC2** | Bastion hosts (jump boxes), custom GitLab/Jenkins persistent runners, and stateful database instances. |
| | **AWS Lambda** | Serverless automation (e.g., automated EBS snapshot cleanup, Slack alert forwarding from CloudWatch, S3 event triggers). |
| **Storage** | **Amazon S3** | Terraform remote state backend (with DynamoDB locking), centralized log archiving, application asset storage, and database backups. |
| | **Amazon EBS** | Persistent Block storage for EKS stateful workloads via EBS CSI Driver (`gp3` volumes with custom IOPS). |
| | **Amazon EFS** | Network-attached shared filesystem accessed concurrently by multiple Kubernetes pods across Availability Zones. |
| **Networking** | **Amazon VPC** | Isolated network topology with dedicated public, private (app), and secure data subnets across 3 AZs. |
| | **NAT Gateway** | Highly available outbound internet access for private subnet workloads without exposing them to inbound internet traffic. |
| | **Transit Gateway** | Centralized hub interconnecting multiple AWS accounts (Dev, Staging, Prod) and on-premises data centers via AWS Direct Connect / VPN. |
| | **VPC Endpoints (PrivateLink)** | Private routing to AWS services (S3, ECR, Secrets Manager) within the AWS backbone, bypassing the public internet and saving NAT Gateway data transfer costs. |
| **Routing & Edge** | **ALB / NLB** | Application Load Balancers for HTTP/HTTPS L7 traffic routing via AWS Load Balancer Controller; Network Load Balancers for L4 high-throughput TCP/UDP workloads. |
| | **Route 53 & CloudFront** | Global DNS management with latency/failover routing policies; CDN caching and SSL/TLS termination at edge locations. |
| **Database & Cache** | **Amazon RDS (PostgreSQL/Aurora)** | Multi-AZ relational databases with automated read replicas, automated snapshots, and KMS encryption. |
| | **Amazon ElastiCache (Redis)** | Distributed in-memory caching for session management and database query offloading. |
| | **Amazon MSK** | Managed Apache Kafka cluster for decoupled event-driven streaming pipelines between microservices. |
| **Security & IAM** | **AWS IAM & IRSA** | Fine-grained least-privilege access; IAM Roles for Service Accounts (IRSA) mapping AWS permissions directly to K8s service accounts via OIDC. |
| | **AWS KMS & Secrets Manager** | Customer Managed Keys (CMK) for envelope encryption of data at rest; rotation and automated injection of database passwords and API tokens. |
| | **AWS WAF** | Web Application Firewall attached to ALBs and CloudFront protecting against SQL injection, cross-site scripting (XSS), and DDoS attacks. |
| **Observability** | **Amazon CloudWatch** | Aggregation of container logs (Container Insights), system metrics, metric alarms, and synthetic canary probes. |
</details>

#### 【 SECURITY 】

<details>
<summary><strong>● How do you manage and secure secrets within Jenkins pipelines and Kubernetes environments?</strong></summary>

**Answer:**
Hardcoded credentials in repositories or plaintext environment variables represent severe security liabilities. We enforce centralized, dynamic secrets management across both CI and runtime environments.

##### 1. Securing Secrets in Jenkins Pipelines
* **Jenkins Internal Credentials Store:**
  Sensitive values (SSH private keys, API tokens) are saved inside Jenkins' encrypted credentials store protected by master encryption keys (`secrets.key`).
* **Credentials Binding:**
  Secrets are injected dynamically at runtime using the `withCredentials` wrapper, which automatically masks secret values in console logs with `****`:
  ```groovy
  withCredentials([usernamePassword(credentialsId: 'artifactory-creds', usernameVariable: 'ARTI_USER', passwordVariable: 'ARTI_PASS')]) {
      sh 'mvn deploy --settings <(echo "<settings><servers><server><id>repo</id><username>${ARTI_USER}</username><password>${ARTI_PASS}</password></server></servers></settings>")'
  }
  ```
* **HashiCorp Vault Integration:**
  For enterprise scalability, Jenkins pipelines authenticate to HashiCorp Vault via AppRole or AWS IAM authentication to retrieve short-lived, dynamic credentials with strict Time-To-Live (TTL).

##### 2. Securing Secrets in Kubernetes Environments
Native Kubernetes `Secret` resources are merely base64-encoded and stored unencrypted in `etcd` by default. To make them enterprise-ready, we implement three layers of security:

```
[ HashiCorp Vault / AWS Secrets Manager ]
                     |
                     | (Sync via External Secrets Operator)
                     v
          [ Kubernetes Native Secret ] (Encrypted in etcd via AWS KMS)
                     |
                     | (Mounted as in-memory tmpfs volume)
                     v
           [ Application Pod Container ]
```

1. **etcd KMS Encryption at Rest:**
   The Kubernetes API server is configured with an `EncryptionConfiguration` provider backed by **AWS KMS**, ensuring all secret resources written to `etcd` are strongly encrypted with envelope encryption.
2. **External Secrets Operator (ESO):**
   * Instead of manually creating K8s Secrets, developers declare `ExternalSecret` custom resources in Git.
   * ESO continuously pulls the actual values from **AWS Secrets Manager** or **HashiCorp Vault** and synchronizes them into local Kubernetes secrets.
3. **Secrets Store CSI Driver (Mount-Only without K8s Secrets):**
   * Pods mount secrets directly into their filesystem from AWS Secrets Manager using the CSI driver.
   * Secrets are mounted in an in-memory **`tmpfs`** volume inside the pod container. They never touch the node's physical disk and do not exist as Kubernetes Secret objects in `etcd`.
4. **Least Privilege RBAC & Service Accounts:**
   * Restrict access to Secret resources using Kubernetes RBAC rules (`verbs: ["get"], resources: ["secrets"]`).
   * Disable `automountServiceAccountToken: false` on pods that do not require communication with the Kubernetes API server.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself and give an overview of your professional background?
</details>

</details>

<details open>
<summary><h2>🏢 InvestCloud</h2></summary>

<details open>
<summary><h3>Level 3</h3></summary>
*Date: 05-08-2026 11:34 AM*

#### 【 LINUX 】

<details>
<summary><strong>● How comfortable are you with debugging general Windows and Linux operating system issues?</strong></summary>

**Answer:**
I have extensive, hands-on production experience diagnosing and resolving deep operating system issues, with **Linux (RHEL, CentOS/Rocky, Ubuntu, Alpine)** as my primary daily platform and strong operational familiarity with **Windows Server (2019/2022)**.

##### 1. Linux OS Troubleshooting Methodology (The USE Method)
When triaging system degradation or service outages, I utilize Brendan Gregg's **USE Method** (Utilization, Saturation, and Errors):
* **CPU & Load Average:**
  * Inspect system load averages using `uptime` or `top` against the number of CPU cores (`nproc`).
  * Run `vmstat 1 5` to identify context switching (`cs`), interrupts (`in`), and whether CPU time is spent in user (`us`), system (`sy`), or waiting on I/O (`wa`).
  * Run `pidstat -u 1` to isolate specific runaway processes or threads.
* **Memory & Out-of-Memory (OOM):**
  * Examine memory consumption: `free -m` (evaluating `available` memory rather than `free`, accounting for buffers/cache).
  * Check for OOM killer kernel events: `dmesg -T | grep -i oom` or `journalctl -k | grep -i "invoked oom-killer"`.
  * Analyze swap activity: `vmstat 1` inspecting `si` (swap in) and `so` (swap out).
* **Disk I/O & Filesystem:**
  * Run `iostat -xz 1` to check disk utilization (`%util`), average request wait time (`await`), and queue sizes.
  * Check disk space (`df -h`) and inode limits (`df -i`).
  * Investigate unreleased open deleted files: `lsof +L1` (processes holding open file descriptors on deleted files preventing disk reclamation).
* **Networking & Sockets:**
  * Verify listening sockets and port bindings: `ss -tulpn` or `netstat -plnt`.
  * Track socket states, TCP connection drops, and TIME_WAIT surges: `ss -s`.
  * Trace active network packets using `tcpdump -nnvv -i eth0 port 443` or test connectivity via `nc -zv <host> <port>` and `curl -Iv`.
* **System Tracing & Logs:**
  * Inspect service logs with `journalctl -u <service_name> -xe --no-pager`.
  * Trace system calls and file/network interactions on hung processes: `strace -p <PID> -f -T -e trace=network,file`.

##### 2. Windows Server Troubleshooting Methodology
* **Event Logging:** Inspect Windows Event Viewer logs (`Application`, `System`, and `Security`) using GUI or PowerShell:
  ```powershell
  Get-WinEvent -FilterHashtable @{LogName='System'; Level=2; StartTime=(Get-Date).AddHours(-2)}
  ```
* **Process & Resource Inspection:** Use Resource Monitor, Performance Monitor (PerfMon), and PowerShell to track CPU/memory consumers:
  ```powershell
  Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
  ```
* **Network & Service Validation:**
  ```powershell
  Test-NetConnection -ComputerName db.internal -Port 1433
  Get-Service -Name "W3SVC" | Restart-Service -Force
  ```
* **Advanced Diagnostics:** Utilize Microsoft Sysinternals tools (**Process Explorer** and **Process Monitor - ProcMon**) to inspect DLL dependencies, file lockouts, and registry access issues.
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● For your Java microservices, do you use a top-level base Docker image (e.g., a specific Java version) that all applications build from, or does each application build its container independently as part of the build pipeline?</strong></summary>

**Answer:**
In enterprise production environments, we enforce a **Standardized Enterprise Golden Base Image** strategy rather than letting individual applications build from arbitrary upstream public images.

```
+-------------------------------------------------------------------------+
|                  CENTRAL PLATFORM TEAM PIPELINE                         |
| Upstream Alpine/UBI -> Security Hardening -> CA Certs -> APM Agent      |
| -> Trivy Scan -> ECR: internal/base-images/eclipse-temurin:17-jre-alpine |
+-------------------------------------------------------------------------+
                                    |
                                    | (Enforced as Base Image)
                                    v
+-------------------------------------------------------------------------+
|                    APPLICATION CI/CD PIPELINE                           |
| Stage 1: Build JAR via Maven                                            |
| Stage 2: FROM internal/base-images/eclipse-temurin:17-jre-alpine        |
|          COPY --from=builder /app/target/service.jar /app/app.jar       |
+-------------------------------------------------------------------------+
```

##### Architectural Design: Golden Base Image vs Independent Builds

| Criteria | Enterprise Golden Base Image (Our Approach) | Independent Ad-Hoc Builds |
| :--- | :--- | :--- |
| **Security & Patching** | Centralized. When a vulnerability (e.g., OpenSSL or glibc CVE) occurs, we patch the golden image once, triggering automated downstream builds. | Fragmented. Every team uses different base versions, leading to hundreds of unpatched CVEs. |
| **Governance & Compliance** | Enforces internal root CA certificates, non-root system users (`USER appuser`), and security agents across all microservices. | High risk of running as `root` or lacking corporate CA trust stores. |
| **Standardized JVM Ergonomics** | Optimized JVM flags configured globally (e.g., `-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0`). | Applications miscalculate cgroup limits, causing frequent silent OOM kills. |
| **Build Speed & Caching** | Common layers are pre-pulled and cached across all cluster nodes and CI runners, speeding up CI builds significantly. | Redundant multi-megabyte layer downloads on every pipeline execution. |

##### How It Works in Practice
1. **The Base Image Pipeline:**
   The Platform team maintains a dedicated Git repository that produces hardened images:
   * Starts from a minimal base like Red Hat UBI Micro or `eclipse-temurin:17-jre-alpine`.
   * Strips package managers (`apk`, `apt`), curl, and compilers to minimize attack surface.
   * Adds the enterprise monitoring APM agent (e.g., OpenTelemetry / Datadog Java tracer).
   * Creates a dedicated non-root UID/GID (`65532:65532`).
   * Published to internal ECR: `internal-ecr.company.com/base/java17-jre:v1.2`.
2. **The Application Pipeline (Multi-Stage Dockerfile):**
   ```dockerfile
   # Stage 1: Build stage (isolated compilation)
   FROM maven:3.9.6-eclipse-temurin-17 AS builder
   WORKDIR /workspace
   COPY pom.xml .
   RUN mvn dependency:go-offline
   COPY src ./src
   RUN mvn clean package -DskipTests

   # Stage 2: Runtime stage (Golden Base Image)
   FROM internal-ecr.company.com/base/java17-jre:v1.2
   WORKDIR /app
   COPY --from=builder /workspace/target/*.jar /app/service.jar
   USER 65532:65532
   ENTRYPOINT ["java", "-XX:+UseContainerSupport", "-XX:MaxRAMPercentage=75.0", "-jar", "/app/service.jar"]
   ```
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● How familiar are you with Kubernetes administration, including both building clusters and providing day-to-day operational support for them?</strong></summary>

**Answer:**
I have end-to-end Kubernetes administration experience spanning both **Day 0 / Day 1 (Cluster Architecture & Provisioning)** and **Day 2 (Operational Maintenance, Upgrades, Scaling, & Disaster Recovery)** across Amazon EKS, Google GKE, and bare-metal/VMware clusters built using `kubeadm`.

##### 1. Cluster Provisioning & Infrastructure Architecture (Day 0 / Day 1)
* **Control Plane & Networking:**
  * Provisioning highly available, multi-AZ clusters using Terraform (`terraform-aws-modules/eks`).
  * Configuring CNI plugins: AWS VPC CNI (with prefix delegation for high pod density) and Calico for Kubernetes NetworkPolicy enforcement.
  * Ingress & Load Balancing: Deploying AWS Load Balancer Controller and NGINX Ingress Controller.
* **Storage & Addons:**
  * Provisioning dynamic storage using the AWS EBS CSI Driver and EFS CSI Driver with automated storage classes (`gp3` with custom IOPS).
  * Installing foundational platform addons via GitOps/Helm: CoreDNS, kube-proxy, Metrics Server, Cert-Manager, and ExternalDNS.

##### 2. Day-to-Day Operations & Maintenance (Day 2)
* **Zero-Downtime Cluster Upgrades:**
  * Executing Kubernetes version step upgrades (e.g., 1.28 -> 1.29 -> 1.30):
  * Upgrading the managed control plane via Terraform, verifying API deprecations using `pluto` or `kubent`.
  * Rolling upgrades of worker node groups: cordoning nodes (`kubectl cordon`), safely evicting pods respecting PodDisruptionBudgets (`kubectl drain --ignore-daemonsets --delete-emptydir-data`), and terminating old instances in the Auto Scaling Group.
* **Autoscaling Architecture:**
  * Implementing **Karpenter** alongside standard Cluster Autoscaler for rapid, cost-optimized node provisioning based on pending pod resource requests.
  * Configuring Horizontal Pod Autoscaler (HPA) using custom Prometheus metrics via the Prometheus Adapter.
* **Disaster Recovery & Cluster Backups:**
  * Utilizing **Velero** backed by Amazon S3 for scheduled backups of cluster state, persistent volumes, and custom resources, enabling complete cross-region cluster recovery.
* **Observability & Triage:**
  * Deep cluster monitoring with Prometheus Operator (kube-prometheus-stack), Grafana, and Loki/OpenSearch for log aggregation.
  * Resolving scheduling bottlenecks (`CrashLoopBackOff`, `OOMKilled`, `NodeNotReady`, `ImagePullBackOff`).
</details>

<details>
<summary><strong>↳ You mentioned using a shared Helm chart for your microservices—do you use a single generic Helm chart that all Java applications fit into, or does each microservice have its own dedicated Helm chart?</strong></summary>

**Answer:**
We utilize a **Single Shared Generic (Library / Blueprint) Helm Chart** maintained centrally by the platform team, rather than duplicating independent Helm charts across every microservice repository.

##### Why the Shared Generic Helm Chart Model Excels
In a microservices ecosystem with 40+ Java services, 90% of the Kubernetes manifests are identical: each service requires a `Deployment`, a `Service`, a `HorizontalPodAutoscaler`, a `PodDisruptionBudget`, an `Ingress`, and a `ServiceAccount` with IRSA annotations.

```
+---------------------------------------------------------------------+
|              CENTRAL PLATFORM HELM REPO (Chart Registry)            |
| "base-microservice-chart" (v2.1.0)                                  |
| - templates/deployment.yaml       - templates/hpa.yaml              |
| - templates/service.yaml          - templates/pdb.yaml              |
| - templates/ingress.yaml          - templates/serviceaccount.yaml   |
+---------------------------------------------------------------------+
             ^                                     ^
             | Pulls dependency                    | Pulls dependency
+---------------------------+       +---------------------------+
|    order-service REPO     |       |    payment-service REPO   |
| - Chart.yaml (v2.1.0)     |       | - Chart.yaml (v2.1.0)     |
| - values.yaml             |       | - values.yaml             |
|   (image, env, resources) |       |   (image, env, resources) |
+---------------------------+       +---------------------------+
```

##### 1. Structure of the Generic Chart
The shared chart exposes structured switches and values:
* **`values.yaml` in Application Repositories:**
  Developers maintain a lightweight `values.yaml` (typically under 40 lines) defining only application specifics:
  ```yaml
  nameOverride: order-service
  image:
    repository: 123456789012.dkr.ecr.us-east-1.amazonaws.com/order-service
    tag: v1.4.2
  service:
    port: 8080
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      memory: 1024Mi
  hpa:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
  env:
    - name: SPRING_PROFILES_ACTIVE
      value: "production"
  ```
* **Centralized Governance:**
  If the platform team needs to enforce security standards (e.g., adding `readOnlyRootFilesystem: true`, injecting standard Datadog labels, or adding mandatory anti-affinity rules), we update the base chart version once. Microservices pick up the new standards simply by bumping the chart dependency.

##### 2. Handling Outliers
When a microservice has unique architecture (e.g., requiring persistent volume mounts, complex statefulsets, or init-containers for database migrations), the shared chart provides extensible hooks (`extraVolumes`, `extraInitContainers`), or a dedicated standalone chart is created as an exception.
</details>

<details>
<summary><strong>↳ How does your deployment mechanism work in practice—when you have a new version to deploy via Helm, does Jenkins invoke Helm to talk directly to the Kubernetes API and apply the changes, or is there a more complex interaction involved?</strong></summary>

**Answer:**
While having Jenkins directly invoke `helm upgrade --install` is common in early-stage pipelines, in mature enterprise environments that approach creates significant security and operational risks. We transitioned from **Direct CI Push** to a **GitOps Pull Model using ArgoCD**.

##### Comparison of the Two Approaches

```
--- 1. Direct CI Push (Legacy / Basic) ---
[ Jenkins Runner ] ---> (Holds Admin Kubeconfig) ---> [ K8s API Server ] (helm upgrade)

--- 2. Enterprise GitOps Pull (Modern / Production) ---
[ Jenkins Runner ] ---> (Commits Tag) ---> [ GitOps Manifest Repo ]
                                                    ^
                                                    | (Pulls & Reconciles)
                                           [ ArgoCD on EKS Cluster ] ---> [ K8s API ]
```

##### 1. Direct CI Push (How it works & why we moved away)
* **Execution:** Jenkins runs on a worker node configured with AWS credentials or kubeconfig, executing:
  ```bash
  helm upgrade --install order-service ./chart \
    --namespace production \
    --values values-prod.yaml \
    --set image.tag=${GIT_COMMIT_SHORT} \
    --wait --timeout 5m
  ```
* **Drawbacks:**
  * **Security Blast Radius:** CI runners require administrative write permissions to the Kubernetes API server across multiple clusters.
  * **No Single Source of Truth:** Manual changes (`kubectl edit`) or out-of-band updates cause silent configuration drift.
  * **Fragile Rollbacks:** If a Jenkins pipeline is killed mid-upgrade, Helm releases can become stuck in `pending-upgrade` status.

##### 2. GitOps Pull Model with ArgoCD (Our Production Workflow)
1. **Decoupled CI:** Jenkins builds the Docker image, runs tests, scans vulnerabilities, pushes the image to ECR, and clones our dedicated `gitops-manifests` Git repository.
2. **Automated Commit:** Jenkins updates the image tag in `environments/prod/order-service/values.yaml` and commits the change:
   ```bash
   git commit -m "ci: promote order-service image to ${GIT_COMMIT_SHORT} [skip ci]"
   git push origin main
   ```
3. **Internal Cluster Reconciliation:**
   * ArgoCD runs entirely inside the EKS cluster. It detects the commit in Git and compares it to the live cluster state.
   * ArgoCD applies the Helm changes internally via the local Kubernetes API.
4. **Benefits:**
   * **Zero Secrets in CI:** Jenkins has zero access to Kubernetes cluster credentials.
   * **Automated Drift Detection & Healing:** If someone modifies a pod or service manually, ArgoCD automatically reconciles and restores the Git-defined state.
   * **Instant Audit Trail & 1-Click Rollback:** Every deployment is a Git commit. Rolling back a release is as simple as running `git revert`.
</details>

#### 【 IAC 】

<details>
<summary><strong>● Can you describe some of the things you've built using Ansible and/or Terraform to provision and configure infrastructure?</strong></summary>

**Answer:**
I apply the **"Right Tool for the Right Job"** principle across infrastructure automation: **Terraform** provisions immutable cloud infrastructure, while **Ansible** handles configuration management, OS hardening, and bare-metal / VM lifecycle orchestration.

##### 1. What I Have Built Using Terraform
* **Multi-Tier AWS VPC Foundation:**
  Reusable Terraform modules provisioning VPCs across 3 Availability Zones with dedicated Public, Private (Application), and Isolated (Database) subnets, NAT Gateways, Internet Gateways, Route Tables, and AWS Transit Gateway attachments.
* **Production Amazon EKS Platform:**
  Built end-to-end EKS clusters with managed node groups, custom launch templates (with IMDSv2 enforced), Karpenter autoscaling, OIDC providers for IAM Roles for Service Accounts (IRSA), and integrated Helm providers for cluster bootstrap addons.
* **Amazon MSK (Managed Streaming for Apache Kafka) Infrastructure:**
  Provisioned multi-broker MSK clusters spanning multiple private subnets with SASL/SCRAM authentication, TLS in-transit encryption, AWS KMS storage encryption, and automated CloudWatch log streaming.
* **Database & Storage Layer:**
  Multi-AZ Amazon Aurora / RDS PostgreSQL instances with automated failover, parameter groups, KMS customer-managed encryption keys, and S3 buckets with lifecycle tiering and object locking.

##### 2. What I Have Built Using Ansible
* **CIS Benchmark OS Hardening:**
  Developed modular Ansible roles enforcing CIS Level 1 and Level 2 security benchmarks on Ubuntu and RHEL instances (configuring `/etc/security/limits.conf`, disabling unused filesystems, securing SSH configurations, and setting auditd logging).
* **Golden AMI Pipeline (Packer + Ansible):**
  Orchestrated with HashiCorp Packer, Ansible playbooks provision base AMIs by installing corporate security agents (CrowdStrike, Datadog), tuning Linux kernel parameters (`sysctl`), and pre-installing required runtime dependencies.
* **Middleware & Service Management:**
  Automated deployment and configuration of NGINX reverse proxies, HAProxy load balancers, Logstash log forwarders, and Prometheus Node Exporters across legacy on-premise VMware VMs and cloud EC2 instances.
</details>

<details>
<summary><strong>↳ For the Terraform module you built for Amazon MSK, did you build it entirely from scratch, or did you use and modify an existing module?</strong></summary>

**Answer:**
I built our Amazon MSK Terraform module **in-house from scratch**, rather than using public community modules (such as `terraform-aws-modules/msk-kafka`).

##### Why We Built It From Scratch
While community modules are versatile, they often introduce significant abstraction layers, dozens of conditional variables, and unnecessary complexity for enterprise use. Building our dedicated module provided key advantages:
1. **Strict Enterprise Security Defaults:**
   We enforced organization-specific security guardrails that developers cannot override:
   * Mandatory TLS encryption in-transit for both inter-broker communication and client-broker traffic (`client_broker = "TLS"`).
   * Mandatory storage encryption at rest using our centralized AWS KMS Customer Managed Key (CMK).
   * Forced SASL/SCRAM authentication, completely disabling unauthenticated plaintext access.
2. **Simplified, Clean Interface:**
   The module exposed only the parameters needed by our internal product teams (e.g., `cluster_name`, `kafka_version`, `broker_instance_type`, `ebs_volume_size`, `subnet_ids`, and `authorized_scram_users`), keeping the code lightweight, easily readable, and maintainable.
3. **Integrated Resource Dependencies:**
   The module internally packaged the MSK cluster resource (`aws_msk_cluster`), custom MSK configuration (`aws_msk_configuration`), CloudWatch log groups for broker logs, and the Secrets Manager association (`aws_msk_scram_secret_association`) in a clean, self-contained bundle.
</details>

<details>
<summary><strong>↳ Did you run into any issues while building the Terraform module for the MSK cluster?</strong></summary>

**Answer:**
Building and managing the Amazon MSK cluster module in Terraform surfaced several distinct real-world challenges:

##### 1. Long Creation and Modification Times Leading to Provider Timeouts
* **Issue:** Amazon MSK cluster provisioning takes between **25 to 45 minutes**, as AWS sets up dedicated broker instances across multiple AZs and establishes Zookeeper/KRaft nodes. Default Terraform provider timeouts occasionally aborted the run mid-provisioning.
* **Resolution:** Configured explicit `timeouts` blocks inside the `aws_msk_cluster` resource:
  ```hcl
  timeouts {
    create = "60m"
    update = "60m"
    delete = "45m"
  }
  ```

##### 2. Unexpected In-Place Replacement (Destructive Re-creation)
* **Issue:** Changing certain attributes (such as changing subnet configurations, switching client authentication modes, or altering KMS keys) triggers a force-recreation of the cluster (`forces replacement`), which in production would result in catastrophic data loss.
* **Resolution:**
  * Implemented `lifecycle { prevent_destroy = true }` on production cluster declarations.
  * Extensively tested all planned updates in lower environments and utilized `terraform plan` output checks in CI pipelines to block any plan containing `-/+ destroy and then create replacement`.

##### 3. Circular Dependency with SASL/SCRAM Secret Association
* **Issue:** Associating SCRAM secrets with MSK requires a multi-step sequence:
  1. Generate secret in AWS Secrets Manager.
  2. Encrypt secret with an AWS KMS key that grants `kms:Decrypt` to the MSK service principal (`kafka.amazonaws.com`).
  3. Associate the secret ARN to the MSK cluster via `aws_msk_scram_secret_association`.
  If the KMS key policy or Secrets Manager resource policy was not applied before the association resource ran, the deployment failed with `AccessDeniedException`.
* **Resolution:** Used explicit Terraform `depends_on` blocks and strictly coordinated resource creation order between the IAM/KMS policy attachments and the SCRAM association.

##### 4. Broker Storage Auto-Scaling Constraints
* **Issue:** Once an EBS storage volume size is increased on an MSK broker, it cannot be decreased. Furthermore, AWS enforces a cooldown period (typically 6 hours) before another storage increase can be triggered.
* **Resolution:** Handled storage expansions cautiously through Terraform and integrated AWS Application Auto Scaling to handle dynamic storage increases rather than manual frequent updates.
</details>

<details>
<summary><strong>↳ Is it fair to say that you mostly used Ansible for post-provisioning configuration of an already-existing VM, rather than for the provisioning itself?</strong></summary>

**Answer:**
**Yes, that is completely accurate.** That distinction represents an industry best-practice division of responsibilities:

```
+-----------------------------------------------------------------------+
|  TERRAFORM (Infrastructure Provisioning)                              |
|  - Provisions VPCs, Subnets, Security Groups, IAM Roles, & EC2/VMs    |
|  - State management tracks cloud API objects                          |
+-----------------------------------------------------------------------+
                                  |
                                  | Hands off IPs / Hostnames
                                  v
+-----------------------------------------------------------------------+
|  ANSIBLE (Configuration Management & Post-Provisioning)               |
|  - Configures OS, installs packages, templates configuration files     |
|  - Manages systemd services, users, and security hardening            |
+-----------------------------------------------------------------------+
```

##### Why Ansible Is Best Kept for Post-Provisioning
1. **Declarative State Management:** Terraform tracks infrastructure state in a state file (`terraform.tfstate`), knowing exactly when an EC2 instance, VPC, or route table exists, needs modification, or should be destroyed. Ansible lacks native state tracking for cloud resources.
2. **Idempotent Configuration on Existing Nodes:** Ansible excels at connecting over SSH or WinRM to an existing machine to:
   * Apply OS patches and security updates.
   * Inject application configuration templates (`jinja2`).
   * Restart services only when configurations change (`handlers`).
3. **Immutable Infrastructure Evolution (Packer):**
   In our cloud environments, we evolved this further: instead of running Ansible post-provisioning on live running instances, we use Ansible as a provisioner inside **HashiCorp Packer** to bake AMIs ahead of time. When instances launch, they are already 100% configured, eliminating boot latency and configuration drift.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>↳ Was the Amazon MSK cluster you built serverless (AWS-managed) or a provisioned cluster where you controlled the underlying EC2 instances?</strong></summary>

**Answer:**
We built a **Provisioned MSK Cluster** rather than an MSK Serverless cluster.

##### Why Provisioned MSK Was Chosen for Production
While MSK Serverless offers automatic scaling without managing broker capacity, our enterprise architecture required capabilities only supported by Provisioned MSK:

| Feature / Requirement | Provisioned MSK (Our Choice) | MSK Serverless |
| :--- | :--- | :--- |
| **Throughput & Predictable Cost** | Dedicated broker instances (`kafka.m5.xlarge`) with predictable baseline throughput for high-volume streaming. | Charges per partition-hour and per MB ingested/streamed; becomes significantly more expensive at continuous high throughput. |
| **Authentication & Protocols** | Full support for **SASL/SCRAM**, mutual TLS (mTLS), and IAM authentication. | Historically limited primarily to IAM authentication, complicating legacy Java clients. |
| **Custom Kafka Configurations** | Complete control over broker parameters (e.g., `auto.create.topics.enable=false`, `log.retention.hours=168`, `compression.type=snappy`). | Does not permit tuning of underlying Apache Kafka broker configuration parameters. |
| **Network & Private Connectivity** | Multi-VPC and on-premise private connectivity via AWS Direct Connect and Transit Gateway with full network routing control. | Restricted networking configuration options. |
| **Custom Partitions & Topics** | Support for thousands of topic partitions per cluster. | Enforces strict maximum limits on partition counts and throughput caps (200 MiB/s ingress). |
</details>

#### 【 BEHAVIORAL 】

<details>
<summary><strong>● Given the company's technology stack (Ansible, small amount of Terraform, VMware, AWS, a small Azure footprint, and GitLab CI/CD) and the fact that the platform team is only two people managing the entire platform, which parts of that stack are you least comfortable with?</strong></summary>

**Answer:**
Being fully transparent and self-aware is critical, especially when joining a lean, high-ownership team of two engineers where cross-skilling and reliability are paramount.

##### 1. My Core Strengths (Immediate Day 1 Impact)
* **Linux, AWS, Terraform, and Docker/Containerization:** This represents my deepest daily expertise. I can immediately take full ownership of AWS infrastructure, Terraform refactoring, container workflows, and Linux system-level troubleshooting.
* **Ansible:** I am completely comfortable writing, modularizing, and maintaining Ansible roles and playbooks.

##### 2. Areas Where I Have Lower Comparative Experience
* **The On-Premises VMware Footprint:** While I understand virtualization fundamentals (vSphere, ESXi, datastores, vSwitches, and VM lifecycle operations), the bulk of my recent years has been heavily focused on cloud-native public cloud environments (AWS).
* **The Azure Footprint:** My multi-cloud experience is predominantly AWS-centered. While I understand Azure resource architecture (Resource Groups, VNets, Azure AD/Entra ID), my day-to-day familiarity with specific Azure CLI commands or Azure-native monitoring is less automatic than AWS.
* **GitLab CI/CD vs Jenkins/GitHub Actions:** While I have used GitLab CI, my primary enterprise CI pipeline development has been centered on Jenkins (Declarative pipelines) and GitHub Actions. However, because GitLab CI uses standard declarative YAML syntax (`stages`, `jobs`, `script`, `rules`, `artifacts`), the core paradigm is conceptually identical.

##### 3. Why This Is an Asset for a 2-Person Team
In a two-person platform team, complementary skills build resilience. I can take deep ownership of the cloud, Linux, and IaC/automation domains, freeing up my teammate to focus on VMware/Azure, while systematically cross-skilling to eliminate single points of failure across the entire platform.
</details>

<details>
<summary><strong>↳ If you were hired, what would your approach be to bridge the gaps in the areas you're less familiar with (such as GitLab CI/CD and on-prem infrastructure), and how would you go about familiarizing yourself with them?</strong></summary>

**Answer:**
To rapidly bridge technical gaps without slowing down team velocity, I apply a structured **30-60-90 Day Ramp-Up Plan**:

```
+-------------------------------------------------------------------------+
| DAYS 1 - 30: AUDIT, SHADOW & MAP                                        |
| - Shadow teammate on on-prem VMware tasks and GitLab CI deployments     |
| - Document existing architecture, runner topologies, and pain points    |
| - Build a dedicated sandbox environment to test GitLab CI pipelines     |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| DAYS 31 - 60: PRACTICAL OWNERSHIP & TARGETED REFACTORING                |
| - Take on routine GitLab CI maintenance & runner auto-scaling           |
| - Automate repetitive VMware VM tasks via Ansible playbooks             |
| - Create standardized, reusable GitLab CI YAML template components      |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| DAYS 61 - 90: FULL AUTONOMY & PLATFORM RESILIENCE                       |
| - Share on-call rotations across the entire hybrid stack                |
| - Standardize runbooks and disaster recovery procedures                 |
| - Eliminate single points of knowledge failure across the 2-person team |
+-------------------------------------------------------------------------+
```

##### 1. Fast-Tracking GitLab CI/CD Mastery
* **Translate Mental Models:** Map Jenkins concepts directly to GitLab CI equivalents (e.g., Jenkins Shared Libraries -> GitLab CI Templates/Components; Jenkins Agent Pods -> GitLab Kubernetes Executor Runners).
* **Runner Architecture Deep-Dive:** Audit the current runner setup (shared vs project-specific runners, shell vs Docker/Kubernetes executors, caching strategies like S3-backed runner caches).
* **Hands-on Refactoring:** Convert one non-critical pipeline to use modern GitLab CI best practices (`rules:if`, `needs: []` for Directed Acyclic Graph (DAG) fast execution, and secret masking).

##### 2. Mastering On-Premise VMware Infrastructure
* **Audit Existing Playbooks:** Review how Ansible interacts with VMware (e.g., `community.vmware` collection, `vmware_guest` module for cloning, customization, and snapshot management).
* **Standardize Runbooks:** Document common manual failure modes (datastore space exhaustion, ESXi host maintenance, vMotion triggers, network port-group allocations).
* **Automate Toil:** Pair Ansible with VMware automation to eliminate manual VM provisioning clicks in vCenter.

##### 3. Outcome
Within 60 days, both engineers will be capable of supporting any component of the hybrid stack, guaranteeing operational continuity and preventing burnout.
</details>

</details>

</details>

<details open>
<summary><h2>🏢 Mphasis</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>
*Date: 05-08-2026 06:47 PM*

#### 【 CI/CD 】

<details>
<summary><strong>● Can you explain how a Jenkins CI/CD pipeline works?</strong></summary>

**Answer:**
A Jenkins CI/CD pipeline automates the entire software delivery lifecycle from code commit to production deployment. In production, we utilize a **Declarative Pipeline** running on a **Master-Agent distributed architecture** (dynamic Kubernetes pod agents):

```
+-----------+    Webhook     +----------------+    Pod Agent    +-------------------------+
| Developer | -------------> | Jenkins Master | --------------> | Jenkins Ephemeral Agent |
| Git Push  |                +----------------+                 +-------------------------+
+-----------+                                                                |
     |                                                                       |
     v                                                                       v
+----------+      +-----------+      +------------+      +-------------+     |
| Checkout | ---> | Compile & | ---> | SonarQube  | ---> | Multi-Stage | ----+
| Source   |      | Tests     |      | Gate Scan  |      | Docker Build|
+----------+      +-----------+      +------------+      +-------------+
                                                               |
                                                               v
+-------------+      +------------+      +------------+  +-------------+
| Post Actions| <--- | Deploy to  | <--- | Automated  | <| Push to ECR |
| & Slack Msg |      | K8s / EKS  |      | Smoke Test |  | Registry    |
+-------------+      +------------+      +------------+  +-------------+
```

##### 1. Core Workflow Stages
1. **Source Code Checkout:** Jenkins receives a GitHub/GitLab webhook trigger and clones the repository using configured SSH credentials, pulling the exact Git commit SHA.
2. **Build & Unit Testing:** Executes project build tools (e.g., `mvn clean test` or `npm run build`), generating test coverage and surefire execution reports.
3. **Code Quality & Static Analysis:** Integrates with SonarQube via `withSonarQubeEnv`. The pipeline halts if code smells, security vulnerabilities, or branch coverage violate the enterprise Quality Gate (`waitForQualityGate()`).
4. **Vulnerability & Secret Scanning:** Scans application dependencies for known CVEs (OWASP Dependency-Check or Snyk) and scans Git history for accidental credential commits (TruffleHog / Gitleaks).
5. **Containerization & Image Scanning:** Compiles a minimal multi-stage Docker image and runs Trivy to detect OS-level package vulnerabilities before publishing.
6. **Registry Publish:** Authenticates against AWS ECR or Docker Hub and pushes the image tagged with the Git short commit hash and build number.
7. **Continuous Deployment (CD):**
   * Updates GitOps repository manifests for ArgoCD automated reconciliation, OR
   * Executes Helm commands directly (`helm upgrade --install <release> <chart>`) to update Kubernetes Deployments with zero downtime.
8. **Post-Build Actions:** Evaluates execution state (`success`, `failure`, `always`). Cleans the workspace (`cleanWs()`) and transmits notifications to Slack or PagerDuty.
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● What is the difference between the ADD and COPY instructions in a Dockerfile?</strong></summary>

**Answer:**
Both `ADD` and `COPY` instructions copy files or directories from a source location into the container's filesystem. However, they differ significantly in functionality, security implications, and best practices:

| Feature / Behavior | `COPY` (Recommended Standard) | `ADD` (Specialized Use Only) |
| :--- | :--- | :--- |
| **Primary Purpose** | Straightforward copying of local files/directories from the build context into the container. | Copying files with extra built-in features (tar auto-unpack and URL download). |
| **Tar Extraction** | **No.** Copies tar files (`.tar.gz`, `.tar`, `.tgz`) as literal tar files without unpacking. | **Yes.** Automatically extracts recognized compressed tar archives into the destination directory. |
| **Remote URLs** | **No.** Can only copy from the local build context or previous build stages. | **Yes.** Can download remote files directly from an HTTP/HTTPS URL into the container. |
| **Multi-Stage Builds** | **Yes.** Supports `--from=<stage_name>` to copy artifacts between build stages. | **No.** Does not support copying from previous build stages. |
| **Ownership Assignment** | Supports `--chown=<user>:<group>` flag directly during copy. | Supports `--chown=<user>:<group>` flag directly during copy. |
| **Docker Best Practice** | **Strongly recommended** for 99% of use cases due to predictability and transparency. | Discouraged unless automatic local archive extraction is specifically required. |

##### Why Docker Recommends `COPY` Over `ADD`:
1. **Remote URL Inefficiency:** When using `ADD` to fetch a remote file (e.g., `ADD https://example.com/package.tar.gz /tmp/`), the downloaded archive remains part of that container layer forever, bloating image size. The recommended approach is using `RUN curl` or `RUN wget` followed immediately by extraction and removal within a single `RUN` command:
   ```dockerfile
   # Best practice instead of ADD for remote URLs
   RUN curl -fsSL https://example.com/package.tar.gz | tar -xz -C /opt/
   ```
2. **Predictable Layer Caching:** Because `COPY` only touches local files, Docker's layer cache validation is faster, safer, and less prone to unexpected archive auto-extraction bugs.
</details>

<details>
<summary><strong>↳ What is the Docker command used to create an image?</strong></summary>

**Answer:**
The foundational command to build a Docker image from a `Dockerfile` and build context is:

```bash
docker build -t <image-name>:<tag> <context-path>
```

##### Production Examples & Essential Flags:
* **Standard Build with Tag:**
  ```bash
  docker build -t order-service:v1.2.0 .
  ```
* **Specifying a Custom Dockerfile Path:**
  ```bash
  docker build -f docker/Dockerfile.prod -t order-service:v1.2.0 .
  ```
* **Passing Runtime Build Arguments:**
  ```bash
  docker build --build-arg APP_ENV=production --build-arg JAVA_VERSION=17 -t order-service:v1.2.0 .
  ```
* **Targeting a Specific Multi-Stage Target:**
  ```bash
  docker build --target tester -t order-service:test .
  ```
* **Bypassing Cache for Clean Builds:**
  ```bash
  docker build --no-cache -t order-service:v1.2.0 .
  ```
* **Modern Cross-Platform Multi-Architecture Builds (Buildx):**
  In modern CI/CD pipelines, `docker buildx` is standard for compiling images for multiple CPU architectures (e.g., AWS Graviton ARM64 and Intel/AMD x86_64):
  ```bash
  docker buildx build --platform linux/amd64,linux/arm64 -t 123456789012.dkr.ecr.us-east-1.amazonaws.com/order-service:v1.2.0 --push .
  ```
</details>

#### 【 IAC 】

<details>
<summary><strong>● What are Ansible playbooks, and why are they used? Can you explain with an example?</strong></summary>

**Answer:**
An **Ansible Playbook** is a human-readable YAML configuration file that defines the desired end-state of remote target servers. Playbooks map a group of managed hosts to a sequential list of declarative tasks executed over agentless SSH (or WinRM for Windows).

##### Why Ansible Playbooks Are Used
1. **Agentless Architecture:** Requires no background daemon or agent installed on target machines; uses standard SSH with Python.
2. **Idempotence:** Tasks only execute changes if the target system does not already match the declared state. Re-running a playbook multiple times produces no unintended side effects.
3. **Declarative State Definition:** Focuses on *what* the system should look like rather than procedural bash scripting *how* to do it.
4. **Reusability & Modularity:** Playbooks can be organized into modular roles, collections, and variable files for complex enterprise fleets.

##### Production Example: Configuring a Hardened NGINX Web Server
Below is an end-to-end playbook demonstrating package installation, dynamic templating, service handlers, and firewall configuration:

```yaml
---
- name: Deploy and Configure Secure NGINX Reverse Proxy
  hosts: webservers
  become: true
  vars:
    nginx_port: 80
    server_admin: admin@company.com

  tasks:
    - name: Update apt cache and install NGINX
      ansible.builtin.apt:
        name: nginx
        state: present
        update_cache: yes

    - name: Deploy customized NGINX configuration from Jinja2 template
      ansible.builtin.template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/nginx.conf
        owner: root
        group: root
        mode: '0644'
      notify: Reload Nginx Service

    - name: Ensure NGINX service is enabled on boot and running
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: yes

    - name: Allow HTTP traffic through UFW firewall
      community.general.ufw:
        rule: allow
        port: "{{ nginx_port }}"
        proto: tcp

  handlers:
    - name: Reload Nginx Service
      ansible.builtin.service:
        name: nginx
        state: reloaded
```
</details>

<details>
<summary><strong>↳ What is the command used to run an Ansible playbook?</strong></summary>

**Answer:**
The CLI command used to execute an Ansible playbook is **`ansible-playbook`**:

```bash
ansible-playbook -i <inventory_file> <playbook_name.yml>
```

##### Production CLI Usage and Essential Flags:
* **Standard Execution with Static Inventory:**
  ```bash
  ansible-playbook -i inventory/production.ini deploy-webserver.yml
  ```
* **Dry-Run (Check Mode) & Diff:**
  Simulates execution without modifying target systems, showing the exact configuration diffs:
  ```bash
  ansible-playbook -i hosts.ini site.yml --check --diff
  ```
* **Limiting Execution to Specific Hosts or Groups:**
  ```bash
  ansible-playbook -i hosts.ini site.yml --limit web_us_east_1
  ```
* **Executing Specific Tagged Tasks:**
  ```bash
  ansible-playbook -i hosts.ini site.yml --tags "nginx,security"
  ```
* **Passing Runtime Extra Variables:**
  ```bash
  ansible-playbook -i hosts.ini deploy.yml -e "app_version=2.4.1 env=staging"
  ```
* **Privilege Escalation and SSH User:**
  ```bash
  ansible-playbook -i hosts.ini site.yml -u ubuntu --become --ask-become-pass
  ```
* **Syntax Checking:**
  ```bash
  ansible-playbook site.yml --syntax-check
  ```
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● What is AWS CloudWatch?</strong></summary>

**Answer:**
**Amazon CloudWatch** is AWS's centralized observability and management service providing monitoring, logging, alarming, and automated actions across AWS resources and customer applications.

```
+-------------------------------------------------------------------------+
|                        AMAZON CLOUDWATCH SUITE                          |
+-------------------------------------------------------------------------+
       |                         |                        |
       v                         v                        v
+------------------+    +------------------+    +------------------+
|    METRICS       |    |      LOGS        |    |     ALARMS       |
| - EC2 / RDS / EKS|    | - Log Groups     |    | - Static Bounds  |
| - Custom Metrics |    | - Metric Filters |    | - Anomaly Detect |
| - CloudWatch Agt |    | - Logs Insights  |    | - Composite      |
+------------------+    +------------------+    +------------------+
       |                         |                        |
       +-------------------------+------------------------+
                                 |
                                 v
                +---------------------------------+
                | ACTIONS & VISUALIZATION         |
                | - CloudWatch Dashboards         |
                | - SNS Alerts (Slack/PagerDuty)  |
                | - EC2 Auto Scaling Triggers     |
                | - EventBridge / Lambda Action   |
                +---------------------------------+
```

##### Core Pillars of AWS CloudWatch:
1. **CloudWatch Metrics:**
   * **Default Metrics:** Hypervisor-level metrics automatically collected without an agent (e.g., EC2 CPU utilization, network in/out, RDS IOPS, S3 bucket sizes).
   * **Custom / Guest OS Metrics:** Memory utilization, swap usage, and disk space are guest OS metrics not visible to the hypervisor; they are streamed via the **CloudWatch Agent** or API (`PutMetricData`).
2. **CloudWatch Logs:**
   * Organizes data into **Log Groups** and **Log Streams**.
   * **Metric Filters:** Scans streaming logs with pattern matchers (e.g., `[..., status_code = 5*, message]`) to generate real-time metrics from raw application logs.
   * **CloudWatch Logs Insights:** A query engine allowing interactive analysis of log data using a SQL-like syntax:
     ```sql
     fields @timestamp, @message
     | filter @message like /Exception/
     | stats count(*) by bin(5m)
     | sort @timestamp desc
     | limit 100
     ```
3. **CloudWatch Alarms:**
   * Evaluates metrics over time windows. Transitions between `OK`, `ALARM`, and `INSUFFICIENT_DATA`.
   * Triggers actions: Amazon SNS notifications (to Slack, OpsGenie, or PagerDuty), EC2 Auto Scaling policies (scale-out/scale-in), or EC2 instance recovery.
4. **CloudWatch Container Insights:**
   Pre-built monitoring for Amazon EKS and ECS, tracking compute, networking, and memory utilization at cluster, node, namespace, and pod levels.
5. **CloudWatch Synthetics:**
   Configurable headless browser canaries (Node.js/Python) testing REST APIs, UI flows, and URL availability 24/7.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● How do you configure Prometheus and Grafana for monitoring?</strong></summary>

**Answer:**
Setting up Prometheus and Grafana establishes an enterprise open-source monitoring stack based on the **pull-based metrics collection** paradigm:

```
[ Microservice App ]  --> Exposes /metrics
[ Node Exporter    ]  --> Exposes /metrics (Host CPU/RAM/Disk)
[ kube-state-metrics] --> Exposes /metrics (K8s Resource State)
        ^
        | Pulls metrics over HTTP every 15s
+-------------------------------------------------------------+
|                     PROMETHEUS SERVER                       |
| - Scrape Engine (Service Discovery / Scrape Configs)        |
| - TSDB Storage (Time Series Database on EBS / Local Disk)   |
| - Rule Engine (Alerting Rules & Recording Rules)            |
+-------------------------------------------------------------+
        |                                        |
        | Sends triggered alerts                 | PromQL queries
        v                                        v
+------------------+                    +--------------------+
|  Alertmanager    |                    |      GRAFANA       |
| -> Slack/PagerDuty|                   | -> Dashboards & UI |
+------------------+                    +--------------------+
```

##### 1. Configuring Prometheus
* **In Kubernetes (Recommended):** Deploy using the **`kube-prometheus-stack`** Helm chart (Prometheus Operator), which manages Prometheus instances, Alertmanager, Grafana, and exporters using Custom Resource Definitions (CRDs).
* **Scrape Configuration (`prometheus.yml`):**
  Defines collection rules and targets:
  ```yaml
  global:
    scrape_interval: 15s
    evaluation_interval: 15s

  rule_files:
    - "/etc/prometheus/alerting_rules.yml"

  scrape_configs:
    - job_name: 'node-exporter'
      kubernetes_sd_configs:
        - role: node
      relabel_configs:
        - action: labelmap
          regex: __meta_kubernetes_node_label_(.+)

    - job_name: 'microservices'
      metrics_path: '/actuator/prometheus'
      kubernetes_sd_configs:
        - role: pod
      relabel_configs:
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
          action: keep
          regex: true
  ```
* **Storage Retention:** Set TSDB retention duration and size: `--storage.tsdb.retention.time=30d --storage.tsdb.retention.size=100GB`.

##### 2. Configuring Grafana
* **Add Prometheus Data Source:**
  In Grafana, configure Prometheus as the default data source pointing to Prometheus's service address:
  * URL: `http://prometheus-k8s.monitoring.svc.cluster.local:9090`
  * Access: Server (default)
  * Scrape interval: `15s`
* **Automated Provisioning (Dashboard/Datasource as Code):**
  Configure datasource definitions via YAML files placed in `/etc/grafana/provisioning/datasources/` to eliminate manual UI clicks.
</details>

<details>
<summary><strong>↳ How do you create a dashboard in Grafana?</strong></summary>

**Answer:**
Creating an enterprise Grafana dashboard follows a structured workflow:

##### 1. Step-by-Step UI Creation Process
1. **Initiate Dashboard:** Click **Dashboards -> New -> New Dashboard -> Add visualization**.
2. **Select Data Source:** Select the configured Prometheus data source.
3. **Formulate PromQL Queries:**
   Enter the time-series PromQL expression. For example, to track Pod CPU utilization:
   ```promql
   sum(rate(container_cpu_usage_seconds_total{namespace="$namespace", pod=~"$pod"}[5m])) by (pod)
   ```
4. **Choose Panel Visualization Type:**
   * **Time Series:** For trends over time (CPU, RAM, latency, network traffic).
   * **Stat / Gauge:** For instantaneous health numbers (uptime, active connection count, current error percentage).
   * **Bar Gauge / Table:** For ranking top resource-consuming pods or database query times.
   * **Heatmap:** For request duration histograms and latency distributions.
5. **Configure Panel Properties:**
   * **Panel Options:** Title (e.g., `Pod CPU Usage (Cores)`), Description.
   * **Standard Options:** Unit (e.g., `short`, `bytes (IEC)`, `percent (0-100)`).
   * **Thresholds:** Set color boundaries (e.g., Green < 70%, Yellow 70–85%, Red > 85%).
6. **Implement Dashboard Template Variables:**
   Under **Dashboard Settings -> Variables**, create dynamic dropdown filters:
   * Variable `$namespace`: Type `Query`, Query `label_values(kube_pod_info, namespace)`
   * Variable `$pod`: Type `Query`, Query `label_values(kube_pod_info{namespace="$namespace"}, pod)`
   This allows operators to filter the entire dashboard by namespace and pod dynamically.

##### 2. Production Best Practice: Dashboard as Code
Rather than relying on manual UI creation, dashboards are exported as JSON models and version-controlled in Git, mounted via Kubernetes ConfigMaps and auto-loaded into Grafana using sidecar containers (`grafana-sc-dashboard`).
</details>

<details>
<summary><strong>↳ How do you set up alerts in Grafana or Prometheus?</strong></summary>

**Answer:**
Production monitoring architectures utilize either **Prometheus Native Alerting (via Alertmanager)** for infrastructure/platform alerts, or **Grafana Managed Alerting** for unified multi-source alerts.

##### 1. Setting Up Prometheus Native Alerts (Alertmanager)
This is the enterprise standard for Kubernetes and cloud infrastructure:
1. **Define Alerting Rules (`alerts.yml`):**
   ```yaml
   groups:
     - name: kubernetes-pod-alerts
       rules:
         - alert: PodCrashLooping
           expr: rate(kube_pod_container_status_restarts_total[15m]) * 60 > 2
           for: 5m
           labels:
             severity: critical
             team: platform
           annotations:
             summary: "Pod {{ $labels.pod }} is crashing frequently"
             description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} has restarted {{ $value }} times over the last 15 minutes."
   ```
2. **Configure Alertmanager Routing (`alertmanager.yml`):**
   Alertmanager routes, groups, dedupes, and silences alerts:
   ```yaml
   route:
     group_by: ['alertname', 'namespace']
     group_wait: 30s
     group_interval: 5m
     repeat_interval: 4h
     receiver: 'slack-notifications'
     routes:
       - match:
           severity: critical
         receiver: 'pagerduty-oncall'

   receivers:
     - name: 'slack-notifications'
       slack_configs:
         - channel: '#prod-alerts'
           api_url: 'https://hooks.slack.com/services/T00/B00/X00'
     - name: 'pagerduty-oncall'
       pagerduty_configs:
         - service_key: '<pagerduty-integration-key>'
   ```

##### 2. Setting Up Grafana Managed Alerting
1. Navigate to **Alerting -> Alert Rules -> New Alert Rule**.
2. **Query & Condition:** Set the PromQL expression and evaluation calculation (e.g., `WHEN avg() OF query(A, 5m, now) IS ABOVE 85`).
3. **Evaluation Behavior:** Define evaluation interval (every `1m`) and pending period `for: 5m`.
4. **Contact Points:** Configure delivery destinations (Slack Webhook, PagerDuty, Webhooks).
5. **Notification Policies:** Map alert labels (`severity=critical`) to appropriate contact points.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● How do you filter logs in Kibana?</strong></summary>

**Answer:**
Kibana (the visualization layer of the ELK/Elastic Stack or OpenSearch Dashboards) provides multiple query and filtering mechanisms inside the **Discover** view:

```
+-------------------------------------------------------------------------------+
| [ Search: service.name: "order-service" AND http.response.status_code >= 500 ]|
+-------------------------------------------------------------------------------+
| + Add Filter |  environment IS "production"  |  log.level IS "ERROR"         |
+-------------------------------------------------------------------------------+
| [ Time Picker: Last 15 minutes v ]   [ Auto-refresh: 10s v ]                 |
+-------------------------------------------------------------------------------+
```

##### 1. Kibana Query Language (KQL)
KQL is the modern, intuitive search language with auto-complete:
* **Exact Matching:**
  ```kql
  service.name: "payment-service" and log.level: "ERROR"
  ```
* **Status Code Range Queries:**
  ```kql
  http.response.status_code >= 500 and http.response.status_code <= 504
  ```
* **Substring & Wildcard Searches:**
  ```kql
  message: *ConnectionTimeoutException*
  ```
* **Nested Object & Array Queries:**
  ```kql
  kubernetes.namespace: "production" and not kubernetes.container.name: "istio-proxy"
  ```

##### 2. Lucene Query Syntax (Advanced)
Switching to Lucene enables regex and proximity searches:
* `log_level: ERROR AND (message: "timeout" OR message: "deadlock")`
* `response_time:[500 TO *]` (All requests with latency 500ms or higher)

##### 3. GUI Filter Pills (`+ Add filter`)
* Click **Add filter** -> Select Field (`kubernetes.labels.app`) -> Operator (`is`, `is not`, `is one of`, `exists`) -> Value (`order-service`).
* Filter pills can be pinned across multiple tabs or temporarily toggled on/off without re-typing.

##### 4. Field Value Inclusion/Exclusion from Log Rows
Expand any log document row in the table:
* Click the **`+` (Magnifying glass)** icon next to a field value to instantly create an inclusive filter.
* Click the **`-` (Negative magnifying glass)** icon to immediately exclude that value from the result set.

##### 5. Time Range Filtering
Use the **Time Picker** in the top-right corner to set relative ranges (`Quick: Last 15 minutes`, `Last 24 hours`) or zoom directly into an incident spike by clicking and dragging across the bar chart histogram.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself?

● **Candidate Introduction:** Can you explain about your project, your role in it, and the tools you used?
</details>

</details>

<details open>
<summary><h2>🏢 Cepegemini</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>
*Date: 05-08-2026 07:25 PM*

#### 【 CI/CD 】

<details>
<summary><strong>↳ Did you write Jenkins pipeline manifest files as part of your role?</strong></summary>

**Answer:**
**Yes, extensively.** In my DevOps engineering roles, I have designed, authored, and maintained production-grade **Declarative Jenkinsfiles** and modular **Groovy Jenkins Shared Libraries**.

##### Scope of Pipeline Manifests Authored:
1. **Root Declarative `Jenkinsfile` Definitions:** Standardized multi-stage pipelines encompassing checkout, linting, compilation, SonarQube quality gates, Docker containerization, security scanning (Trivy), artifact deployment to AWS ECR, and automated rollout to Amazon EKS.
2. **Dynamic Kubernetes Agent Pod Templates:** Defining custom Kubernetes pod templates embedded directly within the pipeline manifest to run build stages inside ephemeral containerized agents:
   ```groovy
   agent {
       kubernetes {
           yaml '''
   apiVersion: v1
   kind: Pod
   spec:
     containers:
     - name: maven
       image: maven:3.9.6-eclipse-temurin-17
       command: ['cat']
       tty: true
   '''
       }
   }
   ```
3. **Jenkins Shared Libraries:** Authored global shared library functions (`vars/deployHelm.groovy`, `vars/notifySlack.groovy`, `vars/trivyScan.groovy`) to eliminate duplicated pipeline code across 40+ microservice repositories.
</details>

<details>
<summary><strong>● What is the Jenkins home directory, and what does it contain?</strong></summary>

**Answer:**
The **Jenkins Home Directory** (typically located at `/var/jenkins_home` in containerized setups or `/var/lib/jenkins` in bare-metal/VM installations, defined by the `$JENKINS_HOME` environment variable) is the centralized file system repository where the Jenkins controller stores all configuration, pipeline definitions, build histories, installed plugins, and security keys.

```
$JENKINS_HOME/
├── config.xml                  # Global Jenkins master configuration
├── credentials.xml             # Encrypted system credentials store
├── secrets/                    # Master encryption keys (master.key, hudson.util.Secret)
├── plugins/                    # Installed plugin binaries (.jpi / .hpi files)
├── jobs/                       # Pipeline job configurations and historical build logs
│   └── order-service/
│       ├── config.xml          # Job-specific settings
│       └── builds/             # Build logs, artifacts, and build metadata
│           └── 42/
│               └── log         # Raw console log for build #42
├── nodes/                      # Permanent agent node configurations
├── userContent/                # Static files served directly by Jenkins
├── fingerprints/               # MD5/SHA checksums tracking file dependencies
└── workspace/                  # Default working directories (in single-node setups)
```

##### Critical Components Stored Inside `$JENKINS_HOME`:
* **`config.xml`:** The primary XML file containing all global configurations (system settings, security realms, authorization matrices, clouds, and agent connections).
* **`secrets/`:** Houses the critical master encryption keys used to decrypt passwords and tokens stored in `credentials.xml`. If this directory is lost, all stored credentials become permanently unrecoverable.
* **`plugins/`:** Contains all installed `.jpi` / `.hpi` plugin archive files and their unpacked data directories.
* **`jobs/`:** Contains a directory for every job and pipeline containing their build numbers, console logs, test results, and archived artifacts.
* **Disaster Recovery Best Practice:** To ensure rapid disaster recovery, `$JENKINS_HOME` (specifically excluding transient `workspace/` and `plugins/` cache) is backed up regularly to Amazon S3, or Jenkins is provisioned immutably via **Jenkins Configuration as Code (JCasC)**.
</details>

<details>
<summary><strong>● If a Jenkins plugin fails to load after a restart, how would you troubleshoot this issue?</strong></summary>

**Answer:**
When a Jenkins plugin fails to load following a controller restart, it usually stems from **incompatible plugin dependencies**, **Jenkins core version mismatch**, **corrupted plugin binaries**, or **file permission issues**.

##### Step-by-Step Troubleshooting Procedure:
1. **Analyze Controller Startup Logs:**
   Inspect the Jenkins system log directly on the host or via GUI (`Manage Jenkins -> System Log`):
   ```bash
   tail -n 100 /var/log/jenkins/jenkins.log
   # Or in Docker/Kubernetes:
   kubectl logs deployment/jenkins -n jenkins --tail=200
   ```
   Look for `java.io.IOException`, `PluginException`, `ClassNotFoundException`, or dependency error messages like `Plugin X depends on Plugin Y (>= 2.15), but version 1.9 is installed`.
2. **Identify Dependency Violations:**
   Jenkins plugins have strict directed acyclic dependency graphs. If a plugin was updated without updating its required downstream dependencies, the plugin will fail to initialize.
3. **Verify Core Version Compatibility:**
   Check if the updated plugin requires a minimum Jenkins core version (`Requires Jenkins 2.440.1`) that is newer than your current controller version.
4. **Emergency Recovery & Safe Mode:**
   If Jenkins fails to boot or hangs due to the corrupted plugin:
   * **Disable the Plugin Manually:** Navigate to `$JENKINS_HOME/plugins/` and create an empty `.disabled` file:
     ```bash
     cd /var/jenkins_home/plugins
     touch <plugin-name>.jpi.disabled
     ```
   * **Rollback to Backup Binary:** Jenkins automatically keeps a `.bak` backup copy of the previous plugin version during an update:
     ```bash
     mv <plugin-name>.jpi.bak <plugin-name>.jpi
     ```
   * **Remove Corrupted File:** If downloaded incompletely, delete the `<plugin-name>.jpi` file and its extracted directory, then restart Jenkins.
5. **Verify File Ownership & Permissions:**
   Ensure the Jenkins system user owns the plugin files:
   ```bash
   chown -R jenkins:jenkins /var/jenkins_home/plugins/
   chmod 644 /var/jenkins_home/plugins/*.jpi
   ```
</details>

<details>
<summary><strong>↳ Have you ever encountered a 'RejectedExecutionException' error in Jenkins?</strong></summary>

**Answer:**
**Yes.** `java.util.concurrent.RejectedExecutionException` in Jenkins occurs when the controller's internal thread pool (work queue executor) is overwhelmed, or when the executor service has been shut down while tasks are still being submitted.

##### Root Causes and Resolutions:

```
[ Incoming Pipeline Requests ] ---> [ Jenkins Master Work Queue ] ---> [ Executor Thread Pool ]
                                                |
                                                v (Queue Full / GC Pause / Shutdown)
                                  [ RejectedExecutionException ! ]
```

1. **Master Thread Pool & Work Queue Exhaustion:**
   * **Cause:** Too many concurrent pipeline tasks, lightweight checkouts, or webhook triggers submitted simultaneously, exceeding the capacity of Jenkins' internal executor thread pool.
   * **Resolution:** Increase work queue limits via JVM launch flags (e.g., `-Djenkins.model.Jenkins.workQueueSize=...`), offload builds strictly to ephemeral Kubernetes agents, and set the controller's built-in executors to **0** (`# of executors: 0` on master) so the master only acts as an orchestrator.
2. **Controller Out of Memory (OOM) / Extended Garbage Collection:**
   * **Cause:** When the Jenkins JVM experiences severe memory pressure and enters long Stop-the-World GC pauses, queued asynchronous tasks timeout and are rejected.
   * **Resolution:** Tune JVM heap parameters (`-Xms4g -Xmx8g -XX:+UseG1GC`) and inspect heap dumps using Eclipse Memory Analyzer (MAT) to identify memory-leaking plugins.
3. **Agent Node Abrupt Disconnection:**
   * **Cause:** A pipeline step attempts to dispatch a task to an agent channel that is already terminated or in the process of disconnecting (e.g., Spot instance termination or killed Kubernetes agent pod).
   * **Resolution:** Implement retry blocks around transient network steps and ensure Kubernetes agent pods have adequate CPU/memory allocations.
</details>

<details>
<summary><strong>● How do you install plugins in Jenkins?</strong></summary>

**Answer:**
In enterprise environments, plugins are installed using four distinct methods depending on security constraints and automation maturity:

##### 1. Web UI (Standard & Interactive)
* Navigate to **Manage Jenkins -> Plugins -> Available Plugins**.
* Search for the required plugin (e.g., "GitLab Plugin", "Kubernetes CLI").
* Select the checkbox and click **"Install without restart"** or **"Download now and install after restart"**.

##### 2. Advanced Offline / Air-Gapped Manual Upload
* Useful when Jenkins runs in isolated private subnets without outbound internet access:
* Download the compiled plugin file (`.hpi` or `.jpi`) from the official Jenkins plugin repository (`updates.jenkins.io`).
* Go to **Manage Jenkins -> Plugins -> Advanced settings -> Deploy Plugin**.
* Upload the `.hpi` file and restart Jenkins.

##### 3. Direct Filesystem Installation
* Copy the `.hpi`/`.jpi` file directly into the server's plugins directory:
  ```bash
  cp git-plugin.jpi /var/jenkins_home/plugins/
  chown jenkins:jenkins /var/jenkins_home/plugins/git-plugin.jpi
  systemctl restart jenkins
  ```

##### 4. Automated & Immutable Infrastructure (Production Standard)
In modern cloud-native setups, manual UI installations are anti-patterns. We manage plugins as code:
* **Docker Image Baking (`plugins.txt`):**
  Maintain a declarative list of plugins with exact versions in a `plugins.txt` file and bake them into a custom Docker image using `jenkins-plugin-cli`:
  ```dockerfile
  FROM jenkins/jenkins:lts-jdk17
  COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
  RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
  ```
* **Jenkins CLI:**
  Install plugins remotely via pipeline scripts or shell:
  ```bash
  java -jar jenkins-cli.jar -s http://jenkins.internal:8080/ -auth admin:token install-plugin git-parameter -restart
  ```
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● Why are containers considered better than virtual machines?</strong></summary>

**Answer:**
Containers and Virtual Machines (VMs) provide workload isolation, but they operate at fundamentally different layers of the infrastructure stack:

```
+-----------------------------+         +-----------------------------+
|        CONTAINERS           |         |      VIRTUAL MACHINES       |
+-----------------------------+         +-----------------------------+
| App A | App B | App C       |         | App A       | App B         |
| Libs  | Libs  | Libs        |         | Guest OS A  | Guest OS B    |
| Container Engine (Docker)   |         | (Kernel, etc)| (Kernel, etc)|
+-----------------------------+         +-----------------------------+
| Shared Host Linux Kernel    |         | Hypervisor (KVM / ESXi)     |
+-----------------------------+         +-----------------------------+
| Host OS & Bare Metal Server |         | Host OS & Bare Metal Server |
+-----------------------------+         +-----------------------------+
```

##### Key Architectural Differences:

| Metric / Dimension | Containers (Docker) | Virtual Machines (VMware / KVM) |
| :--- | :--- | :--- |
| **Virtualization Level** | **OS-Level Virtualization:** Virtualizes the Linux kernel using cgroups and namespaces. | **Hardware-Level Virtualization:** Virtualizes physical hardware components via a Hypervisor. |
| **Guest OS Overhead** | **None.** Shares the host OS kernel; contains only application binaries and libraries. | **Heavy.** Each VM must boot a dedicated, full guest OS (kernel, drivers, background daemons). |
| **Startup Time** | **Milliseconds to seconds.** A container is simply an isolated Linux process. | **Minutes.** Must execute BIOS, bootloader, kernel boot, and systemd init scripts. |
| **Resource Footprint** | Extremely lightweight (Megabytes of RAM; negligible CPU overhead). | Heavy (typically requires 2GB–8GB RAM just to keep the guest OS running). |
| **Density & Cost** | Hundreds of containers can run on a single host. | Limited to dozens of VMs per physical host before RAM/CPU exhaustion. |
| **Portability** | Complete parity across environments: image runs identically anywhere Docker is installed. | VM disk images (`.vmdk`, `.qcow2`) are multi-gigabyte, slow to transfer, and tied to hypervisors. |
</details>

<details>
<summary><strong>↳ Beyond the theoretical explanation, can you give a practical, real-world reason why containers are better than virtual machines?</strong></summary>

**Answer:**
Beyond theoretical resource metrics, the most critical real-world advantages of containers are **rapid autoscaling during live production traffic spikes** and **CI/CD pipeline execution velocity**.

##### 1. Real-World Scenario: Handling Instant Traffic Surges
* **The VM Dilemma:**
  Imagine an e-commerce platform during a flash sale or Black Friday event where incoming traffic surges by 10x in 60 seconds.
  * If the platform runs on traditional VMs (e.g., EC2 Auto Scaling Groups), provisioning new instances requires:
    1. Cloud hypervisor allocating virtual hardware (30–60s).
    2. Booting Linux kernel and systemd (45–90s).
    3. Running cloud-init bootstrap scripts and launching the JVM application (60–120s).
    4. Target group health checks passing (30s).
  * **Total Scaling Latency: 4 to 6 minutes.** During this delay, existing VMs run out of thread connections, requests queue up, users experience HTTP 504 Gateway Timeouts, and transactions are lost.
* **The Container Advantage:**
  * In a Kubernetes cluster with pre-warmed nodes, the Horizontal Pod Autoscaler (HPA) detects the metric spike.
  * Because the container image layers are already cached on the nodes, spinning up 30 new container replicas takes **3 to 8 seconds**.
  * The application absorbs the traffic spike immediately with zero dropped connections.

##### 2. Real-World Scenario: CI/CD Pipeline Throughput
* In a microservices architecture running 50+ builds a day:
  * With VMs, providing clean testing environments requires provisioning disposable VMs via Vagrant or cloud APIs (taking 5–10 minutes per pipeline run).
  * With Docker, pipelines spin up ephemeral PostgreSQL, Redis, and mock service containers using tools like **Testcontainers** in **under 2 seconds**, run tests against clean isolated databases, and terminate them instantly, reducing build times from 25 minutes down to 3 minutes.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Do you have experience working with Kubernetes?</strong></summary>

**Answer:**
**Yes, extensive hands-on enterprise experience.** I have spent over 5 years designing, deploying, securing, and maintaining production-grade Kubernetes environments across **Amazon EKS**, **Google Cloud GKE**, and self-managed vanilla Kubernetes clusters built using `kubeadm`.

##### Core Competencies in Kubernetes:
* **Cluster Provisioning & Architecture:** Provisioning multi-AZ EKS clusters via Terraform, configuring AWS VPC CNI with secondary CIDR ranges for pod IP exhaustion, and integrating Karpenter and Cluster Autoscaler.
* **Workload Management & GitOps:** Deploying microservices using **Helm** charts and **ArgoCD (GitOps)**, leveraging zero-downtime rolling updates, canary deployments (Argo Rollouts), and PodDisruptionBudgets.
* **Security & Governance:** Implementing RBAC, ServiceAccounts mapped to AWS IAM roles via **IRSA (OIDC)**, NetworkPolicies (Calico), Pod Security Standards, and External Secrets Operator connected to AWS Secrets Manager.
* **Observability & Triage:** Production monitoring using the **Prometheus Operator (kube-prometheus-stack)**, Grafana dashboards, Fluent-bit log forwarding to OpenSearch/CloudWatch, and resolving live node/pod incidents (`CrashLoopBackOff`, `OOMKilled`, CPU throttling, etcd latency).
</details>

<details>
<summary><strong>↳ In Amazon EKS, does AWS manage both the master (control plane) node and the worker nodes, or only one of them?</strong></summary>

**Answer:**
In Amazon EKS, **AWS manages ONLY the Control Plane (Master nodes)**. Worker nodes fall under the **Shared Responsibility Model** depending on the compute option selected:

```
+-------------------------------------------------------------------------+
|                  AMAZON EKS RESPONSIBILITY MODEL                        |
+-------------------------------------------------------------------------+
| AWS FULLY MANAGES:                                                      |
| - Control Plane (kube-apiserver, etcd, kube-controller, kube-scheduler)|
| - Multi-AZ High Availability across 3 AZs with 99.95% SLA               |
| - Control Plane auto-patching, automated etcd backups & recovery       |
| - (Zero user SSH / direct host access to master nodes)                  |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| CUSTOMER CONTROLS & CONFIGUTES (WORKER NODES):                          |
| - EC2 Instance Types, Capacities, & Scaling Policies                   |
| - Node Operating System & Security Hardening (AL2, Bottlerocket, Ubuntu)|
| - VPC Subnet placement, Security Groups, & Network Routing              |
| - Node Drain, Rolling Upgrades, & Worker OS Patching                    |
+-------------------------------------------------------------------------+
```

##### Worker Node Options:
1. **EKS Managed Node Groups (MNG):** AWS automates the provisioning, ASG attachment, and rolling AMI updates, but the instances run inside the customer's AWS account and VPC, and the customer configures node sizes, labels, and taints.
2. **Self-Managed Worker Nodes:** The customer writes custom Launch Templates and Auto Scaling Groups and manually executes node drain and AMI rotation.
3. **Karpenter Autoscaling:** An open-source Kubernetes-native node autoscaler running in the cluster that provisions right-sized EC2 instances directly via AWS APIs.
4. **AWS Fargate for EKS (Serverless):** AWS manages both the control plane and the underlying VM execution environment; the customer only provides the pod spec.
</details>

<details>
<summary><strong>↳ How are worker nodes managed and used in your EKS setup?</strong></summary>

**Answer:**
In our production EKS setup, worker node management is designed for high availability, cost efficiency, and zero-downtime maintenance using a hybrid model of **EKS Managed Node Groups** and **Karpenter**:

##### 1. System vs Application Workload Segregation
* **Core System Node Group (Managed Node Group):**
  * A small, static cluster of 3 multi-AZ instances running on On-Demand compute (`m6i.large`).
  * Dedicated to critical infrastructure daemonsets and operators: CoreDNS, AWS VPC CNI, kube-proxy, AWS Load Balancer Controller, Karpenter Controller, and Cert-Manager.
  * Tainted or protected to guarantee platform controllers never suffer eviction.
* **Dynamic Application Node Pools (Managed via Karpenter):**
  * Karpenter evaluates unscheduled pending pods, calculates exact aggregate CPU/memory requests, and launches the most cost-effective EC2 instances in under 45 seconds without relying on rigid ASG sizing.
  * **Spot Instance Optimization:** Stateless microservices are scheduled across diversified Spot instance types (`c6i`, `c6a`, `m6i`, `m6a`) with automatic fallback to On-Demand, achieving 60–70% infrastructure cost savings.

##### 2. Day-2 Lifecycle Management & Rolling Upgrades
* **Node Expiry & Automated Patching:**
  Nodes are configured with an expiration lifetime (`expireAfter: 720h / 30 days`). Karpenter continuously rolls nodes to guarantee that Linux OS security kernels and container runtimes are never more than 30 days old.
* **Safe Eviction via PodDisruptionBudgets (PDB):**
  Every application deployment defines a PDB (`minAvailable: 1` or `maxUnavailable: 25%`), ensuring node drains never violate service availability.
</details>

<details>
<summary><strong>● In an EKS/Kubernetes cluster, what happens to pod scheduling if the Kubernetes scheduler component goes down?</strong></summary>

**Answer:**
If the `kube-scheduler` component fails or becomes completely unreachable, the cluster experiences a **scheduling freeze for new workloads**, while **existing running workloads continue operating completely unaffected**.

##### Detailed Component-by-Component Impact:

```
[ Existing Running Pods ]   --> CONTINUES NORMAL EXECUTION (Managed by local node kubelet)
[ Pod Container Crash ]     --> RESTARTS ON SAME NODE (Kubelet handles restartPolicy locally)
[ New Pod Creation ]        --> ACCEPTS MANIFEST INTO ETCD, BUT REMAINS STUCK IN 'Pending'
[ Node Crash / Failover ]   --> UNABLE TO RESCHEDULE EVICTED PODS TO HEALTHY NODES
[ Explicit nodeName Pods ]  --> SCHEDULES SUCCESSFULLY (Bypasses scheduler completely)
```

1. **Existing Running Pods (NO IMPACT):**
   * The `kubelet` on each individual worker node communicates directly with the local container runtime (containerd) to run containers.
   * Existing pods continue servicing network traffic, accepting API calls, and executing background jobs without interruption.
2. **Container Restarts on Existing Nodes (NO IMPACT):**
   * If an application process crashes inside an already scheduled pod, the local `kubelet` monitors the process and automatically restarts the container according to its `restartPolicy` without consulting the scheduler.
3. **New Pods (STUCK IN `Pending` STATUS):**
   * When new deployments are created or scaled up, the `kube-apiserver` successfully validates the manifest and persists the new Pod object to `etcd`.
   * However, because the `pod.spec.nodeName` attribute is blank, and no scheduler is active to assign a node, the pods remain stuck in the **`Pending`** state indefinitely.
4. **Node Outages & Evictions (BLOCKED):**
   * If a worker node crashes, the `kube-controller-manager` eventually detects the node as `NotReady` and marks pods for eviction, but the newly generated replacement pods cannot be assigned to healthy nodes.
5. **Bypass Mechanism (`spec.nodeName`):**
   * If a pod manifest explicitly defines `spec.nodeName: worker-node-01`, it bypasses the `kube-scheduler` entirely. The specified node's `kubelet` detects the assignment directly from the API server and starts the pod.
6. **High Availability in EKS:**
   * In Amazon EKS, AWS runs multiple redundant control plane master instances with active leader election (`--leader-elect=true`). If the active scheduler crashes, a standby scheduler acquires the leader lease in `kube-system` within seconds, minimizing any scheduling disruption.
</details>

<details>
<summary><strong>● How do you troubleshoot and resolve an OOMKilled (Out of Memory) issue in Kubernetes?</strong></summary>

**Answer:**
An `OOMKilled` status indicates that a container was forcefully terminated by the operating system kernel with **Exit Code 137** (128 + 9 `SIGKILL`) because memory usage exceeded either the container's configured cgroup limit or the physical worker node's available RAM.

##### Step-by-Step Triage & Troubleshooting:
1. **Confirm OOMKilled Status:**
   ```bash
   kubectl get pods -n production
   # Shows Status: CrashLoopBackOff or OOMKilled
   kubectl describe pod <pod_name> -n production
   ```
   Inspect the `Last State` block:
   ```yaml
   Last State:     Terminated
     Reason:       OOMKilled
     Exit Code:    137
   ```
2. **Differentiate Container-Level vs Node-Level OOM:**
   * **Container Cgroup Limit Hit:** The container exceeded its `resources.limits.memory`. The container is killed and restarted, but the underlying worker node remains healthy.
   * **Node Memory Pressure:** The entire worker node ran out of RAM. The Linux kernel OOM killer selected and killed pods based on `oom_score_adj` (usually pods with `BestEffort` QoS class having no limits defined). Look for node events: `kubectl describe node <node_name>` and check for `MemoryPressure: True`.
3. **Analyze Historical Memory Consumption:**
   Query Prometheus / Grafana to inspect memory usage trends right before the crash:
   ```promql
   container_memory_working_set_bytes{namespace="production", pod="<pod_name>"}
   ```
   * *Gradual upward trend:* Indicates an application memory leak (unclosed database connections, infinite map caching).
   * *Sharp instantaneous spike:* Indicates processing a massive payload (e.g., bulk file upload loaded entirely into RAM).
4. **Java / JVM Specific Troubleshooting:**
   * For JVM applications, ensure container-aware flags are active:
     `-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0`
   * Never set `-Xmx` equal to the container memory limit; leave at least 25–30% overhead for JVM Metaspace, thread stacks, off-heap memory, and garbage collector buffers.
   * Configure automated heap dumps on OOM:
     `-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/dumps/oom.hprof`
5. **Remediation Actions:**
   * Adjust deployment memory requests and limits appropriately.
   * Configure a **Vertical Pod Autoscaler (VPA)** in `recommendation` mode to analyze realistic working set memory requirements.
   * Enforce default `LimitRange` in the namespace to prevent deployments from launching with unlimited memory allocations.
</details>

<details>
<summary><strong>● What is a PriorityClass in Kubernetes, and where is it applied?</strong></summary>

**Answer:**
A **`PriorityClass`** is a non-namespaced (cluster-scoped) Kubernetes resource that defines the relative importance and scheduling priority of pods using an integer value.

##### 1. How PriorityClass Works
* Higher numerical values denote higher priority (ranging from 0 up to `1,000,000,000`).
* **Pod Preemption:** When a cluster runs out of compute capacity and a high-priority pod is waiting to be scheduled, the `kube-scheduler` **preempts (evicts) lower-priority pods** from a worker node to free up sufficient CPU and memory to schedule the high-priority pod immediately.

##### 2. Defining a PriorityClass Manifest
```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority-production
value: 1000000
globalDefault: false
preemptionPolicy: PreemptLowerPriority
description: "Mission-critical core payment and transaction services."
```

##### 3. Where It Is Applied
The PriorityClass is applied directly inside the Pod specification (or Deployment template) using the **`priorityClassName`** field:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  namespace: production
spec:
  replicas: 5
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      priorityClassName: high-priority-production
      containers:
      - name: payment-api
        image: payment-service:v2.1
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
```

##### 4. Built-in System Priority Classes:
Kubernetes automatically provides two built-in classes reserved for platform stability:
* `system-cluster-critical` (`2000000000`): Used for cluster-wide critical pods like CoreDNS.
* `system-node-critical` (`2000001000`): Used for node daemonsets like AWS VPC CNI and kube-proxy so they are never evicted for regular applications.
</details>

<details>
<summary><strong>● What is a resource quota in Kubernetes?</strong></summary>

**Answer:**
A **`ResourceQuota`** is a namespace-scoped administrative control mechanism that limits the total aggregate compute resources (CPU and Memory), persistent storage, and Kubernetes API object counts that can be consumed across all workloads within a specific namespace.

```
+-------------------------------------------------------------------------+
|                  NAMESPACE: 'development' (ResourceQuota)               |
+-------------------------------------------------------------------------+
| Total CPU Limit:    16 Cores    [=========>          ] 9 Cores Used     |
| Total Memory Limit: 32 GiB      [==============>     ] 24 GiB Used      |
| Maximum Pods:       20 Pods     [==========>         ] 12 Pods Running  |
| LoadBalancers:       2 Services [====================] 2 Used (MAX HIT) |
+-------------------------------------------------------------------------+
```

##### 1. Production ResourceQuota Manifest
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-team-quota
  namespace: development
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    limits.cpu: "16"
    limits.memory: 32Gi
    persistentvolumeclaims: "10"
    requests.storage: 200Gi
    pods: "25"
    services.loadbalancers: "2"
```

##### 2. Why ResourceQuotas Are Essential:
1. **Multi-Tenant Protection:** Prevents a single team or runaway deployment from exhausting all cluster CPU/memory and starving other applications.
2. **Cloud Cost Governance:** Caps the number of expensive cloud resources (such as AWS Network/Application Load Balancers or EBS storage volumes) created within non-production environments.
3. **Mandatory Enforcement of Requests & Limits:** Once a `ResourceQuota` with CPU/Memory limits is applied to a namespace, **every pod created in that namespace must explicitly define `requests` and `limits`**. Any pod submitted without them is rejected by the API server with a `403 Forbidden` error. (We pair quotas with a **`LimitRange`** to supply automatic default requests/limits).
</details>

<details>
<summary><strong>● What is the difference between Horizontal Pod Autoscaling (HPA) and Vertical Pod Autoscaling (VPA) in Kubernetes?</strong></summary>

**Answer:**
**Horizontal Pod Autoscaler (HPA)** and **Vertical Pod Autoscaler (VPA)** are Kubernetes' two primary automated scaling controllers, differing in their scaling dimensions, operational mechanisms, and ideal workload profiles:

```
--- Horizontal Pod Autoscaling (HPA) ---
Scales OUT / IN by changing pod count:
[ Pod 1 ] ===> [ Pod 1 ] [ Pod 2 ] [ Pod 3 ] [ Pod 4 ]

--- Vertical Pod Autoscaling (VPA) ---
Scales UP / DOWN by changing pod size:
[ Pod (1 Core, 2GB) ] ===> [ Pod (4 Cores, 8GB) ]
```

##### Comprehensive Architectural Comparison:

| Feature / Dimension | Horizontal Pod Autoscaler (HPA) | Vertical Pod Autoscaler (VPA) |
| :--- | :--- | :--- |
| **Scaling Mechanism** | **Scales Out / In:** Increases or decreases the **number of pod replicas**. | **Scales Up / Down:** Modifies the **CPU & Memory requests/limits** of the container. |
| **Target Workloads** | Stateless microservices, REST APIs, consumer queue workers. | Stateful workloads (databases, singletons) or apps that cannot scale horizontally. |
| **Downtime & Restarts** | **Zero downtime.** Seamlessly provisions new pods behind existing Services. | **Requires Pod Restart** to modify cgroup limits (in standard K8s versions), causing pod disruption. |
| **Trigger Metrics** | Instantaneous metrics: CPU/Memory utilization, custom Prometheus metrics (RPS, queue depth). | Historical consumption trends analyzed over days/weeks. |
| **Operational Modes** | Active real-time autoscaling only. | Supports **`Off` (Recommendation Mode)**, `Initial` (only on pod creation), and `Auto` (recreates pods). |
| **Production Best Practice** | Primary scaling engine for modern web and backend microservices. | Frequently run in **Recommendation Mode (`Off`)** to right-size CPU/memory requests for HPA workloads. |

> [!CAUTION]
> **Never configure HPA and VPA together on the same resource metric** (e.g., both targeting CPU). They will enter an unstable race condition where VPA increases pod size while HPA simultaneously spawns more replicas, resulting in cluster thrashing.
</details>

#### 【 IAC 】

<details>
<summary><strong>● What are the different types/modules of Terraform (e.g., root module vs child module)?</strong></summary>

**Answer:**
In Terraform, a **module** is a container for multiple resources that are used together. Any directory containing `.tf` files is considered a module. Architecturally, Terraform distinguishes between two primary types of modules:

```
+-------------------------------------------------------------------------+
|                  ROOT MODULE (Execution Entrypoint)                     |
|                  main.tf, variables.tf, outputs.tf                      |
|                  Run: 'terraform init' & 'terraform apply'              |
+-------------------------------------------------------------------------+
       |                                          |
       | Calls with input arguments               | Calls with input arguments
       v                                          v
+-----------------------------+            +-----------------------------+
| CHILD MODULE 1 (VPC)        |            | CHILD MODULE 2 (EKS)        |
| source = "./modules/aws-vpc"|            | source = "git::ssh://..."   |
+-----------------------------+            +-----------------------------+
```

##### 1. Root Module
* **Definition:** The top-level working directory containing the main `.tf` files where Terraform CLI commands (`terraform init`, `terraform plan`, `terraform apply`) are directly executed.
* **Role:** Acts as the orchestrator. It configures the Terraform backend (e.g., S3/DynamoDB), provider blocks (e.g., AWS, Kubernetes, Helm), defines high-level environment variables, and invokes one or more child modules to compose the overall infrastructure stack.

##### 2. Child Module
* **Definition:** Any module that is called from within another module using a `module` block:
  ```hcl
  module "vpc" {
    source             = "./modules/aws-vpc"
    vpc_cidr           = var.vpc_cidr
    availability_zones = var.azs
  }
  ```
* **Role:** Packages reusable, encapsulated building blocks (e.g., a standardized VPC, a hardened EKS cluster, or a secure RDS database). It receives inputs via module parameters and exports computed values via `output` blocks.
* **Types of Child Modules:**
  * **Local Modules:** Sourced from local directories on the filesystem (`source = "./modules/vpc"`).
  * **Remote / Community Modules:** Sourced from the public Terraform Registry (`source = "terraform-aws-modules/vpc/aws"`), private Git repositories (`source = "git::https://github.com/company/tf-modules.git?ref=v2.1.0"`), or Amazon S3 buckets.

##### Architectural Best Practice:
* Keep root modules lightweight and declarative. Root modules should primarily call version-pinned internal child modules to enforce enterprise security standards, tag propagation, and DRY (Don't Repeat Yourself) principles across environments (`dev`, `staging`, `prod`).
</details>

<details>
<summary><strong>● How do you handle resource drift in Terraform?</strong></summary>

**Answer:**
**Resource Drift** occurs when the actual configuration of resources in the live cloud environment diverges from the recorded state in the Terraform state file (`terraform.tfstate`), usually caused by out-of-band manual changes (`ClickOps`), emergency CLI fixes, or external automated scripts.

```
[ Declared Terraform Code (.tf) ] <====== (DRIFT) ======> [ Live AWS Infrastructure ]
                 |                                                   ^
                 | (Reconcile / Refresh)                             |
                 +-------------------> [ terraform.tfstate ] --------+
```

##### Detection and Remediation Workflow:

##### 1. Detecting Drift (Read-Only)
Run Terraform in refresh-only mode to detect discrepancies without altering code or infrastructure:
```bash
terraform plan -refresh-only
```
Terraform queries the cloud provider APIs, compares the live attributes against the state file, and prints a detailed diff showing all drifted resources.

##### 2. Resolving Drift: Two Strategic Approaches

* **Strategy A: Revert Drift (Enforce Code as Single Source of Truth - Recommended)**
  If unauthorized or manual changes occurred in the cloud console and you want to restore the approved code configuration:
  ```bash
  terraform apply
  ```
  Terraform identifies that the live infrastructure does not match the code and issues API updates to overwrite the out-of-band changes, returning infrastructure strictly to the declared state.

* **Strategy B: Accept Drift (Sync Code with Live Infrastructure Reality)**
  If the manual change was an intentional emergency hotfix that needs to be preserved:
  1. Update the state file with the live cloud values:
     ```bash
     terraform apply -refresh-only
     ```
  2. Update the `.tf` source code to match the new live attributes so that running `terraform plan` produces `No changes. Your infrastructure matches the configuration`.

##### 3. Automated Prevention & Continuous Governance
* **Scheduled Drift Detection Pipelines:** Configure a CI/CD cron job (e.g., running daily in Jenkins/GitLab CI) executing `terraform plan -detailed-exitcode`. Exit code `2` indicates drift and immediately fires an alert to the platform Slack channel.
* **Service Control Policies (SCPs):** Enforce strict AWS IAM SCPs restricting manual console write permissions in production environments, making out-of-band changes impossible.
</details>

<details>
<summary><strong>● What is the difference between variables and outputs in Terraform?</strong></summary>

**Answer:**
In Terraform, **variables** and **outputs** represent the input and output boundaries of configurations and modules:

```
[ Input: variables.tf ] ===> [ Module Configuration (main.tf) ] ===> [ Output: output.tf ]
(Parameters / Arguments)            (Resource Creation)                  (Return Values)
```

##### Comprehensive Architectural Comparison:

| Feature / Attribute | Input Variables (`variable "..."`) | Output Values (`output "..."`) |
| :--- | :--- | :--- |
| **Analogy in Programming** | Function parameters / arguments. | Function return values. |
| **Data Direction** | **Into** the module/configuration. | **Out of** the module/configuration. |
| **Primary Purpose** | Parameterizes configurations, allowing the same code to deploy across environments (`dev`, `staging`, `prod`) without modification. | Exposes computed attributes (IDs, ARNs, DNS names) to the terminal, parent modules, or other states. |
| **Declaration File** | Declared in `variables.tf`. | Declared in `output.tf`. |
| **How Values are Injected / Read** | Injected via `terraform.tfvars`, `-var` flags, environment variables (`TF_VAR_name`), or module arguments. | Read via CLI (`terraform output`), accessed by parent modules (`module.<name>.<output_name>`), or consumed via `terraform_remote_state`. |
| **Configurable Options** | `type`, `default`, `description`, `validation`, `sensitive`, `nullable`. | `value`, `description`, `sensitive`, `depends_on`. |
</details>

<details>
<summary><strong>↳ What do you typically define/mention inside the output.tf file in Terraform?</strong></summary>

**Answer:**
The **`output.tf`** file declares specific resource attributes that need to be surfaced to terminal operators, passed to parent modules, or consumed by external systems (CI/CD pipelines, downstream Terraform states, or Kubernetes manifests).

##### Production Examples of Defined Outputs:
```hcl
# 1. Network Identifiers (Consumed by compute modules)
output "vpc_id" {
  description = "The ID of the provisioned VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs for application workloads"
  value       = aws_subnet.private[*].id
}

# 2. Cluster & Compute Endpoints (Consumed by Helm/ArgoCD pipelines)
output "eks_cluster_endpoint" {
  description = "Endpoint URL for Amazon EKS control plane API server"
  value       = aws_eks_cluster.main.endpoint
}

output "eks_cluster_name" {
  description = "Name of the EKS cluster used for kubeconfig generation"
  value       = aws_eks_cluster.main.name
}

# 3. Load Balancer & Edge DNS (Consumed by Route 53 or DNS teams)
output "alb_dns_name" {
  description = "Public DNS hostname of the ingress Application Load Balancer"
  value       = aws_lb.ingress.dns_name
}

# 4. Database Connection Strings & Sensitive Credentials
output "rds_endpoint" {
  description = "Read/write connection endpoint for RDS PostgreSQL"
  value       = aws_db_instance.database.endpoint
}

output "database_master_password" {
  description = "Generated master database administrator password"
  value       = aws_db_instance.database.password
  sensitive   = true # Masks value from console logs and CLI outputs
}
```
</details>

<details>
<summary><strong>↳ What is the purpose and advantage of using a variables.tf file in Terraform?</strong></summary>

**Answer:**
The **`variables.tf`** file establishes the formal schema and input parameter contract for a Terraform module or root configuration.

##### Purpose & Key Advantages:
1. **DRY Code Reusability:**
   Decouples infrastructure resource definitions from environment-specific configuration. Instead of hardcoding CIDR blocks, AMI IDs, or instance types in `main.tf`, parameters are abstracted into variables, enabling the identical codebase to deploy `dev`, `qa`, `staging`, and `prod` simply by supplying different `.tfvars` files.
2. **Type Safety & Early Validation:**
   Enforces strict type constraints (`string`, `number`, `bool`, `list`, `map`, `object`), catching configuration errors during `terraform validate` before any cloud API calls are made.
3. **Custom Validation Rules:**
   Supports inline custom validation logic to enforce corporate naming conventions or security restrictions:
   ```hcl
   variable "instance_type" {
     type        = string
     description = "EC2 instance type for worker nodes"
     default     = "m6i.large"
     validation {
       condition     = can(regex("^(m6i|c6i|r6i)\\.", var.instance_type))
       error_message = "Only 6th-generation Intel instance types (m6i, c6i, r6i) are approved."
     }
   }
   ```
4. **Secret Masking (`sensitive = true`):**
   Declaring `sensitive = true` on sensitive variables (passwords, tokens) prevents Terraform from printing plaintext values in console logs, plan outputs, or CI/CD logs.
5. **Clear Documentation & Self-Discovery:**
   Provides a clean, centralized schema where developers and platform engineers can immediately inspect all required versus optional inputs, descriptions, and default values.
</details>

#### 【 NETWORKING 】

<details>
<summary><strong>● What are the different OSI model layers?</strong></summary>

**Answer:**
The **Open Systems Interconnection (OSI)** model is a conceptual framework that standardizes telecommunication and computer network communication into **7 distinct layers**:

```
+---+--------------+----------------------------------+------------------------------+
| # | LAYER        | CORE FUNCTION                    | PROTOCOLS & HARDWARE         |
+---+--------------+----------------------------------+------------------------------+
| 7 | Application  | End-user interfaces & network APIs| HTTP, HTTPS, DNS, SSH, gRPC  |
| 6 | Presentation | Data serialization & encryption  | TLS/SSL, JSON, XML, Base64   |
| 5 | Session      | Connection & session management  | RPC, NetBIOS, Sockets        |
| 4 | Transport    | End-to-end reliability & ports   | TCP, UDP, NLB, Ports         |
| 3 | Network      | Routing & logical addressing     | IPv4, IPv6, ICMP, Routers    |
| 2 | Data Link    | Physical addressing & frames     | MAC addresses, Ethernet, VLAN|
| 1 | Physical     | Binary bit transmission over wire| Fiber, Copper (Cat6), Wi-Fi  |
+---+--------------+----------------------------------+------------------------------+
```

##### Detailed Layer Breakdown:
* **Layer 7 - Application:** Provides services directly to end-user software applications. Protocols: **HTTP, HTTPS, DNS, SSH, SMTP, FTP, gRPC**. (Where Application Load Balancers and AWS WAF operate).
* **Layer 6 - Presentation:** Handles data translation, character code translation, data compression, and cryptographic encryption/decryption: **TLS/SSL, JSON, ASCII, gzip**.
* **Layer 5 - Session:** Establishes, manages, coordinates, and terminates sessions and dialogues between applications: **RPC, PPTP, SOCKS**.
* **Layer 4 - Transport:** Manages packet segmentation, flow control, error recovery, and process-to-process addressing via ports: **TCP** (connection-oriented, guaranteed delivery), **UDP** (connectionless, ultra-low latency). (Where Network Load Balancers operate).
* **Layer 3 - Network:** Determines physical paths and handles logical routing and packet forwarding across different networks: **IP (IPv4/IPv6), ICMP, IPsec, Routers, VPC route tables**.
* **Layer 2 - Data Link:** Manages physical node-to-node frame transmission across the same local network segment, error detection, and hardware MAC addressing: **Ethernet, VLANs (802.1Q), ARP, Layer 2 Network Switches**.
* **Layer 1 - Physical:** Transmits unstructured raw bitstreams (`0`s and `1`s) over physical electrical, optical, or radio frequency media: **Cat6 Ethernet cables, Fiber optics, Network Interface Cards (NICs), Wi-Fi radio waves**.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● What is an AWS Fargate profile, and what is its use case in the context of EKS?</strong></summary>

**Answer:**
An **AWS Fargate Profile** is an Amazon EKS configuration resource that specifies which Kubernetes pods should be executed on **AWS Fargate** (serverless compute) rather than on traditional EC2 worker nodes.

```
+-------------------------------------------------------------------------+
|                        AMAZON EKS CONTROL PLANE                         |
+-------------------------------------------------------------------------+
                                    |
            +-----------------------+-----------------------+
            | Match Fargate Profile                         | Default Pods
            v Selectors (Namespace/Labels)                  v
+-------------------------------+               +-----------------------+
| AWS FARGATE (Serverless)      |               | EC2 WORKER NODES      |
| - MicroVM per pod (isolated)  |               | - Shared Linux kernel |
| - Zero node management / OS   |               | - High pod density    |
| - Auto-sized compute capacity |               | - DaemonSets supported|
+-------------------------------+               +-----------------------+
```

##### How Fargate Profiles Work:
A Fargate Profile defines one or more **selectors** combining a Kubernetes `namespace` and optional `labels`:
```hcl
resource "aws_eks_fargate_profile" "batch_workloads" {
  cluster_name           = "production-eks"
  fargate_profile_name   = "fp-batch"
  pod_execution_role_arn = aws_iam_role.fargate_pod_execution.arn
  subnet_ids             = aws_subnet.private[*].id

  selector {
    namespace = "batch-jobs"
    labels = {
      compute-type = "fargate"
    }
  }
}
```
When a pod is submitted to namespace `batch-jobs` matching the label, the EKS admission controller intercepts the pod and automatically schedules it onto an isolated, AWS-managed microVM.

##### Production Use Cases in EKS:
1. **Critical Cluster Bootstrap Workloads:** Running `CoreDNS` on Fargate so that internal DNS resolution functions immediately before any EC2 worker node pools are initialized.
2. **Ephemeral Batch & CI/CD Jobs:** Perfect for Jenkins agent pods, Argo Workflows, or periodic CronJobs that run for only a few minutes; eliminates paying for idle EC2 nodes.
3. **High Security & Regulatory Isolation:** Workloads requiring strict compliance (e.g., PCI-DSS financial payment processing) where pods must have dedicated microVM hardware-level virtualization isolation (via Firecracker) rather than sharing a multi-tenant EC2 Linux kernel.
4. **Zero-Maintenance Applications:** Web apps where the operations team wants zero operational overhead of node patching, OS upgrades, and AMI management.
</details>

<details>
<summary><strong>● What is AWS WAF (Web Application Firewall)?</strong></summary>

**Answer:**
**AWS WAF (Web Application Firewall)** is a Layer 7 security service that monitors and filters incoming HTTP/HTTPS traffic delivered to AWS web applications, protecting them against common web exploits, bots, and application vulnerabilities.

##### Deployment Integrations:
AWS WAF is attached directly to:
* **Application Load Balancers (ALB)**
* **Amazon CloudFront** (protects edge locations globally)
* **Amazon API Gateway** (REST / HTTP APIs)
* **AWS AppSync** (GraphQL APIs)

##### Core Capabilities & Rule Types:
1. **AWS Managed Rules (AMR):**
   Turnkey rule sets curated and updated by AWS Threat Research:
   * *Core Rule Set (CRS):* Shields against OWASP Top 10 vulnerabilities (SQL Injection, Cross-Site Scripting - XSS, Local File Inclusion).
   * *Known Bad Inputs & Amazon IP Reputation List:* Automatically drops traffic from recognized botnets, Tor exit nodes, and scanners.
2. **Custom Rate-Limiting Rules:**
   Blocks IP addresses that exceed request thresholds over a rolling 5-minute window (e.g., block any IP sending > 2,000 requests per 5 minutes to prevent Layer 7 HTTP flood DDoS attacks).
3. **Geographic & IP Set Filtering:**
   Restricts or allows traffic based on originating country codes or specific corporate CIDR whitelist blocks.
4. **AWS WAF Bot Control:**
   Differentiates between legitimate search engine crawlers and malicious automated scraping or credential-stuffing bots.
5. **Rule Actions:**
   Rules can be configured to **`ALLOW`**, **`BLOCK`** (returning a custom HTTP 403 response), **`COUNT`** (monitors and logs traffic without blocking, ideal for dry-run testing), or trigger interactive **`CAPTCHA` / `CHALLENGE`** tests.
</details>

<details>
<summary><strong>● What are AWS Step Functions?</strong></summary>

**Answer:**
**AWS Step Functions** is a fully managed, low-code serverless workflow orchestration service that enables developers and DevOps engineers to coordinate distributed microservices, AWS services, and event-driven architectures using visual **State Machines**.

```
[ Start ] ---> ( Task: Validate Order ) ---> [ Choice: Inventory Available? ]
                                                    |                  |
                                         (Yes)      v                  v (No)
                               ( Task: Charge Card )            ( Task: Notify Customer )
                                         |                             |
                                         v                             v
                              [ End: Success ]                 [ Fail: Out of Stock ]
```

##### Key Architectural Features:
* **Declarative Workflow as Code:** Workflows are declared using the **Amazon States Language (ASL)** (JSON or YAML) defining states (`Task`, `Choice`, `Wait`, `Parallel`, `Pass`, `Fail`, `Succeed`).
* **Direct AWS Service Integrations:** Coordinates over 300 AWS services (AWS Lambda, Amazon ECS/EKS tasks, DynamoDB, SNS, SQS, AWS Batch) directly without writing custom orchestration glue code.
* **Built-in Resiliency & Error Handling:** Provides native `Retry` and `Catch` blocks with configurable exponential backoffs and maximum retry attempts, eliminating fragile application retry logic.
* **Workflow Types:**
  * **Standard Workflows:** Designed for long-running, durable workflows (can run up to **1 year**). Supports human approval steps (`waitForTaskToken`), audit histories, and exactly-once execution.
  * **Express Workflows:** High-throughput, low-latency workflows (up to 5 minutes duration) designed for streaming data processing and IoT event ingestion.
* **DevOps Use Cases:** Automated disaster recovery orchestration, continuous compliance verification, automated AMI bake-and-test pipelines, and multi-step data ETL workflows.
</details>

<details>
<summary><strong>● What is the AWS CLI command used to create an S3 bucket?</strong></summary>

**Answer:**
In AWS CLI, an S3 bucket can be created using either the high-level `aws s3` command or the lower-level API `aws s3api` command:

##### 1. High-Level Command (`aws s3 mb` - Make Bucket)
```bash
aws s3 mb s3://my-enterprise-app-bucket --region us-east-1
```

##### 2. Low-Level API Command (`aws s3api create-bucket` - Production Standard)
The `s3api` command provides fine-grained control over regional constraints:
* **For `us-east-1` (Default Region):**
  ```bash
  aws s3api create-bucket \
    --bucket my-enterprise-app-bucket \
    --region us-east-1
  ```
* **For Any Other Region (e.g., `us-west-2`, `eu-west-1`):**
  AWS requires the `--create-bucket-configuration LocationConstraint=<region>` parameter:
  ```bash
  aws s3api create-bucket \
    --bucket my-enterprise-app-bucket \
    --region us-west-2 \
    --create-bucket-configuration LocationConstraint=us-west-2
  ```

##### Production Post-Creation Security Hardening:
Immediately after creation, enforce baseline security guardrails via CLI:
```bash
# 1. Block all public access
aws s3api put-public-access-block \
  --bucket my-enterprise-app-bucket \
  --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# 2. Enable default AWS KMS / AES-256 encryption at rest
aws s3api put-bucket-encryption \
  --bucket my-enterprise-app-bucket \
  --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'

# 3. Enable bucket versioning
aws s3api put-bucket-versioning \
  --bucket my-enterprise-app-bucket \
  --versioning-configuration Status=Enabled
```
</details>

<details>
<summary><strong>● For a gaming application, which type of AWS load balancer would be more suitable?</strong></summary>

**Answer:**
For a gaming application, a **Network Load Balancer (NLB)** is by far the most suitable load balancer.
</details>

<details>
<summary><strong>↳ Why is a Network Load Balancer (NLB) more suitable for a gaming application compared to other load balancer types?</strong></summary>

**Answer:**
Online gaming applications have rigorous performance, protocol, and latency constraints that make Application Load Balancers (ALB) unsuitable and Network Load Balancers (NLB) optimal:

```
[ Gaming Clients (Mobile/PC/Console) ]
                  |
                  | Ultra-low latency UDP/TCP traffic
                  v
+-------------------------------------------------------------------------+
|                  NETWORK LOAD BALANCER (Layer 4)                        |
| - Sub-millisecond latency & zero handshake processing overhead          |
| - Native UDP & TCP protocol support                                     |
| - Static Anycast IP per AZ                                              |
| - Handles millions of concurrent connections without pre-warming        |
+-------------------------------------------------------------------------+
                  |
                  v
[ Game Dedicated Servers / Pods (EKS / EC2) ]
```

##### Key Technical Reasons Why NLB Excels for Gaming:
1. **Layer 4 UDP & Raw TCP Protocol Support:**
   Real-time multiplayer games rely on **UDP** (User Datagram Protocol) for packet transmission (player positions, physics, inputs) because UDP avoids TCP connection retransmission delays. ALBs operate strictly at Layer 7 (HTTP/HTTPS/gRPC) and **cannot route UDP traffic**. NLB provides native high-performance UDP and TCP routing.
2. **Sub-Millisecond Ultra-Low Latency:**
   In competitive multiplayer gaming, latency (ping) must remain minimal (< 20–30ms). ALBs inspect HTTP headers, evaluate cookies, and parse L7 request data, introducing processing latency. NLB operates at the transport layer, passing packets directly with sub-millisecond response times.
3. **Massive Throughput Scaling Without Pre-Warming:**
   Gaming launches, tournament events, and match queues trigger volatile traffic surges of millions of concurrent connections within seconds. ALBs scale gradually and require manual "pre-warming" requests to AWS Support to survive such surges; NLBs scale instantly to millions of connections per second without intervention.
4. **Static Anycast IP Addresses:**
   NLB provides a dedicated static elastic IP address per Availability Zone. Game client applications and gaming consoles can hardcode or cleanly cache these IP addresses without being disrupted by changing dynamic DNS records.
5. **Preservation of Source Client IP:**
   NLB preserves the original player IP address down to the target game servers, which is crucial for anti-cheat verification, DDoS scrubbing, and geographical player matchmaking.
</details>

#### 【 SECURITY 】

<details>
<summary><strong>● What tool is typically used for handling/managing secrets in Jenkins (similar to how HashiCorp Vault is used with Terraform)?</strong></summary>

**Answer:**
For managing secrets in Jenkins, we utilize two tiers of tooling: the native **Jenkins Credentials Plugin** for standard operations, and **HashiCorp Vault (via the Jenkins HashiCorp Vault Plugin)** for enterprise environments.

##### 1. Jenkins Native Tool: Credentials Plugin & Credentials Binding
* **Functionality:** Built directly into Jenkins to securely store API tokens, SSH private keys, certificates, and username/password pairs.
* **Storage & Encryption:** Secrets are encrypted on the master filesystem inside `$JENKINS_HOME/credentials.xml` using internal master encryption keys (`secrets/master.key` and `secrets/hudson.util.Secret`).
* **Pipeline Integration:** Injected into pipelines using the `withCredentials` block, which guarantees that secret values are automatically masked in console logs:
  ```groovy
  withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
      sh 'mvn sonar:sonar -Dsonar.login=${SONAR_TOKEN}'
  }
  ```

##### 2. Enterprise Tool: HashiCorp Vault Integration (The Industry Standard)
In scalable multi-team environments, storing secrets statically inside Jenkins creates secret sprawl and lifecycle challenges. Similar to how Terraform integrates with Vault, Jenkins integrates with **HashiCorp Vault**:
* **Vault Plugin Workflow:**
  * Jenkins agents authenticate with HashiCorp Vault dynamically using **AppRole**, **Kubernetes ServiceAccount tokens**, or **AWS IAM authentication**.
  * Jenkins retrieves dynamic, short-lived database credentials or AWS STS tokens with auto-expiring Time-to-Live (TTL).
  * Pipeline Syntax:
    ```groovy
    stage('Fetch Dynamic Secrets') {
        steps {
            withVault(vaultSecrets: [[path: 'secret/data/production/database', engineVersion: 2, secretValues: [[envVar: 'DB_PASS', vaultKey: 'password']]]]) {
                sh './deploy.sh'
            }
        }
    }
    ```
* **Advantages:** Centralized audit logs, dynamic credential leasing, zero static secrets stored on the Jenkins master, and instant emergency revocation across the organization.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** What is your total years of professional experience, and how many of those years are relevant experience specifically in DevOps?

↳ **Candidate Introduction:** In your DevOps career, which industry domains have you worked in (e.g., banking, healthcare, retail, telecom)?

↳ **Candidate Introduction:** What was your specific contribution or role in those e-commerce and fintech projects?
</details>

</details>




