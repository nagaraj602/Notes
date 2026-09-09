<details open>
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
                 def uploadSpec = '''{
                     "files": [
                         {
                             "pattern": "target/*.jar",
                             "target": "libs-release-local/com/company/payment-service/${BUILD_NUMBER}/"
                         }
                     ]
                 }'''
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
</details>

<details open>
<summary><h2>🏢 Mphasis</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 17-08-2026 03:49 PM*

#### 【 LINUX 】

<details>
<summary><strong>↳ Follow-up: You mentioned that you work more with shell scripting rather than Python — is that correct?</strong></summary>

**Answer:**
Yes, that is accurate in the context of day-to-day Linux systems operations and CI/CD agent automation, though I leverage both tools based on architectural requirements:

- **Shell / Bash Scripting:** My primary choice for OS-level automation, container entrypoint scripts (`docker-entrypoint.sh`), chaining Linux utilities (`awk`, `sed`, `grep`, `systemctl`, `journalctl`), lightweight cron jobs, and glue code in CI/CD pipeline steps. Shell provides instantaneous execution without runtime interpreter dependencies.
- **Python:** Used whenever the automation requires complex data structures, parsing JSON/YAML payloads, interacting with REST APIs, cloud SDKs (such as **Boto3** for AWS), Kubernetes API client operations, or when comprehensive error handling and unit tests (`pytest`) are necessary.
</details>

#### 【 IAC 】

<details>
<summary><strong>● What is the role of the inventory file in Ansible?</strong></summary>

**Answer:**
The **Ansible inventory file** defines the target managed nodes (hosts) that Ansible communicates with and controls during playbook execution.

**Key Roles:**
1. **Host Definition:** Lists IP addresses, DNS hostnames, and custom connection ports.
2. **Logical Grouping:** Groups servers by function (e.g., `[webservers]`, `[dbservers]`), environment (e.g., `[prod]`, `[staging]`), or geographical region.
3. **Variable Association:** Assigns host-specific (`ansible_host`, `ansible_user`, `ansible_port`) and group-specific variables.
4. **Hierarchical Relationships:** Allows groups of groups (nested groups using `:children`), enabling aggregate plays.
</details>

<details>
<summary><strong>↳ Follow-up: What are the different types of inventory files in Ansible?</strong></summary>

**Answer:**
Ansible supports two primary types of inventories:

1. **Static Inventory:**
   - A manually maintained text file in **INI** or **YAML** format.
   - Best suited for small, predictable on-premise environments where server IPs and hostnames rarely change.
   - Example:
     ```ini
     [web]
     web1.corp.internal ansible_host=192.168.1.10
     web2.corp.internal ansible_host=192.168.1.11

     [web:vars]
     ansible_user=deploy
     http_port=80
     ```

2. **Dynamic Inventory:**
   - Implemented via Ansible inventory plugins (e.g., `amazon.aws.aws_ec2`, `azure.azcollection.azure_rm`, `kubernetes.core.k8s`) or executable scripts.
   - Dynamically queries cloud provider APIs at runtime to discover active compute instances and groups them automatically by metadata and tags (`tag:Environment_prod`).
   - Essential in autoscaling cloud environments where instances are ephemeral.
   - Example configuration (`aws_ec2.yaml`):
     ```yaml
     plugin: amazon.aws.aws_ec2
     regions:
       - us-east-1
     keyed_groups:
       - key: tags.Role
         separator: ''
     ```
</details>

<details>
<summary><strong>● How does variable precedence work in Ansible?</strong></summary>

**Answer:**
Ansible evaluates variables using an extensive precedence hierarchy comprising **22 distinct levels**, designed so that more specific and explicitly defined variables override broader defaults.

**Key Precedence Hierarchy (from lowest to highest):**
1. Role defaults (`roles/x/defaults/main.yml`) — *Lowest precedence, easily overridden*
2. Inventory file or script group vars
3. Inventory `group_vars/all`
4. Playbook `group_vars/all`
5. Inventory `group_vars/*`
6. Playbook `group_vars/*`
7. Inventory file or script host vars
8. Inventory `host_vars/*`
9. Playbook `host_vars/*`
10. Host facts / cached facts
11. Play vars (`vars:` block in playbook)
12. Play vars_prompt
13. Play vars_files
14. Role vars (`roles/x/vars/main.yml`)
15. Block vars (only for tasks in block)
16. Task vars (only for the task)
17. `include_vars`
18. `set_facts` / registered vars
19. Extra vars (`-e` / `--extra-vars`) — *Highest precedence*
</details>

<details>
<summary><strong>↳ Follow-up: In Ansible's variable precedence hierarchy, which source has the highest precedence?</strong></summary>

**Answer:**
**Extra variables (`--extra-vars` or `-e`)** passed on the command line have the **highest precedence** in Ansible. They override all variables defined in role defaults, inventory files, playbooks, host/group vars, role vars, and registered facts.

```bash
ansible-playbook deploy.yml -e "app_version=2.4.1 environment=production"
```
</details>

<details>
<summary><strong>● When would you use handlers in Ansible?</strong></summary>

**Answer:**
**Handlers** are special tasks in Ansible that execute **only when triggered by a `notify` directive** from another task that resulted in a state change (`changed: true`).

**When to use:**
1. **Service Restarts on Configuration Drift:** Restarting or reloading daemons (e.g., Nginx, Apache, Systemd, PostgreSQL) only when their underlying configuration files (`.conf`) have actually been modified.
2. **Post-Task Triggers:** Rebuilding firewall rules (`iptables` / `firewalld`), re-running `ldconfig`, or updating OS CA certificates after installing a new root certificate.

**Execution Behavior:**
- Handlers run **once** at the very end of the play, regardless of how many tasks notified them. This prevents redundant restarts (e.g., modifying 3 Nginx configs results in a single reload).

```yaml
tasks:
  - name: Deploy Nginx configuration
    ansible.builtin.template:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf
    notify: Restart Nginx

handlers:
  - name: Restart Nginx
    ansible.builtin.systemd:
      name: nginx
      state: restarted
```
</details>

<details>
<summary><strong>● How does Ansible ensure secure communication between the control node and target hosts?</strong></summary>

**Answer:**
Ansible uses native, agentless cryptographic protocols to secure control node communications:

1. **Linux / UNIX Hosts:**
   - Uses **OpenSSH (SSH)** by default.
   - Communication is encrypted using standard asymmetric cryptography (Ed25519 or RSA 4096-bit keys).
   - Passwordless key authentication via `ssh-agent` or SSH Bastion/Jump hosts (`ProxyJump`).
   - Host key checking can be strictly enforced (`host_key_checking = True`) to prevent man-in-the-middle (MITM) attacks.

2. **Privilege Escalation:**
   - Runs tasks as a standard unprivileged user and safely escalates privileges using `sudo` with restricted sudoers rules (`become: yes`).

3. **Sensitive Data Protection:**
   - Uses **Ansible Vault** to encrypt sensitive variables, passwords, and private keys with AES-256 encryption at rest.
</details>

<details>
<summary><strong>↳ Follow-up: You mentioned Ansible can also use HTTPS for secure communication — for which specific operating system is that used?</strong></summary>

**Answer:**
Ansible uses **HTTPS** when managing **Microsoft Windows** operating systems via **WinRM (Windows Remote Management)**.

**Key Implementation Details:**
- **Protocol:** WinRM listening on TCP port **5986** (HTTPS with TLS encryption), as opposed to unencrypted HTTP on port 5985.
- **Authentication:** Supports Kerberos (Active Directory), NTLM, or Certificate-based authentication.
- **Ansible Configuration:**
  ```ini
  [win]
  win-server1.corp.internal

  [win:vars]
  ansible_user=Administrator
  ansible_password={{ vault_win_password }}
  ansible_connection=winrm
  ansible_winrm_server_cert_validation=validate
  ansible_port=5986
  ansible_winrm_transport=ntlm
  ```
</details>

<details>
<summary><strong>● What are Ansible facts and how are they used?</strong></summary>

**Answer:**
**Ansible facts** are granular, system-level details and properties automatically discovered and gathered from target hosts prior to executing playbook tasks.

**How they work:**
- The internal module `ansible.builtin.setup` automatically runs at the beginning of each play (unless `gather_facts: false` is configured).
- Discovered facts are stored in the JSON dictionary `ansible_facts` (e.g., `ansible_facts['distribution']`, `ansible_facts['memtotal_mb']`, `ansible_facts['default_ipv4']['address']`).

**Common Use Cases:**
1. **Dynamic Task Execution (OS-conditional logic):**
   ```yaml
   - name: Install Apache on Debian/Ubuntu
     ansible.builtin.apt:
       name: apache2
     when: ansible_facts['os_family'] == "Debian"

   - name: Install Apache on RHEL/CentOS
     ansible.builtin.dnf:
       name: httpd
     when: ansible_facts['os_family'] == "RedHat"
   ```
2. **Template Configuration Rendering:** Injecting system-specific hardware specs (CPU cores, IP addresses, total memory) into Jinja2 templates.
</details>

<details>
<summary><strong>● How do you handle errors or exceptions in Ansible playbooks?</strong></summary>

**Answer:**
Ansible provides multiple robust directives to handle failures and control flow:

1. **`ignore_errors: yes`:**
   Instructs Ansible to continue executing subsequent tasks even if the current task fails.

2. **`failed_when` Condition:**
   Overrides standard exit-code failure detection based on custom string matching or registered task outputs:
   ```yaml
   - name: Check service status
     ansible.builtin.command: /opt/app/status.sh
     register: app_status
     failed_when: "'CRITICAL' in app_status.stderr"
   ```

3. **`changed_when` Condition:**
   Controls whether a task reports a `changed` state (prevents unnecessary handler triggers).

4. **`block`, `rescue`, and `always` (Structured Exception Handling):**
   Similar to try/catch/finally in programming languages:
   ```yaml
   - name: Attempt application deployment
     block:
       - name: Deploy application release
         ansible.builtin.unarchive:
           src: /tmp/app-v2.tar.gz
           dest: /var/www/html/
       - name: Run database migration
         ansible.builtin.command: python manage.py migrate
     rescue:
       - name: Revert to previous release on failure
         ansible.builtin.command: /usr/local/bin/rollback.sh
       - name: Send Slack alert
         community.general.slack:
           msg: "Deployment failed on {{ inventory_hostname }}. Reverted successfully."
     always:
       - name: Cleanup temporary deployment artifacts
         ansible.builtin.file:
           path: /tmp/app-v2.tar.gz
           state: absent
   ```
</details>

<details>
<summary><strong>● How do you manage or control the order of execution for tasks in an Ansible playbook?</strong></summary>

**Answer:**
Task execution in Ansible is governed sequentially from top to bottom, but can be orchestrated using several structural constructs:

1. **Playbook Execution Phasing:**
   - `pre_tasks`: Run before any roles or standard tasks.
   - `roles`: Execute modular roles in listed order.
   - `tasks`: Standard task list.
   - `post_tasks`: Run after all tasks and notified handlers have executed.

2. **Batch Orchestration (`serial` and `strategy`):**
   - `strategy: linear` (default): All hosts execute Task 1 before any host proceeds to Task 2.
   - `strategy: free`: Each host runs through the playbook as fast as possible, independent of other hosts.
   - `serial: <count or percentage>`: Controls batch rolling execution across nodes.

3. **Execution Control Directives:**
   - `delegate_to`: Executes a task on a different machine (e.g., run a task on the database server or load balancer while iterating over webservers).
   - `run_once: true`: Executes a task only once on the first host in the group (e.g., executing a database migration).
</details>

<details>
<summary><strong>● Why do we use ad hoc commands in Ansible when playbooks are generally the preferred approach?</strong></summary>

**Answer:**
**Ad hoc commands** (`ansible <group> -m <module> -a "<args>"`) are quick, one-time commands executed via the CLI without writing a reusable YAML playbook.

**Why they are used:**
1. **Rapid Incident Triage & Inspection:** Instantly querying server state across 500 nodes during an incident:
   ```bash
   ansible webservers -m shell -a "uptime; free -m"
   ```
2. **Emergency Patching & Mass Service Restarts:**
   ```bash
   ansible all -m systemd -a "name=ntpd state=restarted" --become
   ```
3. **Connectivity Verification:**
   ```bash
   ansible all -m ping
   ```
4. **Ad-hoc File Distribution / User Management:** Copying an emergency script or adding a temporary developer SSH key without modifying Git-managed playbooks.
</details>

<details>
<summary><strong>● Suppose you need to update a web application running on 50 servers without causing any downtime for users — how would you approach this using Ansible?</strong></summary>

**Answer:**
This requires an orchestrated **Rolling Deployment** combining Ansible's `serial` batching, AWS Application Load Balancer target deregistration, application updating, and target reregistration.

**Architecture & Workflow:**
```
[ AWS Application Load Balancer (ALB) ]
        |
        +--- Batch 1 (10 servers): Deregister -> Update -> Health Check -> Reregister
        +--- Batch 2 (10 servers): Deregister -> Update -> Health Check -> Reregister
        +--- Batch 3 (10 servers): Deregister -> Update -> Health Check -> Reregister
        ...
```

**Production Playbook Implementation:**
```yaml
- name: Zero-Downtime Rolling Update
  hosts: webservers
  become: yes
  serial: "20%" # Updates 10 servers at a time (5 batches for 50 servers)
  max_fail_percentage: 0 # Halt deployment immediately if any single server fails

  tasks:
    - name: Deregister server from ALB Target Group
      amazon.aws.elb_target:
        target_group_arn: "arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/web-tg/abc"
        target_id: "{{ ansible_ec2_instance_id }}"
        state: absent
      delegate_to: localhost

    - name: Wait for existing connections to drain (Connection Draining)
      ansible.builtin.pause:
        seconds: 30

    - name: Stop application service
      ansible.builtin.systemd:
        name: webapp
        state: stopped

    - name: Deploy new application package
      ansible.builtin.unarchive:
        src: /opt/releases/app-v2.tar.gz
        dest: /var/www/webapp/

    - name: Start updated application service
      ansible.builtin.systemd:
        name: webapp
        state: started
        enabled: yes

    - name: Verify local application health check endpoint
      ansible.builtin.uri:
        url: "http://localhost:8080/health"
        status_code: 200
      register: health_check
      retries: 6
      delay: 5
      until: health_check.status == 200

    - name: Reregister server into ALB Target Group
      amazon.aws.elb_target:
        target_group_arn: "arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/web-tg/abc"
        target_id: "{{ ansible_ec2_instance_id }}"
        state: present
      delegate_to: localhost

    - name: Wait for instance to become healthy in ALB
      amazon.aws.elb_target_info:
        target_group_arn: "arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/web-tg/abc"
        target_id: "{{ ansible_ec2_instance_id }}"
      register: tg_info
      until: tg_info.target_health_descriptions[0].target_health.state == 'healthy'
      retries: 10
      delay: 5
      delegate_to: localhost
```
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself, describe your day-to-day work in your current organization, and share the achievements from your previous organization or projects?

#### 【 OTHER 】

<details>
<summary><strong>● Are you working with Python?</strong></summary>

**Answer:**
Yes, I actively work with Python 3 for cloud infrastructure automation, CI/CD scripting, and custom tooling:

- Developing automation scripts with **Boto3** to automate AWS operations (lifecycle cleanup of untagged EBS snapshots, automated AMI rotation, and auditing S3 bucket security policies).
- Writing CLI utilities to interact with REST APIs for Jira, GitHub, and Jenkins.
- Writing test validation scripts and Kubernetes custom controllers/operators using the Python Kubernetes client.
</details>

<details>
<summary><strong>● How do you resolve package dependencies in Python?</strong></summary>

**Answer:**
In enterprise production environments, Python package dependencies are managed through virtual environments and deterministic dependency locking:

1. **Virtual Environments (`venv`):**
   Isolates dependencies per project to prevent conflicts with the system Python interpreter:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Deterministic Locking with `pip-tools` or `Poetry`:**
   - Storing dependencies in `requirements.in` and generating a pinned `requirements.txt` with SHA256 hashes:
     ```bash
     pip-compile --generate-hashes requirements.in
     pip install -r requirements.txt
     ```
   - Modern enterprise stacks leverage **Poetry** or **uv**, which maintain a lockfile (`poetry.lock`) resolving recursive sub-dependencies to exact versions.

3. **Handling Conflicting Dependencies:**
   - Use `pip check` to verify installed packages have compatible dependencies.
   - Use `pipdeptree` to inspect the visual dependency tree and identify package conflicts.
</details>

<details>
<summary><strong>● How do you write to or read from a file in Python?</strong></summary>

**Answer:**
In Python, file I/O operations must always be performed using the **`with` statement context manager**. This guarantees that file descriptors are properly closed and flushed even if exceptions occur.

**Reading a file safely:**
```python
# Reading entire file or line-by-line
try:
    with open('/var/log/app.log', 'r', encoding='utf-8') as f:
        for line in f:
            if 'ERROR' in line:
                print(line.strip())
except FileNotFoundError:
    print("Error: The log file was not found.")
except PermissionError:
    print("Error: Insufficient read permissions.")
```

**Writing to a file safely:**
```python
# 'w' for overwriting, 'a' for appending
data = ["server1=active
", "server2=maintenance
"]
with open('/tmp/server_status.txt', 'w', encoding='utf-8') as f:
    f.writelines(data)
```
</details>

<details>
<summary><strong>● How do you handle exceptions in Python?</strong></summary>

**Answer:**
Python uses structured exception handling through the `try`, `except`, `else`, and `finally` blocks:

```python
import sys
import logging

logging.basicConfig(level=logging.INFO)

def read_cluster_config(config_path):
    file_obj = None
    try:
        logging.info(f"Opening config file: {config_path}")
        file_obj = open(config_path, 'r')
        data = file_obj.read()
        return data
    except FileNotFoundError as e:
        logging.error(f"Configuration file missing: {e}")
        raise
    except PermissionError as e:
        logging.error(f"Access denied to configuration: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")
        sys.exit(1)
    else:
        logging.info("Configuration read successfully with zero errors.")
    finally:
        if file_obj:
            file_obj.close()
            logging.info("File handle closed.")
```

**Best Practices:**
- Catch specific exceptions (`FileNotFoundError`, `ValueError`) rather than a bare `except:`.
- Re-raise exceptions using `raise` if the error cannot be safely recovered at the current abstraction layer.
- Ensure resources are cleaned up using `finally` or context managers.
</details>
</details>

<details open>
<summary><h3>Level 2</h3></summary>

#### 【 LINUX 】

<details>
<summary><strong>● How would you rate your proficiency and experience with Linux?</strong></summary>

**Answer:**
I rate my proficiency as an **8.5 out of 10 (Advanced / Senior)**. I have over 6 years of deep, daily hands-on experience managing enterprise Linux distributions (RHEL, CentOS, Rocky Linux, Ubuntu Server, Amazon Linux).

**Key Competencies:**
- **Troubleshooting & Performance Tuning:** Analyzing bottlenecked systems using `top`, `htop`, `vmstat`, `iostat`, `strace`, `lsof`, `tcpdump`, and `journalctl`.
- **Storage Management:** Configuring LVM (PV, VG, LV), disk partitioning, resizing filesystems (`xfs_growfs`, `resize2fs`), and managing NFS/CIFS mounts.
- **Networking & Security:** Managing iptables, `firewalld`, SELinux policies, network namespaces, SSH tunneling, and open port diagnostics via `ss` and `netstat`.
- **Process & Service Lifecycle:** Writing Systemd unit files, managing runlevels/targets, and handling process signals.
</details>

<details>
<summary><strong>↳ Follow-up: How do you copy a file from one server to another server using Linux commands?</strong></summary>

**Answer:**
Several commands can be used depending on file size, directory structure, and performance requirements:

1. **`rsync` (Recommended for Production):**
   Fast, transfers only deltas (differences), preserves permissions and timestamps, and allows resuming interrupted transfers:
   ```bash
   rsync -avzP -e "ssh -p 22" /local/path/app.tar.gz user@remote-host:/remote/path/
   ```
   - `-a`: Archive mode (preserves permissions, ownership, timestamps, symlinks).
   - `-v`: Verbose output.
   - `-z`: Compresses data during transit.
   - `-P`: Shows progress bar and allows resumed transfers.

2. **`scp` (Secure Copy Protocol):**
   Standard SSH-based copy for simple, single-file transfers:
   ```bash
   scp -P 22 /local/path/file.txt user@remote-host:/remote/path/
   ```

3. **`sftp`:** Interactive or batch scriptable secure file transfer.
</details>

<details>
<summary><strong>↳ Follow-up: How do you create a 0-byte (empty) file in Linux?</strong></summary>

**Answer:**
There are multiple standard methods:

1. **Using `touch` (Most common):**
   ```bash
   touch emptyfile.txt
   ```
   *(Note: If the file already exists, `touch` updates its access/modification timestamp without overwriting contents).*

2. **Using Shell Redirection (`>`):**
   ```bash
   > emptyfile.txt
   ```
   *(If the file exists, this immediately truncates it to 0 bytes).*

3. **Using `truncate`:**
   ```bash
   truncate -s 0 emptyfile.txt
   ```

4. **Redirecting `/dev/null`:**
   ```bash
   cp /dev/null emptyfile.txt
   # or
   cat /dev/null > emptyfile.txt
   ```
</details>

<details>
<summary><strong>↳ Follow-up: How do you create a file in Linux with the default file permissions?</strong></summary>

**Answer:**
In Linux, default permissions for newly created files are determined by subtracting the active **`umask`** (user file-creation mode mask) from the maximum base permission:

- **Default base permission for files:** `0666` (`rw-rw-rw-`)
- **Default base permission for directories:** `0777` (`rwxrwxrwx`)

**How it works:**
- If the current shell umask is `0022`:
  - New file permission = `0666 & ~0022` = **`0644` (`-rw-r--r--`)**
  - Owner: Read/Write; Group: Read; Others: Read.
- If the current shell umask is `0027`:
  - New file permission = `0666 & ~0027` = **`0640` (`-rw-r-----`)**

Creating the file with standard commands (`touch newfile.txt` or `echo "" > newfile.txt`) will automatically create the file with the default permissions dictated by the active shell's `umask`. You can inspect or modify the mask using the `umask` command (e.g., `umask 022`).
</details>

#### 【 IAC 】

<details>
<summary><strong>● How many years of experience do you have working with Ansible?</strong></summary>

**Answer:**
I have over **5 years** of hands-on experience developing and maintaining Ansible automation across production environments:

- Architecting reusable, modular **Ansible Roles** and Collections following DRY principles.
- Automating OS baselining, CIS benchmark security hardening, and vulnerability patching across large Linux server fleets (500+ nodes).
- Orchestrating zero-downtime rolling application deployments integrated with Jenkins and GitHub Actions.
- Managing cloud resources using Ansible dynamic inventory plugins (`aws_ec2`) and automating Windows hosts via WinRM over HTTPS.
</details>

<details>
<summary><strong>↳ Follow-up: Have you done any automation work using Ansible?</strong></summary>

**Answer:**
Yes, I have led several major enterprise automation initiatives using Ansible:

1. **Automated Server Provisioning & Hardening:** Built a unified provisioning pipeline that configures newly launched EC2 instances with standard users, SSH hardening, NTP/chrony sync, CloudWatch agent, and Falco security monitoring.
2. **Zero-Downtime Microservice Rolling Updates:** Automated application deployments with connection draining from load balancers, health checking, and progressive traffic cutover.
3. **Automated Disaster Recovery & Backup Verification:** Scheduled playbooks to automate database snapshot verification, log rotation, and restoring backups to isolated test environments.
</details>

<details>
<summary><strong>● Can you highlight a specific use case or sample automation you implemented using Ansible or Python?</strong></summary>

**Answer:**
**Use Case:** Automated Fleet-Wide Security Kernel Patching and Rolling Reboot Orchestration across a 100+ node production cluster with zero service interruption.

**Architecture:**
- Used an Ansible playbook executed via Jenkins.
- Target instances were grouped by AWS Auto Scaling Groups (ASGs).
- For each node:
  1. The playbook puts the ASG node into `Standby` status using AWS CLI / Ansible AWS collection.
  2. Waits for active connection draining.
  3. Applies OS security updates via `yum`/`apt`.
  4. Checks if a kernel reboot is required (`/var/run/reboot-required`).
  5. If required, triggers a controlled reboot using `ansible.builtin.reboot` with test command validation.
  6. Restores the ASG node from `Standby` to `InService` and verifies health checks before moving to the next node.
</details>

<details>
<summary><strong>↳ Follow-up: For that automation example using Ansible or Python, what was the problem statement or issue you were solving, and what kind of automation did you implement to address it?</strong></summary>

**Answer:**
- **Problem Statement:** SecOps mandated applying monthly Linux kernel CVE patches within a 7-day SLA. Previously, engineers manually SSHed into individual servers after business hours, causing human error, occasional multi-node outages, and severe engineering toil (20+ manual hours per month).
- **Solution Implemented:**
  - Automated the entire patch and reboot cycle using an Ansible playbook integrated with AWS APIs.
  - Implemented `serial: 1` per availability zone to prevent capacity drop below the required threshold.
  - Added automated pre-checks (disk space > 2GB, cluster consensus) and post-checks (systemd service status, HTTP health endpoint response).
  - Reduced patching time from 20 hours of manual effort to a 45-minute scheduled Jenkins job with zero outages.
</details>

<details>
<summary><strong>↳ Follow-up: In the example where an Ansible playbook was triggered from Jenkins, what kind of playbook did you write, and have you written any Ansible playbooks completely from scratch?</strong></summary>

**Answer:**
Yes, I have written numerous production playbooks completely from scratch, including their directory structure, roles, tasks, handlers, and templates:

In the Jenkins-triggered pipeline, the playbook was an **orchestration and deployment playbook**. In the `Jenkinsfile`, credentials were dynamically injected:
```groovy
stage('Run Ansible Hardening') {
    steps {
        ansiblePlaybook(
            playbook: 'playbooks/site.yml',
            inventory: 'inventory/aws_ec2.yaml',
            credentialsId: 'ansible-ssh-key',
            extraVars: [target_env: 'production', release_version: "${BUILD_NUMBER}"]
        )
    }
}
```
The playbook included modular roles: `common` (users, SSH), `security` (fail2ban, iptables, umask), and `app_deploy` (artifact extraction, systemd service management).
</details>

<details>
<summary><strong>↳ Follow-up: What specific types of Ansible playbooks have you written?</strong></summary>

**Answer:**
I have authored diverse playbooks categorized across operational needs:

1. **Configuration Management & Hardening:** Enforcing CIS Level 1 benchmarks, managing sudoers, disabling unneeded services, and configuring auditd.
2. **Application Deployment & Release:** Pulling container images or compiling binaries, provisioning configuration templates (`.j2`), running DB migrations, and reloading systemd daemons.
3. **Zero-Downtime Rolling Deployment:** Managing load balancer registration/deregistration using `serial` batches.
4. **Disaster Recovery & Backup Automation:** Automating database dump creation, compressing logs, and uploading encrypted archives to S3 buckets.
5. **Monitoring Agent Provisioning:** Installing and configuring Datadog, Prometheus node-exporter, and Fluent Bit log forwarders across mixed operating systems.
</details>

<details>
<summary><strong>↳ Follow-up: Can you demonstrate how you write an Ansible playbook from scratch, for example by typing a sample playbook in an editor?</strong></summary>

**Answer:**
Here is a complete, production-grade Ansible playbook written from scratch that deploys and configures a secure Nginx reverse proxy with Jinja2 templating and handlers:

```yaml
---
- name: Deploy and Configure Secure Nginx Web Server
  hosts: webservers
  become: yes
  vars:
    nginx_port: 80
    server_name: api.company.internal
    backend_app_url: "http://127.0.0.1:8080"

  pre_tasks:
    - name: Update apt repository cache
      ansible.builtin.apt:
        update_cache: yes
        cache_valid_time: 3600
      when: ansible_facts['os_family'] == "Debian"

  tasks:
    - name: Install Nginx package
      ansible.builtin.package:
        name: nginx
        state: present

    - name: Deploy Nginx reverse proxy virtual host configuration
      ansible.builtin.template:
        src: templates/nginx_vhost.conf.j2
        dest: /etc/nginx/conf.d/vhost.conf
        owner: root
        group: root
        mode: '0644'
      notify: Reload Nginx

    - name: Ensure Nginx service is enabled and started
      ansible.builtin.systemd:
        name: nginx
        state: started
        enabled: yes

    - name: Verify Nginx is listening on designated port
      ansible.builtin.wait_for:
        port: "{{ nginx_port }}"
        timeout: 10

  handlers:
    - name: Reload Nginx
      ansible.builtin.systemd:
        name: nginx
        state: reloaded
```
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● What monitoring or observability tools are you familiar with, and how have you used them?</strong></summary>

**Answer:**
I have practical experience across enterprise monitoring tools mapped to operational responsibilities:

1. **Prometheus & Grafana:**
   - Deployed **kube-prometheus-stack** via Helm in Kubernetes.
   - Built custom dashboards tracking cluster capacity, node saturation, pod restart rates, and ingress HTTP 5xx errors.
   - Configured **Alertmanager** routing alerts to Slack channels and PagerDuty on-call engineers.

2. **AWS CloudWatch:**
   - Configured CloudWatch Alarms on ALB target response times, RDS CPU & Freeable Memory, and billing metrics.
   - Streamed application logs into CloudWatch Logs with metric filters tracking application error frequencies.

3. **ELK / OpenSearch Stack:**
   - Ingested container stdout/stderr logs via Fluent Bit DaemonSets.
   - Used Kibana to build query dashboards for developers to trace error stack traces during incidents.

4. **Datadog:**
   - Implemented APM tracing across Java and Go services to isolate high database latency queries and slow external API calls.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Are you familiar with SRE (Site Reliability Engineering), and can you explain what it is?</strong></summary>

**Answer:**
**Site Reliability Engineering (SRE)** is an engineering discipline pioneered by Google that applies software engineering practices to infrastructure and operations problems. As Ben Treynor Sloss defined it: *"SRE is what happens when you ask a software engineer to design an operations team."*

**Core SRE Pillars:**
1. **Service Level Indicators (SLIs):** Quantifiable metrics of service performance (e.g., request latency, error rate).
2. **Service Level Objectives (SLOs):** Target reliability level agreed upon with business stakeholders (e.g., 99.9% successful requests over 30 days).
3. **Error Budgets:** The allowable room for unreliability (`100% - SLO`). If the error budget is healthy, teams ship new features rapidly. If the error budget is exhausted, releases freeze and engineering focuses on stability.
4. **Toil Reduction:** SRE teams actively limit repetitive, manual, non-creative operational work ("toil") to under 50% of their time, using the remaining time to engineer automation.
5. **Blameless Postmortems:** Conducting incident post-mortems focused on systemic root causes rather than blaming individuals.
</details>

<details>
<summary><strong>↳ Follow-up: Have you implemented any SRE best practices in your current role?</strong></summary>

**Answer:**
Yes, I led the implementation of several core SRE practices:

1. **Defined SLIs and SLOs for Critical APIs:**
   - Established an SLO of **99.9% availability** and **p95 latency < 300ms** for the customer checkout service.
   - Configured Prometheus alerting based on **Multi-Window Multi-Burn-Rate** alert rules to catch rapid budget consumption without generating alert fatigue.

2. **Automated Error Budget Policy:**
   - Integrated error budget tracking into our deployment pipeline: if the 30-day rolling error budget dropped below 10%, non-critical production deployments were automatically blocked until reliability engineering resolved the defect.

3. **Toil Elimination Initiatives:**
   - Replaced manual database credential rotations and server patching with automated Lambda functions and Ansible playbooks, reclaiming ~15 engineering hours weekly.

4. **Blameless Postmortem Culture:**
   - Standardized post-incident review templates detailing timeline, root causes (Five Whys), corrective action items with owners, and Jira tickets for permanent remediation.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you please introduce yourself?

● **Candidate Introduction:** What is your current CTC (compensation)?

● **Candidate Introduction:** Which company are you currently working for?

↳ **Candidate Introduction:** *Are you currently serving your notice period, have you already left the company, or are you still actively working there?*

↳ **Candidate Introduction:** *Do you currently have any other job offer in hand?*

↳ **Candidate Introduction:** *What is your salary expectation for this role?*
</details>
</details>

<details open>
<summary><h2>🏢 LTM</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 LINUX 】

<details>
<summary><strong>● How comfortable are you working with the Windows operating system?</strong></summary>

**Answer:**
I am highly comfortable managing enterprise **Windows Server** (2016, 2019, 2022) environments alongside Linux:

- **Administration & Automation:** Experienced in PowerShell scripting, managing Windows Services, Registry, Event Viewer, and Windows Task Scheduler.
- **Remote Orchestration:** Configuring **WinRM** (Windows Remote Management) over HTTPS (port 5986) with SSL certificates to enable automated provisioning and configuration management via Ansible.
- **Enterprise Integrations:** Managing **IIS** web server configurations, application pools, and integrating Windows instances with Active Directory (AD) domains.
- **Package Management:** Automating software installations via **Chocolatey** and AWS Systems Manager (SSM) Run Command.
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● If a Python script runs successfully when executed manually but fails when run through Jenkins, how would you debug and troubleshoot the issue?</strong></summary>

**Answer:**
This is a classic environment discrepancy issue between an interactive human shell and a non-interactive service execution. My systematic debugging approach:

1. **User Identity & Permissions:**
   - Manual runs execute as the logged-in user (e.g., `ec2-user` or `ubuntu`), whereas Jenkins runs as the `jenkins` system user.
   - Debug: Run `whoami` and `id` in the Jenkins shell. Check if `jenkins` has read/write permissions to files, output directories, or SSH keys.

2. **Environment Variables & PATH Discrepancy:**
   - Interactive shells load `~/.bashrc`, `~/.bash_profile`, and export variables (e.g., `AWS_PROFILE`, `VAULT_ADDR`). Jenkins runs non-interactively with a barebones `PATH`.
   - Debug: Print the environment in Jenkins using `sh 'env'` or `sh 'printenv'` and compare against the terminal environment.

3. **Python Interpreter & Virtual Environment:**
   - The manual execution might be using a Python virtual environment (`.venv`) or a custom Python 3 path, while Jenkins calls the OS default (`/usr/bin/python`).
   - Debug: Execute `which python3` and `python3 --version` in the Jenkinsfile. Always use an explicit virtualenv inside the pipeline:
     ```groovy
     sh '''
       python3 -m venv .venv
       source .venv/bin/activate
       pip install -r requirements.txt
       python3 script.py
     '''
     ```

4. **Missing Credentials & TTY Hangs:**
   - Verify cloud credentials (AWS IAM role or Jenkins credentials binding).
   - Check if the script prompts for user input (stdin), causing Jenkins to hang indefinitely due to absence of a pseudo-TTY (`TERM`).
</details>

#### 【 IAC 】

<details>
<summary><strong>● If you had 200 Windows servers and needed to automate daily log cleanup on all of them, how would you approach it?</strong></summary>

**Answer:**
To manage 200 Windows servers reliably and consistently, I would use **Ansible** leveraging the **`community.windows`** and **`ansible.windows`** collections over WinRM/HTTPS or **AWS Systems Manager (SSM) State Manager**:

1. **Develop a Modular PowerShell Cleanup Script:**
   The script scans target log directories (e.g., `C:\inetpub\logs\LogFiles`, application logs) and removes files older than 14 days while logging deleted file counts:
   ```powershell
   $LogPath = "C:\inetpub\logs\LogFiles"
   $DaysBack = 14
   $CutoffDate = (Get-Date).AddDays(-$DaysBack)
   Get-ChildItem -Path $LogPath -Recurse -File | Where-Object { $_.LastWriteTime -lt $CutoffDate } | Remove-Item -Force -Verbose
   ```

2. **Ansible Playbook Implementation:**
   Using the `ansible.windows.win_scheduled_task` module to deploy and schedule this cleanup across all 200 servers:
   ```yaml
   - name: Deploy Daily Log Cleanup Scheduled Task
     hosts: win_servers
     tasks:
       - name: Create Scripts Directory
         ansible.windows.win_file:
           path: C:\Scripts
           state: directory

       - name: Deploy Log Cleanup Script
         ansible.windows.win_copy:
           src: files/Clean-Logs.ps1
           dest: C:\Scripts\Clean-Logs.ps1

       - name: Create Daily Scheduled Task
         community.windows.win_scheduled_task:
           name: "DailyLogCleanup"
           description: "Deletes application and IIS logs older than 14 days"
           actions:
             - path: powershell.exe
               arguments: -ExecutionPolicy Bypass -File C:\Scripts\Clean-Logs.ps1
           triggers:
             - type: daily
               start_boundary: '2026-01-01T02:00:00'
           username: SYSTEM
           state: present
   ```
</details>

<details>
<summary><strong>↳ Follow-up: In that log cleanup automation scenario, how would you schedule the Ansible playbook to run automatically?</strong></summary>

**Answer:**
The automated execution of the Ansible playbook can be scheduled using two production architectures:

1. **Ansible Automation Platform (AAP) / AWX (Recommended):**
   - Configure a **Job Template** referencing the Git repository, the dynamic inventory of 200 Windows hosts, and machine credentials.
   - Configure a native **AWX Schedule** (e.g., Daily at 02:00 UTC) with notification webhooks sent to Slack/Teams upon completion or failure.

2. **Jenkins Cron-Triggered Pipeline:**
   - Configure a Declarative Jenkinsfile triggered via a cron schedule:
     ```groovy
     pipeline {
         agent { label 'ansible-agent' }
         triggers {
             cron('0 2 * * *') // Runs daily at 2:00 AM
         }
         stages {
             stage('Execute Windows Log Cleanup') {
                 steps {
                     ansiblePlaybook(
                         playbook: 'playbooks/windows_cleanup.yml',
                         inventory: 'inventories/production_windows.ini',
                         credentialsId: 'winrm-admin-creds'
                     )
                 }
             }
         }
     }
     ```
</details>

<details>
<summary><strong>↳ Follow-up: Since crontab doesn't work on Windows, how would you schedule the log cleanup task specifically on Windows servers?</strong></summary>

**Answer:**
On Windows servers, the direct equivalent of Linux `crontab` is the **Windows Task Scheduler**.

**Implementation Options:**
1. **Automated via Ansible:**
   Use the `community.windows.win_scheduled_task` module to define task triggers (daily, weekly, at startup), executable binary (`powershell.exe`), script arguments, and run level (`highestAvailable`). Running under the `SYSTEM` account ensures it executes without requiring an interactive user login.
2. **Automated via PowerShell directly:**
   ```powershell
   $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File C:\Scripts\Clean-Logs.ps1"
   $Trigger = New-ScheduledTaskTrigger -Daily -At 2am
   $Principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest
   Register-ScheduledTask -TaskName "DailyLogCleanup" -Action $Action -Trigger $Trigger -Principal $Principal
   ```
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● What AWS services have you worked on?</strong></summary>

**Answer:**
I have broad production experience across AWS core and platform services:

- **Compute:** EC2, Auto Scaling Groups, AWS Lambda, ECS (Fargate), EKS (Elastic Kubernetes Service).
- **Networking & Content Delivery:** VPC, Subnets, Route Tables, NAT Gateways, Internet Gateways, Application Load Balancers (ALB), Network Load Balancers (NLB), Route 53, CloudFront, Transit Gateway, VPC Endpoints (PrivateLink).
- **Storage & Database:** S3, EBS, EFS, RDS (PostgreSQL, MySQL, Aurora Multi-AZ), DynamoDB, ElastiCache (Redis).
- **Security & Governance:** IAM, AWS Organizations, SCPs, AWS KMS, AWS Secrets Manager, Systems Manager (SSM), AWS WAF, Security Groups, NACLs, AWS Shield.
- **Monitoring & Observability:** CloudWatch (Metrics, Alarms, Logs), CloudTrail, EventBridge.
- **Infrastructure as Code:** Terraform with AWS Provider, AWS CloudFormation.
</details>

<details>
<summary><strong>● Have you worked with AWS Security Groups and Network ACLs (NACLs)?</strong></summary>

**Answer:**
Yes, I work with both daily to enforce **Defense-in-Depth** multi-layer network security in AWS:

| Feature | Security Group (SG) | Network ACL (NACL) |
| :--- | :--- | :--- |
| **Operating Layer** | Operates at the **Instance / ENI level** (virtual firewall) | Operates at the **Subnet boundary level** |
| **State Nature** | **Stateful** (Return traffic is automatically allowed regardless of inbound rules) | **Stateless** (Return traffic must be explicitly allowed in both directions) |
| **Rule Types** | Supports **ALLOW rules only** | Supports both **ALLOW and DENY rules** |
| **Rule Evaluation** | All rules are evaluated simultaneously before granting access | Rules are processed sequentially in **numerical order** (lowest number first) |
| **Default Behavior** | Denies all inbound, allows all outbound | Default NACL allows all traffic; Custom NACL denies all traffic until rules are added |
</details>

<details>
<summary><strong>↳ Follow-up: Can you create explicit deny rules in an AWS Security Group?</strong></summary>

**Answer:**
**No, you cannot create explicit DENY rules in an AWS Security Group.**

Security Groups are strictly permissive (allow-only). Any traffic that is not explicitly matched by an allow rule is **implicitly denied**.

**How to implement explicit deny rules:**
1. **Network ACLs (NACLs):** If you must block malicious IP addresses or specific CIDR ranges, configure an explicit `DENY` rule in the subnet's NACL with a lower rule number (e.g., Rule `50: DENY TCP from 203.0.113.50/32` evaluated before Rule `100: ALLOW ALL`).
2. **AWS WAF (Web Application Firewall):** For Layer 7 HTTP/HTTPS traffic on an Application Load Balancer or CloudFront, use IP Match conditions in WAF to block specific IPs or geographic regions.
</details>

<details>
<summary><strong>● If you have an application hosted on an EC2 instance that is inaccessible, how would you troubleshoot the issue?</strong></summary>

**Answer:**
I apply a systematic, OSI-model-based troubleshooting process dividing the problem into three tiers: **Cloud Infrastructure**, **Operating System/Network**, and **Application Process**.

1. **AWS Infrastructure Tier:**
   - Check EC2 Console: Are **System Status Checks** and **Instance Status Checks** passing (2/2)?
   - Verify Security Groups: Is the application port (e.g., 80, 443, 8080) allowed from the client source IP?
   - Verify Route Tables & Subnet: If public, does the route table route `0.0.0.0/0` to an Internet Gateway (`igw-xxx`)? Does the EC2 instance have a Public IP / Elastic IP?
   - Check Subnet NACLs: Ensure both Inbound and Outbound ephemeral ports (`1024–65535`) are not blocked.

2. **OS & Host Tier (Connect via SSH or AWS SSM Session Manager):**
   - Check if the application process is running:
     ```bash
     systemctl status <service_name>
     ps aux | grep <process_name>
     ```
   - Check listening ports and local sockets:
     ```bash
     ss -tulpn | grep :<port>
     # Verify if the process binds to 0.0.0.0 instead of 127.0.0.1 (localhost only)
     ```
   - Inspect host firewalls: Check `iptables -L -n -v` or `ufw status` (Linux) or Windows Defender Firewall.

3. **Application & Resource Tier:**
   - Check disk space: `df -h` (out-of-disk condition prevents log writes and crashes web servers).
   - Check memory & CPU: `free -m`, `top` (OOM Killer might have terminated the application).
   - Inspect application logs: `tail -f /var/log/app/error.log` or `journalctl -u <service> -n 100`.
</details>

<details>
<summary><strong>↳ Follow-up: Can you walk through your step-by-step troubleshooting process for this inaccessible application scenario?</strong></summary>

**Answer:**
Here is the step-by-step diagnostic workflow:

```
[ Step 1: AWS Console Verification ]
  |-- Instance Status: 2/2 Checks Passed?
  |     |-- No -> Check System Logs / Reboot / Recover
  |     +-- Yes -> Proceed
  |-- Security Group: Is Port 80/443 open to client CIDR?
  |-- Subnet Route Table: IGW attached? (Public) or NAT Gateway? (Private)
  +-- NACL: Inbound and Outbound Ephemeral rules permitted?

[ Step 2: Connectivity Testing ]
  |-- Test DNS resolution: dig app.company.com
  |-- Test TCP Handshake: nc -zv <public-ip> 443 or curl -Iv https://app.company.com
  +-- Result: Connection Refused (Host reached, port closed) vs Connection Timeout (Firewall drop)

[ Step 3: Server Access via AWS Systems Manager (SSM) ]
  |-- Execute: systemctl status myapp (Confirm service state)
  |-- Execute: ss -tulpn | grep 8080 (Ensure binding to 0.0.0.0:8080)
  |-- Execute: curl -Iv http://127.0.0.1:8080 (Local loopback verification)
  +-- If loopback fails: Issue is internal application crash or failed database connection
```
</details>

<details>
<summary><strong>● How do you take backups of your infrastructure on AWS?</strong></summary>

**Answer:**
Enterprise AWS backup architectures combine automated orchestration services with Infrastructure-as-Code state persistence:

1. **Centralized Policy-Based Backups via AWS Backup:**
   - Define a central **Backup Plan** with automated lifecycle schedules (e.g., daily backups at 01:00 UTC, retained for 30 days, transitioned to Cold Storage after 90 days).
   - Backs up EBS volumes, RDS databases, DynamoDB tables, EFS filesystems, and EC2 instances natively.
   - Enables **Cross-Region Backup** and **Cross-Account Backup** (to a dedicated Disaster Recovery account) protected by **AWS Backup Vault Lock** (WORM compliance preventing ransomware deletion).

2. **Amazon Data Lifecycle Manager (DLM):**
   - Automatically manages scheduled snapshots of EBS volumes and EBS-backed AMIs based on instance tags (`Backup=Daily`).

3. **Database-Specific Backups:**
   - **RDS / Aurora:** Automated daily snapshots with continuous write-ahead log shipping enabling Point-In-Time Recovery (PITR) to any second within the retention window (up to 35 days).

4. **Infrastructure as Code (IaC):**
   - Terraform configurations stored in Git, enabling complete re-provisioning of cloud infrastructure from scratch.
</details>

<details>
<summary><strong>↳ Follow-up: You mentioned EBS volumes being attached — what did you mean by that, and what are they attached to?</strong></summary>

**Answer:**
**Elastic Block Store (EBS)** is AWS's high-performance block storage service. 

- **What they are attached to:** An EBS volume is attached over a dedicated storage network to an **Amazon EC2 instance**, where it presents itself to the operating system as a physical raw block device (e.g., `/dev/xvda` for the root partition, `/dev/xvdf` or `/dev/nvme1n1` for secondary data disks).
- **Attachment Characteristics:**
  - EBS volumes reside in a specific **Availability Zone (AZ)** and can only be attached to EC2 instances in that identical AZ.
  - While standard EBS volumes are attached to a single EC2 instance at a time, EBS **Multi-Attach** (supported on `io1`/`io2` volume types) allows concurrent read/write attachment to up to 16 Nitro-based EC2 instances for clustered applications.
</details>

<details>
<summary><strong>↳ Follow-up: How do you take backups of your EBS volumes specifically?</strong></summary>

**Answer:**
EBS backups are captured as **EBS Snapshots**, which are point-in-time, crash-consistent (or application-consistent), incremental backups stored securely in Amazon S3:

1. **Incremental Snapshot Mechanism:**
   - The initial snapshot copies all allocated blocks.
   - Subsequent snapshots save only the modified blocks (deltas) since the last snapshot, optimizing backup storage costs and speed.

2. **Creation Methods:**
   - **AWS Backup / Amazon DLM (Production Standard):** Policy-based tag targeting (`tag:Backup=True`) that creates snapshots daily with automated deletion after retention expiry.
   - **AWS CLI / Boto3 Automation:**
     ```bash
     aws ec2 create-snapshot        --volume-id vol-0123456789abcdef0        --description "Manual snapshot before OS upgrade"        --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Name,Value=prod-db-backup}]'
     ```

3. **Consistency Best Practice:**
   - For transactional databases, flush dirty buffers to disk (`sync`) or freeze the filesystem (`xfs_freeze`) prior to snapshot creation to ensure application-consistent recovery.
</details>

<details>
<summary><strong>● In your enterprise environment, is all your infrastructure deployed in a public subnet or a private subnet?</strong></summary>

**Answer:**
In our enterprise production environments, **100% of compute workloads, microservices, and databases are deployed in Private Subnets**.

**Architecture Blueprint:**
- **Private Subnets (RFC 1918 non-routable IPs):**
  - Host all EC2 instances, EKS worker nodes, RDS databases, and ElastiCache clusters.
  - Instances have **no public IP addresses** and no direct route to an Internet Gateway.
  - Outbound internet access (for package updates and API calls) is routed through high-availability **NAT Gateways** located in public subnets.
- **Public Subnets:**
  - Strictly limited to internet-facing boundary components: **Application Load Balancers (ALB)**, NAT Gateways, and public Bastion/VPN gateways.
  - All external user traffic terminates at the ALB in the public subnet, which forwards requests over private AWS network links to target instances in private subnets.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● If you received 10,000 alert emails generated from AWS overnight, what would be your steps when you come in the next morning to handle this situation?</strong></summary>

**Answer:**
Receiving 10,000 alert emails is a critical symptom of **Alert Fatigue** and improper notification routing. My step-by-step actions:

1. **Immediate Triage & Active Outage Assessment (First 10 minutes):**
   - Do **not** read individual emails.
   - Check real-time production dashboards (CloudWatch, Datadog, Grafana) and incident management tools (PagerDuty) to determine if there is an **active, customer-impacting Sev-1/Sev-2 outage**.
   - Check key health signals: Load Balancer 5xx errors, database connectivity, and synthetic ping checks.

2. **Categorize and Cluster the Alerts:**
   - Use mailbox filters or a quick Python script to parse email headers and group by:
     - Alarm Name / Metric (e.g., was it a single flapping metric generating an alarm every 60 seconds across 200 servers?).
     - AWS Service / Resource (e.g., RDS storage running low or an Auto Scaling Group scale-in event).

3. **Identify Root Cause of the Flapping / Storm:**
   - Pinpoint the event that triggered the surge: e.g., a batch job exhausted disk I/O, triggering CPU, latency, and health-check alarms across all downstream dependencies.

4. **Remediate the Monitoring Architecture (Prevent Recurrence):**
   - **Eliminate Raw Email Routing:** Disconnect SNS email subscriptions for raw alarms. Route alarms to **EventBridge -> PagerDuty / Opsgenie** for deduplication and incident grouping.
   - **Tune CloudWatch Alarm Thresholds:** Configure `DatapointsToAlarm` with `M out of N` evaluation (e.g., breach 3 consecutive times in 5 minutes) rather than `1 out of 1` to ignore transient spikes.
   - **Implement Composite Alarms:** Use AWS CloudWatch Composite Alarms to alert only when multiple related conditions occur simultaneously (e.g., `High CPU AND High 5xx Latency`).
</details>

#### 【 SECURITY 】

<details>
<summary><strong>● Is your application connected to an on-premises Active Directory (AD)?</strong></summary>

**Answer:**
Yes, in hybrid cloud enterprise architectures, our AWS workloads integrate with on-premises Active Directory (AD) for centralized identity and access management:

- **Connectivity Layer:** Secure hybrid connectivity established using **AWS Direct Connect (DX)** with an automated failover **AWS Site-to-Site VPN** terminated at an AWS Transit Gateway (TGW).
- **Integration Mechanism:**
  1. **AWS Directory Service (AD Connector):** A directory gateway that proxies authentication requests back to on-premises domain controllers without caching credentials in AWS.
  2. **Dedicated AWS Domain Controllers:** Running secondary read-only domain controllers (RODC) or writable domain controllers on EC2 in dedicated private subnets for low-latency domain join and Kerberos authentication.
  3. **IAM Identity Center (AWS SSO):** Synchronizing Active Directory users and security groups into AWS via SCIM protocol for Single Sign-On across AWS multi-account environments.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** What is your understanding of the job description you applied for, and what do you think the role requires?

● **Candidate Introduction:** Can you please introduce yourself, including your professional background and experience?

↳ **Candidate Introduction:** *How many years of total professional experience do you have?*

↳ **Candidate Introduction:** *Of your total experience, how many years specifically have you worked with AWS?*

#### 【 OTHER 】

<details>
<summary><strong>● Have you done infrastructure automation using Python and PowerShell?</strong></summary>

**Answer:**
Yes, I leverage both languages according to the operating system and platform requirements:

- **Python:** Developed AWS automation scripts using **Boto3** for automated EBS snapshot management, scanning for non-compliant S3 buckets, and building CI/CD test automation harnesses.
- **PowerShell:** Automated Windows Server administration, IIS website deployment, scheduled task creation, active directory queries, and configuration management on Windows EC2 instances.
</details>

<details>
<summary><strong>↳ Follow-up: What is the difference between Python and PowerShell as scripting languages?</strong></summary>

**Answer:**
While both are high-level scripting languages, their architectural foundations and paradigms differ:

| Feature | Python | PowerShell |
| :--- | :--- | :--- |
| **Pipeline Data Model** | Operates on **plain text / strings / byte streams** | Operates on **rich .NET Objects** (properties and methods preserved across pipes) |
| **Runtime Environment** | Python Interpreter (CPython, cross-platform) | .NET CLR runtime (PowerShell Core is cross-platform; Windows PowerShell is Windows-only) |
| **Cloud & DevOps Ecosystem** | Industry standard for Linux, Kubernetes API, cloud SDKs (AWS Boto3, GCP SDK), ML | De facto standard for Windows Server, IIS, Active Directory, Hyper-V, and Azure |
| **Syntax Style** | Clean, readable syntax with whitespace indentation | Verb-Noun cmdlet naming convention (`Get-Service`, `Set-ItemProperty`) |
| **Object Inspection** | Requires parsing JSON/regex from CLI text outputs | Direct access to object properties (e.g., `(Get-Process).WorkingSet`) |
</details>

<details>
<summary><strong>● How do you handle exceptions in Python?</strong></summary>

**Answer:**
In Python, exceptions are handled using the `try`, `except`, `else`, and `finally` structure with explicit error types:

```python
import boto3
from botocore.exceptions import ClientError

def restart_ec2_instance(instance_id):
    ec2 = boto3.client('ec2')
    try:
        response = ec2.reboot_instances(InstanceIds=[instance_id])
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidInstanceID.NotFound':
            print(f"Error: Instance {instance_id} does not exist.")
        else:
            print(f"AWS API Client Error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected system error: {e}")
        raise
    else:
        print(f"Instance {instance_id} reboot initiated successfully.")
        return True
    finally:
        print("Completed reboot execution attempt.")
```
</details>

<details>
<summary><strong>● Do you know what IIS (Internet Information Services) is?</strong></summary>

**Answer:**
**Internet Information Services (IIS)** is Microsoft's enterprise-grade web server software designed for Windows Server.

**Key Components & Concepts:**
- **Application Pools:** Isolates worker processes (`w3wp.exe`) so that a failure in one application does not crash other websites running on the same server.
- **Hosting Capabilities:** Native host for ASP.NET, .NET Core, WCF, and static web content.
- **Bindings & Certificates:** Manages HTTP, HTTPS, and FTP bindings mapped to specific IP addresses, ports, and SSL/TLS certificates.
- **Automation:** Managed and automated via PowerShell (`WebAdministration` module: `Get-IISSite`, `New-WebAppPool`, `Restart-WebAppPool`).
</details>

<details>
<summary><strong>● How much experience do you have working with SQL?</strong></summary>

**Answer:**
I have **over 5 years of practical SQL experience** focused on database administration, operations, and pipeline automation:

- Writing SQL DDL and DML queries (SELECT, JOINs, INDEX creation, GROUP BY, aggregations).
- Integrating automated database schema migration tools (**Flyway**, **Liquibase**) into Jenkins CI/CD pipelines.
- Troubleshooting database performance: analyzing slow query logs, optimizing indexes, inspecting `EXPLAIN ANALYZE` execution plans, and managing connection pooling on AWS RDS PostgreSQL/MySQL.
</details>
</details>
</details>

<details open>
<summary><h2>🏢 Feuji</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 CI/CD 】

<details>
<summary><strong>● Can you explain the CI/CD setup you have worked with?</strong></summary>

**Answer:**
In my recent role, I designed an automated, enterprise **GitOps CI/CD pipeline** running across **GitHub Actions**, **AWS ECR**, and **Argo CD** deploying to an **AWS EKS** multi-tenant cluster:

1. **Continuous Integration (CI):**
   - Developer opens a Pull Request -> Triggers GitHub Actions workflow.
   - **Static Analysis & Testing:** Runs linting, unit tests, and **SonarQube** Quality Gate verification.
   - **Security Auditing:** Scans dependencies with Trivy and Snyk for critical CVEs.
   - **Containerization:** On merge to `main`, executes a multi-stage Docker build, tags the image with the Git commit SHA (`${IMAGE_TAG}`), scans the container image with Trivy, and pushes it to **AWS ECR**.

2. **Continuous Delivery (CD) via GitOps:**
   - A dedicated GitHub Actions step updates the Kubernetes Helm chart values repository (`image.tag: <commit-sha>`).
   - **Argo CD** continuously monitors the Helm Git repository. Upon detecting commit drift, Argo CD triggers an automated sync, executing a rolling deployment to the EKS cluster.
   - Automatic canary analysis via **Argo Rollouts** validates error rates and latency before shifting 100% of user traffic.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Have you deployed any monitoring systems and worked with microservices running in an EKS cluster?</strong></summary>

**Answer:**
Yes, I have extensive hands-on experience architecting and operating production microservices on **AWS EKS** combined with full-stack observability:

- **EKS Architecture:** Designed multi-AZ EKS clusters leveraging **Karpenter** and Cluster Autoscaler for node provisioning, AWS Load Balancer Controller for Application Load Balancers, and AWS VPC CNI for native pod networking.
- **Monitoring Deployments:** Deployed and managed the **Prometheus Operator (kube-prometheus-stack)** with Alertmanager, Grafana, and an **OpenSearch / Fluent Bit** centralized logging pipeline running as DaemonSets across all worker nodes.
- **Observability Integration:** Instrumented containerized Java, Go, and Python microservices with OpenTelemetry (OTel) agents exporting metrics and distributed traces into Grafana and Jaeger.
</details>

<details>
<summary><strong>↳ Follow-up: As part of this CI/CD setup, did you deploy applications to an EKS cluster?</strong></summary>

**Answer:**
Yes, deployments to the EKS cluster were completely automated through **GitOps with Argo CD**:

1. **Deployment Artifacts:** Applications were packaged as standard **Helm charts** parameterized for different environments (`values-dev.yaml`, `values-stage.yaml`, `values-prod.yaml`).
2. **GitOps Synchronization:** Argo CD Application controllers tracked the environment manifests in Git. When the CI pipeline committed an updated image tag, Argo CD reconciled the desired state against the EKS cluster.
3. **Traffic Management:** Handled via **AWS Load Balancer Controller**, dynamically provisioning Target Groups and Application Load Balancers (ALBs) mapped to Kubernetes Ingress resources using IP-mode routing directly to Pod IPs.
</details>

<details>
<summary><strong>↳ Follow-up: If, after a deployment, a user is unable to access the application, how would you troubleshoot the issue?</strong></summary>

**Answer:**
I follow a methodical top-down diagnostic workflow spanning **DNS/Ingress -> Service/Endpoints -> Pods/Containers**:

```
[ 1. Ingress & DNS ]
  |-- dig api.company.com (Verify Route 53 points to ALB DNS)
  |-- kubectl get ingress -n <namespace> (Inspect Ingress status & ALB annotations)
  +-- Check AWS ALB Target Group: Are target pods showing 'healthy' or 'unhealthy'?

[ 2. Service & Endpoints (Core Binding Check) ]
  |-- kubectl get svc <service-name> -n <namespace>
  +-- kubectl get endpoints <service-name> -n <namespace>
        |-- If endpoints list is EMPTY:
        |   The Service 'selector' does NOT match Pod 'labels'!
        +-- If endpoints exist: Proceed to Pod inspection

[ 3. Pod Health & Status ]
  |-- kubectl get pods -n <namespace> -l app=<app-name>
  |     |-- Check Pod Phase: Running, CrashLoopBackOff, Pending, ImagePullBackOff?
  +-- kubectl describe pod <pod-name> -n <namespace>
        |-- Check 'Conditions': Initialized, Ready, ContainersReady, PodScheduled
        +-- If Pod is Running but NOT Ready (0/1):
            The 'readinessProbe' is failing, preventing ingress traffic!

[ 4. Logs & Container Diagnostics ]
  |-- kubectl logs <pod-name> -n <namespace> --tail=100
  |-- kubectl logs <pod-name> -n <namespace> --previous (If restarted)
  +-- Port-forward directly to pod:
      kubectl port-forward pod/<pod-name> 8080:8080 -n <namespace>
      curl -Iv http://localhost:8080/health
```
</details>

#### 【 MONITORING 】

<details>
<summary><strong>↳ Follow-up: How did you configure monitoring systems such as the ELK stack and Grafana for your microservices?</strong></summary>

**Answer:**
I implemented an integrated observability architecture combining **Fluent Bit + OpenSearch (ELK)** for logs and **Prometheus + Grafana** for metrics:

1. **Centralized Logging (ELK / OpenSearch):**
   - **Log Collection:** Deployed **Fluent Bit** as a `DaemonSet` on every EKS node. It tails container stdout/stderr logs from `/var/log/containers/*.log`.
   - **Metadata Enrichment:** The Fluent Bit `kubernetes` filter queries the Kubelet API to attach namespace, pod name, container name, and label metadata to every log entry.
   - **Ingestion & Visualization:** Forwarded structured JSON logs into an **Amazon OpenSearch Service** cluster. Developers query and filter logs using **OpenSearch Dashboards / Kibana** with saved index patterns (`app-logs-*`).

2. **Metrics & Visualization (Prometheus & Grafana):**
   - Deployed **kube-prometheus-stack** via Helm.
   - Microservices expose application telemetry at `/metrics` using Prometheus client libraries.
   - Defined `ServiceMonitor` Custom Resources matching service labels to configure Prometheus scrapers declaratively.
   - Configured **Grafana** with Prometheus as the default timeseries datasource and Alertmanager for threshold notifications.
</details>

<details>
<summary><strong>↳ Follow-up: What kind of dashboards did you create in Grafana?</strong></summary>

**Answer:**
I engineered role-specific Grafana dashboards organized across three operational levels:

1. **Kubernetes Infrastructure Dashboard:**
   - Cluster-wide CPU and Memory capacity vs. requests/limits.
   - Node status, disk pressure, and network throughput.
   - Pod restart counts, deployment replica health, and PVC storage utilization.

2. **Microservice Application Dashboard (RED Method):**
   - **Rate:** Requests per second (RPS) broken down by HTTP endpoint and response code (`2xx`, `4xx`, `5xx`).
   - **Errors:** Error rate percentage (`(5xx / Total Requests) * 100`).
   - **Duration:** Request latency distribution visualized at **p50, p95, and p99** percentiles.

3. **Runtime & Middleware Dashboards:**
   - **JVM Telemetry:** Heap memory utilization, Garbage Collection (GC) pause duration and frequency, active thread count.
   - **Database Connection Pool:** HikariCP active connections, idle connections, and connection acquisition wait times.

4. **Business & Transactional Dashboards:**
   - Completed payments per minute, payment processing failure categories, and third-party gateway response times.
</details>

<details>
<summary><strong>● What is SLI (Service Level Indicator) and SLO (Service Level Objective)?</strong></summary>

**Answer:**
In modern Site Reliability Engineering (SRE):

1. **SLI (Service Level Indicator):**
   - A **quantifiable, real-time metric** that measures how well a service is performing at any given moment.
   - Usually expressed as: `SLI = (Good Events / Total Events) * 100%`.
   - *Example:* "Percentage of successful HTTP requests (non-5xx) processed in under 300ms."

2. **SLO (Service Level Objective):**
   - A **target reliability goal** set by engineering and business stakeholders for an SLI over a specific rolling time window (e.g., 30 days).
   - *Example:* "The Payment Service SLI must be >= 99.95% over any rolling 30-day window."

3. **Relationship with SLA & Error Budget:**
   - **SLA (Service Level Agreement):** The contractual commitment to external clients with financial penalties if breached (usually set lower than the internal SLO, e.g., 99.9%).
   - **Error Budget:** `100% - SLO`. For an SLO of 99.95%, the allowable downtime/error budget over 30 days is **0.05% (~21.6 minutes)**.
</details>

<details>
<summary><strong>↳ Follow-up: Given a payment microservice, how would you define SLIs and SLOs for it, and how would you implement monitoring for them using Grafana?</strong></summary>

**Answer:**
For a mission-critical **Payment Microservice**, reliability and latency are paramount:

**1. Defined SLIs and SLOs:**
- **Availability SLI:**
  $$	ext{SLI}_{	ext{avail}} = rac{\sum 	ext{rate(http\_requests\_total}\{	ext{status} ! \sim 	ext{"5.."}\}[5m])}{\sum 	ext{rate(http\_requests\_total}[5m])} 	imes 100$$
  - **Availability SLO:** **99.99%** successful responses over a rolling 30-day period.
- **Latency SLI:**
  $$	ext{SLI}_{	ext{latency}} = rac{\sum 	ext{rate(http\_request\_duration\_seconds\_bucket}\{	ext{le}="0.5"\}[5m])}{\sum 	ext{rate(http\_request\_duration\_seconds\_count}[5m])} 	imes 100$$
  - **Latency SLO:** **99%** of requests must complete in under **500ms** over 30 days.

**2. Grafana Implementation:**
- **Error Budget Gauge Panel:** Visualizes remaining error budget in percentage using PromQL:
  ```promql
  (
    (sum(increase(http_requests_total{job="payment-service", status!~"5.."}[30d])) or vector(0))
    /
    sum(increase(http_requests_total{job="payment-service"}[30d]))
    - 0.9999
  ) / (1 - 0.9999) * 100
  ```
- **Multi-Window Multi-Burn-Rate Alerts:** Configured in Alertmanager to fire high-priority pages to on-call engineers if the service consumes **2% of the 30-day budget in 1 hour** (Burn Rate = 14.4x), preventing total budget exhaustion.
</details>

<details>
<summary><strong>↳ Follow-up: In the context of dashboards, do you know what the 'golden signals' are in monitoring?</strong></summary>

**Answer:**
The **Four Golden Signals** are the foundational monitoring metrics defined in Google's SRE framework for monitoring customer-facing systems:

1. **Latency:**
   - The time it takes to service a request.
   - Crucial distinction: Measure latency of **successful requests** separately from **failed requests** (e.g., a fast HTTP 500 error can falsely mask slow database queries).

2. **Traffic:**
   - A measure of demand placed on the system.
   - Measured as HTTP requests per second (RPS), concurrent active connections, or network I/O bits/sec.

3. **Errors:**
   - The rate of requests that fail.
   - Includes **explicit errors** (HTTP 500 internal errors), **implicit errors** (HTTP 200 containing an error payload), and policy violations (aborted transactions).

4. **Saturation:**
   - A measure of how full your service is, emphasizing the most constrained resources.
   - Examples: Memory usage %, CPU throttling percentage, database connection pool exhaustion, or disk queue depth. Systems degrade non-linearly when saturation exceeds 85%.
</details>

<details>
<summary><strong>↳ Follow-up: Suppose you need to collect and monitor logs from millions of real users in real time — how would you design and implement such a real-time monitoring system?</strong></summary>

**Answer:**
Handling real-time logs from millions of concurrent users requires a distributed, highly decoupled **streaming ingest and analytics architecture**:

```
[ Millions of Users / Edge Clients ]
                |
          (HTTPS / WSS)
                v
[ AWS CloudFront CDN / API Gateway ]
                |
                v
  [ Ingestion Layer: Apache Kafka / AWS Kinesis ]
  (Partitioned by user_id / session_id; absorbs massive traffic spikes)
                |
      +---------+---------+
      |                   |
      v                   v
[ Stream Processing ]   [ Data Firehose: Cold Storage ]
(Apache Flink / Spark)   |
- Real-time aggregation  v
- Error rate anomalies   [ Amazon S3 Data Lake ]
- Security abuse checks  (Parquet / Snappy format; queryable via Athena)
      |
      v
[ High-Throughput Search / Analytics ]
- OpenSearch / ClickHouse Cluster
- Grafana Real-Time Dashboards & Alerts (< 5s latency)
```

**Key Architectural Decisions:**
1. **Decoupled Buffer (Apache Kafka / AWS Kinesis):**
   Edge ingestion services never write directly to Elasticsearch/OpenSearch. Kafka acts as an elastic shock absorber with multiple partitions to prevent backpressure from crashing services during traffic surges.
2. **Stream Processing (Apache Flink):**
   Computes rolling sliding-window aggregations (e.g., counting HTTP 5xx errors per second) and detects anomalous patterns in real time without storing every raw payload in the search index.
3. **Tiered Storage (Hot vs. Cold):**
   - **Hot Storage (ClickHouse / OpenSearch):** Indexes aggregated logs and error traces for 7 days for sub-second developer debugging.
   - **Cold Storage (Amazon S3):** Kinesis Data Firehose converts logs into Parquet format for long-term retention and cost-effective compliance queries using Amazon Athena.
</details>
</details>
</details>

<details open>
<summary><h2>🏢 Bounteous</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 18-08-2026 07:49 PM*

#### 【 CI/CD 】

<details>
<summary><strong>● Can you explain how a Jenkins CI/CD pipeline works?</strong></summary>

**Answer:**
A Jenkins CI/CD pipeline operates on a distributed **Controller-Agent architecture** orchestrated by a code-defined `Jenkinsfile` stored in Git:

1. **Trigger & Agent Allocation:**
   - A code commit or Pull Request triggers a GitHub webhook pointing to Jenkins.
   - The Jenkins Controller provisions an ephemeral dynamic agent (e.g., a Kubernetes Pod running in EKS) or schedules a worker from an agent pool.

2. **Pipeline Execution Stages:**
   - **Checkout:** Pulls source code for the specific branch/commit.
   - **Build & Unit Tests:** Runs language-specific builds (`mvn compile`, `npm build`) and unit tests, capturing test reports.
   - **Code Quality & Security Gate:** Invokes **SonarQube** scanner. The pipeline pauses at `waitForQualityGate()` to enforce code standards.
   - **Containerization & Vulnerability Scanning:** Builds a multi-stage Docker image, tags it with the Git commit SHA, and scans it via **Trivy** for critical vulnerabilities.
   - **Publishing:** Pushes validated images to **AWS ECR** or Artifactory.
   - **Deployment & Verification:** Deploys manifests to lower environments (Dev/QA) via Helm or GitOps, runs automated integration smoke tests, and requests manual stakeholder approval before promoting to Production.
</details>

#### 【 IAC 】

<details>
<summary><strong>● Can you explain how you automate infrastructure provisioning and management?</strong></summary>

**Answer:**
Infrastructure automation is achieved through an enterprise **GitOps-driven Infrastructure as Code (IaC)** pipeline:

1. **Declarative Modeling with Terraform:**
   - Cloud resources (VPCs, EKS clusters, RDS databases, IAM policies) are defined declaratively in version-controlled Terraform modules.
   - Remote state is maintained in an encrypted S3 bucket with DynamoDB distributed locking.

2. **Automated CI/CD Workflow (Atlantis / GitHub Actions):**
   - When an engineer creates a Pull Request modifying `.tf` files, the pipeline runs `terraform fmt`, `tflint`, security scanning via `tfsec`/`checkov`, and generates an automated `terraform plan`.
   - The plan output is posted directly back into the PR comments for peer review and architectural approval.
   - Upon PR merge, the pipeline executes `terraform apply` in the target environment.

3. **Configuration & OS Management:**
   - Post-provisioning configuration and OS hardening are automated using **Ansible** playbooks or cloud-init user data scripts.
</details>

<details>
<summary><strong>● If you have provisioned your infrastructure on AWS using infrastructure-as-code and someone makes manual changes via the AWS console, how would you handle this situation?</strong></summary>

**Answer:**
This scenario describes **Configuration Drift**. In production, I handle this through a disciplined multi-step protocol:

1. **Detect and Measure Drift:**
   - Run `terraform plan` or `terraform refresh` to compare the live cloud infrastructure against the last recorded state and local code. Terraform highlights the exact attributes modified via console.

2. **Audit via AWS CloudTrail (Identify Root Cause):**
   - Query **AWS CloudTrail Event History** filtering by resource name/ID and event time to identify *who* made the change, *when*, and *why*:
     ```bash
     aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=sg-0123456789
     ```

3. **Remediation Strategy:**
   - **Scenario A (Unauthorized / Mistaken Change):** Enforce code as the single source of truth. Run `terraform apply` to immediately overwrite the manual modification and restore declared state.
   - **Scenario B (Valid Emergency Hotfix):** If the change was an emergency production fix, backport the change into the Terraform code immediately. Run `terraform plan` to verify that the proposed changes drop to `0 to add, 0 to change, 0 to destroy`.

4. **Prevent Future Drift (Governance):**
   - Implement **AWS Service Control Policies (SCPs)** and restrictive IAM Permission Boundaries in production accounts that explicitly deny write actions (`ec2:*`, `rds:*`, `s3:*`) to all human users and console logins, mandating all changes flow through the CI/CD deployment role.
   - Schedule daily automated drift detection jobs that alert the DevOps channel in Slack if drift occurs.
</details>

<details>
<summary><strong>● Can you explain what modules are (in the context of infrastructure-as-code tools like Terraform)?</strong></summary>

**Answer:**
A **Terraform module** is a container for multiple resources that are used together. Every Terraform configuration has at least one root module, and can call reusable **child modules**.

**Standard Structure of a Module:**
```
modules/aws-vpc/
├── main.tf        # Resource declarations (aws_vpc, aws_subnet, aws_nat_gateway)
├── variables.tf   # Input parameter definitions with types and descriptions
├── outputs.tf     # Output values exposed to calling configurations
├── versions.tf    # Required terraform and provider versions
└── README.md      # Documentation and usage examples
```

**Why Modules are Critical in Enterprise IaC:**
1. **Reusability & DRY (Don't Repeat Yourself):** Define an architectural pattern (e.g., standard 3-tier VPC with public/private subnets) once, and instantiate it across Dev, Staging, and Prod with different input parameters.
2. **Standardization & Compliance:** Security teams can bake corporate compliance (e.g., enforcing EBS encryption, S3 bucket public access blocks) directly into golden modules.
3. **Encapsulation & Versioning:** Child modules can be hosted in dedicated Git repositories and referenced using semantic version tags (`git::https://...git?ref=v2.1.0`), preventing accidental breaking changes across environments.
</details>

#### 【 NETWORKING 】

<details>
<summary><strong>● What is the difference between VPC peering and AWS Transit Gateway?</strong></summary>

**Answer:**
Both connect Virtual Private Clouds (VPCs) in AWS, but their network topologies, scalability, and routing models differ fundamentally:

| Feature | VPC Peering | AWS Transit Gateway (TGW) |
| :--- | :--- | :--- |
| **Topology** | **Point-to-Point Mesh** (1:1 connection between two VPCs) | **Hub-and-Spoke** (Central cloud router connecting thousands of VPCs and VPNs) |
| **Transitive Routing** | **Not supported** (If A peers with B, and B peers with C, A cannot talk to C) | **Fully supported** (All attached VPCs route transitively through the central hub) |
| **Scalability** | Becomes unmanageable at scale: connecting $N$ VPCs requires $rac{N(N-1)}{2}$ peering connections | Scales effortlessly: supports up to **5,000 VPC attachments** per gateway |
| **On-Premise Integration** | Cannot connect directly to on-premises Direct Connect or VPN | Connects VPCs, AWS Site-to-Site VPNs, and Direct Connect Gateways to a single hub |
| **Cost Model** | **No hourly connection fee**; pay only for inter-AZ / inter-Region data transfer | **Hourly fee per attachment** (~$0.05/hr/attachment) + data processing fee per GB |
</details>

<details>
<summary><strong>↳ Follow-up: In what scenarios would you choose to use VPC peering versus Transit Gateway?</strong></summary>

**Answer:**
The decision is driven by architecture complexity, throughput requirements, and cost:

1. **Choose VPC Peering When:**
   - Connecting only a small number of VPCs (e.g., 2 to 4 VPCs, such as an analytics VPC pulling data from a single production VPC).
   - High-throughput, data-intensive workloads: VPC Peering has **no bandwidth bottlenecks** and **zero data processing fees** (unlike TGW's per-GB processing surcharge).
   - Simple architectures that do not require routing to on-premise networks.

2. **Choose AWS Transit Gateway When:**
   - Multi-account enterprise environments with tens or hundreds of VPCs (managed via AWS Organizations).
   - Requiring centralized egress/ingress inspection architectures (routing all VPC outbound traffic through a dedicated Central Inspection VPC running Firewalls).
   - Hybrid cloud architectures requiring shared access to on-premises datacenters via a single AWS Direct Connect or Site-to-Site VPN.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Can you explain the different S3 storage classes in AWS?</strong></summary>

**Answer:**
Amazon S3 provides tiered storage classes engineered for different access patterns, latency requirements, and cost profiles:

1. **S3 Standard:**
   - High availability, low latency (milliseconds). Designed for frequently accessed data.
2. **S3 Intelligent-Tiering:**
   - Automatically monitors and moves objects between access tiers (Frequent, Infrequent, Archive Instant, Deep Archive) based on access patterns with **zero retrieval fees** and zero operational overhead.
3. **S3 Standard-IA (Infrequent Access):**
   - For data accessed less frequently but requiring millisecond retrieval when needed. Lower storage price than Standard, but charges per-GB retrieval fees (30-day minimum retention).
4. **S3 One Zone-IA:**
   - Stores data in a single Availability Zone. 20% lower cost than Standard-IA, but lacks multi-AZ resilience. Suitable for recreatable, non-critical backup data.
5. **S3 Glacier Instant Retrieval:**
   - Archive storage with **millisecond retrieval**. Ideal for rarely accessed medical records or historical images accessed once a quarter.
6. **S3 Glacier Flexible Retrieval (formerly Glacier):**
   - Archive storage with retrieval times ranging from 1–5 minutes (Expedited) to 3–5 hours (Standard). 90-day minimum retention.
7. **S3 Glacier Deep Archive:**
   - Lowest-cost cloud storage ($0.00099/GB/month). Retrieval time within 12 to 48 hours. Designed for long-term regulatory data retention (7–10 years).
</details>

<details>
<summary><strong>● How do you connect different AWS accounts when services in those accounts need to communicate with each other?</strong></summary>

**Answer:**
Connecting services across AWS accounts can be achieved at multiple architectural layers depending on security requirements:

1. **Network Layer Connectivity:**
   - **AWS Transit Gateway (TGW) with AWS RAM:** Share the central Transit Gateway with external accounts via AWS Resource Access Manager (RAM). Attach VPCs in different accounts to the shared TGW to enable bidirectional private routing.
   - **Cross-Account VPC Peering:** Direct peering connection created between VPCs in Account A and Account B, requiring peer acceptance and route table updates in both accounts.

2. **Private Service Sharing Layer (AWS PrivateLink / VPC Endpoints):**
   - Account A hosts a service behind a Network Load Balancer (NLB) and configures an **Endpoint Service**.
   - Account B creates an **Interface VPC Endpoint** connecting to that service. Traffic stays on the AWS private backbone with zero VPC peering or CIDR overlap conflicts.

3. **Identity & Authorization Layer (Cross-Account IAM Roles):**
   - Account A defines an IAM Role with an **AssumeRole Trust Policy** allowing Account B's principal/role to assume it via AWS STS (`sts:AssumeRole`), granting temporary scoped permissions.

4. **Resource-Based Policies:**
   - Directly grant permissions in resource policies (e.g., S3 Bucket Policy, KMS Key Policy, SQS Queue Policy) referencing the external account's root ARN or specific role (`arn:aws:iam::ACCOUNT_B:role/service-role`).
</details>

<details>
<summary><strong>● How do you automate taking backups of data in AWS?</strong></summary>

**Answer:**
Enterprise backup automation is implemented using **AWS Backup** and automated lifecycle policies:

1. **AWS Backup Centralized Orchestrator:**
   - Create an automated **Backup Plan** defining backup frequency (e.g., daily cron), backup window, and lifecycle rules (e.g., transition to cold storage after 30 days, expire after 365 days).
   - Assign resources automatically using **tag-based selection** (e.g., `BackupPlan = Tier1-Daily`).
   - Supports automated cross-region and cross-account backup copies to an isolated Disaster Recovery (DR) account.

2. **Amazon Data Lifecycle Manager (DLM):**
   - Automates the creation, retention, and deletion of EBS volume snapshots and EBS-backed AMIs.

3. **Immutable Backups via AWS Backup Vault Lock:**
   - Enforces WORM (Write Once, Read Many) compliance to prevent ransomware or rogue administrators from deleting backup snapshots before the retention period expires.
</details>

<details>
<summary><strong>● What disaster recovery strategies should be followed in AWS?</strong></summary>

**Answer:**
The AWS Well-Architected Reliability Pillar outlines **Four Disaster Recovery (DR) Strategies**, balancing Recovery Time Objective (RTO), Recovery Point Objective (RPO), and cost:

```
[ Cost & Complexity Increases  ------------------------------------------> ]
[ RTO / RPO Decreases (Better) <------------------------------------------ ]

1. Backup & Restore   2. Pilot Light       3. Warm Standby      4. Multi-Region Active-Active
(Hours / Days)        (10 - 30 Mins)       (Minutes)            (Near Zero RTO / RPO)
```

1. **Backup and Restore:**
   - Data is backed up to S3 and replicated across regions (CRR). Infrastructure is provisioned via Terraform only upon disaster declaration.
   - *RPO:* Hours | *RTO:* 24+ Hours | *Cost:* Lowest.

2. **Pilot Light:**
   - Core data is continuously replicated to the DR region (e.g., Aurora Global Database, continuous S3 replication). Compute instances are not running; AMIs and launch templates are pre-staged and scaled up during failover.
   - *RPO:* Minutes | *RTO:* 10–30 Minutes | *Cost:* Low.

3. **Warm Standby:**
   - A scaled-down but fully functional minimal duplicate of production runs 24/7 in the secondary region. During disaster, the secondary environment handles traffic and autoscales to full capacity.
   - *RPO:* Seconds to Minutes | *RTO:* Minutes | *Cost:* Medium.

4. **Multi-Region Active-Active:**
   - Full capacity running simultaneously in two or more AWS regions. User traffic is split using Amazon Route 53 latency-based or geolocation routing.
   - *RPO:* Near Zero | *RTO:* Near Zero | *Cost:* Highest.
</details>

<details>
<summary><strong>● What is the difference between AWS SNS and SQS?</strong></summary>

**Answer:**
Both are fully managed AWS messaging services, but they implement different architectural communication patterns:

| Feature | Amazon SNS (Simple Notification Service) | Amazon SQS (Simple Queue Service) |
| :--- | :--- | :--- |
| **Messaging Paradigm** | **Publish / Subscribe (Pub-Sub)** | **Message Queuing (Point-to-Point)** |
| **Delivery Model** | **Push-based** (Pushes messages instantly to subscribers) | **Pull-based** (Consumers poll the queue to retrieve messages) |
| **Consumers** | Multiple subscribers receive identical copies (fan-out) | Single consumer processes and deletes a specific message |
| **Message Persistence** | **No persistence** (If no subscribers exist or delivery fails, message is lost unless DLQ is attached) | **Persistent** (Messages stored safely in queue until processed or retention expires, up to 14 days) |
| **Supported Subscribers** | SQS queues, AWS Lambda, HTTP/HTTPS endpoints, SMS, Email | EC2 instances, ECS/EKS worker containers, Lambda triggers |

**Common Architectural Pattern (SNS-to-SQS Fan-Out):**
An application publishes an order event to an SNS Topic. The topic fans out the message to multiple SQS queues in parallel (e.g., Billing Queue, Inventory Queue, Shipping Queue), allowing each microservice to process orders independently at its own pace.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself and give an overview of your professional background?
</details>
</details>

<details open>
<summary><h2>🏢 Apty</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Why did you choose EKS over alternatives like Lambda or plain EC2 for running your microservices, and what scale or operational needs drove that decision?</strong></summary>

**Answer:**
We architected our platform around **AWS EKS** after evaluating technical trade-offs across Lambda, EC2, and Kubernetes:

1. **Why Not AWS Lambda (Serverless):**
   - **Execution Time Limits:** Our financial reporting platform runs heavy analytical calculations and report generation taking 10–20 minutes, exceeding Lambda's hard 15-minute execution cap.
   - **JVM Cold Starts:** Our Spring Boot microservices experienced 8–12 second cold starts in VPC-attached Lambdas, violating our <500ms p99 SLA.
   - **Cost at Scale:** Running 24/7 high-throughput sustained workloads (>150 million requests/month) on Lambda is significantly more expensive than bin-packed containers on compute instances.

2. **Why Not Plain EC2:**
   - **Operational Overhead:** Managing AMIs, rolling OS updates, and host-level patching across 40+ virtual machines required significant manual toil.
   - **Slow Scaling Velocity:** EC2 Auto Scaling Groups required 3 to 5 minutes to launch and bootstrap new instances during traffic spikes, whereas container pods scale up in seconds.
   - **Resource Inefficiency:** Inability to bin-pack multiple heterogeneous microservices onto shared compute nodes caused poor CPU/RAM utilization.

3. **Why AWS EKS:**
   - Standardized container orchestration with declarative GitOps (Argo CD).
   - High-density bin-packing reducing cloud compute costs by 35%.
   - Native integration with Kubernetes ecosystem tools (Prometheus Operator, Istio Service Mesh, Karpenter, External Secrets Operator).
</details>

<details>
<summary><strong>↳ Follow-up: How did you handle scaling inside your EKS cluster — did you use the Horizontal Pod Autoscaler or another mechanism, and roughly how many pods did you scale up or down to under load?</strong></summary>

**Answer:**
We implemented a coordinated **two-tier autoscaling architecture** operating at both the pod and node levels:

1. **Pod Level Scaling (HPA v2 + KEDA):**
   - We utilized **Horizontal Pod Autoscaler (HPA)** configured with both resource metrics (CPU > 65%, Memory > 75%) and custom business metrics via **KEDA (Kubernetes Event-driven Autoscaling)**.
   - For our asynchronous report worker services, KEDA scaled pods based on **Kafka Consumer Lag** (scaling up when pending messages in the topic exceeded 500).
   - **Scale Ranges:** Under normal baseline traffic, the reporting service ran **12 pods**. During month-end financial statement generation or market open spikes, HPA dynamically scaled out to **80 pods** within 2 minutes, scaling back down smoothly using an 8-minute stabilization window.

2. **Node Level Scaling (Karpenter):**
   - Replaced the legacy Kubernetes Cluster Autoscaler with **Karpenter**.
   - Karpenter evaluates unschedulable pending pods, calculates exact aggregate resource requirements, and provisions right-sized EC2 instances (mixing On-Demand and Spot instances across varied instance families like `m5.2xlarge`, `c5.2xlarge`) within **30 to 45 seconds**.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● How did you structure your AWS VPC for this platform, including the design of public versus private subnets, routing, and security groups? What did you build and why?</strong></summary>

**Answer:**
We architected a resilient, highly secure **Multi-AZ 3-Tier VPC** spread across three Availability Zones (`us-east-1a`, `us-east-1b`, `us-east-1c`) with a `/16` CIDR block (`10.100.0.0/16`):

```
+-----------------------------------------------------------------------------------+
| AWS VPC: 10.100.0.0/16                                                            |
|                                                                                   |
|  [ Public Subnets: /24 ] (Internet Gateway 0.0.0.0/0)                             |
|  - Internet-facing ALBs                                                           |
|  - High Availability NAT Gateways (1 per AZ to eliminate single-AZ failure)       |
|                                                                                   |
|  [ Private Application Subnets: /20 ] (Route 0.0.0.0/0 -> AZ-specific NAT GW)   |
|  - AWS EKS Worker Nodes & Pods (VPC CNI allocating primary & secondary IPs)       |
|  - Internal Microservices                                                         |
|                                                                                   |
|  [ Private Database Subnets: /24 ] (Isolated - No Route to Internet / No NAT)    |
|  - Amazon Aurora PostgreSQL Multi-AZ Cluster                                      |
|  - Amazon ElastiCache Redis Cluster                                               |
|  - AWS MSK (Managed Streaming for Apache Kafka)                                   |
+-----------------------------------------------------------------------------------+
```

**Security Group Design (Defense-in-Depth):**
- **ALB Security Group (`sg-alb`):** Allows inbound HTTPS (port 443) from external internet (`0.0.0.0/0`).
- **EKS Worker Node Security Group (`sg-eks-nodes`):** Allows inbound traffic on application ports (8080) **only if the source is `sg-alb`**. Direct internet access is blocked.
- **Database Security Group (`sg-rds`):** Allows inbound PostgreSQL (port 5432) **strictly from `sg-eks-nodes`**.
</details>

<details>
<summary><strong>↳ Follow-up: Given that your load balancer sits in the public subnet, how did you secure traffic flowing from the load balancer to your private application subnets? Can you explain how you used security groups versus NACLs, and why you chose that approach?</strong></summary>

**Answer:**
Traffic flowing from the public Application Load Balancer (ALB) to the private application subnets is secured primarily through **Security Group Chaining (Referencing)**:

1. **Security Group Referencing (The Core Mechanism):**
   - Instead of configuring IP/CIDR-based ingress rules on the private EC2/EKS instances, we configure the EKS worker node Security Group to allow inbound traffic **referencing the ALB Security Group ID directly**:
     ```hcl
     resource "aws_security_group_rule" "app_from_alb" {
       type                     = "ingress"
       from_port               = 8080
       to_port                 = 8080
       protocol                = "tcp"
       source_security_group_id = aws_security_group.alb_sg.id
       security_group_id        = aws_security_group.eks_node_sg.id
     }
     ```
   - Because Security Groups are **stateful**, return traffic from the pods back to the ALB is automatically tracked and allowed without opening outbound ephemeral ports.

2. **Security Groups vs. NACLs Selection:**
   - **Why Security Groups for Application Security:** Security Groups operate directly at the virtual network interface (ENI) level, evaluate microservice identities dynamically, and enforce strict least-privilege without worrying about dynamic IP churn or subnet renumbering.
   - **Role of NACLs (Subnet Guardrails):** NACLs were retained at the subnet boundary as coarse defense-in-depth filters: allowing HTTP/HTTPS into public subnets, allowing ephemeral ports (`1024-65535`) out, and explicitly blocking known malicious CIDRs detected by AWS GuardDuty.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● What was the biggest outage you faced on this financial reporting platform?</strong></summary>

**Answer:**
Our most critical incident was a **Sev-1 production outage** during a month-end release where the entire platform began throwing widespread **HTTP 503 Service Unavailable** errors on our customer-facing API endpoints, lasting approximately 18 minutes before remediation.

- **Impact:** Over 12,000 active customer requests failed during the morning peak reporting window, and the ALB reported zero healthy targets across multiple microservice target groups.
- **Immediate Detection:** Automated CloudWatch Alarms fired on `HTTPCode_Target_5XX_Count > 50` and PagerDuty paged the primary on-call SRE.
</details>

<details>
<summary><strong>↳ Follow-up: Regarding the 503 error outage you mentioned, how did you identify the root cause of the issue in production?</strong></summary>

**Answer:**
To isolate the root cause rapidly during the incident:

1. **ALB Metrics & Target Group Health:**
   - Inspected CloudWatch ALB metrics: Saw `TargetConnectionErrorCount` surging and `HealthyHostCount` collapsing to `0`.
   - Verified that the ALB returned 503 because it had **no healthy registered targets** in the target group.

2. **Kubernetes Pod Lifecycle & Events:**
   - Ran `kubectl get pods -n prod`: Observed that new pods from the latest deployment were in `Running` state, but their Ready status was `0/1`.
   - Ran `kubectl describe pod <pod-name>`: Found that the **Readiness Probe was continuously failing with HTTP 500 / Connection Refused** on `/actuator/health`.

3. **Log Analysis via OpenSearch / Kibana:**
   - Checked application stdout logs from newly spawned pods: Discovered that during startup, the application attempted to execute a newly introduced schema verification query against the database that hung due to an unindexed column lock, exhausting the initial HikariCP connection pool before the HTTP server could respond to Kubernetes readiness checks.
</details>

<details>
<summary><strong>↳ Follow-up: What specific fix did you deploy to resolve the 503 error outage?</strong></summary>

**Answer:**
We executed a two-phase resolution: an immediate operational rollback followed by a permanent engineering fix:

1. **Immediate Incident Resolution (Rollback in 2 minutes):**
   - We initiated an immediate GitOps rollback via Argo CD, reverting the application deployment to the prior Git commit:
     ```bash
     argocd app rollback financial-reporting-api --to-revision <PREVIOUS_HEALTHY_REVISION>
     ```
   - Argo CD rolled back the Pod spec, spawning instances of the proven stable image. Healthy targets registered with the ALB Target Group, restoring traffic within 120 seconds.

2. **Permanent Engineering Fix:**
   - Decoupled database schema validation from the runtime application startup path, moving migrations to a Kubernetes pre-deployment `Job`.
   - Corrected the database index to eliminate table lock contention.
   - Adjusted readiness and startup probe timing parameters.
</details>

<details>
<summary><strong>↳ Follow-up: Can you walk me through exactly what happened during the 503 error incident — how you detected the errors and what changes you made to bring the system back to a stable state?</strong></summary>

**Answer:**
Here is the end-to-end incident timeline and stabilization response:

- **09:15 AM:** Automated deployment of release v2.4.1 triggered via Jenkins/Argo CD.
- **09:17 AM:** Kubernetes rolling update terminated old v2.4.0 pods as new v2.4.1 pods entered `Running` status.
- **09:18 AM:** The new pods failed their database initialization and failed readiness probes. Kubernetes removed them from endpoints.
- **09:19 AM:** With all old pods terminated and no new pods reaching `Ready` status, the AWS ALB target group registered `HealthyHostCount = 0`. The ALB immediately started serving `503 Service Unavailable`.
- **09:20 AM:** PagerDuty alerted on-call engineers. We opened an incident bridge.
- **09:22 AM:** Confirmed through `kubectl get endpoints` that zero endpoints were registered for the service.
- **09:24 AM:** Executed `argocd app rollback`.
- **09:26 AM:** Stable v2.4.0 pods passed readiness probes, ALB registered 12 healthy targets, and 503 error rates dropped to zero.
- **09:30 AM:** Declared incident mitigated and initiated an SRE blameless post-mortem.
</details>

<details>
<summary><strong>↳ Follow-up: Regarding the endpoints that weren't updated during the 503 outage, what exactly did you fix — was it a configuration issue, a deployment step, or something related to service registration?</strong></summary>

**Answer:**
It was a combination of **misconfigured Kubernetes lifecycle probes** and **deployment rollout parameters**:

1. **Missing Startup Probe:**
   - Heavy JVM Spring Boot services take 25–40 seconds to warm up caches and establish connection pools.
   - The deployment only configured an aggressive `readinessProbe` with `initialDelaySeconds: 5` and `failureThreshold: 3`. After 15 seconds, Kubelet marked the container unready, preventing endpoint attachment.
   - **Fix:** Implemented a dedicated **`startupProbe`** that gave the application up to 60 seconds to boot before readiness probes began evaluation:
     ```yaml
     startupProbe:
       httpGet:
         path: /actuator/health/liveness
         port: 8080
       failureThreshold: 12
       periodSeconds: 5
     readinessProbe:
       httpGet:
         path: /actuator/health/readiness
         port: 8080
       periodSeconds: 5
       failureThreshold: 2
     ```

2. **Rollout Strategy Configuration:**
   - The deployment used `maxUnavailable: 50%`, which killed half the healthy instances before confirming the new instances were genuinely capable of serving traffic.
   - **Fix:** Changed deployment strategy to `maxSurge: 25%` and `maxUnavailable: 0%`, guaranteeing that zero healthy running pods are terminated until replacement pods are passing readiness probes.
</details>

<details>
<summary><strong>↳ Follow-up: How did you ensure the same 503 outage issue wouldn't happen again in future deployments?</strong></summary>

**Answer:**
We engineered four structural safeguards into our CI/CD and platform architecture:

1. **Adopted Argo Rollouts with Automated Canary Analysis:**
   - Replaced standard Kubernetes Deployments with **Argo Rollouts**.
   - Canary releases route only 5% of traffic to the new revision for 10 minutes while Prometheus queries verify that the HTTP 5xx rate remains below 0.05% and p99 latency does not spike. If any metric breaches, Argo Rollouts aborts and auto-reverts instantly.

2. **Pre-Stop Hooks & Connection Draining:**
   - Configured `lifecycle.preStop` hook running `sleep 15` in container specs. This ensures that when a pod is scheduled for termination, it continues processing in-flight requests while the ALB target group safely deregisters it.

3. **Pod Disruption Budgets (PDB):**
   - Enforced PDBs with `minAvailable: 75%` to prevent voluntary cluster disruptions or node drains from starving application capacity.

4. **Synthetic Pre-flight Verification in Pipeline:**
   - The CI/CD pipeline now executes an automated synthetic test suite against a temporary isolated ephemeral environment before triggering any production traffic shifts.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Which real-world system that you have owned end-to-end would you like to use as the anchor system for this technical discussion?</strong></summary>

**Answer:**
I would like to use our **Enterprise Financial Reporting and Real-Time Analytics Platform** as our anchor system.

**System Overview:**
- **Business Purpose:** Ingests high-volume financial transactions from core banking systems, generates regulatory compliance reports, computes risk metrics, and serves low-latency REST APIs to enterprise banking clients.
- **Scale:** Processes ~25 million daily financial events with a peak throughput of 4,500 requests/second, running over 40 containerized microservices across AWS EKS.
- **My Ownership:** I owned the end-to-end architecture, Infrastructure as Code (Terraform), Kubernetes cluster design, CI/CD GitOps pipelines, multi-region disaster recovery, and 24/7 observability stack.
</details>

<details>
<summary><strong>↳ Follow-up: Which is the most significant system where you owned both the architecture and the operations end-to-end, so we can use it as our anchor system for this discussion?</strong></summary>

**Answer:**
That same **Financial Reporting and Analytics Platform** represents my most comprehensive end-to-end ownership:

```
[ External Banking Clients ]
            |
      (HTTPS / TLS 1.3)
            v
[ AWS Route 53 + AWS WAF ]
            |
            v
[ Internet-Facing Application Load Balancer (Multi-AZ) ]
            |
            v
[ AWS EKS Cluster (Private Subnets across 3 AZs) ]
  |-- API Gateway / Ingress Controller
  |-- Spring Boot & Go Microservices (HPA + Karpenter autoscaling)
  +-- Kafka Consumer & Report Engine Pods
            |
      +-----+-----+
      |           |
      v           v
[ Amazon MSK ]  [ Amazon Aurora PostgreSQL ] <---> [ ElastiCache Redis ]
(Kafka Stream)  (Multi-AZ with Read Replicas)       (Sub-millisecond cache)
      |
      v
[ S3 Bucket (SSE-KMS) ] (Report Archives with Glacier Lifecycle Rules)
```

**Key Operational Dimensions Owned:**
- **Infrastructure:** 100% codified via modular Terraform with remote state locking and strict security compliance.
- **Deployment:** Zero-downtime canary releases powered by Argo CD and Argo Rollouts.
- **Reliability:** Enforced SLIs/SLOs with Prometheus, Grafana, and Alertmanager routing to PagerDuty.
- **Security:** Zero long-term credentials via IAM Roles for Service Accounts (IRSA), HashiCorp Vault for secrets, and KMS customer-managed keys (CMKs) for encryption at rest.
</details>
</details>
</details>

<details open>
<summary><h2>🏢 Bounteous</h2></summary>

<details open>
<summary><h3>Level 2</h3></summary>

*Date: 19-08-2026 06:12 PM*

#### 【 IAC 】

<details>
<summary><strong>● Where do you store the Terraform state file, and how do you handle a situation where the state file becomes corrupted?</strong></summary>

**Answer:**
In enterprise architectures, the Terraform state file (`terraform.tfstate`) is **never stored locally**. It is hosted in a secure, centralized remote backend:

- **Storage Location:** An **Amazon S3 bucket** configured with **Server-Side Encryption (SSE-KMS)**, strict IAM bucket policies blocking public access, and **S3 Bucket Versioning** enabled.
- **State Locking:** Coupled with an **Amazon DynamoDB table** using `LockID` as the primary hash key to prevent concurrent pipeline runs.

**Corrupted State File Recovery Procedure:**
1. **Identify the Corruption:** An apply failure or abrupt termination causes a state read failure (`Error: Error loading state` or invalid JSON syntax).
2. **Retrieve Prior Uncorrupted Version:** Because S3 versioning is enabled, list and download the latest healthy version prior to the corrupted run:
   ```bash
   aws s3api list-object-versions --bucket my-tf-state-bucket --prefix env/prod/terraform.tfstate
   aws s3api get-object --bucket my-tf-state-bucket --key env/prod/terraform.tfstate --version-id <HEALTHY_VERSION_ID> recovered_state.tfstate
   ```
3. **Verify State Integrity:**
   ```bash
   terraform state list -state=recovered_state.tfstate
   ```
4. **Push Recovered State:**
   Force-push the verified state file back to the remote backend:
   ```bash
   terraform state push recovered_state.tfstate
   ```
5. **Run Speculative Plan:** Execute `terraform plan` to ensure that state aligns with live cloud infrastructure and no accidental resource destructions are scheduled.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Can you explain the difference between Security Groups and Network ACLs (NACLs) in AWS?</strong></summary>

**Answer:**
Security Groups and Network ACLs form the core dual-layer network defense in AWS VPC:

1. **Security Groups (Virtual Firewall at Instance Level):**
   - Attached directly to Elastic Network Interfaces (ENIs) of EC2 instances, ALBs, or RDS instances.
   - **Stateful:** If an inbound packet is allowed, return traffic is automatically permitted regardless of outbound rules.
   - Supports **ALLOW rules only**.
   - Evaluates all rules before deciding to allow traffic.

2. **Network ACLs (Subnet Boundary Firewall):**
   - Attached to entire VPC Subnets.
   - **Stateless:** Outbound return traffic must be explicitly permitted in the outbound rules (including ephemeral ports `1024-65535`).
   - Supports both **ALLOW and DENY rules**.
   - Evaluates rules in strict **numerical order** (lowest number evaluated first).
</details>

<details>
<summary><strong>● What is the difference between Service Control Policies (SCPs) and IAM policies in AWS?</strong></summary>

**Answer:**
Both are JSON policy documents, but they operate at different governance hierarchies in AWS:

| Feature | Service Control Policies (SCPs) | IAM Policies |
| :--- | :--- | :--- |
| **Hierarchy Level** | **Organization Level** (Applied to AWS Organization Root, OUs, or Accounts) | **Account Level** (Attached to IAM Users, Groups, or Roles) |
| **Primary Purpose** | Defines **maximum permission boundaries (Guardrails)** across accounts | Grants **explicit permissions** to perform actions on resources |
| **Can it Grant Access?** | **No**. An SCP never grants permissions; it only specifies the maximum allowed actions | **Yes**. Grants permissions within the boundaries allowed by SCPs |
| **Affects Root User?** | **Yes**. SCPs restrict all principals, including the member account's Root user | **No**. IAM policies cannot restrict the account root user |
| **Typical Use Case** | Disabling unapproved AWS regions, preventing disabling of CloudTrail/GuardDuty | Allowing a developer role to manage EC2 instances or S3 buckets |
</details>

<details>
<summary><strong>● How do you configure cross-account access in AWS?</strong></summary>

**Answer:**
Cross-account access is configured using **IAM Roles with STS AssumeRole** federation:

1. **In the Target Account (Account A - Resource Owner):**
   - Create an IAM Role (e.g., `CrossAccountDeployerRole`).
   - Define a **Trust Policy** allowing the external account (Account B) to assume this role:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Principal": { "AWS": "arn:aws:iam::ACCOUNT_B_ID:root" },
           "Action": "sts:AssumeRole"
         }
       ]
     }
     ```
   - Attach permission policies to this role granting access to resources in Account A.

2. **In the Source Account (Account B - Requester):**
   - Create an IAM policy granting Account B's users or CI/CD service role permission to execute `sts:AssumeRole` on Account A's role:
     ```json
     {
       "Effect": "Allow",
       "Action": "sts:AssumeRole",
       "Resource": "arn:aws:iam::ACCOUNT_A_ID:role/CrossAccountDeployerRole"
     }
     ```

3. **Runtime Execution:**
   - The user/script calls AWS STS (`aws sts assume-role`), receiving temporary short-lived credentials (`AccessKeyId`, `SecretAccessKey`, `SessionToken`) to interact with Account A.
</details>

<details>
<summary><strong>● If an external vendor needs access to a specific AWS resource, how would you provide that access?</strong></summary>

**Answer:**
In enterprise security, you **never create IAM users with long-term access keys for external vendors**. Instead, implement **Cross-Account Role Assumption with an External ID**:

1. **Create an IAM Role with an External ID (Prevents Confused Deputy Attack):**
   - Require the vendor to provide their AWS Account ID.
   - Configure a Trust Policy in your account specifying their Account ARN and a unique shared secret string in the `sts:ExternalId` condition:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Principal": { "AWS": "arn:aws:iam::VENDOR_ACCOUNT_ID:root" },
           "Action": "sts:AssumeRole",
           "Condition": {
             "StringEquals": { "sts:ExternalId": "UniqueVendorSecretToken-2026" }
           }
         }
       ]
     }
     ```

2. **Apply Scoped Least-Privilege Permissions:**
   - Attach an IAM policy granting read or write access **only** to the single specific resource required (e.g., read access to `arn:aws:s3:::company-vendor-exchange/*`).

3. **Session Duration & Audit:**
   - Limit the maximum session duration to 1 hour.
   - Monitor all vendor API activities through AWS CloudTrail.
</details>

<details>
<summary><strong>● Can you explain what KMS keys are in AWS and how they are used?</strong></summary>

**Answer:**
**AWS Key Management Service (KMS)** provides centralized control over cryptographic keys used to protect data at rest across AWS services and applications.

**Core Concepts:**
1. **Customer Master Keys (KMS Keys):**
   - **AWS Managed Keys:** Created automatically by AWS services (e.g., `aws/s3`, `aws/ebs`); free, but key policies cannot be modified.
   - **Customer Managed Keys (CMKs):** Created and controlled by the customer. Allows custom key policies, IAM integration, manual/automatic annual rotation, and cross-account sharing.

2. **Envelope Encryption Architecture:**
   - KMS does not encrypt large files directly. Instead, KMS generates a **Data Encryption Key (DEK)**.
   - The application encrypts plaintext data with the plaintext DEK.
   - The plaintext DEK is erased from memory, and the encrypted DEK is stored alongside the encrypted ciphertext.
   - To decrypt, KMS decrypts only the encrypted DEK using the master key.

3. **Key Policies:**
   - The primary resource-based policy that determines *who* has administrative and cryptographic permissions on the key. Every KMS key must have a key policy.
</details>

<details>
<summary><strong>● How do you take backups of resources in AWS?</strong></summary>

**Answer:**
Resource backups in AWS are automated via **AWS Backup**, **Amazon DLM**, and service-native features:

1. **AWS Backup (Centralized Governance):**
   - Configures Backup Plans to automatically snapshot EBS volumes, RDS databases, DynamoDB tables, EFS filesystems, and Aurora clusters.
   - Automates cross-region and cross-account backup replication for disaster recovery.
   - Enforces **AWS Backup Vault Lock** to prevent deletion of backups even by root users.

2. **Amazon Data Lifecycle Manager (DLM):**
   - Automates scheduled EBS volume snapshots and EBS-backed AMI creation with custom retention schedules based on resource tags.

3. **S3 Replication & Versioning:**
   - Buckets maintain versioning to protect against accidental overwrites or deletes, and Cross-Region Replication (CRR) mirrors objects to a secondary region.
</details>

<details>
<summary><strong>● What is the difference between SNS and SQS in AWS?</strong></summary>

**Answer:**
- **Amazon SNS (Simple Notification Service):**
  - **Publish/Subscribe (Pub-Sub)** messaging service.
  - Push-based delivery: A single publisher emits a message to an SNS Topic, which fans out copies immediately to multiple subscribers (SQS, Lambda, HTTPS, email).
  - No message storage: If there are no subscribers, messages are discarded.

- **Amazon SQS (Simple Queue Service):**
  - **Point-to-Point** message queuing service.
  - Pull-based delivery: Consumers poll the queue to retrieve and process messages.
  - Persistent message storage: Holds messages safely for up to 14 days until a consumer processes and deletes them.
  - Provides FIFO queues guaranteeing strict order and exactly-once processing.
</details>

<details>
<summary><strong>● What is a latency-based routing policy in Amazon Route53?</strong></summary>

**Answer:**
A **Latency-Based Routing Policy** in Amazon Route 53 routes user DNS queries to the AWS region that delivers the **lowest network latency** for that specific user.

**How it works:**
1. AWS continuously measures network latency across global internet access points and all AWS regions, maintaining a real-time latency database.
2. When an end-user in Tokyo resolves `api.company.com`, Route 53 inspects the client's resolver IP, checks the latency map, and returns the IP of the endpoint in `ap-northeast-1` (Tokyo).
3. If an end-user in London resolves the same domain, Route 53 returns the endpoint in `eu-west-2` (London).
4. Can be paired with **Route 53 Health Checks** to automatically fail over to an alternate low-latency region if the primary region's endpoint becomes unhealthy.
</details>

<details>
<summary><strong>● What are VPC endpoints in AWS?</strong></summary>

**Answer:**
**VPC Endpoints** enable private connections between your VPC and supported AWS services or third-party services without requiring an Internet Gateway, NAT Gateway, VPN, or Direct Connect. Traffic never leaves the private Amazon network backbone.

**Two Types of VPC Endpoints:**
1. **Gateway Endpoints:**
   - Free of charge.
   - Operates by adding an entry in your VPC route table pointing traffic to the service prefix list.
   - **Supported for only two services:** **Amazon S3** and **Amazon DynamoDB**.
2. **Interface Endpoints (powered by AWS PrivateLink):**
   - Deploys an Elastic Network Interface (ENI) with a private IP directly into your subnet.
   - Incurs hourly charges + data processing fees.
   - Supported for 100+ AWS services (ECR, KMS, Secrets Manager, CloudWatch Logs, SSM) and custom SaaS applications.
</details>

<details>
<summary><strong>● What is AWS DataSync?</strong></summary>

**Answer:**
**AWS DataSync** is an online, high-performance data transfer service that simplifies, automates, and accelerates moving petabytes of data between on-premises storage systems and AWS storage services, or between different AWS storage services.

**Key Capabilities:**
- **Speed:** Uses a purpose-built network protocol up to **10x faster** than open-source tools like rsync.
- **Source & Targets:** Transfers data between Network File System (NFS), Server Message Block (SMB), HDFS, object stores, and AWS services (Amazon S3, Amazon EFS, Amazon FSx).
- **Data Integrity & Verification:** Automatically verifies data integrity both in transit (TLS encrypted) and at rest using checksums.
- **Automation:** Handles scheduling, bandwidth throttling, incremental delta transfers, and error retries natively.
</details>

<details>
<summary><strong>● What is the difference between a public subnet and a private subnet in AWS?</strong></summary>

**Answer:**
The distinction lies entirely in the **Route Table configuration** attached to the subnet:

- **Public Subnet:**
  - Its route table contains an explicit route sending default internet-bound traffic (`0.0.0.0/0`) directly to an **Internet Gateway (`igw-xxxx`)**.
  - Resources can be assigned Public IPs / Elastic IPs and can be directly accessed from the internet.
  - Used for internet-facing load balancers (ALBs) and NAT Gateways.

- **Private Subnet:**
  - Its route table **does not** route directly to an Internet Gateway.
  - Internet-bound traffic (`0.0.0.0/0`) is routed to a **NAT Gateway (`nat-xxxx`)** located in a public subnet, or it has no internet route at all (isolated subnet).
  - Instances only have private IPs (RFC 1918) and cannot be directly reached from the public internet.
</details>

<details>
<summary><strong>● What is AWS Control Tower?</strong></summary>

**Answer:**
**AWS Control Tower** is a managed service that automates the setup of a secure, multi-account AWS environment based on AWS best practices, establishing an enterprise **"Landing Zone"**.

**Key Features:**
1. **Landing Zone Automation:** Automatically configures AWS Organizations, centralized identity (IAM Identity Center), and core accounts (Log Archive Account and Security Audit Account).
2. **Account Factory:** Provides an automated workflow to provision new, pre-configured AWS accounts that automatically inherit security baselines and networking.
3. **Guardrails (Governance & Compliance):**
   - **Preventive Guardrails:** Enforced via Service Control Policies (SCPs) to stop unauthorized actions (e.g., preventing public S3 buckets or disabling CloudTrail).
   - **Detective Guardrails:** Enforced via **AWS Config** rules to continuously audit and flag compliance violations.
</details>

<details>
<summary><strong>● What is a lifecycle policy in Amazon S3?</strong></summary>

**Answer:**
An **Amazon S3 Lifecycle Policy** is an automated rule set defined on an S3 bucket to manage object storage costs and retention throughout their lifecycle.

**Core Actions Defined in Lifecycle Rules:**
1. **Transition Actions:** Automatically moves objects to lower-cost storage classes based on age:
   - *Example:* Transition objects to S3 Standard-IA after 30 days, to S3 Glacier Flexible Retrieval after 90 days, and to S3 Glacier Deep Archive after 180 days.
2. **Expiration Actions:** Permanently deletes objects after a specified retention period (e.g., delete application logs after 365 days).
3. **Noncurrent Version Management:** Automatically cleans up older object versions or deletes expired object delete markers in versioned buckets.
</details>

<details>
<summary><strong>● What are AWS Step Functions?</strong></summary>

**Answer:**
**AWS Step Functions** is a serverless visual workflow orchestration service that allows developers to coordinate distributed applications, microservices, and AWS services into sequential, resilient **State Machines**.

**Core Capabilities:**
- **Visual Workflows:** Workflows are defined using Amazon States Language (JSON/YAML) and visualized graphically in the AWS console.
- **Built-in Error Handling:** Native support for `Retry` policies (exponential backoff) and `Catch` blocks for graceful failure recovery without writing boilerplate error-handling code.
- **Service Integrations:** Directly invokes AWS Lambda, runs ECS/Fargate tasks, triggers AWS Batch jobs, or pauses for human approval via SNS/SQS.
- **Types of Workflows:**
  - **Standard Workflows:** For long-running, auditable workflows (up to 1 year) with exactly-once execution.
  - **Express Workflows:** For high-throughput, short-duration (up to 5 mins) event-processing workflows.
</details>

<details>
<summary><strong>● How can you replicate data to a different region in Amazon S3?</strong></summary>

**Answer:**
Cross-region data replication in S3 is achieved using **S3 Cross-Region Replication (CRR)**:

**Prerequisites & Configuration:**
1. **Enable Versioning:** S3 Versioning must be explicitly enabled on **both** the source bucket and destination bucket.
2. **IAM Replication Role:** Create an IAM service role allowing Amazon S3 permissions to read objects and versioning from the source bucket and replicate them (`s3:ReplicateObject`, `s3:ReplicateDelete`) to the destination bucket.
3. **Configure Replication Rule:**
   - Specify whether to replicate the entire bucket or a filtered prefix/tag.
   - Choose whether to replicate KMS-encrypted objects and provide the destination KMS Key ARN for automatic re-encryption.
   - Enable **S3 Replication Time Control (S3 RTC)** if your business requires an SLA guaranteeing 99.99% of objects replicate within 15 minutes.
</details>

<details>
<summary><strong>● What is the AWS service that allows you to view all the resources you have created in your account?</strong></summary>

**Answer:**
**AWS Resource Explorer** is the dedicated resource search and discovery service that allows you to search for, view, and organize all your resources (EC2, S3, RDS, IAM, VPC) across all AWS regions.

**Complementary Discovery Services:**
- **AWS Config:** Continuously discovers and records configuration histories, relationships, and compliance status for all resources in your account.
- **AWS Tag Editor (Resource Groups):** Allows you to search for resources across multiple regions and services based on tag keys and values.
</details>

<details>
<summary><strong>● What are resource-based policies in AWS?</strong></summary>

**Answer:**
**Resource-Based Policies** are JSON policy documents attached directly to a specific AWS resource (rather than to an IAM identity like a user or role).

**Key Examples:**
- **S3 Bucket Policies:** Controls who can access objects inside a bucket.
- **AWS KMS Key Policies:** Controls who can use the cryptographic key.
- **IAM Role Trust Policies:** Specifies which entities (principals) can assume the role.
- **AWS Lambda Function Policies:** Grants API Gateway or S3 permission to invoke the function.

**Critical Characteristics:**
- Resource-based policies **must explicitly declare the `Principal` element** (specifying *who* is granted or denied access).
- Enables **direct cross-account access**: If a resource-based policy grants access to a principal in Account B, that principal can access the resource immediately without assuming an IAM role in Account A.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● Can you explain AWS CloudWatch and AWS CloudTrail, and how they differ?</strong></summary>

**Answer:**
Both are essential AWS monitoring and governance services, but they serve completely distinct purposes:

| Feature | AWS CloudWatch | AWS CloudTrail |
| :--- | :--- | :--- |
| **Core Question Answered** | **"What is happening right now?"** (Performance & Health) | **"Who did what, when, and from where?"** (Auditing & Governance) |
| **Primary Data Type** | **Metrics, Alarms, and Application Logs** | **API Activity & Event History Logs** |
| **Focus Area** | Resource utilization (CPU, memory, disk I/O), application logs, alerting thresholds | Security auditing, compliance tracking, and detecting unauthorized changes |
| **Trigger Mechanism** | Gathers telemetry periodically (e.g., 1-minute or 5-minute metric datapoints) | Records API calls whenever an action is performed via Console, CLI, SDK, or internal service |
| **Example Scenario** | Alarm triggers when ALB latency exceeds 300ms or EC2 CPU exceeds 80% | Identifies which IAM user modified a Security Group rule or deleted an S3 bucket at 02:15 AM |
</details>
</details>
</details>

<details open>
<summary><h2>🏢 Mindteck</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 20-08-2026 11:34 PM*

#### 【 LINUX 】

<details>
<summary><strong>● Have you worked with virtualization technologies such as virtual machines (VMs)?</strong></summary>

**Answer:**
Yes, I have extensive experience operating and automating enterprise virtualization platforms, including **VMware vSphere/ESXi**, **Microsoft Hyper-V**, and **KVM/QEMU**, alongside cloud compute (AWS EC2).

**Key Responsibilities:**
- Provisioning and configuring virtual machines, virtual switches (vSwitch), VLAN trunking, and storage fabrics (iSCSI, Fibre Channel, NFS datastores).
- Automating VM lifecycle management using **Packer** (building standardized golden VM images), **Terraform** (vSphere provider), and **Ansible** for post-boot configuration.
- Diagnosing hypervisor-to-guest resource contention, CPU ready time (`%RDY`), memory ballooning, and disk I/O scheduling bottlenecks.
</details>

<details>
<summary><strong>↳ Follow-up: If a Hyper-V-hosted VM (among 20-25 VMs) running a database is experiencing high I/O latency, but its resource utilization metrics (CPU, memory) appear normal, how would you troubleshoot and confirm what is actually causing the issue?</strong></summary>

**Answer:**
When a virtualized database suffers from severe disk I/O latency while guest CPU and memory metrics are nominal, the bottleneck is almost always caused by **storage subsystem contention, hypervisor disk queueing, or configuration anomalies**:

1. **Investigate Storage Contention ("Noisy Neighbor" Problem):**
   - On the **Hyper-V Host**, open Performance Monitor (`perfmon`) to check physical disk counters:
     - `\PhysicalDisk(*)\Avg. Disk sec/Read` and `\Avg. Disk sec/Write`: Normal latency is <10ms; if latency is >25–50ms, the underlying storage fabric is saturated.
     - `\PhysicalDisk(*)\Current Disk Queue Length`: If queue length significantly exceeds `2 * (Number of Disks in Array)`, requests are queueing up at the hardware layer.
   - Inspect individual VM storage metrics via `\Hyper-V Virtual Storage Device(*)\*` to determine if another VM sharing the same physical LUN/CSV (Cluster Shared Volume) is generating an unexpected storm of random I/O.

2. **Check for Active Hyper-V Checkpoints (Snapshots):**
   - Check if the database VM has outstanding checkpoints. Active checkpoints force Hyper-V to write to differencing disks (`.avhdx`), creating an extensive read/write tree traversal that degrades database I/O by 40–70%.
   - **Resolution:** Delete/merge checkpoints during a maintenance window.

3. **Verify Virtual Controller & Disk Type:**
   - Ensure the database virtual disk is attached to a **Synthetic SCSI Controller** (not an emulated IDE controller).
   - Ensure the virtual hard disk is **Fixed Size VHDX** or a pass-through disk, rather than a **Dynamically Expanding VHDX** (which causes severe metadata allocation pauses during database write bursts).

4. **Guest OS Storage Alignment & Queue Depth:**
   - Inside the Linux database VM, execute `iostat -xz 1` to inspect `%util`, `await`, and `r_await/w_await`.
   - If `await` is high but throughput (`r/s`, `w/s`) is low, it confirms that storage I/O requests are being choked at the hypervisor or SAN level.
</details>

<details>
<summary><strong>● Do you have hands-on experience with Linux administration, including memory management?</strong></summary>

**Answer:**
Yes, I possess deep Linux systems administration experience with a strong emphasis on kernel memory subsystems and performance tuning:

- **Memory Analysis:** Interpreting `free -m`, `vmstat 1`, and `/proc/meminfo` to distinguish between active application memory (RSS), page cache, buffers, and swap usage.
- **Kernel Tuning:** Tuning kernel parameters via `/etc/sysctl.conf`:
  - `vm.swappiness`: Reducing default `60` down to `1` or `10` on database and Kubernetes nodes to avoid swapping active processes.
  - `vm.vfs_cache_pressure`: Balancing inode/dentry cache reclamation.
  - `vm.overcommit_memory` and `vm.dirty_ratio`: Optimizing dirty page flush thresholds for high-throughput write workloads.
- **OOM Killer Diagnostics:** Investigating system terminations by analyzing `dmesg -T | grep -i oom` and evaluating `/proc/<PID>/oom_score`.
</details>

<details>
<summary><strong>↳ Follow-up: How would you extend an LVM (Logical Volume Manager) partition in Linux? Can you walk through the commands or steps involved in the process?</strong></summary>

**Answer:**
Extending an LVM volume online (without unmounting or downtime) follows a sequential 4-step workflow: **Physical Disk/Partition -> Physical Volume (PV) -> Volume Group (VG) -> Logical Volume (LV) -> Filesystem Resize**.

**Step-by-Step Scenario:** Adding a new 50GB virtual disk (`/dev/sdb`) to extend the `/var/log` filesystem hosted on `/dev/vg_data/lv_logs`:

```bash
# Step 1: Scan for the newly attached disk (if not detected automatically)
echo "- - -" > /sys/class/scsi_host/host0/scan
lsblk

# Step 2: Initialize the new physical disk as a Physical Volume (PV)
pvcreate /dev/sdb
pvs  # Verify physical volume creation

# Step 3: Extend the existing Volume Group (VG)
vgextend vg_data /dev/sdb
vgs  # Verify new free space in vg_data

# Step 4: Extend the Logical Volume (LV)
# Option A: Add a specific size (+50GB)
lvextend -L +50G /dev/vg_data/lv_logs
# Option B: Allocate 100% of remaining free space in the VG
# lvextend -l +100%FREE /dev/vg_data/lv_logs

# Step 5: Resize the underlying filesystem online (No unmount needed)
# For XFS filesystems (pass the MOUNT POINT):
xfs_growfs /var/log

# For EXT4 filesystems (pass the LV DEVICE PATH):
# resize2fs /dev/vg_data/lv_logs

# Step 6: Verify the newly expanded capacity
df -h /var/log
```
*(Note: If resizing an existing virtual disk `/dev/sda2` rather than adding a new disk, run `pvresize /dev/sda2` instead of `pvcreate` and proceed directly to `lvextend`).*
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● How would you design an end-to-end CI/CD pipeline for an application, covering how you would maintain security and credentials, and how you would handle rollback in case of an error or failure in the production pipeline?</strong></summary>

**Answer:**
I design enterprise pipelines following **Shift-Left Security** and **GitOps-driven Progressive Delivery**:

1. **Pipeline Architecture:**
   - **CI Phase (GitHub Actions / Jenkins):** Code linting -> SAST (SonarQube) -> Dependency CVE check (Snyk) -> Multi-stage Docker build -> Container scanning (Trivy) -> Image signing with **Cosign** -> Push to AWS ECR.
   - **CD Phase (GitOps with Argo CD):** Image tag updated in Helm repository via automated PR -> Argo CD detects drift -> Syncs to Kubernetes cluster.

2. **Security & Credential Management:**
   - **Zero Long-Term Secrets:** Eliminate hardcoded passwords and long-term AWS access keys. CI agents assume temporary short-lived AWS IAM roles using **OpenID Connect (OIDC)** federated with GitHub/Jenkins.
   - **Runtime Secrets:** Kubernetes microservices retrieve database passwords and API keys dynamically via the **External Secrets Operator (ESO)** directly from **AWS Secrets Manager** or HashiCorp Vault.
   - **Least Privilege:** Pipeline service accounts have permissions restricted solely to ECR image pushing and updating the specific Helm config repository.

3. **Production Rollback Strategy:**
   - **Automated Canary Rollback:** Using **Argo Rollouts**, the new version is exposed to 10% traffic. Prometheus queries monitor error rates and latency. If HTTP 5xx errors exceed 0.1%, Argo Rollouts halts and rolls traffic back to 100% stable version in seconds with zero human intervention.
   - **Manual Emergency Rollback:** If issues emerge post-promotion, reverting the commit in the Git Helm repository triggers Argo CD to immediately converge the cluster back to the previous stable release.
</details>

<details>
<summary><strong>↳ Follow-up: If a Trivy image scanning stage in your CI/CD pipeline starts taking much longer than expected (e.g., 30 minutes to an hour instead of the expected benchmark), and the team complains about this delay, how would you optimize the Trivy scanning stage?</strong></summary>

**Answer:**
A 30- to 60-minute Trivy scan is almost always caused by **repeatedly re-downloading the vulnerability database** or scanning unneeded directories. I apply four key optimizations to reduce scan time to under 90 seconds:

1. **Persist the Trivy Vulnerability Database Cache:**
   - By default, Trivy downloads the multi-hundred-megabyte vulnerability database on every execution.
   - **Fix:** Mount a persistent volume cache or configure CI caching (`--cache-dir /var/cache/trivy`). In GitHub Actions:
     ```yaml
     - name: Cache Trivy Vulnerability Database
       uses: actions/cache@v3
       with:
         path: ~/.cache/trivy
         key: trivy-db-${{ runner.os }}-${{ steps.date.outputs.date }}
     ```

2. **Deploy Trivy in Client/Server Mode:**
   - Deploy a centralized **Trivy Server** as a service in the Kubernetes cluster.
   - CI build runners execute as lightweight clients (`trivy image --server http://trivy-server:4954 myimage:tag`). The server maintains the warm, pre-downloaded database in memory, eliminating database download overhead completely.

3. **Targeted Vulnerability Scans:**
   - Restrict scan scopes to actionable production vulnerabilities:
     ```bash
     trivy image --vuln-type os,library --severity HIGH,CRITICAL --ignore-unfixed <image>
     ```
   - `--ignore-unfixed`: Excludes vulnerabilities that have no vendor patch available, saving scan and triage time.

4. **Exclude Unnecessary Directories:**
   - Pass `.trivyignore` or `--skip-dirs` to bypass test fixtures, documentation, and cached build artifacts.
</details>

<details>
<summary><strong>↳ Follow-up: If your pipeline passes the build stage successfully but starts failing when pushing the Docker image to the ECR (or any container) registry, what are the possible reasons for this failure and how would you troubleshoot it?</strong></summary>

**Answer:**
Push failures to AWS ECR typically stem from four root causes:

1. **Authentication Token Expiry:**
   - ECR authentication tokens generated via `aws ecr get-login-password` expire after **12 hours**. If a long-running pipeline or agent uses a cached token, `docker push` fails with `denied: Your authorization token has expired` or `no basic auth credentials`.
   - **Fix:** Ensure `aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account_id>.dkr.ecr.<region>.amazonaws.com` runs immediately before the push stage.

2. **Non-Existent ECR Repository:**
   - AWS ECR requires the repository to exist before pushing; unlike Docker Hub, it does not auto-create repositories by default.
   - **Fix:** Verify repository existence using `aws ecr describe-repositories --repository-names <repo-name>` or automate repository creation via Terraform.

3. **Insufficient IAM Permissions:**
   - The IAM role assigned to the CI agent lacks necessary push actions.
   - **Fix:** Verify the role policy includes:
     - `ecr:CompleteLayerUpload`
     - `ecr:UploadLayerPart`
     - `ecr:InitiateLayerUpload`
     - `ecr:BatchCheckLayerAvailability`
     - `ecr:PutImage`

4. **Network & VPC Endpoint Issues:**
   - Private runners lacking outbound routes or missing ECR VPC Endpoints.
</details>

<details>
<summary><strong>↳ Follow-up: When troubleshooting the failure to push images to the registry, would you also check anything related to network connectivity, and if so, what steps would you take?</strong></summary>

**Answer:**
Yes, network connectivity is a frequent failure point, especially when CI/CD agents run inside private subnets:

1. **DNS Resolution Verification:**
   - Test if the agent resolves the ECR endpoint:
     ```bash
     nslookup <account_id>.dkr.ecr.<region>.amazonaws.com
     dig +short <account_id>.dkr.ecr.<region>.amazonaws.com
     ```

2. **TCP Port 443 Handshake Test:**
   - Verify HTTPS connectivity to ECR over port 443:
     ```bash
     nc -zv <account_id>.dkr.ecr.<region>.amazonaws.com 443
     # or
     curl -Iv https://<account_id>.dkr.ecr.<region>.amazonaws.com
     ```

3. **Inspect Subnet Routing & NAT Gateway:**
   - If the CI agent is in a private VPC subnet, verify that its route table has `0.0.0.0/0` pointed to an active **NAT Gateway**, and that the NAT Gateway has available Elastic IP bandwidth and zero port exhaustion.

4. **Verify AWS PrivateLink VPC Endpoints (If No Internet Route):**
   - In fully private clusters, ECR pushes require **three VPC Endpoints**:
     - `com.amazonaws.<region>.ecr.api` (Interface Endpoint)
     - `com.amazonaws.<region>.ecr.dkr` (Interface Endpoint)
     - `com.amazonaws.<region>.s3` (Gateway Endpoint — required because ECR stores image layers in S3 buckets!). If the S3 Gateway Endpoint is missing, layer upload initiation succeeds but pushing layer blobs hangs indefinitely.
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● Do you have hands-on experience working with Docker?</strong></summary>

**Answer:**
Yes, I have extensive production experience containerizing enterprise microservices with Docker:

- Authoring secure, optimized **multi-stage Dockerfiles** using Distroless and Alpine base images.
- Enforcing security best practices: running containers as non-root users (`USER 1001`), dropping Linux capabilities (`cap-drop=ALL`), and setting read-only root filesystems.
- Managing container networking (bridge, host, overlay) and volume mounts for persistent data.
- Diagnosing container runtime crashes, PID 1 zombie process reapings, and resource bottlenecks using `docker stats`, `docker inspect`, and `docker logs`.
</details>

<details>
<summary><strong>↳ Follow-up: If a Docker container is unable to connect to an external database and you receive a connection timeout error, how would you troubleshoot this issue and what components would you check to fix it?</strong></summary>

**Answer:**
A connection timeout indicates that packets are being silently dropped along the network path. I troubleshoot this methodically:

1. **Test Connectivity from Inside the Container:**
   - Exec into the container and test DNS and TCP reachability:
     ```bash
     docker exec -it <container_id> /bin/sh
     # Test DNS resolution
     getent hosts db.company.internal
     # Test TCP handshake to database port
     nc -zv db.company.internal 5432
     ```
   - *Result:* If `nc` hangs and times out, the problem is network routing or firewall drops.

2. **Check Database Security Groups & Network Firewalls:**
   - If the database is on AWS RDS, inspect the RDS Security Group: Does it allow inbound TCP port 5432/3306 from the **Host IP** or the **VPC Subnet CIDR** where the Docker host resides?

3. **Check Docker Host Network & Iptables:**
   - Docker manages host iptables rules for container NAT (`POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE`).
   - If someone reloaded `firewalld` or `ufw` on the host, Docker's custom iptables chains may have been flushed, breaking container outbound forwarding. Fix: `systemctl restart docker`.

4. **Verify Database Server Listening Address:**
   - On the database host, confirm that PostgreSQL/MySQL is listening on all interfaces (`0.0.0.0`) and not strictly on `127.0.0.1` (`bind-address = 0.0.0.0` in configuration).
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● If an EKS cluster is shared by 3-4 teams and a security audit reveals that most team members have cluster-admin privileges (violating least-privilege principles), how would you redesign access control for the cluster to follow security best practices?</strong></summary>

**Answer:**
I would execute a comprehensive **RBAC Redesign** establishing strict multi-tenancy and least privilege:

1. **Namespace Isolation:**
   - Segment workloads into dedicated namespaces for each team: `team-payments`, `team-analytics`, `team-identity`.

2. **Replace ClusterRoleBindings with Namespace-Scoped RoleBindings:**
   - Revoke all global `cluster-admin` bindings for developers.
   - Define granular `Roles` within each team's namespace granting CRUD access only to application workloads (`deployments`, `pods`, `services`, `configmaps`, `ingresses`), while blocking access to cluster-scoped resources (`nodes`, `persistentvolumes`, `storageclasses`, `namespaces`).

3. **Centralized Identity & Access Management (EKS Access Entries):**
   - Leverage AWS EKS **Access Entries** and IAM Identity Center (SSO).
   - Create distinct IAM Roles mapped to enterprise security groups:
     - `EKS-Cluster-Admins-Role` (Infra team: break-glass administrative access).
     - `EKS-Team-Payments-Role` (Dev team: bound strictly to `team-payments` namespace).

4. **Admission Control & Policy Enforcement:**
   - Deploy **Kyverno** or **OPA Gatekeeper** to programmatically enforce policies (e.g., blocking pods running as root, requiring resource limits, and preventing developers from creating ingress rules that clash with other teams).
</details>

<details>
<summary><strong>↳ Follow-up: When designing RBAC roles for an EKS cluster, do you configure roles on a team basis or user basis (e.g., for admins vs. regular team members)? How would you differentiate the access level and role configuration between a team member and an administrator?</strong></summary>

**Answer:**
In production enterprise clusters, RBAC roles are **strictly configured on a TEAM and ROLE basis**, never for individual users. Binding individual users creates administrative sprawl, high operational overhead, and compliance risks when personnel change.

**Architecture for Team vs. Admin Differentiation:**

1. **Team Members (Namespace-Scoped Developer Role):**
   - **Scope:** Bound to specific team namespaces using `RoleBinding`.
   - **Permissions:** Read/Write on application workloads (`deployments`, `pods`, `services`, `horizontalpodautoscalers`). Read-only on `secrets` and `configmaps`.
   - **Forbidden:** No access to RBAC modifications (`roles`, `rolebindings`), network policies, CRDs, or cluster-scoped infrastructure.
   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: Role
   metadata:
     namespace: team-payments
     name: team-developer-role
   rules:
     - apiGroups: ["", "apps"]
       resources: ["pods", "deployments", "services", "configmaps"]
       verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
     - apiGroups: [""]
       resources: ["pods/log", "pods/exec"]
       verbs: ["get", "list", "create"]
   ```

2. **Cluster Administrators (Cluster-Scoped Admin Role):**
   - **Scope:** Bound across the entire cluster using `ClusterRoleBinding` mapped to the `EKS-Platform-Admins` IAM role.
   - **Permissions:** Full `cluster-admin` privileges across all namespaces, managing nodes, storage classes, mutating webhooks, and cluster upgrades.
   - **Governance:** Access requires MFA and Single Sign-On (SSO), with all sessions logged in AWS CloudTrail and Kubernetes Audit Logs.
</details>

<details>
<summary><strong>● Have you worked with Kubernetes?</strong></summary>

**Answer:**
Yes, I have over 5 years of production Kubernetes experience, primarily operating managed AWS EKS clusters:

- Architecting multi-tenant clusters, implementing network policies, and managing cluster upgrades with zero downtime.
- Deploying microservices using **Helm** charts and GitOps automation via **Argo CD**.
- Managing autoscaling using **Karpenter** (node level) and **HPA/KEDA** (pod level).
- Operating observability stacks (Prometheus Operator, Grafana, OpenSearch) and service meshes (Istio).
</details>

<details>
<summary><strong>↳ Follow-up: If, after deploying a production pod, you check its status and see a CrashLoopBackOff error, what could be the possible reasons for this, and how would you troubleshoot it?</strong></summary>

**Answer:**
`CrashLoopBackOff` indicates that Kubelet started the container, but the process terminated with a non-zero exit code or failed liveness checks repeatedly.

**Top Root Causes & Troubleshooting Workflow:**
1. **OOMKilled (Exit Code 137):** Container memory consumption exceeded `resources.limits.memory`.
   - *Verify:* `kubectl describe pod <pod-name>` shows `Last State: Terminated (Reason: OOMKilled)`.
   - *Fix:* Increase memory limits or profile application memory leaks.
2. **Missing Configuration / Secrets (Exit Code 1 or 2):** Application crashed on startup because a referenced environment variable, ConfigMap, or Secret was missing or malformed.
   - *Verify:* Run `kubectl logs <pod-name> --previous` to inspect the fatal exception message.
3. **Misconfigured Liveness / Startup Probes:** The liveness probe evaluated `/health` before the application finished booting.
   - *Fix:* Introduce a `startupProbe` with adequate `failureThreshold` and `periodSeconds`.
4. **Command / Entrypoint Syntax Errors (Exit Code 127):** Binary or script specified in `command:` not found in container filesystem.
</details>

#### 【 IAC 】

<details>
<summary><strong>● Do you have experience working with Terraform?</strong></summary>

**Answer:**
Yes, I have extensive experience managing enterprise cloud infrastructure using **Terraform** and **OpenTofu**:

- Designing modular, reusable Terraform architectures for VPCs, EKS clusters, RDS databases, and IAM policies.
- Managing remote state across multi-account AWS environments using S3 with DynamoDB state locking.
- Implementing automated IaC pipelines with **Atlantis** and GitHub Actions, incorporating static analysis (`tflint`, `tfsec`, `checkov`).
- Executing resource imports, state refactoring (`terraform state mv`), and automated drift detection.
</details>

<details>
<summary><strong>↳ Follow-up: If someone manually changes production infrastructure that is managed by Terraform, causing the Terraform state file to become out of sync with the actual infrastructure and resulting in breaking changes, how would you handle this incident and what measures would you implement to prevent it from happening in the future?</strong></summary>

**Answer:**
**Incident Response Workflow:**
1. **Freeze Pipelines & Audit:** Pause automated CI/CD Terraform apply jobs. Query **AWS CloudTrail** to identify the engineer, timestamp, and exact API parameters of the manual console modification.
2. **Inspect Drift:** Execute `terraform plan` to compare the live cloud reality against the state and codebase.
3. **Resolve Drift:**
   - *If the change was improper/accidental:* Execute `terraform apply` to immediately overwrite the manual drift and restore infrastructure back to the validated code state.
   - *If the change was a necessary emergency hotfix:* Update the Terraform HCL code to match the new live configuration. Run `terraform plan` to confirm the diff is zero, then merge the code into Git.

**Preventive Governance Measures:**
1. **Enforce Service Control Policies (SCPs):** Implement an SCP in the AWS Organization that denies write actions (`ec2:*`, `s3:*`, `rds:*`) to human IAM users/roles in production accounts, forcing all changes to go through the CI/CD pipeline.
2. **Scheduled Drift Detection:** Run a scheduled nightly pipeline executing `terraform plan -detailed-exitcode` that pages DevOps if unexpected drift occurs.
</details>

<details>
<summary><strong>↳ Follow-up: Can you explain how drift detection actually works in Terraform?</strong></summary>

**Answer:**
Terraform drift detection works through a **Three-Way Comparison** during the `terraform plan` phase:

```
[ Desired State (HCL Code) ] <---+
                                 |  (3-Way Diff Comparison)
[ Prior State (.tfstate) ]    <--+--> [ Execution Plan Output ]
                                 |    - No changes (Clean)
[ Actual State (Live Cloud) ] <--+    - Drift detected (+ / ~ / -)
(Queried via Provider API)
```

1. **Refresh Phase:** Terraform calls the cloud provider's `Read` API for every resource listed in the state file.
2. **State Alignment:** Terraform updates its in-memory representation of the state with the real-world resource attributes returned by AWS.
3. **Reconciliation & Diff Generation:** Terraform compares:
   - **Code vs. Live Reality:** If an attribute exists in live AWS but differs from the code, Terraform marks it as an update in-place (`~`).
   - **Missing in Cloud:** If a resource is in state but was deleted manually in the console, Terraform plans to recreate it (`+`).
4. **Exit Code Flagging:** In CI/CD pipelines, running `terraform plan -detailed-exitcode` returns exit code `0` for zero changes, `2` if drift/changes are detected, and `1` if an error occurs.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Do you mostly work with AWS cloud services?</strong></summary>

**Answer:**
Yes, AWS is my primary cloud platform. I have over 6 years of deep architectural and operational experience building scalable, secure, and cost-effective enterprise platforms on AWS across multiple regions and accounts.
</details>

<details>
<summary><strong>↳ Follow-up: Do you have experience designing services using AWS EC2?</strong></summary>

**Answer:**
Yes, I have designed numerous production architectures leveraging EC2:

- Architecting **Auto Scaling Groups (ASGs)** across multiple Availability Zones with custom Launch Templates and predictive scaling.
- Implementing mixed-instance policies combining **On-Demand** and **Spot Instances** to reduce compute costs by up to 60%.
- Managing AMI creation pipelines using **HashiCorp Packer** with CIS security benchmarks.
- Securing EC2 access using **AWS Systems Manager (SSM) Session Manager**, eliminating the need for public IP addresses, bastion hosts, or open SSH port 22.
</details>

<details>
<summary><strong>● If you needed to design a highly available, globally accessible architecture for an engineering team with clients in multiple locations—using EC2 for compute and RDS for the database—how would you approach the design? What specific components would you use to achieve high availability across multiple zones?</strong></summary>

**Answer:**
I would design a **Multi-AZ, Multi-Tier Architecture** fronted by AWS global routing:

```
[ Global Clients ]
        |
        v
[ Amazon Route 53 (Latency-Based Routing + Health Checks) ]
        |
        v
[ AWS CloudFront CDN (Global Edge Caching & SSL Termination) ]
        |
        v
[ AWS WAF (Web Application Firewall) ]
        |
        v
[ Application Load Balancer (ALB) - Public Subnets across 3 AZs ]
        |
        v
[ EC2 Auto Scaling Group - Private Subnets across 3 AZs ]
  - Launch Template with target tracking scaling (CPU > 60%)
        |
        v
[ Amazon RDS Multi-AZ Deployment - Isolated Subnets across 3 AZs ]
  - Primary Instance (Active Read/Write in AZ-a)
  - Synchronous Standby Replica (Passive in AZ-b with automated failover)
  - Cross-AZ Read Replicas (Asynchronous for read-heavy scaling)
```

**High Availability Components Across Multiple Zones:**
1. **Traffic Routing:** Route 53 with Latency-Based routing and automated failover.
2. **Load Balancing:** Application Load Balancer distributing requests across 3 Availability Zones.
3. **Compute Resilience:** Auto Scaling Group spanning 3 private subnets with a minimum capacity of 3 instances (1 per AZ).
4. **Database Resilience:** RDS **Multi-AZ synchronous replication**. If AZ-a fails, RDS automatically switches DNS to the standby replica in AZ-b within 60–120 seconds with zero data loss.
</details>

<details>
<summary><strong>↳ Follow-up: If some of your applications have read-heavy workloads with frequent read operations, would you configure anything specific to handle this, and if so, what?</strong></summary>

**Answer:**
To scale read-heavy workloads and protect the primary database from saturation, I implement a **Three-Tier Read Optimization Architecture**:

1. **In-Memory Caching (Amazon ElastiCache Redis):**
   - Place a Redis cluster in front of the database using a **Cache-Aside (Lazy Loading)** pattern. Frequently read queries (e.g., user profiles, catalog data) are served from cache in sub-milliseconds, offloading 80%+ of read queries.

2. **Amazon RDS Read Replicas:**
   - Deploy up to 5 **asynchronous Read Replicas** across multiple Availability Zones.
   - In the application configuration, split database connections: direct all `INSERT`, `UPDATE`, `DELETE` transactions to the Primary RDS Endpoint, and direct all `SELECT` queries to the **RDS Reader Endpoint** (which load balances read queries across all read replicas).

3. **Aurora Auto-Scaling Replicas (If using Amazon Aurora):**
   - Aurora automatically adds read replicas dynamically based on CPU utilization or connection load, scaling up to 15 replicas.
</details>

<details>
<summary><strong>↳ Follow-up: If an application behind an Application Load Balancer (ALB) suddenly starts experiencing a 504 gateway timeout, how would you troubleshoot and resolve this issue?</strong></summary>

**Answer:**
An **HTTP 504 Gateway Timeout** indicates that the Application Load Balancer established a connection to the backend EC2 target, but the target **failed to respond within the configured ALB Idle Timeout period (default: 60 seconds)**.

**Troubleshooting & Resolution Steps:**
1. **Identify the Slow Component:**
   - Inspect **CloudWatch ALB Metrics**: Check `TargetResponseTime`. If target response time spikes to 60 seconds matching the 504 errors, the problem is 100% inside the backend application or database.
   - Check ALB access logs to identify which specific URL path/endpoint is timing out.

2. **Diagnose Backend EC2 Targets:**
   - Check EC2 CPU and memory saturation (`top`, `free -m`).
   - Check application thread dumps and database connection pool metrics (e.g., HikariCP exhaustion). A slow query holding database table locks causes all subsequent requests to queue up and breach the 60s timeout.

3. **Check Target Keep-Alive Settings:**
   - Verify that the application server (e.g., Nginx, Tomcat) has a **Keep-Alive timeout greater than the ALB Idle Timeout**. If the backend server closes the TCP connection before the ALB does, it can cause transient gateway errors.

4. **Resolution:**
   - Optimize slow database queries and add missing indexes.
   - If the endpoint legitimately performs heavy file processing or report generation, increase the ALB Idle Timeout attribute (e.g., up to 300 seconds) as a temporary measure, while re-architecting the workload to run asynchronously via SQS and worker tasks.
</details>

<details>
<summary><strong>● What is the difference between an AWS Service Control Policy (SCP) and an IAM policy?</strong></summary>

**Answer:**
- **Service Control Policy (SCP):**
  - Applied at the **AWS Organizations** level (Root, Organizational Unit, or Account).
  - Specifies the **maximum boundary of allowed permissions** for all accounts in the OU.
  - Does **not** grant permissions; it acts as a guardrail filter.
  - Applies to **all principals**, including the member account's Root user!
- **IAM Policy:**
  - Applied within an individual AWS account to users, groups, or roles.
  - Grants explicit permissions to access specific resources.
  - Can only grant permissions that are permitted by the overarching SCP.
</details>
</details>
</details>

<details open>
<summary><h2>🏢 Virtusa</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 22-08-2026 11:05 AM*

#### 【 LINUX 】

<details>
<summary><strong>● Have you worked with Linux servers in your role?</strong></summary>

**Answer:**
Yes, Linux is the foundational operating system across all my DevOps and cloud engineering roles. I have over 6 years of experience administering, automating, and securing enterprise distributions:

- **Distributions:** Ubuntu Server (LTS 20.04/22.04), Red Hat Enterprise Linux (RHEL 8/9), Amazon Linux (AL2/AL2023), and Rocky Linux.
- **Day-to-Day Operations:** Shell scripting, kernel memory and CPU profiling, process lifecycle management with Systemd, package repositories, firewall management (`iptables`, `firewalld`), and configuring storage partitions via LVM.
- **Container Host Administration:** Operating Docker daemon and containerd runtimes on high-throughput Linux worker nodes in AWS EKS.
</details>

<details>
<summary><strong>● On a Linux server, how would you check the machine's IP address?</strong></summary>

**Answer:**
In modern Linux distributions, the standard and recommended command is **`ip`** (part of `iproute2`), as legacy tools like `ifconfig` are deprecated:

1. **Detailed Network Interface Information:**
   ```bash
   ip addr show
   # or the shorthand:
   ip a
   ```
   This displays all network interfaces (`eth0`, `lo`, `docker0`), their assigned IPv4/IPv6 addresses, subnet masks, and interface states.

2. **Quickly Retrieve Only the Machine's IP Addresses:**
   ```bash
   hostname -I
   # Returns a space-separated list of all assigned IPv4 addresses
   ```

3. **Determine the Specific IP Used for Outbound Routing:**
   ```bash
   ip route get 1.1.1.1 | awk '{print $7}'
   ```
</details>

<details>
<summary><strong>● If you wanted to verify from an EC2 server whether it can reach google.com, how would you check that?</strong></summary>

**Answer:**
I verify reachability using a multi-layered diagnostic approach:

1. **HTTP/HTTPS Application Layer Test (Most Reliable):**
   ```bash
   curl -Iv --connect-timeout 5 https://www.google.com
   ```
   - Verifies DNS resolution, TCP three-way handshake on port 443, SSL/TLS handshake, and returns the HTTP status code (`200 OK` or `301/302 Redirect`).

2. **TCP Port Connectivity (Bypasses ICMP restrictions):**
   ```bash
   nc -zv www.google.com 443
   ```
   - Instantly confirms if TCP port 443 is reachable through the VPC Route Table, NAT Gateway, and Security Groups.

3. **ICMP Ping Test:**
   ```bash
   ping -c 4 www.google.com
   ```
   *(Note: In AWS, ping will fail if outbound ICMP is blocked in Security Groups or NACLs, even if web traffic on ports 80/443 is working perfectly. Hence, `curl` or `nc` is always preferred).*
</details>

<details>
<summary><strong>↳ Follow-up: If you only have the hostname of a website, how would you check connectivity to it from the Linux server?</strong></summary>

**Answer:**
When given only a hostname (e.g., `api.partner.internal`), I execute a 3-step diagnostic sequence:

1. **Verify DNS Resolution (Is the hostname resolving?):**
   ```bash
   dig +short api.partner.internal
   # or
   nslookup api.partner.internal
   ```
   - If this fails with `NXDOMAIN` or times out, the issue is internal DNS (`/etc/resolv.conf`, CoreDNS, or Route 53 private hosted zone).

2. **Test Socket Connectivity on Expected Ports (80 or 443):**
   ```bash
   nc -zv -w 3 api.partner.internal 443
   ```

3. **Trace the Network Routing Path:**
   ```bash
   traceroute -T -p 443 api.partner.internal
   # Uses TCP SYN packets on port 443 to identify where packets are dropped
   ```
</details>

<details>
<summary><strong>● Have you used the telnet command on Linux?</strong></summary>

**Answer:**
Yes, I have used `telnet` extensively as a classic troubleshooting utility to test raw TCP port connectivity and service banners against remote servers.

- *Usage:* `telnet <hostname_or_ip> <port>`
- *Modern Production Context:* In modern minimal Linux containers and hardened production servers, the `telnet` client is rarely installed by default due to security baselines. I typically use **`nc` (netcat)**, **`curl`**, or native Bash socket testing (`timeout 3 bash -c "</dev/tcp/host/port"`), though the concept of verifying open TCP sockets remains identical.
</details>

<details>
<summary><strong>↳ Follow-up: What is the full command syntax for checking open ports/processes (e.g., using netstat/telnet) on Linux?</strong></summary>

**Answer:**
The standard commands and their full syntax for auditing open ports and listening processes:

1. **Modern Standard (`ss` - Socket Statistics):**
   ```bash
   ss -tulpn
   ```
   - `-t`: Display TCP sockets.
   - `-u`: Display UDP sockets.
   - `-l`: Show only listening sockets.
   - `-p`: Show process name and Process ID (PID) owning the socket (requires `sudo`).
   - `-n`: Do not resolve service names (display numeric port numbers like 80 instead of "http").

2. **Filter for a Specific Port (e.g., Port 8080):**
   ```bash
   ss -tulpn | grep :8080
   # or using lsof:
   sudo lsof -i :8080
   ```

3. **Legacy Syntax (`netstat`):**
   ```bash
   sudo netstat -tulpn
   ```

4. **Testing Remote Port via Telnet:**
   ```bash
   telnet <target-host> <port>
   # Example: telnet 10.0.1.50 5432
   ```
</details>

<details>
<summary><strong>● If a Docker process on a Linux server is hung, how would you search for and locate that process?</strong></summary>

**Answer:**
I search for and locate a hung container process through both the Docker CLI and Linux OS process tables:

1. **Inspect Container Health via Docker:**
   ```bash
   docker ps -a
   ```
   Look for containers marked as `unhealthy`, stuck in `Restarting`, or unresponsive to CLI commands.

2. **Search Linux Host Process Table:**
   ```bash
   ps aux | grep -E "docker|containerd-shim"
   ```
   Inspect the process status column (`STAT`). A hung process often displays:
   - `D`: Uninterruptible sleep (waiting on disk I/O or dead NFS mount).
   - `Z`: Zombie process (terminated process whose parent hasn't reaped it).

3. **Inspect Docker Daemon Health:**
   ```bash
   sudo systemctl status docker
   sudo journalctl -u docker -n 50 --no-pager
   ```
</details>

<details>
<summary><strong>↳ Follow-up: How would you locate the specific Process ID (PID) of that hung Docker process?</strong></summary>

**Answer:**
To locate the exact host PID of a containerized process:

1. **Query via Docker Inspect (Most Direct Method):**
   ```bash
   docker inspect -f '{{.State.Pid}}' <container_name_or_id>
   ```
   This returns the root process PID (`PID 1` inside the container) as seen by the Linux host kernel.

2. **Query via `docker top`:**
   ```bash
   docker top <container_name_or_id>
   ```
   Outputs all host PIDs running inside that container's PID namespace.

3. **Search via `pgrep`:**
   ```bash
   pgrep -fa <process_binary_name>
   ```

4. **Remediation:**
   Once the PID is located:
   - Capture thread stack for diagnosis: `cat /proc/<PID>/stack`
   - Graceful termination: `kill -15 <PID>` (SIGTERM)
   - Forceful termination if completely unresponsive: `kill -9 <PID>` (SIGKILL)
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● Can you describe the complete end-to-end CI/CD pipeline flow used in your organization?</strong></summary>

**Answer:**
Our organization utilizes a secure **GitOps-driven CI/CD architecture** built across **GitHub**, **Jenkins**, **SonarQube**, **JFrog Artifactory/AWS ECR**, and **Argo CD** deploying to an **AWS EKS** cluster:

```
[ Developer Commit ] ---> [ GitHub PR ]
                              |
                     (Webhook Trigger)
                              v
        [ Jenkins Ephemeral Agent (Kubernetes Pod) ]
        |-- 1. Checkout & Validate Syntax
        |-- 2. Unit Testing & Code Coverage (mvn test)
        |-- 3. SAST Scan (SonarQube Quality Gate enforced)
        |-- 4. Dependency Vulnerability Audit (Snyk / Trivy)
        |-- 5. Multi-Stage Container Build (Tagged with Git SHA)
        |-- 6. Container Image Security Scan (Trivy CRITICAL CVE check)
        |-- 7. Push Image to AWS ECR / Artifactory
        +-- 8. Git Commit: Update Image Tag in Helm Git Repo
                              |
                              v
             [ Argo CD GitOps Controller in EKS ]
             |-- Syncs to 'Dev' & 'QA' Environments automatically
             |-- Runs automated integration & smoke test suites
             |-- Manual Approval Gate for 'Production'
             +-- Canary Release via Argo Rollouts (90% stable / 10% canary)
```
</details>

<details>
<summary><strong>● If your deployment pipeline starts failing right after a code merge, how would you debug the issue?</strong></summary>

**Answer:**
When a pipeline fails immediately post-merge, I isolate the failure through a structured triage process:

1. **Examine Pipeline Build Console Output:**
   - Immediately navigate to the failed Jenkins build console output to identify the exact stage that crashed (`Compile`, `Unit Test`, `SonarQube`, `Docker Build`, `Deploy`).

2. **Inspect the Git Merge Commit:**
   - Run `git log -n 1 --stat` and `git diff HEAD~1 HEAD` to inspect the changes introduced by the merge:
     - Did the developer introduce a syntax error or a failing unit test assertion?
     - Were dependency versions modified in `pom.xml`, `package.json`, or `requirements.txt` that conflict with existing packages?
     - Did a merge conflict resolution accidentally delete a required environment property or configuration key?

3. **Check Quality Gate & Security Thresholds:**
   - Did the new code introduce a critical vulnerability or drop test coverage below the required 80% threshold, causing SonarQube's Quality Gate to intentionally fail the build?

4. **Reproduce Locally in an Isolated Container:**
   - Run the exact build command (`mvn clean package`) inside a local container matching the Jenkins build agent image to eliminate environmental false positives.
</details>

<details>
<summary><strong>↳ Follow-up: Have you mainly used Jenkins as your CI/CD tool?</strong></summary>

**Answer:**
Yes, Jenkins has been a core CI/CD orchestrator in my enterprise projects, where I have managed Jenkins controllers, designed distributed agent architectures, and authored modular Declarative `Jenkinsfile` pipelines. However, I also have substantial hands-on experience with **GitHub Actions** and **GitLab CI**, frequently operating hybrid setups where GitHub Actions handles CI (testing and container scans) while Jenkins or Argo CD manages continuous delivery into secure enterprise VPCs.
</details>

<details>
<summary><strong>↳ Follow-up: Do you not use GitHub Actions in your organization for CI/CD?</strong></summary>

**Answer:**
In our organization, we operate a **hybrid CI/CD model**:

- **GitHub Actions:** Heavily utilized for lightweight, developer-facing CI tasks: running pull request linters, unit tests, code formatting checks, and security scans (Dependabot, CodeQL). It provides developers with immediate feedback directly within the GitHub PR UI.
- **Jenkins / Argo CD:** Retained for enterprise deployment orchestration and release management. Because our production infrastructure is isolated inside private AWS VPCs with strict corporate compliance, Jenkins agents and Argo CD running inside the private network have direct, secure access to deploy into private Kubernetes clusters without exposing internal APIs to external SaaS runners.
</details>

<details>
<summary><strong>↳ Follow-up: How many deployment environments do you have in your CI/CD pipeline?</strong></summary>

**Answer:**
We maintain **four distinct deployment environments** to ensure rigorous quality assurance before code reaches production:

1. **Development (`dev`):** Ephemeral or shared environment where developers continuously deploy feature branches. Argo CD automatically syncs on every merge to `develop`.
2. **Quality Assurance / Testing (`qa`):** Automated end-to-end, integration, performance, and regression testing run here against stable builds.
3. **Staging / Pre-Production (`stage`):** Exact production replica (infrastructure, configuration, security controls, and sanitized data). Used for user acceptance testing (UAT) and rehearsal of database migrations.
4. **Production (`prod`):** Live customer-facing environment. Deployments require signed approval gates and are released progressively via canary deployments.
</details>

<details>
<summary><strong>↳ Follow-up: Is your Jenkins pipeline written using the declarative syntax, or configured through the Jenkins UI?</strong></summary>

**Answer:**
Our pipelines are **100% written using the Declarative Pipeline syntax** codified in a version-controlled `Jenkinsfile`. 

We strictly enforce **Pipeline-as-Code** and prohibit creating or configuring pipelines manually through the Jenkins GUI. Configuring pipelines via the UI creates configuration drift, cannot be peer-reviewed, lacks version history, and violates enterprise audit compliance.
</details>

<details>
<summary><strong>↳ Follow-up: What advantages do you see in using the declarative pipeline approach in Jenkins?</strong></summary>

**Answer:**
Declarative Pipeline syntax offers significant structural and operational advantages over legacy UI jobs and Scripted syntax:

1. **Predictable & Robust Structure:** Standardized syntax block (`pipeline { agent { ... } stages { ... } }`) with built-in schema validation before execution starts.
2. **Clean Post-Execution Handlers (`post` block):** Built-in directives (`always`, `success`, `failure`, `cleanup`, `aborted`) that guarantee notifications and workspace cleanups execute reliably without complex try/finally code.
3. **Stage Restartability:** Allows restarting a failed build directly from the specific stage that failed (e.g., re-running only the `Deploy` stage without rebuilding or re-testing).
4. **Declarative Directives:** Native support for `parameters`, `environment`, `options { timeout(...) }`, and `when { branch 'main' }` conditions.
5. **GitOps Alignment:** Code is version-controlled, tested, and reviewed through standard Git pull requests.
</details>

<details>
<summary><strong>↳ Follow-up: Is this declarative Jenkins pipeline code version-controlled and managed through GitHub?</strong></summary>

**Answer:**
Yes, the `Jenkinsfile` resides in the **root directory of the application's GitHub source code repository**.

- In Jenkins, we configure **Multibranch Pipeline jobs** that scan the GitHub repository automatically.
- Whenever a branch or Pull Request is created, Jenkins discovers the `Jenkinsfile`, provisions an agent, and executes the pipeline defined for that specific branch.
- Any change to the build process must be submitted as a pull request, reviewed by the DevOps team, and merged just like standard application code.
</details>

<details>
<summary><strong>● If your Jenkins setup currently supports 2-3 developers deploying code smoothly, but 50 new developers suddenly join and also start deploying, how would you scale Jenkins to handle this increased load?</strong></summary>

**Answer:**
Scaling Jenkins from 3 to 50+ developers requires transitioning from a static VM setup to an **Ephemeral, Dynamic Cloud-Native Architecture**:

```
                              [ GitHub Webhooks (50+ Devs) ]
                                            |
                                            v
                 +------------------------------------------------------+
                 | Jenkins Controller (EKS Pod / Rightsized EC2)        |
                 | - Executors: 0 (No builds run on controller)         |
                 | - Webhook Event Queueing & Rate Limiting             |
                 | - JVM Heap Tuned (16GB+ with G1GC)                   |
                 +------------------------------------------------------+
                                            |
                              (Kubernetes Jenkins Plugin)
                                            |
        +-----------------------------------+-----------------------------------+
        |                                   |                                   |
        v                                   v                                   v
[ Dynamic Agent Pod 1 ]           [ Dynamic Agent Pod 2 ]           [ Dynamic Agent Pod N ]
(Maven/Docker Build)              (NodeJS/Trivy Scan)               (Python/Test Suite)
        |                                   |                                   |
        +-----------------------------------+-----------------------------------+
                                            |
                           [ Auto-Provisioned via Karpenter ]
                             (Spins up EC2 Spot instances)
```

1. **Zero Executors on Controller (Master):**
   - Set controller executors to **`0`**. The Jenkins Controller acts exclusively as an orchestrator and never executes build workloads directly.
   - Rightsize Controller memory (16GB+ RAM, tuned JVM garbage collection with `G1GC`) and store `$JENKINS_HOME` on high-performance AWS EFS or EBS (`gp3`).

2. **Ephemeral Dynamic Agents on Kubernetes (EKS):**
   - Install the **Jenkins Kubernetes Plugin**.
   - When a job triggers, Jenkins instantly spawns an ephemeral Pod in the EKS cluster tailored to that specific job (e.g., container with Maven, container with Docker/Trivy).
   - Once the build completes, the pod terminates immediately, freeing all resources.

3. **Autoscaling Compute Infrastructure via Karpenter:**
   - Back the EKS cluster with **Karpenter**. When 30 jobs fire concurrently, Karpenter provisions Spot EC2 instances within 45 seconds, bin-packing agent pods and terminating instances when idle.

4. **Shared Build & Dependency Caching:**
   - Configure persistent volume mounts on EFS or local worker node volumes to cache Maven (`~/.m2`) and npm packages, preventing 50 developers from repeatedly re-downloading dependencies over the internet.
</details>

#### 【 IAC 】

<details>
<summary><strong>● Have you used Pulumi as an IaC tool, or have you mainly used Terraform?</strong></summary>

**Answer:**
I have **mainly used Terraform (and OpenTofu)** as my primary Infrastructure-as-Code tool across enterprise environments, while maintaining a strong conceptual and hands-on understanding of **Pulumi**:

- **Terraform / OpenTofu (My Primary Focus):** Declarative Domain-Specific Language (HCL). Offers vast community adoption, enterprise module registries, mature provider ecosystems, and widespread organizational standardization.
- **Pulumi Comparison:** Allows defining cloud infrastructure using general-purpose programming languages (TypeScript, Python, Go, C#). Ideal for software engineering teams that want to write infrastructure unit tests using native language test runners (`pytest`, `jest`) and share types between frontend, backend, and infrastructure code.
</details>

<details>
<summary><strong>● If AWS infrastructure was already set up manually and your manager asked you to bring it entirely under Terraform management, how would you approach managing it via Terraform from scratch?</strong></summary>

**Answer:**
I execute a disciplined 5-step reverse-engineering and adoption strategy:

1. **Resource Discovery & Inventory Audit:**
   - Catalog all existing manual resources (VPCs, Subnets, Route Tables, Security Groups, EC2, RDS, S3) using AWS Resource Explorer and discovery tools like **Former2** or AWS CloudFormation IaC generator.

2. **Codify Target HCL Architecture:**
   - Write clean, modular Terraform configuration files matching the existing architecture (defining `variables.tf`, `main.tf`, and `outputs.tf`).
   - In modern **Terraform 1.5+**, write declarative `import` blocks:
     ```hcl
     import {
       to = aws_vpc.main
       id = "vpc-0123456789abcdef0"
     }
     ```

3. **Import Resources into Terraform State:**
   - Execute the import operation:
     ```bash
     terraform import aws_vpc.main vpc-0123456789abcdef0
     terraform import aws_security_group.web_sg sg-0987654321fedcba0
     ```
   - Alternatively, use `terraform plan -generate-config-out=generated.tf` to let Terraform automatically generate the matching HCL code.

4. **Reconcile and Eliminate State Drift:**
   - Run `terraform plan`.
   - Compare the plan output against the live resources. Carefully adjust HCL code attributes until `terraform plan` reports:
     **`Plan: 0 to add, 0 to change, 0 to destroy`**. This confirms 100% parity between code and reality.

5. **Lock Down AWS Console Access:**
   - Enforce IAM policies and SCPs preventing further manual console edits. Commit all code to Git and mandate all future changes flow through CI/CD.
</details>

<details>
<summary><strong>↳ Follow-up: What is the Terraform command used to import an existing resource into Terraform state?</strong></summary>

**Answer:**
The CLI command syntax is:
```bash
terraform import <RESOURCE_TYPE>.<RESOURCE_NAME> <CLOUD_RESOURCE_IDENTIFIER>
```

**Concrete Production Example:**
```bash
terraform import aws_s3_bucket.company_data prod-company-data-bucket-2026
terraform import aws_security_group.web_sg sg-0123456789abcdef0
```
In **Terraform 1.5+**, the preferred approach is using declarative **`import` blocks** inside `.tf` files:
```hcl
import {
  to = aws_s3_bucket.company_data
  id = "prod-company-data-bucket-2026"
}
```
</details>

<details>
<summary><strong>↳ Follow-up: After running Terraform import, how would you verify whether the resource was successfully imported into the Terraform state file?</strong></summary>

**Answer:**
I verify successful state import using three definitive verification steps:

1. **Verify State List:**
   ```bash
   terraform state list
   ```
   - Confirms that `<RESOURCE_TYPE>.<RESOURCE_NAME>` (e.g., `aws_vpc.main`) is present in the state index.

2. **Inspect Resource Attributes in State:**
   ```bash
   terraform state show aws_vpc.main
   ```
   - Displays all captured cloud metadata (CIDR block, VPC ID, tags, tenancy) currently recorded in the state file.

3. **Run a Speculative Plan (Zero-Diff Confirmation):**
   ```bash
   terraform plan
   ```
   - If the import was successful and code matches, Terraform will report:
     **`No changes. Your infrastructure matches the configuration.`**
</details>

<details>
<summary><strong>● If you're building AWS infrastructure from scratch using Terraform and the 'terraform apply' fails partway through, how would you debug and resolve the issue?</strong></summary>

**Answer:**
When `terraform apply` fails partway through, Terraform does **not** perform an automatic rollback; instead, it enters a **partial state** where resources created before the error remain preserved in the state file.

**Step-by-Step Resolution:**
1. **Analyze the Console Error Message:**
   - Examine the cloud provider error code (e.g., `InvalidParameterValue`, `UnauthorizedOperation` due to IAM permission failure, or `CIDRBlockConflict`).

2. **Inspect the State File (`terraform state list`):**
   - Confirm which resources were successfully provisioned and committed to state, and identify which resource failed.

3. **Enable Verbose Debug Logging:**
   ```bash
   export TF_LOG=DEBUG
   export TF_LOG_PATH=terraform_debug.log
   terraform apply
   ```
   - Inspect the exact HTTP request and response payload sent to the AWS API endpoint.

4. **Remediate the Code:**
   - Correct the attribute or provision missing dependencies in the `.tf` configuration.

5. **Re-run Terraform Apply:**
   - Run `terraform plan` followed by `terraform apply`. Terraform intelligently references the state file, recognizes the already-created resources, skips them, and provisions only the remaining uncreated or modified resources.
</details>

<details>
<summary><strong>● Can you share your screen so we can review some of your Terraform code?</strong></summary>

**Answer:**
*(Simulating technical screen-share review)*:

"Certainly! I'll share my screen and walk you through our production repository structure and an enterprise VPC module:

**1. Directory Architecture:**
```
terraform-aws-infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   └── prod/
│       ├── backend.tf       # Remote S3 backend + DynamoDB locking
│       ├── main.tf          # Calls reusable modules
│       ├── outputs.tf
│       └── versions.tf      # Pinning terraform >= 1.5 and aws provider ~> 5.0
└── modules/
    ├── vpc/
    ├── eks/
    └── rds/
```

**2. Sample Modular Code (`modules/vpc/main.tf`):**
```hcl
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.common_tags, {
    Name = "${var.environment}-vpc"
  })
}

resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(var.common_tags, {
    Name                              = "${var.environment}-private-subnet-${count.index + 1}"
    "kubernetes.io/role/internal-elb" = "1"
  })
}
```
I enforce strict input variable validation, module outputs, and pre-commit hooks running `terraform fmt -check`, `tflint`, and `checkov` security scanning."
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● In your AWS environment, did you create IAM users manually, or was SSO configured for user access?</strong></summary>

**Answer:**
In our enterprise production environment, we **strictly prohibited manual creation of IAM users** and static access keys. 

We implemented **AWS IAM Identity Center (formerly AWS SSO)** federated with our corporate identity provider (**Okta / Microsoft Entra ID**):

- **Zero Static Credentials:** Engineers log in through the Okta SSO portal using Multi-Factor Authentication (MFA).
- **Short-Lived STS Credentials:** AWS SSO automatically generates temporary, 1-hour session credentials via AWS STS.
- **Permission Sets:** Roles and access levels are standardized as Permission Sets (e.g., `PlatformAdminAccess`, `DeveloperReadOnlyAccess`) assigned to Okta groups mapped to specific AWS accounts across our AWS Organization.
</details>

<details>
<summary><strong>↳ Follow-up: Which team was responsible for granting IAM access/administrator privileges in your AWS account?</strong></summary>

**Answer:**
Granting IAM privileges was governed by the **Cloud Platform & SecOps (Security Operations) Governance Team** through a strictly audited **GitOps and ServiceNow Request Workflow**:

1. **Access Request & Justification:**
   - The engineer submits an access request in **ServiceNow** specifying business justification, duration, and target AWS account.
2. **Dual-Tier Approval:**
   - Requires explicit sign-off from the engineer's Engineering Manager and the SecOps Lead.
3. **Automated Provisioning via GitOps:**
   - Upon approval, the change is committed to the version-controlled IAM repository (modifying Terraform configurations or Okta group memberships).
   - Temporary elevated access (e.g., break-glass production access) is granted via automated temporary role assignments that expire automatically after 4 to 8 hours.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Before your current stint at Sonata, which other organizations did you work for?

↳ **Candidate Introduction:** *What were your job roles/titles at those previous organizations?*
</details>
</details>
