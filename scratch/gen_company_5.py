# -*- coding: utf-8 -*-
"""Generator for Apty interview round (Level 1)."""

def get_apty_markdown():
    return """<details open>
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
</details>"""
