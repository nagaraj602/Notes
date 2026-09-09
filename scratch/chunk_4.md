<details open>
<summary><h2>🏢 Grid Dynamics</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 DOCKER 】

<details>
<summary><strong>● Can you explain how you understand Docker images and containers, and the difference between them?</strong></summary>

**Answer:**
In Docker, images and containers represent two distinct lifecycle phases of an application:

1. **Docker Image (Build-time Artifact):**
   - An immutable, read-only, layered template built according to the Open Container Initiative (OCI) image specification.
   - It packages the application binary, runtime environment, system libraries, configuration files, and default metadata (entrypoint, cmd, environment variables).
   - Built in layers using a Union File System (UnionFS / Overlay2). Each instruction in a `Dockerfile` (`RUN`, `COPY`, `ADD`) creates a read-only layer cached by Docker.

2. **Docker Container (Runtime Instance):**
   - An active, running instance instantiated from a Docker image.
   - Adds a thin, ephemeral **read-write layer** (container layer) on top of the immutable image layers. Any file modifications, creations, or deletions are captured in this layer using the Copy-on-Write (CoW) strategy.
   - Isolated from other containers and the host OS using Linux kernel primitives:
     - **Namespaces:** Provide isolation for PID (processes), NET (network interfaces/routing), MNT (mount points), IPC (inter-process communication), UTS (hostnames), and USER (user IDs).
     - **Control Groups (cgroups):** Enforce hardware resource boundaries and metering (CPU limits/shares, memory limits, block I/O, network bandwidth).

**Key Architectural Differences:**
| Feature | Docker Image | Docker Container |
| :--- | :--- | :--- |
| **State** | Static, read-only, immutable | Dynamic, stateful runtime with writable layer |
| **Analogy** | Executable program on disk / Class definition | Running process in RAM / Object instance |
| **Storage** | Layered blob cache in `/var/lib/docker/overlay2` | Thin CoW layer + bound host mounts/volumes |
| **Lifecycle Command** | `docker build`, `docker pull`, `docker push` | `docker run`, `docker start`, `docker stop`, `docker rm` |
</details>

<details>
<summary><strong>↳ Follow-up: How can you reduce the size of a Docker image?</strong></summary>

**Answer:**
Reducing Docker image size improves deployment speed, lowers network transfer costs, and hardens security by shrinking the attack surface. In production, I employ the following techniques:

1. **Leverage Multi-Stage Builds:**
   - Separate the build environment (compilers, build tools, SDKs, dev dependencies) from the minimal runtime environment. Only copy the compiled artifact into the final stage:
   ```dockerfile
   # Build Stage
   FROM golang:1.22-alpine AS builder
   WORKDIR /app
   COPY . .
   RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o api .

   # Production Runtime Stage
   FROM gcr.io/distroless/static-debian12:nonroot
   COPY --from=builder /app/api /api
   USER nonroot:nonroot
   ENTRYPOINT ["/api"]
   ```

2. **Choose Minimal Base Images:**
   - Use **Distroless** (`gcr.io/distroless`), **Alpine Linux** (~5 MB), or `scratch` instead of full distribution images like Ubuntu (~80 MB) or Debian (~120 MB).

3. **Minimize Layer Creation & Clean Caches:**
   - Chain shell commands with `&& \` within a single `RUN` instruction and clear package manager caches in the same layer:
   ```dockerfile
   RUN apt-get update && apt-get install -y --no-install-recommends \
       curl \
       ca-certificates \
       && rm -rf /var/lib/apt/lists/*
   ```

4. **Utilize `.dockerignore`:**
   - Prevent unnecessary files from entering the Docker build context (e.g., `.git`, `node_modules`, `tests`, `docs`, `*.md`, `.env`, temporary logs).

5. **Strip Binaries & Omit Dev Dependencies:**
   - In Go/C++, strip debugging symbols (`-ldflags="-s -w"`).
   - In Node.js, run `npm ci --only=production`. In Python, use `pip install --no-cache-dir -r requirements.txt`.

6. **Image Analysis Tools:**
   - Use `dive` to inspect layer efficiency and identify duplicate or wasted space between image layers.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● How would you explain what Pods and ReplicaSets are in Kubernetes?</strong></summary>

**Answer:**
In Kubernetes architecture:

1. **Pod (Atomic Compute Unit):**
   - The smallest deployable and manageable unit in the Kubernetes object model.
   - A Pod represents a single instance of a running process in the cluster and encapsulates one or more closely coupled containers (such as an application container and a logging sidecar).
   - Containers within the same Pod share:
     - **Network Namespace:** Same IP address and port space; containers communicate via `localhost`.
     - **Storage Volumes:** Shared volumes mounted into container filesystems.
     - **IPC Namespace:** Shared inter-process communication channels.
   - Pods are ephemeral and mortal by design; when they terminate, their IP address is lost.

2. **ReplicaSet (Self-Healing Controller):**
   - A declarative controller whose primary responsibility is to guarantee the availability of a specified number of identical, running Pod replicas at any given time.
   - **How it functions:**
     - Uses a **Label Selector** (`spec.selector.matchLabels`) to identify the Pods it manages.
     - Continuously executes a reconciliation loop comparing the **desired state** (`spec.replicas`) with the **actual state** reported by the Kubernetes API server.
     - If a Pod crashes or its host node dies, the ReplicaSet creates a replacement Pod. If surplus Pods exist, it terminates the excess.
   - **Production Context:** Engineers rarely manage ReplicaSets directly. Instead, we define **Deployments**, which manage ReplicaSets to provide declarative updates, rolling deployments, and rollbacks.
</details>

<details>
<summary><strong>● If a node in a Kubernetes cluster goes down, what happens to the ReplicaSets and Pods that were running on it?</strong></summary>

**Answer:**
When a worker node experiences an outage (hardware failure, kernel panic, network partition), Kubernetes initiates an automated self-healing sequence:

```
[ Node Fails ] 
      │
      ▼ (40s: node-monitor-grace-period)
[ Node Marked NotReady / Unknown ]
      │
      ▼ (node.kubernetes.io/unreachable:NoExecute taint added)
[ Pod Eviction Timer Begins (tolerationSeconds: 300s) ]
      │
      ▼ (Timer expires)
[ Control Plane Marks Pods as 'Terminating' ]
      │
      ▼
[ ReplicaSet Controller Detects: Ready Replicas < Desired ]
      │
      ▼
[ kube-scheduler Places New Pods on Healthy Worker Nodes ]
```

1. **Heartbeat Failure Detection:**
   - The worker node's `kubelet` regularly posts node lease updates (`kube-node-lease` namespace) to the `kube-apiserver`.
   - If updates stop, the control plane's `node-lifecycle-controller` waits for `node-monitor-grace-period` (default: 40 seconds).
   - Once exceeded, the node condition is set to `Ready=Unknown` or `Ready=False`.

2. **Toleration & Eviction Execution:**
   - The node controller taints the failed node with `node.kubernetes.io/unreachable:NoExecute` or `node.kubernetes.io/not-ready:NoExecute`.
   - Pods running on the node evaluate their tolerations. Standard Pods have a default toleration of 300 seconds (5 minutes) for `tolerationSeconds`.
   - When the timer expires, the control plane initiates eviction, marking the affected Pods on the failed node as `Terminating`.

3. **ReplicaSet Reconciliation:**
   - The ReplicaSet controller continuously monitors the cluster state. It notices that the number of healthy, running Pods is below `spec.replicas`.
   - The controller submits new Pod creation requests to the API server.

4. **Rescheduling:**
   - `kube-scheduler` filters out the failed node and schedules the replacement Pods onto healthy surviving nodes with sufficient compute capacity.
   - The original pods on the dead node remain in `Terminating` until the dead node comes back online and its `kubelet` confirms deletion, or an administrator force-deletes them.
</details>

<details>
<summary><strong>● If you have one application that needs to run across a few different environments, how would you prefer to organize this in Kubernetes using namespaces, multiple clusters, or other approaches?</strong></summary>

**Answer:**
In enterprise Kubernetes environments, isolation strategies balance blast radius, security compliance, operational complexity, and cost:

1. **Recommended Enterprise Architecture: Multi-Cluster Isolation (Hard Boundary):**
   - **Production:** Dedicated EKS cluster in a dedicated AWS Production account.
   - **Non-Production (Dev / Staging / QA):** Shared EKS cluster in a Non-Production AWS account, segmented via **Namespaces**.
   - **Why this is preferred:**
     - **Blast Radius Containment:** Cluster-level issues (control plane outages, misconfigured CRDs, resource exhaustion, kernel exploits) cannot impact production.
     - **Security & Compliance:** Hard isolation ensures strict IAM permissions, preventing non-prod workloads from accessing production data or secrets (e.g., PCI-DSS, SOC 2).
     - **Independent Cluster Upgrades:** Kubernetes version upgrades can be tested thoroughly in the non-prod cluster without risking production uptime.

2. **Soft Multi-Tenancy within Clusters (Namespaces):**
   - Within the non-prod cluster, environments are divided by namespaces (`app-dev`, `app-qa`, `app-staging`).
   - Hardened using:
     - **ResourceQuotas & LimitRanges:** Enforce maximum CPU/memory usage per environment to prevent noisy neighbor starvation.
     - **NetworkPolicies:** Block inter-namespace traffic by default, allowing only explicit intra-namespace communication.
     - **RBAC:** Restrict developer write access to `dev` while limiting `staging` deployments to the CI/CD service account.

3. **Configuration Management Strategy (GitOps with Kustomize/Helm):**
   - Use a GitOps repository managed by **Argo CD** with a base/overlay structure using **Kustomize**:
     ```
     k8s-manifests/
     ├── base/
     │   ├── deployment.yaml
     │   └── service.yaml
     └── overlays/
         ├── dev/
         │   ├── kustomization.yaml (replicas: 1, min resources)
         ├── staging/
         │   ├── kustomization.yaml (replicas: 2)
         └── prod/
             ├── kustomization.yaml (replicas: 5, HPA, PDB, affinity)
     ```
</details>

#### 【 IAC 】

<details>
<summary><strong>● Can you describe the typical Terraform workflow and the commands you use at each stage?</strong></summary>

**Answer:**
A production-grade Terraform workflow follows a deterministic, five-phase declarative lifecycle:

```
[ Code: .tf ] ──> [ terraform init ] ──> [ terraform validate / fmt ] 
                                                   │
                                                   ▼
[ terraform destroy ] <── [ terraform apply ] <── [ terraform plan -out=tfplan ]
```

1. **`terraform init` (Initialization Phase):**
   - Initializes the working directory containing Terraform configuration files.
   - Reads backend configuration (e.g., AWS S3 bucket and DynamoDB lock table).
   - Downloads required provider plugins (e.g., `hashicorp/aws`, `hashicorp/kubernetes`) into `.terraform/providers/`.
   - Downloads referenced child modules from Git or Terraform Registry.

2. **`terraform fmt -check` & `terraform validate` (Verification Phase):**
   - `terraform fmt`: Enforces standard HCL canonical formatting across all `.tf` files.
   - `terraform validate`: Verifies syntax, attribute names, provider schema validity, and internal consistency without accessing remote cloud APIs.

3. **`terraform plan -out=tfplan` (Planning Phase):**
   - Performs a read-only dry run.
   - Refreshes current state against real cloud infrastructure via provider APIs.
   - Computes differences between declared code (`.tf`), existing state (`terraform.tfstate`), and live cloud infrastructure.
   - Outputs the exact actions to take (`+ create`, `~ update in-place`, `- destroy`, `- / + replace`).
   - The `-out=tfplan` flag locks the execution plan for deterministic application in CI/CD.

4. **`terraform apply tfplan` (Execution Phase):**
   - Acquires the state lock in DynamoDB to prevent concurrent executions.
   - Executes API calls against cloud providers in topological dependency order.
   - Commits the resulting real-world IDs and metadata into the remote state backend.
   - Releases the state lock.

5. **`terraform destroy` (Teardown Phase):**
   - Generates a plan to remove all managed infrastructure tracked in the state file. Primarily used for ephemeral test environments.
</details>

<details>
<summary><strong>↳ Follow-up: How does Terraform determine what changes (additions or removals) need to be made to your infrastructure when you run a plan?</strong></summary>

**Answer:**
Terraform uses a **Three-Way Reconciliation Algorithm** to compute the execution plan:

1. **Three Inputs:**
   - **Desired State:** Defined in your `.tf` configuration files.
   - **Prior State:** Stored in the `terraform.tfstate` file (last recorded state).
   - **Actual / Live State:** Current reality in the cloud provider, retrieved by querying provider APIs during the `refresh` step of `terraform plan`.

2. **Reconciliation Steps:**
   - **Step 1 (Refresh):** Terraform queries cloud APIs for every resource tracked in the state file. It updates the state in memory to capture any external out-of-band modifications (**drift**).
   - **Step 2 (Comparison):** Terraform compares the Desired State against the Actual State:
     - **Additions (`+ create`):** A resource block exists in `.tf` code but has no corresponding resource in the state/cloud.
     - **Deletions (`- destroy`):** A resource exists in the state/cloud but its resource block was removed from `.tf` code.
     - **Modifications (`~ update in-place`):** Attributes differ between code and live state, and the provider supports in-place updates.
     - **Replacements (`-/+ replace`):** Attributes differ, but the cloud API requires resource recreation (force-new attributes like EC2 `ami` or subnet changes).
</details>

<details>
<summary><strong>↳ Follow-up: Where do you prefer to store the Terraform state file, and why?</strong></summary>

**Answer:**
In production enterprise environments, the state file must **never** be stored locally. I prefer storing it in a remote backend using **AWS S3 with DynamoDB State Locking** (or **Terraform Cloud / Spacelift**):

```hcl
terraform {
  backend "s3" {
    bucket         = "company-terraform-state-prod"
    key            = "networking/vpc/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}
```

**Key Reasons:**
1. **Concurrency Protection (State Locking):** DynamoDB creates a lock entry with `LockID` during active `plan`/`apply` operations. This prevents multiple team members or CI/CD jobs from modifying the same state simultaneously, eliminating race conditions and state file corruption.
2. **Centralized Single Source of Truth:** Ensures team members and automation pipelines always execute against the authoritative, up-to-date infrastructure state.
3. **Data Security & Encryption:**
   - State files contain sensitive plain-text attributes (passwords, private keys, connection strings).
   - S3 enforces server-side encryption with AWS KMS (`SSE-KMS`), bucket policies prohibiting unencrypted uploads, and strict IAM access controls.
4. **Resilience & Versioning:**
   - S3 Object Versioning is enabled on the state bucket, allowing instant rollback to a prior state version if a corrupted state is committed.
</details>

<details>
<summary><strong>● If you needed to organize a Terraform repository to support three different environments (dev, staging, and production), how would you structure it?</strong></summary>

**Answer:**
The industry best-practice pattern uses **Directory-Based Isolation with Reusable Shared Modules**:

```
terraform-infrastructure/
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── eks/
│   └── rds/
└── environments/
    ├── dev/
    │   ├── backend.tf          # Key: "envs/dev/terraform.tfstate"
    │   ├── main.tf             # Calls ../../modules/networking with dev params
    │   ├── variables.tf
    │   └── terraform.tfvars    # instance_type = "t3.medium"
    ├── staging/
    │   ├── backend.tf          # Key: "envs/staging/terraform.tfstate"
    │   ├── main.tf
    │   ├── variables.tf
    │   └── terraform.tfvars    # instance_type = "m6i.large"
    └── prod/
        ├── backend.tf          # Key: "envs/prod/terraform.tfstate"
        ├── main.tf
        ├── variables.tf
        └── terraform.tfvars    # instance_type = "m6i.xlarge", multi_az = true
```

**Why this structure is superior to Terraform Workspaces:**
1. **Isolated State Files:** Each environment maintains a separate `terraform.tfstate`. A corruption or bug in `dev` has zero blast radius on `prod`.
2. **Separate Cloud Credentials:** CI/CD can run `dev` with dev IAM roles and `prod` with production IAM roles.
3. **Variable & Architectural Divergence:** Allows non-prod environments to disable expensive enterprise features (e.g., single-AZ RDS for dev, Multi-AZ with read replicas for prod) cleanly without complex conditional logic.
</details>

<details>
<summary><strong>↳ Follow-up: Would you personally prefer using a single Terraform repository or multiple repositories for managing different environments, and why?</strong></summary>

**Answer:**
I prefer a **Hybrid Approach: A Dedicated Central Repository for Reusable Modules + A Monorepo (or Terragrunt Repo) for Environment Deployments**:

1. **Central Modules Repository (`terraform-aws-modules`):**
   - Contains versioned modules tagged with Git semantic versions (e.g., `v1.2.0`).
   - Enforces automated unit and integration tests (Terratest, tflint, trivy) before releasing tags.

2. **Environment Live Repository (`terraform-live`):**
   - Organizes environments into separated directories (`dev`, `staging`, `prod`).
   - References versioned modules: `source = "git::https://github.com/org/terraform-modules.git//eks?ref=v1.2.0"`.

**Rationale:**
- **Controlled Upgrades:** `dev` can be upgraded to module `v1.3.0` while `prod` remains locked to `v1.2.0`.
- **RBAC & Branch Protection:** In GitHub/GitLab, directory code owners and branch protection rules ensure that modifications to `environments/prod/` require explicit approvals from senior architects and pass stricter CI/CD gates.
</details>

<details>
<summary><strong>↳ Follow-up: How do you handle and store secrets when working with Terraform?</strong></summary>

**Answer:**
Storing secrets in plain text within `.tf` or `.tfvars` files is a critical anti-pattern. Because Terraform stores all resolved variable values in plain text within the `terraform.tfstate` file, secrets must be handled via secure external sources and state hardening:

1. **External Secret Stores (Runtime Data Sources):**
   - Fetch secrets dynamically from **AWS Secrets Manager**, **AWS SSM Parameter Store**, or **HashiCorp Vault**:
   ```hcl
   data "aws_secretsmanager_secret_version" "db_password" {
     secret_id = "prod/rds/mysql/master-password"
   }

   resource "aws_db_instance" "default" {
     password = data.aws_secretsmanager_secret_version.db_password.secret_string
   }
   ```

2. **Environment Variables in CI/CD:**
   - Inject secrets via transient environment variables in secure CI/CD runners:
     `export TF_VAR_db_password="${SECRET_FROM_RUNNER}"`.

3. **Sensitive Flags:**
   - Mark input variables and outputs as `sensitive = true`. This prevents values from printing in CLI console logs, pull request plan outputs, and CI/CD logs:
   ```hcl
   variable "db_password" {
     type      = string
     sensitive = true
   }
   ```

4. **Securing the State File:**
   - Restrict access to the S3 remote backend bucket using IAM least-privilege policies.
   - Enforce customer-managed KMS key encryption (`aws:kms`) on the state bucket so unauthorized entities cannot read raw secret values from the state file.
</details>

<details>
<summary><strong>● Do you have experience working with Ansible or Puppet?</strong></summary>

**Answer:**
Yes, I have extensive production experience with **Ansible** for configuration management, OS hardening, zero-downtime application deployments, and server lifecycle automation across hybrid cloud environments.

My work includes:
- Authoring modular Ansible Roles following the Galaxy directory standard.
- Implementing dynamic EC2 inventory plugins (`amazon.aws.aws_ec2`) to execute playbooks against instances grouped by AWS tags.
- Applying Center for Internet Security (CIS) benchmark baselines across Ubuntu and Amazon Linux AMI fleets.
- Managing secure credentials using Ansible Vault.
</details>

<details>
<summary><strong>↳ Follow-up: Do you know the difference between Ansible and Puppet as configuration management tools?</strong></summary>

**Answer:**
Both are enterprise configuration management tools, but they differ fundamentally in architecture, execution model, and maintenance overhead:

| Feature | Ansible | Puppet |
| :--- | :--- | :--- |
| **Architecture** | **Agentless** (connects via SSH for Linux, WinRM for Windows) | **Agent-based** (requires `puppet-agent` daemon installed on target nodes) |
| **Master Node** | No central master required; can execute from any laptop or CI/CD runner | Requires a dedicated **Puppet Master** server managing catalogs and certificates |
| **Execution Model** | **Push-based** (control machine pushes changes on demand) | **Pull-based** (agents periodically poll Puppet Master, default every 30 mins) |
| **Configuration Language**| Human-readable **YAML** (Playbooks) | Proprietary declarative **Ruby-like DSL** (Puppet Manifests) |
| **State & Ordering** | Sequential top-to-bottom task execution | Compiles a directed acyclic graph (DAG); dependencies resolved via metaparameters (`before`, `require`) |
| **Operational Overhead** | Minimal; requires only Python and SSH on target | High; requires agent installation, SSL cert signing, master scaling |
</details>

<details>
<summary><strong>↳ Follow-up: If a project uses both Terraform and Ansible, what responsibilities would each tool handle?</strong></summary>

**Answer:**
In modern enterprise DevOps, we enforce a strict separation of concerns: **Terraform manages the Infrastructure (Day 0), while Ansible manages Configuration and OS State (Day 1 / Day 2)**.

```
[ Terraform ] ──> Provisions: VPC, Subnets, Security Groups, ALB, RDS, EC2
       │
       ▼ (Tags instances: Environment=prod, Role=web)
[ Ansible ]   ──> Hardens OS, Installs Packages, Configures Services, Deploys Apps
```

1. **Terraform Responsibilities (Infrastructure Provisioning):**
   - Creates cloud foundation: VPCs, subnets, route tables, internet gateways, security groups.
   - Provisions compute and platform services: EC2 instances, EBS volumes, Load Balancers, RDS databases, IAM roles, S3 buckets.
   - Tags resources with metadata (e.g., `Role = webserver`, `Env = prod`).

2. **Ansible Responsibilities (Configuration Management):**
   - Connects to instances discovered dynamically via the `aws_ec2` inventory plugin.
   - Performs OS hardening (CIS benchmarks, kernel parameter tuning in `/etc/sysctl.conf`, disabling root SSH).
   - Installs and configures system packages, web servers (Nginx/Apache), log shippers (Fluent Bit), and monitoring agents (Datadog/Node Exporter).
   - Manages application configurations, systemd service files, and user/group access.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Can you explain what AWS IAM (Identity and Access Management) is and describe its main components?</strong></summary>

**Answer:**
**AWS IAM** is a foundational identity and access control web service that securely manages authentication (who can access) and authorization (what actions they can perform) across all AWS services and resources.

**Main Components:**
1. **IAM Users:** Long-term identities representing a person or interactive service requiring access to AWS. Authenticates via console password or programmatic Access Key ID / Secret Access Key.
2. **IAM Groups:** Collections of IAM users. Permissions applied to a group automatically apply to all users inside it, simplifying bulk administrative operations.
3. **IAM Roles:** An identity with no permanent credentials. Assumed temporarily by trusted entities (IAM users, EC2 instances, AWS Lambda functions, or external SAML/OIDC federated identities) via the AWS Security Token Service (STS) to receive short-lived credentials.
4. **IAM Policies:** Formal JSON documents defining fine-grained permission boundaries. Contains statements with:
   - `Effect`: `Allow` or `Deny` (explicit Deny always overrides Allow).
   - `Action`: API calls (e.g., `s3:GetObject`, `ec2:RunInstances`).
   - `Resource`: Target ARNs (e.g., `arn:aws:s3:::my-bucket/*`).
   - `Condition`: Contextual constraints (e.g., enforce MFA, restrict to specific IP ranges, enforce TLS version).
5. **Instance Profile:** A container that passes an IAM role to an Amazon EC2 instance at launch.
</details>

<details>
<summary><strong>↳ Follow-up: If you have an EC2 instance that needs access to an S3 bucket, which IAM component would you use to grant that access, and what permissions would you configure?</strong></summary>

**Answer:**
In production, you must **never** hardcode IAM user access keys inside an EC2 instance. Instead, use an **IAM Role attached via an EC2 Instance Profile**.

1. **Architecture & Flow:**
   - Create an IAM Role with an EC2 trust policy allowing `ec2.amazonaws.com` to call `sts:AssumeRole`.
   - Attach an IAM Policy granting least-privilege permissions to the target S3 bucket.
   - Attach the role to the EC2 instance profile.
   - The instance's AWS SDK or CLI automatically queries the Instance Metadata Service (IMDSv2 at `169.254.169.254`) to fetch short-lived temporary security credentials that rotate automatically.

2. **Least-Privilege Policy Configuration:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "ListBucketContents",
         "Effect": "Allow",
         "Action": ["s3:ListBucket"],
         "Resource": ["arn:aws:s3:::production-app-data"]
       },
       {
         "Sid": "ReadWriteBucketObjects",
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:DeleteObject"
         ],
         "Resource": ["arn:aws:s3:::production-app-data/*"]
       }
     ]
   }
   ```
</details>

<details>
<summary><strong>● How would you decide which EC2 instance type to use for a given workload?</strong></summary>

**Answer:**
Selecting the optimal EC2 instance type requires profiling application resource bottlenecks across compute, memory, storage I/O, and networking:

1. **Workload Classification by Family:**
   - **General Purpose (`M7g`, `M6i`, `T4g`):** Balanced CPU-to-memory ratio (1:4). Ideal for microservices, standard web applications, build runners, and non-production environments.
   - **Compute Optimized (`C7g`, `C6i`):** High CPU-to-memory ratio (1:2). Ideal for batch processing, video encoding, gaming servers, high-performance web servers, and distributed ML inference.
   - **Memory Optimized (`R7g`, `R6i`, `X2gd`):** High memory-to-CPU ratio (1:8). Essential for in-memory caches (Redis/Memcached), relational databases (PostgreSQL/MySQL), and big data processing (Apache Spark).
   - **Storage Optimized (`I4i`, `Im4gn`):** Attached high-throughput, low-latency NVMe SSD storage. Ideal for NoSQL databases (Cassandra, MongoDB) and distributed logging (Elasticsearch/OpenSearch).
   - **Accelerated Computing (`P5`, `G5`):** Hardware GPU/ASIC acceleration for deep learning training, LLM serving, and 3D rendering.

2. **Architecture Consideration (AWS Graviton vs. x86):**
   - Adopt **AWS Graviton3/Graviton4** (ARM64 `g` series) by default. Graviton provides up to 25–40% better price-performance compared to comparable x86 Intel/AMD instances.

3. **Data-Driven Optimization:**
   - Launch with conservative estimates, run representative load tests (k6, JMeter), and utilize **AWS Compute Optimizer** and CloudWatch metrics to right-size instances based on real-world memory and CPU utilization.
</details>

<details>
<summary><strong>● Suppose you have an EC2 instance running a web server application, and it's receiving traffic from many clients. During load spikes, the instance becomes unable to handle requests and the service returns errors. What would you do to troubleshoot and improve this situation?</strong></summary>

**Answer:**
A structured troubleshooting and architectural mitigation approach:

1. **Immediate Troubleshooting & Triage:**
   - **System Resource Check:** SSH / SSM into the instance and run `top`, `htop`, `vmstat 1`, and `iostat -xz 1` to identify whether CPU, memory, disk I/O, or thread limits are exhausted.
   - **Application & Server Logs:** Check web server error logs (`/var/log/nginx/error.log`) for HTTP 502/504 errors or connection pool exhaustion (`worker_connections are not enough`).
   - **Kernel Logs:** Run `dmesg -T | grep -i oom` to see if Linux Out-Of-Memory (OOM) Killer terminated the application process.
   - **Network Sockets:** Run `ss -s` or `netstat -ant | grep SYN_RECV` to identify SYN flood issues or TCP connection backlog exhaustion.

2. **Immediate Remediation:**
   - Temporarily scale up the instance size (vertical scaling) to provide compute headroom during the incident.
   - Tune OS and web server connection limits (e.g., increase `somaxconn`, `file-max`, and Nginx worker connections).

3. **Permanent Architectural Improvement (High Availability & Scalability):**
   - Move from a single point of failure to an **Application Load Balancer (ALB)** distributing traffic across an **Auto Scaling Group (ASG)** spanning multiple Availability Zones.
   - Offload static assets to **Amazon CloudFront + S3** to reduce direct hits to the backend web servers.
   - Introduce **Amazon ElastiCache (Redis)** to cache frequent database queries.
</details>

<details>
<summary><strong>↳ Follow-up: If checking system metrics with the 'top' command shows high CPU utilization, what would you do to improve the situation?</strong></summary>

**Answer:**
1. **Identify the Culprit Process:**
   - Press `P` in `top` to sort processes by CPU utilization.
   - Determine if the CPU is consumed by the web server (Nginx/Apache), backend application runtime (Java, Node.js, Python), or a rogue rogue background task.
   - Run `top -H -p <PID>` to inspect individual thread-level CPU consumption.

2. **Immediate Application Tuning:**
   - If application threads are pinned at 100%, collect thread dumps (`jstack` for Java) or run an APM profiler to detect CPU spin-locks, infinite loops, or unindexed database queries causing high serialization overhead.
   - Tune worker processes: Ensure web server worker processes match CPU core count (`worker_processes auto;`).

3. **Infrastructure Scaling:**
   - If the CPU load is legitimate traffic:
     - **Vertical:** Upgrade to a Compute-Optimized instance (e.g., from `t3.large` to `c6i.2xlarge`).
     - **Horizontal:** Trigger automatic scale-out in an Auto Scaling Group by defining a CloudWatch target tracking metric policy (e.g., maintain average CPU at 65%).
</details>

<details>
<summary><strong>↳ Follow-up: If you can no longer scale up the instance's resources because it's already at maximum limits, what would you do next \- for example, would you consider scaling?</strong></summary>

**Answer:**
When vertical scaling reaches physical or economic ceilings, the required architectural pattern is **Horizontal Scaling (Scale Out)**:

1. **Decouple Application State (Make Stateless):**
   - Externalize session storage to an in-memory cluster like **Amazon ElastiCache for Redis**.
   - Move persistent file uploads and media from local EBS storage to **Amazon S3**.
   - Move database processing to a managed **Amazon RDS / Aurora** cluster with read replicas.

2. **Deploy an Auto Scaling Group (ASG) behind a Load Balancer:**
   - Package the stateless web server application into a golden AMI (via Packer) or container image.
   - Create an **Application Load Balancer (ALB)** to distribute incoming client requests across an Auto Scaling Group spanning at least 2–3 Availability Zones.
   - Now the application can dynamically scale from 2 instances to 50+ instances horizontally in response to incoming traffic surges.
</details>

<details>
<summary><strong>↳ Follow-up: What types of scaling do you know about in AWS?</strong></summary>

**Answer:**
AWS provides two primary dimensions of scaling and several policy-driven mechanisms:

1. **Dimensional Scaling:**
   - **Vertical Scaling (Scaling Up / Down):** Increasing or decreasing hardware specifications (vCPUs, RAM, EBS IOPS) of an existing resource (e.g., resizing `t3.medium` to `m6i.4xlarge`). Usually requires an instance stop/start (downtime).
   - **Horizontal Scaling (Scaling Out / In):** Adding or terminating parallel instances or pods to handle variable workload demands with zero downtime.

2. **AWS Auto Scaling Execution Policies:**
   - **Target Tracking Scaling:** Automatically increases or decreases capacity to keep a specific metric at a defined target (e.g., maintain aggregate ASG CPU utilization at 60%, or ALB request count per target at 1000).
   - **Step Scaling:** Adjusts capacity based on predefined step increments and thresholds (e.g., if CPU is between 60% and 80%, add 2 instances; if CPU > 80%, add 5 instances).
   - **Simple Scaling:** Waits for a cooldown period after scaling before evaluating metrics again.
   - **Scheduled Scaling:** Adjusts instance counts at specific dates and times (e.g., scale up on Friday at 8:00 AM before promotional sales).
   - **Predictive Scaling:** Uses machine learning models analyzing historical traffic patterns to forecast future demand and schedule proactive capacity additions ahead of spikes.
</details>

<details>
<summary><strong>↳ Follow-up: When using an Auto Scaling Group, since you can't manually deploy instances the way you would from an AMI directly, what mechanism or template do you use to define instance configuration for the Auto Scaling Group?</strong></summary>

**Answer:**
We use an **EC2 Launch Template** (which has superseded the legacy and deprecated Launch Configuration).

**An EC2 Launch Template defines:**
- **AMI ID:** Base image containing the pre-baked OS and application runtime.
- **Instance Sizing:** Specific instance types or flexible instance weighting across multiple families (e.g., allowing both `c6i.large` and `c7g.large`).
- **Security Groups & Key Pairs:** Network firewall rules and SSH keys.
- **Storage Configuration:** EBS volume sizes, types (`gp3`, `io2`), and encryption settings.
- **IAM Instance Profile:** Grants AWS permissions to instances without static credentials.
- **User Data Script:** Shell script executed by `cloud-init` on first boot to configure environment variables, fetch secrets, and start services.
- **Advanced Options:** Support for Spot instance allocation strategies, Graviton support, T3 unlimited bursting, and template versioning.
</details>

<details>
<summary><strong>↳ Follow-up: If you've deployed multiple instances via an Auto Scaling Group but clients are still only reaching a single instance, what additional component do you need to set up?</strong></summary>

**Answer:**
You need to provision an **Elastic Load Balancer (ELB)**—specifically an **Application Load Balancer (ALB)**—and integrate it with the Auto Scaling Group:

1. **Target Group Association:**
   - Create an ALB Target Group configured with HTTP/HTTPS health checks (e.g., `GET /healthz`).
   - Associate the Target Group directly with the Auto Scaling Group.
   - When the ASG launches an instance, it registers it with the Target Group. When terminating an instance, it initiates **deregistration delay (connection draining)** before shutting it down.

2. **DNS Record Redirection:**
   - Update your domain's DNS in **Amazon Route 53** using an **Alias (A) record** pointing to the ALB's DNS name (`my-alb-12345.us-east-1.elb.amazonaws.com`).
   - Clients resolve the Route 53 record to the ALB's rotating public Anycast IP addresses, and the ALB routes requests evenly across all registered healthy backend EC2 instances.
</details>

<details>
<summary><strong>↳ Follow-up: How would you manage and distribute traffic across multiple EC2 instances?</strong></summary>

**Answer:**
Traffic distribution is managed using an **Application Load Balancer (ALB)** configured with intelligent routing rules:

1. **Routing Algorithms:**
   - **Round Robin:** Sequentially routes requests to each healthy target.
   - **Least Outstanding Requests (LOR):** Routes new requests to the instance processing the fewest active concurrent requests. Highly recommended for workloads with variable processing times.

2. **Health Check Monitoring:**
   - The ALB periodically sends HTTP health check probes to registered targets (e.g., every 15s to `/healthz`).
   - If a target returns non-200 responses or times out for `UnhealthyThresholdCount` times, the ALB automatically removes it from routing rotation until it recovers.

3. **Layer 7 Content-Based Routing:**
   - **Path-based routing:** Route `/api/*` to an API Target Group and `/static/*` to static servers.
   - **Host-based routing:** Route `admin.company.com` to internal instances and `app.company.com` to customer-facing instances.
</details>

<details>
<summary><strong>↳ Follow-up: What are the major types of load balancers available in AWS that you know of?</strong></summary>

**Answer:**
AWS offers four types of Elastic Load Balancers under the ELB umbrella:

1. **Application Load Balancer (ALB) - Layer 7 (HTTP/HTTPS/gRPC):**
   - Inspects application layer payloads.
   - Features: Path/host/query/header routing, TLS/SSL termination with ACM, WebSockets, HTTP/2 and gRPC support, native integration with AWS WAF and Cognito authentication.
   - Best for: Web applications, microservices, and containerized architectures (ECS/EKS).

2. **Network Load Balancer (NLB) - Layer 4 (TCP/UDP/TLS):**
   - Operates at the transport layer with ultra-low latency (sub-millisecond).
   - Capable of scaling to tens of millions of requests per second.
   - Features: Provides a **static Elastic IP** per Availability Zone, preserves client source IP, supports TLS offloading.
   - Best for: Real-time gaming, financial trading systems, IoT protocols, and AWS PrivateLink endpoint services.

3. **Gateway Load Balancer (GWLB) - Layer 3/4:**
   - Simplifies deployment, scaling, and high-availability management of third-party virtual network appliances (firewalls, Intrusion Detection/Prevention Systems).
   - Encapsulates and routes packets using the GENEVE protocol.

4. **Classic Load Balancer (CLB) - Legacy:**
   - Previous generation Layer 4/7 balancer. Deprecated for modern architectures.
</details>

<details>
<summary><strong>↳ Follow-up: Given that you have EC2 instances behind a load balancer and the application works fine, what else would you improve in this architecture to achieve high availability?</strong></summary>

**Answer:**
To achieve true enterprise-grade High Availability (99.99% uptime), I would implement the following architectural enhancements:

1. **Multi-AZ Infrastructure:**
   - Deploy ALB public subnets and backend EC2 private subnets across at least **3 Availability Zones**.
   - Configure ASG `min_size` to ensure enough instances survive the sudden loss of an entire AZ.

2. **Multi-AZ Managed Database:**
   - Migrate relational database workloads to **Amazon Aurora** or **Amazon RDS Multi-AZ** with automated failover to a standby replica in under 60 seconds.

3. **Edge Caching & DDoS Protection:**
   - Position **Amazon CloudFront** in front of the ALB with **AWS Shield Standard** and **AWS WAF** to absorb volumetric DDoS attacks and cache responses globally.

4. **Database Decoupling & In-Memory Caching:**
   - Implement **Amazon ElastiCache for Redis** for session management and read-heavy queries to protect the database from connection spikes.

5. **Disaster Recovery (DR) Readiness:**
   - Replicate S3 buckets across regions using **S3 Cross-Region Replication (CRR)**.
   - Maintain automated Terraform scripts for a warm standby or pilot light deployment in a secondary AWS region.
</details>

<details>
<summary><strong>● What is the difference between a public subnet and a private subnet in a VPC?</strong></summary>

**Answer:**
The distinction lies strictly in their **Route Table associations and routing configurations**:

1. **Public Subnet:**
   - Its associated Route Table has a default route (`0.0.0.0/0`) pointing directly to an **Internet Gateway (IGW)**:
     `0.0.0.0/0 -> igw-xxxxxxxxx`.
   - Instances launched here can receive public IPv4 addresses and can initiate and receive bi-directional connections directly to and from the public internet.
   - Used for: Internet-facing Load Balancers, Bastion hosts / NAT Gateways.

2. **Private Subnet:**
   - Its associated Route Table does **NOT** have a direct route to an Internet Gateway.
   - For outbound internet access (e.g., pulling operating system patches or third-party API calls), its default route points to a **NAT Gateway** located in a public subnet:
     `0.0.0.0/0 -> nat-xxxxxxxxx`.
   - Direct inbound connections from the public internet are blocked at the routing layer.
   - Used for: Backend microservices, application servers, EKS worker nodes, and databases.
</details>

<details>
<summary><strong>● If you have a group of EC2 instances for production and need to create separate development and staging environments, how would you design your VPC architecture to support these three different environments?</strong></summary>

**Answer:**
The industry gold standard recommended by the AWS Well-Architected Framework is a **Multi-Account VPC Architecture**:

```
AWS Organizations
├── Production Account      ──> VPC (CIDR: 10.30.0.0/16) [Prod Workloads]
├── Staging Account         ──> VPC (CIDR: 10.20.0.0/16) [Staging Workloads]
└── Development Account     ──> VPC (CIDR: 10.10.0.0/16) [Dev Workloads]
```

1. **Separate AWS Accounts per Environment:**
   - Provision dedicated AWS accounts for `Dev`, `Staging`, and `Prod` managed under **AWS Organizations**.
   - **Why:** Completely isolates IAM permissions, AWS service quotas, billing attribution, and limits the blast radius of any human or configuration error.

2. **VPC Layout within Each Account:**
   - Assign non-overlapping CIDR blocks to allow seamless inter-VPC connectivity if needed:
     - Dev VPC: `10.10.0.0/16`
     - Staging VPC: `10.20.0.0/16`
     - Prod VPC: `10.30.0.0/16`
   - Implement a standardized 3-tier subnet architecture across 3 Availability Zones:
     - **Public Tier:** Internet-facing ALBs, NAT Gateways.
     - **Private Application Tier:** EC2 backend instances, EKS nodes.
     - **Private Database Tier:** Isolated RDS instances with no internet routing.
</details>

<details>
<summary><strong>↳ Follow-up: Specifically regarding VPC design (not EKS), how would you connect the VPCs across your different environment accounts?</strong></summary>

**Answer:**
In a multi-account environment, the recommended hub-and-spoke networking model uses **AWS Transit Gateway (TGW)**:

1. **Hub-and-Spoke Topology:**
   - Create an AWS Transit Gateway in a dedicated **Network / Core Services AWS Account**.
   - Share the Transit Gateway across all accounts using **AWS Resource Access Manager (RAM)**.
   - Create a VPC Attachment from each environment's VPC (Dev, Staging, Prod) to the central TGW.

2. **Route Table Segmentation (Traffic Isolation):**
   - Create separate TGW Route Tables to strictly enforce isolation:
     - **Non-Prod Route Table:** Associates Dev and Staging VPC attachments. Allows them to access Shared Services (CI/CD tools, logging, artifact repositories), but does **NOT** propagate routes to the Production VPC.
     - **Prod Route Table:** Associates the Prod VPC attachment. It has zero routes to Dev or Staging VPCs, ensuring complete network segmentation.
</details>

<details>
<summary><strong>● Regarding security groups in AWS, can you block a specific IP address using a security group, or not?</strong></summary>

**Answer:**
**No, you cannot explicitly block or deny a specific IP address using a Security Group.**

**Technical Reason:**
- Security Groups operate on a **permissive whitelist model (ALLOW rules only)**.
- Any traffic that does not match an explicit `Allow` rule is implicitly denied by default. There is no `Deny` rule syntax in Security Groups.

**How to Block a Specific IP Address in AWS:**
1. **Network Access Control Lists (NACLs):**
   - NACLs operate at the subnet boundary and support both **ALLOW** and **DENY** rules.
   - Insert an explicit rule with a lower rule number (evaluated first):
     `Rule 50: DENY | IPv4 | 198.51.100.25/32 | All Ports`.
2. **AWS WAF (Web Application Firewall):**
   - If traffic arrives via an Application Load Balancer or CloudFront, create an **IP Set** containing the malicious IP addresses and create a WAF rule with the `Block` action.
</details>

</details>
</details>

<details open>
<summary><h2>🏢 Accenture</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 11-08-2026 09:54 PM*

#### 【 LINUX 】

<details>
<summary><strong>● Do you have any shell scripting experience?</strong></summary>

**Answer:**
Yes, I have extensive production experience with Bash and POSIX shell scripting for system administration, CI/CD pipeline automation, and cloud infrastructure management.

Key areas of expertise include:
- **Resilient Scripting Standards:** Enforcing strict error handling using `set -euo pipefail` to catch unhandled errors, unbound variables, and pipeline failures immediately.
- **Signal & Cleanup Traps:** Implementing `trap cleanup EXIT SIGINT SIGTERM` to ensure temporary files, SSH agent sockets, and background processes are pruned reliably.
- **Automation Tasks:**
  - Automated database backup and S3 upload scripts with KMS encryption.
  - Log rotation and disk space threshold monitoring with Slack/SNS webhook alerting.
  - Parsing JSON payloads using `jq` to orchestrate multi-step AWS CLI workflows.
  - Writing container entrypoint scripts that handle dynamic secret injection and gracefully propagate `SIGTERM` to application processes.
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● Can you walk me through how you use Jenkins for CI/CD in your application, including all the checks and stages involved in the pipeline?</strong></summary>

**Answer:**
I design enterprise Jenkins pipelines using declarative `Jenkinsfile` syntax integrated into a multi-branch Git workflow:

```groovy
pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: maven
    image: maven:3.9-eclipse-temurin-17
    command: ['sleep', '99d']
  - name: trivy
    image: aquasec/trivy:latest
    command: ['sleep', '99d']
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command: ['sleep', '99d']
'''
        }
    }
    stages {
        stage('Checkout & Lint') {
            steps {
                checkout scm
                sh 'mvn spotless:check'
            }
        }
        stage('Unit Tests') {
            steps {
                container('maven') {
                    sh 'mvn clean test'
                }
            }
            post {
                always {
                    junit '**/target/surefire-reports/*.xml'
                }
            }
        }
        stage('SAST & Quality Gate') {
            steps {
                container('maven') {
                    withSonarQubeEnv('SonarQube-Server') {
                        sh 'mvn sonar:sonar -Dsonar.projectKey=order-service'
                    }
                }
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
        stage('Container Vulnerability Scan') {
            steps {
                container('trivy') {
                    sh 'trivy fs --security-checks vuln,config --exit-code 1 --severity CRITICAL .'
                }
            }
        }
        stage('Build & Push Image') {
            steps {
                container('kaniko') {
                    sh '/kaniko/executor --context=dir://. --dockerfile=Dockerfile --destination=123456789012.dkr.ecr.us-east-1.amazonaws.com/order-service:${GIT_COMMIT}'
                }
            }
        }
        stage('Deploy to Staging') {
            steps {
                sh 'git clone https://github.com/org/k8s-gitops.git && cd k8s-gitops'
                sh 'kustomize edit set image order-service=123456789012.dkr.ecr.us-east-1.amazonaws.com/order-service:${GIT_COMMIT}'
                sh 'git commit -am "Update staging image tag to ${GIT_COMMIT}" && git push origin main'
            }
        }
        stage('Production Approval Gate') {
            steps {
                input message: "Approve deployment to Production?", submitter: "devops-leads"
            }
        }
    }
}
```

**Pipeline Stages & Quality Checks:**
1. **Linting & Code Formatting:** Validates compliance with team formatting standards.
2. **Unit Testing & Code Coverage:** Runs JUnit tests and archives test reports.
3. **SAST (SonarQube):** Analyzes code for security vulnerabilities, code smells, and enforces the Quality Gate (>80% coverage, 0 blocker bugs).
4. **SCA & Dependency Check:** Scans libraries for CVEs using Trivy / OWASP Dependency-Check.
5. **Container Build (Kaniko):** Builds OCI container images without requiring insecure Docker-in-Docker (`docker.sock`).
6. **Container Scanning:** Scans the built image for operating system and binary vulnerabilities.
7. **GitOps CD Sync:** Updates the Kubernetes manifest repository, prompting **Argo CD** to sync the deployment.
</details>

<details>
<summary><strong>↳ Follow-up: Which Jenkins agent type are you using in your CI/CD setup?</strong></summary>

**Answer:**
We use **Ephemeral Kubernetes Pod Agents** via the **Jenkins Kubernetes Plugin**.

**How it works:**
- The Jenkins controller does not run builds locally.
- When a pipeline job triggers, the controller calls the Kubernetes API server to spin up a dedicated Pod containing multi-container build environments (e.g., Maven, Node.js, Trivy, Kaniko).
- Once the pipeline execution finishes, the Pod is immediately destroyed.

**Advantages over Static EC2 / VM Agents:**
1. **Zero Resource Idle Costs:** Nodes scale down when no builds run (via Karpenter / Cluster Autoscaler).
2. **Total Build Isolation:** Every build runs in a clean, pristine container environment, preventing workspace pollution.
3. **Horizontal Scalability:** Allows hundreds of concurrent builds without agent queuing bottlenecks.
</details>

<details>
<summary><strong>↳ Follow-up: Where is your Jenkins application configured/hosted — is it on-premise or somewhere else?</strong></summary>

**Answer:**
Our Jenkins infrastructure is hosted natively in the cloud on **AWS (Amazon Web Services)**.

Specifically:
- Deployed inside an enterprise VPC in dedicated private subnets across multiple Availability Zones.
- Accessed securely through an internal Application Load Balancer integrated with our corporate identity provider (Okta via SAML/OIDC) and Route 53 private hosted zones.
</details>

<details>
<summary><strong>↳ Follow-up: Which cluster or cloud environment is Jenkins running in?</strong></summary>

**Answer:**
Jenkins is hosted within a dedicated **Shared Services / Tooling EKS Cluster** on AWS.

This tooling cluster centralizes our core DevOps platforms:
- Jenkins Controller
- SonarQube
- HashiCorp Vault
- Argo CD control planes
- Prometheus / Grafana observability instances

This cluster is connected to our application workload clusters (Dev, Staging, Prod) via **AWS Transit Gateway**.
</details>

<details>
<summary><strong>↳ Follow-up: Is Jenkins running on a separate instance, or is it running inside a Kubernetes cluster?</strong></summary>

**Answer:**
Jenkins runs **inside the Kubernetes cluster (EKS)**, deployed as a StatefulSet using the official Helm chart:
- The Jenkins controller state (`JENKINS_HOME`) is mounted on high-performance persistent storage using an **Amazon EBS volume** (via the AWS EBS CSI driver) backed up with automated Amazon Data Lifecycle Manager (DLM) snapshots.
- Build workloads execute on dynamic ephemeral agent pods scheduled across worker nodes.
</details>

<details>
<summary><strong>↳ Follow-up: Is there a specific reason why Jenkins is run inside the cluster rather than outside it?</strong></summary>

**Answer:**
Running Jenkins inside Kubernetes provides significant operational, economic, and architectural advantages:

1. **Native Dynamic Agent Provisioning:** The controller communicates directly with the local cluster API server via its internal ServiceAccount (`kubernetes.default.svc`), launching and destroying build pods with sub-second latency and zero external network overhead.
2. **Self-Healing & High Availability:** If the Jenkins controller container crashes or its host node suffers hardware failure, the Kubernetes control plane automatically restarts or reschedules it onto a healthy node within seconds, reattaching the persistent EBS volume.
3. **Cost Optimization:** Eliminates dedicated static EC2 agent instances running 24/7. Build agents share the cluster compute pool and leverage Spot instances managed by Karpenter.
4. **Enhanced Security via IRSA:** Jenkins uses **IAM Roles for Service Accounts (IRSA)**. Ephemeral pods receive scoped temporary AWS STS credentials natively without storing static AWS access keys anywhere on disk.
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● After the Docker image is pushed to ECR, how does the application actually consume or pull those images for deployment?</strong></summary>

**Answer:**
The end-to-end image consumption workflow follows GitOps delivery:

```
[ Push to ECR ] ──> [ Update GitOps Repo Tag ] ──> [ Argo CD Detects Drift ]
                                                           │
                                                           ▼
[ containerd pulls image ] <── [ kubelet authenticates ] <── [ EKS Pod Scheduled ]
```

1. **Deployment Trigger:**
   - The CI pipeline pushes the new image: `123456789012.dkr.ecr.us-east-1.amazonaws.com/payment:v2.1.0`.
   - CI updates the image tag in the GitOps deployment repository (`kustomization.yaml`).
   - **Argo CD** detects the Git commit and applies the updated Deployment manifest to the EKS cluster.

2. **Image Pull Authentication:**
   - When the Pod is scheduled onto an EKS worker node, the node's `kubelet` initiates the image pull via the container runtime (`containerd`).
   - Authentication is handled seamlessly by the **Amazon ECR Credential Provider** integrated into `kubelet`. The worker node's IAM Role includes permissions:
     - `ecr:GetAuthorizationToken`
     - `ecr:BatchCheckLayerAvailability`
     - `ecr:GetDownloadUrlForLayer`
     - `ecr:BatchGetImage`
   - `kubelet` fetches a temporary bearer token from ECR and downloads the image layers securely over private AWS network channels without traversing the public internet.
</details>

<details>
<summary><strong>● Have you worked with Docker Swarm clusters?</strong></summary>

**Answer:**
Yes, I have worked with Docker Swarm clusters for orchestrating containerized workloads in environments where a lightweight orchestrator was preferred over the operational complexity of Kubernetes.

Core Swarm concepts managed:
- **Manager Nodes:** Run the Raft consensus algorithm to maintain cluster state, manage task scheduling, and provide service discovery.
- **Worker Nodes:** Execute container tasks assigned by managers.
- **Ingress Routing Mesh:** Multi-node overlay network (using VXLAN) that routes external traffic arriving on any node's exposed port to the appropriate running container task across the cluster.
- **Docker Stack & Service Management:** Deploying multi-container applications declaratively using `docker stack deploy -c docker-compose.yml`.
</details>

<details>
<summary><strong>● If you have hundreds of containers running in a Docker Swarm cluster and need to install/update a server certificate on all of them, what is the best approach to achieve this?</strong></summary>

**Answer:**
In an enterprise Swarm cluster, updating certificates inside hundreds of individual containers is an anti-pattern. The two industry-standard approaches are:

1. **Approach 1 (Recommended Best Practice): Edge TLS Termination at Reverse Proxy:**
   - Terminate SSL/TLS at the ingress edge using an **Application Load Balancer** or a reverse proxy like **Traefik** or **Nginx** running on Swarm manager nodes.
   - The certificate is installed and renewed in a **single location**.
   - Backend containers communicate over the encrypted Swarm overlay network using plain HTTP, completely eliminating the need to distribute certificates across hundreds of backend containers.

2. **Approach 2 (If End-to-End TLS is Mandatory): Docker Swarm Secrets:**
   - Store the certificate as a native Docker Secret:
     `docker secret create app_cert_v2 server.crt`
     `docker secret create app_key_v2 server.key`
   - Update the Swarm service:
     ```bash
     docker service update \
       --secret-rm app_cert_v1 \
       --secret-add source=app_cert_v2,target=/etc/ssl/certs/server.crt \
       --secret-rm app_key_v1 \
       --secret-add source=app_key_v2,target=/etc/ssl/private/server.key \
       my_microservice
     ```
   - Swarm automatically performs an in-memory rolling update across all running tasks without persisting secrets to host disks.
</details>

<details>
<summary><strong>↳ Follow-up: Can you try solving the certificate distribution problem across 100 Docker Swarm containers using a volume mapping approach (e.g., bind mounts)?</strong></summary>

**Answer:**
Using bind mounts to solve this requires placing the certificate on every single host node in the cluster at an identical filesystem path:

1. **Implementation:**
   - Copy the certificate to `/opt/certs/bundle.crt` on all host servers across the cluster (automated via Ansible).
   - In the Swarm Compose file or service definition, configure a bind mount:
     ```yaml
     version: "3.8"
     services:
       web:
         image: my-app:latest
         deploy:
           replicas: 100
         volumes:
           - type: bind
             source: /opt/certs/bundle.crt
             target: /etc/ssl/certs/bundle.crt
             read_only: true
     ```

2. **Evaluation & Drawbacks:**
   - **Configuration Drift:** You must maintain filesystem consistency across all host nodes. If a task is rescheduled onto a new node where the file is missing or outdated, the container fails to start.
   - **Permissions Issues:** UID/GID mismatches between host files and container users can prevent read access.
   - **Operational Overhead:** Rotating the certificate requires an out-of-band host file update across all servers followed by a service reload.
</details>

<details>
<summary><strong>↳ Follow-up: How about using NFS (Network File System) as an approach to share the certificate across all the Docker Swarm containers?</strong></summary>

**Answer:**
Using NFS provides a centralized shared storage model that avoids syncing files to individual host disks:

1. **Implementation:**
   - A central NFS server (or **Amazon EFS**) hosts the certificate directory (`/exports/certs/server.crt`).
   - Define a shared Docker volume backed by the NFS driver in Swarm:
     ```yaml
     version: "3.8"
     services:
       web:
         image: my-app:latest
         deploy:
           replicas: 100
         volumes:
           - cert-volume:/etc/ssl/certs:ro

     volumes:
       cert-volume:
         driver: local
         driver_opts:
           type: nfs
           o: "addr=nfs.internal.corp,rw,nolock,hard,intr"
           device: ":/exports/certs"
     ```

2. **Advantages:**
   - **Single Point of Update:** Replacing the certificate file on the central NFS server instantly updates the file for all 100 containers across all nodes.
   - **Node Agnostic:** New nodes added to the Swarm automatically mount the NFS share with zero local preparation.
</details>

<details>
<summary><strong>↳ Follow-up: Between bind mount and NFS, which do you think is the best approach for sharing the certificate across all the containers?</strong></summary>

**Answer:**
**NFS is significantly better than local bind mounts** for a multi-node Docker Swarm cluster.

**Comparison:**
- **Why NFS wins over Bind Mounts:**
  - Bind mounts violate container portability by creating a tight coupling to individual host node filesystems. If a node is replaced or autoscaled, bind mounts break unless an external tool pre-provisions the certificate.
  - NFS centralizes certificate storage in one location. Updating the certificate on the NFS share propagates immediately to all containers.

**Architectural Caveat:**
- While NFS is superior to bind mounts, **Docker Swarm Secrets** or **Edge Ingress TLS Termination** is still superior to NFS because NFS introduces network I/O latency, a single point of failure (NFS server availability), and stores unencrypted certificates on a shared network drive.
</details>

#### 【 IAC 】

<details>
<summary><strong>↳ Follow-up: Have you worked on automation scripting for deploying applications into a cluster, i.e., scripting the deployment process itself?</strong></summary>

**Answer:**
Yes, I have authored deployment automation scripts across multiple paradigms:

1. **Helm Deployment Wrapper Scripts:**
   - Bash scripts executing automated canary and rolling upgrades with atomic rollbacks:
     ```bash
     helm upgrade --install payment-service ./charts/payment-service \
       --namespace production \
       --values ./charts/payment-service/values-prod.yaml \
       --set image.tag="${GIT_COMMIT}" \
       --atomic \
       --timeout 5m \
       --cleanup-on-fail
     ```

2. **GitOps Automation:**
   - Scripts that update Kustomize overlays in deployment repositories and trigger/validate Argo CD sync operations via the Argo CD CLI:
     ```bash
     argocd app set payment-service --parameter image.tag="${GIT_COMMIT}"
     argocd app sync payment-service --prune
     argocd app wait payment-service --health --timeout 300
     ```
</details>

<details>
<summary><strong>● If we are launching a new application requiring 100 newly-procured servers on AWS, can you walk me through the overall approach to provision all these servers and install the required applications (e.g., Nagios, HTTP server) on them in one automated process?</strong></summary>

**Answer:**
An enterprise automated workflow combines **Terraform for Infrastructure Provisioning**, **Packer for Golden AMIs**, and **Ansible for Configuration Management**:

```
[ Packer ] ──> Bakes Base AMI (Nagios Agent, Security Baseline, CloudWatch)
     │
     ▼
[ Terraform ] ──> Provisions 100 EC2 Instances via Auto Scaling Group
     │
     ▼
[ Ansible ]   ──> Deploys Application Config & Performs Day-1 Service Bootstrapping
```

1. **Step 1: Golden AMI Baking (HashiCorp Packer):**
   - Rather than installing software sequentially on 100 bare servers at launch, pre-bake a hardened AMI using Packer.
   - Pre-installs base packages: Nagios NRPE agent, AWS SSM Agent, CloudWatch agent, common runtime dependencies, and CIS OS hardening.

2. **Step 2: Infrastructure Provisioning (Terraform):**
   - Write Terraform configuration deploying an **EC2 Auto Scaling Group** targeting 100 instances across 3 private subnets:
   ```hcl
   resource "aws_autoscaling_group" "app_fleet" {
     name                = "app-fleet-prod"
     desired_capacity    = 100
     max_size            = 120
     min_size            = 100
     vpc_zone_identifier = var.private_subnet_ids
     target_group_arns   = [aws_lb_target_group.app.arn]

     launch_template {
       id      = aws_launch_template.app_template.id
       version = "$Latest"
     }
   }
   ```
   - Attach IAM Instance Profiles granting SSM access and tag instances: `Role = webserver`, `Env = prod`.

3. **Step 3: Configuration & Service Deployment (Ansible):**
   - Leverage the **AWS Dynamic Inventory Plugin (`amazon.aws.aws_ec2`)** in Ansible to discover all 100 instances by tag.
   - Execute the site playbook with `forks = 50` for high parallel throughput:
     ```bash
     ansible-playbook -i aws_ec2.yaml site.yml -f 50
     ```
   - Playbook roles configure the HTTP server (Nginx), inject certificates, register the node with the central Nagios monitoring server via API, and start the system services.
</details>

<details>
<summary><strong>↳ Follow-up: How do you set up the Ansible control machine so that it can communicate with all 100 target nodes?</strong></summary>

**Answer:**
To configure the Ansible control machine for large-scale cluster orchestration:

1. **Network Placement & Security:**
   - Position the Ansible control node in a private management subnet within the same VPC (or connected via AWS Transit Gateway / VPC Peering).
   - Security Group rule: Target EC2 security groups allow inbound port 22 (or SSM communication) originating strictly from the Ansible control node's security group.

2. **Dynamic Inventory Setup (`aws_ec2.yaml`):**
   ```yaml
   plugin: amazon.aws.aws_ec2
   regions:
     - us-east-1
   filters:
     tag:Role: webserver
     instance-state-name: running
   keyed_groups:
     - key: tags.Environment
       prefix: env
   compose:
     ansible_host: private_ip_address
   ```

3. **Ansible Engine Performance Optimization (`ansible.cfg`):**
   - Tune concurrency and multiplexing:
     ```ini
     [defaults]
     forks = 50
     host_key_checking = False
     gathering = smart
     fact_caching = memory

     [ssh_connection]
     pipelining = True
     ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o PreferredAuthentications=publickey
     ```
</details>

<details>
<summary><strong>↳ Follow-up: Wouldn't you need passwordless authentication set up between the Ansible control machine and the target nodes?</strong></summary>

**Answer:**
Yes, when using SSH as the transport layer, passwordless public-key authentication is mandatory:

1. **Key Generation:**
   - Generate an ED25519 or 4096-bit RSA SSH key pair on the Ansible control machine:
     `ssh-keygen -t ed25519 -f ~/.ssh/ansible_id -C "ansible-control"`

2. **Automated Distribution via Terraform:**
   - In Terraform, register the public key as an AWS Key Pair:
     ```hcl
     resource "aws_key_pair" "ansible_key" {
       key_name   = "ansible-controller-key"
       public_key = file("~/.ssh/ansible_id.pub")
     }
     ```
   - Reference `key_name` in the Launch Template. During EC2 provisioning, AWS `cloud-init` automatically injects this public key into `/home/ec2-user/.ssh/authorized_keys` (or `/home/ubuntu/.ssh/authorized_keys`).

3. **Execution:**
   - Ansible connects seamlessly using the private key configured in `ansible.cfg`:
     `private_key_file = ~/.ssh/ansible_id`.
</details>

<details>
<summary><strong>↳ Follow-up: Between using IAM-based access and passwordless SSH authentication, which is the best approach for enabling Ansible to communicate with the servers?</strong></summary>

**Answer:**
**IAM-based access via AWS Systems Manager (SSM) Session Manager is the modern enterprise best practice**, far superior to passwordless SSH.

**Comparison:**
| Dimension | Passwordless SSH Authentication | IAM-based Access via AWS SSM |
| :--- | :--- | :--- |
| **Port & Ingress Security** | Requires opening **Port 22** in Security Groups | **Zero open inbound ports**; SSM agent communicates outbound via HTTPS (port 443) |
| **Key Lifecycle Management**| Requires generating, distributing, and rotating SSH private keys | **Zero key management**; credentials are short-lived STS tokens managed by AWS |
| **Identity Governance** | OS-level user accounts | Centralized IAM policies, AWS SSO, and MFA enforcement |
| **Audit Logging** | Local `/var/log/secure` logs | Every session and command is logged to **AWS CloudTrail, S3, and CloudWatch** |

**How to use with Ansible:**
Configure the `community.aws.aws_ssm` connection plugin in Ansible. Ansible communicates with all 100 instances over AWS SSM APIs without requiring SSH keys, open port 22, or public IP addresses.
</details>

#### 【 SECURITY 】

<details>
<summary><strong>↳ Follow-up: Do you have any security mechanisms in place to scan container images for vulnerabilities? If asked to introduce a new vulnerability scanning mechanism into the pipeline, how would you implement it?</strong></summary>

**Answer:**
In our DevSecOps workflow, we implement a **Defense-in-Depth Container Security Architecture** covering Build-time, Registry-time, and Run-time:

1. **Pipeline Integration (Shift-Left with Trivy):**
   - In the CI pipeline, add an automated step using **Trivy** immediately after the Docker image build:
   ```bash
   trivy image \
     --severity HIGH,CRITICAL \
     --exit-code 1 \
     --ignore-unfixed \
     --format table \
     "${IMAGE_NAME}:${GIT_COMMIT}"
   ```
   - If any `CRITICAL` or `HIGH` vulnerabilities with available patches are detected, the pipeline exits with code `1` and aborts the build before the image can be pushed to the registry.

2. **Registry-Level Continuous Scanning (Amazon ECR Enhanced Scanning):**
   - Enable **ECR Enhanced Scanning** powered by **Amazon Inspector**.
   - Inspects images continuously against the Common Vulnerabilities and Exposures (CVE) database, alerting if new vulnerabilities emerge in existing images post-push.

3. **Admission Control at Runtime (Kyverno / OPA Gatekeeper):**
   - Deploy an admission webhook in Kubernetes.
   - Enforce policy: Reject any Pod deployment if the container image is not cryptographically signed (via **Cosign**) or if its vulnerability report fails compliance standards.
</details>

<details>
<summary><strong>↳ Follow-up: Have you worked on certificate renewal processes in your past projects?</strong></summary>

**Answer:**
Yes, I have automated TLS certificate lifecycle management across various infrastructure tiers:

1. **Cloud Ingress Tier (AWS ACM):**
   - For domain endpoints on Route 53 pointing to ALBs or CloudFront, we use **AWS Certificate Manager (ACM)**.
   - ACM automates public certificate generation and DNS validation. Certificates renew automatically 60 days before expiration without manual intervention.

2. **Kubernetes Tier (`cert-manager`):**
   - Deployed `cert-manager` controller inside EKS paired with **Let's Encrypt** ACME issuers (DNS-01 challenge via Route 53).
   - Ingress resources declare `tls.secretName`; `cert-manager` automatically requests, issues, and stores renewed certificates in Kubernetes Secrets 30 days prior to expiry.

3. **Linux / OS Tier:**
   - Used `certbot` automated via systemd timers (`certbot.timer`) executing `certbot renew --post-hook "systemctl reload nginx"`.
</details>

<details>
<summary><strong>● Do you know the workflow of certificate signing — for example, self-signed certificates or the Certificate Authority (CA) signing process?</strong></summary>

**Answer:**
The digital certificate signing workflow follows Public Key Infrastructure (PKI) cryptographic standards:

```
[ Server ] ──> Generates Private Key + Public Key
    │
    ▼
[ Create CSR ] ──> Contains Public Key + Subject Info (FQDN, Org) + Signed by Private Key
    │
    ▼
[ Submit to CA ] (DigiCert, Let's Encrypt, or Internal CA)
    │
    ▼
[ CA Verification ] ──> Validates domain control (DNS-01 / HTTP-01 / Email)
    │
    ▼
[ CA Signs Certificate ] ──> CA encrypts CSR hash with CA's Private Key
    │
    ▼
[ Client Verifies ] ──> Browser validates signature using trusted Root CA Public Key
```

1. **Key Generation:**
   - The server creates a cryptographic key pair: a **Private Key** (kept secure on the server) and a **Public Key**.

2. **CSR (Certificate Signing Request) Creation:**
   - The server generates a `.csr` file containing its Public Key, Common Name (FQDN), Subject Alternative Names (SANs), and organization details. This request is signed by the server's Private Key to prove ownership.

3. **CA Validation & Signing:**
   - The CSR is submitted to a trusted **Certificate Authority (CA)**.
   - The CA validates domain ownership (e.g., via DNS TXT record or HTTP challenge).
   - Once validated, the CA hashes the certificate details and encrypts the hash using the **CA's own Private Key**, generating the signed SSL/TLS certificate.

4. **Trust Chain Verification:**
   - The server installs the certificate along with intermediate CA certificates.
   - When a browser connects, it validates the signature chain down to a trusted **Root CA** pre-installed in the browser's operating system trust store.

5. **Self-Signed Certificates (Contrast):**
   - The server signs its own CSR using its own Private Key.
   - There is no external CA trust chain. Browsers reject the connection with an untrusted certificate warning unless the self-signed root is manually installed into client trust stores. Suitable only for local development.
</details>

</details>
</details>

<details open>
<summary><h2>🏢 Wipro</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 KUBERNETES 】

<details>
<summary><strong>● In a Kubernetes cluster, when you need your application to run on a specific number of pods, what is the strategy or mechanism used to achieve that?</strong></summary>

**Answer:**
In Kubernetes, ensuring that an application maintains a specific number of Pod instances is achieved using **declarative workload controllers**—primarily the **Deployment** controller (which manages a **ReplicaSet**) or a **StatefulSet**:

1. **Declarative Specification:**
   - In the manifest, specify the target pod count using the `spec.replicas` field.

2. **Reconciliation Control Loop:**
   - The Kubernetes `kube-controller-manager` runs continuous control loops.
   - The controller queries the current cluster state via the API server and compares it against the declared desired state.
   - If actual Pods < desired replicas (e.g., due to a crashed node or evicted pod), it instructs the API server to create new Pods.
   - If actual Pods > desired replicas, it gracefully terminates excess Pods.
</details>

<details>
<summary><strong>↳ Follow-up: Are you referring to Replicas or ReplicaSets specifically?</strong></summary>

**Answer:**
Both terms are integral to the mechanism, but they represent two different concepts:

- **Replicas:** Represents the **configuration attribute / integer value** (`spec.replicas: 3`) that defines *how many* identical copies of a Pod should be running.
- **ReplicaSet:** Represents the **Kubernetes controller / API object** whose sole responsibility is to *enforce and maintain* that exact number of running Pod replicas.
</details>

<details>
<summary><strong>↳ Follow-up: Which specific Kubernetes option or resource do you use to control the number of pod replicas?</strong></summary>

**Answer:**
1. **Declarative Option:**
   - Inside a **Deployment** (or **StatefulSet**) manifest, set:
     ```yaml
     apiVersion: apps/v1
     kind: Deployment
     metadata:
       name: payment-service
     spec:
       replicas: 5  # <-- Specific option controlling replica count
     ```

2. **Imperative CLI Command:**
   - `kubectl scale deployment payment-service --replicas=5`

3. **Dynamic Autoscaling Resource:**
   - A **HorizontalPodAutoscaler (HPA)** resource dynamically adjusts `spec.replicas` between `minReplicas` and `maxReplicas` based on observed CPU, memory, or custom Prometheus metrics.
</details>

<details>
<summary><strong>↳ Follow-up: What is the difference between a Replica and a ReplicaSet in Kubernetes?</strong></summary>

**Answer:**
- **Replica:** An individual running instance of a Pod that is an identical clone of other pods generated from the same template.
- **ReplicaSet:** The higher-level controller resource. It defines:
  - `replicas`: Desired count.
  - `selector`: Label selector (e.g., `app: payment`) to discover matching Pods.
  - `template`: Pod definition specification used to instantiate new replicas.
</details>

<details>
<summary><strong>● When launching applications in Kubernetes, how do you decide whether to use a StatefulSet or a stateless deployment, based on the use case scenario?</strong></summary>

**Answer:**
The decision is dictated by whether the application requires persistent individual identity and ordered storage bindings:

| Architectural Requirement | Deployment (Stateless) | StatefulSet (Stateful) |
| :--- | :--- | :--- |
| **Pod Identity & Hostname** | Ephemeral, random hash (`app-5d8f76b7-8q2wx`) | Predictable, ordinal index (`db-0`, `db-1`, `db-2`) |
| **Storage Binding** | Shared volume or ephemeral storage; any pod can use any volume | Dedicated volume per pod via `volumeClaimTemplates`; Pod `db-0` always re-attaches to PV `data-db-0` |
| **Scaling & Start Order** | Parallel, non-deterministic startup and teardown | Strict sequential startup (`0 -> 1 -> 2`) and reverse teardown (`2 -> 1 -> 0`) |
| **Network Identity** | ClusterIP routes traffic round-robin to any healthy pod | **Headless Service** (`None`) creates stable DNS A-records per pod (`db-0.db-service.ns.svc.cluster.local`) |
| **Typical Workloads** | Web APIs, Nginx, Node.js, Spring Boot microservices | Databases (PostgreSQL, MongoDB), Kafka brokers, ZooKeeper, Redis Sentinel |
</details>

<details>
<summary><strong>● Given a scenario where your application is running on a specific number of pods and you notice one pod on a particular node keeps restarting, what could be the possible causes, and where would you start your troubleshooting?</strong></summary>

**Answer:**
A systematic, senior-level troubleshooting flow:

1. **Step 1: Check Pod Status & Exit Code:**
   ```bash
   kubectl describe pod <restarting-pod-name> -n <namespace>
   ```
   - Look at `Last State: Terminated`:
     - **Exit Code 137:** Process killed by Linux **OOMKiller** (Out Of Memory). Either container memory limit was exceeded (`limits.memory`), or node ran out of memory.
     - **Exit Code 1:** Unhandled application runtime exception (syntax error, uncaught exception, missing environment variable).
     - **Exit Code 143:** Graceful termination via `SIGTERM` (e.g., failed Liveness Probe).
   - Inspect the **Events** section at the bottom for failed probe warnings, mount failures, or preemption events.

2. **Step 2: Inspect Application Logs:**
   - View logs of the *previous* crashed container instance:
     ```bash
     kubectl logs <restarting-pod-name> -n <namespace> --previous
     ```
   - Look for stack traces, database connection timeouts, or unhandled file-not-found errors right before termination.

3. **Step 3: Check Node-Level Health:**
   - Since the failure is isolated to **one particular node**:
     ```bash
     kubectl describe node <node-name>
     ```
   - Check Node Conditions: Is the node reporting `DiskPressure`, `MemoryPressure`, or `PIDPressure`?
   - SSH/SSM to the node and inspect systemd logs: `journalctl -u kubelet -e` to check if `kubelet` or the container runtime (`containerd`) is experiencing local I/O latency or driver faults.
</details>

<details>
<summary><strong>↳ Follow-up: Can a CrashLoopBackOff state occur on a cluster that is already up and running, not just during initial startup?</strong></summary>

**Answer:**
**Yes, absolutely.** A Pod running stably in production can transition into `CrashLoopBackOff` at any point due to runtime triggers:

1. **Memory Leaks (OOMKilled):** Application gradually leaks heap or native memory over days under sustained traffic until it breaches the cgroup memory limit (`limits.memory`). The Linux kernel terminates it with `Exit Code 137`, and upon restart, it crashes repeatedly if memory pressure persists.
2. **Expired Credentials & Tokens:** An upstream OAuth token, database password, or mTLS certificate expires mid-execution. Background reconnection threads fail, causing the application process to terminate.
3. **External Dependency Failure:** The upstream database, Redis cache, or message broker fails. If the application lacks connection retries and crashes on socket timeout, it enters a restart loop.
4. **Liveness Probe Timeouts under Heavy Load:** During unexpected traffic surges, CPU throttling causes the health check endpoint (`/healthz`) to respond slower than `probe.timeoutSeconds`. Kubelet marks the probe as failed and restarts the container repeatedly.
5. **Disk / Volume Space Exhaustion:** Local temporary directories (`/tmp`) fill up, causing writes to fail and triggering process exit.
</details>

<details>
<summary><strong>↳ Follow-up: Are you saying that when the database pod is not responding to a request, the respective application pod will restart because of this? Is that an accurate statement?</strong></summary>

**Answer:**
**Not automatically—it depends on the application's error handling and how Kubernetes health probes are configured:**

1. **When it DOES cause a restart:**
   - **Poor Application Code:** If the application code has unhandled database connection exceptions that crash PID 1, the container exits, causing `kubelet` to restart it.
   - **Misconfigured Liveness Probe (Anti-Pattern):** If the application's Kubernetes **Liveness Probe** (`/healthz`) queries the database directly, a database outage causes the liveness probe to fail, forcing `kubelet` to kill and restart the healthy application pod in a vicious cycle.

2. **When it DOES NOT cause a restart (Correct Best Practice):**
   - The application handles database errors gracefully (e.g., returns HTTP 503, retries with exponential backoff, or opens a circuit breaker).
   - In Kubernetes, external dependencies must be tied to **Readiness Probes**, **NEVER Liveness Probes**:
     - **Readiness Probe:** If the database is down, the readiness probe fails. Kubernetes removes the Pod from the Service's `EndpointSlice` so it stops receiving client traffic, but **leaves the Pod running** so it can reconnect as soon as the database recovers.
     - **Liveness Probe:** Should only test whether the local container process is responsive (deadlocks, thread hangs).
</details>

<details>
<summary><strong>↳ Follow-up: How and where do you check the logs of a Kubernetes pod when troubleshooting an issue?</strong></summary>

**Answer:**
1. **Via `kubectl` CLI:**
   - Active container logs:
     `kubectl logs <pod-name> -n <namespace>`
   - Stream logs in real time:
     `kubectl logs -f <pod-name> -n <namespace>`
   - Multi-container pods (specify container name):
     `kubectl logs <pod-name> -c <container-name> -n <namespace>`
   - **Crucial for crashed containers:** Inspect logs from the *previous* container instance:
     `kubectl logs <pod-name> -n <namespace> --previous`

2. **Centralized Log Aggregation Platforms (Production Best Practice):**
   - Because ephemeral pod logs are deleted when pods are rescheduled, enterprise environments ship logs to centralized platforms:
     - **Grafana Loki:** Query logs via LogQL in Grafana (`{namespace="prod", app="payment"} |= "error"`).
     - **ELK / OpenSearch:** Query logs shipped via Fluent Bit / Logstash.
     - **AWS CloudWatch / Datadog:** Structured JSON log searching and metric correlation.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● You mentioned you've worked with Grafana. What are the major graphs or dashboards you typically use to monitor a Kubernetes cluster?</strong></summary>

**Answer:**
In production Kubernetes monitoring, we deploy standard dashboards from the **kube-prometheus-stack** supplemented by custom application dashboards:

1. **Kubernetes Cluster Overview Dashboard:**
   - Cluster-wide resource capacity vs. actual utilization (Total CPU and Memory allocated vs. Requests vs. Limits).
   - Node count and cluster health status.
   - Pods by status (`Running`, `Pending`, `Failed`, `CrashLoopBackOff`).

2. **Node Exporter Dashboard (Node Health):**
   - Per-node CPU utilization and system load averages (1m, 5m, 15m).
   - Memory distribution (Used, Cached, Free).
   - Disk space utilization (`node_filesystem_free_bytes`) and Disk I/O latency.
   - Network throughput (Network In/Out bytes and dropped packet counts).

3. **Kubernetes Compute Resources (Workload / Namespace Tier):**
   - CPU and Memory usage per Pod / Deployment compared against `limits` and `requests`.
   - **CPU Throttling Graph:** Tracks `container_cpu_cfs_throttled_periods_total` to identify when containers are starved by CPU cgroup limits.

4. **USE / RED Ingress & Microservice Dashboard:**
   - **Rate:** Requests per second (RPS) handled by the ingress controller.
   - **Errors:** HTTP 4xx client errors and 5xx server errors.
   - **Duration:** Latency distributions (p50, p95, p99 response times).
</details>

<details>
<summary><strong>↳ Follow-up: Have you ever worked on configuring Grafana dashboards yourself?</strong></summary>

**Answer:**
Yes, I build custom dashboards using both the Grafana UI and programmatic **Dashboard-as-Code**:

- **PromQL Query Authoring:** Writing PromQL queries calculating rates and percentiles:
  `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{app="payment"}[5m])) by (le))`
- **Template Variables:** Configuring dynamic dropdowns (`$cluster`, `$namespace`, `$deployment`, `$pod`) using PromQL label queries to allow filtering across environments.
- **Dashboard as Code (GitOps):** Storing dashboard JSON definitions inside Git repositories and managing them as Kubernetes ConfigMaps labeled with `grafana_dashboard: "1"`, which the **Grafana Dashboard Sidecar** automatically discovers and provisions into Grafana.
</details>

<details>
<summary><strong>↳ Follow-up: If a Grafana dashboard is not showing data, what could be the possible reasons?</strong></summary>

**Answer:**
A systematic diagnostic checklist to isolate the failure point:

1. **Time Range & Variable Filter:**
   - The dashboard time picker is set to a window where no data exists (e.g., "Last 5 minutes" when the test was run 2 hours ago).
   - Template variable filters (`$namespace`, `$pod`) are set to empty or non-existent values.

2. **Grafana Data Source Connectivity:**
   - Go to `Administration -> Data sources -> Prometheus` and click **Save & Test**.
   - If it fails, check if the Prometheus Service URL (`http://prometheus-k8s.monitoring.svc:9090`) is unreachable due to DNS resolution failure, network policies, or pod crash.

3. **Prometheus Target Scraping Failure:**
   - Open Prometheus UI (`/targets`).
   - Check if the target scrape endpoint (e.g., `kube-state-metrics`, `node-exporter`) is in the `DOWN` state due to port misconfiguration, path errors (`/metrics`), or firewall rules.

4. **PromQL Metric Name Mismatch:**
   - Metrics were renamed or deprecated following Prometheus / Kubernetes version upgrades (e.g., changes between `container_cpu_usage_seconds_total` and legacy cAdvisor names).
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you briefly describe your technical experience and the different projects you have worked on?

● **Candidate Introduction:** How many total years of professional experience do you have?

<details>
<summary><strong>● Do you have any questions for me?</strong></summary>

**Answer:**
Yes, asking targeted questions demonstrates technical depth and operational leadership. In a senior DevOps/SRE interview, these questions provide valuable insights into engineering maturity:

1. **Deployment Cadence & Delivery Automation:**
   - *"What does your current deployment frequency look like across environments, and what are the main friction points preventing full continuous deployment to production?"*
2. **Observability & On-Call Health:**
   - *"How is on-call rotation structured across engineering teams, how do you mitigate alert fatigue, and what does your blameless postmortem remediation process look like?"*
3. **Platform Engineering vs. Operational Toil:**
   - *"What proportion of your team's engineering capacity is allocated toward platform modernization and developer self-service versus operational maintenance tickets?"*
4. **Immediate Priorities:**
   - *"What is the most critical reliability or infrastructure challenge your team aims for this role to solve in the first 90 days?"*
</details>

#### 【 OTHER 】

<details>
<summary><strong>● Do you have experience with Python coding or Python scripting?</strong></summary>

**Answer:**
Yes, I use Python 3 extensively for cloud automation, custom tooling, and data engineering in DevOps:
- **Cloud Automation via Boto3:** Writing scripts to audit untagged AWS resources, clean up stale EBS snapshots, automate AMI lifecycle rotation, and enforce S3 bucket encryption.
- **REST API Integration:** Building CLI utilities interacting with Jira, GitHub, GitLab, and Jenkins APIs to automate release notes and ticket status transitions.
- **Kubernetes Automation:** Using the official `kubernetes` Python client to interact with cluster resources and write lightweight controllers.
</details>

<details>
<summary><strong>● Can you share your screen and write a Python program that simulates a card game: it should display all 52 cards with their symbols, distribute the deck between 2 players so each gets 13 cards, and ensure no card is repeated?</strong></summary>

**Answer:**
Here is a clean, production-grade Python script implementing the card game simulation:

```python
import random

def simulate_card_game():
    # 1. Define suits with Unicode symbols and ranks
    suits = {
        'Spades': '♠',
        'Hearts': '♥',
        'Diamonds': '♦',
        'Clubs': '♣'
    }
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

    # 2. Build the full deck of 52 unique cards
    deck = [f"{rank}{symbol}" for suit, symbol in suits.items() for rank in ranks]
    
    print(f"=== FULL DECK ({len(deck)} Cards) ===")
    for i in range(0, len(deck), 13):
        print("  ".join(deck[i:i+13]))
    print()

    # 3. Shuffle the deck randomly to simulate a fair deal
    random.shuffle(deck)

    # 4. Deal 13 unique cards to each player
    # Slicing guarantees zero duplicate cards between players
    player_1_hand = deck[0:13]
    player_2_hand = deck[13:26]
    remaining_deck = deck[26:]

    # 5. Display hands
    print(f"=== PLAYER 1 HAND ({len(player_1_hand)} Cards) ===")
    print("  ".join(player_1_hand))
    print()

    print(f"=== PLAYER 2 HAND ({len(player_2_hand)} Cards) ===")
    print("  ".join(player_2_hand))
    print()

    # 6. Verification: Ensure zero card duplication across both hands
    dealt_cards = player_1_hand + player_2_hand
    assert len(dealt_cards) == len(set(dealt_cards)), "Error: Duplicate cards detected!"
    print(f"[Verification] Total dealt cards: {len(dealt_cards)}, Unique cards: {len(set(dealt_cards))} (No duplicates)")

if __name__ == "__main__":
    simulate_card_game()
```
</details>

<details>
<summary><strong>↳ Follow-up: Why does your program's output show each player receiving 26 cards instead of the requested 13 cards each?</strong></summary>

**Answer:**
That issue occurs when the developer divides the 52-card deck evenly in half (`len(deck) // 2 = 26`) instead of dealing 13 cards per player:

- **The Bug:** Slicing `player1 = deck[:26]` and `player2 = deck[26:]` gives each player 26 cards.
- **The Fix:** Explicitly slice 13 cards per player:
  - Player 1: `deck[0:13]` (cards index 0 to 12 = 13 cards)
  - Player 2: `deck[13:26]` (cards index 13 to 25 = 13 cards)
  - Remaining undealt cards in the deck: `deck[26:]` (26 cards remaining).
</details>

<details>
<summary><strong>↳ Follow-up: Can you modify the program to first display the full deck of all 52 cards, and then show how the cards are split between player 1 and player 2?</strong></summary>

**Answer:**
```python
import random

def deal_cards():
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    # Generate 52 unique cards
    full_deck = [f"{r}{s}" for s in suits for r in ranks]
    
    print("=" * 60)
    print("STEP 1: DISPLAYING THE FULL 52-CARD DECK")
    print("=" * 60)
    for i in range(0, len(full_deck), 13):
        print("  ".join(full_deck[i:i+13]))
    
    # Shuffle deck
    shuffled_deck = full_deck.copy()
    random.shuffle(shuffled_deck)
    
    # Split: 13 cards to Player 1, 13 cards to Player 2
    player_1 = shuffled_deck[0:13]
    player_2 = shuffled_deck[13:26]
    remaining = shuffled_deck[26:]
    
    print("\n" + "=" * 60)
    print("STEP 2: DISTRIBUTING 13 CARDS TO EACH PLAYER")
    print("=" * 60)
    print(f"Player 1 ({len(player_1)} cards): {' '.join(player_1)}")
    print(f"Player 2 ({len(player_2)} cards): {' '.join(player_2)}")
    print(f"Cards remaining in deck: {len(remaining)} cards")

if __name__ == "__main__":
    deal_cards()
```
</details>

</details>
</details>

<details open>
<summary><h2>🏢 Mrisoftware</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 LINUX 】

<details>
<summary><strong>● Can you write a script that checks for an environment variable and returns whether it was found or not?</strong></summary>

**Answer:**
Here is an idiomatic Bash script that checks for an environment variable:

```bash
#!/usr/bin/env bash
set -euo pipefail

VAR_NAME="${1:-APP_ENV}"

# Parameter expansion to check if variable is set and non-empty
if [[ -v "${VAR_NAME}" ]]; then
    echo "[SUCCESS] Environment variable '${VAR_NAME}' is set with value: '${!VAR_NAME}'"
    exit 0
else
    echo "[ERROR] Environment variable '${VAR_NAME}' is NOT set."
    exit 1
fi
```

**Alternative Python Script:**
```python
import os
import sys

var_name = sys.argv[1] if len(sys.argv) > 1 else "APP_ENV"
val = os.environ.get(var_name)

if val is not None:
    print(f"[FOUND] {var_name}='{val}'")
else:
    print(f"[NOT FOUND] {var_name} is not set.")
    sys.exit(1)
```
</details>

<details>
<summary><strong>● What kind of scripting knowledge or experience do you have?</strong></summary>

**Answer:**
I have over 6+ years of hands-on scripting experience focusing on infrastructure automation:
- **Bash / Shell Scripting:** Linux administration, automated server bootstrapping (`cloud-init`), log rotation, backup automation, and CI/CD pipeline steps.
- **Python (Boto3, Requests, PyYAML):** AWS automation (auditing resources, auto-remediating non-compliant security groups, managing AMI lifecycle), interacting with REST APIs, writing Kubernetes custom controllers.
- **Declarative Scripting / IaC:** Writing HCL for Terraform, YAML for Ansible Playbooks, Jenkinsfiles (Groovy DSL), and Helm chart templates.
</details>

<details>
<summary><strong>↳ Follow-up: Can you write a shell script that sets a variable and checks whether it is a string or not using an IF-ELSE condition?</strong></summary>

**Answer:**
In Bash, all variables are fundamentally stored as strings. However, we distinguish whether a variable contains **textual string content** versus **pure numeric/integer content** using regular expression matching:

```bash
#!/usr/bin/env bash

# Set test variable (change to "12345" to test integer)
MY_VAR="Production-Cluster-01"

echo "Evaluating variable value: '${MY_VAR}'"

# Regular expression: matches integers (optional leading +/- sign)
if [[ "${MY_VAR}" =~ ^[+-]?[0-9]+$ ]]; then
    echo "Result: '${MY_VAR}' is an INTEGER / NUMERIC value."
else
    echo "Result: '${MY_VAR}' is a NON-NUMERIC STRING value."
fi
```
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● Can you explain the CI/CD pipeline you have worked on?</strong></summary>

**Answer:**
In my recent production environment, I architected a multi-branch GitOps CI/CD workflow:

1. **Source & Pre-Commit:** Developers push feature branches to GitHub; pre-commit hooks validate formatting and scan for committed secrets (`trufflehog`).
2. **CI Trigger (Jenkins on EKS):** GitHub webhook triggers an ephemeral Kubernetes build agent.
3. **Build & Quality Gates:**
   - Compiles application and executes unit tests (`mvn test`).
   - Runs **SonarQube** code analysis; pipeline halts if Quality Gate fails (>80% test coverage, 0 blocker security bugs).
   - Runs **Trivy** filesystem scan for CVEs in third-party libraries.
4. **Container Build & Registry:**
   - Multi-stage Docker build produces a hardened Distroless container image.
   - Pushes image tagged with `${GIT_COMMIT}` to **Amazon ECR**.
5. **Continuous Delivery (GitOps via Argo CD):**
   - Pipeline commits the new image tag to the GitOps Kubernetes repository.
   - **Argo CD** detects drift and initiates an automated Canary rollout via **Argo Rollouts** on the target EKS cluster, validating Prometheus error rates before completing promotion.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● What have you worked with in Kubernetes?</strong></summary>

**Answer:**
My Kubernetes production experience covers both application workload management and cluster platform engineering:
- **Cluster Provisioning:** Deploying and maintaining **Amazon EKS** clusters across multiple AWS accounts using Terraform and Karpenter for dynamic node autoscaling.
- **Workload Management:** Authoring and maintaining Helm charts and Kustomize overlays for Deployments, StatefulSets, DaemonSets, Jobs, and CronJobs.
- **Networking & Ingress:** Configuring **AWS Load Balancer Controller**, Ingress resources, NetworkPolicies for zero-trust microsegmentation, and CoreDNS tuning.
- **Security & RBAC:** Implementing IAM Roles for Service Accounts (IRSA), External Secrets Operator integrated with AWS Secrets Manager, and admission policies using Kyverno.
- **Observability:** Deploying `kube-prometheus-stack` (Prometheus, Alertmanager, Grafana) and shipping logs via Fluent Bit to OpenSearch.
</details>

<details>
<summary><strong>↳ Follow-up: If a Kubernetes pod is stuck in a CrashLoopBackOff state due to dependency issues, how would you debug it?</strong></summary>

**Answer:**
When a Pod crashes due to an upstream dependency failure (e.g., database, message broker, auth service):

1. **Diagnosis:**
   - Check previous logs: `kubectl logs <pod-name> --previous` to identify the connection error (e.g., `Connection refused`, `UnknownHostException`, `timeout connecting to postgres:5432`).
   - Launch an ephemeral debug container to test network reachability:
     ```bash
     kubectl debug <pod-name> -it --image=busybox -- target-container
     nc -zvw3 postgres-service.database.svc.cluster.local 5432
     nslookup postgres-service.database.svc.cluster.local
     ```
   - Verify NetworkPolicies: Ensure no NetworkPolicy is blocking ingress/egress traffic between the application and database namespaces.

2. **Architectural Remediation (Best Practices):**
   - **Implement an InitContainer:** Block the main application container from starting until the dependency is verified reachable:
     ```yaml
     initContainers:
       - name: wait-for-db
         image: busybox:1.36
         command: ['sh', '-c', 'until nc -z -w 2 postgres-service 5432; do echo waiting for db; sleep 2; done']
     ```
   - **Application Resilience:** Implement connection retries with exponential backoff and circuit breaking (e.g., Resilience4j) so the app does not crash PID 1 when dependencies are momentarily unavailable.
   - **Decouple Liveness Probes:** Ensure the liveness probe does **not** check external database connectivity.
</details>

#### 【 IAC 】

<details>
<summary><strong>● Since you have worked with Terraform, what would you do to make your Terraform code more efficient and better organized?</strong></summary>

**Answer:**
To make Terraform production-grade, maintainable, and efficient:

1. **Modular Architecture:**
   - Separate reusable infrastructure components into versioned child modules (VPC, EKS, RDS) and call them with environment-specific parameters.
2. **Directory-Based Environment Isolation:**
   - Separate state files per environment (`environments/dev`, `environments/staging`, `environments/prod`) to avoid large blast radiuses.
3. **Decouple Stacks by Layer (Blast Radius Reduction):**
   - Rather than one monolithic state file managing VPC, EKS, and Databases, split into independent state stacks:
     `01-networking` -> `02-security` -> `03-kubernetes` -> `04-databases`.
4. **Input Validation & Type Constraints:**
   - Enforce explicit types and validation blocks on input variables:
     ```hcl
     variable "environment" {
       type = string
       validation {
         condition     = contains(["dev", "staging", "prod"], var.environment)
         error_message = "Environment must be dev, staging, or prod."
       }
     }
     ```
5. **Static Analysis & Automated Testing:**
   - Integrate `terraform fmt -check`, `tflint`, and security scanners (`tfsec` / `trivy config`) into the CI pipeline.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● What were you using Grafana for in terms of monitoring, and what kind of data were you looking at?</strong></summary>

**Answer:**
We used Grafana as the single pane of glass for real-time telemetry across infrastructure and applications:

1. **Infrastructure Telemetry (Prometheus):**
   - **Cluster Health:** Total node CPU/Memory capacity vs. allocated requests and limits.
   - **Pod Health:** Pod restart rates, OOMKilled counts, and CPU throttling metrics.
   - **Node Resources:** Node filesystem disk capacity, IOPS latency, and network traffic volume.

2. **Application Golden Signals (RED Method):**
   - **Rate:** Incoming HTTP requests per second (RPS).
   - **Errors:** HTTP 4xx and 5xx response error rates.
   - **Duration:** Request latency percentiles (p50, p95, p99).

3. **Log Aggregation (Loki):**
   - Correlating Prometheus metric spikes directly with Loki log streams in the same dashboard window.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● If you were to design a production web application deployed across two environments (UAT and Production) with high availability, secure access, monitoring, and automated deployment with minimum downtime, what components would you include in the architecture?</strong></summary>

**Answer:**
An enterprise cloud architecture incorporating high availability, zero-downtime deployments, and defense-in-depth security:

```
[ Route 53 (Latency Routing / Health Checks) ]
                     │
                     ▼
             [ AWS WAF + CloudFront ]
                     │
                     ▼
          [ Application Load Balancer ] (Multi-AZ Public Subnets)
                     │
                     ▼
      [ Amazon EKS Cluster (Private Subnets across 3 AZs) ]
        ├── Argo Rollouts (Canary Zero-Downtime Deployment)
        ├── Karpenter (Dynamic Node Scaling)
        └── External Secrets Operator (AWS Secrets Manager)
                     │
                     ▼
      [ Amazon Aurora Multi-AZ Cluster (Database Subnets) ]
```

**Architectural Components:**
1. **Multi-Account Segregation:**
   - Dedicated AWS Accounts for UAT and Production under AWS Organizations.
2. **Network & Compute Tier:**
   - VPC across 3 Availability Zones with 3-tier subnets (Public, Private App, Private DB).
   - Compute running on **Amazon EKS** with worker nodes in private subnets, autoscaled via **Karpenter**.
3. **High Availability & Edge Security:**
   - **AWS CloudFront** with **AWS WAF** (blocking SQLi, XSS, rate-limiting) and **ACM SSL/TLS**.
   - Multi-AZ **Application Load Balancer** terminating TLS 1.3.
4. **Data Persistence:**
   - **Amazon Aurora PostgreSQL Multi-AZ** with automated failover and read replicas.
5. **Zero-Downtime Automated Deployments:**
   - **GitOps via Argo CD** paired with **Argo Rollouts**: Performs canary releases (10% traffic routing, Prometheus automated health verification, gradual shift to 100%, automated instant rollback on error threshold breach).
6. **Observability & Alerting:**
   - **kube-prometheus-stack** for metrics, **Grafana Loki** for logs, and **PagerDuty** integration for alerting.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself?

<details>
<summary><strong>● Can you explain a project you have worked on?</strong></summary>

**Answer:**
**Project: Enterprise Cloud Migration and GitOps Modernization to AWS EKS**

- **Situation:** Our organization had legacy monolithic Java applications running on on-premises virtual machines. Deployments were manual, required 3-hour maintenance windows, and experienced frequent configuration drift and downtime.
- **Task:** As Senior DevOps Engineer, I was tasked with architecting a containerized, highly available microservices platform on AWS EKS, establishing automated IaC provisioning, and implementing a zero-downtime GitOps deployment pipeline.
- **Action:**
  1. Built modular **Terraform** code to provision multi-account VPCs, transit gateways, and EKS clusters across 3 Availability Zones.
  2. Containerized the Java applications using multi-stage Docker builds based on Eclipse Temurin Distroless images, shrinking image size from 900MB to 120MB.
  3. Deployed **Argo CD** and **Argo Rollouts** for Canary deployments, integrating Prometheus metrics to automatically abort releases if HTTP 5xx error rates exceeded 0.5%.
  4. Implemented **AWS Secrets Manager** integration via the External Secrets Operator, eliminating static secrets.
  5. Built centralized monitoring dashboards in **Grafana** tracking RED metrics.
- **Result:**
  - Reduced release cycle time from **2 weeks to multiple automated deployments per day**.
  - Achieved **zero-downtime releases** with 99.99% availability.
  - Reduced cloud infrastructure costs by **35%** by migrating non-prod nodes to AWS Graviton and EC2 Spot instances managed by Karpenter.
</details>

</details>
</details>

<details open>
<summary><h2>🏢 R Systems</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 KUBERNETES 】

<details>
<summary><strong>● How much experience do you have working with Kubernetes?</strong></summary>

**Answer:**
I have over 5+ years of hands-on production experience with Kubernetes. My background includes architecting, deploying, securing, and operating enterprise clusters on **Amazon EKS** as well as on-premise clusters bootstrapped via **Kubeadm**.

My focus areas include:
- Cluster autoscaling (Karpenter, HPA, VPA).
- GitOps deployment automation using Argo CD.
- Ingress architecture with AWS Load Balancer Controller.
- Cluster security, RBAC, NetworkPolicies, and IRSA.
- Full observability with Prometheus, Grafana, and Loki.
</details>

<details>
<summary><strong>↳ Follow-up: Which method did you follow to set up your Kubernetes cluster?</strong></summary>

**Answer:**
1. **Production Cloud (AWS EKS):**
   - We use **Terraform** with the battle-tested community module (`terraform-aws-modules/eks/aws`).
   - Provisions the managed control plane, VPC CNI, CoreDNS, kube-proxy, managed node groups, and IAM roles for service accounts (IRSA).
2. **On-Premise / Bare-Metal:**
   - Bootstrapped using **Kubeadm** across Ubuntu servers, configuring containerd as the CRI, Calico for the CNI networking layer, and HAProxy/Keepalived for a multi-master high-availability control plane.
</details>

<details>
<summary><strong>↳ Follow-up: Can you configure or set up a Kubernetes cluster with the help of Grafana?</strong></summary>

**Answer:**
**No, you cannot set up or configure a Kubernetes cluster using Grafana.**

**Technical Clarification:**
- **Grafana** is exclusively a **visualization and observability platform**. It queries data sources (like Prometheus, Loki, CloudWatch) to display metrics, logs, and traces on dashboards.
- To provision a Kubernetes cluster, you must use Infrastructure as Code tools (**Terraform**, **CloudFormation**, **Pulumi**) or cluster bootstrap tools (**Kubeadm**, **kops**, **Rancher**, **EKSctl**).
- Grafana is deployed *after* the cluster exists to monitor its health and workloads.
</details>

<details>
<summary><strong>↳ Follow-up: What is the difference between node affinity and pod affinity in Kubernetes?</strong></summary>

**Answer:**
Both are scheduling constraint mechanisms, but they evaluate different cluster entities:

1. **Node Affinity (Pod-to-Node Relationship):**
   - Constrains which **nodes** a Pod can be scheduled on based on **labels on the Nodes**.
   - *Example:* Schedule this Pod only on nodes labeled with `disktype=ssd` or `topology.kubernetes.io/zone=us-east-1a`.
   - Variants:
     - `requiredDuringSchedulingIgnoredDuringExecution` (Hard rule: Pod will not be scheduled if no matching node exists).
     - `preferredDuringSchedulingIgnoredDuringExecution` (Soft rule: Scheduler tries to match, but schedules elsewhere if unavailable).

2. **Pod Affinity / Pod Anti-Affinity (Pod-to-Pod Relationship):**
   - Constrains which nodes a Pod can be scheduled on based on **labels of other Pods already running on those nodes**.
   - **Pod Affinity:** Place Pod A on the same node/zone as Pod B to minimize network latency (e.g., co-locating a web frontend with a Redis cache).
   - **Pod Anti-Affinity:** Ensure Pod A is *never* co-located on the same node/zone as another replica of Pod A to maximize high availability and prevent single-point node failures.
</details>

<details>
<summary><strong>● Can you write a Kubernetes Deployment YAML manifest for deploying Nginx?</strong></summary>

**Answer:**
Here is a production-ready Kubernetes Deployment manifest for Nginx:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: default
  labels:
    app.kubernetes.io/name: nginx
    app.kubernetes.io/part-of: web-tier
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:1.25-alpine
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 80
              protocol: TCP
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "250m"
              memory: "256Mi"
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
```
</details>

<details>
<summary><strong>↳ Follow-up: In the Nginx Deployment YAML, how would you specify the container port number?</strong></summary>

**Answer:**
The container port is specified under the `spec.template.spec.containers[].ports` array:

```yaml
          ports:
            - name: http           # Descriptive identifier
              containerPort: 80    # Port the container listens on
              protocol: TCP        # Protocol (TCP is default)
```
</details>

#### 【 IAC 】

<details>
<summary><strong>● How much experience do you have working with Terraform?</strong></summary>

**Answer:**
I have over 5+ years of hands-on production experience authoring modular, enterprise Terraform code.

Key proficiencies include:
- Provisioning multi-region AWS architectures (VPC, EKS, RDS, S3, ALB, Route 53, IAM).
- Managing remote backends with S3 and DynamoDB state locking.
- Performing complex state operations (`terraform state mv`, `terraform import`, `moved` blocks).
- Developing CI/CD pipeline automation for Terraform using GitHub Actions and Atlantis.
</details>

<details>
<summary><strong>↳ Follow-up: Can you write the Terraform resource block code to deploy an EC2 instance on AWS?</strong></summary>

**Answer:**
```hcl
resource "aws_instance" "web_server" {
  ami                         = "ami-0c55b159cbfafe1f0" # Amazon Linux 2023
  instance_type               = "t3.medium"
  subnet_id                   = "subnet-0123456789abcdef0"
  vpc_security_group_ids      = ["sg-0123456789abcdef0"]
  associate_public_ip_address = false
  iam_instance_profile        = "web-server-ssm-profile"

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 30
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name        = "web-server-prod"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}
```
</details>

<details>
<summary><strong>↳ Follow-up: How would you modify the Terraform EC2 resource block to use a for_each loop in order to launch 20 instances, each with a different name?</strong></summary>

**Answer:**
Using `for_each` over a map or set provides deterministic resource addressing (e.g., `aws_instance.servers["web-01"]`), preventing the index-shift issues caused by `count`:

```hcl
# Variable defining the 20 instance identifiers and their specific configurations
variable "instance_configs" {
  type = map(object({
    role = string
  }))
  default = {
    "web-01" = { role = "frontend" }
    "web-02" = { role = "frontend" }
    "web-03" = { role = "frontend" }
    # ... up to web-20
    "web-20" = { role = "backend" }
  }
}

resource "aws_instance" "servers" {
  for_each = var.instance_configs

  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t3.medium"
  subnet_id              = "subnet-0123456789abcdef0"
  vpc_security_group_ids = ["sg-0123456789abcdef0"]

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
    encrypted   = true
  }

  tags = {
    Name        = each.key            # Dynamically assigns "web-01", "web-02", etc.
    Role        = each.value.role
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}
```
</details>

<details>
<summary><strong>↳ Follow-up: What is the meaning and purpose of a Terraform variable (tf var)?</strong></summary>

**Answer:**
In Terraform, **Input Variables** (`variable "name" { ... }`) serve as configurable input parameters for modules and configurations:

**Key Purposes:**
1. **Eliminates Hardcoding:** Decouples infrastructure code logic from environment-specific values.
2. **Reusability:** Enables the same Terraform code to be reused across multiple environments (Dev, Staging, Prod) simply by passing different variable values.
3. **Type Safety & Validation:** Enforces strict data types (`string`, `number`, `list`, `map`, `object`) and runtime validation rules.
</details>

<details>
<summary><strong>↳ Follow-up: Is it necessary to define a Terraform variable (tfvars) for this use case, or not?</strong></summary>

**Answer:**
**Strictly speaking, defining a `.tfvars` file is NOT mandatory, but it is best practice:**

- **Why it's not strictly mandatory:** You can declare the variable with a `default` value inside `variables.tf`, or pass values via CLI flags (`-var 'instance_configs=...'`) or environment variables (`TF_VAR_instance_configs=...`).
- **Why it IS recommended in production:** Using environment-specific `.tfvars` files (`dev.tfvars`, `prod.tfvars`) cleanly separates your abstract code logic (`variables.tf`) from environment-specific configuration values, maintaining clean version control and CI/CD promotion workflows.
</details>

<details>
<summary><strong>↳ Follow-up: Which tool did you use to set up the Kubernetes cluster—Ansible or Terraform?</strong></summary>

**Answer:**
We used **Terraform** to provision the Kubernetes cluster on AWS EKS:
- **Terraform** provisions the underlying cloud infrastructure: VPC, subnets, NAT gateways, security groups, IAM roles, EKS control plane, and managed node groups.
- Once Terraform provisions the cluster, **Helm / Argo CD** (or Ansible for bare-metal nodes) takes over to manage in-cluster addons (CoreDNS, metrics-server, AWS VPC CNI, ingress controllers).
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● How much experience do you have working with AWS?</strong></summary>

**Answer:**
I have over 6+ years of production experience architecting, securing, and maintaining AWS cloud infrastructure.

Core competencies include:
- **Compute & Containers:** EC2, Auto Scaling Groups, Launch Templates, EKS, ECS, Lambda.
- **Networking:** VPC architecture, Subnets, Route Tables, NAT Gateways, Transit Gateway, VPC Endpoints (PrivateLink), Direct Connect.
- **Storage & Databases:** S3, EBS, EFS, RDS (PostgreSQL/MySQL), Aurora, DynamoDB.
- **Security & Identity:** IAM, KMS, Secrets Manager, AWS WAF, Security Groups, NACLs, GuardDuty.
</details>

<details>
<summary><strong>● What is a VPC endpoint in AWS?</strong></summary>

**Answer:**
A **VPC Endpoint** enables private connectivity between your VPC and supported AWS services (or third-party SaaS services) without requiring an Internet Gateway, NAT Gateway, VPN connection, or AWS Direct Connect:

**Two Types of VPC Endpoints:**
1. **Gateway Endpoints:**
   - Free of charge.
   - Works by adding a target route in your VPC Route Table.
   - Supports only two AWS services: **Amazon S3** and **Amazon DynamoDB**.
2. **Interface Endpoints (AWS PrivateLink):**
   - Creates an **Elastic Network Interface (ENI)** with a private IP address inside your subnet.
   - Serves as an entry point for traffic destined to supported services (e.g., ECR, SSM, CloudWatch, Secrets Manager, or custom services).
   - Traffic never leaves the private AWS global network.
</details>

<details>
<summary><strong>↳ Follow-up: Can you use a VPC endpoint to interconnect two EC2 instances, such as in a cross-account scenario?</strong></summary>

**Answer:**
**Yes, via AWS PrivateLink (VPC Endpoint Services)!**

**Implementation Flow:**
1. In the Service Provider account, place the EC2 instances behind a **Network Load Balancer (NLB)**.
2. Create an **Endpoint Service (VPC Endpoint Service)** associated with that NLB, and allow the Consumer AWS Account ID.
3. In the Consumer account, create an **Interface VPC Endpoint** pointing to the service name.
4. An ENI with a private IP is created in the Consumer VPC. The Consumer EC2 instance sends traffic to this private IP, and AWS routes it across accounts privately over the AWS backbone to the Provider EC2 instances.
</details>

<details>
<summary><strong>↳ Follow-up: Apart from using a Transit Gateway, what other options are there to interconnect resources across AWS accounts or VPCs?</strong></summary>

**Answer:**
1. **VPC Peering:** Direct 1-to-1 network connection between two VPCs. High performance, zero bandwidth bottlenecks, but non-transitive.
2. **AWS PrivateLink (VPC Endpoints):** Exposes specific microservices securely across accounts without exposing the entire network CIDR block.
3. **Site-to-Site VPN:** IPsec VPN tunnels between VPCs via virtual private gateways.
4. **AWS Cloud WAN:** Global WAN service for connecting VPCs across multiple regions and on-premise locations using a unified core network.
</details>

<details>
<summary><strong>↳ Follow-up: If you use VPC peering between two VPCs, does the traffic go over the public internet or not?</strong></summary>

**Answer:**
**No. VPC peering traffic NEVER traverses the public internet.**

- All communication remains strictly on the private AWS global network backbone.
- Traffic is private, isolated from public IP routing, and does not require an Internet Gateway. Inter-region peering traffic is automatically encrypted at the AWS physical layer.
</details>

<details>
<summary><strong>↳ Follow-up: What is the main objective of using a VPC in AWS, and why do we use a VPC?</strong></summary>

**Answer:**
The main objective of **Amazon VPC (Virtual Private Cloud)** is to provide a **logically isolated virtual network** dedicated to your AWS account.

**Why we use a VPC:**
1. **Complete Network Isolation:** Isolates enterprise cloud resources from other AWS tenants.
2. **Granular Network Control:** Complete authority over IP address ranges (CIDR), subnets, route tables, network gateways, and IP routing.
3. **Multi-Layered Security:** Enforces Defense-in-Depth using Security Groups (stateful firewall at the instance level) and Network ACLs (stateless firewall at the subnet level).
4. **Hybrid Connectivity:** Allows extending on-premise corporate datacenters into the cloud via AWS Direct Connect or IPsec VPNs.
</details>

<details>
<summary><strong>● How would you configure a load balancer in front of an EC2 instance in AWS?</strong></summary>

**Answer:**
A step-by-step Application Load Balancer configuration:

1. **Target Group Creation:**
   - Create an ALB Target Group with target type `instance`, protocol `HTTP`, port `80` (or app port).
   - Configure health checks: Protocol `HTTP`, Path `/healthz`, Healthy threshold `2`, Unhealthy threshold `3`.
   - Register the target EC2 instance(s).
2. **Security Group Configuration:**
   - **ALB Security Group:** Inbound allows HTTP (80) and HTTPS (443) from `0.0.0.0/0`.
   - **EC2 Security Group:** Inbound allows port 80/app port **only** from the ALB Security Group ID.
3. **ALB Provisioning:**
   - Create an internet-facing Application Load Balancer across at least two public subnets in different Availability Zones.
   - Attach the ALB Security Group.
4. **Listener Rules:**
   - Configure a Port 443 HTTPS listener with an ACM certificate forwarding to the Target Group.
   - Configure a Port 80 HTTP listener with a default rule redirecting HTTP to HTTPS (301 redirect).
</details>

#### 【 SECURITY 】

<details>
<summary><strong>↳ Follow-up: If you wanted to apply CA (Certificate Authority) certificates to secure the load balancer setup, what steps would you follow?</strong></summary>

**Answer:**
1. **Obtain or Import the Certificate into AWS Certificate Manager (ACM):**
   - **Option A (Public CA via ACM):** Request a public certificate directly in ACM for `app.company.com`. Complete DNS validation by adding the generated CNAME records into Route 53.
   - **Option B (Third-Party CA like DigiCert):** In the ACM console, choose **Import a certificate**. Paste the Certificate Body (`server.crt`), Certificate Private Key (`server.key`), and Certificate Chain (`intermediate.crt`).
2. **Attach to the Load Balancer Listener:**
   - Open the ALB console and edit the HTTPS (Port 443) listener.
   - Select the ACM certificate as the default SSL/TLS certificate.
3. **Configure Modern Security Policy:**
   - Choose a secure SSL/TLS negotiation policy, such as `ELBSecurityPolicy-TLS13-1-2-2021-06`, disabling deprecated and vulnerable protocols (SSLv3, TLS 1.0, TLS 1.1).
4. **Enforce HTTPS Redirection:**
   - Update the HTTP (Port 80) listener to return a 301 Permanent Redirect to HTTPS port 443.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** How much experience do you have working in DevOps?

↳ **Candidate Introduction:** *Is the experience you mentioned your total professional experience, or specifically your relevant experience in DevOps?*

</details>
</details>

<details open>
<summary><h2>🏢 Mrisoftware</h2></summary>

<details open>
<summary><h3>Level 2</h3></summary>

#### 【 CI/CD 】

<details>
<summary><strong>● Can you describe what you would consider to be the perfect CI/CD pipeline, including its stages, the tools you would use, and the checks you would put in place?</strong></summary>

**Answer:**
A production-grade, state-of-the-art CI/CD pipeline incorporates GitOps, Shift-Left security, and automated progressive delivery:

```
[ Developer Commit ] ──> [ Pre-Commit Checks: TruffleHog, Linting ]
                                    │
                                    ▼
[ CI Phase: GitHub Actions / Jenkins (Ephemeral K8s Agent) ]
  ├── Fast Unit Tests & Code Coverage (>80%)
  ├── SAST: SonarQube Quality Gate
  ├── SCA: Trivy / Snyk Dependency Vulnerability Scan
  ├── Multi-Stage Docker Build (Distroless Base)
  ├── Container Vulnerability Scan (Trivy)
  └── Image Signing with Sigstore Cosign ──> Push to Amazon ECR
                                    │
                                    ▼
[ CD Phase: GitOps via Argo CD & Argo Rollouts (EKS) ]
  ├── Automated Sync to Staging Namespace
  ├── Automated Integration & DAST Smoke Tests (OWASP ZAP)
  └── Progressive Canary Release to Production:
      ├── Route 10% traffic via Service Mesh / ALB
      ├── Automated Metric Analysis: Error rate < 0.1%, p99 latency < 200ms
      └── Automatic Promotion to 100% OR Instant Automated Rollback
```

**Key Hallmarks:**
- **Zero Human Intervention in Non-Prod:** Every merge to `main` automatically deploys through staging to canary.
- **Hermetic & Immutable:** Builds use locked dependency versions; artifacts are tagged with Git commit SHAs and signed cryptographically.
- **Automated Rollback:** Data-driven progressive delivery eliminates manual monitoring during deployments.
</details>

<details>
<summary><strong>● What are the main KPIs that a DevOps engineer should track as part of their CI/CD pipeline and the environments they manage?</strong></summary>

**Answer:**
We track the **DORA Metrics (DevOps Research and Assessment)** as the gold standard for delivery performance, alongside operational pipeline telemetry:

1. **The Four DORA Metrics:**
   - **Deployment Frequency (DF):** How often code is successfully released to production (Elite target: Multiple deploys per day).
   - **Lead Time for Changes (LTFC):** The time it takes for a commit to reach production (Elite target: Less than one hour).
   - **Change Failure Rate (CFR):** The percentage of deployments causing a failure in production requiring rollback or hotfix (Elite target: 0–15%).
   - **Mean Time to Recovery (MTTR):** The time required to restore service when an incident occurs in production (Elite target: Less than one hour).

2. **Pipeline Operational KPIs:**
   - **Pipeline Build Duration:** Wall-clock time of the CI/CD pipeline (target: < 10 minutes to maintain developer flow).
   - **Pipeline Success Rate:** Percentage of green builds vs. flaky test failures.
   - **Vulnerability Remediation SLA:** Mean time to patch critical CVEs detected by scanners.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● What would be the driver to use a standalone, self-managed Kubernetes cluster rather than a managed container service, and why would you choose one approach over the other?</strong></summary>

**Answer:**
The choice between self-managed (Kubeadm on EC2/bare-metal) and managed (AWS EKS, GKE, AKS) involves balancing control against operational burden:

1. **Drivers for Self-Managed Kubernetes:**
   - **Custom Control Plane Configuration:** Need to modify API server flags, etcd tuning, or custom schedulers not permitted by managed cloud providers.
   - **Air-Gapped / Regulatory Compliance:** Government, banking, or sovereign data mandates requiring on-premise, isolated bare-metal environments.
   - **Avoiding Cloud Control Plane Costs at Massive Scale:** For organizations running hundreds of clusters, paying $0.10/hr per cluster ($72/month) plus managed add-on overhead can add up.

2. **Drivers for Managed Kubernetes (AWS EKS) — Recommended:**
   - **Zero Control Plane Toil:** AWS handles multi-AZ etcd quorum, master patching, automated backups, and control plane scaling with an SLA (99.95%).
   - **Cloud-Native Integrations:** Deep integration with IAM (IRSA), AWS VPC CNI (native VPC IP assignment to Pods), EBS/EFS CSI storage drivers, and Application Load Balancers.
   - **Team Focus:** Engineers focus on deploying business microservices rather than debugging etcd split-brain scenarios.
</details>

<details>
<summary><strong>● If a critical production environment goes down and you become aware of it, what actions would you take to resolve the incident?</strong></summary>

**Answer:**
I follow an established, blameless **Production Incident Management Framework**:

1. **Triage & Establish Command (First 5 Minutes):**
   - Acknowledge PagerDuty alert.
   - Declare a P1 incident and assume role of Incident Commander (IC).
   - Open a dedicated war-room (Slack `#incident-warroom` / Zoom) and update the customer status page with an initial acknowledgment.

2. **Assess Blast Radius & Stabilize (First 15 Minutes):**
   - Check what changed: Did a deployment occur recently? Did a cloud infrastructure change happen?
   - **Rule: Mitigate First, Diagnose Later.**
     - If caused by a recent deployment: Trigger an **immediate rollback** via Argo CD or revert the Git commit.
     - If caused by resource saturation: Manually scale the cluster or database capacity.
     - If caused by a regional outage: Initiate failover to the disaster recovery region via Route 53.

3. **Verify Recovery:**
   - Monitor real-time telemetry (Grafana Golden Signals, CloudWatch alarms, synthetic probes) to confirm error rates return to baseline.
   - Publish an incident resolved notification on the status page.

4. **Blameless Postmortem (Within 48 Hours):**
   - Conduct a blameless root cause analysis (RCA) with all stakeholders using the **Five Whys** methodology.
   - Document timeline, trigger causes, and create prioritized Jira tickets for preventive engineering improvements.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Your CV is heavily focused on AWS \- do you have any exposure to Azure and Azure DevOps?</strong></summary>

**Answer:**
While AWS is my primary cloud specialization, core cloud-native architecture principles translate directly across cloud providers:

- **Architectural Parity:**
  - AWS VPC <--> Azure Virtual Network (VNet)
  - AWS EC2 <--> Azure Virtual Machines (VMs)
  - AWS EKS <--> Azure Kubernetes Service (AKS)
  - AWS IAM <--> Microsoft Entra ID (Azure AD)
  - AWS S3 <--> Azure Blob Storage
- **Infrastructure as Code:** Using **Terraform**, multi-cloud provisioning follows the same declarative patterns using the `azurerm` provider.
- **Azure DevOps:** I have practical experience with Azure Pipelines (YAML syntax), managing service connections, Azure Artifacts, and integrating self-hosted agents. My strong foundations in Linux, containers, networking, and GitOps allow me to ramp up on Azure workloads rapidly.
</details>

#### 【 BEHAVIORAL 】

<details>
<summary><strong>● How did your first round of interview go?</strong></summary>

**Answer:**
The first round went exceptionally well. We had an engaging, in-depth technical discussion covering CI/CD automation, Kubernetes pod troubleshooting (specifically debugging CrashLoopBackOff states), Terraform modular design, and high-availability architecture across UAT and Production. The scenario-based questions allowed me to showcase my hands-on production troubleshooting methodology.
</details>

<details>
<summary><strong>↳ Follow-up: Was there any particular question from your first interview round that you found especially interesting, and could you share it with us?</strong></summary>

**Answer:**
Yes, the scenario question regarding debugging a Pod stuck in CrashLoopBackOff due to an upstream database dependency was particularly interesting. It led to a great architectural discussion about implementing Kubernetes readiness probes, initContainers, exponential backoff retries, and circuit breakers to decouple service dependencies rather than letting the application process repeatedly crash.
</details>

● **Candidate Introduction:** Could you give us your educational background, the companies you have worked for, and the nature of work you have been involved in?

↳ **Candidate Introduction:** *Who conducted your first round of interview - was it Ankit?*

● **Candidate Introduction:** Have you been working at the same company for the entire 6.5 years of your career, or have you changed companies?

<details>
<summary><strong>↳ Follow-up: Why are you looking to leave your current company now?</strong></summary>

**Answer:**
I have had a very fulfilling tenure at my current organization where I successfully led major cloud migrations, GitOps modernization, and platform reliability initiatives. Having established stable, automated systems, I am now seeking new technical challenges where I can work at larger scale, architect advanced platform engineering solutions, and contribute to mission-critical infrastructure initiatives.
</details>

● **Candidate Introduction:** What is your current notice period?

↳ **Candidate Introduction:** *Have you already resigned and are currently serving your notice period?*

● **Candidate Introduction:** Do you currently have any other job offers on hand?

● **Candidate Introduction:** What is your current CTC (compensation)?

● **Candidate Introduction:** Given that you already have a competitive offer of 24 LPA, what are you expecting from and why are you interested in joining this company (MRI)?

● **Candidate Introduction:** Are you currently based out of Bangalore?

<details>
<summary><strong>↳ Follow-up: Are you aware that the company expects employees to work from the office 3 days a week, and are you okay with that arrangement?</strong></summary>

**Answer:**
Yes, I am fully aware and completely comfortable with a 3-day hybrid in-office schedule in Bangalore. I value in-person collaboration with engineering teams and believe it accelerates architecture discussions and team alignment.
</details>

<details>
<summary><strong>↳ Follow-up: Are you okay with potentially working in different time zones, which may require working in shifts, including all three shifts?</strong></summary>

**Answer:**
Yes. As a senior DevOps engineer supporting global 24/7 mission-critical infrastructure, I have extensive experience participating in rotational shifts, follow-the-sun operational handovers, and 24/7 on-call rotations using PagerDuty.
</details>

<details>
<summary><strong>↳ Follow-up: Since the company heavily utilizes both Azure and AWS, why does your skill set stand out, and what would make you the right person for this role despite limited Azure exposure?</strong></summary>

**Answer:**
Core modern platform engineering—Terraform, Kubernetes, Docker, Linux systems, network architecture, and GitOps pipelines—is fundamentally cloud-agnostic. Having deep mastery of AWS infrastructure allows me to map cloud primitives directly to Azure equivalents without friction. My track record demonstrates that I ramp up on new tooling rapidly and focus on building resilient, automated systems that drive immediate business impact.
</details>

<details>
<summary><strong>● If you were assigned a task that is completely new to you and you have no prior experience with it, can you walk us through your thought process and how you would approach handling it?</strong></summary>

**Answer:**
I apply a disciplined, five-stage engineering discovery framework:

1. **Requirements & Scope Clarification:** Clarify the business objective, constraints, performance requirements, and acceptance criteria with the product owner or architect.
2. **Research & Documentation:** Review official documentation, architectural whitepapers, and industry best practices.
3. **Sandbox Proof-of-Concept (PoC):** Build a small, isolated sandbox prototype to validate technical assumptions, test edge cases, and evaluate failure modes without risking existing infrastructure.
4. **Peer Review & Feedback:** Present the PoC findings and architectural trade-offs to senior peers and security teams for review.
5. **Productionization & Documentation:** Automate deployment via Terraform/Helm, configure monitoring metrics and alerts, and document standard operating procedures (SOPs) and runbooks for the team.
</details>

● **Candidate Introduction:** What is your educational background?

</details>
</details>

<details open>
<summary><h2>🏢 Capgemini</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 11-08-2026 10:02 PM*

#### 【 KUBERNETES 】

<details>
<summary><strong>● Can you explain the architecture of Kubernetes, including the control plane and worker (data plane) components, and describe what each component does?</strong></summary>

**Answer:**
Kubernetes operates on a declarative, master-worker architecture separated into the **Control Plane** and the **Worker (Data Plane) Nodes**:

```
[ CONTROL PLANE ]
  ├── kube-apiserver          <── REST API Gateway & Authentication
  ├── etcd                    <── Distributed, Consistent State Store
  ├── kube-scheduler          <── Assigns Pods to Optimal Nodes
  ├── kube-controller-manager <── Runs Core Control Loops (Node, ReplicaSet, etc.)
  └── cloud-controller-mgr    <── Interfaces with Cloud Provider APIs (ALB, EBS)

[ WORKER NODE (DATA PLANE) ]
  ├── kubelet                 <── Node Agent Ensuring Containers Run
  ├── kube-proxy              <── Maintains iptables/IPVS Routing Rules
  └── Container Runtime (CRI) <── containerd / CRI-O Managing Pod Processes
```

1. **Control Plane Components:**
   - **`kube-apiserver`:** The front-end API gateway. All communication (from `kubectl`, worker nodes, and controllers) passes through here. Handles authentication, authorization (RBAC), and schema validation.
   - **`etcd`:** A strongly consistent, distributed key-value store holding the complete state, specifications, and metadata of the cluster.
   - **`kube-scheduler`:** Evaluates unscheduled Pods and assigns them to optimal worker nodes based on resource requests/limits, taints, tolerations, and node affinity rules.
   - **`kube-controller-manager`:** Runs daemon control loops that continuously regulate cluster state to match the declared desired state (Node Lifecycle Controller, ReplicaSet Controller, EndpointSlice Controller).
   - **`cloud-controller-manager`:** Integrates cluster operations with underlying cloud provider APIs (managing cloud load balancers, storage volumes, and node routing).

2. **Worker Node (Data Plane) Components:**
   - **`kubelet`:** An agent running on each worker node. Registers the node with the API server, watches for Pod assignments, and interacts with the Container Runtime via CRI to ensure containers are running healthy.
   - **`kube-proxy`:** Maintains host network routing rules using `iptables` or `IPVS` to enable service cluster-IP networking and load balancing.
   - **Container Runtime (CRI):** The low-level runtime engine (e.g., `containerd`, `CRI-O`) that pulls images and executes container processes.
</details>

<details>
<summary><strong>● What are the different types of deployment strategies used in Kubernetes?</strong></summary>

**Answer:**
Kubernetes supports several deployment strategies depending on tolerance for downtime and infrastructure capacity:

1. **RollingUpdate (Default):** Gradually replaces instances of the previous version with the new version using `maxSurge` and `maxUnavailable`. Ensures zero downtime.
2. **Recreate:** Terminates all existing Pods simultaneously before launching the new version. Incurs downtime, but prevents different application versions from running concurrently.
3. **Blue/Green (Red/Black):** Deploys a complete new environment (Green) alongside the old environment (Blue). Traffic is switched instantly at the Service or Ingress layer.
4. **Canary Deployment:** Deploys the new version alongside the current version and routes a small percentage of user traffic (e.g., 5–10%) to it, monitoring error rates before complete rollout (typically managed via **Argo Rollouts**).
5. **Shadow / Dark Launching:** Duplicates live production traffic to the new version without returning its responses to clients, used for performance and load validation.
</details>

<details>
<summary><strong>● Can you explain the difference between the 'Recreate' and 'RollingUpdate' deployment strategies in Kubernetes?</strong></summary>

**Answer:**
| Feature | Recreate Strategy | RollingUpdate Strategy |
| :--- | :--- | :--- |
| **Downtime** | **Guaranteed Downtime** between killing old pods and starting new pods | **Zero Downtime**; always maintains running pods |
| **Pod Lifecycle Order**| Kills ALL existing Pods (`replicas -> 0`), then creates new Pods | Gradually creates new Pods while terminating old Pods |
| **Resource Overhead** | Low; requires no extra cluster compute capacity | Requires temporary compute headroom defined by `maxSurge` |
| **Version Concurrency**| Old and new versions **never** run concurrently | Old and new versions **coexist** during the rollout window |
| **Use Case** | Major database schema changes incompatible with old app version | High-availability production web apps and APIs |
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Are you familiar with AWS cloud services?</strong></summary>

**Answer:**
Yes, I have over 6+ years of comprehensive production experience across AWS core services:
- **Compute:** EC2, Launch Templates, Auto Scaling Groups, Lambda.
- **Containers:** EKS, ECS, ECR.
- **Networking:** VPC, Subnets, Internet/NAT Gateways, Route 53, ALB/NLB, Transit Gateway, PrivateLink.
- **Storage & Databases:** S3, EBS, EFS, RDS (PostgreSQL/MySQL), Aurora, ElastiCache.
- **Security & Governance:** IAM, KMS, Secrets Manager, AWS WAF, Shield, GuardDuty, CloudTrail, CloudWatch.
</details>

<details>
<summary><strong>● Suppose you have an EC2 instance that you (or a junior team member) cannot SSH into, and you get a timeout. How would you troubleshoot this issue — what would you check initially, and what could be the possible causes?</strong></summary>

**Answer:**
A **timeout** specifically indicates packet loss at the network layer (the request is dropped before reaching the SSH daemon):

**Systematic Checklist:**
1. **Security Group Inbound Rules:**
   - Verify that the EC2 instance's Security Group allows inbound traffic on **Port 22**.
   - Verify that the source IP address in the rule matches the client's current public IP address (home broadband and office VPN IPs frequently change).
2. **Subnet Route Table & Internet Gateway:**
   - Confirm whether the instance is in a public subnet. Check if the route table contains a default route to an Internet Gateway (`0.0.0.0/0 -> igw-xxxx`).
3. **Public IP Allocation:**
   - Verify that the instance has an active Public IPv4 address or an attached Elastic IP (EIP).
4. **Network Access Control Lists (NACLs):**
   - Check the subnet NACL. Verify there is no explicit `DENY` on port 22, and ensure outbound ephemeral ports (`1024-65535`) are allowed.
5. **AWS Instance Status Checks:**
   - Check AWS Console: Are both **System Status** and **Instance Status** checks passing (2/2 checks)? If System check fails, AWS hardware underneath is degraded.
</details>

<details>
<summary><strong>↳ Follow-up: Assuming the user already has all necessary IAM access and regularly uses this UAT/staging/dev EC2 instance but suddenly cannot SSH into it, what other reasons (besides access/permissions) could explain this?</strong></summary>

**Answer:**
Non-network and operating system level causes:

1. **Client Public IP Address Changed:** The developer's home ISP or VPN re-assigned their public IP, so their traffic is now dropped by the Security Group whitelist.
2. **Local OS Firewall (`iptables` / `ufw`):** A script or developer accidentally flushed or misconfigured the host firewall rules, blocking port 22.
3. **SSH Daemon (`sshd`) Crash or Termination:** The SSH daemon service stopped or crashed inside the operating system.
4. **Severe CPU / Memory Starvation (Kernel Lockup):** The application experienced a memory leak or 100% CPU lockup, preventing the kernel from allocating file descriptors or forking a new `sshd` process.
5. **Disk Space Exhaustion (100% Inode / Disk Full):** Root filesystem is 100% full, preventing SSH from creating session pseudo-terminals or writing to `/var/log`.
</details>

<details>
<summary><strong>● Given a scenario where an intern accidentally ran 'chmod -R 777' on the wrong directory on a dev EC2 instance, corrupting file permissions including the .ssh folder, and she has now lost SSH access to the instance in new sessions — how would you recover the instance?</strong></summary>

**Answer:**
OpenSSH server strictly refuses key-based authentication if permissions on `~/.ssh` or `authorized_keys` are overly permissive (`chmod 777` allows group and others to write).

**Recovery Strategies:**
1. **If the Current Shell Session is Still Active:**
   - Immediately fix permissions inside the active terminal before disconnecting:
     ```bash
     chmod 755 /home/ubuntu
     chmod 700 /home/ubuntu/.ssh
     chmod 600 /home/ubuntu/.ssh/authorized_keys
     chown -R ubuntu:ubuntu /home/ubuntu/.ssh
     ```
2. **Via AWS Systems Manager (SSM) Session Manager:**
   - Connect via browser-based SSM Session Manager (operates independently of SSH keys and port 22) and run the permission fix commands.
3. **Via EC2 User Data (Reboot Fix):**
   - Stop the instance -> Edit User Data with a corrective bash script -> Start the instance.
4. **Via EBS Rescue Volume Mounting:**
   - Detach root volume -> Attach to a rescue EC2 instance -> Fix permissions -> Reattach to original instance.
</details>

<details>
<summary><strong>↳ Follow-up: Now that you know the exact cause of the issue, what are the fastest ways you can think of to immediately recover the instance?</strong></summary>

**Answer:**
The two fastest recovery methods:

1. **Fastest Method: AWS Systems Manager (SSM) Session Manager:**
   - If the SSM Agent is installed and the instance profile has `AmazonSSMManagedInstanceCore`, click **Connect -> Session Manager** in the AWS Console.
   - Provides an immediate root terminal where you run `chmod 700 /home/ubuntu/.ssh && chmod 600 /home/ubuntu/.ssh/authorized_keys`. (Takes ~30 seconds).

2. **Second Fastest: EC2 User Data Execution on Boot:**
   - Stop the instance.
   - Go to `Actions -> Instance Settings -> Edit User Data`.
   - Add a cloud-init script to reset permissions and start the instance. (Takes ~2 minutes).
</details>

<details>
<summary><strong>↳ Follow-up: Since the SSH directory permissions are corrupted and you cannot SSH into the instance at all, how would you access it to fix the problem?</strong></summary>

**Answer:**
Use out-of-band access mechanisms that bypass the SSH transport layer entirely:
1. **AWS Systems Manager Session Manager:** Authenticates via IAM over outbound HTTPS.
2. **EC2 Serial Console:** Provides direct VTY serial console access via the AWS Console/CLI without network dependencies.
3. **EC2 Instance Connect (via Serial/Console):** Direct browser-based terminal if supported.
</details>

<details>
<summary><strong>↳ Follow-up: If you don't have a backup AMI and need to recover the exact same instance, and you know the root cause is corrupted SSH folder permissions, how (other than using Session Manager) would you reset those permissions to regain SSH access?</strong></summary>

**Answer:**
Use the **EC2 User Data Script Method**:

1. **Stop** the affected EC2 instance.
2. Navigate to **Actions -> Instance settings -> Edit user data**.
3. Input the following script:
   ```bash
   Content-Type: multipart/mixed; boundary="//"
   MIME-Version: 1.0

   --//
   Content-Type: text/x-shellscript; charset="us-ascii"
   #!/bin/bash
   chmod 755 /home/ubuntu
   chmod 700 /home/ubuntu/.ssh
   chmod 600 /home/ubuntu/.ssh/authorized_keys
   chown -R ubuntu:ubuntu /home/ubuntu/.ssh
   --//--
   ```
4. **Start** the instance.
5. On boot, `cloud-init` executes the script as `root`, resetting permissions to secure standards. SSH access is immediately restored.
</details>

<details>
<summary><strong>↳ Follow-up: Setting aside Session Manager, is there any other, quicker way to reset the permissions and regain access to the instance?</strong></summary>

**Answer:**
The **EC2 User Data Method** described above is the quickest alternative because:
- It requires **no extra EC2 instances**.
- It does not require detaching, re-mounting, and re-attaching EBS volumes.
- Total recovery time is under 2 minutes.
</details>

<details>
<summary><strong>● What is Amazon S3 and why is it used?</strong></summary>

**Answer:**
**Amazon Simple Storage Service (S3)** is an industry-leading object storage service offering 99.999999999% (11 9's) data durability.

**Why it is used:**
- **Scalability & Durability:** Redundantly stores data across multiple Availability Zones with near limitless capacity.
- **Security:** Enforces encryption at rest (SSE-S3, SSE-KMS), bucket policies, and S3 Block Public Access.
- **Cost-Optimized Storage Tiers:**
  - *S3 Standard:* High-frequency access.
  - *S3 Intelligent-Tiering:* Automatically shifts objects between tiers based on access patterns.
  - *S3 Glacier / Deep Archive:* Long-term compliance archiving at ultra-low cost ($0.00099 per GB/month).
- **Common Use Cases:** Static website hosting, data lakes, CI/CD build artifacts, and disaster recovery backups.
</details>

<details>
<summary><strong>● Have you worked with AWS RDS, and are you familiar with Aurora? Can you explain the architectural difference between RDS and Aurora?</strong></summary>

**Answer:**
Yes, I have worked extensively with both. While standard RDS deploys traditional database engines onto EC2 and EBS, **Amazon Aurora** is a cloud-native database engine re-architected to **decouple compute from storage**:

```
[ Traditional RDS ]
  Compute (EC2) ──> Monolithic EBS Volume (Asynchronous replication to read replicas)

[ Amazon Aurora ]
  Compute Nodes ──> Distributed 10Gbps Virtualized Storage Fleet
                    (6-way replication across 3 AZs; Shared Storage Layer)
```

| Architectural Dimension | Traditional RDS (MySQL/PostgreSQL) | Amazon Aurora |
| :--- | :--- | :--- |
| **Storage Architecture**| Monolithic EBS block volumes tied to instance | Distributed, auto-scaling storage fleet (scales to 128TB) |
| **Replication Mechanism**| Engine-level binlog replication (high lag) | Shared storage tier replication (near-zero lag, < 10ms) |
| **Resilience & Quorum** | Single EBS volume (or 2 in Multi-AZ) | Writes 6 copies across 3 AZs (4/6 write quorum, 3/6 read quorum) |
| **Failover Speed** | 60–120 seconds (DNS switch) | **Under 30 seconds** (crash-consistent failover) |
| **Read Replicas** | Up to 5 read replicas | Up to **15 read replicas** sharing the same storage |
| **Performance** | Standard database engine performance | Up to **5x throughput of MySQL**, **3x of PostgreSQL** |
</details>

<details>
<summary><strong>● If a client wants to avoid RDS costs by installing MySQL directly on an EC2 instance instead, how would you convince them of the advantages of using RDS over self-managing a database on EC2?</strong></summary>

**Answer:**
I would present a **Total Cost of Ownership (TCO) and Risk Analysis**:

While self-hosting MySQL on EC2 seems cheaper on raw infrastructure bills, it introduces massive hidden operational costs and business risks:
1. **High Availability & Failover:** RDS Multi-AZ provides automated synchronous replication and sub-60-second failover. Self-hosting requires manual replication setups, split-brain mitigation, and complex clustering software.
2. **Automated Backups & Point-in-Time Recovery (PITR):** RDS continuously streams transaction logs, allowing restoration to any second within 35 days with one click.
3. **Automated Patching & Maintenance:** RDS manages OS and database engine security updates automatically without requiring a dedicated DBA.
4. **Storage Auto-Scaling:** RDS expands storage automatically without downtime. EC2 requires manual volume resizing and filesystem extension.
5. **Business Impact:** The engineering hours spent maintaining, backing up, and troubleshooting a self-managed database far exceed the modest cost margin of RDS.
</details>

<details>
<summary><strong>↳ Follow-up: Specifically, what are the concrete advantages of using RDS (e.g., for MySQL) compared to installing and managing MySQL yourself on an EC2 instance?</strong></summary>

**Answer:**
1. **Automated Multi-AZ Standby:** Synchronous physical replication across Availability Zones with automated failover.
2. **Automated Point-in-Time Recovery:** Continuous backups with 1-second granularity.
3. **One-Click Read Replicas:** Scale read throughput effortlessly up to 5 replicas (or 15 in Aurora).
4. **Automated OS & Minor Engine Patching:** Managed maintenance windows.
5. **Storage Autoscaling:** Elastic expansion up to 64TB with zero downtime.
6. **Integrated Encryption & Security:** Native KMS encryption at rest and IAM database authentication.
</details>

<details>
<summary><strong>● Can you explain the difference between Network ACLs (NACLs) and Security Groups in AWS?</strong></summary>

**Answer:**
Both act as virtual firewalls in a VPC, but operate at different layers:

| Feature | Security Group | Network ACL (NACL) |
| :--- | :--- | :--- |
| **Operating Level** | **Instance / ENI Level** | **Subnet Boundary Level** |
| **State Nature** | **Stateful** (Return traffic is automatically allowed) | **Stateless** (Inbound and outbound rules evaluated separately) |
| **Rule Types** | **ALLOW rules only** | Supports both **ALLOW and DENY rules** |
| **Evaluation Order** | All rules evaluated before decision | Evaluated in **strict numerical order** (lowest number first) |
| **Default Configuration**| Inbound denied, outbound allowed | Default NACL allows all inbound and outbound traffic |
</details>

<details>
<summary><strong>● Have you worked on any AWS cost optimization techniques to reduce infrastructure costs?</strong></summary>

**Answer:**
Yes, I actively implement cloud financial management (FinOps) best practices:
- **Compute Optimization:** Purchasing **Compute Savings Plans** (up to 72% savings) for steady-state workloads; adopting **EC2 Spot instances** for stateless Kubernetes worker nodes.
- **Architecture Modernization:** Migrating x86 workloads to **AWS Graviton** for 20% lower cost and 25% higher performance.
- **Storage Lifecycle Management:** Configuring **S3 Lifecycle Rules** and Intelligent-Tiering to transition logs to Glacier; automated pruning of orphaned EBS volumes and obsolete snapshots.
- **Networking Costs:** Deploying **VPC Endpoints** for S3 and ECR to avoid costly NAT Gateway data transfer charges ($0.045/GB).
</details>

<details>
<summary><strong>↳ Follow-up: Can you describe specifically how you implemented these AWS cost optimization techniques?</strong></summary>

**Answer:**
In my previous role, I executed a cost optimization campaign that reduced monthly AWS expenditure by **28%**:
1. **Karpenter Spot Adoption on EKS:** Configured Karpenter to launch Spot instances for development and staging environments, cutting non-prod compute spend by 60%.
2. **Orphaned EBS Volume Cleanup:** Authored a Python Boto3 script scheduled as a monthly AWS Lambda function to identify and delete unattached EBS volumes and snapshots older than 90 days.
3. **S3 Lifecycle Rules:** Implemented rules moving application access logs to S3 Standard-IA after 30 days and to Glacier Flexible Retrieval after 90 days, expiring them after 365 days.
4. **VPC Gateway Endpoints:** Provisioned S3 Gateway Endpoints across all VPC route tables, routing gigabytes of nightly backup data directly to S3 without incurring NAT Gateway processing charges.
</details>

<details>
<summary><strong>● Are you familiar with VPC peering, Transit Gateway, and Direct Connect? Can you explain how VPC peering and Transit Gateway work?</strong></summary>

**Answer:**
- **VPC Peering:** A direct 1-to-1 network connection between two VPCs. Routing is non-transitive (VPC A peered with B and B peered with C does **not** allow A to communicate with C). Ideal for connecting a small number of VPCs with zero data processing fees within the same AZ.
- **AWS Transit Gateway (TGW):** A regional virtual hub-and-spoke router that connects thousands of VPCs and on-premise networks. It supports **transitive routing**, centralized route tables, and cross-account attachments via AWS RAM.
- **Direct Connect (DX):** A dedicated, private physical fiber-optic connection from an on-premise datacenter directly into AWS, bypassing the public internet for predictable throughput and low latency.
</details>

<details>
<summary><strong>↳ Follow-up: Can you continue and specifically explain how AWS Transit Gateway works?</strong></summary>

**Answer:**
**AWS Transit Gateway (TGW)** acts as a distributed Layer 3 regional router:

1. **Attachments:** VPCs, Direct Connect Gateways, and Site-to-Site VPNs attach to the TGW via Elastic Network Interfaces (ENIs) placed in designated subnets across Availability Zones.
2. **Route Tables:** TGW maintains route tables independent of VPC route tables.
3. **Association & Propagation:**
   - *Association:* Each attachment is associated with one TGW route table.
   - *Propagation:* Attachments propagate their CIDR routes into designated TGW route tables.
4. **Transitive Routing:** Packet arriving from VPC A destined for VPC B passes through the TGW and is forwarded directly according to TGW route table entries, eliminating point-to-point peering mesh complexity.
</details>

<details>
<summary><strong>↳ Follow-up: If you need to connect three VPCs (A, B, and C) using VPC peering, how would you ensure all three are fully interconnected?</strong></summary>

**Answer:**
Because VPC Peering is **strictly non-transitive**, you must configure a **Full Mesh**:

1. **Establish 3 Distinct Peering Connections:**
   - Connection 1: `pcx-ab` between VPC A and VPC B.
   - Connection 2: `pcx-bc` between VPC B and VPC C.
   - Connection 3: `pcx-ac` between VPC A and VPC C.
2. **Update Route Tables in All 3 VPCs:**
   - **In VPC A:** Route to VPC B CIDR -> `pcx-ab`; Route to VPC C CIDR -> `pcx-ac`.
   - **In VPC B:** Route to VPC A CIDR -> `pcx-ab`; Route to VPC C CIDR -> `pcx-bc`.
   - **In VPC C:** Route to VPC A CIDR -> `pcx-ac`; Route to VPC B CIDR -> `pcx-bc`.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself, including your experience, your role at your previous company, and the tools, technologies, and domains you worked on?

</details>
</details>

<details open>
<summary><h2>🏢 R Systems</h2></summary>

<details open>
<summary><h3>Level 2</h3></summary>

#### 【 CI/CD 】

<details>
<summary><strong>↳ Follow-up: For this Spring Boot application deployment on AWS, how would you design the CI/CD pipeline?</strong></summary>

**Answer:**
An automated GitOps pipeline tailored for Java Spring Boot microservices:

1. **CI Pipeline (Jenkins / GitHub Actions):**
   - **Compile & Test:** `mvn clean verify` running unit and integration tests.
   - **Static Analysis:** SonarQube quality gate verification.
   - **Containerization:** Multi-stage Dockerfile packaging the compiled JAR into an **Eclipse Temurin JRE 17 Alpine/Distroless** base image.
   - **Security Scanning:** Trivy scans image for CVEs; Cosign signs image attestation.
   - **Push to Registry:** Image pushed to Amazon ECR tagged with `${GIT_COMMIT}`.
2. **CD Pipeline (GitOps via Argo CD):**
   - CI pipeline updates the image tag in the GitOps deployment repository.
   - **Argo CD** synchronizes the new image to the EKS cluster.
   - **Argo Rollouts** performs a Canary deployment, validating `/actuator/health` and Prometheus error metrics before routing 100% of user traffic.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● What is your total hands-on production experience with Kubernetes?</strong></summary>

**Answer:**
I have over 5+ years of daily hands-on production experience operating Kubernetes clusters on AWS EKS and bare-metal environments, managing mission-critical enterprise microservices under high throughput SLAs.
</details>

<details>
<summary><strong>↳ Follow-up: What kind of application are you currently deploying on Kubernetes in your work?</strong></summary>

**Answer:**
We deploy high-throughput microservices architectures:
- **Backend:** Java Spring Boot and Go REST/gRPC microservices.
- **Frontend:** React / Next.js server-side rendered web applications.
- **Data Workers:** Asynchronous event consumers processing messages from Apache Kafka and Amazon SQS.
</details>

<details>
<summary><strong>↳ Follow-up: Can you write the Kubernetes manifest file(s) needed to deploy this Spring Boot-based application?</strong></summary>

**Answer:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spring-boot-app
  namespace: production
  labels:
    app: spring-boot-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: spring-boot-app
  template:
    metadata:
      labels:
        app: spring-boot-app
    spec:
      containers:
        - name: app
          image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/spring-boot-app:v1.0.0
          ports:
            - containerPort: 8080
          env:
            - name: JAVA_TOOL_OPTIONS
              value: "-XX:MaxRAMPercentage=75.0 -XX:+UseG1GC"
            - name: SPRING_PROFILES_ACTIVE
              value: "production"
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "1000m"
              memory: "2Gi"
          livenessProbe:
            httpGet:
              path: /actuator/health/liveness
              port: 8080
            initialDelaySeconds: 45
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /actuator/health/readiness
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: spring-boot-service
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: spring-boot-app
  ports:
    - port: 80
      targetPort: 8080
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: spring-boot-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: spring-boot-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```
</details>

<details>
<summary><strong>↳ Follow-up: For running this workload on Kubernetes (EKS), would you use Fargate (serverless) or provision EC2 worker nodes?</strong></summary>

**Answer:**
For Java Spring Boot workloads, I strongly recommend **EC2 Worker Nodes (managed node groups or Karpenter)**:

**Why EC2 Worker Nodes Win for Spring Boot:**
1. **Image Caching & Startup Latency:** Spring Boot container images are large (250MB–500MB). EC2 nodes cache image layers locally. Fargate must pull the complete image from ECR on every single pod start, causing slow cold starts.
2. **DaemonSet Support:** EC2 supports essential operational DaemonSets (Datadog agent, Fluent Bit, AWS VPC CNI, Calico). Fargate **does not support DaemonSets**.
3. **Cost Efficiency at Scale:** EC2 compute can leverage Compute Savings Plans, Reserved Instances, and Spot instances, making it 40–60% cheaper than Fargate at steady-state.
</details>

<details>
<summary><strong>● Have you worked with service mesh implementations on Kubernetes?</strong></summary>

**Answer:**
Yes, I have worked with **Istio Service Mesh** for microservices traffic engineering:
- **Mutual TLS (mTLS):** Enforced zero-trust peer authentication across all internal pod-to-pod communications.
- **Traffic Management:** Configured `VirtualService` and `DestinationRule` objects for Canary routing (e.g., routing 10% traffic to version 2).
- **Circuit Breaking & Fault Injection:** Configured outlier detection to eject unhealthy backend instances automatically.
- **Distributed Tracing:** Integrated Envoy sidecars with Jaeger for end-to-end request tracing.
</details>

#### 【 IAC 】

<details>
<summary><strong>● Have you used Terraform and AWS CloudFormation together in the same project or environment?</strong></summary>

**Answer:**
Yes, in hybrid enterprise setups:
- **Terraform:** Used as the primary platform orchestration tool to provision foundational infrastructure: VPCs, EKS clusters, RDS instances, and IAM baselines.
- **CloudFormation / SAM:** Utilized by application development teams for deploying serverless applications (AWS Lambda functions, API Gateway, DynamoDB tables) defined within standard AWS Serverless Application Model (SAM) templates.
</details>

<details>
<summary><strong>↳ Follow-up: Given that the earlier application requirement is to be deployed on AWS only, would you recommend using Terraform or AWS CloudFormation to deploy the stack?</strong></summary>

**Answer:**
I would still strongly recommend **Terraform** even for AWS-only deployments.
</details>

<details>
<summary><strong>↳ Follow-up: Aside from multi-cloud support, is there any specific reason you would prefer Terraform over CloudFormation for this AWS-only stack, or would you go entirely with CloudFormation?</strong></summary>

**Answer:**
Key engineering reasons to choose Terraform over CloudFormation on AWS:
1. **Accurate Dry-Run Planning (`terraform plan`):** Provides instant, precise in-memory diffs of additions, updates, and destructions. CloudFormation Change Sets are notoriously slow and less transparent.
2. **Speed & Modularity:** Terraform executes API calls directly in parallel using dependency graphs. CloudFormation can get stuck in agonizingly slow rollback loops (`UPDATE_ROLLBACK_IN_PROGRESS` taking 45+ minutes).
3. **Ecosystem & Unified Providers:** Terraform can manage AWS resources, Kubernetes manifests, Helm releases, and Datadog monitoring alerts within a single unified codebase.
4. **State Manipulation & Refactoring:** Tools like `terraform state rm`, `terraform import`, and `moved` blocks enable seamless infrastructure refactoring without downtime.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● What is your total hands-on experience working with AWS in production-grade environments?</strong></summary>

**Answer:**
I have over 6+ years of production experience architecting, managing, and maintaining enterprise infrastructure on AWS.
</details>

<details>
<summary><strong>↳ Follow-up: Just to clarify, is the experience you mentioned purely in production environments, excluding any lower/non-prod environments?</strong></summary>

**Answer:**
Yes, that represents 6+ years managing 24/7 mission-critical **production environments** subject to strict uptime SLAs (99.95%+), production change management procedures, and on-call rotations.
</details>

<details>
<summary><strong>↳ Follow-up: Where exactly do you plan to deploy the application workload within AWS (e.g., which compute service or platform)?</strong></summary>

**Answer:**
On **Amazon EKS (Elastic Kubernetes Service)** deployed across private subnets in 3 Availability Zones, fronted by an Application Load Balancer.
</details>

<details>
<summary><strong>↳ Follow-up: Which specific EC2 instance series would you choose to run this workload?</strong></summary>

**Answer:**
**AWS Graviton3-based General Purpose instances (`m7g.xlarge` or `m7g.2xlarge`)**:
- Java Spring Boot applications require a balanced compute and memory profile (1 vCPU to 4 GB RAM).
- Graviton3 provides up to **25% better compute performance** and **20% lower cost** compared to comparable x86 instances.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Given a Spring Boot-based application where users upload an image and provide an email address, the application processes the image and notifies the user once processing is complete via a front-end interface, how would you design and deploy the architecture for this application on AWS, incorporating best practices for high availability, disaster recovery, and cost optimization?</strong></summary>

**Answer:**
An event-driven, decoupled, asynchronous cloud architecture:

```
[ User Browser ]
  ├── 1. Request Upload URL ──> [ ALB ] ──> [ Spring Boot API (EKS) ]
  ├── 2. Direct S3 Upload   ──> [ Amazon S3 (Raw Bucket) ]
                                          │ (S3 Event Notification)
                                          ▼
                                   [ Amazon SQS Queue ]
                                          │
                                          ▼
                         [ Background Worker Pods (EKS / KEDA) ]
                               (Processes Image & Stores in S3 Processed)
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
         [ Amazon SES (Email) ]                    [ AWS AppSync / WebSockets ]
       (Sends Email Notification)                    (Notifies Frontend UI)
```

**Architecture & Workflow:**
1. **Direct S3 Upload via Pre-Signed URLs (Cost & Scalability):**
   - User submits metadata to Spring Boot API via ALB.
   - API generates a secure, time-limited **S3 Pre-Signed Upload URL**.
   - Client uploads image directly to the `raw-images` S3 bucket, completely bypassing application servers and saving immense bandwidth and memory.
2. **Decoupled Asynchronous Processing:**
   - S3 upload triggers an **Amazon SQS** message containing the image path and user email.
   - Background worker pods on EKS consume SQS messages. The worker fleet scales dynamically from 0 to 20 pods based on queue length using **KEDA (Kubernetes Event-driven Autoscaling)**.
3. **Notification Layer:**
   - Worker resizes/processes the image, saves it to `processed-images` S3 bucket, and sends an email via **Amazon SES**.
   - Real-time UI notification is delivered via **AWS API Gateway WebSocket API** or **AWS AppSync**.
4. **High Availability & Cost Optimization:**
   - Multi-AZ across 3 Availability Zones.
   - Worker pods run on **EC2 Spot Instances** (saving up to 80%).
   - S3 Lifecycle rules transition raw uploads to Glacier after 30 days.
</details>

#### 【 OTHER 】

<details>
<summary><strong>↳ Follow-up: Would you be able to share your screen so we can go through some practical examples together?</strong></summary>

**Answer:**
Certainly. I am ready to share my screen to walk through architecture diagrams, live Terraform modules, Kubernetes manifests, or terminal debugging workflows.
</details>

<details>
<summary><strong>↳ Follow-up: For the purpose of a deployment exercise, are you more comfortable working with a Python-based application or a Spring Boot-based application?</strong></summary>

**Answer:**
I am comfortable with both:
- For high-throughput enterprise backend services, **Spring Boot** provides a great showcase for containerization, JVM memory tuning (`-XX:MaxRAMPercentage`), and Actuator health probe integration.
- For lightweight microservices and fast scripting exercises, **Python** is equally fast to demonstrate.
</details>

</details>
</details>

<details open>
<summary><h2>🏢 Capgemini</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 12-08-2026 02:55 AM*

#### 【 LINUX 】

<details>
<summary><strong>● Suppose an intern accidentally ran a recursive chmod 777 on the wrong directory (due to a typo instead of using tab-autocomplete), which corrupted the permissions across the entire filesystem, including the .ssh folder, on a Ubuntu dev EC2 instance. She still has access in her current session but loses access once she starts a new session. How would you go about recovering access to the instance?</strong></summary>

**Answer:**
OpenSSH server strictly refuses key authentication if permissions on `~/.ssh` or `authorized_keys` are world-writable (`chmod 777`).

**Step-by-Step Immediate Recovery (Utilizing Active Session):**
Because the intern still has an **active terminal session**, we must execute the corrective permissions commands directly within that shell before disconnecting:

```bash
# 1. Fix user home directory permissions
sudo chmod 755 /home/ubuntu

# 2. Fix .ssh directory and key permissions
sudo chmod 700 /home/ubuntu/.ssh
sudo chmod 600 /home/ubuntu/.ssh/authorized_keys
sudo chown -R ubuntu:ubuntu /home/ubuntu/.ssh

# 3. Fix critical system binaries and SSH daemon host keys
sudo chmod 755 /etc /bin /usr /usr/bin
sudo chmod 755 /etc/ssh
sudo chmod 600 /etc/ssh/ssh_host_*_key
sudo chmod 644 /etc/ssh/ssh_host_*_key.pub
```
Open a separate terminal window to verify SSH connectivity before closing the original session.
</details>

<details>
<summary><strong>↳ Follow-up: Now that you know the root cause is a permissions issue caused by the recursive chmod 777 command, what are the fastest ways you can think of to immediately recover access to the instance?</strong></summary>

**Answer:**
1. **Fix directly inside the active session** (takes 10 seconds).
2. If the active session is lost: **AWS Systems Manager (SSM) Session Manager** connects via browser and allows fixing permissions immediately without SSH.
3. If SSM is not installed: **EC2 User Data script on reboot** (stop instance, edit user data to run chmod script, start instance).
</details>

<details>
<summary><strong>↳ Follow-up: Since the permission changes have broken the SSH directory itself, you won't be able to SSH into the instance normally. Given that constraint, how would you access and fix the instance?</strong></summary>

**Answer:**
Use out-of-band management tools:
- **AWS Systems Manager Session Manager:** Bypasses SSH daemon and keys entirely.
- **EC2 Serial Console:** Direct console access via AWS Management Console.
- **Rescue Volume Attachment:** Detach root EBS volume and mount it to another running instance.
</details>

<details>
<summary><strong>↳ Follow-up: Assuming you don't have a backup AMI available, and Session Manager is not an option, how would you reset the permissions on the broken .ssh folder (and related files) to restore SSH access to the instance? What quicker method could you use?</strong></summary>

**Answer:**
Use the **EC2 User Data Script Method**:
1. Stop the EC2 instance in AWS Console.
2. Select **Actions -> Instance settings -> Edit user data**.
3. Add the shell script:
   ```bash
   Content-Type: multipart/mixed; boundary="//"
   MIME-Version: 1.0

   --//
   Content-Type: text/x-shellscript; charset="us-ascii"
   #!/bin/bash
   chmod 755 /home/ubuntu
   chmod 700 /home/ubuntu/.ssh
   chmod 600 /home/ubuntu/.ssh/authorized_keys
   chown -R ubuntu:ubuntu /home/ubuntu/.ssh
   chmod 600 /etc/ssh/ssh_host_*_key
   --//--
   ```
4. Start the instance. On boot, `cloud-init` runs the script as root and restores SSH access.
</details>

<details>
<summary><strong>● Are you comfortable with shell scripting? Would you be able to share your screen and write shell script logic for a couple of scenario-based problems?</strong></summary>

**Answer:**
Yes, I am completely comfortable writing production-ready Bash scripts on screen. I follow best practices: `set -euo pipefail`, signal handling with traps, clean functions, and structured logging.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Can you explain the architecture of Kubernetes, including the control plane and data plane? What are the key components, and what does each component do?</strong></summary>

**Answer:**
Kubernetes separates responsibilities between the **Control Plane** and the **Worker Nodes (Data Plane)**:

1. **Control Plane:**
   - **`kube-apiserver`:** Central REST API gateway, validating and configuring data for pods, services, and replication controllers.
   - **`etcd`:** Consistent, highly-available key-value store holding the entire cluster state.
   - **`kube-scheduler`:** Watches for newly created Pods and selects optimal nodes for them to run on based on resource availability and affinity rules.
   - **`kube-controller-manager`:** Runs core controllers (Node lifecycle, ReplicaSet reconciliation, EndpointSlice updates).
   - **`cloud-controller-manager`:** Integrates with underlying cloud provider APIs.

2. **Data Plane (Worker Nodes):**
   - **`kubelet`:** Node agent ensuring containers are running and healthy according to PodSpecs.
   - **`kube-proxy`:** Maintains network rules on nodes allowing network communication to Pods from inside or outside the cluster.
   - **Container Runtime (CRI):** Container engine (`containerd`) executing container processes.
</details>

<details>
<summary><strong>● What are the different types of deployment strategies used in Kubernetes?</strong></summary>

**Answer:**
- **RollingUpdate:** Gradually replaces old Pods with new ones (zero downtime).
- **Recreate:** Kills all old Pods before creating new ones (downtime).
- **Blue/Green:** Deploys new version in parallel; switches traffic instantaneously.
- **Canary:** Routes a fraction of traffic to the new version to validate metrics.
</details>

<details>
<summary><strong>↳ Follow-up: Can you explain the difference between the Recreate and Rolling Update deployment strategies in Kubernetes?</strong></summary>

**Answer:**
`RollingUpdate` provides zero-downtime by incrementally scaling up new pods while scaling down old pods. `Recreate` shuts down all existing pods simultaneously before launching new pods, causing a period of downtime but guaranteeing that two versions of the application never run at the same time.
</details>

<details>
<summary><strong>↳ Follow-up: Specifically, how does the Recreate strategy handle pod deployment when rolling out a new application version, compared to how the Rolling Update strategy handles new pods?</strong></summary>

**Answer:**
- **Recreate:** Sets old ReplicaSet replicas to `0`. Waits for all existing Pods to fully terminate. Once `0` running pods remain, sets new ReplicaSet replicas to desired count and starts new Pods.
- **RollingUpdate:** Calculates `maxSurge` and `maxUnavailable`. Starts a batch of new Pods first. Once new Pods pass readiness probes, it terminates an equivalent batch of old Pods, repeating until 100% migrated.
</details>

<details>
<summary><strong>● Can you explain what Ingress is in Kubernetes and why it was introduced? If you have 8 microservices and only one application load balancer, and you don't want to create multiple load balancers for each microservice, how does Ingress help solve this, and what is the traffic flow?</strong></summary>

**Answer:**
**Why Ingress Was Introduced:**
- A Kubernetes Service of type `LoadBalancer` provisions an independent cloud load balancer (ALB/NLB) per service. If you have 8 microservices, creating 8 separate ALBs costs ~$200/month and causes complex DNS management.
- **Ingress** is an API object providing Layer 7 routing rules (path and host-based) managed by a single **Ingress Controller** that provisions **one single Application Load Balancer**.

```
[ Client Request ] ──> [ Route 53 ] 
                            │
                            ▼
[ Single AWS Application Load Balancer (ALB) ]
                            │
                            ├── /users/*   ──> Target: user-service (Port 8080)
                            ├── /orders/*  ──> Target: order-service (Port 8080)
                            └── /payment/* ──> Target: payment-service (Port 8080)
```

**Traffic Flow:**
1. Client requests `https://api.company.com/orders`.
2. DNS resolves to the single ALB.
3. The **AWS Load Balancer Controller** configures ALB listener rules based on the Ingress resource.
4. The ALB routes traffic directly to the target pod IPs (via AWS VPC CNI) matching the `/orders` target group.
</details>

<details>
<summary><strong>● If a Kubernetes pod is continuously failing or stuck in a pending state, how would you troubleshoot it?</strong></summary>

**Answer:**
1. **Troubleshooting Pending Pods:**
   - Run `kubectl describe pod <pod-name>`. Check **Events**:
     - `0/10 nodes available: Insufficient cpu/memory`: Cluster is out of capacity (trigger node autoscaler).
     - `Pod has unbound immediate PersistentVolumeClaims`: Storage provisioning issue.
     - `MatchNodeSelector / Taints`: No node matches the pod's tolerations or node affinity.
2. **Troubleshooting Failing / CrashLoopBackOff Pods:**
   - Run `kubectl logs <pod-name> --previous` to see why the container crashed.
   - Inspect exit code in `kubectl describe pod`: Exit code 137 (OOMKilled) vs Exit code 1 (Application exception).
</details>

#### 【 NETWORKING 】

<details>
<summary><strong>● Have you worked with VPC Peering, Transit Gateway, and Direct Connect? Can you explain how VPC Peering and Transit Gateway work?</strong></summary>

**Answer:**
- **VPC Peering:** Point-to-point 1-to-1 connection between two VPCs. High performance, zero bandwidth fees in same AZ, but non-transitive.
- **Transit Gateway (TGW):** Central hub-and-spoke router connecting thousands of VPCs and on-premises networks with transitive routing.
- **Direct Connect (DX):** Dedicated physical private line between on-premise datacenter and AWS.
</details>

<details>
<summary><strong>↳ Follow-up: Can you continue explaining how AWS Transit Gateway works?</strong></summary>

**Answer:**
AWS Transit Gateway operates as a regional Layer 3 router. VPCs create **TGW Attachments** across multiple AZs. The TGW uses dedicated route tables with route association and propagation rules to route traffic across connected VPCs, Direct Connect gateways, and VPNs seamlessly.
</details>

<details>
<summary><strong>↳ Follow-up: If you need to connect three VPCs (A, B, and C) using VPC Peering, how would you ensure all three are interconnected? How do you establish these connections?</strong></summary>

**Answer:**
Because VPC Peering is non-transitive, you must create a **Full Mesh** of 3 peering connections:
1. Create Peering: `A <-> B`, `B <-> C`, and `A <-> C`.
2. Accept peering requests in each peer account.
3. Update Route Tables in VPC A, VPC B, and VPC C with explicit CIDR routes pointing to each respective `pcx-xxxx` ID.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● If a junior team member comes to you saying they are unable to SSH into an EC2 instance (getting a timeout), how would you troubleshoot this? What initial things would you check, and what might be the possible causes?</strong></summary>

**Answer:**
A **timeout** means packets are dropped at the network layer:
1. Check Security Group: Does port 22 allow the junior's current public IP?
2. Check Route Table: Is there a default route to an Internet Gateway (`0.0.0.0/0 -> igw-xxx`)?
3. Check Public IP: Does the instance have an allocated Public IP?
4. Check NACL: Are port 22 and outbound ephemeral ports allowed?
</details>

<details>
<summary><strong>↳ Follow-up: Assuming the user already has all the necessary access permissions and regularly uses a UAT/staging/dev EC2 instance, but suddenly cannot SSH into it, what other reasons (besides access/IAM issues) could cause this?</strong></summary>

**Answer:**
1. Dynamic public IP change on client home network.
2. Host firewall (`iptables` / `ufw`) blocking port 22.
3. SSH daemon crashed or hung inside the OS.
4. CPU / Memory 100% starvation causing kernel lockup.
5. Disk full (100% space/inodes) preventing SSH session file creation.
</details>

<details>
<summary><strong>● What is an S3 bucket, and why is it used in AWS?</strong></summary>

**Answer:**
An S3 bucket is a globally unique top-level container for storing objects (files and metadata) in Amazon S3. It provides 11 9's durability, automated lifecycle tiering, encryption, and limitless scalability for backups, data lakes, and media storage.
</details>

<details>
<summary><strong>● Have you worked with AWS RDS and Aurora? Can you explain the architectural difference between RDS and Aurora?</strong></summary>

**Answer:**
- **RDS:** Monolithic compute tied to standard EBS volumes; asynchronous binlog replication to replicas; 60–120s failover.
- **Aurora:** Decouples compute from storage; distributed 6-way replicated storage across 3 AZs; shared storage layer with near-zero replica lag; sub-30s failover.
</details>

<details>
<summary><strong>● If a client wants to save costs by installing MySQL directly on an EC2 instance instead of using RDS, how would you convince them of the advantages of using RDS over self-managing a database on EC2?</strong></summary>

**Answer:**
Present the Total Cost of Ownership (TCO): While EC2 saves a small margin on hourly compute, RDS eliminates the massive engineering cost and downtime risk of manual backups, manual Multi-AZ failover configurations, operating system patching, and storage expansions.
</details>

<details>
<summary><strong>↳ Follow-up: What specific advantages do you get from using RDS (with MySQL) compared to installing and managing MySQL yourself on an EC2 instance long-term?</strong></summary>

**Answer:**
1. Automated Multi-AZ synchronous failover.
2. Automated Point-in-Time Recovery (PITR) up to 35 days.
3. One-click read replicas.
4. Push-button storage autoscaling with zero downtime.
5. Automated minor version OS and DB engine patching.
</details>

<details>
<summary><strong>● Can you explain the difference between Network ACLs (NACLs) and Security Groups in AWS?</strong></summary>

**Answer:**
- **Security Group:** Operates at instance/ENI level; stateful; allows only ALLOW rules; all rules evaluated together.
- **NACL:** Operates at subnet level; stateless; supports both ALLOW and DENY rules; evaluated in strict numerical order.
</details>

<details>
<summary><strong>● Have you worked on any cost optimization techniques for AWS infrastructure to reduce costs? Can you describe how you implemented them?</strong></summary>

**Answer:**
Yes:
1. **Savings Plans & Spot Instances:** Compute Savings Plans for base load, Karpenter Spot instances for non-prod Kubernetes nodes.
2. **Storage Management:** S3 Lifecycle policies to Glacier, automated cleanup of untagged EBS snapshots and orphaned volumes via Lambda.
3. **Architecture Optimization:** Migrating x86 to Graviton3 instances; adding S3 Gateway Endpoints to eliminate NAT Gateway transfer costs.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself, including your experience, your role in your previous company, and the tools, technologies, and domains you worked on?

</details>
</details>
