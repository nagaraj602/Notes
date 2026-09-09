<details open>
<summary><h2>🏢 a5econsulting</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 CI/CD 】

<details>
<summary><strong>● Suppose a Jenkins pipeline breaks in the middle of execution. How would you approach rolling back the actions already taken by the pipeline and debugging the logs to identify the cause of failure?</strong></summary>

**Answer:**
When a Jenkins pipeline fails midway through execution, a senior DevOps engineer handles both **incident containment (rollback)** and **root cause analysis (debugging)** systematically:

1. **Automated & Manual Rollback Strategy:**
   - **Declarative `post` Block:** Robust pipelines implement compensation logic inside `post { failure { ... } cleanup { ... } }` or scripted `try-catch-finally` blocks.
     ```groovy
     post {
         failure {
             script {
                 echo "Pipeline failed. Initiating automated rollback..."
                 // Revert Kubernetes deployment to previous revision
                 sh 'kubectl rollout undo deployment/payment-service -n production'
                 // Clean up intermediate cloud resources or temporary artifact staging
                 sh 'terraform apply -destroy -target=aws_instance.temp_worker -auto-approve || true'
                 slackSend channel: '#devops-alerts', color: 'danger', message: "Build ${env.BUILD_NUMBER} failed! Rollback triggered."
             }
         }
         cleanup {
             cleanWs() // Reclaim agent disk space
         }
     }
     ```
   - **Container/Deployment Rollback:** If the failure occurred after partial deployment to Kubernetes, trigger `kubectl rollout undo deployment/<name>` or let an automated canary controller (like Argo Rollouts / Flagger) abort traffic promotion.
   - **Artifact Versioning:** Artifacts pushed to registries (ECR, Nexus) are tagged with immutable Git SHAs (`${GIT_COMMIT}`). Never overwrite mutable tags like `latest`; this ensures the previously running stable image remains untouched and ready for immediate redeployment.
   - **Database Schema Changes:** For database migrations that fail halfway, ensure migrations are written with idempotent backward-compatible up/down scripts (e.g., Flyway/Liquibase).

2. **Log Debugging and Root Cause Isolation:**
   - **Console Output Navigation:** Open Jenkins Blue Ocean or Classic UI, check the failed stage timestamp, and inspect logs around stack traces or non-zero exit codes (`script returned exit code 1`).
   - **Agent-Side Diagnostics:** Check if the failure was infrastructure-related:
     - Check disk space on Jenkins agent: `df -h`
     - Check container runtime memory/OOMKilled: `dmesg -T | grep -i oom` or `docker inspect <container_id>`
   - **External Service Telemetry:** Verify status and rate limits of external endpoints contacted during the build (SonarQube API, Artifactory, AWS IAM credential expiry, HashiCorp Vault token expiration).
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● Can you list and explain all the different Docker commands you know, such as docker pull, docker build, docker prune, and similar commands?</strong></summary>

**Answer:**
In enterprise environments, Docker commands are categorized across the container lifecycle:

1. **Image Management:**
   - `docker build -t app:v1.0 -f Dockerfile .`: Builds an image from a Dockerfile. Use `--no-cache` to force rebuilds and `--target <stage>` for multi-stage targets.
   - `docker pull <image>:<tag>`: Fetches an image from a remote registry (Docker Hub, AWS ECR, Harbor).
   - `docker push <image>:<tag>`: Uploads a tagged image to a remote registry.
   - `docker images` / `docker image ls`: Lists local images with IDs, tags, and virtual sizes.
   - `docker rmi <image_id>`: Removes one or more local images.
   - `docker tag <source> <target>`: Creates an alias tag pointing to a source image (e.g., tagging with commit SHA and registry URL).

2. **Container Lifecycle & Execution:**
   - `docker run -d --name web -p 8080:80 -v app_data:/data --restart=always nginx:alpine`: Creates and starts a container in detached mode with port forwarding, volume mounting, and restart policies.
   - `docker ps` / `docker ps -a`: Lists running containers or all containers including exited ones.
   - `docker stop <id>` & `docker start <id>`: Sends `SIGTERM` (followed by `SIGKILL` after grace period) to stop a container, or starts a stopped one.
   - `docker restart <id>`: Stops and restarts a container.
   - `docker rm -f <id>`: Forcefully removes a running or stopped container.
   - `docker exec -it <id> /bin/sh`: Runs an interactive shell session inside an active container for live debugging.

3. **Inspection, Logs & Diagnostics:**
   - `docker logs -f --tail 100 <id>`: Streams container standard output and error (`stdout`/`stderr`).
   - `docker inspect <id/image>`: Returns detailed JSON metadata (networking, IP addresses, mounted volumes, environment variables, health checks).
   - `docker stats`: Displays a real-time stream of CPU, memory, network I/O, and block I/O resource usage.
   - `docker top <id>`: Displays running processes inside the container.

4. **Housekeeping & Garbage Collection:**
   - `docker system prune -a --volumes`: Cleans up all stopped containers, dangling images, unused networks, and optionally unused volumes.
   - `docker image prune`: Removes dangling (untagged `<none>`) layers to reclaim disk space on CI worker nodes.
</details>

<details>
<summary><strong>↳ Follow-up: What are the different types of Docker volumes available?</strong></summary>

**Answer:**
Docker provides three primary mechanisms for persisting container data:

1. **Named Volumes (`docker volume create`):**
   - Managed completely by Docker and stored in a dedicated part of the host filesystem (`/var/lib/docker/volumes/` on Linux).
   - Best practice for database storage and production state persistence because non-root users cannot modify this directory directly.
   - Can be shared among multiple containers simultaneously and supports volume drivers (e.g., AWS EBS, NFS, Azure File storage drivers).
   - Example: `docker run -v my_named_vol:/var/lib/postgresql/data postgres:15`

2. **Bind Mounts:**
   - Maps an arbitrary host path directly into the container filesystem (e.g., `-v /home/user/app:/app` or `--mount type=bind,source=/path,target=/app`).
   - Relies on the host machine's directory structure and permissions (UID/GID matching).
   - Excellent for local development (hot-reloading code) and sharing host configuration files like `/etc/localtime` or `/var/run/docker.sock` into CI agent containers.

3. **`tmpfs` Mounts (Linux only) / Named Pipes (Windows):**
   - Persists data purely in host system memory (RAM), never written to the host or container writable layer.
   - Best for high-throughput temporary files, sensitive secrets/tokens, or ephemeral session caches that must not touch persistent disk.
   - Example: `docker run --tmpfs /app/cache:rw,noexec,nosuid,size=128m my-app`
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Can you explain how Kubernetes works and describe the different key concepts and components in its architecture?</strong></summary>

**Answer:**
Kubernetes is a declarative container orchestration platform designed to automate deployment, scaling, healing, and traffic management across distributed clusters.

1. **Control Plane Components (Master Node):**
   - **`kube-apiserver`:** The central REST API gateway and front-end for Kubernetes. All administrative commands (`kubectl`), worker nodes, and controllers communicate exclusively through the API server. Validates and configures data for API objects.
   - **`etcd`:** Highly available, distributed key-value data store that holds the complete cluster state, configuration, and secret metadata. Uses the Raft consensus algorithm.
   - **`kube-scheduler`:** Filters and scores available worker nodes based on resource requests/limits, taints/tolerations, node affinity, and topology constraints to assign unassigned pods to optimal nodes.
   - **`kube-controller-manager`:** Runs daemon controllers that continuously regulate actual state toward desired state (e.g., Node Lifecycle Controller, ReplicaSet Controller, EndpointSlice Controller, ServiceAccount Controller).
   - **`cloud-controller-manager`:** Integrates with underlying cloud provider APIs to manage Cloud Load Balancers, EBS/EFS storage volumes, and Node routing tables.

2. **Worker Node Components:**
   - **`kubelet`:** An agent that runs on each node in the cluster. It watches PodSpecs assigned to its node by the API server and ensures container runtimes pull images, start containers, and stay healthy.
   - **`kube-proxy`:** Network proxy managing IP tables or IPVS rules on each worker node to route cluster-internal service traffic to backend pod endpoints.
   - **Container Runtime (CRI):** Low-level container runtime engine conforming to CRI (e.g., `containerd`, `CRI-O`).

3. **Core Kubernetes Concepts:**
   - **Pod:** Smallest deployable unit containing one or more tightly coupled containers sharing network namespace (`localhost`), storage, and IPC.
   - **Service:** Abstraction that defines a logical set of Pods and a policy to access them (ClusterIP, NodePort, LoadBalancer, Headless).
   - **Deployment / ReplicaSet:** High-level controller managing declarative updates, scaling, and rolling replacements of Pod replicas.
   - **ConfigMaps & Secrets:** Decouple environment-specific configuration and sensitive credentials from container image binaries.
   - **Ingress:** Manages external HTTP/S routing rules, host headers, and TLS termination into internal ClusterIP services.
</details>

<details>
<summary><strong>↳ Follow-up: How does the Kubernetes scheduler interact with pods to schedule them onto nodes?</strong></summary>

**Answer:**
The `kube-scheduler` operates via an asynchronous, two-phase evaluation loop: **Filtering (Predicates)** and **Scoring (Priorities)**.

```
+---------------+     Watch Unassigned Pods      +------------------+
| kube-apiserver| <---------------------------- |  kube-scheduler  |
+---------------+                                +--------+---------+
        ^                                                 |
        | 1. Filter Nodes (Predicates)                    v
        |    - NodeResourcesFit (CPU/Mem requests)   [ Candidate ]
        |    - NodeName / NodeSelector Match         [   Nodes   ]
        |    - PodToleratesNodeTaints                     |
        |    - VolumeZoneRestrictions                    |
        |                                                 v
        | 2. Score Nodes (Priorities)                [ Ranked    ]
        |    - NodeResourcesBalancedAllocation       [   Nodes   ]
        |    - ImageLocalityPriority                      |
        |    - NodeAffinityScoring                        v
        |                                            Highest Score
        +---------------- Post Binding Object <-----------+
```

1. **Scheduling Queue:**
   - When a Pod is created without a `spec.nodeName`, `kube-scheduler` detects it via an API Server watch on the active priority queue (`activeQ`).

2. **Filtering Phase (Predicates):**
   - Tests all nodes against hard constraints:
     - `NodeResourcesFit`: Does the node have enough allocatable CPU and RAM to satisfy the pod's `requests`?
     - `PodToleratesNodeTaints`: Does the pod have tolerations matching all taints on the node?
     - `NodeAffinity`: Does the node match `requiredDuringSchedulingIgnoredDuringExecution`?
     - `MatchNodeSelector`: Does the node possess the required key-value labels?
   - Any node failing a filter is removed from consideration. If zero nodes pass, the pod transitions to `Pending` with a `FailedScheduling` event.

3. **Scoring Phase (Priorities):**
   - The remaining candidate nodes are evaluated using weighted scoring plugins (0 to 100):
     - `ImageLocalityPriority`: Favors nodes that already cached the container image locally.
     - `NodeResourcesBalancedAllocation`: Favors nodes where pod allocation creates a balanced CPU/memory ratio.
     - `NodeAffinityPriority`: Scores nodes matching `preferredDuringSchedulingIgnoredDuringExecution`.

4. **Binding Phase:**
   - The scheduler selects the node with the highest aggregate score.
   - It sends a `Binding` API request to `kube-apiserver` writing `spec.nodeName = <selected_node>`.
   - The target node's `kubelet` detects the binding and proceeds to download images and launch containers.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you give a brief introduction about yourself and your professional background?

</details>
</details>

<details open>
<summary><h2>🏢 Mrisoftware</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 11-08-2026 09:40 PM*

#### 【 CI/CD 】

<details>
<summary><strong>● Do you have experience using GitHub Actions and GitLab Runner for CI/CD, given that you've worked with GitHub and GitLab?</strong></summary>

**Answer:**
Yes. I have architected and maintained production-grade continuous integration and continuous deployment workflows across both platforms:

- **GitHub Actions:**
  - Designed modular multi-job workflows (`.github/workflows/*.yml`) utilizing matrix strategies for cross-platform unit testing.
  - Built **Reusable Workflows** (`workflow_call`) and **Custom Composite Actions** to share standard steps (security linting, vulnerability scanning, image building) across hundreds of repositories.
  - Implemented GitHub Environments with protection rules, requiring manual approvals for production deployments, and leveraged OIDC (OpenID Connect) for secure short-lived authentication to AWS without hardcoded IAM credentials.
- **GitLab CI/CD & GitLab Runners:**
  - Designed complex enterprise pipelines using `.gitlab-ci.yml` leveraging `include:`, `extends:`, and anchored YAML configurations.
  - Deployed and operated auto-scaling **GitLab Runners** on Kubernetes using the GitLab Runner Helm Chart, where each CI job executes inside an isolated, ephemeral pod.
  - Managed pipeline caching (`cache:` with branch keys) and build artifacts (`artifacts: expire_in`) to accelerate Maven/NPM build cycles.
</details>

<details>
<summary><strong>● How would you standardize your CI/CD pipeline so that it can be reused consistently across multiple products, projects, and teams?</strong></summary>

**Answer:**
To prevent duplication, drift, and security vulnerabilities across dozens of development teams, I standardize CI/CD pipelines using a **Centralized Shared Library / Template Pattern**:

1. **Centralized Template Repository:**
   - Maintain a dedicated, access-controlled repository (e.g., `devops-shared-templates`) containing parameterized pipeline definitions:
     - In **Jenkins**: Jenkins Shared Libraries (`vars/standardPipeline.groovy`).
     - In **GitHub Actions**: Reusable Workflows (`workflow_call`) and composite actions.
     - In **GitLab CI**: Centralized templates included via `include: { project: 'devops/ci-templates', file: '/templates/java-maven.yml' }`.

2. **Standardized Pipeline Contract:**
   - Define a convention-over-configuration interface where application repositories only provide a simple manifest or parameter file:
     ```yaml
     # Application .github/workflows/deploy.yml
     name: App CI/CD
     uses: enterprise-org/reusable-workflows/.github/workflows/standard-java-pipeline.yml@v2.4.0
     with:
       java-version: '17'
       sonar-project-key: 'billing-service'
       ecr-repo: 'payments/billing'
       deployment-target: 'eks-cluster-prod'
     secrets: inherit
     ```

3. **Semantic Versioning of Templates:**
   - Tag template releases (`@v1`, `@v2.1.0`). Teams pin to major/minor versions. Breaking changes are released under new major versions, allowing engineering teams to upgrade cleanly without breaking builds unexpectedly.

4. **Enforced Security Baseline:**
   - Central templates embed mandatory enterprise guardrails (SAST, Trivy container scanning, secret detection with Gitleaks) that cannot be bypassed or removed by individual developers.
</details>

<details>
<summary><strong>↳ Follow-up: Can you walk me through the stages of your typical CI/CD pipeline?</strong></summary>

**Answer:**
A production-grade microservice pipeline follows six distinct stages:

```
[ Code Checkout ] ──> [ Build & Unit Test ] ──> [ Static Analysis & SAST ]
                                                         │
[ Deployment & Smoke Tests ] <── [ Container Build & Scan ] <──┘
```

1. **Checkout & Secret Scanning:**
   - Ephemeral runner clones the repository. Runs `gitleaks` or `trufflehog` to ensure no API keys or certificates were committed.
2. **Compile & Unit Testing:**
   - Compiles application code (e.g., `mvn clean test` or `npm run test:coverage`) and publishes code coverage reports.
3. **Code Quality & Static Analysis:**
   - Runs **SonarQube** scanner. Checks code smells, bugs, cognitive complexity, and branch coverage. The pipeline enforces a strict **Quality Gate**.
   - Runs **OWASP Dependency-Check** / Snyk to detect known CVEs in third-party libraries.
4. **Container Build & Hardening:**
   - Multi-stage Docker build produces a lean image based on Alpine or Distroless.
   - Tags the image with Git SHA (`${GITHUB_SHA}`) and environment build ID.
   - Runs **Trivy** vulnerability scanner; fails the build if any `CRITICAL` vulnerability without a patch exists.
   - Pushes image to Amazon ECR or Harbor.
5. **GitOps Manifest Update / Artifact Promotion:**
   - For GitOps, updates the target image tag in the Git repository holding Helm charts or Kustomize overlays (`staging/values.yaml`).
6. **Continuous Delivery & Verification:**
   - Argo CD detects the commit and synchronizes the deployment to the Kubernetes cluster.
   - Executes automated post-deployment health checks and synthetic smoke tests (`curl -f https://app-staging.internal/healthz`).
</details>

<details>
<summary><strong>↳ Follow-up: If you were tasked with recreating this same Jenkins CI/CD pipeline using GitHub Actions instead, what would your approach be, and how would you migrate your existing tech stack over?</strong></summary>

**Answer:**
Migrating a Jenkins pipeline to GitHub Actions involves mapping concepts, establishing authentication, and converting scripts systematically:

1. **Architectural Concept Mapping:**
   | Jenkins Concept | GitHub Actions Equivalent |
   |---|---|
   | Jenkins Master / Controller | GitHub Managed Service |
   | Jenkins Agent (Static VM / K8s Pod) | Self-hosted or GitHub-hosted Runner |
   | `Jenkinsfile` (Declarative) | `.github/workflows/*.yml` |
   | Jenkins Credentials Store | GitHub Secrets / GitHub Environments |
   | Shared Libraries | Reusable Workflows (`workflow_call`) & Composite Actions |
   | Post-build actions | `if: always()`, `if: failure()`, `steps.*.outcome` |

2. **Step-by-Step Migration Plan:**
   - **Infrastructure & Runners:** If builds require access to internal VPC resources (private EKS, private databases, internal Artifactory), deploy **GitHub Actions Self-Hosted Runners** inside the AWS VPC using the Actions Runner Controller (ARC) on Kubernetes.
   - **Authentication Modernization:** Replace static AWS access keys stored in Jenkins with **OpenID Connect (OIDC)** federated authentication:
     ```yaml
     - name: Configure AWS Credentials via OIDC
       uses: aws-actions/configure-aws-credentials@v4
       with:
         role-to-assume: arn:aws:iam::123456789012:role/github-actions-ecr-role
         aws-region: us-east-1
     ```
   - **Tooling Parity:** Replicate Maven, Java, SonarQube, and Docker setup using marketplace actions (`actions/setup-java@v4`, `docker/build-push-action@v5`, `sonarsource/sonarqube-scan-action@v4`).
   - **Parallel Validation:** Run both Jenkins and GitHub Actions workflows in parallel across 2-3 sprints to benchmark execution speed, verify artifact equivalence, and ensure zero pipeline downtime before decommissioning the Jenkins job.
</details>

<details>
<summary><strong>↳ Follow-up: Why do you assume that using a different CI/CD tool like GitHub Actions would fundamentally change your approach compared to Jenkins?</strong></summary>

**Answer:**
While the *core engineering principles* (linting, compiling, testing, scanning, building, deploying) remain identical across tools, migrating from Jenkins to GitHub Actions fundamentally changes the **operational paradigm, infrastructure overhead, and security model**:

1. **Control Plane Management Overhead:**
   - In **Jenkins**, the team owns the controller: patching OS vulnerabilities, updating Jenkins core, managing fragile plugin compatibility matrices, and tuning JVM heap memory.
   - In **GitHub Actions**, the control plane is a fully managed SaaS; the team focuses solely on workflow logic rather than infrastructure maintenance.
2. **Ephemeral vs. Persistent Workspace Execution:**
   - Jenkins static agents frequently suffer from "dirty workspace" issues where residual files, uncleaned Docker caches, or modified local configs leak between builds.
   - GitHub Actions treats every job as completely ephemeral (clean VM or fresh container), ensuring absolute build reproducibility.
3. **Modern Credential Architecture (Zero Long-Lived Keys):**
   - Jenkins traditionally relied on long-lived AWS IAM Secret Keys or SSH keys stored in the master credentials store.
   - GitHub Actions natively integrates with AWS/Azure/GCP via **OIDC Token Exchange**, completely eliminating long-lived credentials in favor of short-lived (15-minute) STS assume-role tokens.
4. **Native Developer Experience & Branch Matrixing:**
   - GitHub Actions is deeply integrated with GitHub Pull Requests, branch protection rules, code owners, and status checks, whereas Jenkins requires complex webhook plugins and status notification steps.
</details>

<details>
<summary><strong>● For a Java-based application's CI/CD pipeline, what security and code quality checks would you typically include?</strong></summary>

**Answer:**
A robust Java (Maven/Gradle) enterprise pipeline incorporates a multi-tiered **DevSecOps** defense-in-depth model:

1. **Pre-Commit / Pre-Build Secret Detection:**
   - **Tool:** `gitleaks` or `trufflehog`
   - Scans commits for hardcoded passwords, AWS keys, JWT signing keys, and private certificates before compilation starts.
2. **Static Application Security Testing (SAST) & Code Quality:**
   - **Tool:** **SonarQube** / **Checkstyle** / **SpotBugs** with FindSecBugs plugin.
   - Enforces clean code standards (cyclomatic complexity, code duplication, resource leak detection) and identifies common security flaws (SQL injection vectors, weak cryptographic ciphers, insecure deserialization).
   - Enforces a blocking **Quality Gate** (e.g., zero new Critical/Blocker vulnerabilities, 80%+ unit test coverage).
3. **Software Composition Analysis (SCA) / Dependency Scanning:**
   - **Tool:** **OWASP Dependency-Check**, **Snyk**, or **GitHub Dependabot**.
   - Analyzes `pom.xml` / `build.gradle` dependency trees against the National Vulnerability Database (NVD) to catch CVEs in open-source transitive libraries (e.g., Log4j-style vulnerabilities).
4. **License Compliance Scanning:**
   - Checks library licenses to prevent GPL-infected code from compromising proprietary enterprise software.
5. **Container Image Vulnerability Scanning:**
   - **Tool:** **Trivy** or **Anchore Engine**.
   - Scans the generated container image OS layers and Java runtime artifacts for unpatched vulnerabilities prior to registry push.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Can you explain the difference between a liveness probe and a readiness probe in Kubernetes?</strong></summary>

**Answer:**
Both probes are health check mechanisms managed by the node's `kubelet`, but they serve fundamentally different operational objectives:

| Feature | Liveness Probe | Readiness Probe |
|---|---|---|
| **Primary Purpose** | Determines if the container is **alive** and healthy or deadlocked/frozen. | Determines if the container is **ready to receive network traffic**. |
| **Failure Action** | Kubelet **kills the container and restarts it** according to the Pod's `restartPolicy`. | Kubelet **removes the Pod IP from the Service EndpointSlice**. No restart occurs. |
| **Typical Use Case** | Catching unrecoverable deadlocks, infinite loops, or fatal memory leaks. | Application initialization, loading large caches, warming connection pools. |
| **Impact on Traffic** | Pod restarts; downtime if all replicas fail simultaneously. | Prevents sending HTTP 502/503 errors to clients while warm-up occurs. |

```yaml
spec:
  containers:
  - name: payment-api
    image: payment-api:v2.1
    livenessProbe:
      httpGet:
        path: /healthz/liveness
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /healthz/readiness
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 5
      failureThreshold: 2
```
</details>

<details>
<summary><strong>↳ Follow-up: If a service's pod keeps restarting and goes into CrashLoopBackOff because it needs time for its dependencies to load before it can serve traffic, how would you troubleshoot and fix that issue?</strong></summary>

**Answer:**
1. **Troubleshooting Steps:**
   - Check pod exit code and restart history: `kubectl describe pod <pod-name>`
   - Inspect container termination reason (e.g., `OOMKilled`, or `Exit Code 137` / `143` indicating SIGKILL from liveness probe failure).
   - Check previous container logs: `kubectl logs <pod-name> --previous`
   - Check events: Look for `Liveness probe failed: HTTP probe failed with statuscode: 503`.

2. **Root Cause Analysis:**
   - If the pod restarts repeatedly before it finishes initializing, the **liveness probe is firing too early and failing**, causing the kubelet to terminate the pod before it ever completes dependency loading.

3. **Solutions:**
   - **Increase `initialDelaySeconds`:** Give the application sufficient buffer to boot.
   - **Implement a Startup Probe (`startupProbe`):** (Recommended solution in modern Kubernetes).
     A `startupProbe` disables liveness and readiness checks until it succeeds:
     ```yaml
     startupProbe:
       httpGet:
         path: /healthz
         port: 8080
       failureThreshold: 30
       periodSeconds: 10   # Allows up to 30 * 10 = 300 seconds for slow startup
     livenessProbe:
       httpGet:
         path: /healthz
         port: 8080
       periodSeconds: 10
     ```
   - **Init Containers:** If the application depends on an external dependency (e.g., waiting for database schema migration or message broker availability), move that dependency check into an `initContainer`.
</details>

<details>
<summary><strong>↳ Follow-up: Given that the root cause is confirmed to be a slow-loading dependency (not an application crash) causing the liveness probe to fail, how specifically would you handle that dependency startup delay in Kubernetes?</strong></summary>

**Answer:**
To cleanly handle a slow-loading dependency without masking genuine runtime deadlocks:

1. **Decouple Dependency Readiness from Liveness:**
   - **Golden Rule:** Liveness probes must **never** check external dependencies (database, Redis, third-party APIs). If the database slows down, checking it in a liveness probe causes every pod across the cluster to restart in a cascading failure storm.
   - The `/healthz/liveness` endpoint must only check **internal process health** (e.g., is the event loop responsive, is JVM thread pool unblocked?). It should return `HTTP 200` as long as the process is alive.
   - External dependencies belong exclusively in the `/healthz/readiness` check. If the database is slow, the readiness probe fails, safely detaching the pod from the Service endpoint without triggering a restart.

2. **Implement Kubernetes `startupProbe`:**
   - As introduced in Kubernetes 1.18+, the `startupProbe` protects slow-starting containers:
     ```yaml
     startupProbe:
       httpGet:
         path: /healthz/startup
         port: 8080
       periodSeconds: 5
       failureThreshold: 24  # Gives 24 * 5 = 120 seconds to load dependencies
     ```
   - All liveness and readiness checks remain suspended until the `startupProbe` completes successfully once.

3. **Use Init Containers with Polling Loops:**
   - If the container should not even boot until a remote service is reachable, use an `initContainer`:
     ```yaml
     initContainers:
     - name: wait-for-db
       image: busybox:1.36
       command: ['sh', '-c', 'until nc -z -v -w3 postgres.db.internal 5432; do echo "Waiting for database..."; sleep 2; done;']
     ```
</details>

#### 【 IAC 】

● **Candidate Introduction:** How much experience do you have with Terraform?

<details>
<summary><strong>↳ Follow-up: How would you structure your Terraform code to support multiple environments?</strong></summary>

**Answer:**
There are two primary approaches to multi-environment Terraform architectures:

1. **Directory-Based Separation (Recommended for Enterprise Production):**
   - Separate state files and directory trees per environment (`dev`, `stage`, `prod`):
     ```
     terraform/
     ├── modules/
     │   ├── vpc/
     │   ├── eks/
     │   └── rds/
     └── environments/
         ├── dev/
         │   ├── main.tf        # Calls modules with dev sizing
         │   ├── variables.tf
         │   ├── terraform.tfvars
         │   └── backend.tf     # S3 key: dev/terraform.tfstate
         └── prod/
             ├── main.tf        # Calls modules with HA / multi-AZ sizing
             ├── variables.tf
             ├── terraform.tfvars
             └── backend.tf     # S3 key: prod/terraform.tfstate
     ```
   - **Pros:** Completely isolated state files eliminate the blast radius; production credentials and permissions can be isolated to distinct AWS accounts.

2. **Terraform Workspaces:**
   - Uses a single set of configuration files, with state files partitioned dynamically (`terraform.workspace`).
   - Sizing is managed via maps: `instance_type = var.instance_type[terraform.workspace]`.
   - **Pros:** Quick for non-prod testing.
   - **Cons:** Shared backend config, risky blast radius for production, difficult IAM privilege segregation.
</details>

<details>
<summary><strong>↳ Follow-up: Rather than how you separate environments, can you describe the actual file/module structure of your Terraform project, standardized so it can be reused across multiple teams and projects?</strong></summary>

**Answer:**
To create enterprise-reusable, standardized Terraform modules, I follow the **HashiCorp Standard Module Structure** combined with an internal module registry:

```
terraform-aws-microservice/          # Dedicated Git repository
├── README.md                        # Auto-generated documentation (terraform-docs)
├── LICENSE
├── main.tf                          # Primary resource definitions
├── variables.tf                     # Strongly typed inputs with descriptions & defaults
├── outputs.tf                       # Exposed attributes for consuming root modules
├── versions.tf                      # Required terraform & provider version pins
├── locals.tf                        # Standardized naming, tags, and calculations
│
├── modules/                         # Optional nested sub-modules
│   └── iam-role/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
└── examples/                        # Working examples for consumer teams
    ├── basic/
    │   ├── main.tf
    │   └── terraform.tfvars
    └── complete-ha/
        ├── main.tf
        └── terraform.tfvars
```

Key standardization conventions:
- **`versions.tf`:** Explicitly pins minimum provider versions:
  ```hcl
  terraform {
    required_version = ">= 1.5.0"
    required_providers {
      aws = {
        source  = "hashicorp/aws"
        version = "~> 5.0"
      }
    }
  }
  ```
- **Tag Enforcement:** All resources inherit standard mandatory organizational tags via `locals.tf` (Environment, Owner, CostCenter, ManagedBy = "Terraform").
</details>

<details>
<summary><strong>● If you were starting from scratch with a brand-new AWS account and tasked with setting up infrastructure using Terraform, what steps and prerequisites would you need before setting up the Terraform pipeline?</strong></summary>

**Answer:**
Starting from a fresh AWS account requires bootstrapping the core identity, state storage, and governance foundation:

1. **Root Account Hardening & Break-Glass Setup:**
   - Secure the AWS root account with FIDO/hardware MFA. Do not generate root API access keys.
   - Configure AWS IAM Identity Center (SSO) or create an initial administrative IAM role.

2. **Terraform Remote State Storage Bootstrapping:**
   - Create a dedicated Amazon S3 bucket for remote state storage:
     - Enable S3 Bucket Versioning (essential for state rollback if corrupted).
     - Enable default server-side encryption (AWS KMS or AES256).
     - Block all Public Access at the bucket level.
     - Add S3 bucket policy enforcing TLS 1.2+ (`aws:SecureTransport`).
   - Create an Amazon DynamoDB table for state locking (partition key `LockID` of type String).

3. **CI/CD OIDC Identity Federation:**
   - Configure OpenID Connect (OIDC) identity provider for GitHub Actions, GitLab, or Jenkins.
   - Create an IAM Role with an assume-role policy restricted to the repository and branch, eliminating static long-lived IAM credentials.

4. **Network & Organization Guardrails:**
   - Set up AWS Budgets and CloudWatch billing alerts.
   - Enable AWS CloudTrail in all regions delivering logs to an encrypted central S3 bucket.
</details>

<details>
<summary><strong>↳ Follow-up: What would you do to allow your Terraform setup/pipeline to authenticate and access the AWS account?</strong></summary>

**Answer:**
The industry best practice is **OIDC (OpenID Connect) Identity Federation**:

1. Create an IAM OIDC Identity Provider in AWS pointing to GitHub/GitLab (`https://token.actions.githubusercontent.com`).
2. Create an IAM Role with a Trust Policy conditioned on the repository path and branch:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
         },
         "Action": "sts:AssumeRoleWithWebIdentity",
         "Condition": {
           "StringEquals": {
             "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
           },
           "StringLike": {
             "token.actions.githubusercontent.com:sub": "repo:my-org/infra-repo:ref:refs/heads/main"
           }
         }
       }
     ]
   }
   ```
3. In the CI/CD pipeline, exchange the ephemeral JWT token for temporary AWS STS credentials. No static secrets exist anywhere.
</details>

<details>
<summary><strong>↳ Follow-up: Is installing the AWS CLI actually necessary for Terraform to access AWS?</strong></summary>

**Answer:**
**No, installing the AWS CLI is not required for Terraform to access AWS.**

- Terraform communicates with AWS APIs directly using the **AWS Go SDK** compiled inside the `hashicorp/aws` provider plugin binary.
- The provider natively resolves credentials using the standard AWS credential chain:
  1. Static provider arguments (`access_key`, `secret_key` - not recommended)
  2. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`)
  3. Shared credentials/config files (`~/.aws/credentials`)
  4. Container credentials (ECS task role)
  5. EC2 Instance Metadata Service (IMDSv2) IAM role
  6. Web Identity Token credentials (OIDC / EKS IRSA)

The AWS CLI is only useful if pipeline scripts need to run raw `aws ...` commands outside Terraform.
</details>

<details>
<summary><strong>↳ Follow-up: If your CI/CD pipeline is running as AWS CodePipeline within the AWS account itself, how would you provide it access to the AWS account/resources it needs to provision?</strong></summary>

**Answer:**
When using AWS CodePipeline and CodeBuild natively within AWS:

1. **IAM Service Roles:**
   - Attach an IAM Service Role to the **AWS CodeBuild** project that executes the `terraform init`, `plan`, and `apply` phases.
   - CodeBuild automatically retrieves ephemeral credentials from the AWS container environment without any stored keys.
2. **Cross-Account Provisioning via Role Assumption:**
   - If CodePipeline in the Tooling Account needs to deploy resources into Staging or Production accounts:
     - Create a cross-account role in target accounts (e.g., `arn:aws:iam::PROD_ACCOUNT:role/TerraformExecutionRole`).
     - Grant CodeBuild's service role permission to execute `sts:AssumeRole` on the target role.
     - In `main.tf`:
       ```hcl
       provider "aws" {
         region = "us-east-1"
         assume_role {
           role_arn     = "arn:aws:iam::PROD_ACCOUNT:role/TerraformExecutionRole"
           session_name = "CodePipelineDeploySession"
         }
       }
       ```
</details>

<details>
<summary><strong>● Given an S3 bucket that was created manually (outside of Terraform) in the same AWS account, how would you use Terraform to create bucket policies for that S3 bucket?</strong></summary>

**Answer:**
You reference the existing S3 bucket using its bucket name in the `aws_s3_bucket_policy` resource, along with an `aws_iam_policy_document` data source:

```hcl
# Reference the existing bucket policy resource
resource "aws_s3_bucket_policy" "manual_bucket_policy" {
  bucket = "manually-created-production-logs-bucket" # Use the actual bucket name string
  policy = data.aws_iam_policy_document.allow_tls_only.json
}

data "aws_iam_policy_document" "allow_tls_only" {
  statement {
    sid     = "EnforceTLSRequestsOnly"
    effect  = "Deny"
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    actions = ["s3:*"]
    resources = [
      "arn:aws:s3:::manually-created-production-logs-bucket",
      "arn:aws:s3:::manually-created-production-logs-bucket/*"
    ]
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}
```
</details>

<details>
<summary><strong>↳ Follow-up: Specifically, what is the exact approach to set bucket policies via Terraform for an S3 bucket that already exists but was not created via Terraform?</strong></summary>

**Answer:**
The exact approach is:
1. Define a `data "aws_s3_bucket"` block to query and validate the existing bucket's attributes dynamically from AWS:
   ```hcl
   data "aws_s3_bucket" "target_bucket" {
     bucket = "manually-created-production-logs-bucket"
   }
   ```
2. Construct the desired policy using `data "aws_iam_policy_document"`.
3. Attach the policy using the dedicated `aws_s3_bucket_policy` resource referencing `data.aws_s3_bucket.target_bucket.id`:
   ```hcl
   resource "aws_s3_bucket_policy" "enforce_security" {
     bucket = data.aws_s3_bucket.target_bucket.id
     policy = data.aws_iam_policy_document.policy.json
   }
   ```
This manages the *policy object* in Terraform state while leaving the lifecycle of the underlying S3 bucket itself unmanaged by Terraform.
</details>

<details>
<summary><strong>↳ Follow-up: Do you actually need to import the manually created S3 bucket into Terraform state just to set bucket policies on it, or is there another way?</strong></summary>

**Answer:**
**No, you do not need to import the S3 bucket.**

Because the AWS provider provides `aws_s3_bucket_policy` as a separate, independent resource from `aws_s3_bucket`:
- You only need to supply the target bucket name as a string (or via `data.aws_s3_bucket.<name>.id`) to `aws_s3_bucket_policy`.
- Terraform will manage the policy attachment without owning or risking deletion of the S3 bucket during a `terraform destroy`.
- You only need to import the S3 bucket if you want Terraform to manage bucket-level properties like versioning, lifecycle rules, tags, or encryption settings.
</details>

<details>
<summary><strong>↳ Follow-up: When would you use a Terraform data block versus an import block?</strong></summary>

**Answer:**
| Criteria | `data` Block | `import` Block |
|---|---|---|
| **Objective** | **Read-only query** to fetch existing infrastructure metadata. | **Adopt management** of an existing resource into Terraform state. |
| **State File Impact** | Stored ephemerally during plan/apply; Terraform **does not own** the resource. | Writes the resource into `.tfstate`; Terraform **now manages its entire lifecycle**. |
| **Destruction** | `terraform destroy` will **never** delete the queried resource. | `terraform destroy` **will permanently delete** the resource. |
| **Use Case** | Fetching default VPC ID, latest Amazon Linux AMI ID, or an existing subnet list. | Taking ownership of manually created RDS databases, EC2 instances, or DNS zones. |
</details>

<details>
<summary><strong>● Can you explain what Terraform drift is?</strong></summary>

**Answer:**
**Terraform drift** refers to any divergence between the actual state of physical cloud infrastructure and the state recorded in Terraform's state file (`terraform.tfstate`) or defined in code (`.tf` files).

- **Causes of Drift:**
  - Manual changes in the AWS Console (e.g., someone adds a security group rule or changes an EC2 instance size during an outage).
  - Out-of-band automation (scripts, autoscaling groups changing capacity, AWS services modifying attributes).
  - Failed Terraform apply executions leaving partial resource updates.
- **Detection & Reconciliation:**
  - `terraform plan -refresh-only`: Queries real AWS APIs, updates the state file with reality, and highlights discrepancies without modifying cloud resources.
  - Regular scheduled CI/CD drift detection jobs (e.g., daily cron in GitHub Actions running `terraform plan --detailed-exitcode`).
</details>

<details>
<summary><strong>● How would you implement a secure and auditable Terraform (infrastructure-as-code) workflow?</strong></summary>

**Answer:**
An enterprise secure and auditable IaC workflow is built around GitOps principles and pipeline gating:

1. **Strict Version Control Guardrails:**
   - Main branch is strictly protected. Direct pushes are disabled.
   - All changes require Pull Requests (PRs) with at least two senior peer approvals.
2. **Automated Pipeline Validation:**
   - Pre-commit: Run `terraform fmt -check` and `terraform validate`.
   - Security Scanning: Run `tflint`, `tfsec`, or `checkov`.
3. **Plan Artifact Archiving:**
   - Generate plans using `terraform plan -out=tfplan.binary`.
   - The apply stage only executes that exact binary plan, preventing race conditions or unreviewed code injections.
4. **State Protection & RBAC:**
   - S3 backend encrypted with dedicated AWS KMS customer-managed key with CloudTrail auditing.
   - Developers have read-only access to AWS console; only the CI/CD pipeline's assumed IAM role has provisioning rights.
</details>

<details>
<summary><strong>↳ Follow-up: What is the basic Terraform workflow/lifecycle (init, plan, apply, etc.)?</strong></summary>

**Answer:**
The standard Terraform lifecycle consists of five core stages:

1. **`terraform init`:** Initializes the working directory, downloads required provider plugins (`~/.terraform/providers`), and configures the remote backend.
2. **`terraform validate`:** Verifies the configuration files for syntactical correctness and internal consistency.
3. **`terraform plan`:** Queries the cloud provider APIs to refresh state, compares declared code against real infrastructure, and generates an execution plan detailing resources to be created, modified, or destroyed (`+`, `~`, `-`).
4. **`terraform apply`:** Executes the proposed changes against cloud APIs and updates `terraform.tfstate`.
5. **`terraform destroy`:** Terminates and tears down all managed infrastructure defined in the state file.
</details>

<details>
<summary><strong>↳ Follow-up: Building on the basic Terraform workflow, what specific measures would you put in place to secure it (e.g., PR-based changes, format/validate/lint/plan in pipeline)?</strong></summary>

**Answer:**
To transform the basic lifecycle into a secure enterprise workflow:

1. **PR-Level Automated Verification:**
   ```
   PR Created ──> terraform fmt ──> tflint ──> checkov/tfsec ──> terraform plan (speculative)
   ```
   - Speculative `terraform plan` is posted directly back to the PR comment via a bot (e.g., Atlantis or GitHub Actions comment bot).
2. **Policy as Code Enforcement:**
   - Integrate **Open Policy Agent (OPA) / Conftest** or **HashiCorp Sentinel** before the apply stage. Block any plan that provisions public S3 buckets, unencrypted EBS volumes, or unrestricted ingress (`0.0.0.0/0`) on port 22.
3. **Human Approval Gate:**
   - Merge to `main` triggers the production pipeline. An explicit manual approval from an authorized DevOps lead is required before `terraform apply` executes.
</details>

<details>
<summary><strong>↳ Follow-up: What security best practices have you incorporated into your Terraform IaC pipeline?</strong></summary>

**Answer:**
1. **Zero Hardcoded Secrets:** Pass sensitive values via environment variables (`TF_VAR_db_password`) fetched from AWS Secrets Manager or HashiCorp Vault at runtime.
2. **Remote State Hardening:**
   - Enable S3 bucket versioning and default KMS encryption.
   - Enforce IAM policy denying `s3:GetObject` on the state bucket to all human users; only the CI/CD role can read/write.
3. **Least Privilege Execution:**
   - Segment IAM roles per workload (e.g., Network role can only touch VPC/Route53, Application role can only touch ECS/EKS).
4. **Pinning Everything:**
   - Pin Terraform binary version (`.terraform-version`), provider versions (`~> 5.0`), and module Git tags (`?ref=v1.2.0`).
</details>

<details>
<summary><strong>↳ Follow-up: Specifically for the Terraform pipeline and Terraform code itself, do you have any security or vulnerability checks in place when the pipeline runs?</strong></summary>

**Answer:**
Yes. We implement a multi-scanner static analysis suite in our CI pipeline:

1. **`tfsec` / `trivy config`:**
   - Scans HCL code against CIS benchmarks and cloud security best practices (flags unencrypted disks, missing access logs, open security groups).
2. **`checkov`:**
   - Python-based static analysis tool for IaC. Runs 1000+ built-in policies covering AWS, Kubernetes, and Docker compliance frameworks (NIST, HIPAA, PCI-DSS).
3. **`tflint`:**
   - Catches cloud provider-specific errors that syntax validation misses (e.g., invalid AWS EC2 instance types, missing tags).
4. **Exit-Code Enforcement:**
   - Set pipeline step: `checkov -d . --framework terraform --hard-fail-on HIGH,CRITICAL`. Any high/critical finding immediately fails the pipeline.
</details>

<details>
<summary><strong>↳ Follow-up: Similar to the code quality/security checks used for a Java pipeline (like SonarQube), do you have any equivalent checks specifically for Terraform code?</strong></summary>

**Answer:**
Yes, the direct analogs in the Terraform ecosystem are:

| Java Pipeline Check | Terraform IaC Equivalent Tool | Purpose in Terraform |
|---|---|---|
| **Checkstyle / Prettier** | `terraform fmt -check` | Enforces uniform formatting and indentation across teams. |
| **SpotBugs / PMD** | `tflint` with `aws` ruleset | Detects anti-patterns, deprecated syntax, and invalid instance configurations. |
| **SonarQube (SAST)** | **Checkov** / **tfsec** | Evaluates security rules, CIS benchmarks, and compliance violations. |
| **OWASP Dependency-Check** | **Dependabot** / **Renovate** for Terraform | Tracks upstream provider and module updates for known vulnerabilities. |
| **Unit Testing (JUnit)** | **Terratest** (Go) / Native `terraform test` | Provisions ephemeral infrastructure, verifies assertions, and destroys resources. |
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Have you worked exclusively with AWS, and do you have any experience with Azure?</strong></summary>

**Answer:**
My primary production-grade expertise is centered on **AWS**, where I have architected and operated scalable multi-account environments. However, I have working cross-cloud architectural knowledge of **Microsoft Azure**:

- Conceptual mapping: AWS VPCs map to Azure **Virtual Networks (VNets)**, EC2 maps to **Azure Virtual Machines**, S3 maps to **Azure Blob Storage**, and AWS IAM Roles map to **Azure Managed Identities and RBAC**.
- Experience provisioning Azure base resources using Terraform's `azurerm` provider, configuring Azure Resource Groups, Virtual Networks, Subnets, and Network Security Groups (NSGs).
</details>

<details>
<summary><strong>↳ Follow-up: Can you explain what a Network Security Group (NSG) is in Azure?</strong></summary>

**Answer:**
An Azure **Network Security Group (NSG)** is a virtual packet-filtering firewall that controls inbound and outbound network traffic:

- **Attachment Targets:** Can be attached to a **Subnet** or individual **Network Interface (NIC)** of a VM.
- **Rule Structure:** Each rule specifies Priority (100–4096, lowest number evaluated first), Source/Destination IP/CIDR, Source/Destination Port, Protocol (TCP/UDP/ICMP), and Action (Allow/Deny).
- **Default Rules:** Includes default inbound deny (except VNet-to-VNet and Azure Load Balancer traffic) and default outbound allow.
- **Stateful Nature:** Like AWS Security Groups, NSGs are stateful. If an inbound request is permitted, the outbound response is automatically allowed regardless of outbound rules.
</details>

<details>
<summary><strong>↳ Follow-up: What do you know about Azure in general, even without hands-on experience?</strong></summary>

**Answer:**
Key architectural foundations of Azure include:
- **Hierarchical Governance:** Management Groups -> Subscriptions -> Resource Groups -> Resources.
- **Resource Groups:** Mandatory logical containers grouping related resources sharing a common lifecycle, tagging strategy, and RBAC boundary.
- **Identity:** Managed entirely by **Microsoft Entra ID** (formerly Azure AD), providing native Single Sign-On and OAuth2 federation.
- **Core Services:** Azure Kubernetes Service (AKS), Azure App Services (PaaS), Azure DevOps Services, and ExpressRoute (dedicated on-premises connection equivalent to AWS Direct Connect).
</details>

<details>
<summary><strong>↳ Follow-up: Why are you assuming that AWS does not have an equivalent concept to Azure's resource groups?</strong></summary>

**Answer:**
AWS does indeed have an equivalent feature called **AWS Resource Groups** (part of AWS Systems Manager / Resource Groups API), as well as application-level grouping via **AWS Service Catalog** and **AWS CloudFormation Stacks**.

However, there is an important architectural distinction:
- In **Azure**, a Resource Group is a **mandatory, first-class structural requirement**; every single Azure resource *must* belong to exactly one Resource Group at creation time.
- In **AWS**, resources are created directly in a Region within an AWS Account. AWS Resource Groups are an *optional tag-based or CloudFormation-based querying overlay* used for consolidated monitoring and automation.
</details>

<details>
<summary><strong>● Can you explain what a NAT gateway is in AWS?</strong></summary>

**Answer:**
An AWS **NAT (Network Address Translation) Gateway** is a managed AWS service that enables instances in a **private subnet** to connect outbound to the internet (e.g., for OS patching, package downloads, or third-party API calls) while preventing the external internet from initiating inbound connections to those private instances.

- **Placement:** Must reside in a **public subnet** with an allocated Elastic IP (EIP) and a route to an Internet Gateway (`0.0.0.0/0 -> igw-xxx`).
- **Private Subnet Route Table:** Private subnet route tables route outbound internet traffic to the NAT Gateway (`0.0.0.0/0 -> nat-xxx`).
- **High Availability:** A single NAT Gateway operates within a specific Availability Zone. For enterprise production HA, deploy one NAT Gateway per AZ to ensure an AZ outage does not sever internet connectivity for private workloads in other AZs.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● What deployment strategy would you recommend to minimize risks in a production environment?</strong></summary>

**Answer:**
For critical production environments, I recommend a **Canary Deployment** managed via GitOps and automated metric analysis (using **Argo Rollouts** or **Flagger** with Prometheus/Datadog):

```
100% v1 ──> [ Canary Shift: 10% v2 / 90% v1 ] ──(Metrics OK?)──> [ 50% v2 ] ──> [ 100% v2 ]
                                                      │
                                                (Error Spike?)
                                                      │
                                                      v
                                            [ Instant Abort & Undo ]
```

- **How it works:**
  1. Deploy the new version alongside the current stable version.
  2. Route a small, controlled percentage of traffic (e.g., 5% -> 10% -> 25%) to the new version using service mesh (Istio) or ALB Weighted Target Groups.
  3. Analyze telemetry in real time: HTTP 5xx error rate, p99 latency, and error logs.
  4. If anomalies are detected, traffic instantly falls back to 100% v1 with zero user disruption. If metrics remain healthy over 30 minutes, promote to 100%.
- **Alternative:** **Blue-Green Deployment** is preferred when database schema migrations or stateful dependencies prevent running two application versions simultaneously.
</details>

<details>
<summary><strong>↳ Follow-up: What kind of rollback strategy have you used in your deployments?</strong></summary>

**Answer:**
1. **Automated Metric-Driven Rollback (Kubernetes/Canary):**
   - Configured **Argo Rollouts** `AnalysisTemplate` monitoring Prometheus metrics:
     ```yaml
     metrics:
     - name: success-rate
       interval: 30s
       successCondition: result[0] >= 0.999
       failureLimit: 3
       provider:
         prometheus:
           address: http://prometheus.monitoring:9090
           query: sum(rate(http_requests_total{status!~"5.*"}[2m])) / sum(rate(http_requests_total[2m]))
     ```
   - If success rate drops below 99.9% 3 consecutive times, Argo Rollouts aborts the step and restores 100% traffic to stable immediately.
2. **One-Click GitOps Rollback:**
   - In Git, run `git revert <commit-sha>` and push to `main`. Argo CD detects the commit and rolls back the cluster state to the previous manifest revision.
3. **Emergency Manual Command:**
   - Fast-track command for on-call engineers: `kubectl rollout undo deployment/<service-name> -n production`.
</details>

<details>
<summary><strong>↳ Follow-up: How would you design a zero-downtime deployment strategy differently for stateless applications versus stateful applications?</strong></summary>

**Answer:**
1. **Stateless Applications (e.g., Web APIs, Microservices):**
   - **Characteristics:** Containers do not maintain local state; requests are fungible; session state is stored in external distributed caches (Redis) or databases.
   - **Strategy:** Straightforward **Rolling Updates** or **Canary Deployments**.
   - **Configuration:** Set `maxSurge: 25%` and `maxUnavailable: 0` in Deployment specs. Configure appropriate readiness probes and container lifecycle hooks (`preStop: sleep 15`) to drain connections gracefully before pod termination.

2. **Stateful Applications (e.g., Kafka Brokers, Elasticsearch, Databases):**
   - **Characteristics:** Nodes maintain local persistent storage, cluster quorum, and unique network identities.
   - **Strategy:**
     - Must use Kubernetes **`StatefulSet`** with `podManagementPolicy: OrderedReady` and `updateStrategy: RollingUpdate`.
     - Update **one replica at a time in reverse ordinal sequence** (`pod-2`, then `pod-1`, then `pod-0`).
     - Wait for the updated pod to become healthy and fully sync data (e.g., Kafka partition rebalancing or Elasticsearch replica green status) before proceeding to update the next replica.
     - **Database Migrations:** Follow the **Expand/Contract (Parallel Run) Pattern**:
       - *Phase 1 (Expand):* Add new nullable columns or tables. Old and new code work concurrently.
       - *Phase 2:* Deploy new application code writing to both columns.
       - *Phase 3 (Contract):* Backfill old data, switch reads to new columns, and drop legacy columns in a subsequent release.
</details>

</details>
</details>

<details open>
<summary><h2>🏢 R Systems</h2></summary>

<details open>
<summary><h3>Level 2</h3></summary>

#### 【 CI/CD 】

<details>
<summary><strong>● Which CI/CD tool do you use for deploying and managing this workload?</strong></summary>

**Answer:**
In our production architecture, we use a hybrid **GitLab CI / Jenkins** continuous integration engine combined with **Argo CD** for declarative GitOps continuous delivery:

- **CI Pipeline:** Handles compilation, unit testing, SonarQube static analysis, container image building with Kaniko, and Trivy security scanning.
- **GitOps CD with Argo CD:** Rather than granting Jenkins direct cluster admin credentials to execute `kubectl apply`, our CI pipeline updates the Kubernetes manifest repository (Helm values). Argo CD running inside the cluster continuously monitors Git and reconciles desired state with live cluster state, providing automated rollouts, health monitoring, and instant audit trails.
</details>

<details>
<summary><strong>↳ Follow-up: Do you use any other CI/CD tools besides Jenkins?</strong></summary>

**Answer:**
Yes. Across various production workloads and migration initiatives, I have extensive hands-on experience with:

1. **GitHub Actions:** Our primary choice for cloud-native microservices and open-source integrations, leveraging reusable workflows, composite actions, and OIDC-based short-lived AWS IAM authentication.
2. **GitLab CI/CD:** Utilized for end-to-end DevOps lifecycle management with auto-scaling Kubernetes-based GitLab Runners and native container/package registries.
3. **AWS CodePipeline & CodeBuild:** Implemented for AWS-native workloads requiring tight integration with AWS KMS, CloudTrail, and Service Catalog.
4. **Argo CD & Flux:** Used specifically for Kubernetes GitOps continuous delivery and progressive traffic routing.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>↳ Follow-up: Do you hold any certification for Kubernetes?</strong></summary>

**Answer:**
I have prepared for and pursued the **Certified Kubernetes Administrator (CKA)** curriculum. This hands-on, performance-based certification covers critical operational domains:
- Cluster architecture, installation, and configuration (bootstrap via `kubeadm`, TLS bootstrap, etcd backup/restore).
- Workloads and scheduling (affinity, anti-affinity, taints, tolerations, resource quotas).
- Cluster networking, CNI plugins (Calico, AWS VPC CNI), Ingress controllers, CoreDNS.
- Storage classes, PersistentVolumes, dynamic volume provisioning.
- Deep troubleshooting of kubelet, API server, network policies, and node conditions.
</details>

↳ **Candidate Introduction:** Can you restate your total years of hands-on production experience with Kubernetes?

<details>
<summary><strong>↳ Follow-up: Have you worked with any service mesh technology (e.g., Istio, Linkerd) in a Kubernetes environment?</strong></summary>

**Answer:**
Yes, I have implemented and managed **Istio Service Mesh** in production Kubernetes clusters:

1. **Sidecar Injection & Traffic Management:**
   - Deployed `istiod` control plane and enabled automated Envoy sidecar proxy injection per namespace (`istio-injection=enabled`).
   - Configured **VirtualServices** and **DestinationRules** for fine-grained L7 traffic routing, weighted canary deployments (e.g., 90% v1 / 10% v2), HTTP header-based routing, and URI path rewriting.
2. **Zero-Trust Security & mTLS:**
   - Enforced strict mutual TLS (`PeerAuthentication` in `STRICT` mode) across all inter-service communications, encrypting pod-to-pod transit traffic automatically with short-lived X.509 certificates rotated by Citadel/Istiod.
   - Defined `AuthorizationPolicy` manifests to restrict service-to-service communication (e.g., only `order-service` can call `payment-service` on `/v1/charge`).
3. **Resilience & Fault Injection:**
   - Implemented circuit breaking, connection pool limits, request timeouts, and retries within `DestinationRule` specs to prevent cascading microservice outages.
4. **Observability:**
   - Integrated Envoy telemetry with **Prometheus**, **Jaeger/Zipkin** for distributed tracing, and **Kiali** for live service graph visualization.
</details>

#### 【 IAC 】

<details>
<summary><strong>● For provisioning AWS-based workloads, do you use Terraform or CloudFormation?</strong></summary>

**Answer:**
We standardize on **HashiCorp Terraform** as our primary Infrastructure as Code (IaC) tool across all AWS workloads, while leveraging CloudFormation / AWS CDK selectively only when deploying AWS native Service Catalog portfolios or Control Tower Customizations:

- Terraform provides superior state management, explicit execution plan reviews (`terraform plan`), faster API feature velocity, modular reusability, and multi-provider capability (orchestrating AWS alongside Kubernetes, Cloudflare, and Datadog in a single unified workflow).
</details>

<details>
<summary><strong>↳ Follow-up: What is your reasoning for choosing Terraform over CloudFormation — is it primarily due to CloudFormation being vendor-specific to AWS, or are there other reasons?</strong></summary>

**Answer:**
While multi-cloud portability is an advantage, several technical and operational factors make Terraform superior even purely within AWS:

1. **Explicit Plan Preview (`terraform plan`):**
   - Terraform computes a deterministic dependency graph and displays exact additions, in-place updates, and destructive replacements (`+/-`) before anything touches AWS APIs.
   - CloudFormation Change Sets are slower to generate, often opaque regarding attribute changes, and do not catch validation errors until stack execution begins.
2. **State Management & Speed:**
   - Terraform maintains a local/remote state cache (`terraform.tfstate`), enabling rapid local diffing without querying every AWS API endpoint sequentially. CloudFormation stack operations often take significantly longer due to serialized stack locking.
3. **Ecosystem & Unified Toolchain:**
   - A single Terraform pipeline can provision an AWS EKS cluster (`hashicorp/aws`), configure Kubernetes namespaces and CRDs (`hashicorp/kubernetes`), deploy Helm charts (`hashicorp/helm`), and configure Datadog monitors (`datadog/datadog`). CloudFormation cannot manage non-AWS resources without complex custom resource Lambda handlers.
4. **Community Modules & Tooling:**
   - Access to the vast, battle-tested Terraform Registry (e.g., `terraform-aws-modules/vpc`, `terraform-aws-modules/eks`), along with static analysis tools like `tflint`, `tfsec`, and `checkov`.
</details>

<details>
<summary><strong>↳ Follow-up: If your infrastructure is solely on AWS with no need to support other cloud providers like GCP, would you still choose Terraform over CloudFormation?</strong></summary>

**Answer:**
**Yes, absolutely.** Even for 100% AWS-only workloads, Terraform remains the superior operational choice for:

1. **State Isolation & Blast Radius Control:**
   - Terraform allows breaking down infrastructure into decoupled state files (e.g., `network.tfstate`, `database.tfstate`, `compute.tfstate`). In CloudFormation, nested stacks or large monolithic stacks frequently hit the 500-resource limit or get stuck in unrecoverable `UPDATE_ROLLBACK_FAILED` states requiring AWS Support intervention.
2. **First-Class Refactoring & State Surgery:**
   - Terraform provides powerful CLI state management: `terraform state mv`, `terraform state rm`, and the native `moved {}` and `import {}` blocks, allowing seamless module refactoring without destroying and recreating live cloud resources.
3. **Developer Ergonomics (HCL vs JSON/YAML):**
   - HCL provides rich functional expressions (`for`, `for_each`, `dynamic`, `lookup`, `compact`), strong type validation, and validation rules (`validation {}` blocks in variables) that far surpass CloudFormation's clunky intrinsic functions (`!Sub`, `!Join`, `!GetAtt`).
</details>

<details>
<summary><strong>↳ Follow-up: Aside from vendor lock-in concerns, do you have any other reasons for preferring Terraform over CloudFormation?</strong></summary>

**Answer:**
Key engineering reasons include:
1. **Zero CloudFormation Stack Lock Outages:**
   - CloudFormation stacks frequently get deadlocked in `DELETE_FAILED` or `UPDATE_ROLLBACK_FAILED` if an out-of-band resource dependency exists. Recovering often requires deleting resources manually and re-importing. Terraform never locks the entire cloud stack; state locks are releaseable DynamoDB records (`terraform force-unlock`).
2. **Faster AWS API Feature Availability:**
   - The open-source `hashicorp/aws` provider often supports new AWS features and API parameters within days of AWS announcements, whereas CloudFormation resource specifications historically suffer from months of lag time for newly launched service features.
3. **Local Dry-Run Testing:**
   - With `terraform validate` and `terraform test`, engineers can run fast offline unit tests on their modules without spending cloud credits or waiting on AWS CloudFormation stack creation times.
</details>

#### 【 CLOUD 】

● **Candidate Introduction:** What is your total production-grade experience (excluding POCs, UAT, or non-production environments) working with AWS, Kubernetes, and Terraform?

<details>
<summary><strong>● If you have two AWS accounts, Account A and Account B, and need to securely connect from Account B to Account A, what are the best secure methods you have used to achieve this cross-account access?</strong></summary>

**Answer:**
The mechanism depends on whether the requirement is **Control Plane / IAM Access** or **Network Plane / Data Access**:

1. **Control Plane / Management Access (IAM Cross-Account Role Assumption):**
   - **Method:** Create an IAM Role in Account A (`arn:aws:iam::AccountA:role/CrossAccountServiceRole`) with a Trust Policy granting `sts:AssumeRole` to Account B's root or specific IAM principal:
     ```json
     {
       "Effect": "Allow",
       "Principal": { "AWS": "arn:aws:iam::AccountB:role/AppExecutionRole" },
       "Action": "sts:AssumeRole",
       "Condition": { "StringEquals": { "sts:ExternalId": "SecureEnterpriseToken123" } }
     }
     ```
   - Workloads in Account B invoke `sts:AssumeRole` to receive temporary credentials (15m to 1hr expiry) to interact with Account A's APIs.

2. **Network Plane / Inter-VPC Private Communication:**
   - **AWS Transit Gateway (TGW):** Shared across accounts via **AWS RAM (Resource Access Manager)**. Ideal for scalable hub-and-spoke multi-account topologies connecting dozens of VPCs with route table domain segmentation.
   - **AWS VPC Peering:** For point-to-point, non-overlapping CIDR cross-account communication with zero bandwidth bottlenecks and no extra hourly managed service charge.
   - **AWS PrivateLink (VPC Endpoint Services):** Best when sharing specific TCP/HTTPS services from Account A to Account B without exposing entire subnets or worrying about overlapping CIDRs.
</details>

<details>
<summary><strong>↳ Follow-up: Is there a way to restrict this cross-account AWS access to a specific machine rather than to a user?</strong></summary>

**Answer:**
Yes. You can lock down IAM role assumption and resource policies to a specific machine using several complementary IAM condition keys:

1. **IP-Based Machine Restriction (`aws:SourceIp`):**
   - If the machine has a dedicated static public Elastic IP or egresses through a known corporate NAT Gateway:
     ```json
     "Condition": {
       "IpAddress": { "aws:SourceIp": "203.0.113.50/32" }
     }
     ```
2. **VPC Endpoint Restriction (`aws:sourceVpce` / `aws:sourceVpc`):**
   - If the calling machine runs within a specific VPC or calls AWS via an internal VPC Interface Endpoint:
     ```json
     "Condition": {
       "StringEquals": { "aws:sourceVpce": "vpce-0123456789abcdef0" }
     }
     ```
3. **Instance Profile Principal ARN (`aws:PrincipalArn` / `aws:userId`):**
   - If the calling machine is an EC2 instance in Account B, bind the trust policy directly to that EC2 instance's IAM Role (`arn:aws:iam::AccountB:role/EC2AppRole`) or instance profile role ID, ensuring human IAM users in Account B cannot assume the role.
4. **AWS Systems Manager (SSM) Host-Level Identity:**
   - Use AWS Systems Manager On-Premises Managed Instances with AWS IoT credentials or IAM Roles Anywhere (using X.509 machine certificates) to authenticate specific physical hardware.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Given a Python-based OCR application that needs to be deployed on AWS, where the service can remain idle for extended periods but must be able to handle up to 1,000 requests per minute, and the design must be cost-optimized while also ensuring Disaster Recovery (DR) and High Availability (HA), what high-level AWS services would you use and how would you configure the architecture to meet these requirements?</strong></summary>

**Answer:**
To reconcile extended idle periods (scale-to-zero cost optimization) with high-burst capacity (1,000 RPM) and multi-AZ/multi-region HA/DR, we employ an **Event-Driven Asynchronous Serverless Architecture**:

```
[ Client Requests ]
        │
        v
[ Amazon Route 53 (Latency / Failover Routing + Health Checks) ]
        │
        v
[ Amazon API Gateway (Regional, HTTP API / Payload validation) ]
        │
        v
[ Amazon S3 (Input Bucket: Upload raw image / pre-signed URL) ]
        │ (S3 Event Notification)
        v
[ Amazon SQS FIFO / Standard (Buffering Queue: Absorbs 1000 RPM burst) ]
        │
        v
[ AWS Lambda (Python OCR Workers on Graviton2) ]  <── [ DLQ for Poison Pills ]
  - Auto-scales concurrency (0 to hundreds)
  - Loads Tesseract/EasyOCR via Lambda Layer / Container Image
        │
        ├──> [ Amazon DynamoDB (Stores extracted text & metadata) ]
        └──> [ Amazon S3 (Output Bucket: JSON/Searchable PDF) ]
```

1. **Component Breakdown & Cost-Optimization:**
   - **Ingestion:** Clients upload images to **Amazon S3** via pre-signed URLs provided by **Amazon API Gateway**. Direct-to-S3 upload eliminates API Gateway payload transfer fees.
   - **Buffering:** S3 upload publishes an event to **Amazon SQS**. SQS buffers the 1,000 RPM burst, preventing downstream overload and guaranteeing zero message loss.
   - **Compute (Scale-to-Zero):** **AWS Lambda** configured with container images (packaging Python, OpenCV, and PyTesseract) running on **AWS Graviton2 (arm64)** for 20% lower cost.
     - When idle: **$0 compute cost** (scales to 0 instances).
     - During burst: SQS event source mapping scales Lambda concurrency up to hundreds of parallel executions.
   - **Storage:** S3 lifecycle rules transition raw images to **S3 Intelligent-Tiering** or Glacier Flexible Archive after 30 days.

2. **High Availability (HA) & Disaster Recovery (DR):**
   - **HA:** All chosen services (API Gateway, S3, SQS, Lambda, DynamoDB) are inherently **Multi-AZ serverless primitives** with 99.99%+ availability SLAs out-of-the-box.
   - **DR Strategy (Warm Standby / Active-Passive):**
     - Primary Region: `us-east-1`, Secondary Region: `us-west-2`.
     - **Route 53 Application Recovery Controller (ARC)** for DNS failover.
     - **S3 Cross-Region Replication (CRR)** replicates images to secondary region.
     - **DynamoDB Global Tables** replicates extracted metadata bidirectionally with sub-second latency.
</details>

#### 【 BEHAVIORAL 】

<details>
<summary><strong>● Can you explain the difference between a Build Engineer role and a DevOps Engineer role, based on your experience?</strong></summary>

**Answer:**
While both roles focus on delivering software, their scope, operational boundaries, and architectural responsibilities differ significantly:

| Dimension | Build Engineer | DevOps Engineer |
|---|---|---|
| **Core Focus** | Software compilation, packaging, artifact versioning, and build script maintenance. | End-to-end software delivery lifecycle, infrastructure automation, reliability, and culture. |
| **Tooling Scope** | Maven, Gradle, Ant, Make, MSBuild, compiler optimizations, dependency trees, Nexus/Artifactory. | Terraform, Kubernetes, Helm, Cloud Platforms (AWS/Azure), CI/CD engines, Prometheus/Grafana, Vault. |
| **Infrastructure Ownership** | Maintains build farm hardware/VMs, compilers, and static build slaves. | Provisions and manages the entire cloud infrastructure, VPCs, clusters, databases, and network topologies via IaC. |
| **Operational Responsibility** | Generally stops once artifacts (`.jar`, `.war`, `.rpm`) are successfully published to repository. | Owns the pipeline through staging/production deployments, zero-downtime releases, monitoring, and on-call response. |
| **Philosophy** | Specialization in deterministic, reproducible builds and dependency hygiene. | Cross-functional culture breaking silos between Dev, QA, Security, and Operations. |
</details>

<details>
<summary><strong>● Do you have any additional suggestions or feedback regarding the architecture design task that was given to you?</strong></summary>

**Answer:**
To further optimize the proposed architecture for enterprise readiness, I would recommend three production-grade additions:

1. **Pre-Warming & Cold Start Mitigation:**
   - Large Python OCR models (like PaddleOCR or Tesseract) can experience cold starts of 3–5 seconds. If the application requires sub-second SLA during sudden bursts, configure **Lambda Provisioned Concurrency** scheduled around predictable business hours, or implement an async webhook architecture where clients receive a job ID immediately and get notified via WebSockets/SNS upon OCR completion.
2. **Dead Letter Queue (DLQ) & Poison Pill Handling:**
   - Corrupted or unreadable image uploads must not cause infinite Lambda retries. Attach an SQS Dead Letter Queue with a redrive policy (max receive count: 3) and an automated CloudWatch alarm notifying engineers of unprocessable files.
3. **Security & Data Privacy (PII Redaction):**
   - If OCR processes sensitive identity documents (passports, credit cards), integrate **Amazon Comprehend Medical / PII detection** to automatically mask sensitive fields before persisting output to DynamoDB, and ensure S3 client-side KMS envelope encryption.
</details>

</details>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 CI/CD 】

<details>
<summary><strong>● Which CI/CD tool do you use most frequently?</strong></summary>

**Answer:**
In my day-to-day work, I use **Jenkins** and **GitHub Actions** most frequently. 
- Jenkins serves as our robust, self-hosted CI orchestrator deployed on Kubernetes agents for heavy enterprise legacy workloads and custom enterprise plugin integrations.
- GitHub Actions is our primary tool for modern microservices, providing cloud-native workflows, matrix testing, and seamless developer feedback directly inside Pull Requests.
</details>

<details>
<summary><strong>↳ Follow-up: Besides Jenkins, have you used any other CI/CD tools?</strong></summary>

**Answer:**
Yes. Beyond Jenkins, I have hands-on experience with:
- **GitHub Actions:** Workflow authoring, reusable workflows, custom composite actions, and OIDC AWS integration.
- **GitLab CI/CD:** Writing `.gitlab-ci.yml`, managing Kubernetes-based auto-scaling GitLab Runners, and leveraging GitLab Container Registry.
- **Argo CD:** Operating declarative GitOps continuous delivery targeting multiple Amazon EKS clusters.
- **AWS CodePipeline & CodeBuild:** Configuring AWS-native deployment automation.
</details>

<details>
<summary><strong>● Suppose you have a Jenkins scripted pipeline with three stages — CodeBuild, CodeTest, and CodeDeploy — for a Java application that needs to be deployed to an AWS EC2 instance, and your Jenkins server is completely separate from AWS. How would you configure the integration between Jenkins and AWS, and how would your pipeline determine which specific EC2 instance to deploy the code to?</strong></summary>

**Answer:**
Here is the production-grade implementation for secure, decoupled Jenkins-to-AWS deployment:

1. **Authentication Between Separate Jenkins and AWS:**
   - **Zero Static Credentials Best Practice:** Avoid storing permanent AWS IAM access keys in Jenkins. Instead:
     - Configure an **OIDC Identity Provider** in AWS for Jenkins, OR
     - If Jenkins is on-premises, use **AWS IAM Roles Anywhere** (X.509 certificate authentication), OR
     - Store a restricted IAM User credential in Jenkins Credentials Store that only has permission to execute `sts:AssumeRole` into a designated deployment role in the target AWS account.
   - In the Jenkins pipeline, use `withAWS(role: 'arn:aws:iam::123456789012:role/JenkinsDeployRole')` to retrieve short-lived STS tokens.

2. **Determining Target EC2 Instances Dynamically via AWS Tags:**
   - **Never hardcode private IP addresses or EC2 Instance IDs.**
   - Tag EC2 instances with standard operational tags: `Environment = "production"`, `Application = "payment-gateway"`, `Role = "web-tier"`.
   - In the pipeline, discover healthy instances dynamically using the AWS CLI:
     ```bash
     TARGET_INSTANCES=$(aws ec2 describe-instances \
       --filters "Name=tag:Environment,Values=production" \
                 "Name=tag:Application,Values=payment-gateway" \
                 "Name=instance-state-name,Values=running" \
       --query "Reservations[*].Instances[*].InstanceId" \
       --output text)
     ```

3. **Secure Deployment Execution (Without Direct SSH Port 22 Open):**
   - Use **AWS Systems Manager (SSM) Run Command** or **AWS CodeDeploy**:
     ```groovy
     stage('CodeDeploy') {
         steps {
             sh """
             aws ssm send-command \
               --instance-ids ${TARGET_INSTANCES} \
               --document-name "AWS-RunShellScript" \
               --parameters 'commands=[
                 "aws s3 cp s3://app-artifacts/target/app-${BUILD_NUMBER}.jar /opt/app/app.jar",
                 "systemctl restart payment-service",
                 "curl -f http://localhost:8080/healthz"
               ]'
             """
         }
     }
     ```
   - This eliminates the need to expose port 22 or maintain SSH key pairs across machines.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Do you have experience working with Amazon ECS and EKS?</strong></summary>

**Answer:**
Yes, I have worked extensively with both container platforms on AWS:

- **Amazon ECS (Elastic Container Service):**
  - AWS-native, highly opinionated container management service.
  - Deeply integrated with AWS IAM (Task Execution Roles vs Task Roles), CloudWatch Logs (`awslogs` driver), Application Load Balancers, and Service Discovery (AWS Cloud Map).
  - Ideal for rapid deployments on **AWS Fargate** where teams want zero control plane overhead and do not require Kubernetes API custom resources (CRDs).
- **Amazon EKS (Elastic Kubernetes Service):**
  - Standard CNCF-compliant managed Kubernetes control plane.
  - Required when workloads leverage the broader cloud-native ecosystem: Helm, Argo CD, Istio service mesh, Prometheus Operator, cert-manager, and multi-cloud portability.
  - Experience includes provisioning EKS via Terraform, configuring AWS VPC CNI with custom networking, deploying Karpenter for rapid node autoscaling, and managing IAM Roles for Service Accounts (IRSA / EKS Pod Identity).
</details>

● **Candidate Introduction:** How many years of experience do you have working with Kubernetes?

↳ **Candidate Introduction:** Is your Kubernetes experience hands-on?

<details>
<summary><strong>↳ Follow-up: Have you ever set up a Kubernetes cluster from scratch?</strong></summary>

**Answer:**
Yes. I have set up Kubernetes clusters from scratch both for educational/deep-dive architectural understanding and for enterprise production environments:
- **Bare-Metal / VM Setup via `kubeadm`:** Provisioned Linux VMs, configured kernel modules (`overlay`, `br_netfilter`), disabled swap, installed container runtime (`containerd`), initialized control plane with `kubeadm init`, configured CNI networking (Calico), and joined worker nodes with `kubeadm join`.
- **Production Enterprise Setup via IaC:** Automated multi-AZ EKS cluster provisioning using **Terraform** (`terraform-aws-modules/eks`), configuring managed node groups, KMS secret envelope encryption, private API endpoints, OIDC providers, and core add-ons (VPC-CNI, CoreDNS, kube-proxy, EBS CSI driver).
</details>

<details>
<summary><strong>↳ Follow-up: Which method did you use to set up the Kubernetes cluster from scratch (e.g., kubeadm, ArgoCD, etc.)?</strong></summary>

**Answer:**
To clarify the architectural distinction:
- **`kubeadm`** is the official Kubernetes cluster bootstrapping tool used to initialize the control plane (`kubeadm init`), generate cryptographic certificates, configure static control plane pods, and join worker nodes (`kubeadm join`).
- **Argo CD** is **not** a cluster creation tool; it is a **GitOps continuous delivery engine** that runs *inside* an already provisioned cluster to deploy and sync application workloads.

For bootstrapping from bare OS:
1. Bootstrapped base compute nodes and networking prerequisites.
2. Executed `kubeadm init --pod-network-cidr=192.168.0.0/16 --control-plane-endpoint "k8s-lb:6443" --upload-certs`.
3. Applied the CNI manifest (`kubectl apply -f calico.yaml`).
4. Joined worker nodes using tokenized `kubeadm join` commands.
5. In production AWS, we leverage **Terraform** to provision managed EKS clusters.
</details>

<details>
<summary><strong>● How many components make up the Kubernetes control plane (master node)?</strong></summary>

**Answer:**
There are **4 primary core components** that comprise the standard Kubernetes control plane, plus a 5th cloud-integration component:

1. **`kube-apiserver`** (Cluster API gateway)
2. **`etcd`** (Distributed key-value state database)
3. **`kube-scheduler`** (Pod placement engine)
4. **`kube-controller-manager`** (Core state reconciliation loops)
5. **`cloud-controller-manager`** (Optional/Cloud-specific integration component for AWS/Azure/GCP APIs)
</details>

<details>
<summary><strong>↳ Follow-up: Exactly how many control plane components are there, and what are their names?</strong></summary>

**Answer:**
There are **5 control plane components** in modern cloud environments:

1. **`kube-apiserver`:** The REST interface; authenticates, authorizes, admits, and validates all cluster operations.
2. **`etcd`:** The distributed, highly available key-value store holding the complete cluster state and object specifications.
3. **`kube-scheduler`:** Inspects unscheduled pods and assigns them to suitable worker nodes based on resource constraints, affinity, and taints.
4. **`kube-controller-manager`:** Bundles core controllers into a single binary: Node Controller, ReplicaSet Controller, EndpointSlice Controller, ServiceAccount Controller, and Namespace Controller.
5. **`cloud-controller-manager`:** Decouples cloud-specific logic (provisioning AWS ELB/ALB, attaching EBS volumes, managing cloud VPC routing tables) from the core Kubernetes code.
</details>

<details>
<summary><strong>↳ Follow-up: What is the main responsibility of the Kubernetes scheduler?</strong></summary>

**Answer:**
The primary responsibility of the `kube-scheduler` is to **watch for newly created Pods that have no node assigned (`spec.nodeName` is empty) and select the single best worker node for them to run on**.

It achieves this through a two-step algorithmic loop:
1. **Filtering (Predicates):** Eliminates nodes that do not meet pod requirements (insufficient CPU/RAM, unscheduled taints, missing node labels).
2. **Scoring (Priorities):** Ranks candidate nodes using weighted plugins (resource balance, image locality, affinity rules) and binds the pod to the node with the highest score.
</details>

<details>
<summary><strong>● Suppose you deploy an nginx application with 3 replicas across a cluster of 5 worker nodes, and you want exactly one pod scheduled per node, only on nodes 1, 2, and 3 — never on nodes 4 or 5, even if pods restart or get rescheduled. How would you configure this?</strong></summary>

**Answer:**
To enforce this constraint strictly, you combine **Node Affinity (Hard Rule)** with **Pod Anti-Affinity (Hard Rule)**:

1. **Label the Allowed Nodes (Nodes 1, 2, and 3):**
   ```bash
   kubectl label nodes node-1 node-2 node-3 app-target=nginx-nodes
   ```
   (Do NOT label node-4 or node-5).

2. **Configure the Deployment Manifest:**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: nginx-deployment
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: nginx
     template:
       metadata:
         labels:
           app: nginx
       spec:
         affinity:
           # Constraint 1: Restrict scheduling strictly to nodes 1, 2, and 3
           nodeAffinity:
             requiredDuringSchedulingIgnoredDuringExecution:
               nodeSelectorTerms:
               - matchExpressions:
                 - key: app-target
                   operator: In
                   values:
                   - nginx-nodes

           # Constraint 2: Ensure exactly one pod per node (no co-location)
           podAntiAffinity:
             requiredDuringSchedulingIgnoredDuringExecution:
             - labelSelector:
                 matchExpressions:
                 - key: app
                   operator: In
                   values:
                   - nginx
               topologyKey: "kubernetes.io/hostname"
         containers:
         - name: nginx
           image: nginx:alpine
   ```

**Why this works:**
- `nodeAffinity` hard rule guarantees pods will *never* land on node-4 or node-5.
- `podAntiAffinity` hard rule with `topologyKey: kubernetes.io/hostname` prevents two nginx pods from ever running on the same node.
- Since there are 3 replicas and 3 matching nodes, exactly 1 pod runs per node on nodes 1, 2, and 3.
</details>

<details>
<summary><strong>↳ Follow-up: Between node selector and node affinity, which one have you used in practice, and why?</strong></summary>

**Answer:**
In production enterprise environments, I use **Node Affinity** almost exclusively:

- **`nodeSelector`** is a legacy, primitive mechanism supporting only simple equality key-value matching (`disk: ssd`).
- **Node Affinity** provides:
  1. **Rich Expressive Operators:** Supports `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, and `Lt`.
  2. **Soft vs. Hard Enforcement:** Allows both strict mandatory placement (`requiredDuringSchedulingIgnoredDuringExecution`) and flexible best-effort scoring (`preferredDuringSchedulingIgnoredDuringExecution`).
  3. **Multi-condition Grouping:** Supports logical OR across `nodeSelectorTerms` and logical AND across `matchExpressions`.
</details>

<details>
<summary><strong>↳ Follow-up: What do you mean by 'soft rule' and 'hard rule' in the context of Kubernetes node affinity?</strong></summary>

**Answer:**
In Kubernetes Node Affinity:

1. **Hard Rule (`requiredDuringSchedulingIgnoredDuringExecution`):**
   - **Mandatory constraint.** If no worker node in the cluster satisfies this rule, the pod **cannot be scheduled and remains in `Pending` state**. The scheduler will never compromise on a hard rule.
   - Example: Requiring dedicated GPU nodes for machine learning workloads.

2. **Soft Rule (`preferredDuringSchedulingIgnoredDuringExecution`):**
   - **Advisory / Best-effort preference.** The scheduler iterates over candidate nodes and assigns weight scores (1–100) to nodes matching the rule.
   - If a matching node is available, the pod lands there. If no matching node is available or capacity is full, the scheduler **still schedules the pod on another available node** rather than letting it stay pending.
   - Example: Preferring nodes in a specific availability zone or nodes that already have cached image layers.
</details>

<details>
<summary><strong>● What is the difference between a startup probe and a readiness probe in Kubernetes?</strong></summary>

**Answer:**
| Feature | Startup Probe | Readiness Probe |
|---|---|---|
| **Primary Goal** | Determines if a slow-booting application has completed its initial boot sequence. | Determines if an already running pod is ready to accept user network traffic. |
| **Probe Interaction** | **Disables all other probes** (liveness and readiness) until it succeeds once. | Runs continuously throughout the pod's entire active lifecycle. |
| **Failure Result** | Kubelet terminates and restarts the container after `failureThreshold` is exceeded. | Removes Pod IP from Service EndpointSlice; container is **not** killed or restarted. |
| **Typical Target** | Heavy legacy Java applications, warming up caches, running database migrations. | Checking database connection pool saturation, transient worker queue overload. |
</details>

#### 【 IAC 】

● **Candidate Introduction:** Do you have experience working with Terraform?

↳ **Candidate Introduction:** How many years of experience do you have with Terraform?

↳ **Candidate Introduction:** Is your 2+ years of Terraform experience hands-on, and have you used Terraform in a real production environment?

<details>
<summary><strong>● What is the difference between a static block and a dynamic block in Terraform?</strong></summary>

**Answer:**
In Terraform HCL:

1. **Static Block:**
   - Explicitly declared in the configuration. The number of nested blocks is hardcoded and fixed:
     ```hcl
     resource "aws_security_group" "web_sg" {
       name = "web-sg"
       ingress {
         from_port   = 80
         to_port     = 80
         protocol    = "tcp"
         cidr_blocks = ["0.0.0.0/0"]
       }
       ingress {
         from_port   = 443
         to_port     = 443
         protocol    = "tcp"
         cidr_blocks = ["0.0.0.0/0"]
       }
     }
     ```
   - Inflexible: Adding a new port requires editing code manually.

2. **Dynamic Block (`dynamic "<block_name>"`):**
   - Generates nested configuration blocks programmatically by iterating over a collection (list, map, or set) using `for_each`:
     ```hcl
     variable "allowed_ports" {
       type    = list(number)
       default = [80, 443, 8080]
     }

     resource "aws_security_group" "dynamic_sg" {
       name = "dynamic-web-sg"
       dynamic "ingress" {
         for_each = var.allowed_ports
         content {
           from_port   = ingress.value
           to_port     = ingress.value
           protocol    = "tcp"
           cidr_blocks = ["0.0.0.0/0"]
         }
       }
     }
     ```
   - Standardizes reusable modules where consumer teams supply variable lists of rules without modifying module source code.
</details>

<details>
<summary><strong>● Why do we use the 'for_each' construct in Terraform?</strong></summary>

**Answer:**
`for_each` is used to create multiple instances of a resource or module based on a map or set of strings, offering decisive advantages over the legacy `count` parameter:

1. **Stable State Addressing by Key (Avoiding Index Shifting):**
   - When using `count`, resources are addressed by numerical index (`aws_subnet.public[0]`, `[1]`, `[2]`). If you remove the item at index 0, Terraform re-indexes all subsequent resources, causing unwanted destruction and recreation of healthy production resources.
   - With `for_each`, resources are addressed by key (`aws_subnet.public["us-east-1a"]`). Removing an item deletes *only that specific resource*, leaving all other instances untouched.
2. **Dynamic Configuration Flexibility:**
   - Enables passing detailed maps containing distinct attributes per instance (e.g., custom CIDR, AZ, and tags per subnet) rather than uniform copies.
</details>

<details>
<summary><strong>● What is Terraform state locking?</strong></summary>

**Answer:**
**Terraform state locking** is a concurrency control mechanism that prevents simultaneous write operations on the state file.

- **Why it is essential:** If two engineers or two CI/CD pipeline runs execute `terraform apply` concurrently without locking, they would create race conditions, corrupting the state file and leading to duplicated or orphaned cloud resources.
- **How it functions:** When any state-mutating command (`plan`, `apply`, `destroy`) begins, Terraform acquires a lock. Any concurrent execution attempting to run against the same backend receives a `Error acquiring the state lock` message and aborts immediately until the initial operation completes and releases the lock.
</details>

<details>
<summary><strong>↳ Follow-up: If you have Terraform scripts with an AWS provider and need to provision infrastructure on AWS, what are the steps to lock the Terraform state file (tfstate)?</strong></summary>

**Answer:**
To implement state locking on AWS:

1. **Step 1: Create Amazon S3 Bucket for State Storage:**
   - Enable S3 Bucket Versioning and KMS encryption.
2. **Step 2: Create Amazon DynamoDB Table for Locking:**
   - Table Name: `terraform-state-locks`
   - Primary Partition Key: **`LockID`** (Type: **String**). *This exact name and type are required by Terraform.*
3. **Step 3: Configure the S3 Backend in Terraform (`backend.tf`):**
   ```hcl
   terraform {
     required_version = ">= 1.5.0"
     backend "s3" {
       bucket         = "my-enterprise-tf-state-prod"
       key            = "workloads/payment-service/terraform.tfstate"
       region         = "us-east-1"
       encrypt        = true
       dynamodb_table = "terraform-state-locks" # Enables distributed state locking
     }
   }
   ```
4. **Step 4: Initialize the Backend:**
   - Run `terraform init` to migrate local state to S3 and bind the DynamoDB locking table.
</details>

#### 【 CLOUD 】

● **Candidate Introduction:** How many years of hands-on experience do you have with AWS?

↳ **Candidate Introduction:** Is your AWS experience hands-on?

↳ **Candidate Introduction:** On a scale of 1 to 5, how would you rate your AWS expertise?

↳ **Candidate Introduction:** May I address you as Nidhi for the rest of the interview?

<details>
<summary><strong>● Which AWS services have you used most frequently in your work?</strong></summary>

**Answer:**
My primary production toolset on AWS spans:
- **Compute & Containers:** EC2, Amazon EKS, Amazon ECS, AWS Fargate, AWS Lambda.
- **Networking:** VPC, Public/Private Subnets, NAT Gateways, Internet Gateways, Transit Gateway, Route 53, ALB/NLB, VPC Endpoints (PrivateLink).
- **Storage & Database:** Amazon S3, EBS (gp3/io2), EFS, RDS (PostgreSQL/MySQL Multi-AZ), DynamoDB.
- **Security & Identity:** IAM (Roles, Policies, OIDC, Permission Boundaries), AWS Secrets Manager, AWS KMS, AWS WAF, Security Groups, NACLs.
- **Management & Observability:** CloudWatch (Metrics, Logs, Alarms), CloudTrail, AWS Systems Manager (SSM Session Manager, Parameter Store).
</details>

<details>
<summary><strong>● Suppose you have an EC2 instance running in a private subnet for database purposes, and you want to ensure nobody can access it directly, but you still need to enable internet access on it for patching purposes. How would you configure this to keep it private while enabling internet access?</strong></summary>

**Answer:**
Here is the secure, production-grade network and security architecture:

1. **VPC & Subnet Layout:**
   - Place the database EC2 instance in a **Private Subnet** with no Public IPv4 address assigned (`map_public_ip_on_launch = false`).
2. **NAT Gateway Routing:**
   - Deploy an **AWS NAT Gateway** in a **Public Subnet** (associated with an Elastic IP).
   - In the Private Subnet's Route Table, add a default route:
     `0.0.0.0/0 -> nat-xxxxxxxxxxxxxxxxx`
   - This allows the EC2 instance to initiate outbound requests to download OS security patches from upstream repositories, while blocking external internet hosts from initiating inbound connections.
3. **Strict Security Group Ingress/Egress:**
   - **Inbound Rules:** Restrict to only the application server security group on the database port (e.g., TCP 5432 from `sg-app-servers`). Deny all other inbound traffic (no SSH port 22 open).
   - **Outbound Rules:** Restrict to HTTPS (port 443) and HTTP (port 80) directed to OS package mirror endpoints.
4. **Administrative Access without Bastion or Public IP:**
   - Attach an IAM Role with `AmazonSSMManagedInstanceCore` to the EC2 instance.
   - Engineers access the instance terminal securely via **AWS Systems Manager (SSM) Session Manager**, logged to CloudTrail, with zero inbound ports open.
</details>

<details>
<summary><strong>↳ Follow-up: If team members or employees have general AWS access but should not be able to access this specific EC2 instance, would you achieve this by modifying IAM roles and permissions?</strong></summary>

**Answer:**
Yes. Rather than relying solely on network rules, access to specific EC2 instances is strictly governed using **IAM Resource-Level Permissions and Attribute-Based Access Control (ABAC)**:

1. Tag the sensitive EC2 instance: `Confidentiality = "Restricted-DB"`.
2. In the IAM policies attached to general employee roles, implement an explicit `Deny` on AWS Systems Manager Session Manager actions for instances possessing that tag:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "DenyAccessToRestrictedDatabaseInstances",
         "Effect": "Deny",
         "Action": [
           "ssm:StartSession",
           "ssm:SendCommand",
           "ec2-instance-connect:SendSSHPublicKey"
         ],
         "Resource": "arn:aws:ec2:*:*:instance/*",
         "Condition": {
           "StringEquals": {
             "aws:ResourceTag/Confidentiality": "Restricted-DB"
           }
         }
       }
     ]
   }
   ```
3. Since explicit `Deny` overrides any `Allow`, general users cannot establish interactive sessions, run remote commands, or push SSH keys to that instance.
</details>

<details>
<summary><strong>↳ Follow-up: What are the steps to configure a NAT Gateway in AWS?</strong></summary>

**Answer:**
1. **Allocate an Elastic IP (EIP):**
   - Go to VPC Console -> Elastic IPs -> Allocate Elastic IP (Amazon IPv4 pool).
2. **Create the NAT Gateway:**
   - VPC Console -> NAT Gateways -> Create NAT Gateway.
   - Select a **Public Subnet** (a subnet with a route to an Internet Gateway).
   - Associate the allocated Elastic IP.
3. **Update the Private Subnet Route Table:**
   - Navigate to Route Tables -> Select Private Subnet Route Table -> Edit Routes.
   - Add route: Destination `0.0.0.0/0`, Target `nat-gateway-id`.
4. **Validation:**
   - Verify from an instance in the private subnet: `curl -I https://amazon.com`.
</details>

<details>
<summary><strong>↳ Follow-up: Should a NAT Gateway be placed in a public subnet or a private subnet?</strong></summary>

**Answer:**
**A NAT Gateway MUST be placed in a public subnet.**

- A NAT Gateway requires a two-way network bridge: it must translate private IP addresses to its allocated public Elastic IP (EIP) and route packets directly out through an **Internet Gateway (IGW)**.
- If placed in a private subnet, it would lack a direct route to an Internet Gateway and would be unable to reach the internet.
</details>

<details>
<summary><strong>↳ Follow-up: If the NAT Gateway is in the public subnet, how do you ensure it is properly connected to instances in the private subnet?</strong></summary>

**Answer:**
The connection is established via the **Private Subnet's Route Table**:

1. In the VPC network fabric, instances in the private subnet consult their associated Route Table for any packet destined outside their local CIDR (`10.0.0.0/16`).
2. By defining the default route entry `0.0.0.0/0` with the target set to the NAT Gateway's interface ID (`nat-xxxxxxxx`), AWS VPC software-defined routers automatically forward outbound internet-bound packets from the private subnet across the internal VPC network to the NAT Gateway in the public subnet.
3. Security Groups and NACLs must allow this internal routing without blocking outbound ephemeral ports.
</details>

<details>
<summary><strong>● How do you enable versioning on an S3 bucket in AWS?</strong></summary>

**Answer:**
Versioning can be enabled via multiple methods:

1. **AWS CLI:**
   ```bash
   aws s3api put-bucket-versioning \
     --bucket my-enterprise-bucket \
     --versioning-configuration Status=Enabled
   ```
2. **Terraform (Recommended):**
   ```hcl
   resource "aws_s3_bucket" "example" {
     bucket = "my-enterprise-bucket"
   }

   resource "aws_s3_bucket_versioning" "example_versioning" {
     bucket = aws_s3_bucket.example.id
     versioning_configuration {
       status = "Enabled"
     }
   }
   ```
3. **AWS Console:** S3 -> Select Bucket -> Properties tab -> Bucket Versioning -> Edit -> Select Enable -> Save changes.
</details>

<details>
<summary><strong>● Suppose you have a blogging website running on an EC2 instance and you want to set up an Application Load Balancer in front of it so that user traffic first hits the load balancer and then gets routed to the EC2 instance. What are the configuration steps to set up this Application Load Balancer?</strong></summary>

**Answer:**
Here are the end-to-end production configuration steps:

1. **Create Target Group:**
   - Target type: `Instances`.
   - Protocol: `HTTP`, Port: `80` (or `8080` based on web server).
   - VPC: Select target application VPC.
   - Health Check path: `/healthz` or `/` (HTTP 200 response).
   - Register the EC2 instance into this Target Group.
2. **Create Security Groups:**
   - **ALB Security Group:** Allow Inbound `80` (HTTP) and `443` (HTTPS) from `0.0.0.0/0`.
   - **EC2 Security Group:** Allow Inbound port `80` **only from the ALB Security Group ID** (`sg-alb-id`), preventing users from bypassing the load balancer.
3. **Create Application Load Balancer (ALB):**
   - Scheme: `Internet-facing`, IP address type: `IPv4`.
   - Network Mapping: Select VPC and choose at least **two public subnets across distinct Availability Zones**.
   - Attach the ALB Security Group.
4. **Configure Listeners & Routing Rules:**
   - **HTTP (Port 80):** Set rule to **Redirect HTTP to HTTPS** (301 Permanent Redirect).
   - **HTTPS (Port 443):** Attach ACM SSL/TLS Certificate. Set default action to **Forward to Target Group**.
5. **DNS Configuration:**
   - In Amazon Route 53, create an **Alias A Record** pointing `blog.company.com` to the ALB's DNS name.
</details>

<details>
<summary><strong>↳ Follow-up: In the context of an Application Load Balancer, what is the purpose of a target group and why is it used?</strong></summary>

**Answer:**
A **Target Group** serves as a logical decoupling abstraction between the Load Balancer listener rules and the backend workloads:

1. **Decoupling Routing from Compute:**
   - Listeners inspect incoming traffic (paths like `/api/*`, host headers like `app.com`) and forward requests to target groups, shielding routing logic from knowing individual server IPs.
2. **Continuous Health Checking:**
   - The Target Group executes active health probes against each registered target. If a target fails consecutive health checks, the ALB stops routing traffic to it automatically without terminating the instance.
3. **Diverse Target Types:**
   - A Target Group can register EC2 instances, private IP addresses (including on-premises servers over Direct Connect/VPN), AWS Lambda functions, and Amazon ECS microservice tasks.
4. **Advanced Traffic Controls:**
   - Supports connection draining (deregistration delay), slow-start duration for cache warming, and sticky sessions (cookie-based routing).
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** How many years of experience do you have working in DevOps?

↳ **Candidate Introduction:** Which company are you currently working at?

</details>
</details>

<details open>
<summary><h2>🏢 Vaisesika Consulting</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 LINUX 】

<details>
<summary><strong>● If you have an EC2 instance that you are unable to SSH into, and you don't know the reason, how would you debug this issue?</strong></summary>

**Answer:**
Troubleshooting an unreachable EC2 instance follows a structured layer-by-layer diagnostic methodology:

1. **Layer 1: AWS Console Status & System Checks:**
   - Check the **2/2 Status Checks** in the EC2 Console:
     - *System Status Check Failed:* Underlying AWS hypervisor hardware issue. Remediated by stopping and starting the instance to migrate to a healthy hypervisor.
     - *Instance Status Check Failed:* OS kernel panic, corrupt `/etc/fstab`, or misconfigured filesystem.
   - Inspect **Instance Screenshot** and **System Log (Console Output)** to observe kernel boot logs, grub errors, or filesystem fsck halts.

2. **Layer 2: Network & Routing Diagnostics:**
   - **Security Group:** Verify inbound rule allows TCP port 22 from your specific client public IP CIDR (`/32`), not blocked by port change.
   - **Network ACLs (NACL):** Ensure subnet NACL allows inbound TCP port 22 AND outbound ephemeral ports (1024–65535).
   - **Route Table:** If the instance is in a public subnet, verify a default route exists to an Internet Gateway (`0.0.0.0/0 -> igw-xxx`). If private, verify connectivity via VPN/Direct Connect or AWS Transit Gateway.
   - Test connectivity: `nc -zv -w3 <instance_ip> 22` or `curl -v telnet://<instance_ip>:22`.

3. **Layer 3: Authentication & SSH Client Configuration:**
   - Run SSH in verbose debug mode: `ssh -vvv -i key.pem ec2-user@<instance_ip>`.
   - Verify correct default username for the AMI (`ec2-user`, `ubuntu`, `centos`, `admin`).
   - Check local key file permissions: `chmod 400 key.pem` (OpenSSH rejects keys that are world-readable).

4. **Layer 4: Alternative Out-of-Band Access & Disk Rescue:**
   - **AWS Systems Manager (SSM) Session Manager:** If the SSM agent is active and an instance profile is attached, connect directly via browser or AWS CLI (`aws ssm start-session --target <instance-id>`), bypassing SSH and security groups completely.
   - **EC2 Serial Console:** Connect directly to the serial port for interactive root emergency login.
   - **EBS Rescue Mount:** If credentials or `/etc/ssh/sshd_config` are corrupt: Stop instance -> Detach root EBS volume (`/dev/xvda`) -> Attach to a healthy temporary rescue EC2 instance -> Mount volume -> Inspect `/var/log/secure` or `/var/log/auth.log`, restore `authorized_keys`, fix permissions (`chmod 700 ~/.ssh`, `chmod 600 ~/.ssh/authorized_keys`) -> Unmount and reattach as root device to original instance.
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● Have you only worked with Jenkins for CI/CD, or do you also have experience with GitHub Actions?</strong></summary>

**Answer:**
I have worked extensively with both **Jenkins** and **GitHub Actions** in production environments:
- **Jenkins:** Utilized as an enterprise CI orchestrator deployed on Kubernetes clusters using Kubernetes agents (JWS pods). Implemented complex scripted and declarative multibranch pipelines, shared libraries (`vars/`), artifact promotion, and plugin governance.
- **GitHub Actions:** Our modern standard for microservices CI/CD. Designed reusable workflows (`workflow_call`), matrix builds for multi-version testing, composite actions, and OpenID Connect (OIDC) federation with AWS IAM, eliminating long-lived credentials.
</details>

<details>
<summary><strong>↳ Follow-up: Can you walk me through your CI/CD pipeline end-to-end?</strong></summary>

**Answer:**
Here is our end-to-end GitOps-based microservice delivery pipeline:

1. **Commit & Trigger:** Developer pushes a branch or opens a Pull Request to `main`. GitHub webhook triggers an ephemeral GitHub Actions runner / Jenkins agent.
2. **Security & Code Linting (Shift-Left):** Runs `gitleaks` for secret detection, followed by `mvn test` / `npm test` and **SonarQube** static code analysis with quality gate evaluation.
3. **Software Composition Analysis (SCA):** Scans third-party libraries for CVEs using **OWASP Dependency-Check** / Snyk.
4. **Container Build & Hardening:** Multi-stage Docker build produces a lean Distroless container image tagged with `${GITHUB_SHA}`. **Trivy** scans image layers for OS vulnerabilities.
5. **Registry Push:** Pushes validated image to Amazon ECR.
6. **GitOps Manifest Update:** Pipeline commits the updated image tag into the GitOps deployment repository (`deployment/values.yaml`).
7. **Continuous Delivery:** **Argo CD** detects the Git commit and performs an automated canary rollout to AWS EKS, running synthetic smoke tests before completing 100% traffic shift.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● What is your understanding of NGINX and API gateways, particularly in the context of Kubernetes?</strong></summary>

**Answer:**
In Kubernetes, **NGINX Ingress Controller** and **API Gateways** operate at Layer 7 (Application Layer) to manage ingress traffic, but serve different architectural purposes:

1. **NGINX Ingress Controller:**
   - Implements the Kubernetes Ingress API.
   - Responsible for reverse proxying, SSL/TLS termination, path-based routing (`/api/v1 -> service-a`), host-based routing (`app.domain.com`), and basic rate-limiting or basic authentication.
   - Highly performant and lightweight for cluster-level traffic routing.

2. **API Gateways (e.g., Kong, Envoy, Emissary-ingress, AWS API Gateway):**
   - Extends basic reverse proxying with **advanced API management capabilities**:
     - OAuth2 / OpenID Connect (OIDC) / JWT validation and token introspection at the edge.
     - Dynamic rate-limiting, quota management, and API consumer tiering.
     - Request/Response transformation (JSON to XML, header mutation).
     - Distributed tracing injection, advanced circuit breaking, and API developer portal integration.
</details>

<details>
<summary><strong>↳ Follow-up: Have you configured routing rules before, for example routing a frontend application's requests to an S3 bucket? How would you configure such a route?</strong></summary>

**Answer:**
Yes. There are two primary architectural patterns to route requests from an Ingress or NGINX to an S3 static bucket:

1. **Pattern 1: Kubernetes Ingress with ExternalName Service / Proxy-Pass:**
   - Define a Kubernetes `ExternalName` service pointing to the S3 bucket DNS endpoint:
     ```yaml
     apiVersion: v1
     kind: Service
     metadata:
       name: s3-frontend-svc
     spec:
       type: ExternalName
       externalName: my-frontend-bucket.s3-website.us-east-1.amazonaws.com
     ```
   - In the NGINX Ingress manifest, configure upstream proxy headers:
     ```yaml
     apiVersion: networking.k8s.io/v1
     kind: Ingress
     metadata:
       name: frontend-ingress
       annotations:
         nginx.ingress.kubernetes.io/upstream-vhost: "my-frontend-bucket.s3-website.us-east-1.amazonaws.com"
         nginx.ingress.kubernetes.io/backend-protocol: "HTTP"
     spec:
       rules:
       - host: app.example.com
         http:
           paths:
           - path: /
             pathType: Prefix
             backend:
               service:
                 name: s3-frontend-svc
                 port:
                   number: 80
     ```

2. **Pattern 2: CloudFront Edge Routing (Production Best Practice):**
   - For production, avoid proxying static S3 frontend assets through Kubernetes nodes.
   - Configure **Amazon CloudFront** with two Origins:
     - Origin 1: S3 Bucket (via Origin Access Control - OAC) for static frontend assets (`/*`).
     - Origin 2: Application Load Balancer / Kubernetes Ingress for API routes (`/api/*`).
   - CloudFront handles caching, SSL, and low-latency global delivery without consuming Kubernetes cluster compute bandwidth.
</details>

<details>
<summary><strong>↳ Follow-up: Are all your applications deployed in Kubernetes as microservices?</strong></summary>

**Answer:**
The majority of our modern digital and core business workloads are containerized microservices deployed on Amazon EKS. However, our overall enterprise landscape is hybrid:
- **Stateless Microservices:** Deployed on EKS as Kubernetes Deployments with Horizontal Pod Autoscaling (HPA).
- **Scheduled / Event-Driven Tasks:** Run as Kubernetes CronJobs or AWS Lambda serverless functions.
- **Relational Databases & Stateful Systems:** We deliberately host databases on **Amazon RDS Multi-AZ** (Aurora PostgreSQL) rather than running databases inside Kubernetes, leveraging AWS-managed automated patching, automated point-in-time snapshots, and hardware-level replication.
- **Legacy Monoliths:** A few legacy batch processing workloads remain on dedicated Amazon EC2 instances managed with Auto Scaling Groups.
</details>

<details>
<summary><strong>● What are some of the errors you have encountered while deploying applications in Kubernetes, and how did you debug and fix them?</strong></summary>

**Answer:**
Here are common production Kubernetes errors and the systematic diagnostic procedures used:

1. **`CrashLoopBackOff`:**
   - *Cause:* Application crash immediately after start (misconfigured environment variable, missing database secret, uncaught runtime exception).
   - *Debugging:* `kubectl logs <pod> --previous` to inspect fatal error before exit, followed by `kubectl describe pod <pod>` to view exit codes (`Exit Code 1` = app crash, `137` = SIGKILL/OOM).
   - *Fix:* Correct missing configuration in ConfigMap/Secret or adjust startup probes.

2. **`ImagePullBackOff` / `ErrImagePull`:**
   - *Cause:* Image tag does not exist, registry authentication failure, or private ECR IAM token expired.
   - *Debugging:* `kubectl describe pod <pod>` under `Events:`.
   - *Fix:* Verify image tag in Helm values, check `imagePullSecrets`, or ensure node IAM role has `ecr:GetAuthorizationToken` and `ecr:BatchGetImage`.

3. **`OOMKilled` (Exit Code 137):**
   - *Cause:* Container memory usage exceeded `resources.limits.memory`.
   - *Debugging:* `kubectl describe pod <pod>` shows `Last State: Terminated, Reason: OOMKilled`.
   - *Fix:* Profile JVM heap/native memory, increase memory limit, and adjust JVM flags (`-XX:MaxRAMPercentage=75.0`).

4. **`CreateContainerConfigError`:**
   - *Cause:* Referenced ConfigMap or Secret does not exist or has a typo in the key name.
   - *Fix:* Check events via `kubectl describe pod` and verify referenced secret exists in the same namespace.

5. **`Pending` Pods with `0/N nodes available`:**
   - *Cause:* Insufficient CPU/memory requests, unscheduled node taints, or persistent volume AZ mismatch.
   - *Fix:* Review resource requests, check node capacity with `kubectl top nodes`, or scale node groups via Cluster Autoscaler / Karpenter.
</details>

#### 【 IAC 】

<details>
<summary><strong>● How do you handle automation of your Terraform workflows — do you run Terraform manually, or do you have automation in place for it?</strong></summary>

**Answer:**
We **never execute Terraform manually from local developer laptops** for shared or production environments. All Terraform executions are fully automated using a GitOps / CI/CD pipeline model (using **Atlantis** or **GitHub Actions**):

1. **PR Speculative Execution:** When an engineer opens a Pull Request proposing infrastructure changes, the CI runner automatically executes `terraform fmt -check`, `tflint`, `checkov`, and `terraform plan`.
2. **Plan Visibility:** The generated plan output is automatically formatted and posted directly back to the PR comments for peer review.
3. **Automated State Lock & Apply:** Once the PR receives mandatory senior DevOps approvals and is merged into `main`, the CD pipeline runs `terraform apply` against the pre-generated plan binary, updating S3 remote state and releasing the DynamoDB lock.
</details>

<details>
<summary><strong>↳ Follow-up: Is your Terraform setup designed for a single AWS account, or do you use a centralized approach across multiple accounts?</strong></summary>

**Answer:**
We use a **Multi-Account Centralized Hub-and-Spoke Architecture** adhering to AWS Well-Architected and Control Tower best practices:

- **Management / Tooling Account (Hub):** Houses the centralized CI/CD runners (Jenkins/GitHub ARC) and shared artifact registries.
- **Workload Accounts (Spokes):** Distinct AWS accounts for `Dev`, `Stage`, and `Prod` workloads, plus dedicated accounts for `Log-Archive` and `Security-Core`.
- **Terraform Multi-Account Configuration:**
  - The pipeline in the Tooling Account assumes a dedicated cross-account role (`arn:aws:iam::<TARGET_ACCOUNT_ID>:role/TerraformExecutionRole`) using provider aliasing:
    ```hcl
    provider "aws" {
      alias  = "prod"
      region = "us-east-1"
      assume_role {
        role_arn = "arn:aws:iam::111122223333:role/TerraformExecutionRole"
      }
    }
    ```
  - This architecture isolates the blast radius: a compromised test environment or accidental apply can never touch production infrastructure.
</details>

<details>
<summary><strong>↳ Follow-up: In Terraform, what block would you use to run shell commands or execution commands within a module?</strong></summary>

**Answer:**
To run local shell or remote execution commands in Terraform, you use a **`provisioner` block** inside a resource, most commonly paired with a **`terraform_data`** (Terraform 1.4+) or **`null_resource`**:

1. **`local-exec` Provisioner (Executes on the machine running Terraform):**
   ```hcl
   resource "terraform_data" "run_ansible" {
     triggers_replace = [aws_instance.web.id]

     provisioner "local-exec" {
       command = "ansible-playbook -i ${aws_instance.web.public_ip}, playbook.yml"
       environment = {
         ENV = "production"
       }
     }
   }
   ```

2. **`remote-exec` Provisioner (Executes directly over SSH/WinRM on the provisioned instance):**
   ```hcl
   resource "aws_instance" "web" {
     ami           = "ami-0123456789"
     instance_type = "t3.medium"

     connection {
       type        = "ssh"
       user        = "ec2-user"
       private_key = file("~/.ssh/id_rsa")
       host        = self.public_ip
     }

     provisioner "remote-exec" {
       inline = [
         "sudo yum update -y",
         "sudo yum install -y docker",
         "sudo systemctl start docker"
       ]
     }
   }
   ```
*Production Best Practice Note:* Provisioners are considered a last resort in Terraform because they break idempotency and declare imperative steps. In enterprise cloud engineering, we prefer EC2 `user_data` scripts, cloud-init, AMI baking via HashiCorp Packer, or AWS Systems Manager.
</details>

<details>
<summary><strong>↳ Follow-up: How do you manage the Terraform state file?</strong></summary>

**Answer:**
We manage Terraform state files following strict enterprise durability and security practices:

1. **Remote Backend:** State is stored centrally in **Amazon S3**, partitioned by environment and module domain (`s3://tf-state-prod/vpc/terraform.tfstate`).
2. **State Locking:** **Amazon DynamoDB** table (`LockID` attribute) enforces atomic execution locks.
3. **Encryption & Access Control:** S3 bucket encrypted with AWS KMS customer-managed key. All public access blocked. Strict IAM bucket policy denying access to human users; only the automated CI/CD role can read/write state.
4. **Disaster Recovery:** S3 Bucket Versioning is permanently enabled to allow rollback if state is ever corrupted, combined with MFA Delete and S3 Cross-Region Replication (CRR).
</details>

<details>
<summary><strong>↳ Follow-up: Do you have any approval steps in your Terraform workflow (e.g., after the plan stage), or do you deploy resources directly without approval?</strong></summary>

**Answer:**
Yes, we strictly enforce manual approval gates:
- In lower environments (`dev`/`sandbox`), non-destructive plans can be set to auto-apply upon PR merge after passing automated linting and security scans.
- In staging and production environments, **no automated direct deployment is permitted**. The pipeline pauses after the `terraform plan` stage, publishing the plan output. A designated Lead DevOps Engineer or Infrastructure Approver must review the diff and sign off in the CI/CD UI (e.g., GitHub Environment Protection rules or Atlantis `atlantis apply` comment command) before `terraform apply` can execute.
</details>

<details>
<summary><strong>↳ Follow-up: Do you have an approval step specifically for production Terraform deployments?</strong></summary>

**Answer:**
Yes. For **production Terraform deployments**, we enforce a multi-party approval process:
1. **GitHub Environment Protection Rule:** Production environment deployments require mandatory sign-off from at least two authorized Senior DevOps / Principal Infrastructure leads.
2. **Change Advisory Board (CAB) Integration:** For major infrastructure changes (e.g., VPC peering, database resizing, or Kubernetes version upgrades), an approved Change Request (CR) ticket from Jira/ServiceNow must be referenced.
3. **Pinned Plan Execution:** The pipeline apply stage *only* executes the exact immutable binary plan (`tfplan.binary`) generated during the approved PR stage, ensuring zero out-of-band changes slip in between approval and execution.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● If you have an application hosted on an EC2 instance and you want to send or store its logs in an S3 bucket, what steps would you take to configure this connection between EC2 and S3?</strong></summary>

**Answer:**
Here are the complete production steps:

1. **Step 1: Create IAM Policy with Least Privilege:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["s3:PutObject", "s3:PutObjectAcl"],
         "Resource": "arn:aws:s3:::app-production-logs-bucket/*"
       }
     ]
   }
   ```
2. **Step 2: Create IAM Role and Instance Profile:**
   - Create an IAM Role with `ec2.amazonaws.com` trust policy and attach the above IAM policy.
   - Attach the IAM Instance Profile to the running EC2 instance (`aws ec2 associate-iam-instance-profile`).
3. **Step 3: Log Shipping Agent Configuration:**
   - Rather than custom shell cron scripts, install and configure the **Amazon CloudWatch Unified Agent** or **Fluent Bit** on the EC2 instance.
   - Configure the agent to tail application log files (e.g., `/var/log/app/*.log`) and ship them directly to CloudWatch Logs or flush them periodically to S3.
4. **Step 4: Enable S3 VPC Gateway Endpoint:**
   - To keep log traffic entirely on the private AWS network without egressing through the internet or NAT Gateway (saving bandwidth costs).
</details>

<details>
<summary><strong>↳ Follow-up: Is attaching an IAM role alone sufficient, or what mechanism enables service-to-service connectivity between AWS services like EC2 and S3?</strong></summary>

**Answer:**
Attaching an IAM role provides **identity and authorization (AuthZ)**, but **network routing and transport connectivity** are also required:

1. **Authorization Layer:** The IAM role and S3 Bucket Policy grant API permissions.
2. **Network Transport Layer:** The EC2 instance must have a valid IP route to reach Amazon S3's public or private endpoints:
   - *Option A (Private & Free - Best Practice):* Configure an **AWS S3 VPC Gateway Endpoint**. Add a prefix-list route entry in the VPC route table (`pl-xxxx -> vpce-xxxx`). All traffic to S3 flows directly across the internal AWS backbone with zero NAT Gateway data transfer charges and zero internet exposure.
   - *Option B (Internet Route):* If no VPC endpoint exists, the EC2 instance must have a route to an Internet Gateway (if in a public subnet) or a NAT Gateway (if in a private subnet) to reach `s3.amazonaws.com` over public HTTPS (port 443).
3. **Security Group & NACL:** Egress rules must allow outbound HTTPS (TCP port 443).
</details>

<details>
<summary><strong>● For a hosted application such as an e-commerce application, how would you handle a sudden traffic spike using AWS services?</strong></summary>

**Answer:**
Handling traffic spikes requires a multi-layered auto-scaling and caching architecture:

1. **Edge Layer (Offloading Traffic):**
   - Place **Amazon CloudFront** CDN in front of the application with optimized TTLs to cache static assets (HTML/CSS/JS, product images) at edge locations, offloading up to 80% of requests from origin servers.
2. **DNS & Load Balancing:**
   - Distribute incoming traffic across multi-AZ backend compute using an **Application Load Balancer (ALB)** configured with connection multiplexing and HTTP/2.
3. **Elastic Compute Scaling:**
   - Configure an **EC2 Auto Scaling Group (ASG)** with **Target Tracking Scaling Policies** (e.g., maintain average CPU utilization at 60% or ALB `RequestCountPerTarget` at 1,000 requests/minute).
   - Configure **Predictive Scaling** based on historical machine learning patterns for planned flash sales (e.g., Black Friday).
4. **Application Caching:**
   - Deploy **Amazon ElastiCache for Redis** cluster in front of databases to cache popular catalog items and session tokens.
5. **Database Layer Protection:**
   - Use **Amazon Aurora PostgreSQL/MySQL** with **Aurora Auto Scaling Read Replicas** to absorb read spikes.
   - Deploy **Amazon RDS Proxy** to manage and pool thousands of concurrent database connections, preventing DB connection exhaustion.
</details>

<details>
<summary><strong>● If an S3 bucket gets deleted, would you be able to recover it, and how?</strong></summary>

**Answer:**
1. **If the S3 Bucket itself was completely deleted:**
   - **No, an S3 bucket cannot be recovered once deleted.** AWS permanently purges bucket metadata. If the bucket was deleted, the bucket name immediately becomes available to anyone on the internet, and all non-replicated data is permanently unrecoverable.

2. **How to protect and prepare for recovery beforehand:**
   - **S3 Object Versioning & MFA Delete:** Requires hardware MFA tokens to permanently delete versioned objects.
   - **S3 Cross-Region Replication (CRR):** Replicates all objects automatically to a destination bucket in a separate AWS region under a different AWS account (with ownership override).
   - **AWS Backup for S3:** Automated continuous point-in-time backups and periodic snapshots managed independently of the primary bucket.
   - **S3 Object Lock (WORM):** Enforces compliance retention policies preventing object deletion for a specified retention period (e.g., 7 years).
   - **Terraform Lifecycle Rule:** Set `prevent_destroy = true` on the S3 bucket resource to block accidental Terraform deletion.
</details>

↳ **Candidate Introduction:** How many AWS accounts does your team manage?

#### 【 MONITORING 】

<details>
<summary><strong>● Regarding monitoring, have you ever configured alerts yourself, or have you only used monitoring tools to observe the system?</strong></summary>

**Answer:**
I have hands-on experience designing, provisioning, and tuning alerts end-to-end:
- Configured alerting rules in **Prometheus** (`AlertmanagerConfig` and `PrometheusRule` Custom Resources) and **Datadog / CloudWatch**.
- Defined metric thresholds, evaluated error rate percentages (SLI/SLO burn rates), configured multi-channel notification routing (PagerDuty for P1/P2 incidents, Slack for P3/warnings), and authored runbooks linked directly to alert annotations to streamline on-call remediation.
</details>

<details>
<summary><strong>↳ Follow-up: Do you have an understanding of how Prometheus and Grafana monitoring is configured, even if you haven't set it up yourself?</strong></summary>

**Answer:**
Yes. The standard architecture operates as follows:

```
[ Pod / Service (/metrics) ] <──(Pulls/Scrapes)── [ Prometheus Server ]
                                                        │
                         ┌──────────────────────────────┴──────────────────────────────┐
                         v                                                             v
                 [ Grafana UI ]                                              [ Alertmanager ]
             (PromQL Dashboards)                                          (PagerDuty / Slack)
```

1. **Prometheus Scraping Architecture:**
   - Prometheus operates on a **pull model**, polling target HTTP endpoints (e.g., `/metrics` in OpenMetrics/Prometheus format) at defined scrape intervals (e.g., 15s).
   - In Kubernetes, targets are discovered dynamically using **`ServiceMonitor`** or **`PodMonitor`** CRDs managed by the **kube-prometheus-stack** operator.
2. **Grafana Data Visualization:**
   - Configured with Prometheus as an active Datasource.
   - Dashboards are authored in JSON or provisioned via ConfigMaps using PromQL queries (e.g., `rate(container_cpu_usage_seconds_total[5m])`).
</details>

<details>
<summary><strong>↳ Follow-up: What metrics or monitors are configured in your Grafana dashboard?</strong></summary>

**Answer:**
Our production dashboards adhere to the **Google SRE "Four Golden Signals"** (Latency, Traffic, Errors, Saturation) and the **USE Method** (Utilization, Saturation, Errors):

1. **Cluster & Node Infrastructure Health:**
   - Node CPU utilization, RAM usage (`node_memory_MemAvailable_bytes`), disk I/O saturation, and node filesystem capacity (`node_filesystem_free_bytes`).
2. **Kubernetes Workload Level:**
   - Pod restart counts (`kube_pod_container_status_restarts_total`), pods in non-running states (CrashLoopBackOff, Pending), HPA replica targets vs actual, and CPU/Memory limits vs requests.
3. **Application & Service Level (HTTP/gRPC):**
   - **Traffic / Throughput:** Request rate (RPS) via `sum(rate(http_requests_total[2m])) by (service)`.
   - **Latency:** p50, p95, and p99 latency percentiles via `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`.
   - **Error Rates:** HTTP 5xx and 4xx status response rates.
   - **JVM Telemetry (for Java apps):** JVM Heap used vs max, GC pause duration, and active thread pool count.
</details>

<details>
<summary><strong>↳ Follow-up: How is the alerting part of your monitoring setup configured?</strong></summary>

**Answer:**
The alerting pipeline is configured via **Prometheus Alertmanager**:

1. **Rule Definition (`PrometheusRule` CRD):**
   - Define alert expression, duration threshold (`for: 5m`), severity labels (`critical`, `warning`), and annotations (summary, description, runbook URL):
     ```yaml
     apiVersion: monitoring.coreos.com/v1
     kind: PrometheusRule
     metadata:
       name: api-alerts
     spec:
       groups:
       - name: payment-api
         rules:
         - alert: HighHttp5xxRate
           expr: sum(rate(http_requests_total{status=~"5.."}[2m])) / sum(rate(http_requests_total[2m])) > 0.05
           for: 3m
           labels:
             severity: critical
           annotations:
             summary: "Payment API 5xx rate > 5%"
             runbook_url: "https://wiki.internal/runbooks/payment-5xx"
     ```
2. **Alertmanager Routing & Deduplication:**
   - Alertmanager groups matching alerts by cluster and namespace to prevent alert floods.
   - Routes alerts based on severity:
     - `severity: critical` -> Triggers **PagerDuty** on-call phone paging and incident creation.
     - `severity: warning` -> Posts to dedicated Slack channel (`#ops-alerts`).
   - Implements **Inhibition Rules** (e.g., if a Node is reported Down, mute all individual pod alerts on that node).
</details>

#### 【 SECURITY 】

<details>
<summary><strong>↳ Follow-up: With respect to security, what configurations would you put in place for these APIs?</strong></summary>

**Answer:**
Securing production APIs involves a defense-in-depth model across the network, transport, application, and identity tiers:

1. **Transport & Network Encryption:**
   - Enforce **HTTPS with TLS 1.3** (or 1.2 minimum). Disable weak SSL ciphers. Enforce HTTP Strict Transport Security (HSTS).
   - Restrict public ingress using an **AWS WAF (Web Application Firewall)** attached to the ALB or API Gateway.
2. **Identity & Access Management (OAuth2/OIDC/JWT):**
   - Require cryptographically signed JWT tokens for every request. Verify signature, expiry (`exp`), issuer (`iss`), and audience (`aud`) at the API Gateway before traffic reaches backend microservices.
3. **CORS & Security Headers:**
   - Restrict Cross-Origin Resource Sharing (CORS) strictly to authorized company web domains; never allow wildcard `Access-Control-Allow-Origin: *` for authenticated APIs.
   - Inject security headers: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy`.
</details>

<details>
<summary><strong>↳ Follow-up: Specifically regarding API security in AWS, how would you secure an API against issues like excessive hits, for example by implementing rate limiting?</strong></summary>

**Answer:**
In AWS, rate limiting and DDoS protection are implemented across two complementary tiers:

1. **Amazon API Gateway Usage Plans & Throttling:**
   - Configure **Usage Plans** with **API Keys**:
     - **Throttling (Token Bucket Algorithm):** Set a steady-state request rate (e.g., 500 requests/second) and burst capacity (e.g., 1,000 requests).
     - **Quotas:** Set overall volumetric caps (e.g., 50,000 requests per day per API client).
   - If a client exceeds the threshold, API Gateway automatically responds with `HTTP 429 Too Many Requests` at the AWS edge without burdening backend compute.

2. **AWS WAF (Web Application Firewall) Rate-Based Rules:**
   - Attach AWS WAF to the Application Load Balancer or API Gateway.
   - Create a **Rate-based Rule Statement**:
     - Evaluates requests in 5-minute sliding windows.
     - Limit: E.g., block or CAPTCHA any single client IP address exceeding 1,000 requests in a 5-minute window.
   - Combine with **AWS Shield Standard/Advanced** for automated Layer 3/4/7 DDoS mitigation and AWS Managed Rules (Core Rule Set, Known Bad Inputs).
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● If an API is running slow in production, what steps would you take to debug and troubleshoot the performance issue?</strong></summary>

**Answer:**
Troubleshooting high latency in production follows a systematic data-driven workflow:

1. **Quantify the Issue & Establish Scope:**
   - Inspect APM telemetry (Datadog, AWS X-Ray, New Relic): Is latency elevated for *all* API endpoints or *one specific endpoint*? Are all users affected or only users in a specific region?
   - Compare p50, p95, and p99 latency graphs to determine if latency is systemic or driven by tail-latency outliers.

2. **Analyze Distributed Tracing (Span Breakdown):**
   - Check trace flame graphs to identify where request time is spent:
     - **Database Query Time:** Slow SQL queries, unindexed queries, table locks, connection pool exhaustion.
     - **Downstream Third-Party Calls:** Slow external payment gateway or partner REST API without configured timeouts.
     - **Compute / CPU Bound:** Inefficient deserialization, regular expression backtracking, or synchronous cryptographic operations.

3. **Inspect Infrastructure Saturation:**
   - **Pod / Container Metrics:** Check if pods are being CPU throttled (`container_cpu_cfs_throttled_periods_total`) due to strict Kubernetes CPU limits.
   - **JVM Metrics:** Check for JVM garbage collection pauses (Stop-The-World GC events) or thread contention.
   - **Database Host:** Inspect RDS CPU utilization, Read/Write IOPS, disk queue depth, and active connection pool count.

4. **Remediation Actions:**
   - Increase replica count or trigger horizontal scaling.
   - Add database read replicas or optimize slow queries with indexes (`EXPLAIN ANALYZE`).
   - Implement caching (Redis) for read-heavy hotspots.
   - Tune Kubernetes resource limits and JVM garbage collection parameters (`-XX:+UseG1GC`).
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself, including the tool stacks you have experience with and your overall experience journey as a DevOps engineer?

↳ **Candidate Introduction:** How many product/developer teams do you work with?

<details>
<summary><strong>● As a DevOps team member, do you provide any frontline or on-call support for production issues?</strong></summary>

**Answer:**
Yes. In our organization, we follow the "You build it, you run it" collaborative culture where the DevOps/Platform team shares on-call operational responsibilities with software engineering teams:
- We participate in a weekly **PagerDuty on-call rotation** as Tier-2 infrastructure and deployment escalation engineers.
- Our primary role during an active incident is rapid triage: isolating whether the failure is an infrastructure issue (cluster networking, cloud provider outage, node failure, certificate expiry) or application code regression.
- We facilitate bridge calls, coordinate automated rollbacks if an incident coincides with a release, and lead blameless post-mortem investigations following resolution.
</details>

<details>
<summary><strong>↳ Follow-up: Beyond automated pipeline rollback, how does your team prioritize and handle recurring production or deployment issues during weekends, off-hours, or work hours?</strong></summary>

**Answer:**
Handling recurring issues follows a disciplined Site Reliability Engineering (SRE) approach:

1. **Incident Severity Triaging (P1 to P4):**
   - **P1/P2 (Off-hours / Weekends):** Direct customer impact triggers high-urgency PagerDuty alerts. The on-call engineer engages immediately (15-minute SLA). The immediate priority is **restoring service** (failover, restarting pods, rolling back, or scaling up), not debugging root cause in production.
2. **Blameless Post-Mortem & Action Items:**
   - Following resolution, we hold a blameless post-mortem within 48 hours to identify root cause using the "5 Whys" methodology.
   - Action items are created with high priority in Jira: improving automated health checks, fixing resource leaks, or updating runbooks.
3. **Eliminating Operational Toil:**
   - If an issue recurs twice, it is treated as technical debt. We allocate 20% of sprint capacity to engineer permanent automated remedies (e.g., self-healing cron scripts, tuning HPA metrics, or rewriting flakey tests).
</details>

<details>
<summary><strong>↳ Follow-up: Does your organization have a separate SRE team responsible for handling on-call and production incident response?</strong></summary>

**Answer:**
In our organization, we operate a hybrid model:
- We have a dedicated **Core SRE team** focused on organization-wide observability platforms, SLA/SLO definition, error budget policies, and major cross-department disaster recovery drills.
- However, for day-to-day services, our **DevOps / Platform engineers** work directly alongside embedded product squads. This prevents the traditional anti-pattern of throwing code over the wall to a detached operations team and ensures that developers and DevOps engineers retain shared ownership of operational reliability and deployment pipelines.
</details>

#### 【 OTHER 】

<details>
<summary><strong>↳ Follow-up: Apart from shell scripting, have you used any other programming or scripting languages?</strong></summary>

**Answer:**
Yes. In addition to Bash/Shell scripting:
- **Python:** My primary language for complex automation tasks: writing AWS Boto3 automation scripts, interacting with REST APIs, parsing dynamic JSON/YAML payloads, authoring custom Kubernetes admission webhooks, and writing AWS Lambda functions.
- **Go (Golang):** Used for understanding and contributing to Kubernetes operators, writing custom Terraform providers, and reading open-source CNCF codebases.
- **Groovy:** Used extensively for authoring custom Jenkins Shared Libraries and declarative pipeline scripting.
</details>

<details>
<summary><strong>↳ Follow-up: Do you understand Python well enough to read and comprehend an automation script written in Python?</strong></summary>

**Answer:**
**Yes, absolutely.** I regularly read, write, and maintain production Python scripts:
- Comfortable working with standard data structures (lists, dictionaries, sets), list comprehensions, exception handling (`try-except-finally`), and object-oriented design.
- Extensive experience with popular DevOps libraries: `boto3` (AWS SDK), `requests` (REST API client), `kubernetes` (Python client for K8s API), `pyyaml`, and `pytest` for unit testing automation logic.
</details>

<details>
<summary><strong>● Do you have experience with any other tools or technology stacks beyond what you've already mentioned, such as Airflow?</strong></summary>

**Answer:**
Yes. Beyond the standard CI/CD and cloud toolchain, I have operational experience with data and automation platforms:
- **Apache Airflow:** Deployed and operated Apache Airflow on Amazon EKS using the official Helm Chart with the `CeleryExecutor` and `KubernetesExecutor`. Configured Airflow connections to AWS Secrets Manager, tuned worker pod resource requests, and assisted data engineering teams with CI/CD pipelines to validate and sync Airflow DAGs from Git to S3 / persistent volumes.
- **HashiCorp Vault:** For centralized secret management and dynamic credentials injection.
- **Ansible:** For configuration management, server hardening (CIS benchmark compliance), and base VM provisioning.
</details>

</details>
</details>

<details open>
<summary><h2>🏢 Devon</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 LINUX 】

<details>
<summary><strong>● What is the difference between a soft link and a hard link in Linux?</strong></summary>

**Answer:**
In Linux filesystems, links provide multiple directory references to files, but differ fundamentally in how they interact with filesystem inodes:

| Feature | Soft Link (Symbolic Link / Symlink) | Hard Link |
|---|---|---|
| **Command** | `ln -s target.txt link.txt` | `ln target.txt link.txt` |
| **Inode** | Has its **own unique inode number**; contents point to target file path. | Shares the **exact same inode number** as the target file. |
| **Cross-Filesystem** | **Yes**, can span across different partitions, disks, or NFS mounts. | **No**, restricted strictly to the same physical filesystem / partition. |
| **Target Deletion** | Becomes a **dangling/broken link** pointing to a non-existent path. | Data remains **fully intact and accessible** until all hard links (link count = 0) are removed. |
| **Directory Linking** | Supported. | Prohibited (prevents infinite directory recursion loops). |
| **Size** | Size equals length of target pathname string. | Reflects actual size of the shared data blocks on disk. |
</details>

<details>
<summary><strong>↳ Follow-up: In what scenarios would you prefer using a soft link over a hard link in Linux?</strong></summary>

**Answer:**
Soft links are preferred in several standard system administration and DevOps scenarios:

1. **Cross-Partition / Mount Point Linking:** When pointing to files or directories on separate mounted EBS volumes or NFS shares (e.g., linking `/var/log/app` to `/mnt/ebs_volume/logs`).
2. **Directory Symlinking:** When creating convenient directory aliases (e.g., linking `/opt/java/current` -> `/opt/java/jdk-17.0.8`).
3. **Application Version Switching & Zero-Downtime Rollbacks:** Standard deployment pattern (used by Capistrano/Nginx) where `/var/www/current` is an atomic symlink pointing to `/var/www/releases/20260910/`. Switching versions is an atomic `ln -sfn` pointer update.
4. **Shared Library Versioning:** Linux `/usr/lib64/libssl.so` symlinks pointing to major versioned binaries like `libssl.so.1.1`.
</details>

<details>
<summary><strong>● Can you list some common Linux networking commands used for troubleshooting connectivity issues?</strong></summary>

**Answer:**
Essential Linux networking diagnostic utilities categorized by troubleshooting layer:

1. **Layer 3/4 Connectivity & Port Verification:**
   - `ping <ip/host>`: Tests ICMP reachability and network round-trip latency.
   - `traceroute` / `tracepath` / `mtr <host>`: Traces network hop latency and identifies upstream routing packet loss.
   - `nc -zv -w3 <host> <port>` (Netcat) / `telnet <host> <port>`: Confirms TCP handshake and verifies firewall / security group openness on a specific port.
   - `curl -Iv https://<endpoint>`: Validates HTTP/S status, TLS certificate negotiation, and response headers.

2. **Local Socket & Listening Ports:**
   - `ss -tulpn` (modern replacement for `netstat -tulpn`): Displays active TCP/UDP listening sockets, process IDs (PIDs), and port bindings.
   - `lsof -i :<port>`: Identifies which running process is bound to a specific network port.

3. **DNS Resolution Diagnostics:**
   - `dig +trace <domain>`: Performs hierarchical DNS resolution tracking root nameservers.
   - `nslookup <domain>` / `host <domain>`: Quick query to the locally configured resolver (`/etc/resolv.conf`).

4. **Interface & Routing Tables:**
   - `ip addr show` (replaces `ifconfig`): Lists network interfaces, MAC addresses, and assigned IP CIDRs.
   - `ip route show` (replaces `route -n`): Displays the kernel routing table and default gateway.
   - `tcpdump -i eth0 -nn port 443`: Deep packet inspection to analyze raw network traffic frames during active connectivity failures.
</details>

#### 【 GIT 】

<details>
<summary><strong>● What is the exact difference between git merge and git rebase?</strong></summary>

**Answer:**
Both commands integrate changes from one branch into another, but they treat commit history fundamentally differently:

```
Initial:
      A---B---C (main)
           \
            D---E (feature)

git merge feature (into main):
      A---B---C-------M (main)  <-- New 2-parent merge commit created
           \         /
            D-------E

git rebase main (from feature):
      A---B---C---D'---E' (feature)  <-- Commits replayed linearly with new hashes
```

1. **`git merge`:**
   - **Mechanism:** Creates a new **Merge Commit** with two parent commits, joining the histories together.
   - **History Preservation:** Non-destructive; completely preserves the exact historical timeline, branch existence, and chronological commit order.
   - **Use Case:** Merging feature branches into protected long-lived branches (`main`, `develop`) via Pull Requests to maintain complete auditability.

2. **`git rebase`:**
   - **Mechanism:** Rewrites project history by lifting commits from the feature branch and replaying them one-by-one onto the tip of the target branch, generating **brand-new commit hashes** (`D'`, `E'`).
   - **History Shape:** Produces a clean, perfectly linear Git history without cluttering merge commits.
   - **Use Case:** Keeping local feature branches up-to-date with `main` before opening a Pull Request.
</details>

<details>
<summary><strong>● What is git cherry-pick, and when would you use it?</strong></summary>

**Answer:**
**`git cherry-pick <commit-hash>`** applies the exact diff introduced by a specific commit from one branch onto the currently checked-out branch as a brand-new commit.

- **Primary Use Cases:**
  1. **Production Hotfix Backporting:** A critical bug fix is committed and tested on `main`. You need to apply *only that single bug fix* to an active production release branch (`release/v2.1`) without pulling in unrelated unstable features currently in development.
  2. **Accidental Branch Commits:** A developer accidentally commits code to the wrong branch. Cherry-picking applies it to the intended branch before resetting the incorrect branch.
  3. **Salvaging Code from Abandoned Branches:** Extracting an isolated feature or utility function from a discontinued experimental branch.
</details>

<details>
<summary><strong>↳ Follow-up: Is git cherry-pick generally considered safe or recommended to use?</strong></summary>

**Answer:**
While powerful, `git cherry-pick` is considered a **tactical utility that must be used with caution**:

- **Why it can be risky:**
  - **Duplicate Commits:** Cherry-picking copies the diff but generates a **new commit hash**. When the source branch is eventually merged into the target branch later, Git can encounter duplicate commits or confusing merge conflicts.
  - **Missing Context / Dependencies:** If the cherry-picked commit depends on changes made in preceding commits that were not cherry-picked, it can introduce subtle compile errors or runtime bugs.
- **Best Practice Recommendation:** Use cherry-pick primarily for emergency hotfixes to release branches. For regular feature development, prefer standard feature branching, rebasing, and Pull Request merges.
</details>

<details>
<summary><strong>↳ Follow-up: Have you personally used git cherry-pick in a real production scenario?</strong></summary>

**Answer:**
Yes. In a recent production release cycle:
- Our team was maintaining a live release branch (`release/v3.4.0`) in UAT while active development continued on `develop`.
- A critical security vulnerability (JWT token validation defect) was discovered and resolved on `develop` under commit `a1b2c3d`.
- To patch the production release immediately without bringing in 15+ newly merged features from `develop` that were not yet QA certified, I checked out `release/v3.4.0` and ran:
  ```bash
  git checkout release/v3.4.0
  git cherry-pick -x a1b2c3d
  ```
  *(The `-x` flag automatically appends `(cherry picked from commit ...)` to the commit message for traceability).*
- The hotfix was tested, tagged as `v3.4.1`, and deployed directly to production with zero unintended code leakage.
</details>

<details>
<summary><strong>↳ Follow-up: What happens to commit parent IDs/hashes during a git rebase versus a git merge?</strong></summary>

**Answer:**
- **During `git merge`:**
  - Existing commits on both branches **keep their original commit hashes and parent pointers unchanged**.
  - A single new **Merge Commit** is created whose commit object contains **two parent IDs**: Parent 1 pointing to the HEAD of the target branch, and Parent 2 pointing to the tip of the merged branch.
- **During `git rebase`:**
  - The original commits on the feature branch are discarded (eventually cleaned up by git garbage collection).
  - Git creates **entirely new commit objects with new SHA-1/SHA-256 hashes**.
  - Each rebased commit's **Parent ID is updated** to point sequentially to the commit preceding it in the newly constructed linear chain.
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● Between Jenkins and GitHub Actions, which CI/CD tool are you more comfortable working with?</strong></summary>

**Answer:**
I am highly comfortable with both, but leverage each according to project architecture:
- **GitHub Actions:** Preferred for modern microservices and cloud-native repositories due to native GitHub integration, zero control plane maintenance, ephemeral secure runners, OIDC AWS authentication, and reusable workflows.
- **Jenkins:** Preferred in large enterprise environments with complex legacy build topologies, custom hardware agent pools, complex enterprise LDAP/Active Directory authorization matrices, or long-running orchestrations spanning multiple heterogeneous platforms.
</details>

<details>
<summary><strong>↳ Follow-up: Have you personally written any workflows in GitHub Actions?</strong></summary>

**Answer:**
Yes. I have authored numerous production workflows, including:
- **Matrix Build Workflows:** Testing Node.js/Python microservices across multiple runtime versions and OS environments.
- **Reusable Workflows (`workflow_call`):** Centralized templates enforcing SonarQube quality gates, Trivy container scanning, and ECR publishing across organization repositories.
- **OIDC AWS Deployments:** Workflows deploying Helm charts to Amazon EKS using temporary AWS STS credentials assumed via OpenID Connect.
</details>

<details>
<summary><strong>● What is the difference between a scripted pipeline and a declarative pipeline in Jenkins?</strong></summary>

**Answer:**
| Feature | Declarative Pipeline | Scripted Pipeline |
|---|---|---|
| **Root Syntax** | `pipeline { ... }` | `node { ... }` |
| **Philosophy** | Opinionated, structured, declarative schema. | Imperative Groovy scripting logic. |
| **Extensibility** | Uses predefined sections (`agent`, `stages`, `steps`, `post`). Custom Groovy requires a `script { ... }` block. | Full access to unrestricted Groovy language constructs (loops, conditionals, exception handlers). |
| **Error Checking** | Validates syntax before pipeline starts executing. | Evaluates line-by-line at runtime; syntax errors cause mid-execution halts. |
| **Blue Ocean UI** | Native visualization support for parallel stages and steps. | Limited visual stage rendering in Blue Ocean. |
| **Recommendation** | **Standard best practice** for 95% of enterprise pipelines. | Reserved for legacy systems or extraordinarily complex dynamic build trees. |
</details>

<details>
<summary><strong>↳ Follow-up: Which type of Jenkins pipeline (scripted or declarative) do you use in your current organization?</strong></summary>

**Answer:**
We standardize strictly on **Declarative Pipelines** across all our application repositories:
- Ensures uniform structure across development teams (`pipeline -> stages -> stage -> steps -> post`).
- Enables automated linting via Jenkins CLI (`jenkins-cli declarative-linter`).
- When advanced programmatic logic is required (e.g., dynamic map iteration or custom error handling), we encapsulate that logic into tested **Jenkins Shared Libraries** (`vars/customDeploy.groovy`) or scoped `script {}` blocks, keeping the primary `Jenkinsfile` clean and maintainable.
</details>

<details>
<summary><strong>● If a Jenkins build works on the controller but fails on a specific agent, what would you check to troubleshoot this?</strong></summary>

**Answer:**
When a build passes on the controller but fails on a specific agent, the issue is almost invariably an **environmental divergence or permission mismatch**:

1. **Tooling & Runtime Versions:**
   - Verify installed versions of compilers/runtimes on the agent (`java -version`, `mvn -version`, `node -v`, `docker -v`). Verify the agent's `PATH` and `JAVA_HOME` match the controller.
2. **User Identity & Filesystem Permissions:**
   - Check which system user runs the Jenkins agent daemon (`whoami`).
   - Check permissions on the workspace directory: `ls -ld /home/jenkins/workspace`.
   - Verify Docker socket permissions: Can the `jenkins` user execute `docker ps` without permission denied (`/var/run/docker.sock` group permissions)?
3. **Agent Resource Saturation:**
   - Check available disk space (`df -h` on agent). A full `/tmp` or Docker layer cache causes builds to fail silently.
   - Check memory and OOM killer logs: `dmesg -T | grep -i oom`.
4. **Network & Firewall Restrictions:**
   - If the agent is in a different VPC/subnet, verify it has outbound routing to internal Nexus/Artifactory repositories, SonarQube, and the internet.
5. **Environment Variables & Secrets:**
   - Check if required environment variables or tool locations (`Tool Location` in Jenkins node settings) are configured properly for that specific agent node.
</details>

<details>
<summary><strong>● Have you had the opportunity to work with GitOps practices/tools?</strong></summary>

**Answer:**
Yes. I have implemented and operated **GitOps workflows** for continuous delivery using **Argo CD** and **Helm** on Amazon EKS:
- **Git as Single Source of Truth:** Cluster state, Helm charts, and environment overlays are version-controlled in Git.
- **Automated Pull-Based Synchronization:** Rather than pushing changes from CI pipelines via `kubectl`, Argo CD runs inside the cluster, detects changes in Git, and reconciles the cluster state automatically.
- **Drift Detection & Auto-Healing:** If someone makes manual changes in the cluster (e.g., editing a deployment replica count via `kubectl edit`), Argo CD detects the divergence and automatically rolls it back to match Git.
</details>

<details>
<summary><strong>↳ Follow-up: Have you worked with tools like Argo CD or Helm?</strong></summary>

**Answer:**
Yes, both tools form the backbone of our Kubernetes application management:
- **Helm:** Used to package microservices into standardized, reusable charts (`Chart.yaml`, `values.yaml`, `templates/`). We manage environment-specific configurations via overlay value files (`values-dev.yaml`, `values-prod.yaml`).
- **Argo CD:** Configured with the **App-of-Apps pattern** and **ApplicationSets** to automatically discover and deploy Helm charts across multiple Kubernetes clusters and namespaces based on Git repository directory structures.
</details>

<details>
<summary><strong>↳ Follow-up: Do you have any knowledge or experience with Argo CD?</strong></summary>

**Answer:**
Yes, extensive hands-on operational experience with Argo CD:
- Deploying the Argo CD control plane (`argocd-server`, `argocd-repo-server`, `argocd-application-controller`) via Helm.
- Configuring **SSO Integration** with Okta / GitHub OAuth via Dex.
- Implementing **Sync Policies**: Automated synchronization with `prune: true` (garbage collecting deleted resources) and `selfHeal: true`.
- Implementing **Sync Waves** and **Resource Hooks** (`PreSync`, `PostSync`) to run database migration jobs before updating application deployment pods.
- Integrating with **Argo Rollouts** for Canary and Blue-Green progressive traffic management.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● What is the difference between a Deployment and a StatefulSet in Kubernetes?</strong></summary>

**Answer:**
| Feature | Deployment | StatefulSet |
|---|---|---|
| **Workload Target** | **Stateless applications** (web apps, APIs, microservices). | **Stateful applications** (databases, Kafka, Elasticsearch, ZooKeeper). |
| **Pod Identity** | Pods are fungible, interchangeable, and have **random hash names** (`web-7d8b59d-abc12`). | Pods have **stable, persistent, ordinal identities** (`kafka-0`, `kafka-1`, `kafka-2`). |
| **Network Identity** | Single shared ClusterIP Service; pods do not have dedicated hostnames. | Requires a **Headless Service** (`clusterIP: None`); each pod gets a deterministic DNS record (`pod-0.headless-svc.namespace.svc.cluster.local`). |
| **Storage Binding** | Pods share PVCs or use ephemeral storage. | Uses **`volumeClaimTemplates`**: Each ordinal replica dynamically provisions its own independent PersistentVolumeClaim (PVC) that persists across pod restarts and scaling. |
| **Scaling & Rollouts** | Scaled in parallel; updated via rolling replace (`maxSurge` / `maxUnavailable`). | Ordered scaling (`0 -> 1 -> 2`); updated strictly in **reverse ordinal order** (`2 -> 1 -> 0`). |
</details>

<details>
<summary><strong>● What is the difference between resource requests and limits in Kubernetes?</strong></summary>

**Answer:**
In Kubernetes container specs:

1. **Resource Requests (`resources.requests`):**
   - **Guaranteed baseline allocation.**
   - Used by the **`kube-scheduler`** during the filtering phase to find a worker node that has sufficient allocatable capacity to accommodate the pod.
   - Defines the pod's **Quality of Service (QoS) class** (Guaranteed, Burstable, BestEffort).

2. **Resource Limits (`resources.limits`):**
   - **Hard maximum ceiling** the container is allowed to consume.
   - **CPU Behavior (Compressible Resource):** If a container exceeds its CPU limit, the Linux kernel's Completely Fair Scheduler (CFS) **throttles** CPU cycles. The container runs slower but is *not killed*.
   - **Memory Behavior (Non-compressible Resource):** If a container attempts to allocate memory beyond its memory limit, the Linux kernel terminates the process via **OOM Killer (`OOMKilled` Exit Code 137)**, and the kubelet restarts the container.
</details>

<details>
<summary><strong>● In Kubernetes, if a node fails, what happens to that node and the pods running on it, and what does the scheduler do in response?</strong></summary>

**Answer:**
When a worker node experiences a failure (hardware crash, network partition, kernel freeze):

1. **Node Health Detection:**
   - The node's `kubelet` stops posting periodic heartbeats to the `kube-apiserver`.
   - After `node-monitor-grace-period` (default: 40 seconds), the **Node Lifecycle Controller** marks the node as `NotReady` or `Unknown`.
2. **Pod Eviction Timing:**
   - By default, pods have a built-in toleration:
     `tolerationSeconds: 300` (5 minutes) for `node.kubernetes.io/unreachable` and `node.kubernetes.io/not-ready`.
   - If the node remains down after 300 seconds, the Node Controller marks the pods on that node for deletion (`Terminating`).
3. **Controller & Scheduler Reaction:**
   - The higher-level controller (**ReplicaSet Controller**) notices the actual healthy replica count is less than `spec.replicas`.
   - It creates **brand-new Pod objects** with unassigned node names.
   - The **`kube-scheduler`** detects these unscheduled pods, filters the remaining healthy worker nodes in the cluster, scores them, and assigns the replacement pods to healthy nodes.
   - *Note on StatefulSets:* For pods managed by a StatefulSet, replacement pods will *not* be automatically rescheduled if the node is partitioned to prevent split-brain data corruption until the original pod is confirmed deleted.
</details>

<details>
<summary><strong>● If Kubernetes pods are running but the application is inaccessible, what could be the possible causes?</strong></summary>

**Answer:**
A systematic diagnostic checklist when Pods show `Running` but external/internal traffic fails:

1. **Service Selector Mismatch:**
   - The most common defect: The labels defined in `spec.selector` of the Kubernetes Service do not exactly match `spec.template.metadata.labels` of the Pods.
   - Verify endpoints: `kubectl get endpoints <service-name>`. If endpoints are `<none>`, selectors are misaligned.
2. **Readiness Probe Failure:**
   - If the readiness probe is failing, the pod stays in `Running` state, but the kubelet **removes the Pod IP from the Service EndpointSlice**. Check `kubectl describe pod` for readiness probe failures.
3. **Container Listening Port Misconfiguration:**
   - The application inside the container is listening on `127.0.0.1` (localhost only) instead of `0.0.0.0` (all interfaces), or the Service `targetPort` does not match the application's actual listening port.
4. **Ingress / LoadBalancer Misconfiguration:**
   - Ingress controller routing rules (host header, TLS secret, path prefix) do not route to the correct service name or port.
   - Cloud Load Balancer health checks are failing because the target group path does not return HTTP 200.
5. **NetworkPolicies:**
   - A restrictive `NetworkPolicy` is blocking ingress traffic to the pod on that port.
</details>

<details>
<summary><strong>● If a Kubernetes pod is constantly restarting, what would you check to diagnose the issue?</strong></summary>

**Answer:**
To diagnose a pod in `CrashLoopBackOff` or rapid restart loops:

1. **Check Previous Container Logs:**
   - Standard `kubectl logs <pod>` only shows the current crashed container. Run:
     `kubectl logs <pod> -c <container-name> --previous`
     to inspect the fatal stack trace or exit message right before the crash.
2. **Inspect Describe Output & Exit Codes:**
   - Run `kubectl describe pod <pod>` and look at `Last State: Terminated`:
     - **`Exit Code 137`:** OOMKilled (Out Of Memory) or SIGKILL from a failed liveness probe.
     - **`Exit Code 1 / 255`:** Application fatal exception, syntax error, or unhandled promise rejection.
     - **`Exit Code 143`:** Graceful SIGTERM timeout.
3. **Inspect Probes:**
   - Check events for `Liveness probe failed`. If liveness timeout or initial delay is too aggressive, the kubelet kills the container repeatedly.
4. **Environment Variables & Mounted Secrets:**
   - Verify database connection strings, credentials, and configuration files mounted into the container are valid.
</details>

<details>
<summary><strong>● What is service discovery in the context of Kubernetes/microservices?</strong></summary>

**Answer:**
**Service Discovery** is the automated mechanism that allows microservices to locate and communicate with each other dynamically over the network without hardcoding IP addresses:

1. **Why it is necessary:** Pods in Kubernetes are ephemeral; their IP addresses change every time they scale, restart, or reschedule onto different nodes.
2. **How Kubernetes Implements Service Discovery:**
   - **Kubernetes Services:** A Service provides a stable, static virtual IP (`ClusterIP`) and a DNS name that persists for the entire lifecycle of the workload.
   - **CoreDNS (Internal DNS):** Kubernetes runs CoreDNS inside the cluster. When `order-service` calls `http://payment-service.prod.svc.cluster.local`, CoreDNS resolves the domain to the Service's ClusterIP.
   - **kube-proxy & EndpointSlices:** `kube-proxy` continuously updates IPVS/iptables rules on worker nodes, automatically load-balancing requests sent to the ClusterIP across the real, dynamically changing IP addresses of healthy backend pods.
</details>

<details>
<summary><strong>● What is the difference between an Ingress and a Load Balancer in Kubernetes?</strong></summary>

**Answer:**
| Feature | LoadBalancer Service (`type: LoadBalancer`) | Ingress (`kind: Ingress`) |
|---|---|---|
| **OSI Layer** | **Layer 4** (TCP/UDP). | **Layer 7** (HTTP/HTTPS). |
| **Cloud Resource** | Provisions an **independent cloud load balancer** (e.g., AWS NLB/CLB) for *each individual service*. | Provisions a **single shared load balancer** (e.g., AWS ALB) routing to dozens of backend services. |
| **Cost Efficiency** | Expensive in large clusters (paying for 50 cloud LBs for 50 microservices). | Highly cost-effective (1 load balancer serves the entire cluster). |
| **Routing Capabilities** | Basic port forwarding (`IP:Port -> Pods:Port`). No URI path or host header awareness. | Advanced L7 routing: Path-based (`/api`, `/web`), Host-based (`api.domain.com`), SSL/TLS termination, URL rewriting. |
| **Controller Requirement** | Handled natively by cloud provider integration. | Requires an **Ingress Controller** (e.g., AWS Load Balancer Controller, NGINX Ingress) to translate ingress objects into routing rules. |
</details>

#### 【 IAC 】

<details>
<summary><strong>● What is Terraform drift?</strong></summary>

**Answer:**
**Terraform drift** is any discrepancy between the real-world state of cloud infrastructure and the state recorded in Terraform code and state files:
- Occurs due to emergency manual changes in the AWS Console, ad-hoc CLI scripts, or external service modifications.
- Detected via `terraform plan -refresh-only` or scheduled pipeline drift scanners.
- Reconciled by either applying Terraform to overwrite manual changes or updating Terraform code to incorporate intended infrastructure modifications.
</details>

<details>
<summary><strong>↳ Follow-up: Have you personally performed a Terraform import before?</strong></summary>

**Answer:**
Yes. I have imported existing, manually provisioned AWS infrastructure (such as legacy VPCs, S3 buckets, and RDS instances) into Terraform management to bring unmanaged infrastructure under version-controlled IaC governance.
</details>

<details>
<summary><strong>↳ Follow-up: Can you walk me through the steps involved in performing a Terraform import?</strong></summary>

**Answer:**
In modern Terraform (Terraform 1.5+), the recommended method uses declarative **`import` blocks**:

1. **Step 1: Write the Resource Declaration:**
   - Define the empty or minimal resource block in `.tf`:
     ```hcl
     resource "aws_s3_bucket" "legacy_bucket" {
       bucket = "enterprise-legacy-data-bucket"
     }
     ```
2. **Step 2: Add the `import` Block:**
   ```hcl
   import {
     to = aws_s3_bucket.legacy_bucket
     id = "enterprise-legacy-data-bucket" # Resource physical ID in AWS
   }
   ```
3. **Step 3: Run Plan to Generate/Verify:**
   - Execute `terraform plan`. Terraform queries AWS APIs, reconciles attributes, and indicates that 1 resource will be imported into state.
4. **Step 4: Execute Apply:**
   - Run `terraform apply`. Terraform binds the real AWS resource to the state file without recreating or modifying the physical cloud resource.
</details>

<details>
<summary><strong>↳ Follow-up: Is that the complete process for a Terraform import, or are there additional steps involved?</strong></summary>

**Answer:**
There is a critical additional post-import reconciliation step:

1. **Configuration Alignment (Eliminating Diffs):**
   - The initial HCL declaration often lacks specific cloud attributes (e.g., tags, lifecycle rules, server-side encryption).
   - After importing, you must run `terraform plan`.
   - If Terraform proposes any unwanted changes or in-place modifications (`~`), you must update your `.tf` configuration code until `terraform plan` outputs **`No changes. Your infrastructure matches the configuration.`**
2. **Codebase Cleanup:**
   - Remove or keep the `import {}` block (in Terraform 1.5+, keeping it is valid for documentation, or it can be cleaned up once persisted to `.tfstate`).
   - Commit the updated HCL code to Git and push via Pull Request.
</details>

<details>
<summary><strong>● What are Terraform taints?</strong></summary>

**Answer:**
In Terraform, **tainting** marks a specific resource in the state file as degraded or corrupt, forcing Terraform to **destroy and recreate that resource** during the next `terraform apply`:

- **Legacy Command:** `terraform taint aws_instance.web` (deprecated in v0.15.2+).
- **Modern Preferred Method:** Use the `-replace` flag directly during planning or applying:
  ```bash
  terraform plan -replace="aws_instance.web"
  terraform apply -replace="aws_instance.web"
  ```
- **Use Case:** Re-running user-data cloud-init scripts on an EC2 instance, replacing an unhealthy node, or rebuilding a virtual machine without destroying other resources in the same state file.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● How do you connect two VPCs when you need to share resources between them?</strong></summary>

**Answer:**
To connect two VPCs:
1. **AWS VPC Peering:**
   - Best for point-to-point connection between two VPCs (in the same or different AWS accounts/regions).
   - **Prerequisite:** VPC CIDRs **must not overlap** (e.g., `10.0.0.0/16` and `10.1.0.0/16`).
   - **Setup:** Create VPC Peering Connection -> Accept connection from target VPC -> Add route in both VPC Route Tables pointing target CIDR to `pcx-xxxx` -> Update Security Groups to allow inter-VPC traffic.
   - **Performance:** Direct AWS backbone routing, zero bandwidth bottleneck, no single point of failure.
   - **Limitation:** Non-transitive (VPC A -> VPC B -> VPC C does *not* allow A to talk to C).
</details>

<details>
<summary><strong>↳ Follow-up: How would you connect multiple VPCs together, rather than just two?</strong></summary>

**Answer:**
For connecting multiple VPCs (e.g., 5 to 50+ VPCs across accounts and on-premises datacenters), **AWS Transit Gateway (TGW)** is the architectural standard:

- Acts as a **regional cloud router** (hub-and-spoke topology).
- Eliminates complex mesh VPC peering connections: instead of $N(N-1)/2$ peering pairs, every VPC simply attaches to the Transit Gateway once.
- Supports **Transit Gateway Route Tables** to build network segmentation (e.g., Dev VPCs cannot reach Prod VPCs, but both can reach a Shared Services VPC and On-Premises via Direct Connect).
</details>

<details>
<summary><strong>↳ Follow-up: Who typically manages the Transit Gateway in your organization, and have you personally created one?</strong></summary>

**Answer:**
In enterprise multi-account environments:
- The Transit Gateway is owned and operated by the **Central Cloud Platform / Core Networking Team** inside a dedicated **Network Hub AWS Account**.
- The TGW is shared with workload accounts (Dev, Stage, Prod) using **AWS RAM (Resource Access Manager)**.
- I have personally automated the provisioning of Transit Gateways, Transit Gateway VPC attachments, and inter-attachment route tables using Terraform (`terraform-aws-modules/transit-gateway`).
</details>

<details>
<summary><strong>↳ Follow-up: Can you confirm and elaborate on your hands-on experience creating a Transit Gateway?</strong></summary>

**Answer:**
Yes. Using Terraform:
1. Provisioned `aws_ec2_transit_gateway` with custom ASN (`amazon_side_asn = 64512`) and DNS support enabled.
2. Created `aws_ec2_transit_gateway_vpc_attachment` selecting dedicated `/28` transit subnets in each AZ for each VPC to keep attachment traffic isolated.
3. Configured separate TGW route tables: `Production_TGW_RT` and `NonProd_TGW_RT` to enforce network segregation.
4. Added route entries in VPC route tables: routing corporate on-prem CIDRs (`192.168.0.0/16`) and shared services CIDRs (`10.50.0.0/16`) to the Transit Gateway ID (`tgw-xxxx`).
</details>

<details>
<summary><strong>↳ Follow-up: Which database service does your project use?</strong></summary>

**Answer:**
Our primary production transactional workloads use **Amazon Aurora PostgreSQL Multi-AZ cluster**:
- Storage auto-scales dynamically up to 128 TiB.
- Multi-AZ deployment with an automated failover replica (failover occurs in under 30 seconds with zero data loss).
- Backups are automated with continuous point-in-time recovery (PITR) retained for 35 days.
</details>

<details>
<summary><strong>↳ Follow-up: Is RDS used specifically for the analytics reporting part of the project?</strong></summary>

**Answer:**
No. For analytics and heavy reporting, querying an OLTP production database is an anti-pattern because long-running analytical queries exhaust IOPS and lock tables needed by customer transactions.

Instead:
- **OLTP Transactions:** Handled by Amazon Aurora PostgreSQL.
- **Reporting Queries:** Directed to an **Aurora Read Replica** or Aurora Auto Scaling read pool to isolate query workloads.
- **Heavy OLAP / Big Data Analytics:** We extract data via AWS DMS (Database Migration Service) or Kafka CDC pipelines into **Amazon S3 Data Lake** and query using **Amazon Athena** or load into **Amazon Redshift**.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● Where does your team store application logs, and what logging system do you use?</strong></summary>

**Answer:**
We implement a centralized, tiered logging architecture:
- **Log Collection & Shipping:** Application pods output JSON logs to `stdout`/`stderr`. **Fluent Bit** runs as a Kubernetes DaemonSet, collects container logs from `/var/log/containers/`, enriches them with Kubernetes metadata (pod name, namespace, labels), and streams them upstream.
- **Short-Term Indexing & Search:** Shipped to **OpenSearch / Elasticsearch** (or Datadog Log Management) for real-time querying, visual dashboarding, and alerting.
- **Long-Term Durable Archival:** All raw logs are simultaneously archived into an encrypted **Amazon S3** bucket with lifecycle policies transitioning data to S3 Glacier Flexible Archive after 90 days for cost-effective 7-year compliance auditability.
</details>

<details>
<summary><strong>↳ Follow-up: Have you personally worked hands-on with the ELK stack for logging?</strong></summary>

**Answer:**
Yes, extensive experience with the ELK (Elasticsearch, Logstash, Kibana) and EFK (Elasticsearch, Fluent Bit/Fluentd, Kibana) stacks:
- Deployed OpenSearch/Elasticsearch clusters on AWS.
- Configured **Kibana Index Patterns**, saved search queries, and built operational dashboards tracking HTTP error rates, error stack traces, and slow transactions.
- Configured **Index Lifecycle Management (ILM)** policies: hot phase (SSD NVMe storage for 7 days), warm phase (read-only for 30 days), cold phase (snapshot to S3 and delete index).
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Suppose you've hosted a static website and made a code change, pushed it, and the CI/CD pipeline ran successfully and deployment completed without errors. However, when you browse the website, you still see the old content. What could be causing this issue?</strong></summary>

**Answer:**
The most common cause is **caching layers** serving stale assets:

1. **CDN / CloudFront Edge Cache:**
   - Amazon CloudFront edge locations cached the old `index.html` and static bundles according to the cache behavior TTL (often 24 hours).
   - **Remediation:** Pipeline must execute a **CloudFront Cache Invalidation** after S3 upload:
     ```bash
     aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
     ```
2. **Browser Client Cache:**
   - The user's browser cached `index.html` locally via HTTP headers (`Cache-Control: max-age=86400`).
   - **Remediation:** Hard refresh browser (`Ctrl + F5`), or configure S3 metadata on `index.html` to `Cache-Control: no-cache, no-store, must-revalidate`.
3. **Artifact Bundling Hash Mismatch:**
   - If modern frontend build tools (Webpack/Vite) failed to generate new cache-busting content hashes in asset filenames (`main.a1b2c3.js`), browsers continue requesting cached file names.
</details>

<details>
<summary><strong>↳ Follow-up: Besides the causes you mentioned, are there any other possible reasons the website might still show old content even though the pipeline and deployment succeeded?</strong></summary>

**Answer:**
Yes, several subtle production causes include:

1. **Deployment to Wrong S3 Bucket / Environment:**
   - CI pipeline pushed build artifacts to a `dev` or `staging` S3 bucket instead of the `production` bucket due to misconfigured pipeline environment variables.
2. **CloudFront Origin Misconfiguration:**
   - CloudFront distribution origin points to an outdated S3 prefix or a different S3 bucket.
3. **DNS Resolution to Legacy CDN / Host:**
   - User's local DNS resolver cached a stale IP or points to an older CloudFront distribution or legacy web server.
4. **Intermediate Proxy Caching:**
   - Corporate forward proxies or ISP transparent caching proxies caching HTTP responses.
5. **Service Worker Caching (PWA):**
   - A Progressive Web App (PWA) running an active Service Worker in the user's browser serves cached assets offline until the worker script updates.
</details>

<details>
<summary><strong>● What deployment strategy do you typically use for your applications?</strong></summary>

**Answer:**
In our production Kubernetes environments, we primarily use **Rolling Updates** for standard stateless services and **Canary Deployments** (via Argo Rollouts) for high-impact tier-1 microservices:
- **Rolling Update:** Zero downtime; progressively replaces old pods with new pods while keeping service available throughout.
- **Canary Deployment:** Routes 5%–10% of real user traffic to the new revision, tracks real-time error rates and latency, and automatically promotes or aborts based on Prometheus metrics.
</details>

<details>
<summary><strong>↳ Follow-up: Do you use all three deployment strategies (rolling update, blue-green, and canary) in your projects?</strong></summary>

**Answer:**
We choose the deployment strategy based on workload characteristics and criticality:
- **Rolling Update:** Standard default for internal services, non-critical APIs, and batch workers where standard health checks are sufficient.
- **Canary:** Used for mission-critical, public-facing payment and authentication services where automated metric analysis (error rates, p99 latency) must validate changes before full rollout.
- **Blue-Green:** Used specifically when deploying major version upgrades, breaking API changes, or systems requiring instant 100% cutover and instant fallback capability without mixed version coexistence.
</details>

<details>
<summary><strong>↳ Follow-up: Are all the applications in your current project built as microservices?</strong></summary>

**Answer:**
The core business domain and newly developed customer-facing platforms are built as containerized microservices running on EKS. However, like most mature enterprise ecosystems, we operate in a **hybrid landscape** where some foundational backend services and legacy data pipelines remain on monolithic architectures.
</details>

<details>
<summary><strong>↳ Follow-up: Have you not worked on any legacy applications at all in your current project?</strong></summary>

**Answer:**
We actively interface with legacy backend components:
- Several core transaction systems are legacy Java Spring monoliths running on Amazon EC2 instances with dedicated Auto Scaling Groups.
- As DevOps engineers, our responsibility includes supporting the automated CI/CD packaging for these legacy monoliths, managing their infrastructure via Terraform, and gradually architecting the **Strangler Fig pattern** to carve out independent microservices to Kubernetes.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you start by introducing yourself and giving an overview of your professional background?

<details>
<summary><strong>↳ Follow-up: In all your years of experience, have you never had the opportunity to work on a legacy system?</strong></summary>

**Answer:**
I have indeed worked extensively on legacy systems. In earlier roles and throughout enterprise migration initiatives, I have managed monolithic applications deployed directly onto bare-metal servers and static EC2 instances:
- Handled legacy Ant and Maven build scripts, manual database patching procedures, and monolithic WAR/EAR deployments to Apache Tomcat and WebLogic.
- This hands-on experience with legacy pain points (slow build times, lack of test automation, snowflake servers) is precisely what informed my deep expertise in modern DevOps practices, containerization, and automated CI/CD.
</details>

<details>
<summary><strong>↳ Follow-up: How was your experience working with legacy systems earlier in your career?</strong></summary>

**Answer:**
Working with legacy systems was a tremendous learning experience that reinforced foundational engineering disciplines:
1. **Understanding Root System Behaviors:** Debugging issues without container isolation taught me deep Linux kernel internals, systemd services, socket buffers, and network routing.
2. **Appreciating Automation & Idempotency:** Experiencing "it works on my machine" failures drove my passion for Docker and immutable infrastructure.
3. **Pragmatic Modernization:** Taught me that legacy systems running core business functions cannot simply be rewritten overnight; they require careful, phased modernization using backward-compatible APIs, automated testing, and incremental cloud migrations.
</details>

<details>
<summary><strong>● Can you describe the project you are currently working on (or most recently worked on)?</strong></summary>

**Answer:**
In my current role, I serve as a Senior DevOps Engineer responsible for the cloud platform supporting our **high-throughput digital payments and banking microservices platform**:
- **Scale:** Over 40 containerized microservices running on Amazon EKS across multiple AWS accounts, processing millions of API requests daily.
- **Core Toolset:** Terraform for infrastructure provisioning, Amazon EKS, GitLab CI / GitHub Actions, Helm, Argo CD for GitOps deployments, and Prometheus/Grafana/Datadog for full-stack observability.
- **Key Achievements:**
  - Automated zero-trust security implementation with Istio mutual TLS and AWS KMS encryption.
  - Architected progressive Canary deployments with Argo Rollouts, reducing deployment-related production incidents by 85%.
  - Migrated legacy static Jenkins build slaves to ephemeral auto-scaling Kubernetes runners, cutting CI build times by 40% and saving infrastructure costs.
</details>

#### 【 OTHER 】

<details>
<summary><strong>● What is shift-left testing?</strong></summary>

**Answer:**
**Shift-Left Testing** is the DevOps practice of moving testing, security evaluations, and quality checks **earlier in the software development lifecycle** (toward the "left" side of the delivery timeline):

1. **Traditional Model (Shift-Right):** Testing and security reviews occur at the end of the release cycle (after integration or staging deployment), making bugs expensive, slow, and risky to fix.
2. **Shift-Left Implementation:**
   - **Local Developer Machine:** Pre-commit hooks (`gitleaks`, `tflint`, code linters) and fast unit tests.
   - **Early CI Stages:** Automated unit tests, code coverage gates, static application security testing (SAST with SonarQube), and dependency vulnerability scans (OWASP Dependency-Check) run on every branch push.
   - **Infrastructure as Code:** Static security scanning of Terraform files (`checkov`, `tfsec`) before plans are generated.
3. **Business & Technical Benefits:**
   - Defects are caught when they are cheapest and fastest to fix.
   - Drastically accelerates deployment velocity and prevents broken builds or security vulnerabilities from ever reaching staging or production.
</details>

</details>
</details>

<details open>
<summary><h2>🏢 TruGlobal</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 AI/ML 】

<details>
<summary><strong>↳ Follow-up: Can you elaborate on the tools you have worked with, specifically in the DevOps, cloud, and AI areas, that you use on a daily basis?</strong></summary>

**Answer:**
In my day-to-day engineering workflow, I combine enterprise cloud-native DevOps platforms with cutting-edge AI-assisted developer tooling:

1. **DevOps & Cloud Core:**
   - **Infrastructure as Code:** Terraform and Terragrunt for AWS multi-account orchestration.
   - **Containers & Orchestration:** Docker, Amazon EKS, Helm 3, and Argo CD for GitOps.
   - **CI/CD:** GitHub Actions (reusable workflows) and Jenkins (ephemeral Kubernetes agents).
   - **Observability:** Prometheus, Grafana, OpenSearch/ELK, and Datadog.

2. **AI & Agentic Coding Ecosystem:**
   - **GitHub Copilot & Copilot CLI:** Autocompleting boilerplate HCL, writing complex shell pipelines, drafting unit tests, and debugging error logs.
   - **Cursor IDE & Anthropic Claude Code:** Leveraging AI context-aware coding assistants configured with custom project rules (`.cursorrules`) to perform large-scale refactors of Helm templates and Terraform modules.
   - **Model Context Protocol (MCP):** Implementing and connecting MCP servers (e.g., GitHub, PostgreSQL, AWS, and Kubernetes MCP servers) to empower AI coding agents to securely inspect live cluster state and query databases within local developer environments.
</details>

<details>
<summary><strong>● How have you utilized GitHub Copilot in your day-to-day work? Have you worked with this tool, and if so, how exactly do you use it?</strong></summary>

**Answer:**
I utilize GitHub Copilot daily as an interactive pair programmer across three key DevOps domains:

1. **Infrastructure as Code (Terraform/HCL):**
   - Autocompleting verbose AWS provider resource arguments (e.g., complex S3 lifecycle rules, IAM policy document statements, and ALB listener rules). Copilot significantly speeds up drafting repetitive resource blocks while I enforce security constraints.
2. **Scripting & Command-Line Utilities:**
   - Writing complex `bash`, `python` (Boto3), and `awk` text-processing scripts. For example, prompting Copilot to generate a Python script that parses ECS task definitions and identifies deprecated container environment variables.
3. **CI/CD Pipeline & Manifest Generation:**
   - Drafting GitHub Actions YAML workflows and Kubernetes manifests.
   - Using **GitHub Copilot Chat** to explain cryptic error stack traces from Jenkins build logs or Kubernetes `CrashLoopBackOff` events.
</details>

<details>
<summary><strong>↳ Follow-up: Do you have working-level proficiency in tools like Cursor, Copilot, custom coding agents, and MCP setup, given that the client requires support for these tools?</strong></summary>

**Answer:**
Yes, I possess strong hands-on proficiency in modern AI-assisted engineering and the Model Context Protocol (MCP):

1. **Cursor & Custom Rules:**
   - Experienced in configuring workspace-level `.cursorrules` or `.cursor/rules` to enforce strict organizational standards (e.g., mandating Terraform version pins, required resource tags, error handling conventions in Go/Python, and CIS benchmark security guidelines).
2. **Model Context Protocol (MCP) Setup & Integration:**
   - Configured MCP client integrations in Cursor and Claude Desktop by defining `mcpServers` in `claude_desktop_config.json`:
     - **Kubernetes MCP Server:** Enables the LLM to run read-only diagnostics (`kubectl get pods`, `kubectl logs`) directly from the chat window.
     - **Postgres / Database MCP:** Allows the agent to inspect table schemas and generate accurate SQL migration scripts.
     - **Git / GitHub MCP:** Enables the agent to analyze git diffs, review Pull Requests, and author commit messages adhering to conventional commit standards.
3. **Custom Coding Agents:**
   - Understanding of agentic patterns: tool calling, structured JSON output validation, multi-turn reasoning loops, and prompt engineering tailored to automated DevOps workflows.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Could you please introduce yourself?

</details>
</details>

<details open>
<summary><h2>🏢 Photon</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 CI/CD 】

<details>
<summary><strong>● Can you explain the stages of a Jenkins CI/CD pipeline that you have implemented for your applications?</strong></summary>

**Answer:**
A production-grade Jenkins declarative pipeline implemented for our containerized Java/Node.js microservices includes the following sequential stages:

```
[ Checkout ] ──> [ Code Quality & Unit Test ] ──> [ SAST & Quality Gate ]
                                                           │
[ GitOps Manifest Sync ] <── [ Image Push ] <── [ Docker Build & Trivy ] <──┘
```

1. **Checkout & Secret Scanning:** Clones source code; runs `gitleaks` to verify no hardcoded secrets exist.
2. **Compile & Unit Test:** Compiles source code (`mvn clean test`) and publishes JaCoCo code coverage.
3. **Static Analysis & Quality Gate:** Scans code with **SonarQube** via `withSonarQubeEnv`. The pipeline halts at `waitForQualityGate()` if bugs, vulnerabilities, or coverage criteria fail.
4. **Software Composition Analysis (SCA):** Runs OWASP Dependency-Check to identify CVEs in third-party libraries.
5. **Container Build & Security Scan:**
   - Multi-stage Docker build produces a hardened Distroless image tagged with `${GIT_COMMIT}`.
   - **Trivy** scans image layers; pipeline fails if `CRITICAL` unpatched vulnerabilities are found.
6. **Registry Publish:** Pushes image to Amazon ECR.
7. **GitOps Manifest Update:** Clones the deployment Helm repository, updates the image tag in `values.yaml`, commits, and pushes to trigger **Argo CD** automated synchronization.
</details>

<details>
<summary><strong>● How would you set up a master-slave (controller-agent) architecture in Jenkins?</strong></summary>

**Answer:**
In modern enterprise environments, Jenkins controller-agent architecture is configured using **ephemeral Kubernetes agents** (preferred) or **static SSH agents**:

1. **Kubernetes Ephemeral Agents (Production Best Practice):**
   - Install the **Jenkins Kubernetes Plugin** on the Jenkins Controller.
   - Under `Manage Jenkins -> Clouds -> Add a new cloud -> Kubernetes`, configure the Kubernetes cluster API URL, service account token, and namespace.
   - Define **Pod Templates**: Each build job spins up an on-demand, isolated pod containing required containers (e.g., Maven, Docker CLI, Kaniko, SonarQube Scanner). When the build completes, the pod is automatically terminated, ensuring pristine workspaces and zero idle compute costs.

2. **Static VM Agent via SSH:**
   - Provision an EC2 instance / VM with Java (JRE) installed.
   - Generate an SSH key pair; add the public key to `/home/jenkins/.ssh/authorized_keys` on the agent.
   - On the Controller: `Manage Jenkins -> Manage Nodes -> New Node` -> Launch method: **Launch agents via SSH** -> Supply Agent IP, SSH credentials, and remote root directory (`/home/jenkins`).
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● Have you worked with Docker Compose?</strong></summary>

**Answer:**
Yes. I use **Docker Compose** (`compose.yaml`) extensively to define and orchestrate multi-container application stacks for local developer environments, integration testing, and CI pipeline test fixtures:
- Defining services, build contexts, environment variables (`.env`), port mappings, health checks (`healthcheck:`), dependency ordering (`depends_on:` with condition `service_healthy`), internal networks, and named volume persistence (e.g., running app, PostgreSQL, Redis, and localstack concurrently).
</details>

<details>
<summary><strong>↳ Follow-up: Have you also worked with Docker networking?</strong></summary>

**Answer:**
Yes. Docker provides several core network drivers:
- **`bridge` (Default):** Creates an isolated virtual bridge network on the host (`docker0`). Containers connect to it via `veth` pairs and communicate via IP. In *user-defined bridge networks*, Docker provides automatic DNS resolution between container names.
- **`host`:** Removes network isolation between container and host; the container shares the host's networking namespace directly (maximum performance, but port conflicts possible).
- **`none`:** Completely disables networking for isolated batch or cryptographic processes.
- **`overlay`:** Enables multi-host container networking across Docker Swarm nodes using VXLAN tunnels.
- **`macvlan`:** Assigns a physical MAC address to the container, making it appear as a physical hardware device on the local network.
</details>

<details>
<summary><strong>● How would you optimize Dockerfiles using multi-stage builds?</strong></summary>

**Answer:**
Multi-stage builds separate the **build environment** (heavy compilers, SDKs, build tools) from the **runtime environment** (minimal runtime libraries), dramatically reducing image size, attack surface, and build time:

```dockerfile
# Stage 1: Build & Compile
FROM maven:3.9-eclipse-temurin-17-alpine AS builder
WORKDIR /build
# Cache dependencies first (layer caching)
COPY pom.xml .
RUN mvn dependency:go-offline -B
# Copy source and compile
COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Hardened Minimal Runtime
FROM gcr.io/distroless/java17-debian12:nonroot
WORKDIR /app
# Copy only the compiled JAR from builder stage
COPY --from=builder /build/target/payment-service.jar app.jar
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

**Optimization Benefits:**
- Drops image size from ~800MB to ~150MB.
- Strips package managers (`apt`, `apk`), compilers, and build tools from the production container, eliminating thousands of potential CVE vulnerabilities.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● What is the difference between Docker Swarm and Kubernetes as container orchestration platforms?</strong></summary>

**Answer:**
| Feature | Docker Swarm | Kubernetes (K8s) |
|---|---|---|
| **Complexity & Setup** | Extremely simple; built directly into Docker CLI (`docker swarm init`). Minimal learning curve. | Complex architecture, steep learning curve, requires control plane management or managed cloud services (EKS/GKE). |
| **Scaling & Performance** | Fast deployment for smaller workloads (up to hundreds of nodes). | Enterprise-scale (up to 5,000 nodes, 150,000 pods per cluster). |
| **Autoscaling** | No native Horizontal Pod or Node Autoscaling. | Robust native **HPA**, **VPA**, Cluster Autoscaler, and **Karpenter**. |
| **Ecosystem & Extensibility** | Limited ecosystem; virtually no third-party integrations. | Vast CNCF ecosystem; extensible via **Custom Resource Definitions (CRDs)** and Operators. |
| **Service Mesh & GitOps** | Limited. | Deep native support for Istio, Linkerd, Argo CD, and Flux. |
| **Industry Adoption** | Largely phased out in modern enterprise production. | The de-facto global industry standard for container orchestration. |
</details>

<details>
<summary><strong>● If a downtime occurs in an application running on Kubernetes (e.g., EKS), how would you troubleshoot and distinguish between application-level and system/network-level issues to find the root cause?</strong></summary>

**Answer:**
Troubleshooting Kubernetes downtime follows a structured isolation matrix dividing application issues from infrastructure issues:

1. **Step 1: Rapid High-Level Cluster Triage:**
   - Check cluster node status: `kubectl get nodes`. Are any nodes in `NotReady` or experiencing disk/memory pressure?
   - Check pod status across namespace: `kubectl get pods -n <ns> -o wide`. Are pods in `CrashLoopBackOff`, `OOMKilled`, `ImagePullBackOff`, or `Running`?

2. **Step 2: Distinguishing Application-Level Issues:**
   - **Characteristics:** Pods restart frequently, high restart count, exit codes non-zero.
   - **Verification:**
     - Run `kubectl logs <pod> --previous` to inspect uncaught exceptions or database connection pool timeouts.
     - Check exit code: `kubectl describe pod <pod>` (`Exit Code 137` = OOMKilled, `1` = runtime exception).
     - Check health probe logs: Are liveness/readiness probes returning HTTP 500/503 from the app?

3. **Step 3: Distinguishing System / Network-Level Issues:**
   - **Characteristics:** Pods show `Running (Ready)`, but external users receive HTTP 502/504 or connection timeouts.
   - **Verification:**
     - **DNS:** Test CoreDNS resolution from inside the cluster: `kubectl run debug --rm -i --tty --image=busybox -- nslookup kubernetes.default`.
     - **Endpoints:** Verify Service endpoint mapping: `kubectl get endpointslices` or `kubectl get endpoints <svc>`.
     - **Ingress & Cloud LB:** Check ALB target group health in the AWS Console. Are targets failing health checks? Inspect AWS Load Balancer Controller logs in `kube-system`.
     - **CNI / IP Exhaustion:** Check AWS VPC CNI logs (`aws-node`) to verify if worker nodes exhausted available ENI IP addresses.
</details>

<details>
<summary><strong>● What deployment update strategy do you typically follow in Kubernetes?</strong></summary>

**Answer:**
We primarily use the **Rolling Update** strategy (`type: RollingUpdate`) for stateless workloads:
- Configured with `maxSurge: 25%` (creates 25% additional pods before deleting old ones) and `maxUnavailable: 0` (guarantees zero drop in baseline capacity).
- Combined with proper **readiness probes** and graceful shutdown lifecycle hooks (`preStop: sleep 15`) to ensure zero dropped HTTP connections during pod rotation.
</details>

<details>
<summary><strong>↳ Follow-up: Are you familiar with other Kubernetes deployment update strategies besides rolling updates?</strong></summary>

**Answer:**
Yes:
1. **Recreate (`type: Recreate`):** Terminates all existing pods simultaneously before creating new ones. Introduces downtime; used only when application state or database migrations prohibit multiple versions running concurrently.
2. **Canary Deployments (via Argo Rollouts / Flagger):** Routes a small percentage of traffic (10%) to the new version, validates Prometheus metrics, and progressively promotes to 100%.
3. **Blue-Green Deployments:** Runs two identical environments (Blue = live, Green = new) simultaneously, switching the Service selector or Load Balancer target group instantly once Green passes validation.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Suppose an EC2 instance owner has lost their PEM key file, and you need to give a developer access to log into that machine. How would you achieve this?</strong></summary>

**Answer:**
There are several secure, production-grade recovery options that avoid data loss:

1. **Method 1: AWS Systems Manager (SSM) Session Manager (Fastest & Zero-Downtime):**
   - If the EC2 instance has the SSM Agent running and an IAM role with `AmazonSSMManagedInstanceCore` attached, no SSH key is needed at all.
   - Grant the developer IAM permissions for `ssm:StartSession`. The developer logs in securely via the AWS Console or AWS CLI (`aws ssm start-session --target <instance-id>`).
2. **Method 2: AWS EC2 Instance Connect (Zero-Downtime):**
   - Push a new ephemeral public key valid for 60 seconds using the AWS CLI:
     `aws ec2-instance-connect send-ssh-public-key --instance-id <id> --instance-os-user ec2-user --ssh-public-key file://dev_key.pub`
   - The developer then SSHs directly using their private key.
3. **Method 3: EBS Volume Rescue Mount (Offline Recovery):**
   - If SSM is not installed: Stop instance -> Detach root EBS volume -> Attach as secondary volume (`/dev/sdf`) to a temporary rescue EC2 instance -> Mount volume (`mount /dev/xvdf1 /mnt`) -> Append developer's public key into `/mnt/home/ec2-user/.ssh/authorized_keys` -> Unmount -> Reattach to original instance as `/dev/xvda` -> Start instance.
</details>

<details>
<summary><strong>↳ Follow-up: Given your proposed solution, are you concluding that the developer would be able to SSH into the EC2 machine directly from their own machine?</strong></summary>

**Answer:**
Yes. If the developer needs direct terminal SSH access from their local laptop:
- **Via EC2 Instance Connect / Authorized Keys:** Once their public key is in `authorized_keys`, they run `ssh -i ~/.ssh/id_ed25519 ec2-user@<instance-ip>`.
- **Via SSM Session Manager Proxy (SSH over SSM):** The developer configures `~/.ssh/config`:
  ```
  host i-* mi-*
    ProxyCommand sh -c "aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p'"
  ```
  This allows running standard `ssh ec2-user@<instance-id>` directly from their local terminal through encrypted AWS SSM tunnels without opening port 22 or needing a public IP.
</details>

<details>
<summary><strong>↳ Follow-up: If a developer needs to SSH directly from their terminal into an EC2 instance's IP address without possessing the PEM key file, what steps would allow them to log in?</strong></summary>

**Answer:**
The exact steps are:
1. **Developer Generates Keypair:** On their local terminal, the developer runs:
   `ssh-keygen -t ed25519 -C "developer@company.com"`
   *(The developer keeps the private key completely private on their local machine).*
2. **Public Key Sharing:** The developer provides *only their public key* (`id_ed25519.pub`) to the DevOps/Cloud administrator.
3. **Administrator Injects Public Key:** The administrator uses AWS SSM Session Manager or EC2 User Data to append the developer's public key string into `/home/ec2-user/.ssh/authorized_keys` and sets permissions:
   `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys`.
4. **Developer Logs In:**
   `ssh -i ~/.ssh/id_ed25519 ec2-user@<instance-ip>`.
</details>

<details>
<summary><strong>↳ Follow-up: Without ever sharing the actual PEM key with the developer, how can you enable them to SSH into the EC2 instance?</strong></summary>

**Answer:**
By following the **Public Key Cryptography principle**: **Never share private keys.**
1. The original PEM file is a private key; sharing it is a security anti-pattern.
2. The developer generates their own independent key pair locally.
3. Only the developer's *public key* is added to the EC2 server's `~/.ssh/authorized_keys` file.
4. SSH authentication verifies mathematical possession of the private key without the server or administrator ever seeing it.
5. Alternatively, grant access entirely via **IAM Role and AWS Systems Manager Session Manager**, eliminating SSH keys completely.
</details>

<details>
<summary><strong>● If you need to write a security policy for a particular EC2 instance to allow only specific ports and control public IP exposure, how would you configure this using security groups?</strong></summary>

**Answer:**
1. **Subnet & IP Allocation:** Deploy the EC2 instance in a **Private Subnet** with no public IP address assigned (`AssociatePublicIpAddress = false`).
2. **Security Group Configuration:**
   - **Inbound Rules:**
     - Open only the specific application port (e.g., TCP 8080).
     - Set the Source to the **Security Group ID of the Application Load Balancer** (`sg-alb-id`), not an open CIDR. This enforces that traffic *must* pass through the ALB and WAF.
     - For administrative access, allow SSH (port 22) only from a specific corporate VPN CIDR (`203.0.113.10/32`) or use SSM Session Manager with no inbound ports open.
   - **Outbound Rules:** Restrict egress to TCP 443 (HTTPS) for updates, rather than default open `0.0.0.0/0`.
</details>

<details>
<summary><strong>● In an EC2 security group, if inbound rule 1 allows traffic on port 8080 and a second inbound rule (rule 2) on the same port 8080 denies traffic, which rule takes effect?</strong></summary>

**Answer:**
**Traffic is ALLOWED.**

- **Key AWS Architecture Principle:** **AWS Security Groups do NOT support "DENY" rules.**
- All rules in a Security Group are **permissive (ALLOW only)**. You cannot create a deny rule inside a Security Group.
- If multiple rules match the same port, any rule that allows traffic takes precedence.
- To explicitly **DENY** traffic from specific IP addresses or CIDRs, you must use a **Network Access Control List (NACL)** at the subnet boundary, which processes rules in numerical order and supports explicit `ALLOW` and `DENY` actions.
</details>

<details>
<summary><strong>● If you have created an EBS volume attached to an EC2 instance, is it possible to mount that same EBS volume to another EC2 instance, and how would you do it?</strong></summary>

**Answer:**
1. **Standard EBS Volumes (gp2, gp3, st1, sc1):**
   - Can only be attached to **a single EC2 instance at a time** within the same Availability Zone. To move it to another instance, it must be detached from instance A (`umount` and `detach-volume`) before attaching to instance B.
2. **EBS Multi-Attach (`io1` / `io2` Provisioned IOPS):**
   - **Yes, it is possible** using **EBS Multi-Attach**.
   - Allows attaching a single `io1` or `io2` volume concurrently to up to 16 AWS Nitro-based EC2 instances within the **same Availability Zone**.
   - *Critical Requirement:* Workloads must use a **cluster-aware filesystem** (such as GFS2, OCFS2) to prevent data corruption from concurrent, uncoordinated writes.
3. **Alternative for Shared Storage:** For cross-instance read-write shared filesystems across multiple AZs, use **Amazon EFS** (Elastic File System).
</details>

<details>
<summary><strong>↳ Follow-up: Is it possible to transfer an EBS volume to a different AWS account?</strong></summary>

**Answer:**
An EBS volume itself cannot be directly moved across AWS accounts, but you transfer it via **Shared EBS Snapshots**:

1. **Step 1: Create Snapshot:** Create a snapshot of the source EBS volume.
2. **Step 2: KMS Key Sharing:** If encrypted with a KMS customer-managed key (CMK), update the KMS key policy in the source account to grant permissions (`kms:CreateGrant`, `kms:DescribeKey`) to the target AWS account ID.
3. **Step 3: Share Snapshot:** Share the snapshot permissions with the target AWS account ID via `aws ec2 modify-snapshot-attribute`.
4. **Step 4: Copy and Create Volume in Target Account:** In the target account, copy the shared snapshot to an account-local snapshot (re-encrypting with target KMS key) and execute `aws ec2 create-volume --snapshot-id <id>` in the desired AZ.
</details>

<details>
<summary><strong>● Have you heard about the latest updates/upgrades to AWS S3?</strong></summary>

**Answer:**
Yes. Significant recent AWS S3 enhancements include:
1. **Amazon S3 Express One Zone:** A new high-performance storage class delivering single-digit millisecond data access (up to 10x faster than S3 Standard) with 50% lower request costs, designed specifically for AI/ML training and financial analytics.
2. **Default S3 Bucket Encryption:** All new objects uploaded to S3 are automatically encrypted with SSE-S3 (AES-256) at zero additional cost.
3. **Automatic Disabling of S3 ACLs (Bucket Owner Enforced):** AWS now disables Access Control Lists (ACLs) by default for new buckets, simplifying access control strictly to IAM and Bucket Policies.
4. **S3 Object Lambda:** Enables adding custom Python code to process and transform data as it is being retrieved from S3 (e.g., dynamic PII redaction or image resizing on-the-fly).
</details>

<details>
<summary><strong>● In an AWS security group or route table, what does specifying 0.0.0.0/0 for a subnet mean?</strong></summary>

**Answer:**
In IPv4 CIDR notation, **`0.0.0.0/0` represents all possible IPv4 addresses (the entire internet / any network)**:

1. **In a Route Table:**
   - It acts as the **Default Route (Gateway of Last Resort)**. Any packet whose destination IP address does not match a more specific route in the routing table will match `0.0.0.0/0`.
   - In a public subnet: `0.0.0.0/0 -> igw-xxx` (routes internet-bound traffic to the Internet Gateway).
   - In a private subnet: `0.0.0.0/0 -> nat-xxx` (routes outbound traffic to the NAT Gateway).
2. **In a Security Group:**
   - **Inbound:** Specifying `0.0.0.0/0` means the port is open to the **entire public internet** (e.g., acceptable for HTTP/S on public load balancers, but a critical security vulnerability if configured on SSH port 22 or database port 5432).
   - **Outbound:** Allows instances to communicate outbound to any IPv4 destination.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● What monitoring tools have you used in your projects?</strong></summary>

**Answer:**
I have worked with a modern observability toolchain:
- **Metrics & Dashboards:** **Prometheus** (time-series metric collection), **Grafana** (dashboards and PromQL visualization), and **Amazon CloudWatch** (AWS infrastructure metrics).
- **APM & Distributed Tracing:** **Datadog APM** and **AWS X-Ray** for transaction tracing, latency breakdowns, and distributed call graphs.
- **Log Management:** **OpenSearch / Elasticsearch** and **Fluent Bit** for centralized log aggregation.
- **Alerting & Incident Management:** **Prometheus Alertmanager** and **PagerDuty** with Slack integration for on-call alerting.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself, describe your roles and responsibilities, and walk through your previous projects?

#### 【 OTHER 】

<details>
<summary><strong>● Have you worked with Apache Kafka and streaming applications using Kafka?</strong></summary>

**Answer:**
Yes. I have supported and managed **Apache Kafka** both self-hosted on Kubernetes (via the **Strimzi Kafka Operator**) and managed via **Amazon MSK (Managed Streaming for Apache Kafka)**:
- **Operational Management:** Configuring topic partitions, replication factors (min in-sync replicas = 2), and retention policies (`retention.ms`, `retention.bytes`).
- **Cluster Sizing & Performance Tuning:** Tuning JVM heap, monitoring broker disk usage, network throughput, and consumer group lag (`kafka_consumergroup_lag`) via Prometheus and Grafana.
- **Security & Access:** Enforcing SASL/SCRAM and TLS encryption for client communication, with IAM authentication policies on Amazon MSK.
- **Disaster Recovery:** Deploying Kafka MirrorMaker 2 (MM2) for cross-cluster active-passive topic replication.
</details>

</details>
</details>

<details open>
<summary><h2>🏢 Streive</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 LINUX 】

<details>
<summary><strong>● Which shell scripting languages/tools are you familiar with?</strong></summary>

**Answer:**
In my day-to-day Linux administration and pipeline engineering:
- **Bash / POSIX Shell:** Writing modular automation scripts, systemd service lifecycle wrappers, container entrypoints (`entrypoint.sh`), and CI/CD step scripts.
- **Core Linux Processing Utilities:** Extensive use of `awk` for columnar data extraction, `sed` for in-place text replacement, `grep`/`ripgrep` for regex pattern matching, `jq` for parsing JSON API payloads, and `xargs` for parallel processing.
- **Linting & Best Practices:** Enforcing **ShellCheck** (`shellcheck -e SC2086 script.sh`) in pre-commit hooks and CI pipelines to prevent quoting bugs, unbound variables (`set -euo pipefail`), and unhandled exit codes.
- **Python (Alternative):** Used whenever scripting requirements involve complex REST APIs, AWS SDK (Boto3), or multi-threaded processing.
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● In your current role, are you responsible for creating CI/CD pipelines from scratch, and do you also handle troubleshooting activities within the CI/CD pipeline?</strong></summary>

**Answer:**
Yes. I own the end-to-end lifecycle of our CI/CD pipelines:
- **Greenfield Pipeline Design:** Authoring declarative `Jenkinsfile` definitions, GitHub Actions reusable workflows, and GitLab CI configurations from scratch. Defining the stage progression (compile, unit test, SonarQube SAST, containerization, vulnerability scanning, and GitOps manifest updates).
- **Daily Operational Troubleshooting:** Diagnosing build breakages (e.g., dependency lockfile discrepancies, flaky integration tests, SonarQube quality gate failures, Docker layer cache poisoning, container registry authentication errors, and agent out-of-memory or out-of-disk events).
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Do you have any experience with cloud migrations, specifically involving AWS EKS?</strong></summary>

**Answer:**
Yes. I have participated in migrating on-premises and VM-based workloads into Amazon EKS:
1. **Containerization & Packaging:** Dockerized legacy Java/Python monoliths and microservices using multi-stage builds, decoupled configurations into Kubernetes ConfigMaps and Secrets, and packaged applications into standardized Helm charts.
2. **Cluster Infrastructure Provisioning:** Provisioned production-grade EKS clusters using Terraform, configuring AWS VPC CNI with custom networking (secondary CIDRs to prevent IP exhaustion), private API endpoints, and Karpenter for dynamic node provisioning.
3. **Data & Workload Migration:** Migrated relational databases to Amazon RDS Multi-AZ using AWS Database Migration Service (DMS). Deployed workloads to EKS and validated staging environments with synthetic load testing.
4. **Traffic Cutover:** Implemented weighted Route 53 DNS routing (shifting 10% -> 50% -> 100% traffic to EKS ALB Ingress) to ensure zero customer disruption during cutover.
</details>

<details>
<summary><strong>↳ Follow-up: Are you currently using AWS EKS in your work?</strong></summary>

**Answer:**
Yes, Amazon EKS is our primary production container orchestration platform. My day-to-day responsibilities include:
- Managing managed node groups and **Karpenter** provisioners for rapid, cost-optimized Spot/On-Demand compute autoscaling.
- Operating the **AWS Load Balancer Controller**, **external-dns**, and **cert-manager** for automated ingress and TLS certificate management.
- Enforcing security policies: IAM Roles for Service Accounts (IRSA / EKS Pod Identity), Kubernetes NetworkPolicies via Calico, and AWS KMS envelope encryption for Kubernetes Secrets.
- Managing GitOps deployments using **Argo CD**.
</details>

#### 【 IAC 】

<details>
<summary><strong>● Are you familiar with Terraform?</strong></summary>

**Answer:**
Yes, Terraform is my primary Infrastructure as Code tool:
- Architecting reusable modules adhering to HashiCorp standard module conventions.
- Managing multi-account, multi-region AWS environments using directory-based state isolation.
- Configuring remote state in S3 with DynamoDB distributed locking and KMS customer-managed encryption.
- Implementing CI/CD automation with Atlantis and GitHub Actions, incorporating static analysis (`tflint`, `checkov`).
</details>

<details>
<summary><strong>● Can you write a Terraform script to provision an AWS VPC with 2 public subnets and 2 private subnets across 2 availability zones, including an internet gateway for the public subnets and a NAT gateway for the private subnets? Also, output the VPC ID, public subnet ID, and private subnet ID.</strong></summary>

**Answer:**
Here is the complete, production-grade Terraform configuration:

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# 1. VPC Definition
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "production-vpc"
  }
}

# Availability Zones Data Source
data "aws_availability_zones" "available" {
  state = "available"
}

# 2. Public Subnets (AZ-a and AZ-b)
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  tags = {
    Name = "public-subnet-1"
  }
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true
  tags = {
    Name = "public-subnet-2"
  }
}

# 3. Private Subnets (AZ-a and AZ-b)
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]
  tags = {
    Name = "private-subnet-1"
  }
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.12.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]
  tags = {
    Name = "private-subnet-2"
  }
}

# 4. Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "main-igw"
  }
}

# 5. Elastic IP and NAT Gateway (Placed in Public Subnet 1)
resource "aws_eip" "nat" {
  domain     = "vpc"
  depends_on = [aws_internet_gateway.igw]
  tags = {
    Name = "nat-eip"
  }
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_1.id
  tags = {
    Name = "main-nat-gateway"
  }
}

# 6. Public Route Table (Routes out to IGW)
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = {
    Name = "public-route-table"
  }
}

resource "aws_route_table_association" "pub_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "pub_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

# 7. Private Route Table (Routes out to NAT Gateway)
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }
  tags = {
    Name = "private-route-table"
  }
}

resource "aws_route_table_association" "priv_1" {
  subnet_id      = aws_subnet.private_1.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "priv_2" {
  subnet_id      = aws_subnet.private_2.id
  route_table_id = aws_route_table.private.id
}

# 8. Required Outputs
output "vpc_id" {
  description = "The ID of the provisioned VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "List of IDs for the public subnets"
  value       = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

output "private_subnet_ids" {
  description = "List of IDs for the private subnets"
  value       = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}
```
</details>

<details>
<summary><strong>● Suppose you inherit legacy infrastructure managed by inconsistent Ansible playbooks and roles. What steps would you take to standardize, refactor, and document the automation while ensuring minimal disruption to active deployments?</strong></summary>

**Answer:**
A disciplined, phased approach to refactoring legacy Ansible automation:

1. **Step 1: Inventory & Codebase Discovery:**
   - Audit all playbooks, custom modules, and static inventory files. Identify hardcoded IP addresses, credentials, and non-idempotent shell commands (`command:`, `shell:` without `creates:`).
   - Run **`ansible-lint`** to generate a baseline scorecard of syntax errors, deprecated modules, and anti-patterns.

2. **Step 2: Modular Role Refactoring (Ansible Galaxy Standard):**
   - Decompose monolithic playbooks into structured **Ansible Roles**:
     `roles/<role_name>/{tasks, handlers, templates, defaults, vars, meta}`.
   - Separate code from configuration: Move environment-specific values to `group_vars/` and role defaults to `defaults/main.yml`.
   - Replace raw shell executions with native declarative Ansible modules (`apt`, `yum`, `systemd`, `template`, `copy`).

3. **Step 3: Test-Driven Validation with Molecule:**
   - Implement **Molecule** with Docker to test each role in isolation against clean OS containers before touching production servers.
   - Run playbooks in dry-run mode against existing staging servers:
     `ansible-playbook -i staging site.yml --check --diff`
     to verify that playbooks report zero unexpected changes.

4. **Step 4: Dynamic Inventory & Secrets Management:**
   - Replace static IP text files with **AWS EC2 Dynamic Inventory (`aws_ec2` plugin)** querying instances by tag.
   - Encrypt plain-text passwords and keys using **Ansible Vault** or retrieve them dynamically from AWS Secrets Manager.

5. **Step 5: Documentation & CI/CD Integration:**
   - Document role prerequisites, variable contracts, and example playbooks in `README.md`. Integrate `ansible-lint` into pre-merge Pull Request pipelines.
</details>

<details>
<summary><strong>● Suppose you need to update an application across hundreds of servers with zero downtime using Ansible. Can you discuss your approach, including the playbook structure, handling of rolling updates, and failure recovery, to minimize service impact?</strong></summary>

**Answer:**
Updating an application across hundreds of servers with zero downtime requires a **batch-rolling orchestration with load balancer health integration**:

1. **Playbook Batch Control (`serial`):**
   - Use the `serial` directive to process servers in controlled batches rather than all at once:
     ```yaml
     - name: Zero-Downtime Rolling Update
       hosts: app_servers
       serial: "10%"            # Updates 10% of servers at a time
       max_fail_percentage: 0   # Aborts immediately if any server in the batch fails
     ```

2. **Lifecycle Execution per Batch (Target Group Integration):**
   ```yaml
       tasks:
       - name: 1. Deregister from AWS Target Group
         amazon.aws.elb_target:
           target_group_arn: "{{ target_group_arn }}"
           target_id: "{{ ansible_ec2_instance_id }}"
           state: absent
         delegate_to: localhost

       - name: 2. Wait for connection draining (deregistration delay)
         ansible.builtin.pause:
           seconds: 30

       - name: 3. Deploy new application binary & config
         ansible.builtin.copy:
           src: /releases/app-v2.1.jar
           dest: /opt/app/app.jar
           mode: '0755'

       - name: 4. Restart Application Service
         ansible.builtin.systemd:
           name: payment-service
           state: restarted

       - name: 5. Local Health Check Verification
         ansible.builtin.uri:
           url: "http://localhost:8080/healthz"
           status_code: 200
         register: result
         until: result.status == 200
         retries: 10
         delay: 3

       - name: 6. Re-register into AWS Target Group
         amazon.aws.elb_target:
           target_group_arn: "{{ target_group_arn }}"
           target_id: "{{ ansible_ec2_instance_id }}"
           state: present
         delegate_to: localhost
   ```

3. **Failure Recovery (`block-rescue`):**
   - Wrap deployment steps in an Ansible `block` with a `rescue` section. If health checks fail on a batch, the rescue block restores the previous binary version, restarts the service, and halts the entire playbook before remaining batches are touched.
</details>

<details>
<summary><strong>● Suppose a critical production environment requires strict compliance and auditability. How would you use Terraform to implement automated policy enforcement and an audit trail for all infrastructure changes? Can you describe your strategy and the key tools/services involved?</strong></summary>

**Answer:**
To achieve strict enterprise compliance (SOC2, PCI-DSS, HIPAA, CIS Benchmarks) with Terraform:

1. **Policy-as-Code (Shift-Left Enforcement):**
   - **Conftest / Open Policy Agent (OPA):** In the CI/CD pipeline, convert `terraform plan -out=tfplan.binary` to JSON and evaluate against Rego security policies:
     - Enforce: S3 buckets *must* have SSE-KMS encryption and public access blocks enabled.
     - Enforce: Security groups *must never* permit `0.0.0.0/0` on ports 22 or 3389.
     - Enforce: All provisioned resources *must* possess mandatory tags (`Environment`, `Owner`, `CostCenter`).
   - If any policy is violated, the pipeline fails the build and blocks the Pull Request.

2. **Immutable Audit Trail:**
   - **Git Versioning:** Every infrastructure change is initiated via Pull Request with peer sign-offs, creating a timestamped, cryptographically signed commit log of *who* approved *what* change and *why*.
   - **Archived Plans:** The pipeline stores the exact binary plan (`tfplan.binary`) as an immutable artifact in an access-restricted S3 bucket with Object Lock enabled.

3. **Runtime Auditing & Drift Guardrails:**
   - **AWS CloudTrail:** Logs every underlying AWS API mutation initiated by the Terraform execution role, recorded with caller identity and session context.
   - **AWS Config:** Continuously monitors resource compliance against AWS Config Rules (e.g., non-compliant EBS volumes without encryption trigger automated remediation).
</details>

<details>
<summary><strong>● Suppose you are tasked with integrating Terraform into a CI/CD pipeline that must deploy infrastructure across multiple cloud providers. What challenges might you face, and how would you design the workflow to ensure reliability, modularity, and secure handling of secrets?</strong></summary>

**Answer:**
1. **Core Architectural Challenges:**
   - **Provider Schema Asymmetry:** Cloud primitives differ significantly (AWS VPCs are regional; GCP VPCs are global; Azure VNets use subnets with attached NSGs). A single "generic" module covering all three is an anti-pattern.
   - **Authentication Complexity:** Handling multiple long-lived credentials across cloud platforms creates massive security risk.
   - **State File Synchronization:** Managing multiple remote backends or locking mechanisms across clouds.

2. **Workflow Architecture Design:**
   - **Directory & State Isolation per Cloud:**
     ```
     terraform/
     ├── aws/environments/{dev, prod}/
     ├── azure/environments/{dev, prod}/
     └── gcp/environments/{dev, prod}/
     ```
     Each cloud workload maintains its own decoupled state file to eliminate blast radius.
   - **Zero-Static Secrets via OIDC Federation:**
     Authenticate CI/CD runners (GitHub Actions / GitLab) using native OpenID Connect (OIDC) to exchange ephemeral JWT tokens for:
     - AWS STS AssumeRoleWithWebIdentity
     - Azure Workload Identity Federation
     - GCP Workload Identity Federation
     *Zero static API keys or secrets are stored in the CI/CD repository.*
   - **Standard Pipeline Progression:**
     `Checkout -> fmt -check -> tflint -> checkov/tfsec -> Speculative Plan -> Manual Approval Gate -> Apply saved plan binary`.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Suppose your organization needs to migrate an application to the cloud, but some third-party integrations rely on static IPs and legacy VPNs. How would you plan the migration to ensure connectivity and minimize disruption for those dependencies?</strong></summary>

**Answer:**
A production migration plan addressing legacy VPNs and static IP dependencies involves:

1. **Static Egress IP Architecture:**
   - Deploy the cloud application in a **Private Subnet**.
   - Route all outbound internet traffic through an **AWS NAT Gateway** (or redundant NAT Gateways across AZs) associated with dedicated, allocated **Elastic IP addresses (EIPs)**.
   - Provide these static Elastic IPs to the third-party partners well in advance to whitelist in their firewalls before cutover.
   - *Alternative (BYOIP):* If the third party cannot update their whitelist, use **AWS Bring Your Own IP (BYOIP)** to onboard the company's existing on-premises public IP range into AWS.

2. **Legacy VPN Connectivity:**
   - Provision an **AWS Site-to-Site VPN** connection between the AWS VPC Virtual Private Gateway (VGW) / Transit Gateway and the third party's customer gateway (IPSec IKEv2 tunnel).
   - Configure pre-shared keys (PSKs) and BGP dynamic routing (or static routes) matching legacy encryption algorithms.

3. **Phased Validation & Cutover:**
   - Establish the VPN and static IP whitelist while the on-premises application is still active.
   - Deploy a test instance in the AWS private subnet to perform synthetic API handshake tests over the VPN and public internet.
   - Execute application cutover via DNS change once third-party communication is 100% verified.
</details>

<details>
<summary><strong>↳ Follow-up: If you are migrating the data using a tool like AWS Snowball, how would you handle integrating the static IPs and legacy VPNs used by third-party dependencies during that migration?</strong></summary>

**Answer:**
When leveraging **AWS Snowball** for petabyte-scale data migration alongside active VPN dependencies:

1. **Decouple Bulk Seed from Real-Time Synchronization:**
   - Snowball is an **offline transport appliance**; it does *not* participate in network routing or VPN connectivity.
   - Order the AWS Snowball Edge device to on-premises, copy the massive historical data baseline (e.g., 100 TB of files/database dumps), and ship it back to AWS for ingest into Amazon S3.
2. **Delta Synchronization over Legacy VPN / Direct Connect:**
   - While Snowball is in physical transit (3–5 days), changes continue occurring on-premises.
   - Use continuous Change Data Capture (CDC) via **AWS Database Migration Service (DMS)** or continuous file syncing (`rsync` / `aws s3 sync`) over the established **AWS Site-to-Site VPN or Direct Connect** to replicate the ongoing delta changes into AWS.
3. **Third-Party Integration Readiness:**
   - The static EIPs and third-party VPN tunnels are already established and idle in AWS.
   - Once the Snowball import completes and the delta sync reaches near-zero lag, schedule a brief maintenance cutover window: pause on-premises writes, let the delta sync catch up, switch DNS to AWS, and immediately route third-party transactions through the pre-tested static EIPs and VPN.
</details>

<details>
<summary><strong>↳ Follow-up: If there is a failure in one region of your deployment, how would you recover from it, and what strategy would you use?</strong></summary>

**Answer:**
For multi-region resilience, we implement a **Warm Standby (or Active-Passive) Multi-Region Disaster Recovery Strategy**:

```
[ Route 53 Application Recovery Controller / Failover Routing ]
        │
        ├── Primary Region (us-east-1: Active 100%)
        │     ├── ALB -> EKS Workloads -> Aurora Primary
        │     └── S3 Primary Bucket
        │           │
        │           │ (Async Replication)
        │           v
        └── Secondary Region (us-west-2: Standby)
              ├── ALB -> EKS Workloads (Scaled to baseline)
              ├── Aurora Cross-Region Read Replica (Promotable)
              └── S3 Replicated Bucket (CRR)
```

1. **Data Layer Replication:**
   - **Amazon Aurora Global Database:** Replicates storage across regions with latency under 1 second.
   - **Amazon S3 Cross-Region Replication (CRR):** Automatically replicates objects to the standby region.
2. **Compute & Ingress:**
   - EKS cluster and core Helm charts are pre-provisioned via Terraform in the secondary region with minimal baseline replica capacity.
3. **Automated Failover Execution (DNS Routing):**
   - **Route 53 Application Recovery Controller (ARC)** monitors primary health checks.
   - If a major regional failure occurs:
     1. Trigger automated failover routing shifting 100% DNS traffic to the secondary region ALB.
     2. Promote the Aurora cross-region replica to standalone write-capable primary database (`aws rds promote-read-replica`).
     3. Trigger Karpenter / HPA to rapidly scale EKS pod replicas in the secondary region to absorb full production load.
   - Target SLA: **RPO < 1 minute, RTO < 10 minutes**.
</details>

<details>
<summary><strong>● Are you familiar with Google Cloud Platform (GCP)?</strong></summary>

**Answer:**
Yes. I have working architectural knowledge of Google Cloud Platform:
- **Compute & Orchestration:** Google Kubernetes Engine (GKE) — recognized for best-in-class Kubernetes management, GKE Autopilot, and fast node provisioning.
- **Networking:** GCP's unique **Global VPC** model (subnets span regions under a single global network), Cloud Interconnect, and Cloud Load Balancing (single global anycast IP).
- **Identity & Storage:** Google Cloud IAM (Service Accounts with Workload Identity), Cloud Storage (GCS), and BigQuery.
- **IaC:** Provisioning GCP resources using Terraform's `hashicorp/google` provider.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● Which monitoring tools are you familiar with?</strong></summary>

**Answer:**
My monitoring and observability stack includes:
- **Metrics Collection & Querying:** **Prometheus** (kube-prometheus-stack, PromQL, Alertmanager).
- **Visualization:** **Grafana** (building custom executive and operational dashboards, tracking SRE Golden Signals).
- **Cloud Infrastructure Monitoring:** **Amazon CloudWatch** (metrics, log insights, alarms).
- **Application Performance Monitoring (APM):** **Datadog APM** and **Dynatrace** (distributed tracing, code-level bottleneck identification, database query profiling).
- **Log Aggregation:** **OpenSearch / Elasticsearch** paired with **Fluent Bit** DaemonSets.
- **Incident Escalation:** **PagerDuty** with automated alert deduplication and on-call escalation schedules.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Suppose you are tasked with migrating a legacy database that has a high transaction volume to a cloud-based solution. What strategy would you use to ensure data integrity and minimize business disruption during the migration?</strong></summary>

**Answer:**
Migrating a high-throughput, mission-critical production database requires an **Online Zero-Downtime Migration Pattern** using Change Data Capture (CDC):

```
[ On-Premise Legacy DB ] (Active OLTP)
         │
         ├── 1. Schema Migration (AWS SCT)
         │
         ├── 2. Initial Full-Load Seed
         │
         ├── 3. Continuous CDC Stream (AWS DMS Replication Instance)
         │           │
         │           v
         └──> [ Target Cloud DB: Amazon Aurora Multi-AZ ] (In Sync)
                     │
                     └── 4. Switch App Writes (2-min Cutover)
```

1. **Phase 1: Planning & Schema Conversion:**
   - Use **AWS Schema Conversion Tool (SCT)** to convert database schemas, stored procedures, and triggers to the target cloud database (e.g., Oracle/SQL Server to PostgreSQL), resolving incompatibilities beforehand.
2. **Phase 2: Full Load + Change Data Capture (CDC):**
   - Deploy an **AWS Database Migration Service (DMS)** replication instance.
   - Configure a migration task with **Full Load + Ongoing Replication (CDC)**.
   - DMS extracts a snapshot of all data without locking source tables, loads it into Amazon Aurora, and continuously streams all ongoing INSERT/UPDATE/DELETE transactions from the source database transaction logs.
3. **Phase 3: Data Integrity Validation:**
   - Enable **AWS DMS Data Validation** to continuously compare source and target records, reporting discrepancies or data type truncations.
   - Maintain continuous replication until CDC lag drops to near zero seconds.
4. **Phase 4: Read Traffic Migration (Canary):**
   - Point read-heavy reporting queries to the new cloud Aurora read replicas to validate production read query compatibility.
5. **Phase 5: Maintenance Window Cutover (Near-Zero Downtime):**
   - Schedule a 5-minute maintenance window.
   - Place legacy source DB in read-only mode to flush all final transactions.
   - Wait for DMS replication lag to reach exactly 0.
   - Update application configuration (DNS CNAME or SSM Parameter) to point to the Amazon Aurora Cluster Endpoint.
   - Re-enable application traffic on the cloud database.
</details>

</details>
</details>

<details open>
<summary><h2>🏢 NTT Data</h2></summary>

<details open>
<summary><h3>Manager</h3></summary>

#### 【 LINUX 】

<details>
<summary><strong>● What is your experience with scripting, and what kinds of scripts have you written (e.g., shell scripts) in your DevOps work?</strong></summary>

**Answer:**
Scripting is foundational to my daily DevOps work across both **Bash** and **Python**:

- **Bash Scripting:**
  - Container entrypoint lifecycle scripts (`docker-entrypoint.sh`) that dynamically template configuration files using `envsubst` before launching the main process.
  - Automated maintenance cron jobs: disk cleanup scripts pruning Docker dangling layers (`docker system prune`) and archiving rotated logs when partition usage exceeds 85%.
  - Health probe scripts checking socket reachability and database readiness during CI runner boot sequences.
- **Python (Boto3 & Automation):**
  - Automating AWS maintenance: scripts triggering automated AMI backups, cleaning up untagged/unattached EBS volumes to reduce cloud spend, and scanning IAM roles for unused permissions.
  - CI/CD automation: scripts parsing SonarQube API JSON outputs to extract quality gate status and notify team channels via Slack incoming webhooks.
</details>

<details>
<summary><strong>● Can you write a simple shell command/script to find the top running services (processes consuming the most memory or CPU) on a Linux machine?</strong></summary>

**Answer:**
Here are standard, one-liner commands and a clean shell script:

1. **Top 5 Memory-Consuming Processes:**
   ```bash
   ps aux --sort=-%mem | head -n 6
   ```
2. **Top 5 CPU-Consuming Processes:**
   ```bash
   ps aux --sort=-%cpu | head -n 6
   ```

3. **Production Diagnostic Shell Script (`top_processes.sh`):**
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail

   echo "=================================================="
   echo "          TOP 5 CPU-CONSUMING PROCESSES          "
   echo "=================================================="
   ps -eo pid,user,%cpu,%mem,comm --sort=-%cpu | head -n 6

   echo -e "\n=================================================="
   echo "         TOP 5 MEMORY-CONSUMING PROCESSES        "
   echo "=================================================="
   ps -eo pid,user,%mem,%cpu,comm --sort=-%mem | head -n 6
   ```
</details>

<details>
<summary><strong>↳ Follow-up: Can you explain what the 'ps -ef' command does in Linux?</strong></summary>

**Answer:**
The **`ps -ef`** command lists every active process running on the Linux operating system using standard System V (UNIX) syntax:

- It provides an instantaneous snapshot of system process tables, displaying detailed information for all processes across all users and background system daemons.
- Output columns displayed:
  - **`UID`:** User running the process.
  - **`PID`:** Unique Process ID.
  - **`PPID`:** Parent Process ID (who spawned this process).
  - **`C`:** Processor utilization factor for CPU scheduling.
  - **`STIME`:** Starting time/date of the process.
  - **`TTY`:** Controlling terminal (`?` if background daemon).
  - **`TIME`:** Cumulative CPU compute time consumed.
  - **`CMD`:** Full executable command name and command-line arguments.
</details>

<details>
<summary><strong>↳ Follow-up: In the 'ps -ef' command, what do the '-e' and '-f' flags specifically mean?</strong></summary>

**Answer:**
- **`-e` (Select All Processes):** Instructs `ps` to display **every process** running on the entire system (identical to the `-A` flag), including processes belonging to other users, kernel threads, and detached background daemons. Without `-e`, `ps` only shows processes associated with the current user's active terminal session.
- **`-f` (Full Format Listing):** Formats the output with the comprehensive, extended set of column headers (UID, PID, PPID, C, STIME, TTY, TIME, and the complete command string including arguments).
</details>

<details>
<summary><strong>● What Linux command would you use to check whether a specific file already exists in a given folder?</strong></summary>

**Answer:**
1. **Interactive Shell / Single Command:**
   ```bash
   test -f /var/log/app/output.log && echo "File exists" || echo "File does not exist"
   ```
   Or using `ls`:
   ```bash
   ls /var/log/app/output.log 2>/dev/null && echo "Exists"
   ```

2. **In Shell Scripting (`if` Conditional):**
   ```bash
   FILE_PATH="/etc/app/config.json"
   if [ -f "$FILE_PATH" ]; then
       echo "File $FILE_PATH exists."
   else
       echo "File $FILE_PATH not found!" >&2
       exit 1
   fi
   ```
   *Note: `-f` specifically tests that the path exists AND is a regular file. Use `-d` for directories or `-e` for general existence.*
</details>

<details>
<summary><strong>↳ Follow-up: How would you search for a file within subfolders of a directory (for example, searching recursively inside /tmp)?</strong></summary>

**Answer:**
The **`find`** command is the standard Linux utility for recursive directory searching:

1. **Exact Filename Search:**
   ```bash
   find /tmp -type f -name "app.log"
   ```
2. **Case-Insensitive Search with Wildcard:**
   ```bash
   find /tmp -type f -iname "*.log"
   ```
3. **Filter by Size and Modification Time:**
   ```bash
   find /tmp -type f -name "*.tar.gz" -size +50M -mtime -7
   ```
   *(Finds `.tar.gz` files in `/tmp` larger than 50MB modified in the last 7 days).*
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● Can you briefly explain the different stages of a typical DevOps/CI-CD pipeline, the tools used at each stage, and your hands-on experience with those individual steps?</strong></summary>

**Answer:**
A standard enterprise pipeline encompasses seven core stages:

1. **Source Code & Pre-commit:**
   - *Tools:* **Git**, **GitHub / GitLab**, `pre-commit` hooks.
   - *Action:* Branch protection rules, conventional commits, local secret detection (`gitleaks`).
2. **Continuous Integration (Build & Compile):**
   - *Tools:* **Jenkins**, **GitHub Actions**, **Maven / Gradle / npm**.
   - *Action:* Compiling application code, generating binaries, running unit tests.
3. **Static Analysis & Security (SAST & SCA):**
   - *Tools:* **SonarQube**, **Checkstyle**, **OWASP Dependency-Check**, **Snyk**.
   - *Action:* Evaluating code quality, enforcing 80%+ test coverage, scanning for CVEs, halting at Quality Gate.
4. **Containerization & Image Scanning:**
   - *Tools:* **Docker**, **Kaniko**, **Trivy**.
   - *Action:* Multi-stage build producing minimal Distroless images; scanning layers for CRITICAL CVEs.
5. **Artifact Storage:**
   - *Tools:* **Amazon ECR**, **JFrog Artifactory**, **Nexus**.
   - *Action:* Pushing immutable tagged artifacts (`${GIT_COMMIT}`).
6. **Continuous Delivery (Deployment):**
   - *Tools:* **Argo CD**, **Helm**, **Terraform**.
   - *Action:* GitOps-driven deployment to Amazon EKS namespaces with progressive Canary rollouts.
7. **Continuous Monitoring & Telemetry:**
   - *Tools:* **Prometheus**, **Grafana**, **Datadog**, **PagerDuty**.
   - *Action:* Verifying post-deployment health checks, tracking error rates, and alerting on anomalies.
</details>

<details>
<summary><strong>↳ Follow-up: What does 'Jenkins standardization' mean, and what practices/considerations do you follow when setting up a standardized Jenkins pipeline?</strong></summary>

**Answer:**
**Jenkins Standardization** means creating a centralized, reusable, and secure pipeline architecture across an organization so that individual teams do not maintain snowflake `Jenkinsfile` scripts:

1. **Jenkins Shared Libraries (`vars/standardMicroservicePipeline.groovy`):**
   - Encapsulate the entire declarative pipeline into a single shared function. Application repositories maintain a minimal 5-line `Jenkinsfile` calling the shared library.
2. **Version Pinned Library Releases:**
   - Pin application repositories to explicit shared library tags (`@v2.1.0`), preventing breaking pipeline changes from unexpectedly impacting teams.
3. **Immutable Ephemeral Agents (Kubernetes Plugin):**
   - Standardize all execution agents as ephemeral Docker containers running on Kubernetes. Eliminates agent configuration drift and "dirty workspace" issues.
4. **Mandatory Security Baselines:**
   - Embed mandatory SAST (SonarQube) and image vulnerability scanning (Trivy) directly into the shared library steps where developers cannot comment them out.
5. **Centralized Credentials Governance:**
   - Bind credentials via Jenkins Credentials Manager using scoped IDs, or authenticate to AWS using OIDC / IAM Roles rather than storing long-lived access keys.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● What is a Kubernetes Service, and can you explain its types and use cases?</strong></summary>

**Answer:**
A **Kubernetes Service** is an abstraction that defines a logical set of Pods and a consistent policy to access them. Because Pods are ephemeral and constantly receive new IP addresses upon restart or rescheduling, a Service provides a **single, stable IP address (`ClusterIP`) and DNS name** for the lifetime of the application.

1. **`ClusterIP` (Default):**
   - Exposes the Service on an internal, cluster-private IP address.
   - **Use Case:** Internal microservice-to-microservice communication within the cluster. Inaccessible from outside the cluster.
2. **`NodePort`:**
   - Exposes the Service on each Node's IP at a static port allocated from a configured range (default: 30000–32767).
   - **Use Case:** Direct access during testing or integrating with legacy external hardware load balancers.
3. **`LoadBalancer`:**
   - Exposes the Service externally using a cloud provider's managed load balancer (e.g., AWS Network Load Balancer or Classic Load Balancer).
   - Automatically provisions the cloud LB, which routes traffic to the NodePort / Pod IPs.
   - **Use Case:** Production external ingress for TCP/UDP services.
4. **`ExternalName`:**
   - Maps the Service to the contents of the `externalName` field (e.g., `db.company.com`) by returning a CNAME DNS record.
   - **Use Case:** Pointing internal pods to external databases or third-party APIs without proxying traffic through the cluster.
5. **Headless Service (`clusterIP: None`):**
   - Does not allocate a ClusterIP; CoreDNS returns the individual A-records of all matching pods.
   - **Use Case:** StatefulSets (databases, Kafka, ZooKeeper) requiring direct peer-to-peer communication.
</details>

#### 【 IAC 】

<details>
<summary><strong>● Can you describe your experience with Infrastructure as Code (IaC), such as the tools you've used and how you've implemented them?</strong></summary>

**Answer:**
I have extensive production experience implementing Infrastructure as Code as the foundational pillar of cloud automation:

- **Terraform / Terragrunt:**
  - Standardized on Terraform for provisioning multi-tier cloud infrastructure: VPCs, subnets, Transit Gateways, Amazon EKS clusters, RDS Multi-AZ databases, and IAM role hierarchies.
  - Implemented the HashiCorp standard module structure to publish versioned, reusable modules to an internal registry.
  - Configured remote state backends using Amazon S3 with KMS encryption and DynamoDB distributed state locking.
- **Ansible:**
  - Used for OS-level configuration management, host hardening against CIS benchmarks, package installations, and systemd service management on EC2 instances.
- **IaC CI/CD Automation:**
  - Integrated Terraform into automated GitOps pipelines using Atlantis and GitHub Actions, incorporating pre-commit linting (`terraform fmt`, `tflint`), security scanning (`checkov`), speculative plan PR comments, and manual approval gates.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you give a quick summary of your DevOps experience, including the toolsets and technologies you have used throughout your career?

● **Candidate Introduction:** What is your highest level of formal education?

↳ **Candidate Introduction:** Was your M.Tech degree a full-time or part-time program?

↳ **Candidate Introduction:** In which year did you complete your M.Tech degree?

↳ **Candidate Introduction:** What was your M.Tech degree specialization/field of study?

● **Candidate Introduction:** Has TransUnion been your only employer so far in your career?

↳ **Candidate Introduction:** Was your role at TransUnion based in Bangalore?

↳ **Candidate Introduction:** What location are you currently based out of?

● **Candidate Introduction:** What is your current CTC (cost to company/compensation)?

↳ **Candidate Introduction:** Does your current CTC include any variable pay component?

● **Candidate Introduction:** What is your current employment status with TransUnion—have you already resigned, and if so, what is your last working day?

↳ **Candidate Introduction:** Given that you've already resigned and have a fixed last working day, why are you still looking at additional job opportunities?

↳ **Candidate Introduction:** Since you already have a last working day set, do you currently have another job offer in hand?

● **Candidate Introduction:** What is your expected CTC (compensation) for this new role?

</details>
</details>





