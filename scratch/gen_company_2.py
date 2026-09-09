# -*- coding: utf-8 -*-
"""Generator for LTM interview round (Level 1)."""

def get_ltm_markdown():
    return """<details open>
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
   The script scans target log directories (e.g., `C:\\inetpub\\logs\\LogFiles`, application logs) and removes files older than 14 days while logging deleted file counts:
   ```powershell
   $LogPath = "C:\\inetpub\\logs\\LogFiles"
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
           path: C:\\Scripts
           state: directory

       - name: Deploy Log Cleanup Script
         ansible.windows.win_copy:
           src: files/Clean-Logs.ps1
           dest: C:\\Scripts\\Clean-Logs.ps1

       - name: Create Daily Scheduled Task
         community.windows.win_scheduled_task:
           name: "DailyLogCleanup"
           description: "Deletes application and IIS logs older than 14 days"
           actions:
             - path: powershell.exe
               arguments: -ExecutionPolicy Bypass -File C:\\Scripts\\Clean-Logs.ps1
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
   $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File C:\\Scripts\\Clean-Logs.ps1"
   $Trigger = New-ScheduledTaskTrigger -Daily -At 2am
   $Principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\\SYSTEM" -LogonType ServiceAccount -RunLevel Highest
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
     aws ec2 create-snapshot \
       --volume-id vol-0123456789abcdef0 \
       --description "Manual snapshot before OS upgrade" \
       --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Name,Value=prod-db-backup}]'
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
</details>"""
