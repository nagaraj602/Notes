# -*- coding: utf-8 -*-
"""Generator for Mphasis interview rounds (Level 1 & Level 2)."""

def get_mphasis_markdown():
    return """<details open>
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
data = ["server1=active\n", "server2=maintenance\n"]
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
</details>"""
