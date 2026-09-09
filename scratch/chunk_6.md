<details open>
<summary><h2>🏢 Apexon</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 26-08-2026 02:41 PM*

#### 【 CI/CD 】

<details>
<summary><strong>● Can you explain the flow of your Jenkins CI/CD pipeline?</strong></summary>

**Answer:**
In our production setup, we run an automated, GitOps-aligned Declarative Pipeline running on dynamic Kubernetes agents:

1. **Trigger & Checkout:** A pull request or push event in GitHub triggers Jenkins via webhook. Jenkins dynamically provisions an ephemeral agent pod on our EKS cluster.
2. **Static Code Analysis & Unit Testing:** Executes unit tests (`mvn clean test` or `npm test`) and sends reports to **SonarQube** using `withSonarQubeEnv`. The pipeline halts at `waitForQualityGate()` if code coverage drops below 80% or any high/critical security vulnerability is found.
3. **Container Build & Scanning:** Docker build creates an image tagged with the Git commit SHA (`${IMAGE_NAME}:${GIT_COMMIT}`). The image is scanned for CVEs using **Trivy** (`trivy image --severity HIGH,CRITICAL --exit-code 1`).
4. **Publish Artifact:** The authenticated image is pushed to **Amazon ECR** using temporary IAM credentials.
5. **GitOps CD Sync:** Rather than executing direct `kubectl apply`, the pipeline clones our Kubernetes GitOps manifest repository, updates the image tag in Helm `values.yaml`, and commits. **Argo CD** detects the Git drift and safely synchronizes the deployment to the staging/production cluster using a rolling or canary strategy.
</details>

<details>
<summary><strong>↳ Follow-up: If you push a Docker image to ECR from your Jenkins pipeline, how does the CD pipeline automatically pick up the latest tag of that image?</strong></summary>

**Answer:**
There are two production patterns we implement:

1. **GitOps Repository Update Pattern (Recommended):**
   - After Jenkins builds and pushes `app:sha-1a2b3c` to ECR, the pipeline executes a step to update our GitOps repository (where Helm charts or Kustomize manifests reside):
     ```bash
     git clone https://github.com/org/gitops-repo.git
     cd gitops-repo/environments/prod
     yq e '.image.tag = "sha-1a2b3c"' -i values.yaml
     git commit -am "ci(image): update payment-service to sha-1a2b3c [skip ci]"
     git push origin main
     ```
   - **Argo CD** polls or receives a GitHub push webhook and reconciles the desired state in the EKS cluster within seconds.

2. **Event-Driven Image Automation:**
   - We utilize **Argo CD Image Updater** or **Flux Image Reflector/Automation Controller**. It monitors the AWS ECR registry via API/ECR EventBridge events. When a new tag matching a semantic versioning regex or timestamp is detected, it automatically writes the update back to Git and synchronizes the cluster.
</details>

<details>
<summary><strong>● How would you integrate a SonarQube server with Jenkins?</strong></summary>

**Answer:**
The integration is established through the following configuration steps:

1. **Plugin Installation & Global Config:**
   - Install the **SonarQube Scanner** plugin on Jenkins.
   - Under `Manage Jenkins -> System -> SonarQube servers`, add the SonarQube server URL (e.g., `https://sonarqube.internal.corp`) and bind a Jenkins Secret Text credential containing an authentication token generated from SonarQube (`User -> My Account -> Security -> Tokens`).

2. **Webhook Configuration:**
   - In SonarQube (`Administration -> Configuration -> Webhooks`), add a webhook targeting Jenkins: `https://<jenkins-url>/sonarqube-webhook/`. This enables Jenkins to receive asynchronous notifications when background analysis finishes.

3. **Pipeline Implementation:**
   ```groovy
   stage('SonarQube Analysis') {
       steps {
           withSonarQubeEnv('SonarQube-Server') {
               sh 'mvn sonar:sonar -Dsonar.projectKey=payment-service'
           }
       }
   }
   stage('Quality Gate') {
       steps {
           timeout(time: 5, unit: 'MINUTES') {
               script {
                   def qg = waitForQualityGate()
                   if (qg.status != 'OK') {
                       error "Pipeline aborted: Quality gate failed with status ${qg.status}"
                   }
               }
           }
       }
   }
   ```
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>↳ Follow-up: If you noticed an issue with the liveness probe and readiness probe configuration in Kubernetes, how would you fix it?</strong></summary>

**Answer:**
Fixing misconfigured probes involves root cause identification and tuning probe parameters:

1. **Common Failure Symptoms & Root Causes:**
   - **Premature Liveness Kills:** If `initialDelaySeconds` is too low for a slow-starting JVM/Spring application, the liveness probe fails while the app is still initializing, causing repeated `CrashLoopBackOff` restarts.
   - **Flapping Readiness:** If `timeoutSeconds` or `failureThreshold` is too aggressive during brief CPU spikes, the pod is repeatedly removed and added to the Service endpoint list.
   - **Deep Dependency Probing:** Probing `/health` which internally queries a database or external cache. If the database latency spikes, all pods fail their probes simultaneously, triggering a catastrophic cascading failure.

2. **Remediation Steps:**
   - **Use Startup Probes:** Add a `startupProbe` to give slow apps up to 3–5 minutes to boot before liveness probes activate:
     ```yaml
     startupProbe:
       httpGet:
         path: /healthz
         port: 8080
       failureThreshold: 30
       periodSeconds: 10
     livenessProbe:
       httpGet:
         path: /livez
         port: 8080
       periodSeconds: 10
       timeoutSeconds: 3
       failureThreshold: 3
     readinessProbe:
       httpGet:
         path: /readyz
         port: 8080
       periodSeconds: 5
       timeoutSeconds: 2
       failureThreshold: 2
     ```
   - **Decouple Dependencies:** Configure `/livez` to check only local process responsiveness, and `/readyz` to check if internal buffers/queues can accept new traffic, never cascading external dependencies.
</details>

<details>
<summary><strong>● What are the Deployment controller and ReplicaSet controller in Kubernetes?</strong></summary>

**Answer:**
Both are control loop mechanisms running inside the `kube-controller-manager` that maintain desired application state:

1. **ReplicaSet Controller:**
   - Its primary responsibility is to guarantee that a specified number of identical Pod replicas are running at any given time (`spec.replicas`).
   - It continuously compares observed cluster state with the pod selector criteria using label selectors. If there are fewer pods than desired, it creates new ones via the API server; if there are excess pods, it deletes them.

2. **Deployment Controller:**
   - Operates at a higher abstraction level above ReplicaSets.
   - Manages declarative updates, rolling updates, rollbacks, and pause/resume mechanisms for applications.
   - When a Deployment's pod template is modified (e.g., updating container image), the Deployment controller creates a **new ReplicaSet**, scales it up gradually, while scaling down the old ReplicaSet according to `maxSurge` and `maxUnavailable` settings.
   - If a rollback (`kubectl rollout undo deployment/<name>`) is issued, the Deployment controller points back to the earlier ReplicaSet revision without deleting previous ReplicaSets.
</details>

#### 【 IAC 】

<details>
<summary><strong>● Can you write a Terraform script to create three resources named 'dev', 'test', and 'prod'?</strong></summary>

**Answer:**
Using `for_each` with a map or set is the production-grade approach because deleting or reordering an environment does not shift index positions (unlike `count`):

```hcl
variable "environments" {
  description = "Target environment specifications"
  type = map(object({
    instance_type = string
    env_tag       = string
  }))
  default = {
    "dev"  = { instance_type = "t3.micro", env_tag = "Development" }
    "test" = { instance_type = "t3.small", env_tag = "Testing" }
    "prod" = { instance_type = "m5.large", env_tag = "Production" }
  }
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }
}

resource "aws_instance" "env_instances" {
  for_each = var.environments

  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = each.value.instance_type

  tags = {
    Name        = "app-server-${each.key}"
    Environment = each.value.env_tag
    ManagedBy   = "Terraform"
  }
}

output "instance_private_ips" {
  value = { for k, v in aws_instance.env_instances : k => v.private_ip }
}
```
</details>

<details>
<summary><strong>↳ Follow-up: What are input variables and output values in Terraform?</strong></summary>

**Answer:**
1. **Input Variables (`variable`):**
   - Serve as parameters to customize Terraform modules and configurations without altering the underlying code.
   - Support strict type constraints (`string`, `number`, `bool`, `list`, `map`, `object`), default values, descriptions, and custom validation blocks:
     ```hcl
     variable "environment" {
       type        = string
       description = "Target deployment environment"
       validation {
         condition     = contains(["dev", "staging", "prod"], var.environment)
         error_message = "Environment must be one of: dev, staging, prod."
       }
     }
     ```

2. **Output Values (`output`):**
   - Expose information about resources created by Terraform.
   - Enable sharing data between parent and child modules, exposing values to CLI callers (`terraform output`), or querying them via `terraform_remote_state` data sources.
   - Can be flagged with `sensitive = true` to mask sensitive values (passwords, tokens) in terminal logs.
</details>

<details>
<summary><strong>↳ Follow-up: How would you take the instance name as an input from the user in a Terraform configuration?</strong></summary>

**Answer:**
You can declare an input variable without a default value, or pass it via several standard Terraform precedence channels:

1. **Variable Declaration (`variables.tf`):**
   ```hcl
   variable "instance_name" {
     type        = string
     description = "The human-readable tag name for the EC2 instance"
     nullable    = false
   }

   resource "aws_instance" "web" {
     ami           = "ami-0c55b159cbfafe1f0"
     instance_type = "t3.medium"

     tags = {
       Name = var.instance_name
     }
   }
   ```

2. **Passing Input from User:**
   - **CLI Prompt:** If no default is provided and no variable flag is passed, Terraform interactively prompts in the terminal: `var.instance_name:`.
   - **CLI Flag:** `terraform apply -var="instance_name=payment-gateway-prod"`
   - **Environment Variable:** `export TF_VAR_instance_name="payment-gateway-prod"` followed by `terraform apply`.
   - **`.tfvars` File:** In `terraform.tfvars`: `instance_name = "payment-gateway-prod"`.
</details>

#### 【 NETWORKING 】

<details>
<summary><strong>● If your database server is in a private subnet, how would your EC2 instance communicate with that database server?</strong></summary>

**Answer:**
Direct communication is governed by VPC networking, routing, and Security Group chaining:

1. **Subnet & Route Table Architecture:**
   - Both the EC2 instance (application tier) and database instance (RDS/Aurora or self-hosted DB) reside within the same AWS VPC across private subnets.
   - The VPC's local route table entry (`10.0.0.0/16 -> local`) enables routing across all subnets in the VPC by default without needing an Internet Gateway or NAT Gateway.

2. **Security Group Referencing (Defense-in-Depth):**
   - Rather than whitelisting IP addresses or CIDR blocks, the Database Security Group (`sg-db`) allows inbound traffic on port 5432 (PostgreSQL) or 3306 (MySQL) **referencing the application EC2 Security Group ID (`sg-app`)**:
     ```hcl
     resource "aws_security_group_rule" "db_ingress_from_app" {
       type                     = "ingress"
       from_port               = 5432
       to_port                 = 5432
       protocol                = "tcp"
       source_security_group_id = aws_security_group.app_sg.id
       security_group_id        = aws_security_group.db_sg.id
     }
     ```
   - This ensures that only EC2 instances with `sg-app` attached can communicate with the database, regardless of instance auto-scaling or IP churn.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● If your application is running in a private subnet and you need to apply security patches or upgrades, how would you go about doing that?</strong></summary>

**Answer:**
We implement two production strategies depending on whether instances are mutable or immutable:

1. **Immutable Infrastructure Strategy (Industry Best Practice):**
   - We do not patch live production instances. Instead, we use **HashiCorp Packer** to build a newly patched Golden AMI with the latest OS CVE updates and application binaries.
   - We update the Launch Template in Terraform and trigger an **Auto Scaling Group (ASG) Instance Refresh**:
     ```bash
     aws autoscaling start-instance-refresh \
       --auto-scaling-group-name prod-app-asg \
       --preferences '{"MinHealthyPercentage": 100, "InstanceWarmup": 300}'
     ```
   - ASG spins up new patched instances, passes health checks, and terminates unpatched instances zero-downtime.

2. **In-Place Patching via AWS Systems Manager (SSM):**
   - If in-place OS patching is mandated:
     - The private subnet routes outbound traffic through a **NAT Gateway** (or AWS VPC Endpoints for Systems Manager: `ssm`, `ssmmessages`, `ec2messages`).
     - Instances have the **AmazonSSMManagedInstanceCore** IAM policy attached.
     - **AWS SSM Patch Manager** applies Patch Baselines via scheduled Maintenance Windows without needing inbound SSH or public IPs.
</details>

<details>
<summary><strong>● What is EBS (Elastic Block Store) and what is ELB (Elastic Load Balancer) in AWS?</strong></summary>

**Answer:**
1. **EBS (Elastic Block Store):**
   - Network-attached, persistent block-level storage designed for EC2 instances.
   - Operates within a single Availability Zone (replicated across multiple servers to prevent hardware failure).
   - Can be formatted with filesystems (ext4, xfs) for databases, OS root volumes, and low-latency storage.
   - Volume types include **gp3** (general purpose SSD with baseline 3,000 IOPS / 125 MB/s), **io2 Block Express** (high-performance databases up to 256,000 IOPS), and **st1/sc1** (throughput-optimized HDD). Supports point-in-time automated snapshots to S3.

2. **ELB (Elastic Load Balancer):**
   - Fully managed traffic distribution service that routes incoming application traffic across multiple EC2 targets, containers, IP addresses, and Lambda functions across multiple Availability Zones.
   - Types of ELB:
     - **ALB (Application Load Balancer):** Layer 7 (HTTP/HTTPS), supports host/path routing, gRPC, WebSockets, and AWS WAF integration.
     - **NLB (Network Load Balancer):** Layer 4 (TCP/UDP/TLS), ultra-low latency, handles millions of requests per second, provides static elastic IPs.
     - **GWLB (Gateway Load Balancer):** Deploys and scales 3rd-party virtual appliances (firewalls, IDS/IPS).
</details>

#### 【 SECURITY 】

<details>
<summary><strong>● Where do you store secrets used in your CI/CD pipeline?</strong></summary>

**Answer:**
We adhere to zero-plain-text secret storage using centralized enterprise secret managers:

1. **AWS Secrets Manager / HashiCorp Vault:**
   - Production API tokens, database credentials, and SSL certificates are stored in AWS Secrets Manager or HashiCorp Vault with automated rotation policies.
2. **Short-Lived OIDC Authentication (Zero Stored Credentials):**
   - For cloud access (AWS/Azure/GCP), we configure **OpenID Connect (OIDC)** between GitHub Actions / Jenkins and AWS IAM. The pipeline requests an ephemeral JWT token from AWS STS (`AssumeRoleWithWebIdentity`), eliminating static `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` completely.
3. **Encrypted Pipeline Secrets:**
   - For credentials required directly by the CI engine, we store them as masked, encrypted variables in Jenkins Credentials Manager (backed by `credentials-binding` plugin) or GitHub Encrypted Secrets.
</details>

<details>
<summary><strong>● How would you store secrets in Jenkins and Kubernetes?</strong></summary>

**Answer:**
1. **In Jenkins:**
   - Stored in the **Jenkins Credentials Store** under strictly scoped domains/folders.
   - Formats: Secret text, Username with password, Secret file, SSH Username with private key.
   - Accessed in Declarative Pipelines via `withCredentials`:
     ```groovy
     withCredentials([usernamePassword(credentialsId: 'ecr-user-creds', usernameVariable: 'ECR_USER', passwordVariable: 'ECR_PASSWORD')]) {
         sh 'echo $ECR_PASSWORD | docker login -u $ECR_USER --password-stdin'
     }
     ```
   - Sensitive variables are automatically masked in console outputs.

2. **In Kubernetes:**
   - **Native Kubernetes Secrets:** Stored as `Secret` objects. However, base64 encoding is not encryption. At rest, they must be encrypted in etcd using `KMS Provider` (e.g., AWS KMS with EKS envelope encryption).
   - **External Secrets Operator (ESO) (Recommended Production Pattern):**
     - Rather than hardcoding secrets in Git, we deploy ESO. A `SecretStore` connects via IAM Roles for Service Accounts (IRSA) to AWS Secrets Manager.
     - ESO dynamically synchronizes cloud secrets into Kubernetes `v1/Secret` objects:
       ```yaml
       apiVersion: external-secrets.io/v1beta1
       kind: ExternalSecret
       metadata:
         name: db-credentials
       spec:
         refreshInterval: 1h
         secretStoreRef:
           name: aws-secret-store
           kind: ClusterSecretStore
         target:
           name: db-secret
         data:
           - secretKey: password
             remoteRef:
               key: prod/rds/postgres
               property: db_password
       ```
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● If an application is not working in production, what steps would you take to troubleshoot and resolve the issue?</strong></summary>

**Answer:**
I execute an incident triage framework to restore service while preserving diagnostic evidence:

1. **Initial Assessment & Blast Radius:**
   - Check status dashboards (Datadog/Grafana/CloudWatch), alert channels, and customer impact. Check if this correlates with a recent release, deployment, or configuration change.
2. **Edge & Ingress Verification:**
   - Trace from the outside in: Is DNS resolving? Is the ALB returning HTTP 502/503/504? Inspect ALB target health metrics (`TargetResponseTime`, `HTTPCode_Target_5XX_Count`).
3. **Cluster & Pod Diagnostics:**
   - Run `kubectl get pods -n prod -o wide`: Check for `CrashLoopBackOff`, `OOMKilled`, or `Pending` pods.
   - Run `kubectl describe pod <pod-name>`: Check Recent Events for failed readiness probes, volume mount issues, or node resource pressure.
4. **Logs & APM Traces:**
   - Inspect container logs: `kubectl logs <pod-name> --tail=200 --previous`.
   - Query APM/Distributed tracing (OpenSearch / Datadog / Jaeger) to pinpoint the exact failing stack trace or slow downstream microservice.
5. **Mitigation First (Restore Service):**
   - If caused by a new deployment, initiate an immediate rollback via Argo CD (`git revert`) or Helm rollback (`helm rollback app-release <previous-rev>`).
   - If caused by resource exhaustion, scale out replicas or increase node capacity.
6. **Post-Incident Review:**
   - Conduct a blameless post-mortem, determine root cause using the 5 Whys, and implement preventive alert and architectural fixes.
</details>

<details>
<summary><strong>● How is migration typically carried out in your organization?</strong></summary>

**Answer:**
We execute cloud or microservice migrations using the **AWS 6 Rs Framework** (Rehost, Replatform, Refactor, Repurchase, Retain, Retire) backed by a phased migration lifecycle:

1. **Discovery & Assessment:**
   - Inventory applications, data stores, network dependencies, latency tolerances, and licensing constraints using tools like AWS Application Discovery Service.
2. **Landing Zone Foundation:**
   - Provision multi-account AWS Organizations landing zone with Terraform/Control Tower, configuring Transit Gateway, Direct Connect, IAM SSO, and security guardrails.
3. **Proof of Concept (PoC) & Pilot:**
   - Migrate non-critical workloads to validate the automated CI/CD pipelines, containerization scripts, and network performance.
4. **Data Migration Strategy:**
   - **Database Migration:** AWS DMS (Database Migration Service) with continuous Change Data Capture (CDC) replication maintains zero-downtime synchronization between on-prem and cloud databases.
   - **File/Object Storage:** AWS DataSync or AWS Snowball for petabyte-scale data transfers.
5. **Cutover & Validation:**
   - Execute dry runs in staging. During cutover window, switch traffic using Amazon Route 53 Weighted Routing (gradual shift from on-prem to cloud: 10% -> 50% -> 100%).
6. **Optimization & Modernization:**
   - Post-migration rightsizing, implementing Graviton processors, Spot instances, and transitioning monolithic applications into Kubernetes microservices.
</details>
</details>
</details>

<details open>
<summary><h2>🏢 Nitor Infotech</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 CI/CD 】

<details>
<summary><strong>● Could you elaborate on a specific challenge you faced in a CI/CD pipeline and how you resolved it?</strong></summary>

**Answer:**
- **The Challenge:** Our Jenkins CI build times escalated from 8 minutes to over 42 minutes as our monorepo microservice architecture expanded. The Jenkins EC2 controller suffered high CPU load, Docker builds constantly contended for local disk I/O, and build queues backed up during peak sprint release hours.
- **Root Causes:**
  1. Docker builds lacked remote layer caching and re-downloaded hundreds of megabytes of npm and Maven dependencies on every execution.
  2. Sequential execution of integration test suites and security scans.
  3. Static, fixed-size EC2 Jenkins worker instances leading to resource saturation.
- **The Resolution:**
  1. **Dynamic Ephemeral Kubernetes Agents:** Migrated Jenkins workers to Kubernetes pods running on AWS EKS using the Jenkins Kubernetes plugin, scaling automatically from 0 to 50 concurrent build pods.
  2. **Multi-Stage Builds & Remote Cache:** Implemented `docker buildx` with `--cache-from` and `--cache-to` backed by an ECR registry cache, cutting image build time by 70%.
  3. **Parallelized Pipeline Stages:** Parallelized unit tests, SAST scanning (SonarQube), and dependency vulnerability scans (Trivy) using declarative `parallel { }` blocks.
  4. **Persistent Dependency Caching:** Mounted an EFS PVC to worker pods to cache Maven `.m2` and npm caches across builds.
- **Impact:** Average pipeline duration dropped from 42 minutes to **6.5 minutes**, and developer deployment velocity tripled with zero queue bottlenecks.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Can you explain the core components of Kubernetes?</strong></summary>

**Answer:**
Kubernetes architecture is bifurcated into the **Control Plane** and **Worker Node** components:

1. **Control Plane Components (Cluster Brain):**
   - **kube-apiserver:** The front end of the control plane; exposes the Kubernetes REST API. All internal and external communications pass through it.
   - **etcd:** Distributed, consistent, highly available key-value store holding the complete state and configuration data of the cluster.
   - **kube-scheduler:** Watches for newly created pods with no assigned node and selects the best worker node based on resource requests/limits, affinities, taints, and tolerations.
   - **kube-controller-manager:** Runs controller background loops (Node Controller, Replication Controller, EndpointSlice Controller, ServiceAccount Controller).
   - **cloud-controller-manager:** Interacts with underlying cloud providers (AWS, Azure) to manage cloud resources (LBs, EBS volumes, routes).

2. **Worker Node Components (Workload Execution):**
   - **kubelet:** Primary node agent. Registers node with API server, watches `PodSpecs`, instructs container runtime to pull images and start/stop containers, and reports health.
   - **kube-proxy:** Network proxy maintaining network rules on nodes (via iptables or IPVS) to enable Kubernetes Service IP routing across pods.
   - **Container Runtime:** Software executing containers (containerd, CRI-O).
</details>

<details>
<summary><strong>● What are the options for running Kubernetes on AWS?</strong></summary>

**Answer:**
AWS provides multiple approaches based on control, operational overhead, and flexibility:

1. **Amazon EKS (Elastic Kubernetes Service) with Managed Node Groups (Most Popular):**
   - AWS manages and guarantees the Control Plane SLA (99.95%).
   - You run worker nodes on EC2 instances managed by AWS EKS AMI lifecycle and Auto Scaling Groups.
2. **Amazon EKS with AWS Fargate (Serverless Containers):**
   - Removes worker node management entirely. Every pod runs in its own dedicated, isolated microVM compute environment. You pay strictly for requested vCPU and memory.
3. **Amazon EKS with Karpenter (Modern Production Standard):**
   - Dynamic, high-speed node autoscaler replacing Kubernetes Cluster Autoscaler. Launches right-sized EC2 instances directly via AWS APIs within 30-45 seconds based on unschedulable pod requirements.
4. **Self-Managed Kubernetes on EC2 (kOps / kubeadm):**
   - Full control over control plane and etcd nodes on raw EC2 instances. Incurs high operational burden for patching, scaling, high availability, and backups.
5. **Amazon EKS Anywhere:**
   - Enables running EKS clusters on customer on-premises infrastructure (bare metal or VMware vSphere) with centralized AWS console management.
</details>

<details>
<summary><strong>● What is Helm, and can you explain its structure?</strong></summary>

**Answer:**
**Helm** is the package manager for Kubernetes. It packages multiple Kubernetes resource manifests (Deployments, Services, ConfigMaps, Ingress, HPA) into a versioned, reusable release unit called a **Helm Chart**.

**Standard Helm Chart Structure:**
```
my-microservice/
├── Chart.yaml          # Metadata: chart name, version, appVersion, dependencies
├── values.yaml         # Default configuration values for templates
├── values-staging.yaml  # Environment-specific overrides
├── values-prod.yaml     # Production override values
├── charts/             # Subcharts/chart dependencies (e.g., redis, postgresql)
└── templates/          # Templated Kubernetes manifest files (Go templating)
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    ├── hpa.yaml
    ├── configmap.yaml
    ├── _helpers.tpl    # Reusable template snippets and label definitions
    └── NOTES.txt       # Instructions printed to CLI upon helm install
```
</details>

<details>
<summary><strong>↳ Follow-up: How does Helm manage upgrades and rollbacks of releases?</strong></summary>

**Answer:**
1. **Release Tracking via Secrets:**
   - Helm stores each release's state and manifest history as a versioned Kubernetes Secret (or ConfigMap) inside the target namespace:
     `sh.helm.release.v1.<release-name>.v1`, `sh.helm.release.v1.<release-name>.v2`, etc.
   - Each secret contains base64-encoded, gzip-compressed metadata of the deployed manifests and user-supplied values.

2. **Upgrades (`helm upgrade <release-name> <chart-path> -f values.yaml`):**
   - Helm renders the new template against provided values, computes a three-way diff between the current live state, previous release manifest, and newly proposed manifest, and applies changes via API server patch operations. A new release revision (e.g., `v3`) is created.

3. **Rollbacks (`helm rollback <release-name> <revision-number>`):**
   - When a rollback is commanded (`helm rollback my-app 1`), Helm reads the secret corresponding to revision 1, renders those manifests, and applies them to the cluster.
   - Importantly, Helm generates a **new revision** (e.g., `v4`) whose content mirrors revision 1, maintaining an immutable forward-only audit trail of operations.
</details>

<details>
<summary><strong>● How do you scale an application in Kubernetes?</strong></summary>

**Answer:**
Scaling is managed across both pod (workload) and node (infrastructure) tiers:

1. **Pod-Level Scaling:**
   - **Manual Scaling:** `kubectl scale deployment <name> --replicas=10`.
   - **Horizontal Pod Autoscaler (HPA):** Dynamically scales pod replicas based on metrics:
     - Standard metrics: CPU (`targetCPUUtilizationPercentage: 70`) and Memory utilization queried via Metrics Server.
     - Custom metrics: HTTP requests per second, queue depth via Prometheus Adapter.
   - **Vertical Pod Autoscaler (VPA):** Dynamically adjusts CPU and memory `requests` and `limits` for existing pods.
   - **KEDA (Kubernetes Event-driven Autoscaling):** Scales workloads to zero or hundreds based on external triggers (Kafka consumer lag, RabbitMQ queues, AWS SQS depth).

2. **Node-Level Scaling:**
   - **Cluster Autoscaler:** Monitors unschedulable `Pending` pods and scales up AWS Auto Scaling Groups.
   - **Karpenter:** Rapid, node-group-less provisioning directly selecting optimal EC2 instance types and Spot/On-Demand mixes in ~40 seconds.
</details>

<details>
<summary><strong>● If a pod is stuck in a CrashLoopBackOff error, how would you troubleshoot it?</strong></summary>

**Answer:**
`CrashLoopBackOff` indicates that the container repeatedly starts, fails, exits, and Kubernetes is backing off before restarting it again. My troubleshooting procedure:

1. **Inspect Pod Status and Exit Codes:**
   ```bash
   kubectl get pods -n <namespace>
   kubectl describe pod <pod-name> -n <namespace>
   ```
   - Look under `Containers[].State.Last State`:
     - **Exit Code 1:** General application runtime error (uncaught exception, missing config file).
     - **Exit Code 137:** Process received `SIGKILL` — typically **OOMKilled** (Out Of Memory). Verify `OOMKilled: true` in `kubectl describe`.
     - **Exit Code 139:** Segmentation fault.
     - **Exit Code 127:** Command or entrypoint binary not found inside container image.

2. **Analyze Application Logs:**
   ```bash
   # Check logs from the failing container instance
   kubectl logs <pod-name> -c <container-name> -n <namespace>
   # Check logs from the previously crashed container instance
   kubectl logs <pod-name> -c <container-name> -n <namespace> --previous
   ```

3. **Verify Configuration Dependencies:**
   - Check if environment variables, ConfigMaps, or Secrets referenced by the pod actually exist.
   - Check database connectivity, network policies, or missing DNS hostnames.

4. **Interactive Debugging:**
   - If the container exits immediately, override entrypoint using an ephemeral debug container:
     ```bash
     kubectl debug -it <pod-name> --image=busybox:latest --target=<container-name>
     ```
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● How does AWS manage the control plane in Amazon EKS?</strong></summary>

**Answer:**
Amazon EKS runs a single-tenant, managed Kubernetes control plane across at least three Availability Zones (AZs) within an AWS-managed VPC:

1. **High Availability Architecture:**
   - AWS provisions at least two API server instances and three `etcd` instances spanning 3 separate AZs to ensure tolerance against single-AZ outages.
   - EKS automatically detects and replaces unhealthy control plane instances without customer disruption.

2. **Scaling & Load Balancing:**
   - An AWS-managed Network Load Balancer (NLB) sits in front of the API servers, scaling dynamically based on traffic and API request volumes.
   - EKS auto-scales control plane instance compute and storage resources behind the scenes when cluster load increases.

3. **Connectivity to Worker Nodes:**
   - EKS provisions cross-account Elastic Network Interfaces (ENIs) directly into the customer's worker node subnets. This facilitates secure bidirectional communication between the EKS control plane (API server) and worker nodes (`kubelet`, `kube-proxy`) without exposing traffic to the public internet.

4. **SLA & Maintenance:**
   - AWS guarantees a 99.95% uptime SLA for the EKS control plane endpoint. Control plane version upgrades are orchestrated zero-downtime with etcd schema migrations handled automatically.
</details>

#### 【 SECURITY 】

<details>
<summary><strong>● How do you secure an EKS cluster?</strong></summary>

**Answer:**
Securing an EKS cluster requires defense-in-depth across identity, network, workload, and data:

1. **Authentication & Authorization:**
   - Disable raw `aws-auth` ConfigMap and adopt **EKS Access Entries** integrated with AWS IAM Identity Center (SSO).
   - Enforce Kubernetes RBAC adhering to the principle of least privilege.
   - Use **IRSA (IAM Roles for Service Accounts)** or EKS Pod Identities so pods assume short-lived, least-privilege IAM roles instead of inheriting worker node instance profile permissions.

2. **Control Plane & Network Security:**
   - Set cluster API server endpoint to **Private Only** (accessible only via VPN, Direct Connect, or bastion).
   - Implement **Kubernetes NetworkPolicies** (via Calico or AWS VPC CNI Network Policy engine) to enforce default-deny egress/ingress between namespaces and pods.
   - Deploy Security Groups per Pod using AWS VPC CNI.

3. **Workload & Container Security:**
   - Enforce **Pod Security Standards (PSS)** at `Restricted` level using Admission Controllers (Kyverno or OPA Gatekeeper): block running as root (`runAsNonRoot: true`), drop all capabilities (`drop: ["ALL"]`), make root filesystem read-only.
   - Scan container images in ECR using AWS Inspector / Trivy before deployment.

4. **Data Protection & Auditing:**
   - Enable **Envelope Encryption** for Kubernetes Secrets in `etcd` using an AWS KMS Customer Managed Key (CMK).
   - Enable EKS control plane logging (API, Audit, Authenticator, ControllerManager, Scheduler) to Amazon CloudWatch and ingest into SIEM.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you tell me about yourself?
</details>
</details>

<details open>
<summary><h2>🏢 Valtriix</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 03-09-2026 02:06 AM*

#### 【 GIT 】

<details>
<summary><strong>↳ Follow-up: When you mentioned that you create the PR, what exactly do you mean by 'creating the PR'?</strong></summary>

**Answer:**
"Creating a Pull Request (PR)" or Merge Request means submitting a formal proposal to merge code changes from an isolated working branch (such as `feature/user-auth` or `bugfix/cart-null-pointer`) into a target shared branch (such as `develop` or `main`).

Technically and operationally, creating a PR involves:
1. Pushing the local branch commits to the remote Git repository (`git push origin feature/user-auth`).
2. Initiating the PR through GitHub CLI (`gh pr create --base develop --head feature/user-auth --title "feat: user authentication"`) or the Web UI.
3. Specifying release context: detailed description, Jira issue links, risk assessments, and test evidence.
4. Designating code reviewers and code owners (`CODEOWNERS`).
5. Triggering automated pre-merge checks (CI build, SonarQube quality gate, security linting) which must pass before merge eligibility.
</details>

<details>
<summary><strong>↳ Follow-up: Isn't the PR creation process entirely handled by GitHub itself, with no manual action needed from your side?</strong></summary>

**Answer:**
No, GitHub provides the platform and hosting infrastructure, but GitHub does **not** automatically decide when, why, or which target branch a developer wants to merge into without an intentional action or automation script.

- **Standard Workflow:** A developer or engineer must explicitly initiate the PR by specifying the source branch, target base branch, PR title, description, and reviewers.
- **Automated PR Exceptions:** In DevOps automation, PR creation can be automated via scripts, CLI, or GitHub Actions. For instance:
  - **Dependabot / Renovate:** Automatically scans package manifests and opens PRs when security patches are released.
  - **CI Bot Updates:** When a new container image is built, a Jenkins pipeline can execute `gh pr create` or call the GitHub REST API to submit a PR against a GitOps configuration repository.
  However, someone or an automated pipeline must explicitly initiate the API call.
</details>

#### 【 CI/CD 】

<details>
<summary><strong>↳ Follow-up: Suppose you want to configure the CI pipeline so that whenever a user commits code, a PR is automatically created and the CI pipeline is triggered without any manual intervention. How would you set this up in your CI configuration?</strong></summary>

**Answer:**
To automate this flow from a branch commit:

1. **Step 1: Webhook / Event Trigger on Push:**
   - Configure a webhook on the repository for `push` events on feature branches matching `feature/*`.
   - In GitHub Actions or Jenkins, the pipeline triggers immediately on push:
     ```yaml
     on:
       push:
         branches:
           - 'feature/**'
     ```

2. **Step 2: Automated PR Creation via CLI / API:**
   - Inside the pipeline job, authenticate using a GitHub App token or Personal Access Token (PAT) with `repo` permissions and execute `gh pr create`:
     ```yaml
     jobs:
       auto-pr:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v4
           - name: Create Pull Request
             env:
               GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
             run: |
               # Check if a PR already exists for this branch to prevent duplicates
               PR_EXISTS=$(gh pr list --head "${GITHUB_REF_NAME}" --base develop --json number -q '.[0].number')
               if [ -z "$PR_EXISTS" ]; then
                 gh pr create \
                   --base develop \
                   --head "${GITHUB_REF_NAME}" \
                   --title "Auto PR: ${GITHUB_REF_NAME} into develop" \
                   --body "Automated PR generated from commit ${GITHUB_SHA}."
               else
                 echo "PR already exists: #${PR_EXISTS}"
               fi
     ```

3. **Step 3: Triggering PR Validation CI:**
   - The created PR immediately emits a `pull_request` event, triggering the PR verification workflow (build, test, lint, scan).
</details>

<details>
<summary><strong>↳ Follow-up: Besides configuring the webhook trigger, what specific variable would you use in the CI configuration to ensure the CI pipeline automatically triggers when a PR is created?</strong></summary>

**Answer:**
In modern CI systems, specific event and branch context variables govern PR triggers:

1. **GitHub Actions:**
   - Trigger event keyword: `pull_request` (with activity types `[opened, synchronize, reopened]`).
   - Context variables used in conditions:
     - `${{ github.event_name == 'pull_request' }}`: Verifies the pipeline was invoked strictly by a PR event.
     - `${{ github.base_ref }}`: Identifies the target branch (e.g., `main` or `develop`).
     - `${{ github.head_ref }}`: Identifies the source branch submitting the PR.

2. **Jenkins (Generic Webhook / GitHub Branch Source Plugin):**
   - Environment variables injected by the GitHub plugin:
     - `CHANGE_ID`: Present only on PR builds (contains the PR number).
     - `CHANGE_TARGET`: The target branch (e.g., `main`).
     - In Multibranch Pipelines, we check:
       ```groovy
       when {
           expression { env.CHANGE_ID != null }
       }
       ```
     - For Generic Webhook Trigger, we capture the JSON payload path `$.action` (evaluating to `opened` or `reopened`).
</details>

<details>
<summary><strong>● What is a CI/CD pipeline, and why do we need pipelines in the software development lifecycle (SDLC)?</strong></summary>

**Answer:**
A **CI/CD pipeline** is an automated workflow that orchestrates the path of software from developer source code commit to production delivery.

1. **Core Pillars:**
   - **Continuous Integration (CI):** Automates code integration from multiple developers into a central repository multiple times a day. Each commit triggers automated builds, unit tests, code quality gates (SonarQube), and security vulnerability scans (SAST/SCA).
   - **Continuous Delivery / Deployment (CD):** Automates artifact packaging (Docker images, Helm charts, binaries) and stages deployments across environments (Dev -> QA -> Staging -> Prod) with zero-downtime strategies and automated rollbacks.

2. **Why We Need Pipelines in the SDLC:**
   - **Eliminates "Merge Hell":** Early bug detection prevents late-stage integration conflicts.
   - **Accelerates Time-to-Market:** Reduces cycle time from weeks to minutes.
   - **Enforces Quality & Compliance Guardrails:** No code reaches production without passing test coverage, security scans, and audit approvals.
   - **Consistency & Repeatability:** Eliminates manual human errors during deployments ("works on my machine" syndrome).
</details>

<details>
<summary><strong>↳ Follow-up: How would you design a complete continuous integration (CI) pipeline for a project, from code commit through to build and testing?</strong></summary>

**Answer:**
A robust production CI pipeline incorporates the following sequential stages:

```
[ Developer Commit ] 
       │
       ▼ (Webhook)
[ 1. Pre-flight & Linting ] ──────> (ShellCheck, MarkdownLint, Secret Detection: Gitleaks)
       │
       ▼
[ 2. Compile & Unit Test ] ───────> (mvn test / npm test / go test, Code Coverage generation)
       │
       ▼
[ 3. SAST & Quality Gate ] ───────> (SonarQube scan: fails if coverage < 80% or Critical Bugs > 0)
       │
       ▼
[ 4. Dependency Scanning ] ───────> (Snyk / OWASP Dependency-Check for library CVEs)
       │
       ▼
[ 5. Container Image Build ] ─────> (Multi-stage Dockerfile, tag with Git SHA)
       │
       ▼
[ 6. Container Vulnerability Scan ] (Trivy / AWS Inspector: fail on High/Critical CVEs)
       │
       ▼
[ 7. Artifact Publication ] ──────> (Push container image to Amazon ECR / JFrog Artifactory)
       │
       ▼
[ 8. Manifest Update / GitOps ] ──> (Commit new image tag to GitOps repo for Argo CD sync)
```

**Key Architectural Principles:**
- Fail fast: Place fast linting and unit testing before expensive container image builds.
- Ephemeral build environments: Run on dynamic Kubernetes pods or containers to prevent agent state contamination.
- Cache dependencies: Leverage caching for Maven repositories (`.m2`), npm modules, or Docker layer caching.
</details>

<details>
<summary><strong>↳ Follow-up: What build tools would you use to build the source code, for example in a Java application?</strong></summary>

**Answer:**
For Java applications, the standard enterprise build tools are:

1. **Apache Maven (Most Widely Used):**
   - Declarative XML configuration (`pom.xml`).
   - Standardized lifecycle (`validate`, `compile`, `test`, `package`, `verify`, `install`, `deploy`).
   - Automated dependency management via central/private artifact repositories (Nexus, JFrog Artifactory).
   - In pipelines: `mvn clean package -DskipTests=false`.

2. **Gradle (High-Performance Modern Standard):**
   - Groovy or Kotlin DSL (`build.gradle` / `build.gradle.kts`).
   - Significantly faster build times than Maven due to **Gradle Build Daemon**, incremental compilation, and local/remote build cache.
   - Preferred for large monorepos and Android/microservice applications.
   - In pipelines: `./gradlew clean build --build-cache`.

3. **Apache Ant with Ivy (Legacy):**
   - Procedural XML (`build.xml`); requires manual definition of all build steps and targets. Mostly phased out in modern cloud-native architectures.
</details>
</details>
</details>

<details open>
<summary><h2>🏢 Nisum</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 LINUX 】

<details>
<summary><strong>● Could you write a shell script to delete log files that are older than 30 days?</strong></summary>

**Answer:**
Here is a production-grade Bash script equipped with directory validation, logging, dry-run option, and safe deletion:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Configuration
LOG_DIR="${1:-/var/log/application}"
RETENTION_DAYS=30
AUDIT_LOG="/var/log/cleanup_audit.log"

# Validate directory existence
if [ ! -d "$LOG_DIR" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Target directory $LOG_DIR does not exist." | tee -a "$AUDIT_LOG"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting log cleanup in $LOG_DIR for files older than $RETENTION_DAYS days..." | tee -a "$AUDIT_LOG"

# Find and safely delete log files matching criteria
# Using -print0 and xargs -0 or -exec to safely handle spaces/special characters
find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.gz" \) -mtime +$RETENTION_DAYS -exec rm -f {} +

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cleanup completed successfully." | tee -a "$AUDIT_LOG"
```

**Key Shell Best Practices Included:**
- `set -euo pipefail`: Exits immediately on command errors, unset variables, or pipe failures.
- Directory validation to ensure the script doesn't execute against an empty variable (which could default to root `/`).
- `-type f`: Restricts deletion to regular files, preventing accidental directory deletion.
- `-mtime +30`: Targets files modified more than 30 * 24 hours ago.
- `-exec rm -f {} +`: Executes in batches for performance rather than spawning a separate process per file.
</details>

<details>
<summary><strong>↳ Follow-up: In the shell script command you wrote, are you missing anything, such as specifying the directory to search in with the find command?</strong></summary>

**Answer:**
In my initial script:
- The target search directory was explicitly provided as the first positional parameter (`LOG_DIR="${1:-/var/log/application}"`) and passed as the first argument to `find`:
  ```bash
  find "$LOG_DIR" -type f -name "*.log" -mtime +30 -exec rm -f {} +
  ```
- **Why Specifying the Path Explicitly is Critical:**
  If the directory path is omitted (e.g. running `find -name "*.log"`), GNU find defaults to the current working directory (`.`). In production, if this script is executed via a system cron job or Jenkins agent where the default working directory is `/` or `/root`, running `find .` without an explicit directory parameter could traverse root filesystems, cause high I/O saturation, and delete critical system files. Therefore, explicitly declaring and validating the directory path before passing it to `find` is mandatory.
</details>

<details>
<summary><strong>● What kind of Linux activities and tasks have you performed in your role?</strong></summary>

**Answer:**
As a Senior DevOps Engineer, my Linux activities span systems engineering, security hardening, networking, and CI/CD operations:

1. **System Administration & Performance Troubleshooting:**
   - Diagnosing CPU, memory, and I/O bottlenecks using `htop`, `vmstat`, `iostat`, `dstat`, and `sar`.
   - Managing system daemons and troubleshooting boot/runtime failures using `systemd` (`systemctl status`, `journalctl -u service -f --since "1 hour ago"`).
   - Disk space and inode exhaustion triage using `df -h`, `df -i`, `du -sh *`, and resolving unlinked open file locks with `lsof +L1`.

2. **User Management & Security Hardening:**
   - Managing RBAC, `sudoers` configurations, POSIX ACLs (`setfacl`/`getfacl`), and SSH key management.
   - Enforcing OS hardening standards (CIS Benchmarks), configuring SELinux/AppArmor policies, and auditing PAM configurations.

3. **Networking & Diagnostics:**
   - Troubleshooting connectivity issues, DNS resolution, and port binding using `ss -tulpn`, `ip route`, `dig`, `traceroute`, `curl -Iv`, and packet inspection via `tcpdump`.
   - Configuring host-level firewalls (`iptables`, `nftables`, `ufw`).

4. **Automation & Maintenance:**
   - Writing modular Bash automation scripts for log rotation, backup verification, and dynamic configuration generation.
   - Automating patch management via Ansible (`yum`/`dnf`/`apt` update automation) across fleet instances.
</details>

#### 【 GIT 】

<details>
<summary><strong>● Could you explain the Git branching strategy you have used in your project?</strong></summary>

**Answer:**
We implement a **Trunk-Based Development model with short-lived feature branches** (or a tailored **GitFlow** for strict quarterly enterprise releases):

```
main (Production: Tagged v1.0.0, v1.1.0)
  │
  └── release/v1.1.0 (Release candidate hardening & regression testing)
        │
develop (Integration branch for staging)
  │
  ├── feature/PAY-101-stripe-webhook (Short-lived, < 2 days)
  └── bugfix/PAY-104-tax-rounding (Short-lived bug fixes against develop)

hotfix/PAY-999-auth-bypass (Branched directly from main to patch Sev-1 prod bugs)
```

1. **`main` / `master` Branch:** Always production-ready, protected. Direct pushes are blocked; requires PR with 2 peer approvals, passing CI checks, and linear git history (Squash & Merge).
2. **`develop` Branch:** Shared integration branch continuously deployed to dev/QA environments.
3. **`feature/*` Branches:** Branched from `develop` for new user stories. Merged back via Pull Request after CI checks pass.
4. **`release/*` Branches:** Branched from `develop` when feature scope freezes; deployed to UAT/Staging for final regression and performance tests.
5. **`hotfix/*` Branches:** Branched directly from `main` to address critical production incidents, merged into both `main` and `develop`.
</details>

<details>
<summary><strong>↳ Follow-up: What is the difference between a hotfix branch and a bug fix branch in your Git branching strategy?</strong></summary>

**Answer:**
The differences center around urgency, lifecycle origin, and deployment target:

| Feature | Hotfix Branch (`hotfix/*`) | Bug Fix Branch (`bugfix/*`) |
| :--- | :--- | :--- |
| **Urgency / Severity** | **Sev-1 / Critical Production Outage** (Security vulnerability, payment gateway down, data corruption). | Normal/Medium priority defect found during development or QA testing. |
| **Branch Origin** | Branched directly from **`main` / `master`** (the current production commit/tag). | Branched from **`develop`** (or active `release/*` branch). |
| **Merge Target** | Merged immediately into **`main`** (tagged with patch version `v1.2.1`) AND back-merged into **`develop`**. | Merged into **`develop`** (or the respective `release/*` branch). |
| **Deployment Lifecycle** | Fast-tracked through an expedited emergency CI/CD pipeline directly to production. | Follows the standard scheduled sprint release cadence through QA, UAT, and Staging. |
</details>

<details>
<summary><strong>↳ Follow-up: From which branch do you create the bug fix branch?</strong></summary>

**Answer:**
A **bug fix branch (`bugfix/*`)** is created from the **`develop`** branch (in standard GitFlow) or from an active **`release/*`** branch if the bug was discovered during pre-production UAT/staging regression testing:

```bash
# Creating a bug fix for an issue identified in development
git checkout develop
git pull origin develop
git checkout -b bugfix/PROJ-412-fix-null-pointer
```
</details>

<details>
<summary><strong>↳ Follow-up: Again, from which branch specifically is the bug fix branch created?</strong></summary>

**Answer:**
Specifically, in our sprint cycle:
1. **During active sprint development:** It is branched specifically from **`develop`**.
2. **During pre-release testing / stabilization window:** It is branched specifically from the candidate **`release/*`** branch (e.g., `release/v2.4.0`), fixed there, and then merged back into both `release/v2.4.0` and `develop`.
</details>

<details>
<summary><strong>↳ Follow-up: From which branch is the hotfix branch created?</strong></summary>

**Answer:**
A **hotfix branch (`hotfix/*`)** is created strictly and exclusively from the **`main` (or `master`)** branch, which represents the exact commit currently live in the production environment:

```bash
git checkout main
git pull origin main
git checkout -b hotfix/PROJ-911-urgent-security-patch
```

This guarantees that the hotfix contains only the critical fix and does not accidentally bring unreleased, untested features currently sitting in `develop` into production. Once tested and deployed, it is merged into `main` and immediately back-merged into `develop`.
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● Could you write a Jenkins declarative pipeline that you have used in a project, including its stages?</strong></summary>

**Answer:**
Here is a production-grade Jenkins Declarative Pipeline utilizing dynamic Kubernetes pod agents, SonarQube quality gates, Docker build, and GitOps trigger:

```groovy
pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
metadata:
  labels:
    role: jenkins-agent
spec:
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
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
'''
        }
    }
    environment {
        AWS_DEFAULT_REGION = 'us-east-1'
        ECR_REGISTRY       = '123456789012.dkr.ecr.us-east-1.amazonaws.com'
        IMAGE_NAME         = 'order-service'
        IMAGE_TAG          = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
    }
    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }
    stages {
        stage('Checkout & Compile') {
            steps {
                container('maven') {
                    checkout scm
                    sh 'mvn clean compile'
                }
            }
        }
        stage('Unit Test & Code Coverage') {
            steps {
                container('maven') {
                    sh 'mvn test jacoco:report'
                }
            }
        }
        stage('SonarQube Static Analysis') {
            steps {
                container('maven') {
                    withSonarQubeEnv('SonarQube-Server') {
                        sh 'mvn sonar:sonar -Dsonar.projectKey=order-service'
                    }
                }
            }
        }
        stage('Quality Gate Check') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    script {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            error "Pipeline aborted: SonarQube Quality Gate failed (${qg.status})"
                        }
                    }
                }
            }
        }
        stage('Build & Push Docker Image') {
            steps {
                container('docker') {
                    withCredentials([usernamePassword(credentialsId: 'ecr-docker-auth', usernameVariable: 'ECR_USER', passwordVariable: 'ECR_PASS')]) {
                        sh '''
                            echo $ECR_PASS | docker login --username $ECR_USER --password-stdin $ECR_REGISTRY
                            docker build -t $ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG .
                            docker push $ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG
                        '''
                    }
                }
            }
        }
        stage('Trigger GitOps Deployment') {
            steps {
                container('maven') {
                    withCredentials([string(credentialsId: 'github-bot-token', variable: 'GH_TOKEN')]) {
                        sh '''
                            git clone https://${GH_TOKEN}@github.com/my-org/gitops-manifests.git
                            cd gitops-manifests/environments/staging
                            sed -i "s/tag:.*/tag: ${IMAGE_TAG}/" values.yaml
                            git config user.name "jenkins-bot"
                            git config user.email "jenkins-bot@company.com"
                            git commit -am "chore: promote order-service to ${IMAGE_TAG} [skip ci]"
                            git push origin main
                        '''
                    }
                }
            }
        }
    }
    post {
        always {
            cleanWs()
        }
        failure {
            slackSend channel: '#alerts-devops', message: "Job ${env.JOB_NAME} #${env.BUILD_NUMBER} FAILED."
        }
    }
}
```
</details>

<details>
<summary><strong>● What does your Jenkins master-agent architecture look like, and how many masters and agents have you configured?</strong></summary>

**Answer:**
In our production enterprise infrastructure:

1. **Architecture Overview:**
   - **Controller (Master):** Deployed as a stateful application on AWS EKS using an EBS volume for `$JENKINS_HOME` with automated daily Velero snapshots. The controller handles UI interaction, job definitions, build scheduling, and webhook processing; **it runs zero build workloads**.
   - **Agents (Dynamic Ephemeral Nodes):** Managed via the **Jenkins Kubernetes Plugin**. When a build is triggered, the controller makes an API call to the EKS cluster, dynamically launching a lightweight Pod running the `inbound-agent` container and custom runtime containers. Once the build completes, the pod is terminated and deleted.

2. **Scale & Sizing:**
   - **Controllers:** We operate **3 Controllers** organized by organizational boundaries (One for Core Platform/Infrastructure pipelines, one for Banking/Payment microservices, and one dedicated to Data Engineering/ETL pipelines).
   - **Agents:** Because agents are ephemeral Kubernetes pods, agent counts scale elastically:
     - Baseline: **0 to 5 active agent pods** during off-hours.
     - Peak: Dynamically scales up to **40–60 concurrent agent pods** during peak developer commit windows across dedicated Karpenter EC2 compute nodes.
</details>

<details>
<summary><strong>↳ Follow-up: Can Jenkins be configured with multiple masters/controllers?</strong></summary>

**Answer:**
Yes, Jenkins can be configured with multiple controllers, and in enterprise environments, horizontal partitioning is the standard design:

1. **Horizontal Partitioning / Multi-Controller Model (CloudBees CI / Jenkins Operations Center):**
   - Jenkins natively has a single-controller architecture per instance (it does not support an active-active clustered single controller due to disk locks on `$JENKINS_HOME`).
   - However, using **CloudBees CI (Enterprise Jenkins)** or managing multiple open-source controllers behind an ALB, an organization runs multiple controllers managed under a centralized **Operations Center**.
   - Jobs are distributed across controllers by business unit, line of business, or environment (Dev vs. Prod).

2. **Active-Passive High Availability (Failover):**
   - An active-passive setup using Kubernetes StatefulSets, AWS EFS/EBS Multi-Attach, or Pacemaker/Corosync. If the primary controller instance fails, health checks fail and the secondary standby instance spins up, mounting the shared `$JENKINS_HOME`.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Can you explain the Kubernetes architecture, including its main components?</strong></summary>

**Answer:**
Kubernetes operates on a distributed client-server architecture split into the **Control Plane** (managing cluster state) and **Worker Nodes** (running user workloads):

```
+-------------------------------------------------------------------------------+
|                             CONTROL PLANE                                     |
|  [ kube-apiserver ] <---> [ etcd (distributed key-value store) ]             |
|          ^                                                                    |
|          |---> [ kube-scheduler ] (selects optimal node for pending pods)     |
|          |---> [ kube-controller-manager ] (maintains desired state loops)    |
|          +---> [ cloud-controller-manager ] (interfaces with cloud provider)  |
+-------------------------------------------------------------------------------+
                                 |  (mTLS communication)
                                 v
+-------------------------------------------------------------------------------+
|                              WORKER NODES                                     |
|  [ kubelet ]             <--- Registers node & manages pod lifecycles        |
|  [ kube-proxy ]          <--- Manages iptables/IPVS service routing rules     |
|  [ Container Runtime ]   <--- Executes containers (containerd, CRI-O)        |
|  [ Pods ]                <--- Application workloads                           |
+-------------------------------------------------------------------------------+
```

1. **Control Plane:**
   - **kube-apiserver:** Central orchestrator; validates and configures data for pods, services, replication controllers. Exposes REST API.
   - **etcd:** Consistent, highly available key-value store holding the complete cluster state.
   - **kube-scheduler:** Assigns unscheduled pods to nodes based on resource constraints, affinity/anti-affinity, taints, and tolerations.
   - **kube-controller-manager:** Executes controllers: node lifecycle, endpoint slices, namespace management, service accounts.
   - **cloud-controller-manager:** Handles cloud-specific resources like load balancers, VPC routing tables, and EBS storage volumes.

2. **Worker Nodes:**
   - **kubelet:** Agent running on each node; ensures containers defined in PodSpecs are running and healthy.
   - **kube-proxy:** Network proxy reflecting Kubernetes Services on each node, directing traffic to backend pod IPs.
   - **Container Runtime:** Low-level engine (containerd) pulling images and running container processes.
</details>

<details>
<summary><strong>↳ Follow-up: Which version of Kubernetes have you been using, and for how many years have you worked with Kubernetes?</strong></summary>

**Answer:**
I have worked extensively with Kubernetes for **over 5 years** across production environments, starting from Kubernetes **v1.16/1.18** through recent versions including **v1.28, v1.29, and v1.30** on Amazon EKS:

- **Early Experience (v1.16 - v1.21):** Managed clusters during the major deprecations of `extensions/v1beta1`, `apps/v1beta1`, and the Docker shim deprecation transition to `containerd`.
- **Recent Production Experience (v1.27 - v1.30):** Managing enterprise EKS clusters with Karpenter, Pod Security Standards (PSS), Gateway API, and EKS Access Entries.
</details>

<details>
<summary><strong>↳ Follow-up: What is the current Kubernetes version you are using in your project?</strong></summary>

**Answer:**
In our current production environment, we are running **Kubernetes version 1.29** on Amazon EKS, and we are currently validating our lower staging environments on **version 1.30** in preparation for the upcoming production upgrade window to stay well ahead of AWS EKS standard support end dates.
</details>

<details>
<summary><strong>↳ Follow-up: What Kubernetes version were you using at the start of your career with Kubernetes?</strong></summary>

**Answer:**
At the start of my Kubernetes journey around 2019–2020, I started with **Kubernetes v1.16 and v1.18**. That period involved learning core primitives, navigating the major API removals of `extensions/v1beta1` for Deployments and Ingresses, and using `kubeadm` and `kOps` prior to migrating workloads onto managed Amazon EKS.
</details>

<details>
<summary><strong>● Since you have been working on EKS, have you ever performed a cluster upgrade?</strong></summary>

**Answer:**
Yes, I have performed multiple production EKS cluster upgrades (e.g., upgrading from 1.26 to 1.27, 1.27 to 1.28, and 1.28 to 1.29). 

EKS requires upgrading **one minor version at a time** (sequential upgrades: e.g., 1.28 -> 1.29). In production, upgrades are treated as controlled change initiatives: first executed and validated in sandbox and development clusters, followed by staging/UAT, and finally scheduled in production during off-peak maintenance windows.
</details>

<details>
<summary><strong>↳ Follow-up: What prerequisites do you follow before upgrading an EKS cluster?</strong></summary>

**Answer:**
Our production EKS upgrade checklist involves the following prerequisites:

1. **API Deprecation Audit:**
   - Run **Pluto** (by Fairwinds) or **kube-no-trouble (`kubent`)** against the cluster to identify any deployed manifests or Helm releases using deprecated or removed APIs in the target version.
2. **Cluster Add-ons Compatibility Check:**
   - Verify compatibility matrix for Amazon EKS managed add-ons:
     - **VPC CNI** (`aws-node`)
     - **CoreDNS**
     - **Kube-proxy**
     - **AWS EBS CSI Driver**
   - Check third-party controllers: Ingress Controllers (AWS Load Balancer Controller, NGINX), Argo CD, Prometheus, Cert-Manager, and Karpenter.
3. **Pod Disruption Budgets (PDBs) Verification:**
   - Inspect PDBs (`kubectl get pdb -A`) to ensure `minAvailable` or `maxUnavailable` settings don't block node draining during worker node updates.
4. **Subnet IP Availability:**
   - Verify that worker node subnets have sufficient available IP addresses for spinning up new node groups concurrently during rolling replacements.
5. **Backups:**
   - Take full cluster backup using **Velero** and take EBS snapshots of stateful database volumes.
</details>

<details>
<summary><strong>↳ Follow-up: How many days does it typically take to upgrade the production environment after validating in lower environments?</strong></summary>

**Answer:**
Typically, the overall lifecycle across all environments spans **2 to 3 weeks**, with the actual production upgrade executed within a **single scheduled 4-hour maintenance window**:

- **Week 1 (Dev & QA):** Upgrade development and QA clusters; validate pipeline deployments, Helm charts, and add-ons compatibility (2–3 days).
- **Week 2 (Staging / Pre-Prod):** Upgrade staging cluster; run full regression test suites, smoke tests, and synthetic load testing for 5–7 days to observe stability and memory leak behavior.
- **Week 3 (Production Window):** Following Change Advisory Board (CAB) approval, the production upgrade is performed during a weekend or off-peak night window, completing in approximately 2 to 3 hours with active post-upgrade validation.
</details>

<details>
<summary><strong>↳ Follow-up: Do you cordon the nodes during the EKS cluster upgrade process?</strong></summary>

**Answer:**
Yes, absolutely. During worker node upgrades, nodes are **cordoned** and **drained**:

1. **Cordoning (`kubectl cordon <node-name>`):** Marks the node as unschedulable, ensuring that no newly created pods or scaling replicas land on the node scheduled for termination.
2. **Draining (`kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data`):** Gracefully evicts existing pods from the node, honoring termination grace periods and Pod Disruption Budgets (PDBs), allowing pods to be rescheduled onto newly provisioned nodes running the upgraded Kubernetes version AMI.
3. **Automated Drain via Managed Node Groups / Karpenter:** When upgrading AWS Managed Node Groups via Terraform or AWS Console, AWS automatically executes cordon and drain operations node-by-node during rolling updates.
</details>

<details>
<summary><strong>↳ Follow-up: How much time does the overall cluster upgrade process take?</strong></summary>

**Answer:**
For a single EKS cluster, the end-to-end upgrade execution takes approximately **1.5 to 2.5 hours**:
- **Control plane upgrade:** ~20 to 30 minutes.
- **Cluster add-ons upgrade:** ~15 to 20 minutes.
- **Worker node group replacement (rolling update/drain):** ~45 to 60 minutes (dependent on total node count, pod termination grace periods, and PDB constraints).
- **Smoke testing and health verification:** ~30 minutes.
</details>

<details>
<summary><strong>↳ Follow-up: How long does it take to upgrade the control plane, node groups, and add-ons specifically during an EKS upgrade?</strong></summary>

**Answer:**
Breaking down each component:

1. **Control Plane Upgrade (AWS Managed):**
   - Takes **20 to 30 minutes**. AWS upgrades the API server and etcd instances in an automated rolling fashion across 3 AZs. During this time, the cluster control plane API endpoint remains accessible.
2. **Managed Add-ons Upgrade:**
   - Takes **10 to 15 minutes** in total. Upgrades are applied sequentially: VPC CNI -> Kube-proxy -> CoreDNS -> EBS CSI Driver.
3. **Worker Node Groups Upgrade:**
   - Takes **30 to 60 minutes** (for a standard 10–20 node cluster). AWS Managed Node Groups provision new EC2 instances with the new AMI, join them to the cluster, cordon and drain old nodes one by one (or according to `maxUnavailable` percentage), and terminate them cleanly.
</details>

<details>
<summary><strong>● What deployment strategy do you use for deploying applications in Kubernetes?</strong></summary>

**Answer:**
We employ two primary deployment strategies based on service criticality and traffic profile:

1. **Rolling Update (Default for Standard Services):**
   - Native Kubernetes Deployment strategy configured with `maxSurge: 25%` and `maxUnavailable: 0`.
   - Gradually replaces old pods with new pods. A new pod must pass its `readinessProbe` before old pods are terminated, ensuring zero downtime.

2. **Canary Deployments via Argo Rollouts (For Critical Customer APIs):**
   - For payment and checkout microservices, we utilize **Argo Rollouts** integrated with our Service Mesh / ALB:
     - Deploys new revision and routes **10%** of live traffic to the canary version.
     - Performs automated metric analysis via Prometheus (evaluating HTTP 5xx error rates < 0.05% and p99 latency < 200ms).
     - If metrics remain healthy over a 15-minute analysis run, traffic automatically steps up to 50% and then 100%.
     - If metrics breach threshold, Argo Rollouts executes an instant automatic abort and rollback to the stable version.
</details>

#### 【 IAC 】

<details>
<summary><strong>● Have you been using Terraform in your project?</strong></summary>

**Answer:**
Yes, Terraform is our primary Infrastructure as Code (IaC) standard for provisioning and managing multi-region cloud infrastructure across AWS accounts.

We maintain a modular architecture adhering to DRY (Don't Repeat Yourself) principles:
- **Core Modules:** Standardized, version-tagged modules for VPCs, EKS clusters, IAM Roles for Service Accounts (IRSA), RDS Aurora databases, and KMS keys.
- **Environment Stacks:** Dedicated stacks (`dev`, `stage`, `prod`) consuming version-pinned modules with remote S3 backend state storage and DynamoDB distributed state locking.
- **CI/CD Integration:** Automated IaC pipelines in GitHub Actions executing `terraform fmt -check`, `tflint`, `checkov` security scans, `terraform plan` output posted as PR comments, and strict manual approval gates before `terraform apply`.
</details>

<details>
<summary><strong>↳ Follow-up: What kind of Terraform are you using—Terragrunt or plain Terraform?</strong></summary>

**Answer:**
We use **plain Terraform with a modular repository layout and standard backend configurations**, though I have experience with both:

- **Why Plain Terraform in our Setup:**
  - Modern Terraform (versions 1.5+) has built-in features that addressed many early pain points that previously required Terragrunt (e.g., `import` blocks, `check` blocks, module testing frameworks, and advanced meta-arguments).
  - Keeps the toolchain standard and eliminates additional binary dependencies in CI/CD runners.
- **When Terragrunt is Beneficial:**
  - **Zero Backend Duplication:** Terragrunt provides `terragrunt.hcl` parent-child inheritance where backend configurations and provider blocks are defined once globally.
  - **Multi-Module Orchestration:** Commands like `terragrunt run-all plan` / `apply` automatically calculate the Directed Acyclic Graph (DAG) dependency order between disparate modules across accounts.
</details>

<details>
<summary><strong>● What is the purpose of the 'terraform fmt' command?</strong></summary>

**Answer:**
The `terraform fmt` command rewrites Terraform configuration files (`.tf` and `.tfvars`) into a canonical format and style defined by HashiCorp standards:

- **Formatting Adjustments:** Standardizes indentation (2 spaces), aligns attribute equals signs (`=`) in blocks, removes unnecessary whitespace, and organizes arguments consistently.
- **CI/CD Enforcement:** In automated pipelines, we run:
  ```bash
  terraform fmt -check -diff -recursive
  ```
  This checks configurations recursively across all subdirectories and fails the CI pipeline with a diff if any unformatted code is committed, ensuring consistent codebase readability.
</details>

<details>
<summary><strong>↳ Follow-up: What does the 'terraform validate' command do?</strong></summary>

**Answer:**
The `terraform validate` command verifies the **syntactical and structural correctness** of configuration files within a directory without accessing remote APIs or state:

1. **What It Checks:**
   - HCL syntax errors (missing brackets, malformed strings).
   - Attribute validity against provider schemas (e.g., verifying that `aws_instance` has valid arguments).
   - Correct variable types and required arguments.
   - Resource and variable name validity.
2. **Prerequisites:**
   - Must be executed after `terraform init`, because `validate` needs the downloaded provider schemas in `.terraform/providers` to check argument validity against provider plugins.
</details>

<details>
<summary><strong>↳ Follow-up: What happens when you run the 'terraform init' command?</strong></summary>

**Answer:**
The `terraform init` command initializes the working directory containing Terraform configuration files. Specifically, it performs five key operations:

```
[ terraform init ]
       │
       ├──> 1. Initializes Backend (Configures S3, connects to DynamoDB state lock table)
       ├──> 2. Downloads & Caches Provider Plugins (aws, kubernetes, tls -> .terraform/providers)
       ├──> 3. Installs Child Modules (Clones external Git or Terraform Registry modules -> .terraform/modules)
       ├──> 4. Generates / Verifies Dependency Lock File (.terraform.lock.hcl: records exact hashes)
       └──> 5. Configures Workspaces (Sets up default or active workspace metadata)
```

If provider versions or module sources change, running `terraform init -upgrade` updates providers and lockfiles to the newest allowed versions.
</details>

<details>
<summary><strong>↳ Follow-up: How do you manage the Terraform state file in your project?</strong></summary>

**Answer:**
We manage the Terraform state using an enterprise-grade **Remote S3 Backend with State Locking and Encryption**:

```hcl
terraform {
  required_version = ">= 1.5.0"
  
  backend "s3" {
    bucket         = "company-tfstate-prod-us-east-1"
    key            = "vpc/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "company-tflocks-prod"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/xxxx-xxxx"
  }
}
```

**Security & Operational Safeguards:**
1. **Concurrency Control:** Amazon DynamoDB provides distributed locking (`LockID`) to prevent simultaneous applies from corrupting state.
2. **Encryption:** S3 bucket enforces server-side encryption via AWS KMS Customer Managed Keys (CMK) and enforces `aws:SecureTransport` (HTTPS only).
3. **Immutability & Recovery:** S3 Object Versioning and MFA Delete are enabled to protect against accidental state deletion or corruption.
4. **State Segregation:** State files are isolated by environment and layer (e.g., `networking/vpc.tfstate`, `compute/eks.tfstate`, `database/aurora.tfstate`) to limit the blast radius of any single plan or apply operation.
</details>

<details>
<summary><strong>● If there is a configuration drift between Terraform state and actual AWS infrastructure, how would you handle it?</strong></summary>

**Answer:**
Configuration drift occurs when cloud resources are modified outside of Terraform (e.g., via AWS Management Console, CLI, or automated cloud tools), causing the real-world state to diverge from the Terraform configuration and state file.

**Handling & Remediation Process:**
1. **Detect Drift:**
   - Execute `terraform plan -refresh-only` or standard `terraform plan`.
   - Terraform queries cloud APIs via provider reads, compares live infrastructure with the stored state file, and generates a plan showing the detected differences without proposing changes to the code.
2. **Evaluate the Drift:**
   - **Scenario A (Unauthorized / Accidental Change):** Someone manually opened port 22 in a security group via console. 
     - *Action:* Re-run `terraform apply`. Terraform automatically overwrites the manual modification and restores the resource to the desired state declared in the `.tf` code.
   - **Scenario B (Intentional / Approved Out-of-Band Change):** A manual emergency change made during a Sev-1 incident that must be preserved.
     - *Action:* Update the `.tf` code to reflect the new desired attributes, run `terraform plan` to ensure a clean zero-diff plan, and commit the updated code to Git.
</details>

<details>
<summary><strong>↳ Follow-up: After identifying drift using 'terraform plan', how would you bring the resource back to the desired managed state?</strong></summary>

**Answer:**
Depending on whether the desired state is defined by the **existing code** or the **new live infrastructure**:

1. **To Overwrite Live Infrastructure and Restore to Code Definition:**
   - Simply execute:
     ```bash
     terraform apply
     ```
   - Terraform detects that the live resource has drifted from the configuration, updates the cloud provider via API to undo the out-of-band modifications, and updates the state file to reflect the reconciled desired state.

2. **To Accept Live Infrastructure Changes into Terraform:**
   - Update your `.tf` configuration file to match the modified live attributes.
   - Run `terraform plan -refresh-only` to refresh the state file.
   - Run `terraform apply -refresh-only` to commit the observed real-world state into the state file with zero changes proposed to the infrastructure.
</details>

<details>
<summary><strong>↳ Follow-up: What is 'terraform taint' and how is it used?</strong></summary>

**Answer:**
`terraform taint` informs Terraform that a specific managed resource has become degraded, damaged, or corrupted, and must be **destroyed and recreated** on the next execution of `terraform apply`.

1. **Legacy CLI Usage:**
   ```bash
   terraform taint aws_instance.web_app
   # Terraform marks the resource in state as "tainted"
   terraform apply
   # Terraform destroys aws_instance.web_app and provisions a fresh replacement
   ```

2. **Modern Replacement (`-replace` flag in Terraform 0.15.2+ / 1.0+):**
   - HashiCorp officially deprecated `terraform taint` in favor of the safer, non-mutating `-replace` flag:
     ```bash
     terraform plan -replace="aws_instance.web_app"
     terraform apply -replace="aws_instance.web_app"
     ```
   - Unlike `terraform taint` (which immediately mutates the state file before you run apply), `-replace` creates a speculative plan showing the recreation without modifying state beforehand.
</details>

<details>
<summary><strong>↳ Follow-up: What is 'terraform import' and how is it used?</strong></summary>

**Answer:**
`terraform import` is used to bring pre-existing infrastructure that was created manually or via other tools **under Terraform state management**.

1. **Traditional CLI Import:**
   - Step 1: Write a minimal resource block in `.tf`:
     ```hcl
     resource "aws_s3_bucket" "legacy_bucket" {
       bucket = "my-pre-existing-company-bucket"
     }
     ```
   - Step 2: Execute CLI import command:
     ```bash
     terraform import aws_s3_bucket.legacy_bucket my-pre-existing-company-bucket
     ```
   - Step 3: Run `terraform plan` and align attributes in `.tf` until it reports `No changes`.

2. **Modern Declarative `import` Block (Terraform 1.5+):**
   - Allows code-driven, auditable imports through Git without manual CLI execution:
     ```hcl
     import {
       to = aws_s3_bucket.legacy_bucket
       id = "my-pre-existing-company-bucket"
     }
     ```
   - Running `terraform plan -generate-config-out=generated_bucket.tf` automatically generates the HCL resource configuration.
</details>

<details>
<summary><strong>↳ Follow-up: Wouldn't you use 'terraform import' to resolve drift instead of taint?</strong></summary>

**Answer:**
**No, absolutely not.** `terraform import` and `terraform taint` serve fundamentally different purposes in Terraform:

1. **Why `terraform import` Cannot Resolve Drift:**
   - `terraform import` is strictly designed for **unmanaged resources** that do not yet exist in the Terraform state file.
   - When a resource has drifted, it **is already registered in the state file**. Running `terraform import` on an already-managed resource will throw an error:
     `Error: Resource already managed by Terraform`.
   - To resolve drift, you simply run `terraform apply` (to revert live changes back to code) or update the `.tf` code (to accept live changes).

2. **Role of `taint` / `-replace`:**
   - Taint is used when a managed resource is physically or logically broken (e.g., an EC2 instance had its root filesystem corrupted or an initialization user-data script failed halfway), and you want to force Terraform to destroy and recreate that resource from scratch.
</details>

<details>
<summary><strong>↳ Follow-up: Why would you use 'terraform taint' to force recreation of a resource instead of other approaches?</strong></summary>

**Answer:**
You use `terraform taint` (or modern `terraform apply -replace=...`) specifically when:

1. **OS / Software Corruption Without Infrastructure Attribute Change:**
   - An EC2 instance, database replica, or container host has suffered internal OS-level corruption, bad kernel updates, or corrupted local databases, but its declared Terraform attributes (AMI, instance type, VPC) have not changed.
   - A normal `terraform apply` reports `No changes` because the cloud resource metadata matches the `.tf` code. Taint forces recreation.
2. **Re-executing Bootstrapping / User Data:**
   - If an EC2 `user_data` bash script failed partway through on initial boot, the cloud provider considers the VM running and healthy. Tainting the instance ensures it is cleanly torn down and re-provisioned with fresh user data.
3. **Controlled recreation in dependency chains:**
   - Tainting a resource ensures that downstream dependent resources (e.g. security group attachments, route table associations) are evaluated and rewired cleanly through Terraform's dependency graph.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● What cost optimization strategies have you implemented in your AWS projects?</strong></summary>

**Answer:**
We implemented a multi-pillar FinOps cost optimization framework on AWS across compute, storage, databases, and networking:

1. **Compute Rightsizing & Modernization:**
   - Migrated x86 (`m5`, `c5`, `r5`) EC2 and EKS node workloads to **AWS Graviton3/Graviton4 (`m7g`, `c7g`, `r7g`)**, delivering up to **20–25% lower cost and 40% better price-performance**.
   - Implemented **Karpenter** on EKS with diverse Spot instance pools for stateless microservices and dev environments, cutting non-production compute costs by ~65%.
2. **Commitment Discounts:**
   - Analyzed AWS Cost Explorer and Compute Optimizer recommendations to purchase **Savings Plans** and **Reserved Instances (RIs)** for predictable baseline workloads (yielding 30–50% savings).
3. **Storage Lifecycle Policies:**
   - Configured **Amazon S3 Lifecycle Rules**: transition objects to S3 Standard-Infrequent Access after 30 days, Glacier Flexible Retrieval after 90 days, and expiration after retention policies. Enabled S3 Intelligent-Tiering for unpredictable access patterns.
   - Upgraded EBS volumes from `gp2` to **`gp3`**, resulting in an immediate 20% cost savings per GB with independent IOPS and throughput provisioning.
4. **Database & Idle Resource Governance:**
   - Deployed AWS Instance Scheduler / EventBridge Lambda to automatically stop development RDS and EC2 instances during off-hours (weekends and nights), reducing dev infrastructure runtime by ~60%.
   - Cleaned up unattached EBS volumes, stale EBS snapshots, unassociated Elastic IPs, and idle Classic Load Balancers using AWS Trusted Advisor and automated AWS Config rules.
</details>

<details>
<summary><strong>↳ Follow-up: How did you determine that the cost optimization resulted in a 10% reduction?</strong></summary>

**Answer:**
We measured and validated the 10% cost reduction using empirical FinOps data analysis across multiple AWS billing and reporting tools:

1. **AWS Cost Explorer Baseline Comparison:**
   - Established a 90-day normalized baseline of daily and monthly unblended costs prior to optimization.
   - Compared the **Monthly Run Rate (MRR)** and average cost per day before and after optimizations, filtering by service and Cost Allocation Tags (`Environment: prod`, `Team: CoreBanking`).
2. **AWS Cost and Usage Report (CUR) with Amazon Athena & QuickSight:**
   - Ran SQL queries against hourly CUR data stored in S3 to isolate unit economics:
     - Calculated **Cost per 10,000 API Transactions** and **Cost per Active Pod/User**.
     - This ensured that the 10% reduction was a true efficiency gain and not simply an artifact of decreased user traffic.
3. **AWS Budgets & Anomaly Detection:**
   - Validated sustained month-over-month invoice reductions in AWS Billing & Cost Management console against configured budget thresholds.
</details>

<details>
<summary><strong>↳ Follow-up: What type/kind of EC2 instances do you use for your workloads?</strong></summary>

**Answer:**
We select EC2 instance families tailored specifically to workload characteristics:

1. **General Purpose Workloads (EKS Worker Nodes & Web APIs):**
   - **`m7g.large` / `m7g.xlarge`** (AWS Graviton3 ARM-based): Best price-performance balance for microservice APIs, message consumers, and web frontends.
   - **`m5.xlarge` / `m6i.xlarge`** (Intel-based): Used where third-party proprietary binaries require x86_64 architecture.
2. **Compute-Intensive Workloads (CI/CD Runners, Batch Processing):**
   - **`c7g.2xlarge` / `c6i.2xlarge`**: High CPU-to-memory ratio for compiling code, running SonarQube static analysis, and cryptographic operations.
3. **Memory-Intensive Workloads (Databases & Caches):**
   - **`r7g.2xlarge` / `r6i.2xlarge`**: High memory-to-vCPU ratio for Amazon ElastiCache (Redis), Apache Kafka brokers, and Elasticsearch/OpenSearch indexing.
4. **Purchasing Models:**
   - **On-Demand / Savings Plans:** For stateful workloads and production database clusters.
   - **Spot Instances:** Managed by Karpenter for ephemeral CI/CD agents and non-critical batch workers.
</details>
</details>
</details>

<details open>
<summary><h2>🏢 KPIT</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 05-09-2026 05:21 PM*

#### 【 CI/CD 】

<details>
<summary><strong>● If you were designing a CI/CD pipeline for REST-based microservices, what stages would you include?</strong></summary>

**Answer:**
A production-grade CI/CD pipeline for REST-based microservices balances high velocity with strict quality and security guardrails:

```
[ Git Push / PR ]
       │
       ▼
[ 1. Pre-flight & Linting ] ─────────> (Cargo clippy / fmt, ShellCheck, Gitleaks for secret detection)
       │
       ▼
[ 2. Build & Test ] ─────────────────> (cargo test / pytest / mvn test, code coverage generation)
       │
       ▼
[ 3. SAST & Quality Gate ] ──────────> (SonarQube analysis, fails if coverage < 80% or Blocker CVEs found)
       │
       ▼
[ 4. Dependency Vulnerability Scan ]  (cargo audit / Snyk / OWASP Dependency Check)
       │
       ▼
[ 5. Containerization & Layer Cache ] (Multi-stage Docker build using Buildx)
       │
       ▼
[ 6. Container Image Security Scan ] ─> (Trivy / AWS Inspector: fail build on High/Critical vulnerabilities)
       │
       ▼
[ 7. Artifact Publishing ] ──────────> (Push signed image with Git SHA to Amazon ECR)
       │
       ▼
[ 8. GitOps PR / Manifest Update ] ──> (Update Helm values.yaml / Kustomize image tag via CI bot)
       │
       ▼
[ 9. Automated Deployment & Verification ] (Argo CD sync -> Canary/Blue-Green rollout with automated rollback)
```
</details>

#### 【 DOCKER 】

<details>
<summary><strong>↳ Follow-up: What would you use as a Docker image repository for this platform?</strong></summary>

**Answer:**
For an AWS cloud-native platform, **Amazon Elastic Container Registry (Amazon ECR)** is the production standard:

1. **Native IAM & IRSA Authentication:** Integrates seamlessly with AWS IAM Identity Center and Kubernetes IRSA, eliminating static credentials and secret rotation overhead.
2. **Built-in Vulnerability Scanning:** Offers enhanced automated scanning powered by **AWS Inspector**, continuously scanning stored images against the latest CVE databases upon push and on an ongoing basis.
3. **Immutability & Lifecycle Policies:** Supports **Image Tag Immutability** to prevent overwriting existing release tags (such as `v1.2.0`), and **Lifecycle Policies** to expire untagged or old development images after 14 days, minimizing storage costs.
4. **Cross-Region Replication:** Enables automated geo-replication across AWS regions with low-latency image pulls during multi-region disaster recovery failovers.
</details>

<details>
<summary><strong>● How would you optimize Docker images for a Rust application?</strong></summary>

**Answer:**
Rust produces statically linked native machine binaries. To optimize for minimal footprint, rapid build caching, and hardened security:

1. **Multi-Stage Build with `cargo-chef` for Dependency Caching:**
   - Because Rust dependencies recompile slowly if any source file changes, we use **`cargo-chef`** to pre-build and cache dependencies in Docker layer cache:
     ```dockerfile
     # Stage 1: Cargo Chef Planner
     FROM lukemathwalker/cargo-chef:latest-rust-1.78-alpine AS chef
     WORKDIR /app

     FROM chef AS planner
     COPY . .
     RUN cargo chef prepare --recipe-path recipe.json

     # Stage 2: Cache & Build Dependencies
     FROM chef AS builder
     COPY --from=planner /app/recipe.json recipe.json
     # Build dependencies - this layer is cached unless Cargo.lock changes!
     RUN cargo chef cook --release --target x86_64-unknown-linux-musl --recipe-path recipe.json

     # Stage 3: Build Application Binary
     COPY . .
     RUN cargo build --release --target x86_64-unknown-linux-musl --bin microservice

     # Stage 4: Minimal Distroless / Scratch Runtime (< 15MB)
     FROM gcr.io/distroless/static-debian12:nonroot
     WORKDIR /app
     COPY --from=builder /app/target/x86_64-unknown-linux-musl/release/microservice /app/server
     USER nonroot:nonroot
     EXPOSE 8080
     ENTRYPOINT ["/app/server"]
     ```

2. **Compile with MUSL Target (`x86_64-unknown-linux-musl`):**
   - Produces a fully self-contained static binary with zero dynamic C runtime dependencies, allowing execution on `scratch` or `distroless/static`.
3. **Compiler Flag Optimizations (`Cargo.toml`):**
   - Enable Link Time Optimization and strip symbols:
     ```toml
     [profile.release]
     opt-level = 3
     lto = true
     codegen-units = 1
     panic = "abort"
     strip = true
     ```
   - Drops final image size from 1.2GB down to **under 15MB** with zero CVE attack surface.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● What Kubernetes probes are you aware of, and how do they work?</strong></summary>

**Answer:**
Kubernetes provides three core health probes configured on container specs:

1. **Startup Probe:**
   - **Purpose:** Determines whether the application process inside the container has fully initialized.
   - **Mechanism:** Disables liveness and readiness checks until it succeeds. Ideal for legacy JVM or slow-starting frameworks. If it fails past `failureThreshold`, the kubelet kills and restarts the container.
2. **Liveness Probe:**
   - **Purpose:** Determines if the container is healthy and actively running.
   - **Mechanism:** If the liveness probe fails (e.g., deadlock, infinite loop, hung thread), the kubelet terminates the container and initiates a restart according to the pod's `restartPolicy`.
3. **Readiness Probe:**
   - **Purpose:** Determines if the pod is ready to accept incoming network traffic.
   - **Mechanism:** If it fails, the pod's IP address is immediately removed from the `Endpoints` / `EndpointSlices` of all matching Kubernetes Services. Traffic is rerouted to remaining healthy pods without restarting the container.

**Probe Mechanisms:** HTTP GET request (`httpGet`), TCP socket check (`tcpSocket`), or command execution (`exec`).
</details>

<details>
<summary><strong>● How does Kubernetes Horizontal Pod Autoscaler (HPA) work?</strong></summary>

**Answer:**
The **Horizontal Pod Autoscaler (HPA)** automatically adjusts the number of replica pods in a Deployment, ReplicaSet, or StatefulSet based on observed resource utilization or custom metrics:

1. **Control Loop Operation:**
   - Runs as a control loop inside `kube-controller-manager` executing periodically (default every 15 seconds).
   - Queries metrics via the **Metrics API** (`metrics.k8s.io` via Metrics Server) or custom/external metrics APIs (`custom.metrics.k8s.io` via Prometheus Adapter).

2. **Mathematical Scaling Algorithm:**
   $$\text{Desired Replicas} = \left\lceil \text{Current Replicas} \times \left( \frac{\text{Current Metric Value}}{\text{Target Metric Value}} \right) \right\rceil$$

3. **Stabilization Window & Cooldowns:**
   - Configurable `behavior` block prevents thrashing ("flapping"):
     ```yaml
     behavior:
       scaleDown:
         stabilizationWindowSeconds: 300
         policies:
         - type: Percent
           value: 10
           periodSeconds: 60
     ```
   - Smoothly scales down over a 5-minute stabilization window while scaling up rapidly during traffic spikes.
</details>

<details>
<summary><strong>● How would you implement a blue-green deployment strategy?</strong></summary>

**Answer:**
Blue-Green deployment provisions two identical production environments: **Blue** (currently running live production traffic) and **Green** (idle environment where the new version is deployed and validated).

```
                 [ Ingress / ALB ]
                         │
        (Switch selector: version=green)
                         │
           +-------------+-------------+
           │                           │
           ▼                           ▼
[ Service: Blue (v1.0) ]    [ Service: Green (v1.1) ]
(100% Live Traffic)         (Pre-cutover Smoke Testing)
```

**Implementation Steps via Kubernetes Service Selector:**
1. Maintain two independent Deployments: `my-app-blue` (image: `v1.0`) and `my-app-green` (image: `v1.1`).
2. Deploy new version `v1.1` to the Green Deployment. Green is connected to a dedicated internal/test Service (`my-app-test-svc`).
3. Run automated synthetic smoke tests against Green via test endpoint.
4. **Traffic Cutover:** Update the production Kubernetes Service label selector from `version: blue` to `version: green`:
   ```bash
   kubectl patch service my-app-prod -p '{"spec":{"selector":{"version":"green"}}}'
   ```
5. Traffic instantly switches to Green with zero downtime. If any issue arises, immediately patch the selector back to `version: blue`. Keep Blue idle for 1 hour before decommissioning.
</details>

<details>
<summary><strong>● Do you have knowledge about canary deployments, and can you explain how they work?</strong></summary>

**Answer:**
A **Canary Deployment** progressively rolls out changes to a small subset of real users before releasing to the entire infrastructure:

1. **How It Works:**
   - A small percentage of production traffic (e.g., 5% or 10%) is routed to the new release ("Canary"), while 90–95% continues hitting the stable version.
   - Key operational SLIs (HTTP 5xx rate, p99 response latency, error logs) are monitored in real time against the baseline.
   - If error rates remain healthy, traffic shifts incrementally (10% -> 25% -> 50% -> 100%).
   - If anomalies or SLA breaches occur, traffic is instantly rolled back to 0% with negligible blast radius.

2. **Enterprise Implementation (Argo Rollouts + ALB / Istio):**
   - We utilize **Argo Rollouts** with an `AnalysisTemplate` querying Prometheus metrics:
     ```yaml
     apiVersion: argoproj.io/v1alpha1
     kind: Rollout
     metadata:
       name: payment-service
     spec:
       strategy:
         canary:
           steps:
           - setWeight: 10
           - pause: { duration: 15m }
           - analysis:
               templates:
               - templateName: success-rate-check
           - setWeight: 50
           - pause: { duration: 10m }
     ```
</details>

<details>
<summary><strong>↳ Follow-up: How do you check the health of a pod in a Kubernetes (AKS) cluster?</strong></summary>

**Answer:**
In an AKS (Azure Kubernetes Service) or any standard Kubernetes cluster:

1. **CLI Commands:**
   - Check Pod status and restart count:
     ```bash
     kubectl get pods -n <namespace> -o wide
     ```
   - Deep inspection of events, probes, and conditions:
     ```bash
     kubectl describe pod <pod-name> -n <namespace>
     ```
     Inspect `Conditions: [Initialized, Ready, ContainersReady, PodScheduled]` and check the `Events` section at the bottom.
   - Stream real-time container stdout/stderr logs:
     ```bash
     kubectl logs <pod-name> -c <container-name> -n <namespace> --tail=100 -f
     ```

2. **Azure Cloud Native Monitoring (Azure Monitor / Container Insights):**
   - Navigate to Azure Portal -> AKS Cluster -> **Container Insights**.
   - Review Pod CPU/Memory utilization graphs, live container log streams via Kusto Query Language (KQL), and alert rules evaluating failed probe metrics.
</details>

#### 【 IAC 】

<details>
<summary><strong>● How do you manage Terraform state?</strong></summary>

**Answer:**
We manage Terraform state adhering to enterprise resilience and security standards:

1. **Remote Backend Storage with S3 & DynamoDB:**
   - State files are stored in an Amazon S3 bucket with **Object Versioning** enabled to preserve point-in-time recovery points.
   - **Distributed State Locking:** Configured with Amazon DynamoDB (`LockID` attribute) to prevent concurrent executions from causing race conditions or state corruption.
2. **Strict Encryption & Least Privilege:**
   - Enforce AWS KMS Customer Managed Key (CMK) encryption at rest and TLS 1.3 in transit (`aws:SecureTransport: true`).
   - Restrict access via S3 Bucket Policies to dedicated CI/CD execution IAM roles.
3. **State Segregation & Layering:**
   - Rather than maintaining a monolithic state file for the entire infrastructure, state is partitioned by environment and architectural layer (`networking.tfstate`, `eks-cluster.tfstate`, `databases.tfstate`).
   - Cross-stack data sharing is handled via remote state data sources (`terraform_remote_state`) or AWS SSM Parameter Store references.
</details>

<details>
<summary><strong>● What Terraform modules are you familiar with or have used?</strong></summary>

**Answer:**
I have extensive experience both consuming battle-tested open-source community modules and engineering custom enterprise internal modules:

1. **AWS Community Modules (Cloud Posse / Terraform AWS Modules):**
   - **`terraform-aws-modules/vpc/aws`**: Configures multi-AZ VPCs, public/private/database subnets, NAT gateways, and VPC endpoints.
   - **`terraform-aws-modules/eks/aws`**: Provisions complete EKS clusters, OIDC providers, managed node groups, and cluster access entries.
   - **`terraform-aws-modules/rds-aurora/aws`**: Deploys Multi-AZ Aurora PostgreSQL/MySQL clusters with read replicas, parameter groups, and automated backups.
   - **`terraform-aws-modules/security-group/aws`**: Configures granular ingress/egress rules.

2. **Custom Enterprise Internal Modules:**
   - Engineered modular, reusable blueprints adhering to company compliance:
     - Standardized **Microservice Ingress & ALB Module**.
     - **IAM Roles for Service Accounts (IRSA) Module** tying Kubernetes ServiceAccounts to least-privilege IAM policies.
     - **S3 Secure Bucket Module** with automated lifecycle policies, bucket logging, and KMS key association.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● What are the key AWS services required for building a Rust-based microservices platform?</strong></summary>

**Answer:**
Building an enterprise-grade, high-throughput Rust microservices platform on AWS leverages the following core services:

```
[ Route 53 / AWS WAF ]
         │
         ▼
[ Application Load Balancer / AWS API Gateway ]
         │
         ▼
[ Amazon EKS / AWS Fargate ] ──> (Rust Axum / Tokio Containers)
    │           │
    ├── (Async) └──> [ Amazon MSK (Kafka) / Amazon SQS & SNS ]
    │
    ├── (Cache) ───> [ Amazon ElastiCache (Redis) ]
    ├── (OLTP)  ───> [ Amazon Aurora PostgreSQL Serverless v2 ]
    ├── (NoSQL) ───> [ Amazon DynamoDB ]
    │
    └── (Obs.)  ───> [ CloudWatch + AWS X-Ray (OpenTelemetry) + Managed Prometheus & Grafana ]
```

- **Compute & Orchestration:** **Amazon EKS** with Graviton3/4 instances or **AWS Fargate** for running low-memory, high-concurrency Rust containers (using Tokio / Axum / Actix-web).
- **Networking & API Gateway:** **Application Load Balancer (ALB)** or **Amazon API Gateway** with AWS WAF for rate limiting, SSL termination, and JWT authorization.
- **Messaging & Event-Driven Backbone:** **Amazon MSK (Managed Streaming for Apache Kafka)** or **Amazon SQS/SNS** for decoupled async event streaming.
- **Databases & Cache:** **Amazon Aurora PostgreSQL Serverless v2**, **Amazon DynamoDB** (sub-10ms key-value store), and **Amazon ElastiCache Redis** for distributed caching.
- **Security & Identity:** **AWS KMS**, **AWS Secrets Manager**, and **AWS IAM Roles for Service Accounts (IRSA)**.
- **Observability:** **AWS X-Ray** / AWS Distro for OpenTelemetry (ADOT), **Amazon CloudWatch**, and Amazon Managed Prometheus/Grafana.
</details>

<details>
<summary><strong>↳ Follow-up: For a Rust-based microservices platform on AWS, what would you use for asynchronous communication between services?</strong></summary>

**Answer:**
Depending on throughput, ordering guarantees, and architectural pattern:

1. **Amazon MSK (Managed Streaming for Apache Kafka) (High-Throughput Event Streaming):**
   - Ideal for event-driven architectures, event sourcing, and high-frequency stream processing (> 100k events/sec).
   - Rust services leverage the high-performance **`rdkafka`** crate (wrapper around C `librdkafka`) with consumer groups, partition rebalancing, and exactly-once processing semantics.
2. **Amazon SNS + SQS Fan-Out Pattern (Decoupled Task Processing):**
   - Publishers publish events to an **Amazon SNS Topic**.
   - Multiple **Amazon SQS Queues** subscribe to the topic with Dead Letter Queues (DLQs) attached.
   - Rust workers consume messages asynchronously using **`aws-sdk-sqs`** and Tokio asynchronous runtime loops, providing automatic retry backoff and fault isolation.
3. **Amazon EventBridge (Schema-Driven Enterprise Event Bus):**
   - For loosely coupled microservice domain events across AWS accounts with content-based filtering and OpenAPI schema registry integration.
</details>

<details>
<summary><strong>↳ Follow-up: For a Rust-based microservices platform on AWS, what services would you use for data storage?</strong></summary>

**Answer:**
We implement polyglot persistence based on workload access patterns:

1. **Relational / Transactional (OLTP):**
   - **Amazon Aurora PostgreSQL (Serverless v2 / Multi-AZ):** ACID-compliant transactional data (users, orders, payments). Rust integrates using asynchronous connection pools via **`sqlx`** or **`diesel`** with compile-time SQL verification.
2. **High-Velocity NoSQL / Key-Value:**
   - **Amazon DynamoDB:** For shopping carts, user sessions, idempotency keys, and device states requiring predictable single-digit millisecond latency at any scale. Rust interfaces via the official **`aws-sdk-dynamodb`**.
3. **In-Memory Cache:**
   - **Amazon ElastiCache for Redis / Valkey:** Low-latency caching of hot database rows, distributed rate-limiting tokens, and pub/sub. Rust services use the asynchronous **`fred`** or **`redis-rs`** crate with connection pooling.
4. **Unstructured & Object Storage:**
   - **Amazon S3:** Storing media assets, invoices, PDF exports, and audit logs with lifecycle tiers to Glacier.
</details>

<details>
<summary><strong>● What are the major differences between AWS ECS, EKS, and Fargate for orchestration?</strong></summary>

**Answer:**
These represent distinct orchestration layers versus compute engines:

| Dimension | AWS ECS (Elastic Container Service) | AWS EKS (Elastic Kubernetes Service) | AWS Fargate |
| :--- | :--- | :--- | :--- |
| **Architectural Model** | AWS-proprietary container orchestrator. Simpler, deeply integrated with AWS ecosystem (Task Definitions, Services). | Open-source Kubernetes orchestrator. Highly portable, cloud-agnostic, massive CNCF ecosystem (Helm, Istio, Argo CD). | **Serverless Compute Engine** (not an orchestrator itself). Runs containers on-demand without managing EC2 hosts. |
| **Operational Overhead** | Low to moderate. AWS manages the orchestrator control plane free of charge. | Moderate to high. Requires managing Kubernetes versions, add-ons, CRDs, RBAC, and cluster networking. Costs $0.10/hr per cluster. | **Zero host management.** No OS patching, AMI management, or instance scaling. |
| **Compute Compatibility** | Runs on EC2 instances or **AWS Fargate**. | Runs on EC2 instances (Self-managed / Managed Node Groups / Karpenter) or **AWS Fargate**. | Works as the underlying execution backend for **both** ECS and EKS. |
| **Ecosystem & Portability** | Vendor lock-in to AWS APIs. Minimal third-party tool ecosystem. | Extreme portability across AWS, Azure (AKS), GCP (GKE), and on-premises. | Tied to AWS infrastructure. |
</details>

<details>
<summary><strong>● Are you familiar with AWS X-Ray?</strong></summary>

**Answer:**
Yes, **AWS X-Ray** is a distributed tracing service that collects data about requests served by an application to provide an end-to-end trace map of microservices interactions.

1. **How It Works:**
   - Injects trace context headers (`X-Amzn-Trace-Id`) across service boundaries (ALB -> API Gateway -> EKS Microservice A -> Microservice B -> Aurora DB / SQS).
   - Generates a **Service Map** illustrating latencies, HTTP 4xx/5xx error rates, downstream database queries, and bottlenecks across distributed architectures.
2. **Modern Implementation (OpenTelemetry Standard):**
   - Rather than legacy proprietary SDKs, we deploy the **AWS Distro for OpenTelemetry (ADOT)** collector as a Kubernetes DaemonSet or sidecar.
   - Microservices instrumented with OpenTelemetry SDKs send traces (OTLP over gRPC) to ADOT, which securely exports them to AWS X-Ray and CloudWatch ServiceLens.
</details>

<details>
<summary><strong>● How do you perform cost optimization on AWS?</strong></summary>

**Answer:**
Cost optimization requires a structured FinOps lifecycle across four operational levers:

1. **Compute Optimization:**
   - Transition eligible workloads to **AWS Graviton3/4** processors (20% cost reduction).
   - Leverage **Spot Instances** for stateless pods and CI/CD agents using **Karpenter** on EKS.
   - Implement **Compute Savings Plans** (commit to 1- or 3-year hourly spend for up to 66% discount on baseline EC2/Fargate/Lambda).
2. **Storage Rightsizing:**
   - Migrate EBS volumes from `gp2` to **`gp3`** (20% lower baseline storage cost).
   - Enforce **S3 Intelligent-Tiering** and automated lifecycle transition policies to S3 Glacier for aging audit and log archives.
3. **Database & Network Efficiencies:**
   - Scale down or pause non-production RDS instances during off-hours using AWS Instance Scheduler.
   - Eliminate unnecessary NAT Gateway cross-AZ data processing charges by keeping traffic within the same AZ and deploying **VPC Gateway Endpoints** (S3, DynamoDB) which route traffic free of charge.
4. **Continuous Governance:**
   - Daily AWS Cost Anomaly Detection alerts sent to Slack.
   - Enforcing tagging policies (`CostCenter`, `Owner`, `Environment`) via AWS Organizations Service Control Policies (SCPs).
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● How do you monitor REST APIs in production?</strong></summary>

**Answer:**
Production REST API monitoring is built on Google SRE's **Four Golden Signals** (Latency, Traffic, Errors, Saturation):

```
                        [ REST API Monitoring Architecture ]
                                        │
           +----------------------------+----------------------------+
           │                            │                            │
           ▼                            ▼                            ▼
[ 1. Metrics (Prometheus) ]    [ 2. Distributed Tracing ]   [ 3. Centralized Logging ]
- RED: Rate, Errors, Duration  - AWS X-Ray / Jaeger         - FluentBit -> OpenSearch
- HTTP 5xx rate < 0.1%         - p99 tail latency triage    - Structured JSON logs
- p95/p99 latency histograms   - Database lock spans        - Error stack trace search
```

1. **The RED Method (Rate, Errors, Duration):**
   - **Rate:** Ingested requests per second (`http_requests_total`).
   - **Errors:** Error rate percentage (`http_requests_total{status=~"5.."}`). Alert if 5xx exceeds 0.5% over 5 minutes.
   - **Duration:** Request latency tracked via Prometheus Histograms (`http_request_duration_seconds_bucket`). Alert if p99 exceeds 500ms.
2. **Synthetic / Blackbox Monitoring:**
   - CloudWatch Synthetics Canaries or Grafana Synthetic Monitoring executing synthetic REST requests every 60 seconds from external global regions to verify uptime, DNS resolution, and SSL validity.
3. **Distributed Tracing & APM:**
   - Ingesting traces via OpenTelemetry to correlate slow API responses directly with slow SQL queries or third-party HTTP dependencies.
4. **Alerting & Escalation:**
   - Prometheus Alertmanager routing multi-burn-rate alerts to **PagerDuty** for primary SRE on-call dispatch.
</details>

#### 【 SECURITY 】

<details>
<summary><strong>↳ Follow-up: For a Rust-based microservices platform on AWS, which services or measures would you use for security?</strong></summary>

**Answer:**
We implement defense-in-depth across six distinct architectural layers:

1. **Perimeter & Edge Protection:**
   - **AWS WAF** attached to ALBs/CloudFront: Enforces OWASP Top 10 rule sets, SQL injection prevention, cross-site scripting (XSS) mitigation, and IP reputation rate limiting.
   - **AWS Shield Advanced:** Protects against Layer 3/4 Distributed Denial of Service (DDoS) attacks.
2. **Identity & Access Management:**
   - **EKS Pod Identity / IRSA (IAM Roles for Service Accounts):** Eliminates static IAM credentials inside containers; Rust pods assume short-lived, least-privilege IAM roles.
   - **OAuth2 / OIDC JWT Validation:** Microservices validate JWT signatures (issued by Amazon Cognito / Okta) at the edge or via Actix/Axum middleware.
3. **Network Isolation & Zero Trust:**
   - Multi-AZ private VPC subnets with zero public IP exposure for microservices and databases.
   - **Kubernetes NetworkPolicies:** Default-deny ingress and egress rules isolating service-to-service communication.
   - **Mutual TLS (mTLS):** Enforced across microservices via a service mesh (Istio / Linkerd) or AWS App Mesh.
4. **Data Encryption:**
   - **In Transit:** TLS 1.3 enforced on all external and internal endpoints.
   - **At Rest:** AWS KMS envelope encryption for Aurora databases, DynamoDB, S3, EBS, and Kubernetes secrets in `etcd`.
5. **Container & Application Security:**
   - Minimal **Distroless/Scratch** container base images containing zero package managers or shells.
   - **Pod Security Standards (Restricted):** Containers execute as non-root (`runAsNonRoot: true`), read-only root filesystems, dropping all Linux capabilities (`cap_drop: ALL`).
   - Automated dependency vulnerability scanning in CI/CD using `cargo audit`.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Can you explain the circuit breaker pattern used to prevent cascading failures in microservices?</strong></summary>

**Answer:**
The **Circuit Breaker Pattern** prevents a failing downstream service from exhausting resources (threads, memory, connections) across caller services, avoiding a system-wide catastrophic cascading outage:

```
                  +-----------------------------------+
                  |                                   |
                  v                                   |
+-------------------+  Failure Threshold Exceeded   +------------------+
|   CLOSED STATE    | ----------------------------> |    OPEN STATE    |
| (Normal traffic,  |                               | (Fails fast      |
|  calls execute)   | <---------------------------- |  instantly with  |
+-------------------+   Success threshold met       |  fallback)       |
          ^                                         +------------------+
          |                                                   |
          |           +-----------------------+               |
          |           |   HALF-OPEN STATE     | <-------------+
          +---------- | (Tests limited canary |   Wait timeout expires
                      |  calls downstream)    |
                      +-----------------------+
```

1. **Closed State:**
   - Normal operation. Requests pass through to the downstream service. The circuit breaker counts successes and failures over a sliding time window.
2. **Open State:**
   - When the error rate breaches a predefined threshold (e.g., 50% failures over 10 seconds), the circuit **trips OPEN**.
   - Subsequent calls **fail fast immediately** without attempting network calls downstream, returning a cached response, default fallback value, or HTTP 503. This protects the caller's connection pool and gives the downstream service breathing room to recover.
3. **Half-Open State:**
   - After a configured sleep window (e.g., 30 seconds), the breaker transitions to **Half-Open**.
   - It allows a limited number of trial (probe) requests through. If these succeed, the breaker resets to **Closed**. If any fail, it resets back to **Open**.
</details>

<details>
<summary><strong>↳ Follow-up: How would you prevent cascading failures in a microservices system, such as when a circuit opens after repeated failures?</strong></summary>

**Answer:**
Beyond basic circuit breakers, we design resilient distributed systems using a defense-in-depth reliability pattern:

1. **Graceful Fallbacks & Degraded Operation:**
   - When the circuit opens, return a degraded response rather than throwing a hard 500 error:
     - E.g., If the Recommendation Service fails, the UI falls back to a static list of popular items from an in-memory Redis cache.
2. **Strict Timeouts & Deadlines:**
   - Every outgoing HTTP/gRPC request must enforce strict, aggressive timeouts (e.g., 500ms socket timeout). Without timeouts, slow downstream responses tie up upstream worker threads until the connection pool starves.
3. **Exponential Backoff with Jitter:**
   - Retries should never be executed immediately. Implement exponential backoff ($2^n \times \text{base}$) combined with randomized **jitter** to prevent the "Thundering Herd" problem from overwhelming a recovering service.
4. **Bulkhead Pattern:**
   - Partition critical resource pools (HTTP client connection pools, thread pools, memory allocations) so that a failure in one non-critical downstream integration cannot exhaust resources needed for core checkout/payment flows.
5. **Rate Limiting & Shedding Load:**
   - Implement token-bucket rate limiters at the API Gateway to shed excess traffic when latency breaches critical thresholds.
</details>

<details>
<summary><strong>● Suppose API latency suddenly increases from 50 milliseconds to 2 seconds in production. How would you troubleshoot this issue?</strong></summary>

**Answer:**
I execute a methodical, metric-driven triage to isolate the exact latency contributor:

```
[ Ingress / ALB ] ──> [ Kubernetes / Pod ] ──> [ Downstream Services ] ──> [ Database / Cache ]
(Check Target Latency)   (Check CPU/Memory/GC)    (Check Traces / X-Ray)     (Check Slow Queries / Locks)
```

1. **Step 1: Metric Verification & Triage:**
   - Check CloudWatch ALB metrics: Compare `TargetResponseTime` vs `Latency`. If ALB latency is high but target response time is low, the delay is at the ALB/TLS handshake level. If `TargetResponseTime` is 2s, the application backend is responsible.
2. **Step 2: Distributed Tracing Inspection (AWS X-Ray / OpenTelemetry):**
   - Filter trace samples by duration (`duration > 1.5s`).
   - Inspect the trace waterfall chart: Identify which specific span is consuming the 1,950ms — is it a downstream REST API call, an Amazon Aurora SQL query, or application processing time?
3. **Step 3: Database & Cache Diagnostics:**
   - If traces point to the database:
     - Check Amazon Aurora Performance Insights and CloudWatch `CPUUtilization`, `DatabaseConnections`, and `ReadLatency`.
     - Check `pg_stat_activity` for table locks, lock contention, or slow unindexed sequential scans (`pg_stat_statements`).
     - Check ElastiCache Redis memory saturation or CPU spike (`EngineCPUUtilization`).
4. **Step 4: Pod & Node Health Check:**
   - Run `kubectl top pods -n prod` and `kubectl top nodes`.
   - Check if pods are experiencing **CPU Throttling** (`container_cpu_cfs_throttled_periods_total`) due to overly restrictive CPU limits.
   - Check application JVM / garbage collection pause logs for stop-the-world GC pauses.
5. **Step 5: Mitigation:**
   - If database connection pool exhaustion: Increase connection pool or scale read replicas.
   - If CPU throttling: Increase CPU limits or scale out pod replicas via HPA.
   - If bad release: Roll back deployment to the previous stable revision.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Could you tell me about yourself and your roles and responsibilities in your current project?
</details>
</details>

<details open>
<summary><h2>🏢 Nisum</h2></summary>

<details open>
<summary><h3>HR</h3></summary>

*Date: Yesterday at 03:03 PM*

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Which city are you currently located in?

↳ **Candidate Introduction:** *Why didn't you attend this interview in person?*

↳ **Candidate Introduction:** *Can you clarify exactly where you are currently located?*

↳ **Candidate Introduction:** *Did you travel to Visakhapatnam recently?*

↳ **Candidate Introduction:** *Did you travel to Visakhapatnam for a festival, or was it for another reason?*

● **Candidate Introduction:** Are you currently still working with TransUnion, and if not, until what date did you work there?

↳ **Candidate Introduction:** *Can you confirm that your last working day with TransUnion is the 10th of September?*

● **Candidate Introduction:** Do you currently have any other job offer in hand?

↳ **Candidate Introduction:** *Are you unwilling to relocate to Chennai for the other offer you have?*

↳ **Candidate Introduction:** *Are you settled in Visakhapatnam or in Hyderabad?*

↳ **Candidate Introduction:** *Are you specifically looking for job opportunities in Hyderabad?*

● **Candidate Introduction:** Did you previously also work with TransUnion before your current stint?

↳ **Candidate Introduction:** *Why did you work at Caliber for only 8 months before leaving?*

↳ **Candidate Introduction:** *So you returned back to TransUnion after leaving Caliber?*

↳ **Candidate Introduction:** *What role/position were you working as at TransUnion?*
</details>
</details>




