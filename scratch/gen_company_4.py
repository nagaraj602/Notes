# -*- coding: utf-8 -*-
"""Generator for Bounteous interview round (Level 1)."""

def get_bounteous1_markdown():
    return """<details open>
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
| **Scalability** | Becomes unmanageable at scale: connecting $N$ VPCs requires $\frac{N(N-1)}{2}$ peering connections | Scales effortlessly: supports up to **5,000 VPC attachments** per gateway |
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
</details>"""
