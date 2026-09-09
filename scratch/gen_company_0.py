# -*- coding: utf-8 -*-
"""Generator for Cyient interview round."""

def get_cyient_markdown():
    return """<details open>
<summary><h2>🏢 Cyient</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 16-08-2026 02:31 AM*

#### 【 CI/CD 】

<details>
<summary><strong>● Can you explain one of your CI/CD pipelines end-to-end, from code commit to production deployment?</strong></summary>

**Answer:**
In my recent production environment, I architected a multi-branch GitOps-driven CI/CD pipeline using **GitHub**, **Jenkins**, **SonarQube**, **JFrog Artifactory**, and **Argo CD** targeting an **AWS EKS** cluster.

1. **Source Code & Pre-commit Phase:**
   - Developers work on feature branches and create Pull Requests (PRs) against the `develop` or `main` branch.
   - Pre-commit hooks enforce formatting (`black`/`prettier`) and detect accidental secret commits using `detect-secrets` or `trufflehog`.

2. **Continuous Integration (CI) Trigger & Static Analysis:**
   - GitHub webhook triggers an ephemeral Jenkins Kubernetes agent.
   - **Linting & Unit Testing:** Executes unit tests (`mvn test` / `pytest`) and generates coverage reports.
   - **Static Application Security Testing (SAST):** Code is scanned by **SonarQube** using `withSonarQubeEnv`. The pipeline halts at `waitForQualityGate()` if code coverage is below 80% or any Blocker/Critical bugs or security vulnerabilities exist.
   - **Dependency Scanning:** Scans project dependencies for known CVEs using OWASP Dependency-Check or Snyk.

3. **Container Build & Artifact Management:**
   - A multi-stage Docker build produces a hardened container image based on Distroless/Alpine.
   - The image is tagged with the Git commit SHA: `${IMAGE_NAME}:${GIT_COMMIT}`.
   - Container vulnerability scanning runs via **Trivy** in the pipeline (`trivy image --exit-code 1 --severity CRITICAL`).
   - Binaries (JAR/WAR/npm) and Docker images are published to **JFrog Artifactory** / **AWS ECR**.

4. **Continuous Delivery (CD) & GitOps Deployment:**
   - The CI pipeline updates the Kubernetes manifest/Helm chart repository with the new image tag commit via a Git bot.
   - **Argo CD** running inside the EKS cluster detects the Git repository drift.
   - It performs automated synchronization into the `staging` environment.
   - Integration and smoke tests run automatically against the staging namespace.

5. **Production Release Strategy:**
   - Promotion to `production` requires a signed approval gate in Jenkins / GitHub Release.
   - Argo CD / **Argo Rollouts** performs a **Canary deployment**: routes 10% traffic to the new revision, tracks Prometheus metrics (HTTP 5xx rate < 0.1%, p99 latency < 250ms), and progressively shifts traffic to 100% over 30 minutes. If anomalies are detected, it executes an automatic rollback.
</details>

<details>
<summary><strong>↳ Follow-up: How did you integrate SonarQube and Artifactory with Jenkins in your CI/CD pipeline?</strong></summary>

**Answer:**
Both integrations were implemented using standard Jenkins declarative pipeline syntax with security tokens stored in Jenkins Credentials Manager:

1. **SonarQube Integration:**
   - Installed the **SonarQube Scanner** plugin on Jenkins.
   - Configured SonarQube Server under `Manage Jenkins -> System -> SonarQube servers` with the server URL and a secret authentication token.
   - Configured a Webhook in SonarQube pointing to `<JENKINS_URL>/sonarqube-webhook/`.
   - In the `Jenkinsfile`:
     ```groovy
     stage('SonarQube Analysis') {
         steps {
             withSonarQubeEnv('SonarQube-Server') {
                 sh 'mvn clean verify sonar:sonar -Dsonar.projectKey=payment-service'
             }
         }
     }
     stage('Quality Gate') {
         steps {
             timeout(time: 5, unit: 'MINUTES') {
                 script {
                     def qg = waitForQualityGate()
                     if (qg.status != 'OK') {
                         error "Pipeline aborted due to quality gate failure: ${qg.status}"
                     }
                 }
             }
         }
     }
     ```

2. **JFrog Artifactory Integration:**
   - Installed the **JFrog Artifactory** plugin.
   - Configured the Artifactory instance in Jenkins system settings with API tokens / service account credentials.
   - In the `Jenkinsfile`, used the Artifactory DSL:
     ```groovy
     stage('Publish Artifacts') {
         steps {
             script {
                 def server = Artifactory.server('artifactory-prod')
                 def uploadSpec = """{
                     "files": [
                         {
                             "pattern": "target/*.jar",
                             "target": "libs-release-local/com/company/payment-service/${BUILD_NUMBER}/"
                         }
                     ]
                 }"""
                 def buildInfo = server.upload(uploadSpec)
                 server.publishBuildInfo(buildInfo)
             }
         }
     }
     ```
   - For Docker images, credentials were bound using `withCredentials([usernamePassword(credentialsId: 'artifactory-docker-creds', usernameVariable: 'USER', passwordVariable: 'PASS')])` followed by `docker login` and `docker push`.
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● Can you explain the lifecycle of a Docker container?</strong></summary>

**Answer:**
A Docker container transitions through distinct lifecycle states governed by Docker engine and Linux kernel primitives (namespaces, cgroups, and storage drivers):

```
[ Dockerfile ] -> (docker build) -> [ Image ]
                                       |
                                 (docker create)
                                       v
                                 [ Created ]
                                       |
                                  (docker start)
                                       v
        (docker pause)   +---> [ Running ] <---+ (docker restart)
       +-------------->  |         |           |
       |  [ Paused ]  |  |         | (docker stop: SIGTERM -> SIGKILL)
       +--------------+  |         v
        (docker unpause) +---- [ Stopped / Exited ]
                                       |
                                  (docker rm)
                                       v
                                  [ Deleted ]
```

1. **Created (`docker create`):** The image layers are mounted with a thin read-write container layer, namespaces and cgroups are initialized, and container ID is allocated, but PID 1 has not started.
2. **Running (`docker start` / `docker run`):** The entrypoint/cmd process is launched as PID 1 inside the namespaces. The container stays running as long as PID 1 is alive.
3. **Paused (`docker pause`):** Uses the Linux cgroups `freezer` subsystem to suspend all processes in the container without freeing memory. Resumed using `docker unpause`.
4. **Stopped / Exited (`docker stop` / `docker kill`):**
   - `docker stop`: Sends `SIGTERM` to PID 1, waits for a grace period (default 10s) for graceful cleanup, then sends `SIGKILL` if still alive.
   - `docker kill`: Immediately sends `SIGKILL` (or custom signal like `SIGHUP`).
5. **Deleted (`docker rm`):** Removes the container metadata, execution state, and its writable layer from the host filesystem.
</details>

<details>
<summary><strong>● Can you explain what a multi-stage Dockerfile is and why it's used?</strong></summary>

**Answer:**
A **multi-stage Dockerfile** uses multiple `FROM` instructions in a single file to separate the **build environment** (SDKs, compilers, package managers, test tools) from the **runtime environment** (bare minimum binaries and OS libraries).

**Why it is used:**
1. **Dramatically Smaller Image Size:** Drops image sizes from 800MB–1.5GB down to 20MB–100MB by discarding build artifacts, caches, and dev tools.
2. **Hardened Security & Attack Surface Reduction:** Eliminates build tools (gcc, git, curl, npm) and shell utilities from production, preventing remote attackers from exploiting them.
3. **Optimized Build Caching:** Build stages can be independently cached, accelerating CI/CD pipelines.

**Production-Grade Multi-Stage Example (Go Microservice):**
```dockerfile
# Stage 1: Build & Compile
FROM golang:1.22-alpine AS builder
WORKDIR /src
RUN apk add --no-cache git ca-certificates
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o /bin/service .

# Stage 2: Minimal Distroless Runtime
FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /
COPY --from=builder /bin/service /service
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/service"]
```
The final image contains only the statically linked Go binary, CA certificates, and a non-root user—zero OS shell, zero package manager, and minimal vulnerability footprint.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● How do you troubleshoot a CrashLoopBackOff error in Kubernetes?</strong></summary>

**Answer:**
`CrashLoopBackOff` indicates that a container starts, encounters a fatal condition, exits, and Kubelet attempts to restart it with exponential backoff delay (10s, 20s, 40s... up to 5 minutes).

**Systematic Senior DevOps Troubleshooting Process:**

1. **Inspect Pod State and Exit Codes:**
   ```bash
   kubectl get pods -n <namespace> -o wide
   kubectl describe pod <pod-name> -n <namespace>
   ```
   Check the `State` and `Last State` sections for **Exit Code** and termination reason:
   - **Exit Code 0:** Application finished task and exited cleanly; container had no long-running process (PID 1 exited).
   - **Exit Code 1 / 2:** Application fatal runtime exception, missing configuration, syntax error.
   - **Exit Code 137 (`128 + 9`):** Container received `SIGKILL`. Most commonly **OOMKilled** (Out Of Memory). Verify if `Last State: Terminated (Reason: OOMKilled)` appears. Fix: increase `resources.limits.memory` or address application memory leak.
   - **Exit Code 139 (`128 + 11`):** Segmentation fault (library incompatibility or corrupted binary).
   - **Exit Code 143 (`128 + 15`):** Container received `SIGTERM` (often triggered by failed liveness probe or node draining).

2. **Analyze Container Logs:**
   - Check current container logs:
     ```bash
     kubectl logs <pod-name> -n <namespace> -c <container-name>
     ```
   - **Crucial:** Check logs from the crashed container *prior* to restart:
     ```bash
     kubectl logs <pod-name> -n <namespace> -c <container-name> --previous
     ```

3. **Check Liveness / Readiness Probes:**
   - If `livenessProbe` has an aggressive timeout (`initialDelaySeconds: 5` when the app takes 30s to boot), Kubelet prematurely kills the container, inducing a CrashLoop. Fix: increase `initialDelaySeconds` or configure a `startupProbe`.

4. **Verify Dependencies and Configurations:**
   - Missing or misnamed ConfigMaps, Secrets, or persistent volume mounts (`kubectl get configmap,secrets -n <namespace>`).
   - Database connection failure, DNS resolution failure (`coredns`), or unavailable downstream microservices.

5. **Debug Interactively:**
   ```bash
   # Override entrypoint to keep container alive for live inspection
   kubectl run debug-pod --image=<image> -n <namespace> --command -- sleep 3600
   kubectl exec -it debug-pod -n <namespace> -- /bin/sh
   ```
</details>

<details>
<summary><strong>● What is the difference between a ClusterIP service and a NodePort service in Kubernetes?</strong></summary>

**Answer:**
Both are Kubernetes Service abstractions that direct traffic across dynamic pod IPs using label selectors, but they serve different networking scopes:

| Feature | ClusterIP | NodePort |
| :--- | :--- | :--- |
| **Default Service Type?** | Yes | No (built on top of ClusterIP) |
| **IP Address Allocated** | Virtual IP from cluster CIDR (internal only) | Allocates internal ClusterIP + dedicated port on every node |
| **Accessibility** | Accessible **only** within the Kubernetes cluster | Accessible internally **and** externally via `<NodeIP>:<NodePort>` |
| **Port Range** | Any valid TCP/UDP port (e.g., 80, 443, 8080) | Restricted range (default: `30000–32767`) |
| **Routing Mechanism** | `kube-proxy` configures iptables/IPVS rules mapping virtual IP to Pod endpoints | `kube-proxy` binds port across all worker nodes; forwards to internal ClusterIP |
| **Primary Use Cases** | Internal microservice communication, database access, backends behind an Ingress controller | Direct external access without cloud load balancer, bare-metal clusters, or edge legacy systems |

**Manifest Comparison:**
```yaml
# ClusterIP (Internal only)
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
    - port: 80
      targetPort: 8080

---
# NodePort (External via any Node IP on port 30080)
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport-service
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080
```
In modern cloud environments, production architectures avoid exposing NodePorts directly to the internet; instead, they expose an Ingress Controller (via AWS ALB / NGINX) backed by internal `ClusterIP` services.
</details>

<details>
<summary><strong>● Can you briefly explain the difference between ConfigMaps and Secrets in Kubernetes?</strong></summary>

**Answer:**
Both **ConfigMaps** and **Secrets** decouple configuration artifacts from container image code, but they are engineered for different levels of sensitivity and security:

1. **ConfigMap:**
   - **Purpose:** Stores non-confidential configuration data as key-value pairs or complete configuration files (e.g., `nginx.conf`, database hostnames, environment variables).
   - **Storage & Security:** Stored in plain text in `etcd`. Visible in cleartext via `kubectl get configmap <name> -o yaml`.
   - **Use Case:** Application properties, feature flags, UI themes, logging levels.

2. **Secret:**
   - **Purpose:** Stores confidential data such as passwords, API keys, SSH keys, and TLS certificates.
   - **Storage & Security:** Stored Base64-encoded by default (not encrypted by default unless `EncryptionConfiguration` is enabled in etcd). When mounted as volumes, Secrets are written to in-memory virtual filesystems (`tmpfs`) on the node, preventing sensitive data from writing to physical disks.
   - **Best Practice:** Encrypt etcd at rest using AWS KMS or HashiCorp Vault, and synchronize secrets dynamically via the **External Secrets Operator (ESO)** or **AWS Secrets Manager CSI driver**.

```yaml
# Example usage in a Deployment pod spec:
env:
  - name: DB_HOST
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: db_host
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: db_password
```
</details>

#### 【 IAC 】

<details>
<summary><strong>● Can you explain the Terraform workflow from 'terraform init' to 'terraform apply'?</strong></summary>

**Answer:**
The Terraform core workflow comprises four key stages:

1. **`terraform init` (Initialization):**
   - Scans configuration files (`.tf`) in the working directory.
   - Configures the backend (e.g., AWS S3 bucket with DynamoDB state locking).
   - Downloads required provider plugins (e.g., `hashicorp/aws`, `hashicorp/kubernetes`) into `.terraform/providers/`.
   - Downloads referenced child modules (local or remote registry) into `.terraform/modules/`.
   - Generates or updates the dependency lock file (`.terraform.lock.hcl`).

2. **`terraform validate` (Static Verification):**
   - Verifies configuration syntax, internal consistency, attribute names, and types without accessing remote APIs.

3. **`terraform plan` (Execution Planning):**
   - Refreshes state: Queries cloud provider APIs to determine the current state of existing resources.
   - Compares the desired state (code) against the refreshed state (`terraform.tfstate`).
   - Computes delta and produces a speculative plan displaying actions:
     - `+` Create, `~` Update in-place, `-` Destroy, `-/+` Replace.
   - Can save the binary execution plan (`terraform plan -out=tfplan`) to guarantee deterministic execution in CI/CD.

4. **`terraform apply` (Execution & State Convergence):**
   - Acquires a state lock (e.g., via DynamoDB) to prevent concurrent executions.
   - Executes cloud API calls in the calculated dependency graph order.
   - Writes the new resource attributes and metadata to the remote state file.
   - Releases the state lock upon completion.
</details>

<details>
<summary><strong>● How do you roll back changes made through Terraform?</strong></summary>

**Answer:**
Terraform does **not** possess a native `terraform rollback` command. In production enterprise environments, rollbacks must be handled through strict state management and GitOps practices:

1. **Git Revert (Forward-Fix Rollback - Recommended):**
   - Revert the problematic commit in Git:
     ```bash
     git revert <commit-sha>
     git push origin main
     ```
   - Trigger the CI/CD pipeline: Terraform calculates the difference between current live infrastructure and the reverted code, cleanly generating a plan to revert resources back to their prior configuration.

2. **State Version Rollback (Corrupted State Recovery):**
   - If an apply failed and left state corrupted or out of sync, download the previous state version from S3 (enabled by S3 bucket versioning):
     ```bash
     aws s3api list-object-versions --bucket tf-state-bucket --prefix env/prod/terraform.tfstate
     aws s3api get-object --bucket tf-state-bucket --key env/prod/terraform.tfstate --version-id <PREV_VERSION_ID> terraform.tfstate
     terraform state push terraform.tfstate
     ```

3. **Targeted Apply (`-target`):**
   - If an outage is caused by a single misconfigured resource, immediately fix that resource in code and apply only that target to avoid running a full plan during an incident:
     ```bash
     terraform apply -target=aws_security_group.app_sg
     ```

4. **Anti-pattern to Avoid:** Never run `terraform destroy` as a rollback strategy in production, as it destroys dependent persistent resources (databases, EFS, VPCs).
</details>

<details>
<summary><strong>● Can you explain what a Terraform remote backend is and how it works?</strong></summary>

**Answer:**
A **Terraform remote backend** specifies where Terraform stores its state file (`terraform.tfstate`) and how operations like state locking and remote execution are handled.

**How it works in AWS (S3 + DynamoDB architecture):**
```
   Engineer / CI/CD (Runs terraform plan / apply)
                    |
      +-------------+-------------+
      |                           |
      v                           v
[ AWS DynamoDB ]             [ AWS S3 ]
(State Locking Table)      (Encrypted State Storage)
- LockID: md5(path)        - SSE-KMS Encryption
- Prevents concurrent run  - S3 Bucket Versioning
                           - Restrictive IAM Policies
```

1. **State Locking:** Before any write operation (`plan`, `apply`), Terraform writes a lock record containing an MD5 checksum, info, and timestamp to a designated DynamoDB table (`LockID`). If another pipeline or developer runs simultaneously, it receives `Error: Error acquiring the state lock` and terminates.
2. **Encrypted State Storage:** S3 stores the JSON state file with Server-Side Encryption (`SSE-KMS`) and bucket versioning. Sensitive variables stored in state are protected by KMS keys and S3 bucket access policies.
3. **Collaboration Single Source of Truth:** Ensures that team members and CI/CD runners never operate on stale local state files.

**Configuration Example:**
```hcl
terraform {
  backend "s3" {
    bucket         = "prod-company-tfstate-bucket"
    key            = "vpc/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}
```
</details>

<details>
<summary><strong>● Can you explain what an Ansible inventory is and how it's used?</strong></summary>

**Answer:**
An **Ansible inventory** is a configuration file or executable script that defines the target hosts (servers, network devices, containers) where Ansible tasks and playbooks will be executed.

**How it is used:**
1. **Grouping & Categorization:** Organizes servers into logical tiers (e.g., `[webservers]`, `[dbservers]`, `[prod]`, `[staging]`), enabling playbooks to target specific groups.
2. **Variable Assignment:** Defines host-specific (`host_vars`) or group-specific (`group_vars`) parameters such as connection ports, SSH users, and application settings.

**Types of Inventories:**
- **Static Inventory (INI or YAML):**
  ```ini
  [webservers]
  web1.company.internal ansible_host=10.0.1.10
  web2.company.internal ansible_host=10.0.1.11

  [dbservers]
  db1.company.internal ansible_host=10.0.2.10

  [prod:children]
  webservers
  dbservers

  [prod:vars]
  ansible_user=ubuntu
  ansible_ssh_private_key_file=~/.ssh/id_rsa
  ```
- **Dynamic Inventory:** Used in dynamic cloud environments where instances are autoscaled or ephemeral. Ansible plugins (such as `aws_ec2`) dynamically query cloud APIs to build inventory based on tags (`tag:Environment: production`).
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Can you explain how auto scaling works in AWS?</strong></summary>

**Answer:**
AWS Auto Scaling automatically adjusts compute capacity to maintain application availability and optimize costs based on demand. In EC2, it operates through three core elements:

1. **Launch Template:** Defines what to launch:
   - AMI ID, EC2 instance type/size, IAM instance profile, Key pair, Security groups, EBS storage volumes, and User Data bootstrap scripts.

2. **Auto Scaling Group (ASG):** Defines where and how many instances to run:
   - VPC subnets across multiple Availability Zones (Multi-AZ resilience).
   - Capacity limits: `Min Size`, `Desired Capacity`, and `Max Size`.
   - Target Group integration: Registers new instances automatically with an Application Load Balancer (ALB).

3. **Scaling Policies:** Defines when to scale:
   - **Target Tracking Scaling:** Adjusts capacity to keep a selected metric at a target value (e.g., maintain ALB Request Count Per Target at 1000, or Average CPU Utilization at 60%).
   - **Step Scaling:** Scales by specific step increments when CloudWatch alarms breach thresholds (e.g., CPU > 75% add 2 instances; CPU > 90% add 4 instances).
   - **Scheduled Scaling:** Pre-scales ahead of known business traffic spikes (e.g., scale up at 8 AM on weekdays).
   - **Predictive Scaling:** Machine learning models forecast future traffic patterns and provision capacity before spikes occur.

4. **Health Checks & Self-Healing:**
   - Evaluates EC2 hardware status checks and ALB HTTP health check responses (`/healthz`).
   - If an instance is marked unhealthy, the ASG terminates it and provisions a replacement to satisfy the `Desired Capacity`.
   - Default cooldown and instance warmup periods prevent metric thrashing and rapid over-scaling.
</details>

<details>
<summary><strong>● Can you differentiate between an IAM role and an IAM user in AWS?</strong></summary>

**Answer:**
Both are AWS Identity and Access Management (IAM) identities that have attached permission policies, but their authentication mechanisms and security postures differ fundamentally:

| Feature | IAM User | IAM Role |
| :--- | :--- | :--- |
| **Intended Entity** | Individual humans or legacy applications | AWS services (EC2, Lambda, EKS pods), cross-account access, federated identities (Okta, Azure AD) |
| **Credentials** | **Long-term credentials** (Console password + Access Key ID / Secret Access Key) | **Short-lived temporary credentials** issued via AWS STS (Security Token Service) |
| **Credential Expiry** | Do not expire automatically; must be rotated manually | Expire automatically (15 minutes to 12 hours) |
| **Security Risk** | High: risk of accidental hardcoding in Git repos or leak | Minimal: zero hardcoded secrets; credentials auto-renewed |
| **Trust Policy** | Does not have a trust policy | Must have an **AssumeRole Trust Policy** specifying who can assume it |
| **Production Best Practice** | Prohibited for CI/CD and services; human access managed via SSO | Industry standard for all service-to-service communication and EKS IRSA |

**Role Trust Policy Example (EC2 Assumption):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● How many monitoring tools do you have experience with?</strong></summary>

**Answer:**
In enterprise production platforms, I have hands-on experience designing and operating tools across the **Three Pillars of Observability** (Metrics, Logs, and Traces):

1. **Metrics & Alerting:**
   - **Prometheus & Alertmanager:** Primary open-source monitoring stack for Kubernetes, utilizing Prometheus Operator (`ServiceMonitor`, `PrometheusRule`).
   - **Grafana:** Building operational and executive dashboards, alerting, and visualizing metric correlations.
   - **AWS CloudWatch:** Cloud-native monitoring for managed AWS services (RDS, ALB, Lambda, DynamoDB, NAT Gateway metrics).

2. **Centralized Logging:**
   - **ELK / OpenSearch Stack:** Elasticsearch/OpenSearch clusters for indexing, Logstash/Fluent Bit as log shippers running as Kubernetes DaemonSets, and Kibana/OpenSearch Dashboards for query and analysis.

3. **APM & Distributed Tracing:**
   - **Datadog:** Full-stack APM, synthetic testing, network monitoring, and host metrics.
   - **Jaeger & OpenTelemetry (OTel):** Instrumentation of microservices for distributed tracing to diagnose p99 latency bottlenecks across API calls.

4. **Incident Response & Paging:**
   - **PagerDuty & Opsgenie:** On-call rotation scheduling, escalation policies, and alert deduplication.
</details>

<details>
<summary><strong>↳ Follow-up: How does Prometheus collect metrics from Kubernetes nodes and pods?</strong></summary>

**Answer:**
Prometheus uses a **pull-based architecture**, scraping HTTP endpoints that expose metrics in the OpenMetrics / Prometheus text format:

```
[ Prometheus Server ]
    |
    |-- Scrapes HTTP GET /metrics every 15s via Service Discovery
    |
    +---> [ node-exporter DaemonSet ] (Node CPU, RAM, Disk, Network)
    |
    +---> [ Kubelet / cAdvisor ]      (Container CPU, Memory, cgroup limits)
    |
    +---> [ kube-state-metrics ]      (Pod phase, Deployment replicas, PVC status)
    |
    +---> [ Application Pods ]        (Custom business metrics at /metrics)
```

1. **Node Metrics (`node-exporter`):**
   - Deployed as a `DaemonSet` on every Kubernetes worker node. It extracts Linux kernel hardware and OS metrics (CPU, memory, disk I/O, network stats) and exposes them on port 9100 (`/metrics`).

2. **Container & Pod Metrics (`cAdvisor`):**
   - Embedded directly inside the **Kubelet** daemon running on every node. It inspects Linux cgroups to gather container-level resource utilization (CPU throttles, memory RSS, network traffic) and exposes them at `https://<NodeIP>:10250/metrics/cadvisor`.

3. **Kubernetes Object State (`kube-state-metrics`):**
   - Connects to the Kubernetes API server and transforms object status (e.g., Desired vs. Ready replicas, pod scheduling status, PVC capacity) into Prometheus metrics.

4. **Service Discovery & Scraping Mechanisms:**
   - In standard setups, Prometheus uses `kubernetes_sd_configs` to query the API server for endpoints matching annotations (`prometheus.io/scrape: "true"`).
   - In modern setups with the **Prometheus Operator**, scraping is managed declaratively using `ServiceMonitor` and `PodMonitor` Custom Resources that select Kubernetes services based on label selectors.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Can you explain what a canary deployment strategy is?</strong></summary>

**Answer:**
A **canary deployment** is an advanced progressive delivery technique where a new application version (canary) is deployed alongside the existing stable version (baseline), and a small percentage of production traffic (e.g., 5% to 10%) is routed to it.

**Workflow & Architecture:**
```
                     +--> [ Stable Deployment v1.0 ] (90% Traffic)
[ Ingress / Router ] |
                     +--> [ Canary Deployment v2.0 ] (10% Traffic)
                                 |
                        (Prometheus Analysis)
                     - HTTP 5xx Error Rate < 0.1%
                     - p99 Latency < 200ms
                                 |
                +----------------+----------------+
                | Passed                          | Failed
                v                                 v
   Scale Canary to 100%               Immediate Auto-Rollback to v1.0
```

1. **Traffic Splitting:** Traffic is divided using an Ingress controller (NGINX ingress canary annotations), a Service Mesh (Istio `VirtualService` weights), or Kubernetes controller extensions like **Argo Rollouts** or **Flagger**.
2. **Automated Metric Verification:** As live traffic hits the canary, automated health analysis runs continuously. Key Golden Signals (error rates, latency, saturation) are queried from Prometheus or Datadog.
3. **Automated Promotion or Abort:**
   - If error rates remain within acceptable thresholds, traffic progressively increases (e.g., 10% -> 25% -> 50% -> 100%).
   - If anomalies or threshold breaches occur, traffic is instantly reverted back to 100% on the stable version with zero user-visible outage.

**Key Advantages:**
- Minimizes blast radius: Only a tiny fraction of users encounter a bug if the release is flawed.
- Zero-downtime releases with data-driven validation.
- Requires database backward compatibility (schema changes must support both v1.0 and v2.0 concurrently).
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Where are you originally from?

● **Candidate Introduction:** Can you introduce yourself and give an overview of your professional background?

● **Candidate Introduction:** How many years of professional experience do you have?

● **Candidate Introduction:** What was your previous company?
</details>
</details>"""
