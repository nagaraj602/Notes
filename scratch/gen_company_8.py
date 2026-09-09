# -*- coding: utf-8 -*-
"""Generator for Virtusa interview round (Level 1)."""

def get_virtusa_markdown():
    return """<details open>
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
</details>"""
