# -*- coding: utf-8 -*-
"""Generator for Bounteous interview round (Level 2)."""

def get_bounteous2_markdown():
    return """<details open>
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
</details>"""
