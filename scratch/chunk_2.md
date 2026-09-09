<details open>
<summary><h2>🏢 Curatal</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 LINUX 】

<details>
<summary><strong>● In Linux, how do you search for a specific word inside a file?</strong></summary>

**Answer:**
In Linux, the primary and most versatile tool for searching text inside files is `grep`, along with modern utilities like `ripgrep` (`rg`) and stream processing tools like `awk` and `sed`.

1. **Standard `grep` commands:**
   - **Case-sensitive search:**
     ```bash
     grep "error_code" /var/log/application.log
     ```
   - **Case-insensitive search (`-i`) with line numbers (`-n`):**
     ```bash
     grep -in "connection refused" /var/log/syslog
     ```
   - **Recursive directory search (`-r` or `-R`) with file names only (`-l`):**
     ```bash
     grep -rnwl '/etc/nginx/' -e "proxy_pass"
     ```
   - **Display context lines (`-B` before, `-A` after, `-C` both):**
     ```bash
     grep -C 3 "NullPointerException" /var/log/app/catalina.out
     ```
   - **Extended regular expressions (`-E` or `egrep`):**
     ```bash
     grep -E "(FATAL|CRITICAL): [0-9]{3}" app.log
     ```

2. **Stream & text processing alternatives:**
   - **`awk` (search and format specific fields):**
     ```bash
     awk '/Failed password/ {print $1, $2, $11}' /var/log/auth.log
     ```
   - **`ripgrep` (`rg`) (ultra-fast for large production codebases/logs):**
     ```bash
     rg -i "database_url" /opt/microservices/
     ```
</details>

<details>
<summary><strong>● If a Linux file system becomes full, what steps would you follow to identify the root cause?</strong></summary>

**Answer:**
When a Linux file system hits 100% disk utilization, services can crash, logs stop writing, and database transactions stall. Here is the production troubleshooting framework:

1. **Identify the Full Mount Point:**
   ```bash
   df -h
   ```
   Determine whether the issue is on `/`, `/var`, `/home`, or a specific data volume.

2. **Check for Inode Exhaustion (`df -i`):**
   ```bash
   df -i
   ```
   Even if disk space shows available megabytes, running out of inodes prevents any new file creation (common when millions of tiny session files or mail queue files accumulate in `/var/spool` or `/tmp`).

3. **Locate the Largest Directories & Files:**
   ```bash
   # Find top 10 largest directories from the target mount
   du -ahx /var | sort -rh | head -n 10

   # Find individual large files (>1GB)
   find /var -xdev -type f -size +1G -exec ls -lh {} +
   ```
   *(Note: `-xdev` prevents `find` and `du` from crossing into other mounted filesystems).*

4. **Identify Deleted Files Still Held Open by Processes (Orphaned File Handles):**
   A common production root cause occurs when someone deletes a running log file (`rm app.log`), but the process still holds the open file descriptor, meaning disk blocks cannot be freed by the kernel.
   ```bash
   lsof +L1
   # or
   lsof | grep deleted
   ```
   - **Remediation without restarting the service:** Truncate the file via its proc file descriptor:
     ```bash
     : > /proc/<PID>/fd/<FD_NUMBER>
     ```

5. **Examine Common Culprits:**
   - **Log growth & logrotate failure:** Check `/var/log` for uncompressed, unrotated logs. Vacuum systemd journal logs:
     ```bash
     journalctl --vacuum-size=500M
     ```
   - **Container runtime accumulation:** Docker/containerd unused layers, stopped containers, and build cache:
     ```bash
     docker system df
     docker system prune -af --volumes
     ```
   - **Core dumps:** Check `/var/crash` or `/var/lib/systemd/coredump`.
</details>

<details>
<summary><strong>● How do you view all running processes on a Linux system?</strong></summary>

**Answer:**
Linux provides multiple tools to inspect process hierarchies, resource usage, and threads:

1. **`ps` command (Snapshot of current processes):**
   - **BSD syntax (standard for DevOps engineers):**
     ```bash
     ps aux
     ```
     `a` = all users, `u` = user-oriented format (shows CPU/memory percentages, user, start time), `x` = includes processes without a controlling TTY (daemons).
   - **POSIX / System V syntax:**
     ```bash
     ps -ef
     ```
     `-e` = select all processes, `-f` = full-format listing (shows UID, PID, PPID - Parent Process ID, C, STIME, TTY, TIME, CMD).

2. **Interactive Real-Time Monitoring:**
   - **`top`:** Real-time summary of CPU states (us, sy, ni, id, wa, hi, si, st), memory, swap, and top consumers.
   - **`htop` / `btop`:** Enhanced terminal viewers supporting mouse scrolling, thread visualization, and instant process killing (`F9`).

3. **Process Hierarchy & Tree View:**
   ```bash
   pstree -p
   ```
   Displays processes in a tree structure showing parent-child relationships, useful for tracing fork-bombs or orphaned worker pools.

4. **Targeted Process Inspection:**
   - Find process by name: `pgrep -l <process_name>` or `pidof <daemon>`.
   - Inspect directly via the `/proc` filesystem:
     ```bash
     cat /proc/<PID>/status
     ls -l /proc/<PID>/exe
     cat /proc/<PID>/cmdline
     ```
</details>

<details>
<summary><strong>● If a user encounters a 'permission denied' error on Linux, what would you check to troubleshoot it?</strong></summary>

**Answer:**
A systematic diagnostic checklist for 'Permission Denied' errors:

1. **Standard POSIX File Permissions (`ls -la`):**
   - Check Read (`r`), Write (`w`), and Execute (`x`) bits for User, Group, and Others:
     ```bash
     ls -la /path/to/target/file
     ```
   - **Directory Traversal:** For a user to access a file inside a directory, the user must have **execute (`+x`) permissions on all parent directories** leading up to the file.

2. **Ownership & Group Membership:**
   - Verify file owner and group: `chown user:group filename`.
   - Verify the requesting user's identity and secondary groups:
     ```bash
     id <username>
     groups <username>
     ```

3. **POSIX Access Control Lists (ACLs):**
   - If `ls -l` shows a plus sign (e.g. `-rwxr-xr--+`), an extended ACL is enforced:
     ```bash
     getfacl /path/to/target/file
     ```
   - Adjust ACL: `setfacl -m u:<username>:rwx /path/to/target/file`.

4. **Linux Security Modules (SELinux / AppArmor):**
   - **SELinux:** Check current mode (`getenforce`). Inspect audit log for AVC denials:
     ```bash
     ausearch -m avc -ts recent
     sealert -a /var/log/audit/audit.log
     ```
     Fix mismatched context: `restorecon -Rv /path/to/target`.
   - **AppArmor:** Check profile status: `aa-status`.

5. **File Attribute Immutability:**
   - Check if the immutable (`i`) or append-only (`a`) flag is enabled:
     ```bash
     lsattr /path/to/target/file
     ```
     Remove immutable bit: `chattr -i /path/to/target/file`.

6. **Filesystem Mount Options:**
   - Check if the filesystem is mounted as read-only (`ro`) or with security flags preventing execution (`noexec`, `nosuid`):
     ```bash
     mount | grep $(df /path/to/target/file | tail -1 | awk '{print $6}')
     ```
</details>

<details>
<summary><strong>● How would you schedule a script to run every day at 1 AM on Linux?</strong></summary>

**Answer:**
There are two production-grade ways to schedule tasks on Linux: traditional `cron` and modern `systemd` timers.

#### Approach 1: Using Cron (Standard)
1. Open the crontab for the relevant user:
   ```bash
   crontab -e
   ```
2. Add the cron expression:
   ```cron
   0 1 * * * /usr/local/bin/daily_backup.sh >> /var/log/daily_backup.log 2>&1
   ```
   - **Cron Syntax breakdown:**
     - `0`: Minute (0)
     - `1`: Hour (1 AM in 24-hour format)
     - `*`: Day of month (any)
     - `*`: Month (any)
     - `*`: Day of week (any)
   - **Senior Best Practices for Cron:**
     - Always use **absolute paths** for both the script and commands inside the script (`/usr/bin/python3`, `/usr/bin/aws`) because cron runs with a minimal `$PATH`.
     - Explicitly redirect stdout and stderr (`>> /path/to/log 2>&1`) to prevent silent failures.
     - Ensure the script has executable permissions (`chmod +x /usr/local/bin/daily_backup.sh`).

#### Approach 2: Using Systemd Timers (Enterprise Recommended)
Systemd timers offer execution logging via `journalctl`, dependency ordering, and catch-up on missed runs.
1. Create a service unit `/etc/systemd/system/daily-backup.service`:
   ```ini
   [Unit]
   Description=Daily Backup Job

   [Service]
   Type=oneshot
   ExecStart=/usr/local/bin/daily_backup.sh
   User=backupuser
   ```
2. Create a matching timer unit `/etc/systemd/system/daily-backup.timer`:
   ```ini
   [Unit]
   Description=Run Daily Backup at 1 AM

   [Timer]
   OnCalendar=*-*-* 01:00:00
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```
3. Enable and start the timer:
   ```bash
   systemctl daemon-reload
   systemctl enable --now daily-backup.timer
   systemctl list-timers
   ```
</details>

<details>
<summary><strong>● What is the purpose and use of the Linux command 'ss \-tulmp'?</strong></summary>

**Answer:**
The `ss` (Socket Statistics) command is the modern, high-performance successor to `netstat`. It retrieves socket details directly from the Linux kernel's `sock_diag` netlink subsystem, making it orders of magnitude faster on servers with thousands of open connections.

**Flag Breakdown for `ss -tulmp`:**
- `-t`: Display **TCP** sockets.
- `-u`: Display **UDP** sockets.
- `-l`: Display only **Listening** sockets (omits active established client connections).
- `-m`: Display socket **Memory usage** (shows receive/send buffers: `skmem(r0,rb131072,t0,tb16384...)`).
- `-p`: Display the **Process** and PID using the socket (requires `sudo` or `root` privileges).

**Example Output:**
```text
Netid  State   Recv-Q  Send-Q   Local Address:Port   Peer Address:Port   Process
tcp    LISTEN  0       128            0.0.0.0:80          0.0.0.0:*       users:(("nginx",pid=1420,fd=6))
tcp    LISTEN  0       511            0.0.0.0:6379        0.0.0.0:*       users:(("redis-server",pid=982,fd=7))
```

**Common Troubleshooting Use Cases:**
1. **Port conflict detection:** Check if an application fails to start because port 80 or 8080 is already bound by another daemon.
2. **Binding interface verification:** Confirm if a service is bound to `127.0.0.1` (localhost only) vs `0.0.0.0` (all external interfaces).
3. **Socket buffer bloat / exhaustion:** The `-m` flag reveals whether TCP buffers are overflowing during high network throughput or DDoS scenarios.
</details>

<details>
<summary><strong>● Which scripting languages have you worked with?</strong></summary>

**Answer:**
In enterprise DevOps and cloud engineering environments, I work with three primary scripting and automation languages based on the problem domain:

1. **Bash / Shell Scripting:**
   - Primary use cases: Linux OS bootstrap scripts (cloud-init), Docker container entrypoint scripts (`entrypoint.sh`), CI/CD runner steps (Jenkins, GitLab CI, GitHub Actions), and system maintenance/log cleanup.
   - Core proficiencies: POSIX standards, strict error handling (`set -euo pipefail`), regex processing, trap signal handling for graceful container termination.

2. **Python:**
   - Primary use cases: Cloud automation via AWS SDK (`boto3`), REST API integrations, Kubernetes client automation (`kubernetes-client`), custom Prometheus metrics exporters, and automated data validation scripts.
   - Core proficiencies: Object-oriented scripting, virtual environments, packaging, error handling, requests, JSON/YAML manipulation.

3. **Go (Golang):**
   - Primary use cases: Writing custom Kubernetes Operators using Kubebuilder / Operator SDK, high-performance CLI utilities, and contributing custom resources or extensions to Terraform providers.
</details>

<details>
<summary><strong>↳ Follow-up: Can you write a simple shell script that adds the numbers from 1 to 100?</strong></summary>

**Answer:**
Here are two implementations: an idiomatic Bash iterative loop, and a mathematical $O(1)$ one-liner.

#### Implementation 1: Idiomatic Bash Loop
```bash
#!/usr/bin/env bash
set -euo pipefail

total=0

for (( i=1; i<=100; i++ )); do
    (( total += i ))
done

echo "The sum of numbers from 1 to 100 is: ${total}"
```

#### Implementation 2: Constant Time $O(1)$ Formula (Gauss Formula)
```bash
#!/usr/bin/env bash
set -euo pipefail

n=100
sum=$(( n * (n + 1) / 2 ))

echo "The sum of numbers from 1 to 100 is: ${sum}"
```

#### Implementation 3: One-liner using `seq` and `bc`
```bash
seq -s + 1 100 | bc
```
</details>

<details>
<summary><strong>↳ Follow-up: Can you explain the logic behind the shell script you just wrote to sum numbers from 1 to 100?</strong></summary>

**Answer:**
**Logical Breakdown:**
1. **Interpreter & Error Handling:**
   - `#!/usr/bin/env bash`: Ensures portability across different Linux distributions.
   - `set -euo pipefail`: Strict mode where `-e` exits immediately if a command fails, `-u` treats unset variables as errors, and `-o pipefail` ensures pipeline return codes reflect the last non-zero exit.

2. **Initialization:**
   - `total=0`: An accumulator variable initialized to zero to hold the running sum.

3. **C-Style Loop Construction:**
   - `for (( i=1; i<=100; i++ ))`:
     - Initialization (`i=1`): Sets counter variable `i` to 1.
     - Evaluation Condition (`i<=100`): Runs the loop body as long as `i` is less than or equal to 100. Once `i` increments to 101, the condition evaluates to false and the loop terminates.
     - Step Increment (`i++`): Increments `i` by 1 at the end of each iteration.

4. **Arithmetic Expansion:**
   - `(( total += i ))`: Uses Bash built-in arithmetic compound evaluation to add the current value of `i` to `total` without needing external subshells like `expr` or `bc`.

5. **Mathematical Equivalence:**
   - The loop performs 100 additions: $1 + 2 + 3 + \dots + 100 = 5050$.
   - This directly validates Carl Friedrich Gauss's arithmetic progression formula: $S = \frac{n(n+1)}{2} = \frac{100 \times 101}{2} = 5050$.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>↳ Follow-up: If an application is not responding, how would you troubleshoot and handle this situation, particularly in a Kubernetes environment?</strong></summary>

**Answer:**
When a Kubernetes-hosted application becomes unresponsive, I follow an outside-in, structured troubleshooting tree across the networking, control plane, pod, and application layers:

```
[ Ingress / ALB ] -> [ Service / Endpoints ] -> [ Pod Network (CNI) ] -> [ Container Runtime ] -> [ Application Engine ]
```

1. **Step 1: Ingress & Edge Layer:**
   - Verify if external traffic is reaching the cluster:
     ```bash
     kubectl get ingress -n <namespace>
     kubectl describe ingress <ingress-name> -n <namespace>
     ```
   - Check Ingress Controller logs (e.g. NGINX ingress or AWS Load Balancer Controller) for HTTP 502/504 errors or SSL handshake failures.

2. **Step 2: Service & Endpoints Resolution:**
   - Ensure the Service is correctly selecting pods:
     ```bash
     kubectl get svc <service-name> -n <namespace>
     kubectl get endpoints <service-name> -n <namespace>
     # Or in modern K8s:
     kubectl get endpointslices -l kubernetes.io/service-name=<service-name> -n <namespace>
     ```
   - **Crucial check:** If `Endpoints` is empty (`<none>`), the Service selector labels do not match the Pod labels.

3. **Step 3: Pod Status & Health Probes:**
   - Check pod health states across the namespace:
     ```bash
     kubectl get pods -n <namespace> -o wide
     ```
   - If pods show `CrashLoopBackOff`, `OOMKilled`, or `Pending`:
     ```bash
     kubectl describe pod <pod-name> -n <namespace>
     ```
   - Inspect the **Events** section: Look for failing **Liveness** or **Readiness** probes, scheduling failures due to CPU/memory insufficiency, or node taints.

4. **Step 4: Inspect Application Logs:**
   - Fetch live and crashed container logs:
     ```bash
     # Live logs
     kubectl logs <pod-name> -n <namespace> --tail=100
     # Previous crashed container instance logs
     kubectl logs <pod-name> -n <namespace> --previous
     ```
   - Search for thread deadlocks, unhandled exceptions, or database connection pool exhaustion.

5. **Step 5: Resource Utilization & Throttling:**
   - Check if the pod is hitting resource limits:
     ```bash
     kubectl top pod <pod-name> -n <namespace>
     ```
   - Extreme CPU throttling causes an application to stop responding to health checks without crashing.

6. **Step 6: Network Policies & In-Cluster Connectivity:**
   - Verify if a `NetworkPolicy` is inadvertently blocking ingress or egress traffic:
     ```bash
     kubectl get netpol -n <namespace>
     ```
   - Launch an ephemeral debug container to test connectivity directly from inside the cluster:
     ```bash
     kubectl run curl-test --rm -it --image=curlimages/curl -- curl -Iv http://<service-name>.<namespace>.svc.cluster.local:<port>/healthz
     ```
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● Which monitoring tools have you worked with?</strong></summary>

**Answer:**
I have worked extensively with enterprise observability and monitoring stacks spanning metrics, logs, traces, and synthetics:

1. **Prometheus & Grafana (Cloud-Native Standard):**
   - **Prometheus:** Deployed via `kube-prometheus-stack` / Prometheus Operator. Handles scraping metrics via `ServiceMonitor` and `PodMonitor` CRDs, time-series storage (TSDB), recording rules, and Alertmanager.
   - **Grafana:** Building interactive operational dashboards, SLO/SLA tracking, unified alerting, and templating across multiple data sources.

2. **Log Aggregation & Search:**
   - **ELK / EFK Stack:** Elasticsearch/OpenSearch, Fluentd/Fluentbit/Logstash, and Kibana.
   - **Grafana Loki:** Lightweight, label-indexed log aggregation tightly integrated with Grafana and Prometheus metrics.

3. **Application Performance Monitoring (APM) & Distributed Tracing:**
   - **OpenTelemetry (OTel):** Standardized telemetry collection using OpenTelemetry Collector.
   - **Jaeger / Zipkin:** Tracing distributed microservice call latencies and bottleneck spans.
   - **Datadog:** Comprehensive SaaS APM, infrastructure monitoring, synthetic tests, and network performance monitoring (NPM).

4. **Cloud-Native Provider Monitoring:**
   - **AWS CloudWatch & Container Insights:** Metrics, alarms, logs, and metric streams forwarded to Kinesis.
   - **Azure Monitor & Log Analytics Workspaces.**
</details>

<details>
<summary><strong>↳ Follow-up: How would you set up a Grafana dashboard?</strong></summary>

**Answer:**
Setting up an enterprise-grade Grafana dashboard involves a structured 5-step workflow:

1. **Configure Data Source:**
   - Navigate to `Configuration -> Data Sources -> Add data source`.
   - Select **Prometheus** (or CloudWatch/Elasticsearch), provide the HTTP URL (e.g. `http://prometheus-k8s.monitoring.svc:9090`), set scrape intervals, authentication tokens, and click **Save & Test**.

2. **Establish Dashboard Variables (Templating for Reusability):**
   - Under `Dashboard Settings -> Variables`, create dynamic drop-down selectors to allow filtering across environments, clusters, namespaces, and pods.
   - Example Query Variable for `$namespace`:
     ```promql
     label_values(kube_pod_info, namespace)
     ```
   - Example Query Variable for `$pod` dependent on `$namespace`:
     ```promql
     label_values(kube_pod_info{namespace="$namespace"}, pod)
     ```

3. **Build Visual Panels Using the Four Golden Signals:**
   - **Latency (p95 / p99):**
     ```promql
     histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{namespace="$namespace"}[5m])) by (le))
     ```
   - **Traffic (RPS):**
     ```promql
     sum(rate(http_requests_total{namespace="$namespace"}[5m])) by (status)
     ```
   - **Errors (Error Rate %):**
     ```promql
     (sum(rate(http_requests_total{status=~"5..", namespace="$namespace"}[5m])) / sum(rate(http_requests_total{namespace="$namespace"}[5m]))) * 100
     ```
   - **Saturation (CPU / Memory vs Limits):**
     ```promql
     sum(container_memory_working_set_bytes{namespace="$namespace"}) / sum(kube_pod_container_resource_limits{resource="memory", namespace="$namespace"}) * 100
     ```

4. **Organize Panels into Collapsible Rows:**
   - Group panels into rows: **Overview / Health Status**, **Application Performance**, **JVM / Runtime Metrics**, **Infrastructure Utilization**.

5. **Dashboard as Code (GitOps):**
   - Avoid manual UI creation in production. Export the dashboard JSON and manage it via:
     - **Terraform:** `resource "grafana_dashboard" "app_dashboard"`
     - **Kubernetes ConfigMap with Label:** A ConfigMap with the label `grafana_dashboard: "1"` automatically picked up by Grafana's sidecar container.
</details>

<details>
<summary><strong>↳ Follow-up: How would you set up alerting in Grafana?</strong></summary>

**Answer:**
Setting up alerting in modern Grafana (Grafana Unified Alerting) involves configuring **Alert Rules**, **Contact Points**, and **Notification Policies**:

1. **Step 1: Create an Alert Rule:**
   - Go to `Alerting -> Alert rules -> New alert rule`.
   - **Query A (Metric Scrape):** Define PromQL query, for example:
     ```promql
     sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100
     ```
   - **Condition B (Expression Threshold):** Set condition `WHEN Query A IS ABOVE 2` (trigger if error rate exceeds 2%).
   - **Evaluation Interval:** Set evaluation group to evaluate every `1m` for a duration of `5m` (pending state before firing to prevent flapping).

2. **Step 2: Add Rule Metadata & Annotations:**
   - Add Labels: `severity = critical`, `team = backend-sre`, `environment = production`.
   - Add Annotations:
     - **Summary:** `High HTTP 5xx error rate on {{ $labels.service }}`
     - **Description:** `Service {{ $labels.service }} has an error rate of {{ $values.B.Value }}% over the last 5 minutes.`
     - **Runbook URL:** `https://wiki.company.com/runbooks/high-error-rate`

3. **Step 3: Define Contact Points:**
   - Go to `Alerting -> Contact points -> Add contact point`.
   - Configure integrations:
     - **Slack:** Incoming Webhook URL and target channel `#prod-alerts`.
     - **PagerDuty:** Integration Key for high-priority incidents.
     - **Email / Webhook / OpsGenie.**

4. **Step 4: Configure Notification Policies (Routing Tree):**
   - Set up routing rules based on alert labels:
     - Root policy -> Default to `#general-monitoring` Slack channel.
     - Specific child policy -> If `severity = critical`, route immediately to PagerDuty with `repeat_interval = 4h`.
     - Non-prod child policy -> If `environment = dev`, route to `#dev-alerts` with muted weekends.

5. **Step 5: Mute Timings & Silences:**
   - Define Mute Timings for scheduled maintenance windows to suppress notifications during planned deployments.
</details>

<details>
<summary><strong>↳ Follow-up: Do you have any knowledge about annotations in the context of Prometheus/Grafana monitoring?</strong></summary>

**Answer:**
Yes, annotations serve two distinct, critical roles in the Prometheus and Grafana ecosystem:

1. **Alert Rule Annotations (Informational Metadata):**
   - In Prometheus and Grafana Alertmanager, while **Labels** are used to identify and route alerts (e.g. `severity="critical"`, `cluster="us-east-1"`), **Annotations** carry non-identifying, human-readable information.
   - They support templating using Go template syntax:
     ```yaml
     annotations:
       summary: "High memory utilization on instance {{ $labels.instance }}"
       description: "Instance {{ $labels.instance }} memory usage is currently at {{ $value | humanizePercentage }}."
       runbook_url: "https://ops.internal/runbooks/node-memory-leak"
       dashboard_url: "https://grafana.internal/d/node-exporter?var-node={{ $labels.instance }}"
     ```

2. **Grafana Dashboard Annotations (Visual Event Markers):**
   - Grafana dashboard annotations render vertical markers or colored shaded bands across time-series graphs to correlate metric anomalies with real-world operational events.
   - **Use Cases:**
     - **Deployments:** Marking the exact timestamp when a new Docker image or Git commit was deployed via Jenkins/Argo CD.
     - **Kubernetes Events:** Node reboots, OOMKilled pod terminations, or cluster auto-scaling events.
     - **Outage Periods:** Shading the timeline of an ongoing P1 incident.
   - **Implementation:** Configured in `Dashboard Settings -> Annotations`, querying Prometheus (e.g. `changes(kube_deployment_status_observed_generation[1m]) > 0`) or via Grafana's HTTP Annotations API invoked by CI/CD pipelines:
     ```bash
     curl -X POST -H "Authorization: Bearer $GRAFANA_API_KEY" \
       -H "Content-Type: application/json" \
       -d '{"text":"Deployed Release v2.4.0","tags":["deploy","prod"]}' \
       https://grafana.internal/api/annotations
     ```
</details>

<details>
<summary><strong>↳ Follow-up: Can you explain what templates are used for in Grafana's Alert Manager?</strong></summary>

**Answer:**
In Grafana Alertmanager (and Prometheus Alertmanager), **Notification Templates** are reusable template definitions written in Go templating syntax (`text/template`) used to customize and standardize the format of alert notification payloads sent to receivers like Slack, PagerDuty, Microsoft Teams, and Email.

**Key Purposes & Use Cases:**
1. **Standardizing Notification Layouts:**
   Instead of raw JSON or unformatted text, templates format alerts into rich Slack blocks or clean HTML emails showing title, status (FIRING / RESOLVED), severity, impacted components, and duration.
2. **Iterating Over Batched Alerts:**
   Alertmanager groups related alerts together to prevent alert fatigue. A template iterates over all grouped alerts using `{{ range .Alerts }}` to display each firing instance and its individual value.
3. **Dynamic Links to Dashboards and Runbooks:**
   Templates automatically generate actionable hyperlinks using alert metadata:
   ```gotemplate
   {{ define "slack.mycustom.message" }}
     {{ if eq .Status "firing" }}🔥 *ALERT FIRING* 🔥{{ else }}✅ *RESOLVED* ✅{{ end }}
     *Alert:* {{ .CommonLabels.alertname }} - {{ .CommonLabels.severity | toUpper }}
     {{ range .Alerts }}
       • *Instance:* `{{ .Labels.instance }}`
       • *Summary:* {{ .Annotations.summary }}
       • *Current Value:* `{{ .Values.B }}`
       • *Runbook:* <{{ .Annotations.runbook_url }}|Click Here>
     {{ end }}
   {{ end }}
   ```
4. **Conditional Formatting:** Applying different colors (red for Critical, yellow for Warning, green for Resolved) based on `.CommonLabels.severity`.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● How would you manage a situation where two P1 (highest priority) production issues occur simultaneously?</strong></summary>

**Answer:**
Handling simultaneous P1 incidents requires applying the **Incident Command System (ICS)** methodology to prevent cognitive overload, split resources effectively, and prioritize customer impact.

```
                  [ Executive Incident Commander (Overall Oversight) ]
                                         |
               +-------------------------+-------------------------+
               |                                                   |
      [ Bridge 1: War Room A ]                            [ Bridge 2: War Room B ]
      - Dedicated Ops Lead                                - Dedicated Ops Lead
      - Application Engineers                             - Database / Network SREs
      - Communications Lead                               - Communications Lead
      - Focus: Immediate Mitigation                       - Focus: Immediate Mitigation
```

**Step-by-Step Response Strategy:**

1. **Step 1: Triage & Assess Blast Radius:**
   - Quickly assess the business and financial impact of both issues:
     - *Issue A:* Core payment processing API failing (direct revenue loss and customer checkout failure).
     - *Issue B:* Customer profile/avatar image upload failing on non-critical portal (degraded experience, but checkout continues).
   - If engineering resources are constrained, **Issue A takes technical precedence** for immediate remediation.

2. **Step 2: Split Incident Leadership & Establish Dual War Rooms:**
   - Never keep both incidents on a single bridge—cross-talk leads to confusion.
   - Designate an **Overall Incident Commander (IC)** who maintains global situational awareness and manages executive communication.
   - Delegate two separate **Technical Leads (Ops Leads)** to run dedicated war rooms (Bridge A and Bridge B) with segregated engineering squads.

3. **Step 3: Focus on Mitigation Over Root Cause:**
   - The immediate goal during a P1 is **restoring service (Time to Restore - TTR)**, not deep root cause analysis:
     - Revert the latest deployment/hotfix if an update coincided with the incident.
     - Fail over traffic to secondary AWS regions or healthy availability zones.
     - Engage circuit breakers or degrade gracefully (e.g. disable search recommendations to preserve core database CPU).
     - Temporarily scale out compute or restart frozen worker pools.

4. **Step 4: Proactive Stakeholder & Customer Communication:**
   - Assign dedicated **Communications Leads** to update the public status page (e.g. Statuspage.io) and internal executive channels every 15–20 minutes with concise status updates: *Investigating -> Identified -> Mitigating -> Resolved*.

5. **Step 5: Post-Incident Review (Blameless Postmortem):**
   - Once both systems are stable, conduct a comprehensive blameless postmortem.
   - Determine if there was a common underlying failure mode (e.g. shared database bottleneck, upstream cloud provider outage, shared transit gateway saturation).
   - Track preventive action items with high priority in Jira.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you give me a brief introduction about yourself and your professional background?

● **Candidate Introduction:** How many total years of professional experience do you have?

<details>
<summary><strong>● Have you worked with any programming languages?</strong></summary>

**Answer:**
Yes. As a Senior DevOps Engineer, my programming focus is centered around systems automation, infrastructure orchestration, and cloud-native tool development:

- **Python:** My primary language for infrastructure automation, AWS SDK (`boto3`) scripting, serverless Lambda microservices, writing Kubernetes custom controllers via `kopf`, and developing custom monitoring exporters.
- **Bash / Shell:** Used extensively for Linux system provisioning, writing hardened container entrypoints, and orchestrating complex build and deployment workflows in CI/CD pipelines.
- **Go (Golang):** Used for developing custom Kubernetes Operators and controllers using the Operator SDK / Kubebuilder, analyzing open-source Kubernetes and Terraform provider codebases, and writing performant internal CLI utilities.
- **Groovy:** Extensively used for authoring maintainable, modular Jenkins Shared Libraries and declarative/scripted Jenkinsfiles.
</details>

<details>
<summary><strong>● If given the opportunity, how much time would you take to learn new technologies?</strong></summary>

**Answer:**
I follow an accelerated, hands-on learning framework that allows me to become productive rapidly:

1. **Days 1–3 (Core Concepts & Fundamentals):** Study official documentation, architecture designs, and core primitives rather than superficial tutorials.
2. **Days 4–7 (Hands-on Prototyping / PoC):** Build a functional Proof of Concept (PoC) in a local sandbox or development environment (e.g. containerizing the tool, creating sample manifests, deploying on Minikube or an isolated cloud VPC).
3. **Week 2 (Production Hardening & Best Practices):** Learn security implications (RBAC, least privilege, secret handling), high-availability considerations, and CI/CD integration.
4. **Weeks 3–4 (Production Deployment & Team Enablement):** Author reusable Terraform modules or Helm charts, write comprehensive runbooks and documentation, and lead a knowledge-sharing session for the team.
</details>

● **Candidate Introduction:** What is your current location or the location you are looking for?

● **Candidate Introduction:** What is your current notice period?

↳ **Candidate Introduction:** Have you already resigned/submitted your resignation from your current job?

#### 【 OTHER 】

<details>
<summary><strong>● In your current role, which databases have you worked on?</strong></summary>

**Answer:**
From an infrastructure, high-availability, backup/recovery, and performance-tuning perspective, I have worked with:

1. **Relational Databases (RDBMS):**
   - **PostgreSQL & Amazon RDS / Aurora PostgreSQL:** Managing Multi-AZ deployments, read replicas, parameter groups (`max_connections`, `shared_buffers`), automated snapshot lifecycles, and point-in-time recovery (PITR).
   - **MySQL / Amazon RDS MySQL:** Monitoring query performance, slow query logs, connection pooling with ProxySQL / AWS RDS Proxy.

2. **NoSQL Databases:**
   - **Amazon DynamoDB:** Designing on-demand and provisioned capacity scaling, Global Tables for multi-region active-active architectures, and DynamoDB Streams.
   - **MongoDB:** Managing replica sets, sharding architectures, automated backups, and running containerized MongoDB instances in non-prod Kubernetes clusters.

3. **In-Memory Caching & Key-Value Stores:**
   - **Redis / Amazon ElastiCache:** Cluster mode enabled setups, Redis Sentinel for automatic failover, cache-aside architectural patterns, and eviction policy tuning (`allkeys-lru`).
</details>

<details>
<summary><strong>↳ Follow-up: What is the difference between a primary key and a unique key in a database?</strong></summary>

**Answer:**
Both Primary Key and Unique Key enforce entity integrity and uniqueness across table columns, but they have key structural and architectural differences:

| Feature | Primary Key (PK) | Unique Key (UK) |
| :--- | :--- | :--- |
| **Purpose** | Uniquely identifies each record/row in the table. | Prevents duplicate values in specific column(s). |
| **Quantity per Table** | Only **one** Primary Key per table. | A table can have **multiple** Unique Keys. |
| **Nullability** | **Cannot accept NULL values** (strictly `NOT NULL`). | Can accept **NULL** values (allows one NULL in SQL Server/Postgres, multiple in MySQL). |
| **Index Creation** | Automatically creates a **Clustered Index** by default in engines like MySQL InnoDB / SQL Server. | Automatically creates a **Non-Clustered Index** by default. |
| **Modifications** | Rarely modified or updated; critical for foreign key relationships. | Can be modified or updated more easily based on business rules. |
| **Example** | `user_id INT PRIMARY KEY` | `email VARCHAR(255) UNIQUE` |
</details>

<details>
<summary><strong>↳ Follow-up: What is indexing in the context of databases?</strong></summary>

**Answer:**
In databases, an **index** is a specialized data structure (most commonly a **B-Tree** / **B+ Tree**, or a **Hash table**) created on one or more columns of a table to drastically accelerate data retrieval operations without scanning every row in the table (preventing costly Full Table Scans).

**How it Works (Book Index Analogy):**
Without an index, finding a specific user by email in a table with 10 million rows requires inspecting all 10 million rows sequentially ($O(N)$ time complexity). With a B-Tree index on `email`, the database engine navigates the tree nodes by comparing key values, finding the record in logarithmic time ($O(\log N)$), typically requiring only 3–4 disk I/O operations.

**Clustered vs. Non-Clustered Indexes:**
1. **Clustered Index:**
   - Dictates the physical storage order of rows on disk.
   - There can only be **one** clustered index per table (typically the Primary Key).
   - The leaf nodes of a clustered index contain the actual data rows.
2. **Non-Clustered (Secondary) Index:**
   - Stored in a separate structure from the physical table data.
   - Leaf nodes contain the indexed column values and a row locator pointer (the clustered index key or memory address) to locate the full row.
   - Tables can have multiple non-clustered indexes.

**DevOps & Production Trade-Offs:**
- **Read vs. Write Trade-off:** While indexes speed up `SELECT` queries, they slow down `INSERT`, `UPDATE`, and `DELETE` operations because the database must update both the table data and all associated index trees on every write.
- **Storage Overhead:** Indexes consume significant disk space and RAM (buffer pool).
- **Query Optimization:** Used in conjunction with `EXPLAIN ANALYZE` to ensure queries leverage indexes (`Index Scan` / `Index Only Scan`) rather than `Seq Scan`.
</details>

<details>
<summary><strong>↳ Follow-up: What is the difference between the DELETE, DROP, and TRUNCATE commands in SQL?</strong></summary>

**Answer:**
The differences across SQL commands for removing data:

| Feature | `DELETE` | `TRUNCATE` | `DROP` |
| :--- | :--- | :--- | :--- |
| **Command Type** | **DML** (Data Manipulation Language) | **DDL** (Data Definition Language) | **DDL** (Data Definition Language) |
| **Scope of Action** | Removes specific rows based on condition. | Removes **all** rows from the table. | Completely deletes the table structure, data, and metadata. |
| **`WHERE` Clause** | **Supported** (`DELETE FROM t WHERE id=5`). | **Not supported** (operates on entire table). | **Not supported**. |
| **Mechanism** | Scans and deletes rows one by one. | Deallocates data pages directly at storage level. | Removes table definition and deallocates all data pages. |
| **Performance** | **Slowest** (logs each deleted row individually in transaction log). | **Very Fast** (minimal logging of page deallocations). | **Fastest** (instant schema removal). |
| **Rollback / Transaction** | Can be rolled back inside a transaction block (`ROLLBACK`). | Can be rolled back in PostgreSQL/SQL Server; cannot in MySQL. | Can be rolled back in Postgres; cannot in MySQL/Oracle. |
| **Table Structure** | Preserved. | Preserved (resets auto-increment counters). | **Destroyed** (table ceases to exist). |
| **Triggers** | Fires `ON DELETE` triggers. | **Does not fire** `DELETE` triggers. | **Does not fire** triggers; drops them. |
</details>

<details>
<summary><strong>● Do you know what ITIL (IT Infrastructure Library / IT service management framework) is?</strong></summary>

**Answer:**
**ITIL (Information Technology Infrastructure Library)** is a globally recognized, vendor-neutral framework of best practices designed to align IT services with business objectives and manage IT Service Management (ITSM).

**Core Philosophy:**
ITIL provides guidelines for establishing repeatable, predictable, and measurable IT operations, transitioning from ad-hoc firefighting to structured service delivery.

**ITIL 4 Service Value System (SVS):**
In modern DevOps organizations, ITIL 4 aligns with Agile and SRE principles by organizing delivery around the **Service Value Chain**:
1. **Plan:** Strategic architectural planning and governance.
2. **Improve:** Continual improvement loops (measuring KPIs, postmortems).
3. **Engage:** Stakeholder and customer feedback loops.
4. **Design & Transition:** Releasing new services with quality gates and compliance checks.
5. **Obtain / Build:** Infrastructure and software delivery (CI/CD automation).
6. **Deliver & Support:** Day-2 operations, observability, incident and problem resolution.
</details>

<details>
<summary><strong>↳ Follow-up: Do you have any knowledge of ITIL processes such as change management and problem management?</strong></summary>

**Answer:**
Yes, both are vital components of enterprise production stability:

1. **Change Management (Change Enablement in ITIL 4):**
   - **Objective:** Ensure that changes to production infrastructure, pipelines, or application code are introduced smoothly without causing outages, disruptions, or compliance breaches.
   - **Classification of Changes:**
     - **Standard Changes:** Pre-authorized, low-risk, well-documented changes (e.g., standard GitOps release to dev/staging, periodic log rotation). Fully automated via CI/CD pipelines.
     - **Normal Changes:** Moderate-to-high-risk changes requiring formal review, testing proof, rollback strategies, and approval by a **Change Advisory Board (CAB)** (e.g., major database schema migration, Kubernetes version upgrade).
     - **Emergency Changes:** Critical changes required to restore a down production system during a P1 incident or patch an active zero-day vulnerability. Handled via an Emergency CAB (ECAB) with expedited retroactive documentation.
   - **DevOps Integration:** Modern change management is automated—pull requests, automated security scans (SonarQube/Trivy), and automated canary analysis replace manual bureaucracy.

2. **Problem Management:**
   - **Objective:** Prevent recurring incidents and minimize the impact of incidents that cannot be prevented.
   - **Incident vs. Problem:**
     - *Incident Management:* Reactive firefighting—restoring service as fast as possible (e.g. restarting an OOMKilled container).
     - *Problem Management:* Proactive root cause analysis (RCA)—investigating why the container leaked memory in the first place and delivering a permanent fix.
   - **Core Workflow:**
     - Problem Detection -> Problem Prioritization (RCA) -> Workaround Identification (documented in **Known Error Database - KEDB**) -> Permanent Fix (initiating a Change Request) -> Post-Implementation Review.
</details>
</details>
</details>

<details open>
<summary><h2>🏢 Protiviti</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 05-08-2026 08:19 PM*

#### 【 KUBERNETES 】

<details>
<summary><strong>● Do you have experience working with Kubernetes?</strong></summary>

**Answer:**
Yes. I have over 5 years of hands-on experience designing, provisioning, securing, and maintaining production-grade Kubernetes clusters across both cloud-managed environments (primarily **AWS EKS** and **Azure AKS**) and self-managed multi-node setups.

My day-to-day responsibilities include:
- Cluster provisioning via **Terraform** using the official AWS EKS module (`terraform-aws-modules/eks`).
- Implementing GitOps continuous delivery workflows using **Argo CD** and Helm charts.
- Setting up ingress controllers (AWS Load Balancer Controller, NGINX Ingress) and cert-manager for automated TLS certificates.
- Implementing zero-trust cluster networking with **Calico** NetworkPolicies and AWS VPC CNI.
- Hardening clusters using Pod Security Standards, Open Policy Agent (OPA) / Gatekeeper, and role-based access control (RBAC).
- Cluster observability using Prometheus Operator, Grafana, and OpenTelemetry.
</details>

<details>
<summary><strong>↳ Follow-up: What kinds of issues have you troubleshooted in Kubernetes?</strong></summary>

**Answer:**
In high-throughput production environments, I have debugged and resolved issues across all layers of the Kubernetes architecture:

1. **Pod Lifecycle & Scheduling Issues:**
   - **CrashLoopBackOff:** Caused by missing environment variables, failing database migrations, missing secret references, or misconfigured container entrypoints.
   - **OOMKilled (Exit Code 137):** Investigated memory leaks by analyzing JVM heap dumps and cgroup memory limits, then adjusting requests and limits.
   - **Pending Pods:** Debugged scheduling failures caused by insufficient node compute, unsatified node selectors/affinities, or un-tolerated node taints.

2. **Node-Level Outages & Failures:**
   - **Node `NotReady`:** Traced to Kubelet crashes, container runtime (`containerd`) socket freezes, disk pressure on `/var/lib/containerd`, or network partitions disconnecting Kubelet from the API server.

3. **Networking & DNS Anomalies:**
   - **CoreDNS NXDOMAIN Storms & Latency:** Fixed DNS resolution timeouts caused by Linux `ndots:5` lookup behavior by tuning CoreDNS autoscaling and deploying NodeLocal DNSCache.
   - **Pod-to-Pod Communication Failures:** Resolved IP address exhaustion in AWS VPC CNI subnets using secondary CIDR blocks and custom CNI configurations.

4. **Storage & State Issues:**
   - PVC stuck in `Pending` or `Multi-Attach error for volume`: Debugged AWS EBS CSI driver detachment timeouts when moving stateful pods across Availability Zones.
</details>

<details>
<summary><strong>● Suppose you have two Kubernetes nodes and one node needs to be taken down for maintenance. How would you migrate all the pods running on that node to the other working node?</strong></summary>

**Answer:**
Migrating all pods safely without service disruption is achieved through a standard two-step operational workflow: **Cordon** and **Drain**.

1. **Step 1: Cordon the Node (Prevent New Scheduling):**
   ```bash
   kubectl cordon <target-node-name>
   ```
   This marks the node as `SchedulingDisabled`. The scheduler will not place any new pods on this node, but existing running pods remain unaffected.

2. **Step 2: Drain the Node (Gracefully Evict Existing Workloads):**
   ```bash
   kubectl drain <target-node-name> --ignore-daemonsets --delete-emptydir-data --force
   ```
   The drain operation communicates with the Kubernetes Eviction API, honoring each application's **PodDisruptionBudget (PDB)**. The ReplicaSet / Deployment controllers detect the terminating pods and immediately spin up replacement pods on the remaining healthy node.

3. **Step 3: Perform Maintenance:**
   Upgrade the kernel, apply security patches, or restart hardware on the cordoned node.

4. **Step 4: Uncordon the Node (Restore to Active Pool):**
   ```bash
   kubectl uncordon <target-node-name>
   ```
   The node status returns to `Ready`, allowing future pods to be scheduled on it.
</details>

<details>
<summary><strong>↳ Follow-up: Before or after cordoning a node, how do you drain the target node to gracefully evict the existing pods running on it, and what command would you use?</strong></summary>

**Answer:**
**Order of Execution:**
The cordon step **must happen before or at the start of draining**. In fact, running `kubectl drain` automatically cordons the node first as its very first action before issuing eviction requests. However, manually running `kubectl cordon` first is enterprise best practice to immediately halt scheduling while preparing the drain arguments.

**Exact Command:**
```bash
kubectl drain <node-name> \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --grace-period=60 \
  --timeout=5m
```

**Technical Explanation of Flags:**
- `--ignore-daemonsets`: **Mandatory.** DaemonSet pods (e.g. `kube-proxy`, `aws-node`, `datadog-agent`) run on all nodes by design. If you attempt to drain without this flag, `kubectl` will error out and refuse to evict because DaemonSet pods cannot be rescheduled away.
- `--delete-emptydir-data`: **Mandatory if pods use local ephemeral storage.** Pods with `emptyDir` volumes will lose their temporary local data when evicted; this flag confirms you accept local data loss for stateless caches/scratch spaces.
- `--grace-period=60`: Gives application processes 60 seconds to complete in-flight transactions and shut down gracefully after receiving `SIGTERM` before the kernel sends `SIGKILL`.
- `--timeout=5m`: Prevents the command from hanging indefinitely if a misconfigured pod or strict PodDisruptionBudget refuses eviction.
</details>

<details>
<summary><strong>● Can you describe the Kubernetes architecture, specifically what services/components run on the master (control plane) node versus the worker node?</strong></summary>

**Answer:**
Kubernetes follows a master-worker distributed architecture. The **Control Plane (Master)** manages cluster state and orchestration, while **Worker Nodes** execute the containerized application workloads.

```
+-------------------------------------------------------------------------------+
|                             CONTROL PLANE (MASTER)                            |
|                                                                               |
|  +--------------------+    +--------------------+    +---------------------+  |
|  |   kube-apiserver   |<-->|       etcd         |    |   kube-scheduler    |  |
|  +--------------------+    +--------------------+    +---------------------+  |
|            ^                                                                  |
|            |               +--------------------+    +---------------------+  |
|            +-------------->| kube-controller-   |    |  cloud-controller-  |  |
|                            |     manager        |    |      manager        |  |
|                            +--------------------+    +---------------------+  |
+-------------------------------------------------------------------------------+
                                     |
              Network / TLS Communication (Port 6443 / 10250)
                                     v
+-------------------------------------------------------------------------------+
|                                 WORKER NODE                                   |
|                                                                               |
|  +--------------------+    +--------------------+    +---------------------+  |
|  |      kubelet       |    |     kube-proxy     |    |  Container Runtime  |  |
|  |                    |    |   (iptables/IPVS)  |    | (containerd/CRI-O)  |  |
|  +--------------------+    +--------------------+    +---------------------+  |
|            |                                                    |             |
|            +----------------------------------------------------+             |
|                                     |                                         |
|                                     v                                         |
|                       +---------------------------+                           |
|                       | Pod 1 | Pod 2 | Pod 3 ... |                           |
|                       +---------------------------+                           |
+-------------------------------------------------------------------------------+
```

#### 1. Control Plane (Master Node) Components:
- **`kube-apiserver`:** The central nervous system of Kubernetes. Exposes the JSON/REST API over HTTPS, handles authentication, authorization (RBAC), admission control, and writes state directly to `etcd`.
- **`etcd`:** A distributed, highly-available, consistent key-value store (using Raft consensus) that holds the single source of truth for the entire cluster state, configuration, and secrets.
- **`kube-scheduler`:** Inspects newly created, unscheduled pods and selects the optimal worker node based on resource requests, node selectors, taints/tolerations, affinities, and data locality.
- **`kube-controller-manager`:** Runs daemon controllers that continuously regulate actual state toward desired state:
  - *Node Controller:* Detects and responds when nodes go offline.
  - *Deployment / ReplicaSet Controller:* Maintains the desired pod replica count.
  - *EndpointSlice Controller:* Links Services to matching Pod IP endpoints.
  - *ServiceAccount & Token Controllers:* Creates default accounts and API access tokens.
- **`cloud-controller-manager`:** Integrates with underlying cloud APIs (AWS/Azure) to manage cloud-specific resources like Cloud Load Balancers, Route tables, and EBS/Managed Disks.

#### 2. Worker Node Components:
- **`kubelet`:** The primary node agent that registers the node with the API server. Watches for assigned PodSpecs, invokes the Container Runtime Interface (CRI) to start containers, executes liveness/readiness health probes, and reports node status.
- **`kube-proxy`:** Maintains host network rules (using `iptables` or `IPVS`) to implement Kubernetes Service abstractions, routing traffic destined for a ClusterIP/NodePort across healthy backend pods.
- **`Container Runtime` (e.g., `containerd`, CRI-O):** Low-level software responsible for pulling container images, unpacking root filesystems, and executing containers using Linux namespaces and cgroups.
</details>

#### 【 IAC 】

<details>
<summary><strong>● Suppose a customer is on AWS with a midsize environment of around 400-500 VMs, along with RDS, S3, and other AWS services, all of which were deployed manually. They now want to automate everything using Terraform and a CI/CD tool like Jenkins or GitLab, converting the manually deployed infrastructure into automated infrastructure-as-code. How would you approach automating this entire environment?</strong></summary>

**Answer:**
Modernizing a manually deployed 500-VM AWS infrastructure into Infrastructure-as-Code (IaC) requires a phased, risk-mitigated strategy to prevent accidental downtime.

```
Phase 1: Discovery -> Phase 2: Modular Arch -> Phase 3: Automated Reverse-Eng -> Phase 4: Import -> Phase 5: CI/CD Pipeline
```

#### Phase 1: Automated Discovery & Inventory
- Run AWS Config and automated discovery scripts (AWS CLI / Python Boto3) to catalogue all existing assets: VPCs, subnets, route tables, security groups, EC2 instances, EBS volumes, RDS databases, S3 buckets, and IAM roles.
- Establish environment boundaries (Production, Staging, Shared Services).

#### Phase 2: Design Modular Architecture & State Partitioning
- **Crucial Rule:** Never place 500 VMs into a single monolithic state file (doing so causes slow plans, API rate limiting, and catastrophic blast radius).
- Decompose infrastructure into decoupled layers, each with its own independent Terraform state:
  1. `networking/` (VPCs, Subnets, NAT Gateways, Transit Gateway)
  2. `security/` (IAM roles, Security Group baselines, KMS keys)
  3. `storage/` (S3 buckets, EFS filesystems)
  4. `database/` (RDS clusters, parameter groups)
  5. `compute/` (EC2 instances organized by tier/workload)

#### Phase 3: Leverage Reverse Engineering & Generation Tools
- Rather than manually authoring HCL for 500 VMs line-by-line, utilize modern automated generation tools:
  - **Terraform 1.5+ `import` blocks:** Declare target resources and execute `terraform plan -generate-config-out=generated.tf`.
  - **Terraformer (open-source by Google):** Extracts existing AWS resources into modular HCL2 and corresponding `.tfstate` files:
    ```bash
    terraformer import aws --resources=vpc,subnet,ec2,rds --regions=us-east-1
    ```
  - **Former2:** Generates valid, idiomatic HCL from AWS API calls.

#### Phase 4: Reconcile Drift & Validate Plans
- Clean up the generated HCL: parameterize variables, reference outputs, and remove hardcoded values.
- Execute `terraform plan` on each state layer until **zero diffs** are reported (`Plan: 0 to add, 0 to change, 0 to destroy`).

#### Phase 5: CI/CD Pipeline Integration (GitLab CI / Jenkins)
- Commit the validated modules to a version-controlled Git repository.
- Build a multi-stage pipeline:
  1. **Lint & Security Gate:** `terraform fmt -check`, `tflint`, `tfsec` / `checkov`.
  2. **Plan Stage:** Runs `terraform plan -out=tfplan` and publishes the plan output to the Pull Request.
  3. **Approval Gate:** Requires manual peer signoff before production deployment.
  4. **Apply Stage:** Runs `terraform apply tfplan` automatically.
</details>

<details>
<summary><strong>↳ Follow-up: Given that you would need to write Terraform code and import every existing resource individually (VPCs, subnets, IPs, disks, S3 buckets, etc.), wouldn't this be a very time-consuming and hectic task? How would you address that?</strong></summary>

**Answer:**
Yes, if approached naively using the legacy `terraform import <resource> <id>` CLI command one by one, importing hundreds of resources would be tedious, error-prone, and unsustainable.

**Senior Engineering Approach to Accelerate and Automate:**
1. **Automated Reverse-Engineering via `Terraformer`:**
   Instead of writing code manually, we run **Terraformer**. It automatically queries the AWS APIs, writes the HCL resource definitions into modular directories, and generates the exact matching state files in bulk in a matter of minutes.

2. **Bulk Declarative Import Blocks (Terraform 1.5+):**
   We can script the creation of `import` blocks programmatically using a Python script with Boto3. By querying AWS for all instance IDs and generating:
   ```hcl
   import {
     for_each = toset(var.discovered_ec2_ids)
     to       = aws_instance.fleet[each.key]
     id       = each.key
   }
   ```
   Then running `terraform plan -generate-config-out=ec2_generated.tf`, Terraform generates the complete HCL code automatically.

3. **Treat Stateless VMs as Disposable Auto Scaling Groups:**
   For many of the 400-500 VMs, individual instances are identical stateless application servers. Rather than importing 300 individual `aws_instance` resources, we import or provision an **AWS Launch Template** and an **Auto Scaling Group (ASG)**, allowing the fleet to be managed declaratively as a scalable group.

4. **Iterative Layered Rollout:**
   Divide the workload across a 4-week sprint cycle: Week 1 (VPC & Networking), Week 2 (Storage & IAM), Week 3 (RDS Databases), Week 4 (EC2 Compute).
</details>

<details>
<summary><strong>↳ Follow-up: Since the VPCs, subnets, and other resources already exist because they were deployed manually, is there a better way to import this existing manually-deployed environment into Terraform state?</strong></summary>

**Answer:**
Yes. The modern, best-in-class approach relies on **Terraform 1.5+ Native Code Generation** combined with **Terraformer**:

1. **Terraform 1.5+ Declarative Code Generation:**
   In older versions, you had to write the empty resource HCL first before importing. In modern Terraform, you write an `import` block without any corresponding resource code:
   ```hcl
   import {
     to = aws_vpc.existing_vpc
     id = "vpc-0123456789abcdef0"
   }
   ```
   Then run:
   ```bash
   terraform plan -generate-config-out=vpc_generated.tf
   ```
   Terraform queries the AWS provider API, inspects all attributes (CIDR, DNS hostnames, tags), and automatically writes the full resource configuration into `vpc_generated.tf`.

2. **Google's Terraformer CLI:**
   For comprehensive multi-resource environments, Terraformer imports entire dependency graphs in a single command:
   ```bash
   terraformer import aws --resources=vpc,subnet,igw,route_table,security_group \
     --connect=true \
     --regions=us-east-1
   ```
   It automatically maps cross-resource dependencies (e.g. referencing `aws_vpc.existing_vpc.id` inside `aws_subnet` instead of hardcoding the raw VPC ID).
</details>

<details>
<summary><strong>↳ Follow-up: When using Terraform import to bring existing manually-created resources under Terraform management, do you have to import each resource one by one?</strong></summary>

**Answer:**
**Historically (Pre-Terraform 1.5):** Yes. The legacy CLI command `terraform import <resource_address> <id>` required running commands individually, one resource at a time.

**Modern Terraform (Terraform 1.5 and Later):** **No.**
You can perform bulk imports declaratively:
1. **Multiple `import` blocks in a single file:** You can define dozens or hundreds of `import` blocks in `.tf` files and execute them all concurrently in a single `terraform apply` run.
2. **Dynamic Loops with `for_each` inside `import` blocks:**
   ```hcl
   locals {
     s3_buckets = ["company-logs-prod", "company-assets-prod", "company-backups-prod"]
   }

   import {
     for_each = toset(local.s3_buckets)
     to       = aws_s3_bucket.imported_buckets[each.key]
     id       = each.key
   }
   ```
   A single execution of `terraform apply` imports all buckets simultaneously into state.
</details>

<details>
<summary><strong>↳ Follow-up: Where do you store the Terraform state files?</strong></summary>

**Answer:**
In enterprise production, Terraform state files are **never stored locally** or committed to Git (which exposes plaintext secrets). They are stored in an **encrypted remote backend**.

For AWS environments, the industry standard is **Amazon S3** with the following security and resilience baseline:
1. **Server-Side Encryption (SSE):** Enforce AES-256 or AWS KMS customer-managed keys (`aws:kms`) to encrypt state at rest.
2. **S3 Bucket Versioning:** **Mandatory.** Protects against state corruption by keeping an immutable history of every state revision, enabling instant rollback if a corrupted state is applied.
3. **Strict Bucket Policies & Public Access Block:** Block all public access; enforce TLS/HTTPS in transit (`aws:SecureTransport: "true"`); restrict write access exclusively to the CI/CD pipeline execution IAM role.
4. **MFA Delete & Object Lock:** Optional protection preventing accidental bucket deletion.
</details>

<details>
<summary><strong>↳ Follow-up: How is the Terraform state file locked to prevent concurrent modifications?</strong></summary>

**Answer:**
State locking prevents race conditions and state corruption when two engineers or parallel CI/CD pipeline runs attempt to run `terraform apply` at the same time.

1. **How it works:**
   When an operation (`plan` or `apply`) starts, Terraform writes a lock record containing an ID, the operator's username, hostname, and timestamp. Any competing process attempting to run simultaneously detects the lock and terminates with an error: `Error: Error acquiring the state lock`. Once the operation completes, Terraform automatically releases the lock.

2. **Implementation mechanisms:**
   - **Amazon DynamoDB (Standard):** Configured in the backend block with a DynamoDB table having a primary partition key named `LockID` (String type).
   - **Emergency Manual Unlock:** If a CI/CD runner crashes or network drops while holding a lock:
     ```bash
     terraform force-unlock <LOCK-ID>
     ```
</details>

<details>
<summary><strong>↳ Follow-up: Isn't DynamoDB for Terraform state locking deprecated now, with Terraform using native S3 state locking instead?</strong></summary>

**Answer:**
**Accurate Senior Clarification:**
- **Native S3 Locking is New, not a Deprecation of DynamoDB:** Starting in **Terraform v1.10** (released late 2024), HashiCorp added **native state locking directly in the Amazon S3 backend** using Amazon S3's strong read-after-write consistency and conditional writes (`PutObject` with `If-None-Match: *`).
- To use native S3 locking without DynamoDB in Terraform 1.10+:
  ```hcl
  terraform {
    backend "s3" {
      bucket       = "my-terraform-state-prod"
      key          = "prod/vpc/terraform.tfstate"
      region       = "us-east-1"
      use_lockfile = true # Enables native S3 locking
    }
  }
  ```
- **Status of DynamoDB:** DynamoDB locking is **NOT deprecated**. It remains fully supported for backward compatibility and is still actively used across thousands of existing enterprise codebases. However, for greenfield projects on Terraform 1.10+, native S3 locking (`use_lockfile = true`) is the recommended architectural pattern as it eliminates the need to provision and pay for a separate DynamoDB table.
</details>

<details>
<summary><strong>● What is the purpose of the tfvars file in Terraform?</strong></summary>

**Answer:**
The primary purpose of a `.tfvars` file (such as `terraform.tfvars` or `<environment>.tfvars`) is to **separate generic infrastructure code from specific environment configuration values**.

**Key Principles:**
1. **Decoupling Logic from Data:** `main.tf` defines *what* infrastructure to build (e.g. an EC2 instance), `variables.tf` defines the *contract* (variable names, types, descriptions), and `.tfvars` provides the *concrete values* (e.g. `instance_type = "t3.large"`).
2. **Preventing Hardcoding:** Allows the exact same Terraform module code to deploy `dev`, `qa`, and `prod` simply by supplying different `.tfvars` files.
3. **Variable Precedence:** Terraform loads variables in a strict hierarchy (from lowest to highest precedence):
   - Default values in `variables.tf`
   - Environment variables (`TF_VAR_<var_name>`)
   - `terraform.tfvars`
   - `terraform.tfvars.json`
   - `*.auto.tfvars` (alphabetical order)
   - CLI flags (`-var` or `-var-file`)
</details>

<details>
<summary><strong>↳ Follow-up: If you have three environments (prod, dev, QA) each with its own tfvars file (prod.tfvars, dev.tfvars, qa.tfvars), how would you configure Terraform so that running 'terraform apply' automatically picks up the correct tfvars file for the target environment (e.g., prod.tfvars) without explicitly specifying it on the command line?</strong></summary>

**Answer:**
There are several senior architectural patterns to achieve automatic `.tfvars` selection without typing `-var-file=prod.tfvars`:

#### Pattern 1: Directory-per-Environment Structure (Enterprise Recommended)
Organize the repository so each environment has its own root module:
```
environments/
├── dev/
│   ├── main.tf (calls ../../modules/app)
│   └── terraform.tfvars (contains dev values)
├── qa/
│   ├── main.tf
│   └── terraform.tfvars (contains qa values)
└── prod/
    ├── main.tf
    └── terraform.tfvars (contains prod values)
```
When an engineer or pipeline executes `cd environments/prod && terraform apply`, Terraform **automatically loads `terraform.tfvars` by default** without any CLI flags.

#### Pattern 2: Symlinking `<workspace>.auto.tfvars`
Terraform automatically loads any file ending in `.auto.tfvars`. If using Terraform Workspaces:
Create symlinks or a pipeline step:
```bash
ln -sf ${ENV}.tfvars ${ENV}.auto.tfvars
terraform apply
```

#### Pattern 3: Using Environment Variable `TF_CLI_ARGS`
Export the environment variable in the shell or CI/CD runner:
```bash
export TF_CLI_ARGS_apply="-var-file=prod.tfvars"
export TF_CLI_ARGS_plan="-var-file=prod.tfvars"
terraform apply
```

#### Pattern 4: Terragrunt
Using Terragrunt (`terragrunt.hcl`) which automatically imports inputs from parent and environment-specific `env.hcl` files based on the directory path.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>↳ Follow-up: Is your experience primarily on AWS, or do you also have experience with Azure?</strong></summary>

**Answer:**
My primary expertise is in **Amazon Web Services (AWS)**, where I have deep hands-on architectural experience managing production workloads across EKS, EC2, VPC, RDS, S3, IAM, CloudFront, Route53, and KMS.

However, I also possess strong working knowledge of **Microsoft Azure**:
- Designing and provisioning **Azure Kubernetes Service (AKS)** clusters with Azure CNI and Managed Identities.
- Core networking in Azure: Virtual Networks (VNets), Subnets, Network Security Groups (NSGs), and VNet Peering.
- Storage and Databases: Azure Blob Storage, Azure SQL Database.
- Identity & Governance: Microsoft Entra ID (formerly Azure AD), Azure RBAC, and Azure Monitor / Log Analytics Workspaces.
</details>

<details>
<summary><strong>● Apart from Kubernetes, have you managed AWS infrastructure directly, such as server patching?</strong></summary>

**Answer:**
Yes. Outside of containerized environments, I have managed large fleets of standalone Linux and Windows EC2 instances, with direct ownership over automated patching and vulnerability remediation.

**Two Primary Approaches I Implemented:**

1. **In-Place Patching via AWS Systems Manager (SSM) Patch Manager:**
   - **Patch Baselines:** Configured custom patch baselines specifying approval rules (e.g. automatically approve Critical and Security patches 7 days after vendor release to ensure stability).
   - **Maintenance Windows:** Scheduled automated maintenance windows using SSM Maintenance Windows during off-peak hours (e.g. Sunday 2 AM).
   - **SSM Run Command & Patch Groups:** Tagged instances with `PatchGroup = WebFleet-Prod` and targeted them without requiring SSH or bastion hosts.
   - **Reporting:** Sent compliance reports to AWS Security Hub and S3.

2. **Immutable Infrastructure via Golden AMI Pipeline (Cloud-Native Best Practice):**
   - For auto-scaled fleets, we avoided in-place patching entirely.
   - Built a CI pipeline using **HashiCorp Packer** and **Ansible** that builds a hardened, patched AMI monthly.
   - Triggered an **EC2 Auto Scaling Instance Refresh** (`aws autoscaling start-instance-refresh`) to rolling-replace instances with zero downtime.
</details>

<details>
<summary><strong>● Have you performed any cloud cost assessments, such as a FinOps assessment?</strong></summary>

**Answer:**
Yes. I have led FinOps and cost optimization assessments using the standard FinOps Foundation framework: **Inform -> Optimize -> Operate**.

**Key Tools & Metrics Utilized:**
- **AWS Cost Explorer & AWS Budgets:** Tracking monthly spend by service, cost allocation tags (`Environment`, `Owner`, `Application`), and forecasting runway.
- **AWS Compute Optimizer:** Identifying over-provisioned compute and memory instances.
- **Infracost:** Integrated into GitHub Actions / GitLab CI pipelines to display estimated cost impact on Pull Requests before Terraform merges.
- **Kubecost:** Allocating Kubernetes pod and namespace-level infrastructure costs in shared clusters.

**Key Outcomes Delivered:**
- 25–35% overall reduction in cloud bill through unattached EBS cleanup, Graviton migrations, S3 lifecycle transitions, and strategic Compute Savings Plans.
</details>

<details>
<summary><strong>↳ Follow-up: If a customer asked you to perform a cost assessment to review whether their EC2 instances are right-sized and to check if they are overspending on cloud, what would be your approach to performing this assessment?</strong></summary>

**Answer:**
I would execute a structured 5-step diagnostic assessment:

1. **Step 1: Verify Telemetry & Enable Memory Metrics:**
   - Default AWS CloudWatch metrics **only report CPU, disk, and network**—they do *not* report memory utilization.
   - Ensure the **Amazon CloudWatch Agent** is installed on all instances to collect RAM metrics (`mem_used_percent`) over a 30–90 day evaluation window to capture month-end and peak usage.

2. **Step 2: Run AWS Compute Optimizer:**
   - Review Compute Optimizer ML findings for instances flagged as *Over-provisioned*.
   - Filter for instances with average CPU < 20% and peak memory < 40%.

3. **Step 3: Analyze Instance Generation & Architecture:**
   - Identify older generation instances (e.g. `m4`, `c4`, `m5`) and evaluate upgrades to modern **AWS Graviton** (`m7g`, `c7g`), which provide up to 20% lower cost and 19% better performance.

4. **Step 4: Identify Idle & Orphaned Assets:**
   - Unattached EBS volumes in `available` state.
   - Obsolete EBS snapshots older than 90 days.
   - Idle Elastic IPs and empty Application Load Balancers.

5. **Step 5: Present an Actionable FinOps Report:**
   - Group recommendations into **Low Risk** (Dev/QA right-sizing, stopping instances on weekends), **Medium Risk** (Stateless web tiers in ASGs), and **High Risk** (Production databases).
   - Project ROI: Calculate monthly cost savings vs required engineering effort.
</details>

<details>
<summary><strong>↳ Follow-up: In the context of cost optimization for S3 storage, how would you identify which data needs to be moved to a different storage tier?</strong></summary>

**Answer:**
To identify candidate data for storage tiering, I use a combination of three AWS native analytics tools:

1. **S3 Storage Class Analysis (SCA):**
   - Configured on bucket or prefix level to observe data access patterns over a 30-to-60-day window.
   - Generates graphs showing how much storage is accessed frequently vs. infrequently, recommending when to transition objects from S3 Standard to S3 Standard-IA.

2. **S3 Storage Lens:**
   - Provides organization-wide dashboards displaying metrics on:
     - Percentage of storage in Standard vs. Infrequent Access vs. Glacier.
     - Incomplete Multipart Uploads (which silently consume gigabytes of billable storage).
     - Non-current object versions accumulating in version-enabled buckets.

3. **Amazon Athena Queries on S3 Inventory:**
   - Generate daily S3 Inventory CSV reports and query them using Athena to pinpoint specific file extensions (e.g. `.log`, `.tar.gz`, `.csv`) that have not been modified or accessed in >90 days.
</details>

<details>
<summary><strong>↳ Follow-up: What S3 lifecycle policy would you apply to move infrequently used data to lower-cost storage tiers?</strong></summary>

**Answer:**
Here is a production-grade Terraform configuration for an S3 lifecycle policy implementing multi-tier archiving:

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "data_tiering" {
  bucket = aws_s3_bucket.app_data.id

  rule {
    id     = "auto-tier-and-archive"
    status = "Enabled"

    filter {
      prefix = "logs/"
    }

    # Move to Standard-Infrequent Access after 30 days
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Move to Glacier Instant Retrieval after 90 days (low cost, ms retrieval)
    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }

    # Move to Glacier Deep Archive after 180 days (lowest cost: ~$0.00099/GB)
    transition {
      days          = 180
      storage_class = "DEEP_ARCHIVE"
    }

    # Permanently delete expired data after 365 days
    expiration {
      days = 365
    }

    # Clean up non-current versions after 30 days
    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    # Abort abandoned multipart uploads after 7 days
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}
```
*Note: For unpredictable access patterns, we enable **S3 Intelligent-Tiering** without transition rules, which automatically moves objects between frequent, infrequent, and archive tiers without retrieval fees.*
</details>

<details>
<summary><strong>↳ Follow-up: In terms of cost optimization, how would you optimize the VMs (EC2 instances) in this environment?</strong></summary>

**Answer:**
A 5-pronged strategy to optimize a fleet of 400–500 EC2 instances:

1. **Right-Sizing Compute & Memory:** Downsize underutilized instances based on p95 metrics (e.g. `m5.2xlarge` -> `m5.xlarge`).
2. **Architecture Modernization (AWS Graviton):** Migrate compatible Linux workloads (Python, Java, Node.js, Go) to ARM64 Graviton3 (`m7g`, `c7g`, `t4g`) for an immediate 20% price reduction.
3. **Automated Scheduling for Non-Production:** Implement **AWS Instance Scheduler** or EventBridge + Lambda to stop Dev and QA instances outside business hours (7 PM to 7 AM on weekdays, all weekend), saving ~65% on non-prod compute.
4. **Leverage Spot Instances:** Use EC2 Spot instances (up to 90% discount) for stateless, fault-tolerant workloads like CI/CD build agents, batch processing, and asynchronous worker pools.
5. **Commitment Discounts (Savings Plans):** After right-sizing, purchase 1-year or 3-year **Compute Savings Plans** (flexible across EC2, Fargate, Lambda) for steady-state baseline usage, securing up to 66% savings compared to On-Demand rates.
</details>

<details>
<summary><strong>↳ Follow-up: If AWS's recommendation tool identified around 50 EC2 instances that could be right-sized due to less than 20% CPU and memory utilization, what would be your next step? Would you right-size them immediately?</strong></summary>

**Answer:**
**Direct Answer:** **NO. I would definitely NOT right-size them immediately.**

Right-sizing based solely on an automated recommendation without contextual validation introduces high operational risk.

**Mandatory Next Steps:**
1. **Analyze Workload Profile & Periodicity:**
   - Check if the low utilization is because the instance handles periodic, bursty, or batch workloads (e.g., month-end financial processing, daily ETL jobs running at midnight, or seasonal traffic spikes).
2. **Verify Memory Telemetry:**
   - Confirm whether CloudWatch Agent was actively reporting Memory metrics. If only CPU was measured, down-sizing could trigger catastrophic Out-Of-Memory (`OOMKilled`) panics.
3. **Engage Application Owners:**
   - Review findings with service owners to confirm requirements (e.g. vendor software requirements, minimum thread pools, multi-threaded caching).
4. **Test in Lower Environments:**
   - Apply the recommended size to the Dev or QA replica of the workload, run automated performance/load tests, and monitor latency SLAs.
5. **Schedule Maintenance Window for Production:**
   - Changing EC2 instance type requires an instance `stop` and `start` (incurring several minutes of downtime for standalone VMs). Schedule during approved change windows with an immediate rollback plan.
</details>

<details>
<summary><strong>↳ Follow-up: Given the AWS right-sizing recommendations for those 50 underutilized EC2 instances, what would you recommend to the customer?</strong></summary>

**Answer:**
I would present a phased, risk-categorized recommendation plan:

1. **Phase 1: Quick Wins (Non-Production / Dev Environments):**
   - Resize all non-production instances immediately. Lowest risk, immediate cost reduction.
2. **Phase 2: Stateless Production Fleets behind Load Balancers:**
   - Update Launch Templates to the smaller instance size and perform a rolling instance refresh through the Auto Scaling Group (zero downtime).
3. **Phase 3: Stateful / Critical Production Instances (Databases, Legacy Apps):**
   - Schedule maintenance windows. Take an EBS AMI snapshot prior to downsizing as a fallback.
4. **Phase 4: Architectural Improvements:**
   - Transition static EC2 instances to Auto Scaling Groups so they automatically scale up during peak demand and scale down during troughs.
5. **Projected Financial Impact:** Provide a clear breakdown showing monthly On-Demand savings vs potential Savings Plan commitment.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you give a brief introduction about yourself and what you are currently doing in your role?
</details>
</details>

<details open>
<summary><h2>🏢 LTTS</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 05-08-2026 08:49 PM*

#### 【 MONITORING 】

<details>
<summary><strong>● How do you set up and configure monitoring for a hybrid environment that connects on-premises infrastructure to an Azure data center?</strong></summary>

**Answer:**
Monitoring a hybrid environment spanning on-premises data centers and Microsoft Azure requires a unified observability control plane using **Azure Arc**, **Azure Monitor Agent (AMA)**, and **Log Analytics Workspaces**:

```
[ On-Prem Data Center ]                                  [ Azure Cloud ]
+-------------------------+                              +-------------------------------+
| Bare-metal / VMware VMs |                              | Log Analytics Workspace (LAW) |
|   - Azure Monitor Agent |                              |   - Centralized Telemetry     |
|   - Azure Arc Connected |                              +-------------------------------+
+-------------------------+                                              ^
             | (Port 443 HTTPS via Arc / Log Analytics Gateway)          |
             v                                                           v
  [ ExpressRoute / VPN ] =====================================> [ Azure Monitor ]
                                                                 - Alerts & Action Groups
                                                                 - Azure Workbooks Dashboard
```

1. **Hybrid Connectivity & Gateway Architecture:**
   - Establish reliable network connectivity between on-premises and Azure via **Azure ExpressRoute** or a redundant **Site-to-Site IPSec VPN**.
   - If on-premises servers lack direct outbound internet access, deploy an **Azure Log Analytics Gateway** (forward proxy) on-prem so all agents forward telemetry through a single secure egress point on port 443.

2. **Server Onboarding via Azure Arc:**
   - Register on-premises physical and virtual servers (Windows and Linux) into **Azure Arc-enabled servers**.
   - This projects on-premises machines as native Azure Resource Manager (ARM) resources, allowing unified policy enforcement and role-based access control.

3. **Telemetry Collection via Azure Monitor Agent (AMA):**
   - Deploy the modern **Azure Monitor Agent (AMA)** across both Azure VMs and on-prem Arc-enabled servers.
   - Configure **Data Collection Rules (DCRs)** to centrally define *what* data to collect (performance counters, Syslog facilities, Windows Event Logs) and route it to a centralized **Log Analytics Workspace**.

4. **Network & Interconnect Health Monitoring:**
   - Deploy **Network Watcher Connection Monitor** to continuously probe latency, packet loss, and jitter between on-premises subnets and Azure Virtual Networks across the ExpressRoute circuit.
   - Configure alerts for BGP route flapping or circuit saturation.

5. **Unified Dashboards & Alerting:**
   - Build **Azure Workbooks** or connect an enterprise **Grafana** instance via the Azure Monitor data source plugin to visualize hybrid infrastructure side by side.
</details>

<details>
<summary><strong>● Suppose your application shows a latency of 5 (seconds), but CPU and memory metrics look normal. How would you perform root cause analysis (RCA) to identify the source of this latency issue?</strong></summary>

**Answer:**
When an application experiences high latency (5 seconds) while infrastructure CPU and memory metrics remain comfortably low, the bottleneck is almost always caused by **blocking I/O, lock contention, external network waits, or connection pool starvation**.

```
[ Incoming Request ]
        |
        v
[ Thread Pool ] ---> (Thread Starvation? Waiting for DB connection?)
        |
        v
[ External API Call ] ---> (Downstream third-party timeout / DNS retry?)
        |
        v
[ Database Query ] ---> (Row lock / Table lock? Missing index with lock?)
```

**Diagnostic Methodology:**

1. **Step 1: Inspect Distributed Traces (APM / OpenTelemetry):**
   - Query Application Performance Monitoring (APM) tools (e.g. Azure Application Insights, Datadog, or Jaeger).
   - Trace the 5-second transaction to locate the exact **span** responsible:
     - Is 4.8 seconds spent inside a database query?
     - Is it waiting on an outbound third-party HTTP API call?
     - Is it waiting in the web server thread queue before processing begins?

2. **Step 2: Database Lock Contention & Connection Pool Depletion:**
   - **Connection Pool Starvation:** If the application's connection pool (e.g. HikariCP) is capped at 20 connections and all 20 are busy, incoming requests block waiting for an available connection without utilizing any CPU.
   - **Row / Table Locks:** In PostgreSQL/MySQL, check `pg_locks` or `information_schema.innodb_locks`. A lightweight `UPDATE` query will stall indefinitely with zero CPU usage if another uncommitted transaction holds an exclusive lock on that row.

3. **Step 3: External Downstream Dependencies & Timeouts:**
   - A 5-second latency is a classic signature of a **5000ms default HTTP client timeout**!
   - Check if the application calls an external microservice, payment gateway, or email provider that is silently timing out.

4. **Step 4: JVM Thread Dumps & Garbage Collection:**
   - Take a thread dump: `jstack <PID> > threaddump.txt`.
   - Look for threads in `BLOCKED` or `TIMED_WAITING` state waiting on synchronized monitors or resource locks.
   - Check GC pause logs: Long "Stop-The-World" pauses freeze execution while CPU shows normal average usage.

5. **Step 5: Network & DNS Latency:**
   - Check DNS resolution latency: In Kubernetes, improper `ndots:5` configurations cause 4 sequential NXDOMAIN queries before resolving, adding significant latency.
   - Check for TCP socket backlog or SYN retransmissions (`netstat -s | grep retransmitted`).
</details>

<details>
<summary><strong>● How do you scale Azure Monitor to handle large environments?</strong></summary>

**Answer:**
Scaling Azure Monitor across enterprise footprints with thousands of VMs, AKS clusters, and microservices requires architectural partitioning, ingestion filtering, and cost governance:

1. **Workspace Architecture & Segmentation:**
   - Avoid a single monolithic Log Analytics Workspace across the entire enterprise (which risks hitting Azure ingestion rate limits of 1 GB/s per workspace).
   - Adopt a hub-and-spoke workspace topology:
     - **Central Security Workspace:** Dedicated to Microsoft Sentinel and security audit logs.
     - **Regional / Environment Workspaces:** Split by environment (`Prod` vs `Non-Prod`) and geographic regions (`East US`, `West Europe`) to reduce egress bandwidth and ensure data residency compliance.

2. **Optimize Data Collection via Data Collection Rules (DCR):**
   - Move away from legacy Log Analytics agents to the **Azure Monitor Agent (AMA)**.
   - DCRs allow granular filtering at the source agent:
     - Filter out high-frequency debug and informational syslog facilities.
     - Apply **KQL Transformations directly inside the DCR** to drop noisy columns or filter out health-check endpoints before ingestion occurs.

3. **Adopt Ingestion Data Plans (Analytics vs. Basic Logs):**
   - High-value application logs -> **Analytics Logs** (full KQL query capability, 30–730 day retention, alerting support).
   - High-volume, low-value telemetry (firewall raw logs, container stdout/stderr, NetFlow) -> **Basic Logs** (costs ~80% less per GB, ideal for quick debugging queries).

4. **Capacity Reservation Tiers:**
   - Switch from standard Pay-As-You-Go ($2.30/GB) to **Capacity Reservation tiers** (starting at 100 GB/day up to 5,000 GB/day), providing discounts of 15% to 35% with guaranteed ingestion capacity.

5. **Azure Managed Prometheus for Metrics at Scale:**
   - For Kubernetes clusters, offload high-cardinality time-series metrics from Azure Monitor Logs to **Azure Monitor Managed Service for Prometheus**, which scales horizontally to tens of millions of active time series.
</details>

<details>
<summary><strong>↳ Follow-up: In the context of Azure Monitor, what is an action rule?</strong></summary>

**Answer:**
In Azure Monitor, **Action Rules** (now officially designated as **Alert Processing Rules**) are rules that allow you to modify or apply logic to fired alerts *before* notifications are sent out.

**Key Capabilities & Production Use Cases:**

1. **Alert Suppression during Maintenance Windows:**
   - When patching VMs or performing scheduled database maintenance on weekends, alerts normally fire and page on-call engineers.
   - An Alert Processing Rule configured with a schedule (e.g., Saturday 2 AM to 4 AM) **suppresses notifications** for the target Resource Group or VMs without needing to disable the underlying alert rules.

2. **Dynamic Action Group Assignment at Scale:**
   - Instead of manually attaching notification groups (Action Groups) to hundreds of individual alert rules, an Alert Processing Rule can automatically attach an Action Group (e.g. `P1-PagerDuty-Escalation`) to all alerts originating from resources with the tag `Environment: Production`.

3. **Filtering and Routing:**
   - Add conditions based on alert severity, monitor condition, or resource type to route specific alerts to specialized teams (e.g. route all Storage alerts to `#storage-ops`).
</details>

<details>
<summary><strong>● In the case of a VM CPU spike, how would you monitor and configure alerts for high CPU usage?</strong></summary>

**Answer:**
Configuring enterprise CPU monitoring and alerting in Azure involves metric collection, threshold configuration, and automated remediation:

1. **Metric Collection & Aggregation:**
   - Ensure Azure Monitor Agent (AMA) collects the `Percentage CPU` metric from the VM host hypervisor and guest OS.

2. **Alert Rule Configuration (Azure CLI / ARM / Terraform):**
   - **Target Scope:** Target the VM, VM Scale Set (VMSS), or entire Resource Group.
   - **Signal:** `Percentage CPU`.
   - **Threshold Operator:** `Greater than 80%`.
   - **Aggregation Type:** `Average`.
   - **Window Size (Period):** `5 minutes` (evaluates average CPU over a 5-minute rolling window).
   - **Evaluation Frequency:** `1 minute`.
   - *Why 5 minutes?* Prevents alert flapping caused by transient 10-second spikes (e.g., cron jobs starting).

3. **Dynamic Thresholds (Machine Learning Baseline):**
   - For workloads with cyclical traffic (high by day, low by night), configure **Dynamic Thresholds**. Azure Monitor uses historical machine learning models to detect CPU spikes that deviate from expected seasonal patterns.

4. **Action Group & Automated Remediation:**
   - Route the alert to an **Action Group**:
     - Sends immediate Slack / PagerDuty notification.
     - Triggers an **Azure Automation Runbook** or **Azure Function** via Webhook that connects to the VM, executes `top -b -n 1 | head -20`, and captures the rogue process name for post-incident RCA.
</details>

<details>
<summary><strong>● Suppose you are facing a storage cost issue where log ingestion and metric retention costs have skyrocketed. What steps would you take to address this?</strong></summary>

**Answer:**
To rapidly remediate skyrocketing Log Analytics and monitoring costs, I execute a structured 5-phase FinOps optimization playbook:

```
Step 1: Identify Ingestion Culprits -> Step 2: Filter at Source -> Step 3: Shift to Basic Logs -> Step 4: Shorten Retention -> Step 5: Capacity Reservation
```

1. **Step 1: Identify the Top Ingestion Tables (Run Diagnostic KQL):**
   ```kql
   Usage
   | where TimeGenerated > ago(30d)
   | where DataType has "Quantity"
   | summarize TotalGB = sum(Quantity) / 1024 by DataType
   | sort by TotalGB desc
   ```
   Typically, 80% of volume comes from 3 tables: `ContainerLog`, `AzureDiagnostics`, or `W3CIISLog`.

2. **Step 2: Filter Telemetry at the Source (DCR Ingestion Transformations):**
   - Configure Data Collection Rules to filter out logs before ingestion:
     ```kql
     source
     | where LogLevel !in ("DEBUG", "INFO")
     | where RequestPath !has "/healthz"
     ```
   - Dropping health-check logs and debug messages immediately slashes 40–60% of volume.

3. **Step 3: Move High-Volume Tables to the "Basic Logs" Tier:**
   - Change table plan from **Analytics** to **Basic**:
     ```bash
     az monitor log-analytics workspace table update \
       --resource-group rg-monitoring \
       --workspace-name law-prod \
       --name ContainerLogV2 \
       --plan Basic
     ```
   - Basic Logs cost ~$0.50/GB compared to ~$2.30/GB for Analytics Logs.

4. **Step 4: Reduce Interactive Retention & Enable Data Archiving:**
   - Reduce active workspace retention from 365 days to **30 or 90 days**.
   - Move older logs to the **Archive Tier** ($0.02/GB/month) or export to **Azure Data Lake / Blob Storage** via Log Analytics Data Export rules for low-cost compliance storage.

5. **Step 5: Commit to Capacity Reservations:**
   - If steady-state ingestion exceeds 100 GB/day, purchase a **Log Analytics Capacity Reservation** tier for 15–30% guaranteed savings.
</details>

<details>
<summary><strong>● Do you have any knowledge of the OpenTelemetry (OTel) framework?</strong></summary>

**Answer:**
Yes. **OpenTelemetry (OTel)** is an open-source, vendor-neutral observability framework under the Cloud Native Computing Foundation (CNCF) created by merging OpenTracing and OpenCensus. It has become the global industry standard for generating, collecting, processing, and exporting telemetry data (**Metrics, Logs, and Traces**).

```
+-----------------------------------------------------------------------------------+
| APPLICATION LAYER                                                                 |
| [ Java App / Python App / Go App ] --(OpenTelemetry SDK / Auto-Instrumentation)   |
+-----------------------------------------------------------------------------------+
                                          | (OTLP Protocol: gRPC / HTTP on port 4317/4318)
                                          v
+-----------------------------------------------------------------------------------+
| OPENTELEMETRY COLLECTOR PIPELINE                                                  |
|                                                                                   |
|  [ RECEIVERS ]           [ PROCESSORS ]                    [ EXPORTERS ]          |
|  - OTLP                  - batch                           - OTLP (To Datadog)    |
|  - Prometheus            - memory_limiter                  - Prometheus (Metrics) |
|  - Jaeger / Zipkin       - transform (redact PII / tokens) - Tempo / Jaeger       |
+-----------------------------------------------------------------------------------+
```

**Core Components of OpenTelemetry:**
1. **API:** Defines the abstract instrumentation contract in application code (creating spans, metric counters). Decoupled from any implementation.
2. **SDK:** The language-specific implementation (Python, Java, Go, Node.js) that implements the API, handles memory buffering, tail-based sampling, and serialization.
3. **OpenTelemetry Collector (Vendor-Agnostic Proxy):**
   - Deployed as a sidecar, DaemonSet, or centralized gateway.
   - Built on three composable pipeline stages:
     - **Receivers:** Ingest telemetry via OTLP (ports 4317 gRPC, 4318 HTTP), Prometheus, or Kafka.
     - **Processors:** Batch telemetry, drop PII (tokens/passwords), apply sampling rules (e.g. keep only 10% of successful 200 HTTP traces, keep 100% of 5xx errors).
     - **Exporters:** Fan out telemetry to multiple backends simultaneously (e.g. send traces to Grafana Tempo, metrics to Prometheus, and logs to Azure Monitor).

**Why OTel is Essential for Senior DevOps Engineers:**
- **Zero Vendor Lock-in:** Migrating from Datadog to Dynatrace or open-source Grafana requires editing just one line in the Collector YAML config—application code remains untouched!
</details>

#### 【 SECURITY 】

<details>
<summary><strong>● Suppose you have configured monitoring tools like Kibana or Grafana such that different teams can view the data, but only the SRE team can edit it. How would you configure this access control setup?</strong></summary>

**Answer:**
Implementing strict Role-Based Access Control (RBAC) across monitoring tools ensures developers and QA can self-service view logs and dashboards without risking accidental deletions or configuration drift.

#### 1. In Grafana:
- **Identity Provider (IdP) Integration:** Connect Grafana to corporate Single Sign-On (Azure AD / Okta / Keycloak) via OAuth2/SAML.
- **Role Mapping via SAML / OIDC Claims:**
  - Map the IdP security group `SG-SRE-Engineers` to the Grafana **Admin** or **Editor** role.
  - Map `SG-Developers` and `SG-QA` to the Grafana **Viewer** role.
- **Folder-Level Access Controls:**
  - Organize dashboards into folders: `Production Core`, `Billing`, `Developer Microservices`.
  - Set folder permissions: Grant `View` access to `All Users`, and restrict `Edit` access strictly to the `SRE Team` role.
- **Data Source Locking:** Configure data sources (Prometheus, CloudWatch) as read-only and lock down data source modification permissions to Organization Admins only.

#### 2. In Kibana (Elasticsearch Security / OpenSearch):
- **Role Definition:**
  - Create `developer_read_role`:
    - **Kibana Spaces:** Grant `Read` privileges on the `Production` space (allows viewing Discover, Dashboards, and Visualizations, but disables saving or deleting).
    - **Index Privileges:** Grant `read` and `view_index_metadata` on indices `app-logs-*`.
  - Create `sre_admin_role`:
    - Grant `All` privileges on all Kibana spaces, plus `manage_index_templates`, `manage_pipeline`, and index curation permissions.
- **Role Mappings:**
  - Use Kibana Role Mapping API or YAML to bind Active Directory groups (`cn=SRE,ou=Groups,dc=company,dc=com`) directly to `sre_admin_role`.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself and give an overview of your background and experience?
</details>
</details>

<details open>
<summary><h2>🏢 Mrisoftware</h2></summary>

<details open>
<summary><h3>Interview</h3></summary>

#### 【 CI/CD 】

<details>
<summary><strong>● What CI/CD platforms have you used?</strong></summary>

**Answer:**
Throughout my career managing enterprise CI/CD automation, I have worked with multiple leading platforms:

1. **Jenkins:** Deep expertise authoring modular Declarative and Scripted Pipelines using Groovy Shared Libraries, configuring ephemeral Kubernetes build agents via the Jenkins Kubernetes plugin, and managing master-agent architectures.
2. **GitLab CI/CD:** Writing `.gitlab-ci.yml` pipelines with multi-project triggers, custom Docker executors, Auto DevOps templates, and integrated container registries.
3. **GitHub Actions:** Creating reusable workflows, composite actions, matrix builds, OIDC integration with AWS/Azure, and self-hosted runner scale sets on Kubernetes (Actions Runner Controller - ARC).
4. **Azure DevOps Pipelines:** Authoring YAML-based build and release pipelines, managing environments with deployment gates, and integrating with Azure Artifacts.
</details>

<details>
<summary><strong>↳ Follow-up: How do you set up a pipeline in Jenkins? Can you walk through the stages you typically include?</strong></summary>

**Answer:**
I set up Jenkins pipelines using a **Multibranch Pipeline** project backed by a version-controlled `Jenkinsfile` stored directly in the application Git repository. Builds execute on dynamic, ephemeral pod agents provisioned on-demand in an EKS cluster.

```
[ Git Push / PR ] -> [ Ephemeral K8s Agent ]
                           |
  +------------------------+------------------------+
  |                                                 |
  v                                                 v
Stage 1: Checkout & Lint                     Stage 5: Security Scan (Trivy)
  |                                                 |
  v                                                 v
Stage 2: Unit Testing & Code Coverage        Stage 6: Artifact Push (ECR/JFrog)
  |                                                 |
  v                                                 v
Stage 3: SonarQube Quality Gate              Stage 7: GitOps Trigger (Argo CD)
  |                                                 |
  v                                                 v
Stage 4: Multi-stage Docker Build            Stage 8: Post Actions & Notifications
```

**Standard Enterprise Pipeline Stages:**

1. **Stage 1: Checkout & Pre-Flight Checks:** Clones repository at the commit SHA; runs linters and syntax checks.
2. **Stage 2: Unit Testing & Coverage:** Executes language-specific tests (`mvn test`, `pytest`, `npm test`) and publishes test reports using the `junit` plugin.
3. **Stage 3: SAST & SonarQube Quality Gate:**
   - Analyzes source code for bugs, code smells, and security vulnerabilities.
   - Enforces a strict pipeline halt via `waitForQualityGate()` if test coverage is below 80% or any Blocker bugs exist.
4. **Stage 4: Multi-stage Container Build:** Builds optimized Docker container images tagged with the immutable Git commit SHA: `${IMAGE_NAME}:${GIT_COMMIT}`.
5. **Stage 5: Container Vulnerability Scanning:** Executes **Trivy** or **Aqua Security** against the freshly built image (`trivy image --exit-code 1 --severity CRITICAL`). The build fails if unpatched critical CVEs are present.
6. **Stage 6: Artifact Registry Push:** Authenticates securely and pushes the container image to **AWS ECR** or **JFrog Artifactory**.
7. **Stage 7: Continuous Delivery / GitOps Sync:** Updates the target image tag in the GitOps Helm repository, which triggers **Argo CD** to deploy to Staging/Prod.
8. **Post Actions (`post` block):** Sends Slack / Microsoft Teams build notifications with commit author, build status, and duration; cleans up workspace.
</details>

<details>
<summary><strong>↳ Follow-up: Suppose you want to display certain messages on the console after deployment, such as showing a URL or a command the user needs to run — how would you achieve that?</strong></summary>

**Answer:**
There are several techniques in Jenkins to render clear, actionable post-deployment messages:

1. **Using the `post { success { ... } }` Pipeline Block:**
   ```groovy
   post {
       success {
           script {
               def appUrl = "https://${ENVIRONMENT}.myapp.example.com"
               echo """
               ====================================================================
               🚀 DEPLOYMENT COMPLETED SUCCESSFULLY!
               --------------------------------------------------------------------
               • Environment   : ${ENVIRONMENT.toUpperCase()}
               • Application URL: ${appUrl}
               • Verify Pods   : kubectl get pods -n ${ENVIRONMENT} -l app=myapp
               • Tail Logs     : kubectl logs -n ${ENVIRONMENT} -l app=myapp -f
               • Runbook Link  : https://wiki.internal/runbooks/myapp-deployment
               ====================================================================
               """
           }
       }
   }
   ```

2. **Colorized Console Output via the AnsiColor Plugin:**
   Wrap the output inside `ansiColor('xterm')` with ANSI escape sequences to display bold green or cyan terminal banners:
   ```groovy
   ansiColor('xterm') {
       echo "\033[1;32m [SUCCESS] Deployment complete! Access at: https://${appUrl} \033[0m"
   }
   ```

3. **Setting the Jenkins Build Description (Visible on UI):**
   Set the build display badge so engineers do not even need to open the console logs:
   ```groovy
   currentBuild.description = "<a href='https://${appUrl}'>Open Application (${ENVIRONMENT})</a>"
   ```
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>↳ Follow-up: Where exactly have you set up the deployment stage for the Kubernetes environment — what platform did you use?</strong></summary>

**Answer:**
In our production architecture, the deployment stage targets **Amazon EKS (Elastic Kubernetes Service)** running within dedicated private subnets of a custom AWS VPC.

**Deployment Platform & Tooling:**
- **GitOps Platform:** Rather than having Jenkins execute direct `kubectl apply` commands against the Kubernetes API (which requires sharing cluster admin credentials with CI runners), we adopted a **GitOps workflow using Argo CD**.
- **Execution Flow:**
  1. The Jenkins CI pipeline builds and pushes the Docker container to **AWS ECR**.
  2. Jenkins updates the target image tag in our Kubernetes deployment Git repository (`k8s-manifests`).
  3. **Argo CD**, running *inside* the EKS cluster, detects the Git commit and reconciles the state, deploying the new application version natively into the cluster.
</details>

<details>
<summary><strong>↳ Follow-up: Are you using native Kubernetes manifest files, Helm charts, or something else for deploying into the Kubernetes environment?</strong></summary>

**Answer:**
We primarily use **Helm Charts** combined with **Kustomize** for all microservice deployments:

**Why Helm Charts over Raw Manifests:**
1. **Parameterization & DRY (Don't Repeat Yourself):** Instead of duplicating raw YAML files across 10 microservices and 3 environments, a single standardized base chart defines the Deployment, Service, Ingress, HPA, and ServiceAccount.
2. **Environment Separation via Values Files:** Environment-specific configurations are maintained cleanly in `values-dev.yaml`, `values-qa.yaml`, and `values-prod.yaml`.
3. **Release Lifecycle & Versioning:** Helm packages releases into semantic versioned charts (`.tgz`) stored in our OCI-compliant private AWS ECR registry.
4. **Atomic Upgrades & Rollbacks:** Helm supports `--atomic` and built-in rollbacks (`helm rollback <release> <revision>`) if deployment health checks fail.
</details>

<details>
<summary><strong>↳ Follow-up: Is it possible to display such post-deployment messages using a Helm chart?</strong></summary>

**Answer:**
**Yes, absolutely.** Helm provides a built-in feature specifically designed for this purpose called the **`NOTES.txt` template**.

**How It Works:**
1. You create a file named `NOTES.txt` inside the `templates/` directory of your Helm chart (`mychart/templates/NOTES.txt`).
2. `NOTES.txt` is evaluated by Helm's Go templating engine upon execution.
3. Immediately after `helm install` or `helm upgrade` completes, Helm prints the rendered content directly to the user's terminal console.

**Example `templates/NOTES.txt`:**
```gotemplate
===============================================================================
🎉 SUCCESS! {{ .Chart.Name }} has been deployed to namespace '{{ .Release.Namespace }}'.
===============================================================================

1. Get the application URL:
{{- if .Values.ingress.enabled }}
  https://{{ (index .Values.ingress.hosts 0).host }}
{{- else if contains "LoadBalancer" .Values.service.type }}
  NOTE: It may take a few minutes for the LoadBalancer IP to be available.
  export SERVICE_IP=$(kubectl get svc --namespace {{ .Release.Namespace }} {{ include "myapp.fullname" . }} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
  echo http://$SERVICE_IP:{{ .Values.service.port }}
{{- end }}

2. Verify Pod Health:
  kubectl get pods -n {{ .Release.Namespace }} -l "app.kubernetes.io/name={{ include "myapp.name" . }}"

3. View live logs:
  kubectl logs -n {{ .Release.Namespace }} -l "app.kubernetes.io/name={{ include "myapp.name" . }}" -f
===============================================================================
```
</details>

#### 【 IAC 】

<details>
<summary><strong>● What kind of AWS resources have you set up using Terraform?</strong></summary>

**Answer:**
I have provisioned end-to-end cloud infrastructure in AWS using modular, reusable Terraform code:

- **Core Networking:** Custom VPCs, multi-AZ public and private subnets, Internet Gateways, NAT Gateways, Transit Gateways, Route Tables, and VPC Peering.
- **Compute & Container Platforms:** Amazon EKS clusters (managed node groups, IAM Roles for Service Accounts - IRSA, cluster autoscaler), EC2 Auto Scaling Groups (ASGs), and Launch Templates.
- **Storage & Databases:** Encrypted Amazon S3 buckets with lifecycle tiering rules, Amazon RDS PostgreSQL (Multi-AZ, read replicas, parameter groups), Amazon Aurora, and Amazon ElastiCache (Redis).
- **Security, Identity & Compliance:** IAM roles, instance profiles, least-privilege customer-managed policies, AWS KMS Customer Managed Keys (CMKs), Security Groups, Network ACLs, and AWS WAFv2 rules.
- **Traffic Routing & DNS:** Route 53 private and public hosted zones, AWS Certificate Manager (ACM) public TLS certificates, and Application/Network Load Balancers (ALB/NLB).
</details>

<details>
<summary><strong>● Suppose you are given a task to set up Terraform and provision resources into AWS completely from scratch, with nothing existing in AWS currently. What checklist or set of steps would you follow while setting up the Terraform pipeline?</strong></summary>

**Answer:**
Setting up Terraform from scratch in a greenfield AWS account requires establishing foundational security, remote state storage, and CI/CD pipelines:

```
[ Greenfield AWS Account ]
        |
        +--> Step 1: Remote State Bootstrap (S3 + DynamoDB / S3 Native Lock)
        +--> Step 2: CI/CD OIDC Authentication (No long-lived AWS keys!)
        +--> Step 3: Module & Directory Hierarchy Design
        +--> Step 4: Security Linting & Policy-as-Code Setup
        +--> Step 5: Automated Plan & Manual Gated Apply Pipeline
```

**Step-by-Step Implementation Checklist:**

1. **Step 1: Bootstrap the Remote State Backend:**
   - Manually or via a one-time bootstrap script, provision:
     - An **Amazon S3 bucket** with **Versioning Enabled**, SSE-KMS encryption, and **Public Access Blocked**.
     - An **Amazon DynamoDB table** (Partition key: `LockID` of type String) for state locking (or enable native locking in Terraform 1.10+).

2. **Step 2: Configure Passwordless CI/CD Authentication via OIDC:**
   - Never use static IAM access keys in CI/CD runners.
   - Configure an **AWS IAM OpenID Connect (OIDC) identity provider** for GitHub Actions or GitLab CI.
   - Create an IAM role with least-privilege permissions that the CI/CD runner assumes temporarily using short-lived STS tokens.

3. **Step 3: Repository & Directory Architecture:**
   - Establish a clean repository layout:
     ```
     ├── modules/           # Reusable building blocks (vpc, eks, rds)
     └── environments/      # Concrete root configurations
         ├── dev/           # backend.tf, main.tf, terraform.tfvars
         ├── qa/
         └── prod/
     ```
   - Lock versions in `versions.tf` (`required_version = ">= 1.5.0"`, `aws = "~> 5.0"`).

4. **Step 4: Shift-Left Security & Linting Gates in Pipeline:**
   - In the pipeline pre-flight stage, run:
     - `terraform fmt -check`: Enforces standard formatting.
     - `tflint`: Validates cloud provider syntax and deprecated attributes.
     - `checkov` / `tfsec`: Enforces security guardrails (e.g. fails if S3 bucket has public read or security group opens port 22 to `0.0.0.0/0`).
     - `infracost`: Estimates monthly cost impact on pull requests.

5. **Step 5: Automated Speculative Plan & Approval Gated Apply:**
   - On Pull Request: Run `terraform plan -out=tfplan` and post the human-readable summary as a PR comment.
   - On Merge to `main`: Require peer review approval, then run `terraform apply tfplan`.
</details>

<details>
<summary><strong>↳ Follow-up: What is the purpose of storing the Terraform state file in an S3 bucket?</strong></summary>

**Answer:**
The Terraform state file (`terraform.tfstate`) is the critical metadata database that maps real-world cloud resources to your HCL code definitions. Storing it in Amazon S3 solves four fundamental operational challenges:

1. **Single Source of Truth for Team Collaboration:**
   Storing state locally prevents team members or CI/CD systems from coordinating changes, leading to overlapping apply operations and resource duplication. S3 acts as the centralized repository accessible across the organization.
2. **Durability & High Availability:**
   Amazon S3 offers 99.999999999% (11 9s) data durability. S3 Bucket Versioning guarantees that every state modification generates a new revision, allowing instant rollback if a corrupted state file is written.
3. **Enterprise Security & Encryption:**
   Terraform state files often contain sensitive cleartext data (initial database passwords, private keys, resource ARNs). Storing state in S3 allows enforcing **AWS KMS customer-managed encryption at rest**, TLS-only transit policies (`aws:SecureTransport: true`), and strict IAM least-privilege access.
4. **Integration with State Locking:**
   Enables seamless integration with DynamoDB or native S3 lockfiles (`use_lockfile = true`), preventing race conditions when concurrent pipeline executions occur.
</details>

<details>
<summary><strong>● Suppose you have a Terraform project managing infrastructure that you've been maintaining for about 3 months, and recently created new EC2 instances/web apps using it. If you then revert the Terraform state file to a version from one month ago and run 'terraform apply', what will happen?</strong></summary>

**Answer:**
**Catastrophic State Desynchronization Scenario:**
Reverting the state file back by one month wipes out Terraform's knowledge of any infrastructure created in the last 30 days, while your current `.tf` configuration files *still contain* the code for those new EC2 instances and web apps.

**What Actually Happens During `terraform apply`:**

1. **Terraform Compares Code vs. Reverted State:**
   - Terraform reads the 1-month-old state file and discovers that the new EC2 instances and web apps are completely absent from state.
   - Terraform reads the current `.tf` code files and sees declarations for these instances.
   - **Conclusion reached by Terraform:** *"These resources do not exist yet; I must CREATE them."*

2. **Execution & Collision Failures:**
   - **For Resources with Unique Global or Regional Names (S3, IAM Roles):** The `apply` will fail with an error: `EntityAlreadyExistsException` or `BucketAlreadyOwnedByYou`, because AWS rejects creating an asset that already exists in the account.
   - **For Anonymous or Auto-Named Compute Resources (EC2, EBS Volumes):** AWS EC2 instances do *not* require unique names. Therefore, Terraform will **successfully provision an entirely new duplicate fleet of EC2 instances and EBS volumes**!
   - You will now have duplicate running instances, orphaned EBS volumes, double AWS billing, and orphaned resources that are completely untracked by Terraform.

3. **Remediation:**
   - Immediately restore the latest state file from S3 bucket versioning (`aws s3api list-object-versions` -> copy latest version back to head).
</details>

<details>
<summary><strong>↳ Follow-up: If a 'prevent\_destroy' lifecycle block has been applied to those resources, what will happen when you run 'terraform apply' after reverting the state file?</strong></summary>

**Answer:**
**The `prevent_destroy` block will have ZERO EFFECT and will NOT prevent the problem!**

**Technical Rationale:**
- The `lifecycle { prevent_destroy = true }` meta-argument is a client-side safety guard that instructs Terraform: *"If a planned change would cause an existing resource in the state file to be DESTROYED, reject the plan with an error."*
- However, in this scenario, because the state file was reverted to an older version, the resources **do not exist in the state file**.
- Terraform's execution plan is to **CREATE** (`+ create`) the resources, **not destroy them**.
- Because no destruction is planned, the `prevent_destroy` validation rule is never triggered, and Terraform proceeds to attempt creation.
</details>

<details>
<summary><strong>↳ Follow-up: If you actually want those resources to be destroyed despite the 'prevent\_destroy' lifecycle block, how would you go about destroying them?</strong></summary>

**Answer:**
If you legitimately want to destroy resources protected by `prevent_destroy`, Terraform will block any `terraform destroy` command with:
`Error: Instance cannot be destroyed ... prevent_destroy is set to true`.

**To bypass and destroy them safely:**
1. **Method 1: Temporarily Edit the Configuration (Standard Best Practice):**
   - Open the `.tf` file containing the target resource.
   - Comment out or remove the lifecycle block:
     ```hcl
     # lifecycle {
     #   prevent_destroy = true
     # }
     ```
   - Run `terraform destroy -target=<resource_address>` or remove the resource block from code and run `terraform apply`.
   - Once destroyed, delete the code block permanently.

2. **Method 2: Remove from State and Delete via Cloud Provider (Out-of-Band):**
   - Remove the resource from Terraform state management so Terraform no longer tracks it:
     ```bash
     terraform state rm <resource_address>
     ```
   - Manually delete the resource using the AWS Management Console or AWS CLI (`aws ec2 terminate-instances --instance-ids <id>`).
</details>

<details>
<summary><strong>↳ Follow-up: Suppose the same Terraform pipeline is working fine after destroying resources, but 2-3 days later you encounter an error while running the pipeline. What troubleshooting approach would you follow?</strong></summary>

**Answer:**
When a previously stable Terraform pipeline suddenly fails without code changes, I follow a systematic 5-point root cause analysis:

1. **Step 1: Analyze Pipeline Error & Traceability:**
   - Read the exact pipeline error message. Look for common runtime categories:
     - **Authentication / Expired Credentials:** Did the CI/CD IAM role assumption fail or AWS STS token expire?
     - **Provider Version Drift:** If the AWS provider version was unconstrained in `versions.tf` (e.g. `version = ">= 5.0"` instead of `~> 5.30.0`), a new provider release might have introduced a breaking change.
     - **State Lock Stale:** Check if a previous canceled pipeline run left a dangling lock in DynamoDB.

2. **Step 2: Enable Verbose Debug Logging:**
   - Run the plan locally or in a debug pipeline with debug logs enabled:
     ```bash
     export TF_LOG=DEBUG
     export TF_LOG_PATH=terraform_debug.log
     terraform plan
     ```
   - Search `terraform_debug.log` for HTTP `403 Forbidden`, `404 Not Found`, or `409 Conflict` returned by the AWS API.

3. **Step 3: Detect Out-of-Band State Drift (`refresh-only`):**
   - Execute:
     ```bash
     terraform plan -refresh-only
     ```
   - This compares the state file against actual AWS infrastructure without proposing changes. It reveals if someone made manual changes in the AWS Console (e.g. deleted a dependent subnet, modified a security group rule).

4. **Step 4: Check AWS CloudTrail Audit Logs:**
   - Query AWS CloudTrail for the impacted resource ARN or ID over the last 72 hours to see:
     - *Who* modified or deleted the resource?
     - *Which* IAM identity or automation tool initiated the API call?

5. **Step 5: Inspect State Consistency:**
   - Run `terraform state pull | jq .` to verify that the remote state file is valid JSON and not corrupted.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself and describe your experience with the various DevOps tools and technology stacks you have worked with?
</details>

<details open>
<summary><h3>Level 2</h3></summary>

#### 【 CI/CD 】

<details>
<summary><strong>● If you were building a CI/CD pipeline from scratch for a new project and wanted it to be as ideal as possible, what stages and tools would you include, and what would the overall pipeline look like?</strong></summary>

**Answer:**
An ideal, production-grade enterprise CI/CD pipeline combines **DevSecOps (Shift-Left Security)** with **GitOps (Continuous Delivery)** and **Progressive Canary Deployment**:

```
[ Developer Commit / PR ]
         |
         v
+-----------------------------------------------------------------------------------------+
| CONTINUOUS INTEGRATION (CI) PIPELINE (GitHub Actions / GitLab CI)                      |
|                                                                                         |
|  [ Stage 1: Pre-Flight ]     [ Stage 2: Quality & SAST ]   [ Stage 3: Build & Hardening]|
|  - Pre-commit hooks          - Unit Tests + Coverage (>80%)- Multi-stage Dockerfile     |
|  - Detect-secrets            - SonarQube Quality Gate      - Non-root Distroless base   |
|  - Linter (golangci / flake8)- Dependency-Check (SCA)                                   |
|                                                                                         |
|  [ Stage 4: Container Security ]  [ Stage 5: Publish & Sign ]                           |
|  - Trivy Image CVE Scan           - Push to AWS ECR / Artifactory                       |
|  - Fail on CRITICAL vulnerabilities- Sign image via Sigstore Cosign                     |
+-----------------------------------------------------------------------------------------+
                                             |
                               (Update Image Tag in GitOps Repo)
                                             v
+-----------------------------------------------------------------------------------------+
| CONTINUOUS DELIVERY (CD) VIA GITOPS (Argo CD & Argo Rollouts)                           |
|                                                                                         |
|  [ Staging Environment ]       [ Automated Smoke Tests ]    [ Production Gate ]         |
|  - Argo CD auto-sync           - DAST (OWASP ZAP)           - Manual / Approval gate    |
|                                - Cypress / Postman Tests                                |
|                                                                                         |
|  [ Production Canary Release (Argo Rollouts) ]                                          |
|  - 10% traffic -> Prometheus Analysis (Error rate < 0.1%, p99 latency < 200ms)          |
|  - Progressive Shift: 25% -> 50% -> 100% (Instant automated rollback on metric failure)  |
+-----------------------------------------------------------------------------------------+
```

**Key Pillars of the Ideal Pipeline:**
1. **Security Shift-Left:** Every commit runs static secret detection and dependency vulnerability checks before compilation.
2. **Immutable Artifacts:** The Docker image is built once, tagged with the Git commit SHA, signed cryptographically using **Cosign**, and promoted across environments without rebuilds.
3. **GitOps Operational Model:** No direct cluster access from CI runners; **Argo CD** pulls desired state from Git.
4. **Automated Canary Validation:** Progressive delivery via **Argo Rollouts** monitoring real-time Prometheus error rates, eliminating release downtime and blast radius.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● What is your core cloud platform skill—Azure or AWS?</strong></summary>

**Answer:**
My core cloud platform specialization is **Amazon Web Services (AWS)**, backed by extensive experience designing and operating cloud-native architectures at scale:
- Compute & Containers: Deep expertise in **Amazon EKS**, EC2 Auto Scaling, and AWS Lambda.
- Networking & Edge: Complex multi-VPC topologies, AWS Transit Gateway, Direct Connect, ALB/NLB, and CloudFront CDN.
- Storage & Databases: Amazon RDS Multi-AZ, Aurora Global Databases, DynamoDB, and multi-tier S3 architectures.
- Security & IAM: Zero-trust least-privilege IAM policies, IRSA for EKS, KMS encryption, AWS WAFv2, and GuardDuty.

Additionally, I maintain strong multi-cloud proficiency in **Microsoft Azure**, particularly in provisioning **Azure Kubernetes Service (AKS)**, managing Azure Virtual Networks (VNets), securing identities via Microsoft Entra ID (Azure AD), and implementing enterprise observability using Azure Monitor.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● As a DevOps engineer, what KPIs (key performance indicators) do you think should be tracked from a DevOps perspective?</strong></summary>

**Answer:**
A high-performing DevOps organization must measure both **Engineering Velocity & Stability** (via DORA metrics) and **Operational Reliability** (via SRE Golden Signals):

#### 1. The Four DORA Metrics (DevOps Research and Assessment):
- **Deployment Frequency (DF):** How often code is successfully deployed to production. (Target: Multiple deploys per day / on-demand).
- **Lead Time for Changes (LTTC):** The time it takes for a code commit to successfully run in production. (Target: Less than 1 hour).
- **Change Failure Rate (CFR):** The percentage of deployments that require a hotfix, rollback, or cause a production incident. (Target: 0–15%).
- **Failed Deployment Recovery Time (MTTR):** The time required to restore service when a production incident occurs. (Target: Under 30 minutes).

#### 2. SRE & Operational Golden Signals (Google SRE Framework):
- **Latency:** Time taken to service a request (measuring p95 and p99 percentiles, not averages).
- **Traffic (Throughput):** Demand placed on the system (Requests Per Second - RPS or concurrent connections).
- **Errors:** Rate of requests that fail (e.g. HTTP 5xx error percentage).
- **Saturation:** Resource utilization against theoretical capacity (CPU throttling %, Memory working set %, DB connection pool exhaustion).
- **SLO / Error Budget Burn Rate:** How rapidly the service is consuming its agreed reliability buffer over rolling 30-day windows.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>↳ Follow-up: Given that you mentioned high availability, what is your background in terms of pipelines and DevOps—do you focus on the application side, the infrastructure side, or both?</strong></summary>

**Answer:**
I operate as a **Full-Lifecycle Platform & Systems DevOps Engineer**, actively owning both the infrastructure foundation and the application delivery platform:

1. **Infrastructure Side:**
   - Architecting multi-AZ cloud foundations (VPCs, Transit Gateways, subnets across 3 Availability Zones).
   - Building highly available compute clusters (EKS node groups spread evenly across AZs using Pod Topology Spread Constraints).
   - Designing multi-AZ database failover (RDS Multi-AZ, Aurora read replicas).

2. **Application & Pipeline Side:**
   - Implementing zero-downtime deployment patterns (Canary and Blue-Green deployments via Argo Rollouts).
   - Configuring application resilience primitives inside Kubernetes: `PodDisruptionBudgets` (PDB), graceful shutdown handling with `preStop` sleep hooks, and properly calibrated `liveness` and `readiness` probes.
   - Enabling 12-factor application compliance: externalized configuration via ConfigMaps/Vault and stateless horizontal scaling.
</details>

<details>
<summary><strong>↳ Follow-up: From a high-availability (HA) perspective, what would you do at the infrastructure level to make a product highly available?</strong></summary>

**Answer:**
To achieve true high availability (99.99% uptime) at the infrastructure layer, I implement an architecture that eliminates every single point of failure (SPOF):

```
                                [ AWS Route 53 (DNS Failover / Latency Routing) ]
                                                        |
                         +------------------------------+------------------------------+
                         |                                                             |
                         v                                                             v
             [ AWS CloudFront (CDN Edge) ]                                 [ Secondary Region (DR) ]
                         |
                         v
             [ Application Load Balancer (Multi-AZ) ]
                         |
       +-----------------+-----------------+
       |                                   |
       v                                   v
 [ AZ-1 Private Subnet ]             [ AZ-2 Private Subnet ]             [ AZ-3 Private Subnet ]
 - NAT Gateway 1                     - NAT Gateway 2                     - NAT Gateway 3
 - EKS Worker Nodes (Zone A)         - EKS Worker Nodes (Zone B)         - EKS Worker Nodes (Zone C)
       |                                   |                                   |
       +-----------------+-----------------+-----------------------------------+
                         |
                         v
             [ Amazon Aurora Global Database ]
             - AZ-1: Writer Instance
             - AZ-2: Reader Instance (Auto-failover in <30s)
             - AZ-3: Reader Instance
```

**Key Infrastructure HA Engineering Steps:**

1. **Multi-Availability Zone Compute Redundancy:**
   - Deploy compute workloads across a minimum of **3 Availability Zones**.
   - Use Kubernetes **Pod Topology Spread Constraints** (`topologyKey: topology.kubernetes.io/zone`) to ensure pods are evenly distributed across physical failure domains.
2. **Redundant Egress & Ingress Paths:**
   - Deploy independent NAT Gateways in each Availability Zone so an AZ-specific network outage does not block outbound internet egress for the other zones.
   - Use cross-zone load balancing on AWS Application Load Balancers.
3. **Database High Availability & Auto-Failover:**
   - Provision **Amazon Aurora Multi-AZ** with read replicas. If the primary writer fails, Aurora automatically promotes a reader in another AZ in under 30 seconds without data loss.
4. **Cross-Region Disaster Recovery (Warm Standby / Active-Active):**
   - For mission-critical workloads, replicate data to a secondary AWS region using **Aurora Global Database** (storage-level replication with latency < 1s) and Route 53 health-check DNS failover.
5. **Self-Healing Infrastructure via Auto Scaling:**
   - Configure Auto Scaling Groups with dynamic target tracking policies (CPU/memory) and auto-replacement of unhealthy EC2 instances.
</details>

<details>
<summary><strong>● In a global company where cloud engineering and DevOps are operated as a global unit across many regions, how can we ensure standards and consistency in DevOps practices across all regions?</strong></summary>

**Answer:**
Operating a unified DevOps culture across global regions (Americas, EMEA, APAC) without creating operational silos requires building an **Internal Developer Platform (IDP)** powered by central governance and decentralized execution:

```
[ Central Cloud Platform / SRE Team ]
  - Golden Path Terraform Modules
  - Standardized CI/CD Templates
  - Organizational Policy-as-Code (SCPs, Kyverno, Checkov)
                 |
                 +=============================+=============================+
                 |                             |                             |
                 v                             v                             v
           [ APAC Region ]               [ EMEA Region ]               [ Americas Region ]
           - Standard VPC Module         - Standard VPC Module         - Standard VPC Module
           - Standard EKS Module         - Standard EKS Module         - Standard EKS Module
           - Central Guardrails          - Central Guardrails          - Central Guardrails
```

1. **Centralized "Golden Path" Module Repositories:**
   - Maintain a single, version-controlled library of enterprise **Terraform modules** and **Helm charts**.
   - Regional teams are not permitted to invent bespoke VPC or EKS architectures; they consume version-pinned Golden Modules (`source = "git::https://.../terraform-aws-eks.git?ref=v3.2.0"`).

2. **Standardized CI/CD Pipeline Templates:**
   - Use centralized **GitHub Reusable Workflows** or **GitLab CI Templates**.
   - Pipeline stages (SAST, secret scanning, container build, image signing) are managed centrally. Regional application teams simply call the template, guaranteeing that security and compliance gates run uniformly worldwide.

3. **Policy as Code (Enforced Guardrails):**
   - **Cloud Level:** Enforce **AWS Service Control Policies (SCPs)** organization-wide to prevent regional drift (e.g., restrict allowed AWS regions, disallow disabling CloudTrail, block unencrypted EBS volumes).
   - **Terraform Level:** Run **Checkov** or **OpenTofu/Sentinel** in CI to reject code that violates corporate security policies.
   - **Cluster Level:** Deploy **Kyverno** or **OPA/Gatekeeper** across all Kubernetes clusters globally to enforce identical container security standards (e.g. require non-root, deny privileged containers, enforce memory limits).

4. **Global Observability & Standard Tagging Taxonomy:**
   - Enforce a mandatory global resource tagging strategy (`CostCenter`, `Environment`, `Owner`, `Region`) enforced via automated policy.
   - Centralize telemetry into federated Prometheus/Grafana or Datadog instances with standardized SLO/SLA dashboards.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you tell us about your educational background, specifically where you completed your B.Tech?

↳ **Candidate Introduction:** Where have you been working as a DevOps engineer during your 6 years of experience?

↳ **Candidate Introduction:** Given your job history of 1.5 years at Informatica, 4 years at Accenture, and now only about 6-8 months back at Informatica, why are you looking to change jobs again?

● **Candidate Introduction:** What is your current CTC (compensation)?

↳ **Candidate Introduction:** What is your expected CTC (compensation) for this role?

↳ **Candidate Introduction:** Why do you believe a 42% salary increase is justified, especially since you only recently joined Informatica within the past year?

↳ **Candidate Introduction:** When you mention wanting career growth, what does career growth mean to you?

● **Candidate Introduction:** Are you aware that this position requires working in shifts and sometimes working from the office depending on the shift?

<details>
<summary><strong>● If you were working on a critical project and started facing conflicting priorities that put the project at risk, what would your thought process be and what actions would you take?</strong></summary>

**Answer:**
When conflicting priorities threaten a critical deliverable, I follow a disciplined 4-step conflict resolution framework:

1. **Step 1: Quantify Impact & Map Dependencies (Data-Driven Assessment):**
   - I assess both initiatives objectively rather than reacting emotionally:
     - What is the business and financial impact of each deliverable?
     - Are there hard contractual customer SLAs or compliance deadlines attached?
     - What are the upstream and downstream technical blockers?

2. **Step 2: Transparent & Proactive Stakeholder Alignment:**
   - The biggest mistake an engineer can make is silent struggling or hoping for the best.
   - I immediately schedule a short, focused alignment meeting with the Project Managers, Product Owners, and Engineering Manager.

3. **Step 3: Present Actionable Trade-Off Options (MoSCoW Prioritization):**
   - Instead of presenting a binary "I can't do this," I bring structured alternatives:
     - **Option A (Phased Delivery):** Deliver the core Minimum Viable Product (MVP) of the critical project on schedule, deferring nice-to-have features to the next sprint.
     - **Option B (Re-sequencing):** Focus 100% bandwidth on Project 1 for one week, then pivot fully to Project 2 with an adjusted delivery date agreed upon by stakeholders.
     - **Option C (Resource Augmentation):** Delegate or pair-program specific tasks with another team member to absorb the load.

4. **Step 4: Formalize & Re-Baseline:**
   - Once the decision is agreed upon, I document the revised priorities and timelines in Jira and Confluence, ensuring all stakeholders have shared expectations and no surprises occur later.
</details>

● **Candidate Introduction:** How big is the team you have worked with in your current or recent role?
</details>
</details>

<details open>
<summary><h2>🏢 Accionlabs</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 05-08-2026 08:58 PM*

#### 【 LINUX 】

<details>
<summary><strong>● Can you explain how the Linux boot process works and describe its different stages?</strong></summary>

**Answer:**
The Linux boot process consists of six fundamental, sequential stages that transition the machine from bare hardware to a fully functional multi-user operating system:

```
[ 1. BIOS / UEFI ] -> [ 2. GRUB2 Bootloader ] -> [ 3. Kernel Init ] -> [ 4. Initramfs ] -> [ 5. Systemd (PID 1) ] -> [ 6. User Space Targets ]
```

1. **Stage 1: BIOS / UEFI (Hardware Initialization):**
   - Executes the **POST (Power-On Self-Test)** to verify hardware integrity (RAM, CPU, disks).
   - Reads the boot order from CMOS/NVRAM and loads the initial bootloader code from the Master Boot Record (MBR) or the EFI System Partition (ESP) on a GPT drive.

2. **Stage 2: Bootloader (GRUB2):**
   - Displays the operating system selection menu and default timeout.
   - Loads the selected compressed Linux kernel image (`/boot/vmlinuz-<version>`) and the initial RAM filesystem (`/boot/initramfs-<version>.img`) into system memory.
   - Passes boot parameters (e.g. `root=UUID=... ro quiet splash`) to the kernel.

3. **Stage 3: Kernel Initialization:**
   - The kernel decompresses itself into RAM and initializes core hardware subsystems (CPU memory management, page tables, interrupts).
   - Unpacks the `initramfs` image into a temporary root filesystem (ramfs/tmpfs) in memory.

4. **Stage 4: Initramfs (Temporary Root & Driver Loading):**
   - Contains temporary minimal user-space binaries and device drivers (RAID, LVM, multipath, SCSI, NVMe, LUKS disk encryption).
   - Mounts the actual root filesystem (`/`) from the storage device.
   - Executes `pivot_root` or `switch_root` to replace the temporary RAM disk with the real root filesystem.

5. **Stage 5: Init System (Systemd - PID 1):**
   - The kernel launches the first user-space process: `/usr/lib/systemd/systemd` with **PID 1**.
   - Systemd reads the default boot target (symlink `/etc/systemd/system/default.target`).
   - Analyzes unit dependency graphs and mounts all filesystems declared in `/etc/fstab`.

6. **Stage 6: Target Execution & User Space Daemons:**
   - Starts target services in parallel (e.g., `sshd`, `networkd`, `chronyd`, `docker`, `cron`).
   - Reaches `multi-user.target` (console login) or `graphical.target` (display manager / GUI).
</details>

<details>
<summary><strong>↳ Follow-up: When a Linux system is normally booted, what runlevel is it typically at?</strong></summary>

**Answer:**
In production environments, a Linux system typically boots into:
- **Runlevel 3 (`multi-user.target`):** The standard runlevel for **production servers**. It provides a non-graphical, multi-user environment with full networking services and remote SSH access.
- **Runlevel 5 (`graphical.target`):** The standard runlevel for **workstations and desktops**. It includes everything in Runlevel 3 plus an X11 or Wayland display manager and Graphical User Interface (GUI).

**Reference Mapping between SysV Init Runlevels and Modern Systemd Targets:**

| SysV Runlevel | Modern Systemd Target | Purpose / Operational Mode |
| :---: | :--- | :--- |
| **0** | `poweroff.target` | Halts and powers off the system. |
| **1 / S** | `rescue.target` | Single-user maintenance mode (root shell, no networking). |
| **2** | `multi-user.target` (without NFS) | Multi-user mode without network file sharing (Debian/Ubuntu). |
| **3** | `multi-user.target` | **Standard Server Mode:** Multi-user, CLI only, full networking. |
| **4** | Custom / User-defined | Unused / reserved for custom configurations. |
| **5** | `graphical.target` | **Standard Desktop Mode:** Multi-user, networking, GUI. |
| **6** | `reboot.target` | Reboots the system. |

To check and change the active target:
```bash
# Check current target
systemctl get-default
runlevel

# Set default to server multi-user mode
sudo systemctl set-default multi-user.target
```
</details>

<details>
<summary><strong>● How do you troubleshoot slowness on a system or server?</strong></summary>

**Answer:**
To troubleshoot server performance degradation methodically without guessing, I apply the **USE Method** (Utilization, Saturation, and Errors) across the four physical hardware pillars: **CPU, Memory, Storage I/O, and Network**.

```
[ Step 1: High-Level Health Check ]
uptime -> Check Load Average (1m, 5m, 15m) vs. Available CPU Cores
   |
   +---> CPU Bottleneck?    --> Check top, htop, pidstat, mpstat
   +---> Memory Exhaustion? --> Check free -m, vmstat (si/so), dmesg (OOM)
   +---> Storage I/O Wait?  --> Check iostat -xz 1 (%util, await)
   +---> Network Saturation?--> Check sar -n DEV 1, ss -s, nic drops
```

1. **Step 1: Check System Load vs Core Count (`uptime`):**
   ```bash
   uptime
   nproc
   ```
   If the 1-minute load average is significantly higher than the total CPU core count (`nproc`), processes are queuing up waiting for CPU or disk resources.

2. **Step 2: CPU Saturation & Process Profiling:**
   ```bash
   top -c
   mpstat -P ALL 1
   ```
   - High `%us` (user): Application CPU saturation (e.g. infinite loop, intensive computation).
   - High `%sy` (system): Kernel contention, high syscall frequency, or excessive context switching.
   - High `%wa` (iowait): The CPU is sitting idle waiting for storage disk operations to finish!

3. **Step 3: Memory Contention & Swapping (`free -m` & `vmstat 1`):**
   ```bash
   free -h
   vmstat 1 5
   ```
   - Inspect `si` (swap-in) and `so` (swap-out) in `vmstat`. If active swapping is occurring, disk thrashing degrades throughput by 100x.
   - Check kernel ring buffer for Out-Of-Memory events: `dmesg -T | grep -i oom`.

4. **Step 4: Disk I/O Saturation (`iostat -xz 1`):**
   ```bash
   iostat -xz 1
   ```
   - `%util`: If utilization is approaching 100%, the underlying disk is completely saturated.
   - `await`: Average time in milliseconds for I/O requests. An `await` > 15–20ms indicates storage latency or EBS volume IOPS throttling.
   - Locate the offending process using `iotop -oPa`.

5. **Step 5: Network Contention & Socket Drops:**
   ```bash
   sar -n DEV 1
   ss -s
   netstat -s | grep -i retrans
   ```
   Check for dropped packets, high TCP retransmissions, or socket buffer overflows.
</details>

<details>
<summary><strong>● Have you ever encountered a situation where inodes on a system were full, and if so, what did you do to resolve it?</strong></summary>

**Answer:**
Yes. A memorable production incident occurred when our monitoring alerted that an application server was failing all write operations with the error `No space left on device`, despite `df -h` showing **over 40 GB of free storage space available**.

**1. Root Cause Diagnosis:**
Running `df -i` immediately revealed that the root filesystem `/` had reached **100% Inode Utilization** (`IUse% = 100%` with 0 free inodes), preventing the kernel from allocating any new file metadata table entries:
```bash
df -i /
# Filesystem      Inodes   IUsed   IFree IUse% Mounted on
# /dev/nvme0n1p1 2097152 2097152       0  100% /
```

**2. Tracking Down the Inode Hog:**
I ran an automated shell command to count the number of files per directory:
```bash
find / -xdev -printf '%h\n' | sort | uniq -c | sort -k 1 -nr | head -n 10
```
This revealed that a directory under `/var/spool/postfix/maildrop` and an application session folder `/tmp/client_sessions` had accumulated **over 1.8 million zero-byte orphaned files** due to a failing cleanup script.

**3. Remediation (Handling "Argument list too long"):**
Executing standard `rm *` failed with `bash: /bin/rm: Argument list too long`. I cleaned the directories efficiently using `find` with `-delete`:
```bash
find /tmp/client_sessions -type f -name "sess_*" -mtime +2 -delete
```
This immediately freed 1.5 million inodes and restored application service within minutes.

**4. Permanent Prevention:**
- Configured a systemd tmpfiles cleanup rule (`/etc/tmpfiles.d/session-cleanup.conf`) to purge orphaned session files automatically every 6 hours.
- Created a Prometheus alert rule checking `node_filesystem_files_free / node_filesystem_files < 0.15` to trigger warnings when inode capacity drops below 15%.
</details>

<details>
<summary><strong>● Can you explain the difference between a process and a thread?</strong></summary>

**Answer:**
In modern operating systems, processes and threads are fundamental execution abstractions with distinct resource boundaries:

```
+---------------------------------------------------------------+
| PROCESS (Independent Virtual Address Space)                   |
| [ Code Segment ]  [ Data / Heap ]  [ Open File Descriptors ]  |
|                                                               |
|   +-----------------------+     +-----------------------+     |
|   | THREAD 1              |     | THREAD 2              |     |
|   | - Stack & Registers   |     | - Stack & Registers   |     |
|   | - Program Counter(PC) |     | - Program Counter(PC) |     |
|   +-----------------------+     +-----------------------+     |
+---------------------------------------------------------------+
```

| Comparison Feature | Process | Thread (Lightweight Process) |
| :--- | :--- | :--- |
| **Definition** | An executing instance of a computer program with dedicated resources. | The smallest unit of execution scheduled by the OS CPU scheduler. |
| **Memory Isolation** | **Completely Isolated.** Each process has its own virtual address space, page table, and heap. | **Shared Memory.** All threads within a process share the same heap, data segment, and code. |
| **Resources** | Owns dedicated file descriptors, network sockets, and environment variables. | Shares file descriptors and open resources with peer threads in the same process. |
| **Individual State** | Process ID (PID), memory maps, credentials. | Own Thread ID (TID), Program Counter (PC), CPU registers, and private stack memory. |
| **Creation Overhead** | **Heavyweight.** Requires `fork()` / `clone()` system calls, duplicating page tables and allocating address space. | **Lightweight.** Created via `pthread_create()`; consumes minimal memory. |
| **Context Switching** | **Slow.** Requires flushing/invalidating CPU TLB (Translation Lookaside Buffer) and swapping memory maps. | **Fast.** Memory maps remain unchanged; only CPU registers and stack pointers are switched. |
| **Communication** | Requires **Inter-Process Communication (IPC)**: Unix domain sockets, pipes, shared memory (`shmget`). | Direct communication via shared variables and memory pointers (requires mutexes/locks to avoid race conditions). |
| **Failure Blast Radius** | If one process crashes (e.g. SegFault), other processes continue running unaffected. | If one thread crashes with a segmentation fault, it typically brings down the **entire parent process**. |
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● What is your understanding of CI/CD pipelines, and what is the most complex pipeline you have built, including the scale at which it operated?</strong></summary>

**Answer:**
**Understanding of CI/CD:**
CI/CD is not merely automated scripting; it is the **engineering backbone of modern software delivery**. It provides an automated, reproducible contract that validates code correctness, enforces security policies, builds immutable artifacts, and safely deploys them to production with zero downtime and instant rollback capabilities.

**Most Complex Enterprise Pipeline Built:**
At my previous engagement, I architected a unified **Multi-Region DevSecOps & GitOps Pipeline** supporting an enterprise fintech platform consisting of 35+ microservices deployed across three AWS regions (`us-east-1`, `eu-west-1`, `ap-southeast-1`):

```
[ Developer PR ]
       |
       v
[ GitHub Actions / Jenkins Dynamic K8s Agent ]
  ├── Parallel Matrix: Unit Tests + Coverage (Python / Go / Java)
  ├── Security Gate: SonarQube SAST + Snyk SCA Dependency Scan
  ├── Multi-Arch Container Build (AMD64 + ARM64) via BuildKit
  ├── Image Vulnerability Scan (Trivy: Fail on CRITICAL CVEs)
  └── Ephemeral Preview Environment (Spun up dynamic K8s namespace for QA)
       |
  (PR Merged -> Auto-Tag & Sign Image via Cosign -> Push to AWS ECR)
       |
       v
[ GitOps Repository (Image Digest Updated via Git Bot) ]
       |
       v
[ Argo CD & Argo Rollouts ]
  ├── Staging Auto-Sync & Automated E2E Cypress API Tests
  └── Production Progressive Canary Release:
      - 10% traffic routed to Canary
      - Prometheus metric analysis (Error rate < 0.05%, p99 latency < 250ms)
      - Traffic progressively shifts to 100% over 45 minutes
      - Instant automated rollback if metric anomalies occur
```

**Scale and Operational Metrics:**
- Handled **300+ builds per day** across 80+ software engineers.
- Median pipeline execution time dropped from 28 minutes to **6.5 minutes** using remote Docker build caching and parallelized test execution.
- Maintained a **Change Failure Rate (CFR) under 2%** with zero deployment downtime.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Can you briefly explain how Kubernetes works?</strong></summary>

**Answer:**
Kubernetes operates on a declarative **Reconciliation Loop (Control Loop)** model: *"Observe actual state, compare with desired state, and execute actions to eliminate the difference."*

```
User (Declarative YAML) -> [ kube-apiserver ] <---> [ etcd (Single Source of Truth) ]
                                   ^
                                   | (Watches & Reconciles)
     +-----------------------------+-----------------------------+
     |                                                           |
[ kube-scheduler ]                                  [ kube-controller-manager ]
(Assigns Pods to Nodes)                             (Maintains Replica Counts)
     |                                                           |
     +-----------------------------+-----------------------------+
                                   | (Dispatches PodSpec via TLS)
                                   v
                      [ Worker Node: kubelet ]
                                   | (CRI)
                      [ containerd / CRI-O ] -> Starts Pod Containers
                                   | (CNI)
                      [ Calico / VPC CNI ]   -> Allocates IP & Routes
```

1. **Declarative Intent:** The user declares desired state (e.g. `replicas: 3`) using YAML and submits it to the `kube-apiserver`.
2. **Persistence:** The API server authenticates, authorizes (RBAC), validates the manifest via admission webhooks, and writes the spec into `etcd`.
3. **Controller Reconciliation:** The Deployment/ReplicaSet controller inside `kube-controller-manager` detects that desired replicas (3) exceeds actual running pods (0) and generates three unbound Pod objects.
4. **Scheduling:** The `kube-scheduler` observes unscheduled pods, filters nodes based on resource capacity, taints, tolerations, and affinities, and binds each pod to a node.
5. **Node Execution:** The `kubelet` daemon on the target worker node receives the PodSpec, commands the container runtime (e.g., `containerd`) via the Container Runtime Interface (CRI) to pull images and run containers, and calls the CNI plugin to configure pod IP networking.
6. **Self-Healing:** Kubelet monitors container health via Liveness/Readiness probes. If a container crashes, Kubelet restarts it; if an entire worker node dies, the control plane reschedules its pods onto healthy nodes.
</details>

<details>
<summary><strong>● Suppose you have namespace1 and namespace2, each with a pod, and these pods are scheduled on two different nodes. If you try to resolve and perform a TCP probe from a pod in namespace2 to a pod in namespace1, will you be able to do that? If so, how would this be accomplished in Kubernetes?</strong></summary>

**Answer:**
**Default Kubernetes Behavior:** **YES, absolutely.**

In standard Kubernetes networking (conforming to the fundamental CNI specification):
- Every pod gets its own unique IP address.
- All pods can communicate with all other pods across all namespaces and all nodes **without NAT (Network Address Translation)** by default.

**How to Accomplish This in Kubernetes:**

1. **Expose the Target Pod in `namespace1` via a Service:**
   Create a ClusterIP Service in `namespace1`:
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: backend-svc
     namespace: namespace1
   spec:
     selector:
       app: backend
     ports:
     - protocol: TCP
       port: 8080
       targetPort: 8080
   ```

2. **Connect from the Pod in `namespace2` using CoreDNS FQDN:**
   From the pod inside `namespace2`, initiate the TCP connection using the **Fully Qualified Domain Name (FQDN)**:
   ```bash
   backend-svc.namespace1.svc.cluster.local:8080
   ```
   - CoreDNS resolves this FQDN to the ClusterIP of `backend-svc`.
   - `kube-proxy` (or Cilium eBPF) routes the TCP packet across the physical nodes directly to the destination pod IP.

3. **Exception: When NetworkPolicies are Enforced:**
   If zero-trust `NetworkPolicies` are enabled in `namespace1`, all incoming traffic is blocked by default. To allow `namespace2` to communicate:
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: allow-from-namespace2
     namespace: namespace1
   spec:
     podSelector:
       matchLabels:
         app: backend
     ingress:
     - from:
       - namespaceSelector:
           matchLabels:
             kubernetes.io/metadata.name: namespace2
       ports:
       - protocol: TCP
         port: 8080
   ```
</details>

<details>
<summary><strong>● In a scenario where you have a pool of GPU-based servers in a Kubernetes cluster, how would you ensure that only GPU-based pods get scheduled onto those nodes, and not other pods?</strong></summary>

**Answer:**
To achieve complete, bidirectional scheduling isolation—ensuring **non-GPU pods never run on expensive GPU nodes**, and **GPU pods only run on GPU nodes**—you must combine **Taints & Tolerations** with **Node Affinity**:

```
[ GPU Worker Node Pool ]
  - Taint:  sku=gpu:NoSchedule           <--- Repels standard pods!
  - Label:  accelerator=nvidia-tesla-v100 <--- Attracts GPU pods!

[ Standard Pod ]                          [ Machine Learning GPU Pod ]
  - No toleration                         - Toleration: sku=gpu:NoSchedule
  - Result: REJECTED by GPU nodes         - NodeAffinity: accelerator=nvidia-tesla-v100
                                          - Result: SCHEDULED onto GPU nodes!
```

1. **Step 1: Taint the GPU Nodes (Repel standard workloads):**
   ```bash
   kubectl taint nodes <node-gpu-01> sku=gpu:NoSchedule
   ```
   *Effect:* Standard pods without a matching toleration will never be scheduled on these nodes.

2. **Step 2: Label the GPU Nodes (Provide identification):**
   ```bash
   kubectl label nodes <node-gpu-01> accelerator=nvidia-tesla-v100
   ```

3. **Step 3: Configure the GPU Workload Manifest:**
   In the GPU deployment manifest, specify both the **Toleration** (to pass through the taint) and a **NodeAffinity** (to force placement on the GPU nodes):
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: gpu-inference-service
   spec:
     replicas: 2
     template:
       metadata:
         labels:
           app: gpu-inference
       spec:
         # 1. Toleration allows pod to be placed on tainted GPU nodes
         tolerations:
         - key: "sku"
           operator: "Equal"
           value: "gpu"
           effect: "NoSchedule"

         # 2. NodeAffinity ensures pod ONLY runs on GPU nodes
         affinity:
           nodeAffinity:
             requiredDuringSchedulingIgnoredDuringExecution:
               nodeSelectorTerms:
               - matchExpressions:
                 - key: accelerator
                   operator: In
                   values:
                   - nvidia-tesla-v100

         containers:
         - name: inference-engine
           image: company/model-runner:v2.1
           resources:
             limits:
               nvidia.com/gpu: 1 # Requests physical GPU device
   ```
</details>

#### 【 IAC 】

<details>
<summary><strong>● What is your understanding of Terraform?</strong></summary>

**Answer:**
Terraform is an open-source Infrastructure-as-Code (IaC) software tool created by HashiCorp. It enables engineers to define, provision, configure, and version both cloud infrastructure (AWS, Azure, GCP) and on-premises software (Kubernetes, VMware, Vault) using a high-level declarative configuration language known as **HashiCorp Configuration Language (HCL)**.

**Key Technical Attributes:**
1. **Declarative Nature:** You declare the *desired end state* of infrastructure; Terraform determines the dependency graph and exact sequence of API calls needed to reach that state.
2. **Provider Plugin Architecture:** Terraform decouples the core orchestration engine from cloud-specific logic using modular, version-pinned provider plugins.
3. **State Management:** Tracks real-world cloud metadata and resource IDs in a state file (`terraform.tfstate`), enabling precise drift detection and safe planning.
4. **Idempotence:** Running `terraform apply` multiple times without code changes results in zero modifications (`0 to add, 0 to change, 0 to destroy`).
</details>

<details>
<summary><strong>↳ Follow-up: Could you explain roughly how Terraform works internally?</strong></summary>

**Answer:**
Terraform's internal architecture is divided into two primary layers: **Terraform Core** and **Terraform Plugins (Providers)**, which communicate over **gRPC**:

```
+-------------------------------------------------------------------------------+
| TERRAFORM CORE (Go Binary)                                                    |
|                                                                               |
|  [ Parse HCL & Config ] ---> [ Build Dependency Graph (DAG) ]                 |
|                                         |                                     |
|  [ Compute State Diff ] <---------------+ (Fetch Live State via gRPC)        |
|  [ Generate Plan ]                                                            |
+-------------------------------------------------------------------------------+
                                          | (gRPC Protocol)
                                          v
+-------------------------------------------------------------------------------+
| TERRAFORM PROVIDER PLUGIN (e.g. terraform-provider-aws)                       |
|                                                                               |
|  [ Schema Definition ] <---> [ Translates HCL to AWS SDK / REST API Calls ]   |
+-------------------------------------------------------------------------------+
```

1. **Configuration Parsing & AST:** Terraform Core reads all `.tf` files in the working directory, resolves variables, locals, functions, and module calls into an Abstract Syntax Tree (AST).
2. **Graph Construction (DAG):** Analyzes references between resources (e.g. `aws_subnet` referencing `aws_vpc.main.id`) and builds a **Directed Acyclic Graph (DAG)** to determine execution order and parallelizable actions.
3. **State Refresh:** Terraform Core invokes the Provider via gRPC to call cloud APIs and refresh the live status of all tracked assets into memory.
4. **Diffing Engine:** Compares the freshly refreshed live infrastructure against the desired HCL code and calculates the minimal set of CRUD actions (Create, Read, Update, Destroy).
5. **Plan / Apply Graph Walk:** Walks the graph concurrently (defaulting to 10 parallel threads). For each node, the provider executes the appropriate cloud API call and returns updated metadata, which Terraform Core writes immediately to the remote state file.
</details>

<details>
<summary><strong>↳ Follow-up: How do you use Terraform in your day-to-day work?</strong></summary>

**Answer:**
In my daily operations as a Senior DevOps Engineer, Terraform is integrated into our GitOps workflow:

- **Developing Reusable Modules:** Authoring version-controlled, tested modules for VPCs, EKS clusters, and RDS databases.
- **Pull Request Code Reviews & Automated Plans:** Reviewing automated `terraform plan` speculative runs generated in GitHub Actions / Atlantis on pull requests.
- **State File Curation:** Performing surgical state operations when refactoring modules (`terraform state mv`, `terraform state rm`, `terraform import`).
- **Drift Detection:** Running scheduled daily automated pipelines (`terraform plan -detailed-exitcode`) to catch unauthorized manual changes made via cloud consoles.
- **Security & Policy Scanning:** Using `tflint`, `tfsec`, and `checkov` in pre-commit hooks and CI pipelines to enforce compliance and security standards.
</details>

<details>
<summary><strong>↳ Follow-up: What are some complex tasks you have performed using Terraform?</strong></summary>

**Answer:**
1. **Multi-Account Zero-Trust Network Topology:**
   Provisioned an enterprise AWS Transit Gateway interconnecting 8 AWS accounts (Shared Services, Security, Dev, Staging, Prod), automating cross-account RAM resource shares, VPC attachments, route table associations, and propagation via Terraform.
2. **Zero-Downtime Monolithic State Refactoring:**
   Decomposed a massive, fragile 4,000-line monolithic Terraform state file into 4 decoupled, independently deployable layers (`networking`, `security`, `data`, `compute`) using `moved {}` blocks and `terraform state mv` without destroying a single production resource.
3. **Blue/Green Cluster Migrations:**
   Automated the provisioning of parallel EKS clusters during Kubernetes minor version upgrades, orchestrating Route 53 weighted DNS traffic shifts through Terraform configurations.
</details>

<details>
<summary><strong>● How do you manage multiple environments in Terraform when only the values differ between them, and how do you do this efficiently?</strong></summary>

**Answer:**
The industry-standard, most scalable enterprise approach is the **Directory-per-Environment Pattern using Shared Reusable Modules**:

```
repo-root/
├── modules/                      # Reusable, tested HCL code
│   ├── networking/ (vpc, subnets)
│   ├── compute/    (eks, asg)
│   └── database/   (rds, elasticache)
└── environments/                 # Concrete, isolated root configurations
    ├── dev/
    │   ├── backend.tf            # Points to s3://.../dev/terraform.tfstate
    │   ├── main.tf               # Calls ../../modules/...
    │   └── terraform.tfvars      # dev values (e.g. t3.medium, 2 nodes)
    ├── qa/
    │   ├── backend.tf            # Points to s3://.../qa/terraform.tfstate
    │   ├── main.tf
    │   └── terraform.tfvars
    └── prod/
        ├── backend.tf            # Points to s3://.../prod/terraform.tfstate
        ├── main.tf
        └── terraform.tfvars      # prod values (e.g. m5.2xlarge, Multi-AZ)
```

**Why this pattern is superior to Terraform Workspaces:**
1. **State Blast Radius Isolation:** The state files are completely separated. An accidental destructive apply in `dev` cannot corrupt or lock the `prod` state file.
2. **Granular IAM Permissions:** CI/CD runners for Dev can have limited AWS account access, while Prod pipelines require separate production credentials.
3. **Environment-Specific Drift:** Allows deploying experimental module versions in Dev (`ref=v2.0.0-rc1`) while keeping Prod pinned to stable (`ref=v1.4.0`).
4. **DRY Configuration via Terragrunt:** To eliminate boilerplate backend and provider code across environment folders, **Terragrunt** can be introduced as a thin wrapper.
</details>

<details>
<summary><strong>● Can you write a Terraform manifest to create an S3 bucket, using the Terraform documentation as reference?</strong></summary>

**Answer:**
Here is a production-grade, hardened Amazon S3 bucket manifest adhering to AWS security best practices (Terraform AWS Provider v4/v5+):

```hcl
# 1. Base S3 Bucket Resource
resource "aws_s3_bucket" "app_storage" {
  bucket        = "company-secure-assets-${var.environment}"
  force_destroy = false # Protects against accidental deletion of non-empty buckets

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Compliance  = "PCI-DSS"
  }
}

# 2. Enable Bucket Versioning (Essential for disaster recovery)
resource "aws_s3_bucket_versioning" "storage_versioning" {
  bucket = aws_s3_bucket.app_storage.id

  versioning_configuration {
    status = "Enabled"
  }
}

# 3. Enforce Server-Side Encryption (KMS)
resource "aws_s3_bucket_server_side_encryption_configuration" "storage_encryption" {
  bucket = aws_s3_bucket.app_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = true # Reduces KMS API costs by up to 99%
  }
}

# 4. Block All Public Access (Mandatory Security Standard)
resource "aws_s3_bucket_public_access_block" "storage_public_block" {
  bucket = aws_s3_bucket.app_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 5. Enforce TLS 1.2+ in Transit Bucket Policy
resource "aws_s3_bucket_policy" "enforce_tls" {
  bucket = aws_s3_bucket.app_storage.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureConnections"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.app_storage.arn,
          "${aws_s3_bucket.app_storage.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
```
</details>

#### 【 NETWORKING 】

<details>
<summary><strong>↳ Follow-up: Do you have an understanding of how TCP packets work?</strong></summary>

**Answer:**
Yes. The **Transmission Control Protocol (TCP)** is a Layer 4 (Transport Layer) connection-oriented protocol that guarantees reliable, ordered, and error-checked delivery of octets between networked applications.

```
+-----------------------------------------------------------------------------------+
| TCP PACKET HEADER (20 - 60 Bytes)                                                 |
|                                                                                   |
|  [ 16-bit Source Port ]                 [ 16-bit Destination Port ]               |
|  [ 32-bit Sequence Number (Seq) ]                                                 |
|  [ 32-bit Acknowledgment Number (Ack) ]                                           |
|  [ 4-bit Offset ] [ Reserved ] [ Flags: URG, ACK, PSH, RST, SYN, FIN ] [ Window ] |
|  [ 16-bit Checksum ]                    [ 16-bit Urgent Pointer ]                 |
|  [ Options (MSS, Window Scale, SACK) ]  [ Payload / Application Data ]            |
+-----------------------------------------------------------------------------------+
```

**Core Mechanical Principles:**

1. **Three-Way Handshake (Connection Establishment):**
   ```
   Client                                  Server
     |  --- SYN (Seq=X) ------------------>  | (Server in LISTEN state)
     |  <-- SYN-ACK (Seq=Y, Ack=X+1) ------  | (Server transitions to SYN-RCVD)
     |  --- ACK (Seq=X+1, Ack=Y+1) ------->  | (Connection ESTABLISHED)
   ```

2. **Reliable In-Order Delivery & Retransmissions:**
   - Every transmitted byte has a Sequence Number (`Seq`).
   - The receiver confirms receipt with an Acknowledgment Number (`Ack`).
   - If an ACK is not received within the **Retransmission Timeout (RTO)**, the sender automatically retransmits the missing segment.

3. **Flow Control & Congestion Control:**
   - **Sliding Window (`Window Size`):** The receiver advertises its available buffer space so the sender does not overwhelm it.
   - **Congestion Control Algorithms (Cubic, BBR):** Adjust the Congestion Window (`cwnd`) based on detected network loss and round-trip time (RTT).

4. **Four-Way Handshake (Connection Teardown):**
   - Active closer sends `FIN` -> Passive closer responds with `ACK`.
   - Passive closer finishes buffer transmission and sends its own `FIN` -> Active closer responds with `ACK`.
   - Active closer enters `TIME_WAIT` (default $2 \times \text{MSL} = 60\text{s}$) to guarantee the final ACK arrived before closing the socket.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you explain your roles and responsibilities in your current/previous project?
</details>
</details>

<details open>
<summary><h2>🏢 Innova Solutions</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 LINUX 】

<details>
<summary><strong>↳ Follow-up: Which scripting language did you use for automation tasks (e.g., with Ansible)?</strong></summary>

**Answer:**
In my automation workflows with Ansible and Linux systems, I rely primarily on **Python** and **Bash**:
- **Python:** Because Ansible is natively written in Python, I use it for authoring custom Ansible modules, custom filters, callback plugins, and dynamic inventory scripts querying AWS APIs via `boto3`.
- **Bash / Shell:** Used for lightweight system tasks, quick shell-based deployment verification, bootstrapping remote hosts with Python dependencies (`cloud-init`), and executing local pre-commit tasks.
</details>

#### 【 GIT 】

<details>
<summary><strong>● Suppose a developer accidentally committed directly to the main branch in Git. How would you fix this?</strong></summary>

**Answer:**
The remediation strategy depends on whether the commit was already pushed to the remote repository or only exists locally.

#### Scenario 1: The Commit is ONLY Local (Not Pushed to Remote)
This is the simplest and safest scenario:
```bash
# 1. Create a new feature branch containing the accidental commit
git branch feature/new-work

# 2. Reset the local main branch to match the remote main branch exactly
git checkout main
git reset --hard origin/main

# 3. Switch to the new feature branch and continue working safely
git checkout feature/new-work
```

#### Scenario 2: The Commit HAS BEEN PUSHED to Remote `main`
In a shared enterprise repository, never force-push over `main` without coordination, as it breaks the history for all other developers.

- **Option A: Clean Non-Destructive Revert (Recommended Enterprise Best Practice):**
  ```bash
  # 1. Create a feature branch preserving the developer's work
  git checkout -b feature/new-work

  # 2. Return to main and revert the accidental commit
  git checkout main
  git revert <accidental_commit_hash> -m 1

  # 3. Push the clean revert commit to remote main
  git push origin main

  # 4. Open a formal Pull Request from feature/new-work for review
  ```
- **Option B: Force-Push with Lease (If the commit just happened and nobody pulled):**
  ```bash
  git checkout -b feature/new-work
  git checkout main
  git reset --hard HEAD~1
  git push origin main --force-with-lease
  ```

#### Preventative Guardrails (Eliminate the Problem):
Enable **Branch Protection Rules** (GitHub) or **Protected Branches** (GitLab):
- Require Pull Request reviews before merging (minimum 1 peer review).
- Require status checks to pass before merging.
- Restrict pushes to `main` completely (disallow direct pushes even for repository administrators).
</details>

#### 【 CI/CD 】

<details>
<summary><strong>↳ Follow-up: Which tool did you use for CI/CD?</strong></summary>

**Answer:**
I have extensive hands-on experience using **Jenkins** (orchestrated with dynamic Kubernetes agent pods) and **GitLab CI/CD** for continuous integration and automated testing, coupled with **Argo CD** for continuous GitOps delivery into Kubernetes clusters.
</details>

<details>
<summary><strong>↳ Follow-up: Do you have any experience or knowledge of Azure DevOps?</strong></summary>

**Answer:**
Yes. I have hands-on experience configuring **Azure DevOps (ADO)** services:
- **Azure Pipelines:** Designing multi-stage YAML pipelines for continuous integration and deployment.
- **Azure Repos:** Branch policies, PR status checks, and branch permissions.
- **Service Connections:** Establishing passwordless, least-privilege OIDC service connections to Azure subscriptions and AWS accounts.
- **Variable Groups & Azure Key Vault:** Securely injecting runtime credentials and certificates into build pipelines without exposing plaintext secrets.
- **Self-Hosted Agents:** Deploying custom agent pools running inside containerized environments or virtual machine scale sets.
</details>

<details>
<summary><strong>● Did you use Jenkins pipelines to provision Terraform infrastructure, i.e., to deploy Terraform-managed resources?</strong></summary>

**Answer:**
Yes. I have implemented production-grade, automated Jenkins pipelines to manage the full Terraform lifecycle:

**Pipeline Architecture & Stages:**
1. **Dynamic Ephemeral Runner:** Jenkins triggers an ephemeral Docker container or Kubernetes pod agent containing pre-installed, version-locked `terraform`, `tflint`, and `checkov`.
2. **Lint & Security Gate:** Runs `terraform fmt -check`, `tflint`, and security scans (`checkov -d . --framework terraform`).
3. **Speculative Plan Generation (`terraform plan`):** Generates an execution plan:
   ```bash
   terraform plan -out=tfplan -no-color
   ```
   Saves `tfplan` as a build artifact to guarantee that the exact inspected plan is applied.
4. **Interactive Manual Approval Gate (Production):**
   ```groovy
   stage('Approval') {
       steps {
           script {
               input message: "Approve deployment of tfplan to Production?", ok: "Deploy"
           }
       }
   }
   ```
5. **Apply Stage:** Executes `terraform apply tfplan` using temporary AWS credentials assumed via IAM STS.
</details>

<details>
<summary><strong>↳ Follow-up: Suppose a deployment to a production environment using Jenkins failed halfway through. How would you handle this situation?</strong></summary>

**Answer:**
A mid-deployment failure in production requires immediate risk mitigation, impact analysis, and state stabilization:

```
[ Step 1: Mitigate Customer Impact ] -> [ Step 2: Analyze Jenkins Log ] -> [ Step 3: Check State / Lock ] -> [ Step 4: Remediate & Reapply ]
```

1. **Step 1: Check Production Health & Mitigate Traffic:**
   - Verify whether live customer traffic is affected.
   - If deploying application containers via Blue/Green or Canary, immediately rollback the load balancer or traffic router to 100% stable version.
2. **Step 2: Inspect Jenkins Logs & Identify Failure Point:**
   - Determine whether the failure was due to network timeouts, cloud provider API rate limits, missing IAM permissions, or a failing health check.
3. **Step 3: Inspect Remote State & State Locks (If Terraform was deploying):**
   - Terraform apply operations are **non-atomic**. Resources created before the crash exist in the real cloud and in the state file!
   - Ensure the state lock in DynamoDB was properly released; if dangling, verify no runner is alive and run `terraform force-unlock`.
4. **Step 4: Check for Tainted Resources:**
   - A resource that failed creation halfway through may be marked as `tainted`.
   - Re-running `terraform apply` will cleanly destroy and recreate tainted resources while preserving successfully created ones.
5. **Step 5: Postmortem & Pipeline Hardening:**
   - Add automated cleanup blocks in `post { failure { ... } }` to alert on-call teams via PagerDuty and capture diagnostic logs.
</details>

<details>
<summary><strong>↳ Follow-up: Do you have any knowledge or experience with Azure DevOps?</strong></summary>

**Answer:**
Yes. In Azure DevOps, I have designed multi-stage YAML pipelines that implement enterprise CI/CD standards:
- Structuring pipelines using **Stages, Jobs, and Steps** (`stages: -> jobs: -> steps:`).
- Implementing deployment environments (`environment: 'production'`) with configured **Approvals and Checks** (e.g., requiring signoff from senior engineers or passing ServiceNow change requests).
- Utilizing **Deployment Strategies** (`runOnce`, `rolling`, `canary`) for VM and Kubernetes deployments.
- Reusing standardized pipeline logic across repositories using **YAML templates** (`template: steps/build.yml@templates`).
</details>

<details>
<summary><strong>↳ Follow-up: Can you explain how you built a Docker image, pushed it to ECR, and deployed it to an EKS or ECS cluster using your CI/CD pipeline?</strong></summary>

**Answer:**
Here is the end-to-end automated lifecycle:

1. **Step 1: Build & Optimize Docker Image:**
   - In the pipeline, execute a multi-stage Docker build tagged with the immutable Git commit SHA:
     ```bash
     docker build -t ${ECR_REGISTRY}/${REPO_NAME}:${GIT_COMMIT} .
     ```
2. **Step 2: Security Vulnerability Scan:**
   - Run **Trivy** to scan the freshly built image:
     ```bash
     trivy image --exit-code 1 --severity CRITICAL ${ECR_REGISTRY}/${REPO_NAME}:${GIT_COMMIT}
     ```
   - If critical vulnerabilities are found, the pipeline halts immediately.
3. **Step 3: Authenticate & Push to Amazon ECR:**
   - Obtain short-lived Docker credentials via AWS CLI:
     ```bash
     aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${ECR_REGISTRY}
     docker push ${ECR_REGISTRY}/${REPO_NAME}:${GIT_COMMIT}
     ```
4. **Step 4: Deploy to EKS or ECS:**
   - **For EKS (GitOps Approach):** The pipeline updates the target image tag in the GitOps deployment repository (`values.yaml`), triggering **Argo CD** to execute a zero-downtime rolling update.
   - **For ECS (Direct Deployment):** The pipeline registers a new task definition revision updating the container image URI and invokes `aws ecs update-service` to initiate a rolling deployment.
</details>

<details>
<summary><strong>↳ Follow-up: Once the Docker image is pushed to ECR, how would you deploy it to ECS or EKS using a Jenkins pipeline?</strong></summary>

**Answer:**
Here is the exact declarative Jenkins pipeline code for both deployment targets:

#### Target A: Deploying to Amazon EKS (Using Helm)
```groovy
stage('Deploy to EKS') {
    steps {
        withAWS(role: 'arn:aws:iam::123456789012:role/JenkinsEKSRole', region: 'us-east-1') {
            sh '''
            # Update local kubeconfig for the EKS cluster
            aws eks update-kubeconfig --name prod-cluster --region us-east-1

            # Perform atomic Helm upgrade with rolling update
            helm upgrade --install my-app ./charts/my-app \
              --namespace production \
              --set image.repository=${ECR_REGISTRY}/my-app \
              --set image.tag=${GIT_COMMIT} \
              --atomic \
              --timeout 5m
            '''
        }
    }
}
```

#### Target B: Deploying to Amazon ECS (Updating Task Definition)
```groovy
stage('Deploy to ECS') {
    steps {
        withAWS(role: 'arn:aws:iam::123456789012:role/JenkinsECSRole', region: 'us-east-1') {
            sh '''
            # 1. Fetch current active task definition
            TASK_DEF=$(aws ecs describe-task-definition --task-definition my-service)

            # 2. Inject the new ECR image tag using jq
            NEW_TASK_DEF=$(echo $TASK_DEF | jq --arg IMAGE "${ECR_REGISTRY}/my-app:${GIT_COMMIT}" \
              '.taskDefinition | .containerDefinitions[0].image = $IMAGE | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)')

            # 3. Register the new task definition revision
            NEW_REVISION_ARN=$(aws ecs register-task-definition --cli-input-json "$NEW_TASK_DEF" --query 'taskDefinition.taskDefinitionArn' --output text)

            # 4. Trigger rolling update of the ECS Service
            aws ecs update-service --cluster prod-ecs-cluster --service my-service --task-definition $NEW_REVISION_ARN --force-new-deployment
            '''
        }
    }
}
```
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● How do you manage Docker images and their versioning?</strong></summary>

**Answer:**
Managing container images at enterprise scale requires strict immutability, vulnerability scanning, and lifecycle retention policies:

1. **Tagging Convention (Never Use `latest` in Production!):**
   - **Git Commit SHA:** Every build is tagged with the 7-character Git commit SHA (`app:a1b2c3d`) for 100% traceability back to source code.
   - **Semantic Versioning (SemVer):** Release tags follow `app:v2.4.1`.
2. **Immutable Image Tags in Registry:**
   - Enable **Tag Immutability** in Amazon ECR or JFrog Artifactory. Once `app:v2.4.1` is pushed, nobody can overwrite or retag it, preventing supply chain attacks.
3. **Registry Lifecycle Management (Pruning):**
   - Configure **ECR Lifecycle Policies** to keep registry storage costs controlled:
     - Retain untagged images for only 3 days.
     - Keep the last 30 feature-branch images.
     - Keep all release tags matching `v*` indefinitely.
4. **Vulnerability Scanning & Signing:**
   - Enable automated scanning on push via AWS Inspector / Trivy.
   - Cryptographically sign container images using **Sigstore Cosign** and enforce signature verification inside Kubernetes via Kyverno before allowing container execution.
</details>

<details>
<summary><strong>↳ Follow-up: Did you use Docker within your CI/CD pipelines?</strong></summary>

**Answer:**
Yes, in two distinct architectural patterns:
1. **Docker as Ephemeral Build Environments:**
   Instead of installing Java, Node.js, Python, or Go directly on persistent Jenkins host runners, Jenkins pipeline steps execute inside specialized disposable Docker containers (`agent { docker { image 'maven:3.8-openjdk-17' } }`). This guarantees clean, reproducible builds across all jobs.
2. **Building Container Images (Kaniko / BuildKit):**
   Within Kubernetes-hosted Jenkins runners, rather than mounting the vulnerable host Docker socket (`/var/run/docker.sock`), we use **Google Kaniko** or **BuildKit** to build and push container images securely in user space without requiring root privileges.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Do you have experience working with Kubernetes?</strong></summary>

**Answer:**
Yes. I have over 5 years of production experience managing Kubernetes clusters on Amazon EKS and self-hosted environments. My expertise encompasses cluster design, ingress networking (ALB / NGINX), GitOps (Argo CD), Helm chart packaging, multi-tenancy, RBAC, CNI network policies, CSI storage, and production incident response.
</details>

<details>
<summary><strong>● Suppose you have hosted microservices using Kubernetes, and a microservice pod keeps entering a CrashLoopBackOff state. What troubleshooting steps would you follow to resolve this?</strong></summary>

**Answer:**
`CrashLoopBackOff` indicates that the container repeatedly starts, fails, and restarts, with Kubernetes applying an exponential backoff delay. Here is my structured diagnostic workflow:

1. **Step 1: Check Pod Status & Exit Code:**
   ```bash
   kubectl get pods -n <namespace> -o wide
   kubectl describe pod <pod-name> -n <namespace>
   ```
   Inspect the **Last State: Terminated** section for the **Exit Code**:
   - **Exit Code 137:** The container was **OOMKilled** (Out Of Memory). It exceeded its defined memory limit.
   - **Exit Code 1:** Application fatal exception / unhandled error (e.g. database connection failed, missing configuration).
   - **Exit Code 126 / 127:** Executable not found or bad container entrypoint path.
   - **Exit Code 143:** Graceful termination via `SIGTERM`.

2. **Step 2: Inspect Previous Container Logs:**
   Standard `kubectl logs` might return empty if the container just crashed. Fetch logs from the crashed instance:
   ```bash
   kubectl logs <pod-name> -n <namespace> --previous
   ```
   Look for stack traces, uncaught exceptions, or failed initialization routines.

3. **Step 3: Verify Environment Variables & Secrets:**
   Ensure all referenced ConfigMaps and Secrets exist:
   ```bash
   kubectl get configmap,secret -n <namespace>
   ```
   A pod will fail at startup if an environment variable references a non-existent Secret key.

4. **Step 4: Check Liveness & Startup Probes:**
   If an application takes 45 seconds to initialize (e.g. large Spring Boot service) but the Liveness probe begins checking after 10 seconds, Kubernetes will mistakenly kill the container while it is still starting.
   - *Fix:* Introduce a **Startup Probe** with `failureThreshold: 30` and `periodSeconds: 10`.
</details>

<details>
<summary><strong>● Suppose your Kubernetes worker nodes suddenly become 'NotReady'. What could be the possible causes, and how would you troubleshoot this issue?</strong></summary>

**Answer:**
A node transitions to `NotReady` when the `kube-apiserver` stops receiving heartbeats from the node's `kubelet` daemon for longer than the node monitor grace period (default 40 seconds).

**Possible Causes:**
1. **Kubelet Failure:** The `kubelet` process crashed, ran out of file descriptors, or stopped.
2. **Container Runtime Failure:** `containerd` or Docker daemon froze or became unresponsive.
3. **Disk Pressure / Inode Exhaustion:** `/var/lib/containerd` or the root disk reached 100% utilization.
4. **Memory / CPU Starvation:** System processes were starved of resources, freezing the kernel.
5. **Network Partition:** Network outage between the worker node subnet and the control plane API.

**Troubleshooting Steps:**
1. **Inspect Node Conditions from Cluster API:**
   ```bash
   kubectl describe node <node-name>
   ```
   Check the `Conditions` table: Look at `DiskPressure`, `MemoryPressure`, `PIDPressure`, and `Ready`. Check the **Events** section at the bottom.
2. **Connect to the Node (via AWS SSM / SSH):**
   - Check Kubelet Service:
     ```bash
     systemctl status kubelet
     journalctl -u kubelet -n 100 --no-pager
     ```
   - Check Container Runtime (`containerd`):
     ```bash
     systemctl status containerd
     crictl ps
     ```
   - Check Disk and Memory:
     ```bash
     df -h
     df -i
     free -m
     ```
</details>

<details>
<summary><strong>↳ Follow-up: Given that you can't afford much downtime while troubleshooting NotReady worker nodes, what process would you follow to quickly and safely recover the affected workloads?</strong></summary>

**Answer:**
When production uptime is at risk, **workload recovery takes precedence over node debugging**:

1. **Step 1: Cordon the Failing Node Immediately:**
   ```bash
   kubectl cordon <node-name>
   ```
   Ensures no newly created pods are routed to the unhealthy node.
2. **Step 2: Force Immediate Eviction / Rescheduling:**
   By default, Kubernetes waits 5 minutes (`pod-eviction-timeout`) before rescheduling pods from a `NotReady` node.
   - To bypass this delay immediately, force-delete the stuck pods belonging to Deployments:
     ```bash
     kubectl delete pod <pod-name> -n <ns> --grace-period=0 --force
     ```
   - The Deployment ReplicaSet controller will instantly provision replacement pods on healthy surviving nodes.
3. **Step 3: Trigger Cloud Provider Auto-Recovery (Cloud-Native Best Practice):**
   - Rather than manually debugging a frozen VM in production, **terminate the unhealthy EC2 instance**:
     ```bash
     aws ec2 terminate-instances --instance-ids <instance-id>
     ```
   - The AWS Auto Scaling Group (or Karpenter) detects the missing instance and automatically provisions a clean, healthy worker node in under 2 minutes. Workloads redistribute automatically.
</details>

<details>
<summary><strong>● Suppose your Kubernetes cluster suddenly experiences memory pressure and pods start failing. How would you identify which process is causing this issue, and how would you recover from it?</strong></summary>

**Answer:**
1. **Step 1: Identify Saturated Nodes & Culprit Pods:**
   ```bash
   # Check which node is under memory pressure
   kubectl top nodes

   # Sort all pods cluster-wide by memory utilization
   kubectl top pods -A --sort-by=memory | head -20
   ```
2. **Step 2: Check Node Eviction Events:**
   ```bash
   kubectl describe node <affected-node> | grep -A 10 "Conditions"
   kubectl get events -A --field-selector reason=Evicted
   ```
3. **Step 3: Identify the "Noisy Neighbor" Rogue Container:**
   Inspect the top-consuming pod to verify if a single container has an unbounded memory leak.
4. **Step 4: Immediate Recovery:**
   - Scale out the cluster compute capacity immediately (add nodes via Auto Scaling Group or Karpenter).
   - If a specific non-critical workload is leaking memory uncontrollably, temporarily scale down its deployment (`kubectl scale deployment <rogue-app> --replicas=0`) to protect shared production infrastructure.
5. **Step 5: Permanent Prevention:**
   - Enforce **Resource Quotas** and **LimitRanges** per namespace.
   - Require all application deployments to define explicit memory `requests` and `limits`.
</details>

<details>
<summary><strong>↳ Follow-up: How would you identify where pod evictions are happening and which node is affected?</strong></summary>

**Answer:**
- **Find all currently evicted pods across all namespaces:**
  ```bash
  kubectl get pods -A --field-selector status.phase=Failed -o wide | grep Evicted
  ```
- **Filter cluster events specifically for Eviction reasons:**
  ```bash
  kubectl get events -A --field-selector reason=Evicted --sort-by='.metadata.creationTimestamp'
  ```
- **Inspect the affected node's eviction threshold events:**
  ```bash
  kubectl describe node <node-name> | grep -E "MemoryPressure|DiskPressure|EvictionThresholdMet"
  ```
</details>

<details>
<summary><strong>↳ Follow-up: What specific command would you use to identify the process (the 'noisy neighbor') consuming excessive CPU or memory inside a pod?</strong></summary>

**Answer:**
Depending on whether the container has a shell or is a hardened/distroless image:

1. **Direct In-Pod Execution (Standard Images):**
   ```bash
   # CPU top consumers
   kubectl exec -it <pod-name> -n <namespace> -- ps aux --sort=-%cpu | head -10

   # Memory top consumers
   kubectl exec -it <pod-name> -n <namespace> -- ps aux --sort=-%mem | head -10
   ```

2. **Ephemeral Debug Container (For Distroless / Minimal Images without `ps` or `sh`):**
   ```bash
   kubectl debug -it <pod-name> -n <namespace> --image=busybox --target=<container-name> -- top
   ```
   Using `--target=<container-name>` joins the target container's process namespace directly.

3. **From the Host Worker Node via Container Runtime CLI:**
   ```bash
   crictl stats
   crictl top <container-id>
   ```
</details>

#### 【 IAC 】

<details>
<summary><strong>● Have you worked with Terraform?</strong></summary>

**Answer:**
Yes. I have extensive experience using Terraform to provision, version, and manage enterprise infrastructure as code across cloud platforms (primarily AWS) using modular design patterns, remote state locking, and automated CI/CD pipelines.
</details>

<details>
<summary><strong>↳ Follow-up: What kind of infrastructure do you provision using Terraform?</strong></summary>

**Answer:**
Full-stack production environments, including:
- **Networking:** Multi-tier VPCs, public/private subnets, NAT Gateways, Internet Gateways, Route Tables, Transit Gateways.
- **Compute & Containers:** Amazon EKS clusters (managed node groups, IAM OIDC providers, Karpenter), EC2 Auto Scaling Groups, Launch Templates.
- **Data & Storage:** Amazon RDS PostgreSQL/Aurora clusters, ElastiCache Redis, S3 buckets with KMS encryption and lifecycle rules.
- **Security & IAM:** IAM roles, policies, KMS keys, Security Groups, WAFv2 Web ACLs.
</details>

<details>
<summary><strong>↳ Follow-up: Do you use Terraform specifically to provision AWS resources?</strong></summary>

**Answer:**
Yes, predominantly Amazon Web Services (AWS) using the official `hashicorp/aws` provider. I also have experience deploying resources to Microsoft Azure using `hashicorp/azurerm` and orchestrating Kubernetes objects using `hashicorp/kubernetes` and `hashicorp/helm` providers.
</details>

<details>
<summary><strong>↳ Follow-up: Do you also use Terraform modules in your infrastructure provisioning?</strong></summary>

**Answer:**
Yes, modular design is central to our Terraform architecture:
- **Custom Internal Modules:** We author reusable internal modules (`modules/vpc`, `modules/eks-cluster`, `modules/rds-postgres`) that bake in corporate security standards, required tags, and compliance baselines.
- **Community Verified Modules:** We leverage trusted open-source modules from the Terraform Registry (e.g. `terraform-aws-modules/vpc` and `terraform-aws-modules/eks`), pinning them to exact semantic release versions.
</details>

<details>
<summary><strong>● What command would you use to unlock a Terraform state lock?</strong></summary>

**Answer:**
```bash
terraform force-unlock <LOCK_ID>
```
</details>

<details>
<summary><strong>↳ Follow-up: Even with a remote backend configured, Terraform state locks can still occur in some cases. How would you go about unlocking the state in such situations?</strong></summary>

**Answer:**
State locks become stuck when a Terraform execution (locally or in a CI runner) is abruptly terminated, killed by an OOM error, canceled by a user, or disconnected by a network dropout before it can release the lock.

**Safe Unlocking Procedure:**
1. **Step 1: Confirm No Active Run Exists:**
   Verify with team members and inspect CI/CD build runners to ensure that no process is actively applying changes. Forcing an unlock on an active run can cause catastrophic state corruption!
2. **Step 2: Obtain the Lock ID:**
   When Terraform fails to acquire the lock, it prints an error message containing the unique **Lock ID**:
   ```text
   Error: Error acquiring the state lock
   Lock Info:
     ID:        3b2a5d10-8f92-4e56-b089-a1b2c3d4e5f6
     Path:      my-bucket/prod/terraform.tfstate
     Operation: OperationTypeApply
     Who:       jenkins@runner-pod-14
     Created:   2026-08-05 14:20:00 UTC
   ```
3. **Step 3: Execute `force-unlock`:**
   ```bash
   terraform force-unlock 3b2a5d10-8f92-4e56-b089-a1b2c3d4e5f6
   ```
4. **Step 4: Manual DynamoDB Removal (Fallback):**
   If the CLI command fails, navigate to the AWS DynamoDB Console, open the state lock table, locate the item whose primary key `LockID` matches the state file path, and manually delete the item.
</details>

<details>
<summary><strong>↳ Follow-up: Can you explain why using a remote backend is important in Terraform?</strong></summary>

**Answer:**
Using a remote backend (such as Amazon S3 with DynamoDB / native lockfile) is critical for four reasons:
1. **Concurrency & Race Condition Prevention:** Remote state locking guarantees that only one engineer or pipeline can execute changes at a time, preventing split-brain states.
2. **Team Collaboration & Single Source of Truth:** Centralizes state so all team members and automation runners operate against the identical infrastructure view.
3. **Security & Secret Protection:** State files contain unmasked sensitive values. Remote backends enforce KMS encryption at rest, TLS in transit, and granular IAM role-based access control.
4. **Disaster Recovery:** S3 Bucket Versioning automatically archives every state modification, enabling instant recovery if a corrupted state is written.
</details>

<details>
<summary><strong>● Suppose some resources were deployed manually through the AWS Console, and you now want to manage them using Terraform. How would you go about doing that?</strong></summary>

**Answer:**
Bringing manually deployed AWS resources under Terraform management follows a 4-step workflow:

1. **Step 1: Write the Declarative HCL Code:**
   Write the resource configuration block in your `.tf` files matching the real-world resource attributes (or write a modern Terraform 1.5+ `import` block).
   ```hcl
   resource "aws_s3_bucket" "existing_bucket" {
     bucket = "my-manually-created-bucket"
   }
   ```
2. **Step 2: Import the Resource into State:**
   - **Modern Approach (Terraform 1.5+):**
     ```hcl
     import {
       to = aws_s3_bucket.existing_bucket
       id = "my-manually-created-bucket"
     }
     ```
     Run: `terraform plan -generate-config-out=generated_bucket.tf`
   - **CLI Approach:**
     ```bash
     terraform import aws_s3_bucket.existing_bucket my-manually-created-bucket
     ```
3. **Step 3: Reconcile Drift:**
   Run `terraform plan` to compare the imported state with your code. Adjust any missing arguments, tags, or properties until the plan reports:
   `Plan: 0 to add, 0 to change, 0 to destroy`.
4. **Step 4: Commit to Version Control:**
   Merge the updated HCL code into Git. The resource is now 100% under Terraform IaC management.
</details>

<details>
<summary><strong>● How would you manage multiple environments—such as dev, QA, and prod—using Terraform?</strong></summary>

**Answer:**
The recommended enterprise architecture is the **Directory-per-Environment Pattern with Shared Modules**:
- Modules live in `modules/` (e.g. `modules/vpc`, `modules/app`).
- Environments live in dedicated directories: `environments/dev`, `environments/qa`, `environments/prod`.
- Each environment directory has its own distinct remote state S3 key, provider credentials, and `terraform.tfvars`.
- This ensures 100% state blast-radius isolation, distinct IAM access controls, and independent deployment schedules.
</details>

<details>
<summary><strong>● Suppose deployments to dev and QA environments succeeded, but the staging deployment failed because someone manually changed a resource in that environment. How would you identify which resource was manually changed, and how would you fix it?</strong></summary>

**Answer:**
1. **Step 1: Identify the Drifted Resource (`terraform plan -refresh-only`):**
   Execute:
   ```bash
   terraform plan -refresh-only
   ```
   This command queries AWS directly, updates the in-memory state, and displays the exact diff between the real-world infrastructure and the state file without proposing code changes.
2. **Step 2: Investigate Who Made the Manual Change (AWS CloudTrail):**
   Query CloudTrail event history for the drifted resource ID (e.g. security group ID or subnet ARN) to identify the IAM user, IP address, and timestamp of the unauthorized console modification.
3. **Step 3: Fix & Reconcile:**
   - **If the manual change was unauthorized/accidental:** Run `terraform apply` to overwrite the manual drift and restore the desired configuration defined in Git.
   - **If the manual change was an approved emergency hotfix:** Update the staging `.tf` code to incorporate the change and run `terraform apply` to cleanly synchronize state.
</details>

<details>
<summary><strong>● If a 'terraform apply' fails midway while deploying to a production environment, how would you recover from that?</strong></summary>

**Answer:**
1. **Understand Terraform State Realities:**
   Terraform apply operations are **non-atomic**. Resources created before the failure occurred **exist in AWS and in the state file**.
2. **Check State Lock:** Ensure the lock was released cleanly; if dangling, verify no runner is running and run `terraform force-unlock`.
3. **Diagnose the Failure:** Read the exact error (e.g. subnet CIDR overlap, IAM role propagation delay, missing dependency).
4. **Clean up Tainted Resources:** If a resource was partially initialized, Terraform marks it as `tainted`. On the next run, Terraform will destroy and recreate the tainted resource automatically.
5. **Re-run Apply (Idempotency):** Fix the code or cloud constraint and re-run `terraform apply`. Because Terraform is idempotent, it will skip all previously created resources and only provision the remaining missing pieces.
</details>

<details>
<summary><strong>● Can you explain the Terraform lifecycle block and its components?</strong></summary>

**Answer:**
The `lifecycle` meta-argument is placed inside a resource block to customize how Terraform creates, updates, and destroys that specific resource:

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.medium"

  lifecycle {
    create_before_destroy = true
    prevent_destroy       = true
    ignore_changes        = [tags["LastUpdated"], user_data]
    replace_triggered_by  = [aws_security_group.web.id]
  }
}
```

1. **`create_before_destroy = true`:**
   Normally, when a resource replacement is required, Terraform destroys the existing resource first, then creates the new one (causing downtime). This flag reverses the order: it creates the new replacement resource *first*, verifies it is healthy, and only then destroys the old one. Essential for zero-downtime ALB target groups and Auto Scaling launch templates.
2. **`prevent_destroy = true`:**
   A safety guard that rejects any plan that would destroy the resource. Protects critical production databases, S3 buckets, and KMS keys.
3. **`ignore_changes = [...]`:**
   Instructs Terraform to ignore modifications to specified attributes made outside of Terraform (e.g. ignoring tag updates added by external compliance scanners or auto-scaling replica adjustments).
4. **`replace_triggered_by = [...]`:**
   Forces resource replacement whenever a referenced resource or attribute changes.
</details>

<details>
<summary><strong>● Have you worked with Ansible?</strong></summary>

**Answer:**
Yes. I have used Ansible for configuration management, server orchestration, OS baseline hardening (CIS benchmarks), software installation, and orchestrating multi-node rolling updates across EC2 fleets.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Have you hosted any application using AWS EC2?</strong></summary>

**Answer:**
Yes. I have designed and deployed production applications on EC2 using both standalone setups and high-availability auto-scaled architectures:
- Deployed stateless web tiers in private subnets across 3 Availability Zones fronted by an **AWS Application Load Balancer (ALB)**.
- Integrated **EC2 Auto Scaling Groups (ASGs)** with Target Tracking policies based on CPU and ALB request count per target.
- Hardened instances using custom Golden AMIs built with Packer, with automated health checks, SSM Agent management, and CloudWatch logging.
</details>

<details>
<summary><strong>● Can you explain the difference between AWS Security Groups and Network ACLs (NACLs)?</strong></summary>

**Answer:**
Security Groups and Network ACLs provide defense-in-depth networking security inside AWS VPCs, operating at different layers:

| Feature | Security Group (SG) | Network ACL (NACL) |
| :--- | :--- | :--- |
| **Operating Layer** | **Instance / ENI Level** (Virtual firewall for individual EC2/RDS instances). | **Subnet Level** (Boundary firewall for the entire subnet). |
| **State Tracking** | **Stateful:** If an inbound request is permitted, response traffic is automatically allowed outbound, regardless of outbound rules. | **Stateless:** Return traffic is NOT automatically allowed; explicit outbound rules must permit traffic to ephemeral ports (1024–65535). |
| **Rule Types Supported** | Supports **Allow rules only** (cannot explicitly create Deny rules). | Supports both **Allow and Deny rules**. |
| **Rule Evaluation** | All rules are evaluated as a whole before deciding to allow traffic. | Rules are evaluated in **strict numerical order** (lowest rule number processed first; first match wins). |
| **Default Association** | Each instance can have up to 5 Security Groups attached. | Exactly **one** NACL is associated with each subnet. |
| **Common Use Case** | Restricting port 443 to ALB, or port 5432 to web application SG. | Blocking specific malicious IP addresses/CIDRs (`Deny 203.0.113.5/32`). |
</details>

<details>
<summary><strong>● Can you explain what an AWS Transit Gateway is and how it is used?</strong></summary>

**Answer:**
**AWS Transit Gateway (TGW)** is a regional, highly scalable network transit hub (a cloud router) that simplifies interconnectivity between Amazon VPCs, AWS accounts, and on-premises networks (via Site-to-Site VPN or AWS Direct Connect).

```
+-----------------------------------------------------------------------------------+
| AWS TRANSIT GATEWAY (Central Hub-and-Spoke Cloud Router)                          |
|                                                                                   |
|           +-----------------------+-----------------------+                       |
|           |                       |                       |                       |
|           v                       v                       v                       |
|    [ VPC A: Web ]          [ VPC B: App ]          [ VPC C: DB ]                  |
|    (10.1.0.0/16)           (10.2.0.0/16)           (10.3.0.0/16)                  |
|                                   ^                                               |
|                                   |                                               |
|           +-----------------------+-----------------------+                       |
|           |                                               |                       |
|           v                                               v                       |
|  [ Direct Connect Gateway ]                     [ Corporate On-Prem ]             |
+-----------------------------------------------------------------------------------+
```

**Why It Is Used (Hub-and-Spoke vs. Full-Mesh Peering):**
- **Eliminates VPC Peering Complexity:** Connecting 10 VPCs with peering requires 45 individual peering connections ($N \times (N-1) / 2$). With Transit Gateway, each VPC connects once to the TGW (10 attachments).
- **Centralized Routing & Segmentation:** Uses multiple TGW route tables to segment environments (e.g. preventing Dev VPC from routing to Prod VPC).
- **Transit Gateway Peering:** Enables peering across different AWS regions for global corporate interconnectivity.
</details>

#### 【 SECURITY 】

<details>
<summary><strong>● If you notice that secrets are visible in Terraform state files, how would you secure them?</strong></summary>

**Answer:**
Terraform state files must store the attributes of managed resources in JSON, which often includes sensitive values (database passwords, private keys). Securing this requires a defense-in-depth approach:

1. **Lock Down the Remote State Storage:**
   - Store state in **Amazon S3** with **Server-Side Encryption via AWS KMS Customer Managed Keys (CMKs)**.
   - Enforce strict IAM policies allowing only the CI/CD deployment role to read the state bucket.
   - Enforce TLS in transit (`aws:SecureTransport: true`).
2. **Decouple Secrets from Terraform HCL:**
   - Never hardcode plaintext passwords in `.tf` or `.tfvars` files.
   - Generate passwords dynamically inside cloud services using **AWS Secrets Manager** (`resource "aws_secretsmanager_secret"`) with automated rotation.
   - In Kubernetes, use **External Secrets Operator (ESO)** to sync secrets from AWS Secrets Manager directly into Kubernetes Secrets at runtime without passing through Terraform state.
3. **Mark Outputs as Sensitive:**
   - Use the `sensitive = true` attribute on outputs to prevent values from displaying in CLI logs or CI/CD console output:
     ```hcl
     output "db_password" {
       value     = aws_db_instance.db.password
       sensitive = true
     }
     ```
</details>

<details>
<summary><strong>● If a developer mistakenly pushed AWS keys or secrets to a Git repository, what would be the immediate response to address this?</strong></summary>

**Answer:**
A compromised credential requires executing an **Emergency Incident Response Playbook** immediately:

```
Step 1: Deactivate IAM Key IMMEDIATELY -> Step 2: Audit CloudTrail -> Step 3: Issue New Key -> Step 4: Purge Git History -> Step 5: Enforce Guardrails
```

1. **Step 1: Deactivate the IAM Access Key Immediately (Do NOT wait to edit Git!):**
   - Public GitHub repositories are continuously scraped by automated malicious bots within 10–30 seconds.
   - Immediately log into the AWS Console or use AWS CLI to **deactivate / delete the exposed Access Key**:
     ```bash
     aws iam update-access-key --access-key-id <EXPOSED_KEY_ID> --status Inactive --user-name <username>
     ```
2. **Step 2: Audit AWS CloudTrail for Unauthorized Activity:**
   - Query CloudTrail events filtering by the compromised `access_key_id` over the last 24–48 hours:
     - Check for newly created IAM users, roles, or access keys (backdoors).
     - Check for newly launched high-CPU EC2 instances (cryptominers).
     - Check for S3 bucket enumeration or unauthorized data downloads.
3. **Step 3: Issue New Credentials:**
   - Generate a new access key for the developer and transmit it via a secure channel (e.g. 1Password / Vault).
4. **Step 4: Purge Secret from Git Repository History:**
   - Making a new commit removing the secret does NOT remove it from commit history!
   - Use **`git-filter-repo`** or **BFG Repo-Cleaner** to purge the secret from all historic commits:
     ```bash
     git filter-repo --replace-text expressions.txt
     git push origin --force --all
     ```
5. **Step 5: Enforce Shift-Left Preventative Guardrails:**
   - Install **pre-commit hooks** with **TruffleHog** or **detect-secrets** on developer machines.
   - Enable **GitHub Secret Scanning** and **Push Protection**, which blocks pushes containing recognized API key patterns before they leave the developer's workstation.
</details>

<details>
<summary><strong>● How do you manage secrets within Jenkins pipelines?</strong></summary>

**Answer:**
Managing secrets securely inside Jenkins pipelines follows three best practices:

1. **Jenkins Built-In Credentials Manager:**
   - Store secrets under `Manage Jenkins -> Credentials` as **Secret text**, **Username with password**, or **Secret file**. Credentials are encrypted on disk using an AES master key.
2. **Declarative Pipeline Binding (`withCredentials`):**
   - Bind credentials safely to environment variables in pipeline scripts:
     ```groovy
     stage('Deploy') {
         steps {
             withCredentials([string(credentialsId: 'sonar-api-token', variable: 'SONAR_TOKEN')]) {
                 sh 'mvn sonar:sonar -Dsonar.login=$SONAR_TOKEN'
             }
         }
     }
     ```
   - **Automatic Log Masking:** Jenkins automatically intercepts console output and replaces any occurrence of `$SONAR_TOKEN` with `****`.
3. **Enterprise HashiCorp Vault / AWS Secrets Manager Integration:**
   - For enterprise environments, integrate Jenkins with **HashiCorp Vault** using AppRole or JWT authentication, injecting short-lived, dynamically rotated credentials directly into the runner memory.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you briefly introduce yourself and describe your professional background?
</details>
</details>

<details open>
<summary><h2>🏢 Photon</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

*Date: 05-08-2026 09:08 PM*

#### 【 CI/CD 】

<details>
<summary><strong>↳ Follow-up: Can you elaborate specifically on your deployment process and the DevOps implementation you have set up for this project?</strong></summary>

**Answer:**
In our current architecture, we implemented a modern, automated **GitOps-driven continuous delivery model** connecting GitHub, Jenkins, AWS ECR, and Argo CD targeting Amazon EKS:

```
[ Feature PR / Merge ] -> [ Jenkins CI Pipeline ]
                                  ├── Linting, Unit Testing & Code Coverage (>80%)
                                  ├── SAST: SonarQube Quality Gate
                                  ├── Container Build & Hardening (Multi-stage)
                                  ├── Security Scan: Trivy (Fail on CRITICAL CVEs)
                                  └── Push Image to AWS ECR with Git Commit SHA tag
                                               |
                                (Git Bot updates image tag in GitOps Repo)
                                               v
[ GitOps Manifest Repo ] <-----[ Argo CD Continuous Reconciliation ]
                                               |
                     +-------------------------+-------------------------+
                     |                                                   |
                     v                                                   v
         [ Staging Namespace ]                               [ Production Canary Rollout ]
         - Auto-sync on commit                               - Argo Rollouts (10% -> 100%)
         - Automated Cypress E2E Tests                       - Automated Prometheus Analysis
```

1. **Continuous Integration (CI):**
   - Every pull request triggers an ephemeral Jenkins Kubernetes pod agent that executes unit tests, SonarQube quality gates, and Trivy container vulnerability scans.
   - Upon merging to `main`, the container is built using Docker BuildKit, tagged with the Git commit SHA, and pushed to Amazon ECR.
2. **GitOps Handoff:**
   - The CI pipeline updates the deployment repository (`k8s-manifests`) with the new image tag commit.
3. **Continuous Delivery (CD):**
   - **Argo CD** detects the Git repository update and synchronizes the staging environment.
   - After automated smoke tests pass, production promotion is initiated via **Argo Rollouts** performing progressive canary traffic shifting.
</details>

<details>
<summary><strong>↳ Follow-up: Are you using tools like Argo CD or Flux for continuous deployment/GitOps in your setup?</strong></summary>

**Answer:**
Yes, **Argo CD** is our primary GitOps continuous delivery platform for all Kubernetes workloads.

**Why We Chose Argo CD:**
1. **Declarative GitOps Engine:** Continuously compares live cluster state against the desired state declared in Git, providing automated drift detection and automated self-healing.
2. **Application & ApplicationSet CRDs:** We use `ApplicationSet` to manage templated deployments across multiple clusters and environments from a single repository.
3. **Native Progressive Delivery (Argo Rollouts):** Seamless integration with Argo Rollouts for automated canary and blue-green deployments with automated metric analysis.
4. **Security & Single Sign-On:** Native support for Okta/Azure AD OIDC authentication and granular Kubernetes role-based access control (RBAC).
</details>

<details>
<summary><strong>↳ Follow-up: Are you familiar with the concept of GitOps?</strong></summary>

**Answer:**
Yes. **GitOps** is an operational paradigm for cloud-native applications where **Git is the single source of truth** for both declarative infrastructure and application deployment manifests.

**The Four Principles of GitOps (OpenGitOps Standard):**
1. **Declarative State:** The entire desired state of the system is described declaratively (using Kubernetes YAML, Helm, Kustomize, or Terraform).
2. **Versioned and Immutable:** State is stored in version control (Git), creating a complete, tamper-proof audit trail where every change is an immutable commit.
3. **Pulled Automatically:** Software agents running *inside* the target environment (e.g. Argo CD or Flux) continuously pull and reconcile state, eliminating the need to expose cluster API credentials to external CI runners.
4. **Continuously Reconciled:** The system continuously monitors runtime state. If an operator makes an unauthorized manual change via `kubectl`, the GitOps operator detects the drift and either alerts or automatically overwrites the change back to the desired Git state.
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● As a DevOps engineer, if you wanted to create a minimal-sized Docker image containing your application code that is portable and deployable across all environments, what steps would you take to achieve that?</strong></summary>

**Answer:**
Creating a minimal, secure, and portable Docker container image follows a disciplined 6-point engineering playbook:

```dockerfile
# STAGE 1: Build & Compilation Environment
FROM golang:1.22-alpine AS builder
WORKDIR /app
# 1. Optimize layer caching by copying dependencies first
COPY go.mod go.sum ./
RUN go mod download
COPY . .
# 2. Compile static binary without CGO dependencies
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o myapp .

# STAGE 2: Minimal Distroless Runtime Environment
FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /app
# 3. Copy only the compiled artifact from the builder
COPY --from=builder /app/myapp .
# 4. Run as non-root user
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/app/myapp"]
```

**Key Architectural Steps:**
1. **Multi-Stage Builds:** Discard compilers, build tools, source code, and package manager caches from the final image, copying only the compiled binary.
2. **Minimal Hardened Base Image:** Use **Google Distroless** (`gcr.io/distroless/static`), **Chainguard**, or **Alpine Linux**. This reduces image size from 1 GB down to **< 20 MB** and eliminates shell binaries (`/bin/sh`), drastically shrinking the attack surface.
3. **Run as Unprivileged User:** Enforce `USER 10001:10001` or `USER nonroot`. Never run containers as root in production!
4. **Optimize Layer Caching:** Order instructions from least frequently changed to most frequently changed (`COPY package.json` -> `RUN npm install` -> `COPY app code`).
5. **Leverage `.dockerignore`:** Exclude `.git`, `.github`, local documentation, tests, secrets, and temporary files.
6. **Compile with Optimization Flags:** Strip debug symbols and symbol tables (e.g. `-ldflags="-w -s"` in Go) to shave off an extra 20–30% of binary size.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>↳ Follow-up: What deployment strategy have you been following for releasing application updates in your Kubernetes environment?</strong></summary>

**Answer:**
We employ different deployment strategies depending on service criticality:

1. **Canary Deployment via Argo Rollouts (Production Critical Services):**
   - Routes a small slice of live production traffic (e.g., 10%) to the new revision.
   - Evaluates real-time Prometheus analysis metrics: HTTP 5xx error rate < 0.1%, p99 latency < 250ms.
   - Progressively shifts traffic (10% -> 25% -> 50% -> 100%) over a 45-minute window with instant automated rollback if metrics degrade.
2. **RollingUpdate (Standard Internal Microservices):**
   - Configured with `maxSurge: 25%` and `maxUnavailable: 0` to ensure zero downtime while replacing pods.
3. **Blue/Green Deployment (Major API Upgrades / Database Changes):**
   - Deploys the complete new version (Green) alongside the active version (Blue).
   - Executes automated smoke tests against the Green service before switching the production Service selector to Green instantly.
</details>

<details>
<summary><strong>↳ Follow-up: How many Kubernetes clusters have you been managing/handling?</strong></summary>

**Answer:**
In our current infrastructure, I manage a fleet of **5 Amazon EKS clusters** distributed across two AWS regions:
- `mgmt-cluster-useast1`: Centralized platform management (Argo CD, Vault, Harbor, Jenkins agents).
- `dev-cluster-useast1`: Multi-tenant development environment with automated ephemeral preview namespaces.
- `qa-cluster-useast1`: QA, load, and automated regression testing.
- `prod-primary-useast1`: Active primary production cluster handling live customer traffic.
- `prod-secondary-uswest2`: Standby production cluster in a secondary region for disaster recovery and geo-redundancy.
</details>

<details>
<summary><strong>↳ Follow-up: Do you use one Kubernetes cluster per environment, or how is your cluster setup organized?</strong></summary>

**Answer:**
We follow a **hybrid multi-cluster architecture**:
- **Environment Isolation:** We maintain **dedicated, separate clusters for Production vs. Non-Production**. Production clusters reside in dedicated AWS accounts and dedicated VPCs, ensuring complete physical blast-radius isolation, distinct IAM access boundaries, and SOC2/PCI-DSS compliance.
- **Namespace Isolation (Non-Prod):** Within our Non-Production clusters, we utilize namespace-level logical multi-tenancy for `dev`, `feature-branches`, and `integration` testing, governed by strict `ResourceQuotas` and `NetworkPolicies`.
</details>

<details>
<summary><strong>↳ Follow-up: How many environments (e.g., dev, staging, prod) do you have in your setup?</strong></summary>

**Answer:**
We operate four distinct environments:
1. **Development (`dev`):** Fast-paced environment for developer integration and automated PR previews.
2. **Quality Assurance (`qa`):** Dedicated to automated regression testing, integration testing, and performance profiling.
3. **Staging (`staging`):** Exact 1:1 replica of production used for pre-release validation and load testing.
4. **Production (`prod`):** Live customer-facing environment with strict change governance and multi-AZ high availability.
</details>

<details>
<summary><strong>↳ Follow-up: If you have three namespaces within a single Kubernetes cluster, how does that setup work?</strong></summary>

**Answer:**
Operating multiple environments (e.g. `dev`, `qa`, `staging`) as namespaces within a shared cluster requires robust logical multi-tenancy controls:

1. **Resource Governance (Quotas & LimitRanges):**
   - Each namespace is assigned a **`ResourceQuota`** setting hard ceilings on CPU, memory, and storage to prevent a rogue application in `dev` from starving `staging`.
   - A **`LimitRange`** enforces default resource requests and limits on every container.
2. **Network Segmentation (`NetworkPolicy`):**
   - By default, Kubernetes allows all cross-namespace traffic. We apply default-deny **Calico NetworkPolicies** so pods in the `dev` namespace cannot probe or communicate with pods in `staging`.
3. **Role-Based Access Control (RBAC):**
   - Developers are granted `edit` RoleBindings in the `dev` namespace, but only `view` permissions in `staging`.
4. **Ingress & DNS Routing:**
   - Ingress controllers route external traffic based on subdomains (`api.dev.company.com` -> `dev` namespace service; `api.staging.company.com` -> `staging` namespace service).
</details>

<details>
<summary><strong>↳ Follow-up: Can you confirm \- do you operate with only a single Kubernetes cluster?</strong></summary>

**Answer:**
**Clarification:** No, we do **NOT operate with only a single Kubernetes cluster**.

Relying on a single cluster for all workloads is an anti-pattern for enterprise production. A cluster-level failure (such as an API server freeze, CNI subnet exhaustion, or a corrupted control plane upgrade) would cause an outage across development, testing, and production simultaneously. We strictly separate our production environments into dedicated clusters.
</details>

<details>
<summary><strong>↳ Follow-up: Can you confirm you have dev, staging, and production namespaces within that single cluster?</strong></summary>

**Answer:**
**Clarification:** No. In our production architecture, **Production does not share a cluster with Dev and Staging**.
- Dev and QA share a non-production cluster utilizing namespace segmentation.
- Staging and Production run on **dedicated, physically separated clusters** in isolated AWS accounts to ensure absolute security, independent scaling, and zero noisy-neighbor risk for live users.
</details>

<details>
<summary><strong>● Can you explain what a CrashLoopBackOff error is in Kubernetes and how you would troubleshoot it?</strong></summary>

**Answer:**
`CrashLoopBackOff` is a pod state indicating that a container started, exited or crashed abnormally, and Kubernetes is repeatedly attempting to restart it with an exponential backoff delay ($10\text{s}, 20\text{s}, 40\text{s}, \dots, 300\text{s}$).

**Root Causes & Diagnostic Commands:**
1. **Check Exit Code:**
   ```bash
   kubectl describe pod <pod-name> -n <ns>
   ```
   - **Exit Code 137:** Process killed by Linux kernel OOM-killer (Out of Memory).
   - **Exit Code 1:** Application fatal exception (e.g. database connection refused, syntax error).
   - **Exit Code 127:** Command not found (misconfigured Dockerfile `ENTRYPOINT`).
2. **Inspect Previous Logs:**
   ```bash
   kubectl logs <pod-name> -n <ns> --previous
   ```
   Crucial because standard logs may be empty if the container just terminated.
3. **Inspect Configuration & Secret References:**
   Verify if referenced ConfigMaps or Secrets are missing or misnamed.
4. **Check Liveness / Startup Probes:**
   If a heavy application takes 40s to boot but the liveness probe starts checking after 10s, Kubernetes repeatedly kills the booting container.
</details>

<details>
<summary><strong>● Can you explain the role of a service mesh (such as Istio) in a Kubernetes environment?</strong></summary>

**Answer:**
A **Service Mesh** (like **Istio** or **Linkerd**) is a dedicated infrastructure layer that manages service-to-service (East-West) network communication within a Kubernetes cluster using high-performance sidecar proxies (**Envoy**) injected alongside each pod.

```
[ Pod A ]                                    [ Pod B ]
+-------------------------+                  +-------------------------+
| [ App Container ]       |                  | [ App Container ]       |
|       | (localhost)     |                  |       ^ (localhost)     |
|       v                 |                  |       |                 |
| [ Envoy Proxy Sidecar ] |--(Mutual TLS)--->| [ Envoy Proxy Sidecar ] |
+-------------------------+ (Encrypted/Auth) +-------------------------+
```

**The Three Pillars of a Service Mesh:**
1. **Traffic Management:**
   - Dynamic traffic routing, canary traffic splitting (e.g. 90% v1 / 10% v2 via `VirtualService`), circuit breaking, retries, and fault injection without touching application code.
2. **Zero-Trust Security & Encryption:**
   - Enforces **automatic mutual TLS (mTLS)** across all pod communication with cryptographic identity verification (SPIFFE IDs).
   - Granular access control using `AuthorizationPolicy` (e.g., only `payment-service` can call `billing-db`).
3. **Deep Observability:**
   - Generates uniform golden signals (latency, error rates, requests per second) for all microservices and automatically propagates headers for distributed tracing (Jaeger/Zipkin).
</details>

<details>
<summary><strong>● Which tool or managed service are you using to manage your Kubernetes cluster?</strong></summary>

**Answer:**
We use **Amazon EKS (Elastic Kubernetes Service)** managed declaratively using **Terraform** via the official community module `terraform-aws-modules/eks`.

For day-to-day operations and cluster scaling:
- **Node Management & Autoscaling:** **Karpenter** for fast, just-in-time node provisioning directly via the AWS Fleet API, alongside EKS Managed Node Groups.
- **GitOps Orchestration:** **Argo CD** for declarative deployment synchronization.
- **Cluster Observability:** Prometheus Operator (`kube-prometheus-stack`) and Grafana.
</details>

<details>
<summary><strong>● Can you explain Kubernetes CNI network plugins such as Calico and Flannel and their role in cluster networking?</strong></summary>

**Answer:**
A **Container Network Interface (CNI)** plugin is responsible for inserting network interfaces into container network namespaces, allocating unique IP addresses (IPAM), and establishing packet routing between pods across physical cluster nodes.

**Comparison of Leading CNIs:**

| CNI Plugin | Networking Mechanism | NetworkPolicy Support | Best Production Use Case |
| :--- | :--- | :---: | :--- |
| **Flannel** | Simple Layer 3 overlay network (typically VXLAN encapsulation). | **NO** (No security filtering). | Lightweight, basic clusters where network security is managed externally. |
| **Calico** | High-performance overlay (VXLAN/IPIP) or native BGP routing. | **YES (Advanced)** | Enterprise clusters requiring strict zero-trust security and granular Layer 3/4 network policies. |
| **AWS VPC CNI (`aws-node`)** | Native AWS VPC networking (allocates real VPC secondary IPs via ENIs). | Requires Calico or native EKS Network Policy. | **EKS Standard:** Wire-speed throughput without packet encapsulation overhead; direct VPC routability. |
</details>

<details>
<summary><strong>● Suppose you have multiple services running in your Kubernetes cluster and one service is not reachable from another namespace within the cluster \- what could be the possible causes of this issue and how would you troubleshoot it?</strong></summary>

**Answer:**
A systematic diagnostic workflow:

1. **Step 1: Check DNS Resolution & FQDN:**
   - The connecting pod must use the full FQDN: `<service-name>.<namespace>.svc.cluster.local:<port>`.
   - Test CoreDNS resolution from inside the cluster:
     ```bash
     kubectl run netshoot --rm -it --image=nicolaka/netshoot -- nslookup <service>.<target-ns>.svc.cluster.local
     ```
2. **Step 2: Check Service Selector and Endpoints:**
   - Verify that the target Service actually selects live pods:
     ```bash
     kubectl get endpoints <service-name> -n <target-namespace>
     ```
   - If `Endpoints` shows `<none>`, the Service's `spec.selector` labels do not match the Pod's `metadata.labels`.
3. **Step 3: Check NetworkPolicies (Primary Culprit):**
   - Inspect network policies in the target namespace:
     ```bash
     kubectl get netpol -n <target-namespace>
     ```
   - If a default-deny ingress policy exists without an explicit rule allowing traffic from the source namespace, traffic will be silently dropped.
4. **Step 4: Verify Container Listening Port & Binding:**
   - Verify that the target pod container is actually listening on `0.0.0.0` (all interfaces) rather than `127.0.0.1` (localhost only).
5. **Step 5: Check Service Mesh (mTLS) Policies:**
   - If Istio is active, check if `PeerAuthentication` enforces `STRICT` mTLS while the calling client is not part of the mesh.
</details>

<details>
<summary><strong>● You mentioned using Helm charts for deployment \- how would you manage different environments (like dev, staging, prod) using Helm?</strong></summary>

**Answer:**
We manage multi-environment deployments using a **Single Standardized Base Chart with Environment-Specific Values Files**:

```
helm/microservice-chart/
├── Chart.yaml
├── values.yaml               # Default baseline configuration
├── values-dev.yaml           # Dev overrides: replicas: 1, low CPU/RAM, ingress: dev.internal
├── values-staging.yaml       # Staging overrides: replicas: 2, staging DB endpoints
└── values-prod.yaml          # Prod overrides: replicas: 5, HPA enabled, Multi-AZ, PDB
```

**Deployment Command:**
```bash
helm upgrade --install payment-svc ./helm/microservice-chart \
  -f ./helm/microservice-chart/values.yaml \
  -f ./helm/microservice-chart/values-prod.yaml \
  --namespace production \
  --set image.tag=${GIT_COMMIT} \
  --atomic
```
*In GitOps, Argo CD Application manifests point to the same Helm chart repository while specifying the target environment's values file (`values-prod.yaml`).*
</details>

<details>
<summary><strong>● Can you explain what a Pod Disruption Budget is in Kubernetes and how it is used?</strong></summary>

**Answer:**
A **Pod Disruption Budget (PDB)** (`policy/v1`) is an API object that guarantees high availability by limiting the number of pods of a replicated service that can be simultaneously taken down during **voluntary disruptions**.

**Voluntary vs. Involuntary Disruptions:**
- *Involuntary Disruptions (PDB cannot prevent):* Hardware failure, kernel panic, hypervisor crash.
- *Voluntary Disruptions (PDB regulates):* `kubectl drain`, node OS patching, cluster autoscaler scale-down, EKS control plane upgrades.

**Example PDB Manifest:**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: payment-pdb
  namespace: production
spec:
  minAvailable: 2 # Ensures at least 2 pods remain alive at all times during node maintenance
  selector:
    matchLabels:
      app: payment-service
```
When an engineer runs `kubectl drain`, the Kubernetes Eviction API checks the PDB. If evicting a pod would violate `minAvailable`, the eviction is blocked until replacement pods become healthy.
</details>

<details>
<summary><strong>● If one of your services in the cluster is experiencing high latency, how would you go about troubleshooting it?</strong></summary>

**Answer:**
1. **Distributed Tracing (OpenTelemetry / Jaeger):** Inspect trace flamegraphs to isolate the exact bottleneck: is the delay in external HTTP APIs, database query execution, or in-process serialization?
2. **Check for CPU Throttling:** Check PromQL `rate(container_cpu_cfs_throttled_periods_total[5m])`. Overly restrictive CPU limits cause Linux cgroups CFS throttling, drastically spiking latency without crashing the pod.
3. **CoreDNS Latency & Search Domains:** Inspect DNS query latencies. Misconfigured `ndots:5` settings in Linux `/etc/resolv.conf` can add 4 sequential failed queries before resolving external domains. Deploy **NodeLocal DNSCache**.
4. **Database Connection Pool Saturation:** Check if application threads are blocked waiting for an available connection from the pool.
5. **Network Packet Drops:** Inspect `kubectl top nodes` and CNI metrics for saturated host interfaces.
</details>

<details>
<summary><strong>● Would you be able to write some Kubernetes YAML code for me right now to demonstrate?</strong></summary>

**Answer:**
Yes, absolutely. I write and review Kubernetes manifests daily. I can construct complete, production-grade Deployment, Service, Ingress, HPA, and PDB manifests.
</details>

<details>
<summary><strong>↳ Follow-up: Can you write a Kubernetes Deployment YAML file that includes resource limits/requests and specifies three replicas?</strong></summary>

**Answer:**
Here is a production-hardened Deployment manifest incorporating 3 replicas, resource requests/limits, zero-downtime rolling update strategy, health probes, and security context:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  namespace: production
  labels:
    app.kubernetes.io/name: payment-service
    app.kubernetes.io/part-of: checkout-platform
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Allows 1 extra pod during rollout (4 total)
      maxUnavailable: 0  # Guarantees all 3 replicas remain available at all times
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      # Pod Anti-Affinity: Spreads replicas across different physical worker nodes
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values: ["payment-service"]
              topologyKey: "kubernetes.io/hostname"

      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        fsGroup: 10001

      containers:
      - name: app
        image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/payment-service:v2.4.1
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8080
          name: http

        resources:
          requests:
            cpu: "250m"      # 0.25 CPU cores guaranteed
            memory: "512Mi"  # 512 MB RAM guaranteed
          limits:
            cpu: "1000m"     # 1 CPU core maximum
            memory: "1Gi"    # 1 GB RAM maximum (OOMKilled if exceeded)

        # Health Probes
        readinessProbe:
          httpGet:
            path: /healthz/ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 3

        livenessProbe:
          httpGet:
            path: /healthz/live
            port: 8080
          initialDelaySeconds: 20
          periodSeconds: 10
          failureThreshold: 3
```
</details>

#### 【 IAC 】

<details>
<summary><strong>● Do you have experience using Ansible?</strong></summary>

**Answer:**
Yes. I have used Ansible extensively for OS configuration management, CIS benchmark security baselines, patch management, application deployment on standalone EC2 instances, and automated AMI provisioning in tandem with HashiCorp Packer.
</details>

<details>
<summary><strong>↳ Follow-up: What are handlers in Ansible, and how are they used within Ansible playbooks?</strong></summary>

**Answer:**
In Ansible, **Handlers** are special tasks that only execute when triggered by a **`notify`** directive from another task that has successfully resulted in a state change (`changed: true`).

**Key Architectural Behaviors:**
1. **Idempotence & Batch Execution:** Handlers run **only once at the very end of the play**, regardless of how many tasks notified them.
2. **Classic Production Use Case:** Restarting a service (like Nginx, SSH, or PostgreSQL) only when its configuration file is modified:
   ```yaml
   tasks:
   - name: Deploy Nginx Configuration
     ansible.builtin.template:
       src: nginx.conf.j2
       dest: /etc/nginx/nginx.conf
       validate: nginx -t -c %s
     notify: Restart Nginx Service

   handlers:
   - name: Restart Nginx Service
     ansible.builtin.systemd:
       name: nginx
       state: restarted
   ```
</details>

<details>
<summary><strong>● Do you have experience using Terraform?</strong></summary>

**Answer:**
Yes. I have over 5 years of experience authoring enterprise-grade, modular Terraform code to provision multi-account AWS environments, EKS clusters, networking foundations, and CI/CD pipelines with remote state locking and automated testing.
</details>

<details>
<summary><strong>↳ Follow-up: As a DevOps engineer, if you wanted to achieve a highly available architecture, what steps would you take (especially using Terraform)?</strong></summary>

**Answer:**
Using Terraform, I implement High Availability (HA) across all tiers by codifying the following architectural patterns:

1. **Multi-AZ Network Foundation:**
   ```hcl
   module "vpc" {
     source = "terraform-aws-modules/vpc/aws"
     azs    = ["us-east-1a", "us-east-1b", "us-east-1c"]
     enable_nat_gateway     = true
     single_nat_gateway     = false # Deploy redundant NAT Gateway in EACH AZ
     one_nat_gateway_per_az = true
   }
   ```
2. **Compute Redundancy across Availability Zones:**
   - Configure EKS node groups and Auto Scaling Groups to distribute instances across all 3 private subnets.
3. **Database High Availability:**
   - Provision `aws_rds_cluster` (Amazon Aurora) with Multi-AZ instances and automatic failover in < 30 seconds.
4. **Resilient Load Balancing:**
   - Provision `aws_lb` across all public subnets with cross-zone load balancing enabled.
</details>

<details>
<summary><strong>↳ Follow-up: How do you handle Terraform state management and securing the state file?</strong></summary>

**Answer:**
1. **Remote Backend:** Store state in Amazon S3 with **S3 Bucket Versioning** enabled for instant rollback and disaster recovery.
2. **State Locking:** Prevent concurrent execution using DynamoDB or native S3 locking (`use_lockfile = true` in Terraform 1.10+).
3. **Encryption:** Enforce server-side encryption with AWS KMS Customer Managed Keys (`aws:kms`) and enforce TLS in transit (`aws:SecureTransport: true`).
4. **Access Control:** Restrict read/write access to the state bucket strictly to the CI/CD execution IAM role.
5. **Output Masking:** Mark sensitive outputs with `sensitive = true`.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● Have you primarily worked with Azure or AWS as your cloud platform?</strong></summary>

**Answer:**
My primary expertise is in **Amazon Web Services (AWS)**, where I have architected large-scale enterprise platforms. I also possess working knowledge of **Microsoft Azure**, particularly in Azure Kubernetes Service (AKS), Azure VNets, and Microsoft Entra ID integration.
</details>

<details>
<summary><strong>↳ Follow-up: Have you used AWS Lambda functions in your work?</strong></summary>

**Answer:**
Yes. I have utilized AWS Lambda for event-driven serverless automation:
- Automating EBS snapshot backups and lifecycle cleanups.
- Triggering automated image resizing and asset processing pipelines from S3 events.
- Building custom AWS Config and CloudWatch EventBridge remediations (e.g. automatically shutting down non-compliant security groups).
- Forwarding application logs from CloudWatch to Elasticsearch/OpenSearch via Lambda stream processors.
</details>

<details>
<summary><strong>↳ Follow-up: If you wanted to reduce the cold start time/frequency for an AWS Lambda function, how would you go about doing that?</strong></summary>

**Answer:**
A 5-step engineering playbook to eliminate or minimize Lambda cold starts:

1. **Enable Provisioned Concurrency:**
   - Keeps a specified number of execution environments pre-warmed and initialized 24/7. Cold start latency drops from 2–5 seconds down to **< 15 milliseconds**.
2. **Optimize Runtime & Bundle Size:**
   - Use lightweight, fast-initializing runtimes (Node.js, Python, or compiled Go/Rust) instead of heavy JVM/Java runtimes.
   - Strip unused dependencies using tools like Webpack, esbuild, or ProGuard to keep bundle sizes under 10 MB.
3. **Allocate More Memory (CPU Scaling):**
   - In AWS Lambda, allocating more memory proportionally allocates more CPU cores. Increasing RAM from 128 MB to 1024 MB speeds up initialization code execution significantly.
4. **Optimize Initialization Code:**
   - Initialize database connection pools, AWS SDK clients, and heavy objects *outside* the event handler function (in global scope) so they are reused across warm invocations.
5. **Scheduled EventBridge Warmers (Low Cost Alternative):**
   - Configure an Amazon EventBridge rule to ping the Lambda function every 5 minutes with a lightweight `{ "warmer": true }` payload to keep execution environments active.
</details>

#### 【 SECURITY 】

<details>
<summary><strong>↳ Follow-up: How does Helm handle secrets management during deployments?</strong></summary>

**Answer:**
By default, native Helm converts values into standard Kubernetes `Secret` resources, which are only **base64-encoded, NOT encrypted**. Committing unencrypted values files to Git violates security compliance.

**Enterprise Secret Management Patterns for Helm:**
1. **External Secrets Operator (ESO - Recommended):**
   - Helm manifests deploy an `ExternalSecret` custom resource.
   - The ESO controller securely queries **AWS Secrets Manager** or **HashiCorp Vault** at runtime to fetch and inject the secret directly into a Kubernetes Secret inside the cluster. No secrets are stored in Git or Helm values!
2. **Helm-Secrets with Mozilla SOPS:**
   - Uses **SOPS** to encrypt sensitive fields in `secrets.yaml` using AWS KMS or PGP.
   - Encrypted files can be safely committed to Git. The Helm-Secrets plugin decrypts them on-the-fly during CI/CD execution (`helm secrets upgrade`).
3. **Sealed Secrets:**
   - Uses asymmetric encryption: developers encrypt secrets using a public key; only the in-cluster Sealed Secrets controller holds the private key to decrypt them.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Can you explain the architecture of your current project and how you implemented the DevOps approach for it?</strong></summary>

**Answer:**
In my recent engagement, I led the cloud-native platform architecture for a high-traffic fintech transaction platform:

```
[ AWS Cloud Platform Infrastructure ]
  - Multi-Account AWS Landing Zone (Core, Security, Staging, Prod) via Terraform
  - Multi-AZ VPC across 3 Availability Zones interconnected with AWS Transit Gateway
  - Amazon EKS Cluster (Managed Node Groups + Karpenter for dynamic autoscaling)
  - Amazon Aurora PostgreSQL (Multi-AZ with read replicas) + ElastiCache Redis

[ CI/CD & Delivery Platform ]
  - GitHub Actions CI: Ephemeral build agents, SonarQube SAST, Trivy CVE scanning
  - Immutable Container Images signed via Cosign and stored in Amazon ECR
  - Argo CD & Argo Rollouts: GitOps continuous delivery with automated canary analysis

[ Observability & Security ]
  - Prometheus Operator + Grafana: SLO/SLA dashboards, Golden Signals alerting
  - OpenTelemetry Collector: Distributed tracing across 30+ microservices
  - HashiCorp Vault: Dynamic secrets management with automated rotation
  - Calico: Zero-trust network policies enforcing namespace and pod isolation
```
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself and walk me through your professional background and past work experience?

<details>
<summary><strong>● Do you have any questions for me before we conclude the interview?</strong></summary>

**Answer:**
As a Senior DevOps candidate, I use this opportunity to evaluate the team's engineering maturity, operational health, and architectural vision:

1. **Deployment Cadence & Bottlenecks:**
   *"What does the team's current deployment cadence look like across services, and what is currently the biggest friction point between a pull request being merged and running in production?"*
2. **Platform Engineering & Developer Experience:**
   *"Is the organization moving toward an Internal Developer Platform (IDP) model with standardized golden paths, or do application squads currently manage their own pipeline manifests?"*
3. **Major Architectural Roadmap Priorities:**
   *"What are the major infrastructure and cloud reliability initiatives planned for the next 6 to 12 months (e.g., multi-region expansion, Kubernetes version upgrades, or FinOps cost optimization)?"*
4. **On-Call Culture & Operational Health:**
   *"How is on-call rotation structured between SRE and software engineering squads, and how actively does the engineering leadership support blameless postmortems and dedicated toil-reduction sprints?"*
</details>
</details>
</details>

<details open>
<summary><h2>🏢 Investcloud</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 CI/CD 】

<details>
<summary><strong>↳ Follow-up: Which system do you use to run your Terraform pipelines — do you use GitHub Actions, or something else?</strong></summary>

**Answer:**
In my recent projects, we have run Terraform automation primarily through **GitLab CI/CD** and **GitHub Actions**, supplemented by specialized IaC orchestration tooling like **Atlantis**:

- **GitHub Actions / GitLab CI Workflow:**
  - Authenticates to AWS via **OIDC (OpenID Connect)** without static access keys.
  - On Pull Requests: Runs `terraform fmt -check`, `tflint`, `checkov`, and `terraform plan`, posting a structured plan diff directly to the PR comments.
  - On Merge to `main`: Applies the saved plan file (`terraform apply tfplan`) through an automated job with required peer review gates.
- **Atlantis:** For GitOps-native pull request automation, where developers execute `atlantis plan` and `atlantis apply` directly via PR comment threads with automatic workspace locking.
</details>

<details>
<summary><strong>↳ Follow-up: Within your Jenkins pipeline, after the Terraform provisioning step completes, do you then have a subsequent step that runs Ansible?</strong></summary>

**Answer:**
Yes, in hybrid or VM-based provisioning workflows:
1. **Terraform Phase:** Provisions underlying AWS infrastructure (VPC, Security Groups, EC2 instances, EBS volumes).
2. **Handoff Step:** Upon successful apply, Terraform outputs the newly provisioned instance IDs and private IP addresses (`terraform output -json`).
3. **Ansible Phase:** The pipeline invokes Ansible using the **AWS EC2 Dynamic Inventory plugin (`aws_ec2.yml`)**, targeting instances by tags assigned during the Terraform run (e.g. `Role: AppServer`, `Env: Production`):
   ```groovy
   stage('Configure via Ansible') {
       steps {
           sh 'ansible-playbook -i inventories/aws_ec2.yml playbooks/app_config.yml'
       }
   }
   ```
*Modern Cloud-Native Alternative:* For immutable infrastructure, we prefer using **HashiCorp Packer with Ansible** to pre-bake hardened Golden AMIs *before* Terraform runs, eliminating post-provisioning configuration steps completely.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● If you needed to set up pod and node autoscaling for an application running on EKS, what are the main things you would need to configure to support that?</strong></summary>

**Answer:**
Autoscaling in Amazon EKS operates at two interdependent tiers: **Horizontal Pod Autoscaling (HPA)** and **Node Autoscaling (Karpenter / Cluster Autoscaler)**:

```
[ Application Traffic Spike ]
              |
              v
[ Horizontal Pod Autoscaler (HPA) ] ---> (Increases Pod Replicas: 3 -> 12)
              |
              v
[ Pods stuck in PENDING (Insufficient CPU/RAM) ]
              |
              v
[ Karpenter / Cluster Autoscaler ] ---> (Provisions new EC2 Worker Nodes via AWS API in <45s)
```

1. **Pod Horizontal Autoscaling (HPA):**
   - **Metrics Server:** Deploy the `metrics-server` add-on to expose core pod CPU and memory utilization metrics.
   - **Container Resource Requests:** **Mandatory.** Every pod container must define `resources.requests.cpu` and `memory`. HPA calculates scaling percentages based on requests.
   - **HPA Resource Definition:**
     ```yaml
     apiVersion: autoscaling/v2
     kind: HorizontalPodAutoscaler
     metadata:
       name: app-hpa
     spec:
       scaleTargetRef:
         apiVersion: apps/v1
         kind: Deployment
         name: my-app
       minReplicas: 3
       maxReplicas: 15
       metrics:
       - type: Resource
         resource:
           name: cpu
           target:
             type: Utilization
             averageUtilization: 70
     ```

2. **Node Autoscaling (Karpenter - Modern EKS Standard):**
   - Deploy the **Karpenter** controller with IAM Roles for Service Accounts (IRSA).
   - Configure **`NodePool`** and **`EC2NodeClass`** CRDs. Karpenter bypasses slow Auto Scaling Groups, watching for pending unscheduled pods and directly launching optimally-sized EC2 instances in under 45 seconds.
</details>

<details>
<summary><strong>● In a scenario where you have two applications with different compute needs (e.g., one CPU-heavy, one RAM-heavy) and you have separate node groups optimized for CPU and for RAM respectively, how would you configure things so that each application gets scheduled onto the correct node group?</strong></summary>

**Answer:**
To achieve bidirectional scheduling isolation—ensuring compute workloads only land on CPU nodes, and memory workloads only land on RAM nodes—you combine **Node Labels & Node Affinity** with **Taints & Tolerations**:

#### 1. Label and Taint the Node Groups:
- **Compute-Optimized Node Group (`c5.4xlarge`):**
  - Node Label: `node-type=compute-optimized`
  - Node Taint: `workload=compute:NoSchedule`
- **Memory-Optimized Node Group (`r5.4xlarge`):**
  - Node Label: `node-type=memory-optimized`
  - Node Taint: `workload=memory:NoSchedule`

#### 2. Configure the CPU-Heavy Application Deployment:
```yaml
spec:
  template:
    spec:
      tolerations:
      - key: "workload"
        operator: "Equal"
        value: "compute"
        effect: "NoSchedule"
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: node-type
                operator: In
                values: ["compute-optimized"]
```

#### 3. Configure the RAM-Heavy Application Deployment:
Follow the identical pattern, matching toleration `workload=memory` and affinity `node-type=memory-optimized`. Standard pods without tolerations will be rejected by both node groups!
</details>

<details>
<summary><strong>↳ Follow-up: You mentioned using kubectl to label nodes so pods get scheduled to the right node group. How do you ensure that when a new node is added due to autoscaling, it automatically receives the same labels?</strong></summary>

**Answer:**
**Crucial Operational Rule:** You **NEVER manually run `kubectl label node`** in production autoscaling environments, because manually applied labels are lost when instances scale down or new nodes are launched!

**How Labels and Taints Are Applied Automatically During Autoscaling:**

1. **At the AWS EKS Managed Node Group Level (Terraform):**
   Define labels and taints directly within the Terraform `aws_eks_node_group` configuration:
   ```hcl
   resource "aws_eks_node_group" "compute_fleet" {
     cluster_name    = var.cluster_name
     node_group_name = "compute-optimized"
     instance_types  = ["c5.4xlarge"]

     labels = {
       "node-type" = "compute-optimized"
     }

     taint {
       key    = "workload"
       value  = "compute"
       effect = "NO_SCHEDULE"
     }
   }
   ```
2. **Kubelet Node Registration Flag:**
   When an EC2 instance launches, the Auto Scaling Group executes the EKS bootstrap script (`/etc/eks/bootstrap.sh`), passing `--kubelet-extra-args '--node-labels=node-type=compute-optimized'`. When Kubelet registers the node with the API server, the labels are applied natively upon birth.
3. **In Karpenter:**
   Labels and taints are defined declaratively in the `NodePool` CRD spec (`spec.template.metadata.labels`), automatically tagging newly created nodes.
</details>

<details>
<summary><strong>● Given a scenario where you need to upgrade three EKS clusters (development, UAT, and production) by three minor versions each, what would your high-level project plan look like to go from the current state to completion, and what specific steps would you take within each cluster to perform the upgrade?</strong></summary>

**Answer:**
**Golden Rule:** Kubernetes **DOES NOT support skipping minor versions**! Upgrading three minor versions (e.g. v1.27 to v1.30) requires **three sequential single-version upgrade cycles: 1.27 -> 1.28 -> 1.29 -> 1.30**.

#### High-Level Project Plan (Phased Environment Rollout):
1. **Phase 1: Discovery & Deprecation Audit (Week 1):**
   - Run **Kube-no-trouble (`kubent`)** or Pluto across all clusters to identify deprecated APIs.
   - Update application Helm charts to support target API versions.
2. **Phase 2: Development Cluster Upgrades (Weeks 2–3):**
   - Execute the 3 upgrade hops sequentially (1.27 -> 1.28 -> 1.29 -> 1.30) in Development.
   - Validate CI/CD pipelines and developer workloads.
3. **Phase 3: UAT / Staging Cluster Upgrades (Week 4):**
   - Perform identical upgrades in UAT; execute full end-to-end regression and load tests.
4. **Phase 4: Production Cluster Upgrades (Weeks 5–6):**
   - Execute sequential upgrades during scheduled maintenance windows with rollbacks ready, or perform a **Blue-Green Cluster Migration**.

#### Step-by-Step Per-Cluster Upgrade Sequence (Repeated for each minor hop):
```
[ Step 1: Upgrade EKS Add-ons ] -> [ Step 2: Upgrade Control Plane ] -> [ Step 3: Rolling Upgrade Node Groups ] -> [ Step 4: Verify Health ]
```
1. **Step 1: Upgrade In-Cluster Add-ons:**
   - Update AWS EKS core add-ons to versions compatible with target minor release:
     - **VPC CNI (`aws-node`)**
     - **CoreDNS**
     - **`kube-proxy`**
     - **AWS EBS CSI Driver**
2. **Step 2: Upgrade EKS Control Plane:**
   - Update cluster version via Terraform: `cluster_version = "1.28"`.
   - AWS manages control plane API server and etcd upgrade with zero downtime.
3. **Step 3: Upgrade Worker Node Groups:**
   - For EKS Managed Node Groups, trigger a rolling update:
     ```bash
     aws eks update-nodegroup-version --cluster-name prod --nodegroup-name compute-nodes --kubernetes-version 1.28
     ```
   - EKS cordons and drains existing nodes gracefully, honoring **PodDisruptionBudgets (PDB)**, and replaces them with fresh AMIs.
4. **Step 4: Upgrade In-Cluster Controllers:**
   - Upgrade Karpenter, Argo CD, cert-manager, and Ingress controllers to compatible versions.
5. **Step 5: Verify & Proceed to Next Version:**
   - Confirm all pods are healthy (`kubectl get pods -A | grep -v Running`).
   - Proceed to the next minor version hop (1.28 -> 1.29).
</details>

#### 【 IAC 】

<details>
<summary><strong>● In your current role, would people come directly to you and ask for a new piece of Terraform code (for example, to build an EKS cluster), and would you be the one to design that Terraform solution from scratch yourself?</strong></summary>

**Answer:**
Yes, absolutely. As a Senior DevOps and Platform Engineer, I serve as the infrastructure architect and Subject Matter Expert (SME) for cloud automation:
- Engineering squads and product leads submit infrastructure requests through architectural RFCs or Jira platform tickets.
- I design and author modular, production-ready Terraform modules from scratch, baking in corporate networking topology (multi-AZ VPCs), IAM least-privilege security baselines, tag governance, encryption at rest, and automated backup lifecycles.
- I provide these modules as "Golden Paths" for teams to consume via our internal Terraform registry.
</details>

<details>
<summary><strong>↳ Follow-up: If you're consuming a Terraform module (such as a VPC module) from another repository and you need to change that module, how would you go about doing that?</strong></summary>

**Answer:**
Consuming and extending shared infrastructure modules follows standard software engineering versioning practices:

1. **Never Edit Locally in `.terraform/modules`:** Direct local edits are ephemeral and will be wiped out on the next `terraform init`.
2. **Branch the Source Module Repository:** Clone the module's Git repository and create a feature branch (`git checkout -b feature/add-firewall-subnets`).
3. **Implement Changes with Backward Compatibility:** Add the new features using optional variables with default values to ensure existing consumers are not broken.
4. **Test Thoroughly:** Write automated tests using **Terratest** or deploy into an isolated development sandbox.
5. **Open a Pull Request:** Submit a PR with documentation updates (`terraform-docs`).
6. **Semantic Release Tagging:** Once merged to `main`, release a new semantic version tag (e.g. `v2.4.0`).
7. **Consume in Downstream Projects:** Update the calling Terraform code to reference the new release:
   ```hcl
   module "vpc" {
     source = "git::https://github.com/company/terraform-aws-vpc.git?ref=v2.4.0"
   }
   ```
</details>

<details>
<summary><strong>↳ Follow-up: If you needed to modify a Terraform module beyond just changing input variables — for example, adding a network firewall to a VPC module — what steps would you take to actually edit the module itself?</strong></summary>

**Answer:**
1. **Branch the Module Codebase:** Create a working branch in the VPC module repo.
2. **Author New Resources:** Add the required HCL resource blocks:
   - `aws_networkfirewall_firewall`
   - `aws_networkfirewall_firewall_policy`
   - `aws_networkfirewall_rule_group`
   - Route table associations directing egress traffic through the firewall endpoints.
3. **Implement Feature Toggles (Non-Breaking Design):**
   Wrap the new resources in count/for_each blocks controlled by a boolean flag:
   ```hcl
   variable "enable_network_firewall" {
     type        = bool
     default     = false # Ensures existing consumers without firewalls are not impacted
     description = "Enable AWS Network Firewall in dedicated inspection subnets"
   }
   ```
4. **Expose Relevant Outputs:** Export firewall endpoints, ARNs, and routing status in `outputs.tf`.
5. **Validate & Test:** Run `terraform validate`, `tflint`, and execute a test deployment in a sandbox account.
6. **Publish Semantic Release:** Tag the repository with a new Minor version (`v2.5.0`) and update module documentation.
</details>

<details>
<summary><strong>↳ Follow-up: If you've already written a Terraform module and reused it across 10 different projects, and then you realize you need to add something new to that module, what would you do?</strong></summary>

**Answer:**
1. **Enforce Semantic Versioning (SemVer):**
   - If the new feature is additive and backward-compatible, release it as a **MINOR version** (e.g. `v1.3.0` -> `v1.4.0`).
   - If the change contains breaking changes (e.g. renamed required variables), release it as a **MAJOR version** (`v2.0.0`).
2. **Provide Safe Defaults:**
   - Ensure all new variables have default values (e.g. `default = false` or `default = null`) so the existing 10 projects can upgrade without syntax errors.
3. **Immutable Tag Pinning:**
   - Because the 10 existing projects pin their module sources to specific immutable Git tags (`?ref=v1.3.0`), **none of them are affected or broken** by the new release.
4. **Phased Migration:**
   - The project needing the new feature pins to `?ref=v1.4.0`. The remaining 9 projects can upgrade at their own pace during scheduled maintenance sprints.
</details>

<details>
<summary><strong>● Can you give me an example of something you've used Ansible for on a project?</strong></summary>

**Answer:**
I used Ansible to automate **CIS Benchmark Level 1 OS Hardening** across an enterprise fleet of 250+ Red Hat Enterprise Linux (RHEL) servers:
- Auditing and disabling legacy, unencrypted services (`telnet`, `rsh`, `ftp`).
- Hardening SSH daemon configuration (`/etc/ssh/sshd_config`): disabling root login, enforcing SSH protocol 2, setting idle timeout intervals, and enforcing key-based authentication.
- Configuring kernel security parameters via `sysctl` (disabling IP forwarding, enabling SYN flood cookies, ignoring ICMP redirects).
- Configuring centralized log shipping via `rsyslog` and configuring `auditd` rules for file integrity monitoring.
</details>

<details>
<summary><strong>↳ Follow-up: After provisioning resources with Terraform, do you call Ansible directly from Terraform, or do you use a separate system like Ansible Tower/AWX? How exactly do you invoke Ansible after Terraform provisioning?</strong></summary>

**Answer:**
**Production Best Practice:** We **do NOT call Ansible directly from Terraform using `local-exec`**.
- Calling Ansible from `local-exec` tightly couples configuration management to infrastructure provisioning, fails in remote CI/CD runners, and hangs if SSH connections drop.

**How We Decouple and Invoke Ansible:**
1. **Pipeline Orchestrator (GitLab CI / Jenkins):**
   The pipeline executes `terraform apply` as Stage 1. Once successful, Stage 2 invokes Ansible cleanly using the AWS Dynamic Inventory plugin (`aws_ec2.yml`).
2. **Ansible Tower / AWX Integration:**
   In enterprise environments, Terraform finishes provisioning and triggers an **AWX Job Template via REST API / Webhook**, passing the environment tags (`Env: Production`, `App: Billing`). AWX syncs its dynamic inventory directly from AWS and executes the playbook with full role-based auditing and credential isolation.
</details>

<details>
<summary><strong>↳ Follow-up: In your workflow, after running Terraform format/plan/apply to provision a new resource, at what point do you transition to using Ansible, and how do you do it?</strong></summary>

**Answer:**
The transition occurs in the CI/CD pipeline immediately following the successful completion of the `terraform apply` stage:

```
[ Step 1: terraform apply ]
             |
             +---> Infrastructure Provisioned (EC2 instances launched with Tags)
             |
[ Step 2: Readiness Health Check ]
             |
             +---> Wait for AWS SSM Agent / Cloud-Init to complete (Instance Status Checks 2/2)
             |
[ Step 3: Transition to Ansible ]
             |
             +---> Run: ansible-playbook -i inventories/aws_ec2.yml playbooks/site.yml
```

**How It Is Executed:**
1. Terraform tags instances with `ManagedBy: Terraform` and `Role: WebServer`.
2. The pipeline runs a wait loop checking `aws ec2 wait instance-status-ok`.
3. Ansible runs using the **AWS EC2 Dynamic Inventory plugin**, which automatically queries AWS APIs to discover the newly launched IP addresses without requiring static IP files.
</details>

<details>
<summary><strong>● Do you know the difference between an Ansible playbook and an Ansible role? Can you explain the difference?</strong></summary>

**Answer:**
| Feature | Ansible Playbook | Ansible Role |
| :--- | :--- | :--- |
| **Concept** | The **orchestration script** that maps target hosts to execution tasks. | The **reusable, modular package** containing tasks, variables, and templates. |
| **Structure** | A single YAML file (`deploy.yml` or `site.yml`). | A standardized directory structure (`tasks/`, `handlers/`, `templates/`, `defaults/`, `vars/`, `meta/`). |
| **Reusability** | Specific to a particular deployment workflow or environment. | Highly reusable across multiple playbooks, teams, and repositories (can be published to Ansible Galaxy). |
| **Analogy** | A Playbook is the **recipe** orchestrating the dinner course. | A Role is an **individual culinary technique or ingredient package** (e.g. Nginx role, Docker role). |

**Directory Structure of a Role:**
```
roles/nginx/
├── tasks/main.yml       # Primary execution tasks
├── handlers/main.yml    # Service restart handlers
├── templates/nginx.j2   # Jinja2 configuration templates
├── defaults/main.yml    # Default variables (lowest precedence)
└── vars/main.yml        # Role-specific variables
```
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● If someone asked you to design AWS architecture for a new application that needs an EC2 instance, Kubernetes, and a database, at a high level, what are the important things you would think about when designing that architecture?</strong></summary>

**Answer:**
Applying the **AWS Well-Architected Framework** (Security, Reliability, Performance, Cost, Operations):

```
                                [ AWS Route 53 (DNS) ]
                                           |
                                [ AWS CloudFront + WAF ]
                                           |
                              [ Application Load Balancer ]
                                           |
    +--------------------------------------+--------------------------------------+
    |                                      |                                      |
    v                                      v                                      v
[ Private Subnet AZ-1 ]          [ Private Subnet AZ-2 ]          [ Private Subnet AZ-3 ]
- EKS Worker Nodes (Zone A)      - EKS Worker Nodes (Zone B)      - EKS Worker Nodes (Zone C)
- Standalone EC2 (Worker)        - Standalone EC2 (Worker)
    |                                      |                                      |
    +--------------------------------------+--------------------------------------+
                                           |
                                           v
                             [ Isolated Database Subnets ]
                             - Amazon Aurora PostgreSQL (Multi-AZ)
                             - Multi-AZ ElastiCache Redis
```

1. **Network Segmentation & Zero Trust:**
   - Multi-AZ VPC across 3 Availability Zones.
   - Public subnets contain only ALBs. Private subnets contain EKS worker nodes and EC2 instances. Isolated database subnets have no route to the internet.
2. **Container Platform (Kubernetes):**
   - **Amazon EKS** with managed node groups and Karpenter for autoscaling.
   - IAM Roles for Service Accounts (IRSA) for least-privilege pod-level AWS access.
3. **Database Tier:**
   - **Amazon Aurora PostgreSQL Multi-AZ** with read replicas, storage auto-scaling, and automated backups with Point-In-Time Recovery (PITR).
4. **Standalone EC2 Compute:**
   - Placed in private subnets; managed via **AWS Systems Manager (SSM) Session Manager** (no public IP, no open port 22, no bastion hosts).
5. **Security & Identity:**
   - KMS encryption for all EBS volumes, S3 buckets, and RDS databases. AWS WAF fronting the ALB.
</details>

<details>
<summary><strong>↳ Follow-up: Thinking about high availability from a geographic/architectural footprint perspective, at a simple level, what would you do to ensure fault tolerance if an application or instance went down?</strong></summary>

**Answer:**
1. **Multi-AZ Redundancy:** Run application pods and EC2 instances across a minimum of **two or three physical Availability Zones** behind an Application Load Balancer with continuous health probes.
2. **Self-Healing via Auto Scaling:** Auto Scaling Groups (ASGs) continuously monitor instance health. If an instance fails, the ASG terminates it and provisions a replacement automatically.
3. **Database Multi-AZ Failover:** Amazon RDS/Aurora synchronously replicates data to a standby instance in another AZ. If the primary instance dies, failover occurs in <30 seconds without data loss.
4. **Cross-Region Disaster Recovery (DR):** Use **Route 53 DNS Failover Routing** to route global traffic to a secondary AWS region if an entire primary cloud region suffers an outage.
</details>

#### 【 BEHAVIORAL 】

<details>
<summary><strong>● Can you tell me what you think the platform engineering role is that we're looking for, and what role you believe you've applied for?</strong></summary>

**Answer:**
Platform Engineering is the discipline of designing and operating an **Internal Developer Platform (IDP)** that treats infrastructure, tooling, and developer workflows as a **product**, with application developers as the primary customers.

**Key Distinction from Traditional DevOps:**
- Traditional DevOps often results in ops engineers writing bespoke pipelines and resolving tickets for developers.
- Platform Engineering builds **"Golden Paths"**—reusable Terraform modules, self-service CI/CD templates, automated security gates, and observability dashboards—enabling development teams to deploy and manage their own applications autonomously without waiting on operations tickets.
</details>

<details>
<summary><strong>● Now that I've described the platform engineering team's responsibilities (infrastructure provisioning in AWS and on-prem, owning GitLab/Ansible/JFrog, building CI/CD templates for the DevOps team), does that sound like something you want to do?</strong></summary>

**Answer:**
Yes, absolutely. That is precisely where my core technical strengths and career focus lie. I thrive on building high-leverage developer platforms, automating multi-cloud infrastructure, establishing robust CI/CD template libraries, and eliminating operational friction for engineering organizations.
</details>

● **Candidate Introduction:** How long have you been working with EKS and AWS?

<details>
<summary><strong>↳ Follow-up: Are you working with EKS and AWS on a daily basis, every day?</strong></summary>

**Answer:**
Yes, on a daily basis. My day-to-day responsibilities include:
- Managing and optimizing EKS clusters, node groups, and Karpenter autoscalers.
- Authoring and maintaining modular Terraform infrastructure code.
- Reviewing GitOps pull requests and monitoring Argo CD application syncs.
- Responding to Prometheus/Grafana alerts and investigating application performance bottlenecks.
</details>

<details>
<summary><strong>↳ Follow-up: Have you personally performed an EKS cluster version upgrade yourself before?</strong></summary>

**Answer:**
Yes, I have personally planned and executed multiple EKS cluster version upgrades across both production and non-production environments (including upgrading through Kubernetes 1.25, 1.26, 1.27, and 1.28).

**My Standard Execution Process:**
1. Running `kubent` to audit and replace deprecated API versions.
2. Upgrading managed add-ons (VPC CNI, CoreDNS, kube-proxy, EBS CSI).
3. Upgrading the EKS Control Plane version via Terraform.
4. Performing a zero-downtime rolling node upgrade on the worker node groups respecting PodDisruptionBudgets.
5. Verifying workload health and Prometheus golden signals.
</details>

<details>
<summary><strong>↳ Follow-up: If you haven't personally performed the EKS upgrade yourself, how do you know the detailed steps involved?</strong></summary>

**Answer:**
While I *have* directly executed production EKS upgrades, deep mastery comes from thorough engineering discipline:
- Rigorously studying the official AWS EKS Upgrade Documentation and Kubernetes upstream release notes.
- Simulating every upgrade end-to-end in isolated sandbox clusters prior to touching staging or production.
- Authoring comprehensive, peer-reviewed operational runbooks that outline pre-upgrade checks, execution sequences, and rollback procedures.
</details>

<details>
<summary><strong>● Can you tell me about a time (not necessarily Kubernetes-related) when you had to upgrade a system and it didn't go well, i.e., something went wrong?</strong></summary>

**Answer:**
During a major version upgrade of our primary **Amazon RDS PostgreSQL database from version 11 to 14**:

**What Went Wrong:**
The upgrade completed successfully in AWS, but within 10 minutes of reopening production traffic, application API response times spiked from 50ms to over 3 seconds, causing connection pool exhaustion.

**Root Cause:**
During a major PostgreSQL version upgrade, the query planner's internal statistics are wiped out. The PostgreSQL query optimizer, lacking updated table statistics, reverted to executing expensive **Sequential Full Table Scans** on tables with 20+ million rows instead of using indexed lookups.

**Remediation:**
I immediately ran an accelerated database analyze command:
```sql
ANALYZE VERBOSE;
```
Within 2 minutes, as statistics were rebuilt, query execution times dropped back to sub-millisecond levels and connection pool saturation subsided.

**Postmortem Action Item:**
Updated our database upgrade runbook to mandate running `vacuumdb --all --analyze-in-stages` immediately following any major engine upgrade before releasing traffic.
</details>

<details>
<summary><strong>● Can you tell me about a time in your job when you broke something or caused a problem?</strong></summary>

**Answer:**
Early in my career as a DevOps engineer, while refactoring Terraform code for our staging environment's security groups, I made a mistake:

**What Happened:**
I inadvertently removed an inbound CIDR block in an internal security group rule that allowed the web tier to talk to the backend caching tier. When I applied the Terraform plan, staging web applications began throwing 500 errors.

**Action Taken (Accountability & Resolution):**
1. I immediately posted in the team incident channel taking full ownership: *"Staging API errors are due to a security group change I just applied; investigating now."*
2. Checked `git diff` on my recent commit, identified the missing port 6379 ingress rule, and applied the correction within 3 minutes.
3. Services restored immediately.

**Long-Term Process Improvements:**
- Introduced **`checkov`** and **`tflint`** in pre-commit hooks to validate security group rules against baselines.
- Built an automated smoke testing step in the CI/CD pipeline that verifies end-to-end connectivity before marking any infrastructure apply as complete.
</details>
</details>
</details>

<details open>
<summary><h2>🏢 TransUnion</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 GIT 】

<details>
<summary><strong>● You mentioned setting up Git repositories for use with Jenkins. Can you walk me through the branching strategy you followed?</strong></summary>

**Answer:**
In our enterprise engineering organization, we adopted a **GitFlow / GitHub Flow hybrid branching strategy** designed to support both continuous integration and stable, audited releases:

```
[ Feature Branches: feature/* ]
       | (PR + Review + CI Pass)
       v
[ Integration Branch: develop ] ---> Deployed to Dev / QA
       | (Release Cut)
       v
[ Release Branch: release/v2.4 ] ---> Deployed to Staging (Regression / Hardening)
       | (Final Approval Gate)
       v
[ Production Branch: main ] --------> Deployed to Production (Canary via GitOps)
  ^ (Tagged: v2.4.0)
  |
[ Hotfix Branch: hotfix/fix-auth ] (Branched directly from main for P1 incidents)
```

1. **`main` Branch (Production):**
   - Contains strictly production-ready code.
   - Direct commits and force-pushes are blocked via branch protection. Every merge generates a release tag (e.g. `v2.4.0`).
2. **`develop` Branch (Active Integration):**
   - The primary integration branch where ongoing sprint work converges. Merges to `develop` automatically trigger CI builds and deployments to the `dev` environment.
3. **`feature/*` Branches:**
   - Branched off `develop`. Developers work in short-lived branches (1–3 days). Merging requires opening a Pull Request (PR), passing automated CI unit tests/linters, and obtaining at least 1 peer approval.
4. **`release/*` Branches:**
   - Cut from `develop` when preparing for a release milestone. Deployed to Staging for regression testing and QA sign-off. Only bug fixes are permitted. Once validated, merged into `main` and back-merged into `develop`.
5. **`hotfix/*` Branches:**
   - Used for emergency production fixes. Branched directly from `main`, tested in Staging, and merged into both `main` and `develop`.
</details>

<details>
<summary><strong>● Walk me through a tricky merge conflict you resolved early in your career using SCM practices like branching and merging.</strong></summary>

**Answer:**
Early in my career, our team encountered a complex merge conflict when two long-lived feature branches were merged back into `develop` simultaneously:

**The Conflict Scenario:**
- **Branch A (Performance Refactor):** A developer restructured our primary database access layer, refactoring synchronous calls into asynchronous `async/await` methods across 15 core service files.
- **Branch B (Multi-Tenant Feature):** Another developer updated the identical service files to accept a new `TenantContext` parameter across all database queries.
- When Branch B attempted to merge after Branch A, Git flagged **hundreds of conflicting lines across 15 files**.

**Step-by-Step Resolution Process:**
1. **Never Resolve Blindly in the Web UI:** Complex conflicts should never be resolved in GitHub/GitLab web editors. I checked out the branch locally and initiated the merge:
   ```bash
   git checkout feature/multi-tenant
   git merge origin/develop
   ```
2. **Leverage 3-Way Merge Tools:** Configured `git mergetool` with VS Code to inspect the 3-way merge view: **BASE** (common ancestor), **LOCAL** (Branch B changes), and **REMOTE** (Branch A async changes).
3. **Collaborative Pair-Programming:** I scheduled a 30-minute working session with the authors of both branches. We walked through the logic together to preserve both features: wrapping the new `TenantContext` logic cleanly inside the newly introduced `async` method signatures.
4. **Comprehensive Local Testing:** Once all conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) were resolved, we ran the full test suite locally:
   ```bash
   mvn clean test
   ```
   Fixed two failing integration tests where tenant contexts were not being passed into async thread locals.
5. **Commit & Push Clean Merge:** Completed the merge commit and verified the CI pipeline passed 100% on the pull request.
6. **Key Takeaway:** Advocated for adopting **Trunk-Based Development** and shorter-lived feature branches (< 2 days) to eliminate long-lived branch divergence.
</details>

<details>
<summary><strong>● Have you worked with any version control system other than Git?</strong></summary>

**Answer:**
Yes. While **Git** has been my primary version control system throughout my career (across GitHub, GitLab, Bitbucket, and AWS CodeCommit), I have working knowledge and historical experience with **Apache Subversion (SVN)** and **Perforce**:

- **Centralized vs. Distributed VCS Differences:**
  - *Centralized VCS (SVN):* Relies on a single central server. Developers check out a working copy and must be connected to the corporate network to commit. Branching and merging are heavy and slow.
  - *Distributed VCS (Git):* Every clone contains the full repository history, commit tree, and cryptographic SHA hashes. Developers branch, commit, and inspect logs completely offline. Branching is lightweight (just a 41-byte pointer to a commit).
</details>

<details>
<summary><strong>↳ Follow-up: Do you know anything about Bitbucket specifically?</strong></summary>

**Answer:**
Yes. **Atlassian Bitbucket** is an enterprise Git solution deeply integrated with the Atlassian suite:
- **Jira & Confluence Integration:** Automated tracking between Git commits, pull requests, and Jira tickets. Using "Smart Commits", a commit message like `PROJ-123 #close #comment Deployed to staging` automatically transitions the Jira issue.
- **Bitbucket Cloud vs. Bitbucket Data Center:** Bitbucket Cloud is Atlassian's managed SaaS offering; Bitbucket Data Center is the self-hosted enterprise clustering solution offering active-active high availability and local Git mirrors for distributed global teams.
- **Bitbucket Pipelines:** Built-in cloud-native CI/CD service configured via `bitbucket-pipelines.yml`.
- **Enterprise Governance:** Strict branch permission rules, mandatory pull request merge checks, and IP allowlisting.
</details>

#### 【 CI/CD 】

<details>
<summary><strong>● You mentioned implementing automated testing solutions for unit and integration testing. Did you personally implement these, or did the developers on your team do it?</strong></summary>

**Answer:**
We operated under a collaborative **DevSecOps responsibility matrix**:

- **Developers' Responsibility (Test Authorship):**
  - Application developers authored the actual test code, test fixtures, and business assertions using testing frameworks (e.g. JUnit, Mockito, PyTest, Jest).
- **My Platform / DevOps Responsibility (Test Infrastructure & Orchestration):**
  - **CI Pipeline Automation:** I codified the pipeline stages in the `Jenkinsfile` to execute unit tests automatically on every commit.
  - **Dynamic Ephemeral Test Infrastructure (Testcontainers):** For integration tests that required real databases, I configured Docker-in-Docker / Testcontainers to spin up ephemeral PostgreSQL and Redis containers dynamically during the CI run.
  - **Quality Gates & Code Coverage:** I integrated **JaCoCo** / **pytest-cov** with **SonarQube**, enforcing strict quality gates (e.g. build fails if overall unit test coverage drops below 80% or new code coverage is under 85%).
  - **Parallelization & Feedback Velocity:** Partitioned test suites to run in parallel across dynamic Kubernetes agent pods, slashing test execution time from 25 minutes down to 6 minutes.
</details>

<details>
<summary><strong>● You mentioned using Jenkins and Argo CD together. Can you describe the workflow where Jenkins hands off and Argo CD takes over in the deployment process?</strong></summary>

**Answer:**
The handoff between Jenkins and Argo CD represents the architectural boundary between **Continuous Integration (CI)** and **Continuous Delivery (CD)**:

```
+-------------------------------------------------------------------------------+
| JENKINS CI DOMAIN                                                             |
|                                                                               |
|  [ Code Checkout ] -> [ Unit Tests ] -> [ SonarQube ] -> [ Docker Build ]     |
|                                                                  |            |
|  [ Push Image to AWS ECR ] <-------------------------------------+            |
|    (Tagged with Git SHA: app:c7a4e8f)                                         |
+-------------------------------------------------------------------------------+
                                       |
                       (THE HANDOFF: Git Commit via Machine Token)
                                       v
+-------------------------------------------------------------------------------+
| GITOPS DEPLOYMENT REPOSITORY (k8s-manifests)                                  |
|                                                                               |
|  - environments/staging/values.yaml (Updated: image.tag = "c7a4e8f")          |
+-------------------------------------------------------------------------------+
                                       |
                       (Continuous Pull / Drift Detection)
                                       v
+-------------------------------------------------------------------------------+
| ARGO CD DOMAIN (Running inside Amazon EKS)                                    |
|                                                                               |
|  [ Detects Git Drift ] -> [ Reconciles Cluster ] -> [ Canary Rollout (EKS) ]   |
+-------------------------------------------------------------------------------+
```

**Step-by-Step Handoff Sequence:**
1. **Jenkins Completes the CI Phase:**
   - Jenkins builds, scans, and pushes the hardened container image to Amazon ECR tagged with the Git commit SHA: `${ECR_REGISTRY}/payment-svc:${GIT_COMMIT}`.
2. **The Handoff Step (Decoupled via Git):**
   - **Crucial Rule:** Jenkins **never touches the Kubernetes API directly**.
   - Instead, Jenkins uses a machine user token to clone the dedicated **GitOps Manifest Repository**.
   - Jenkins updates the target image tag in the environment's values file:
     ```bash
     yq eval '.image.tag = "'${GIT_COMMIT}'"' -i environments/staging/values.yaml
     git commit -am "ci(staging): update payment-svc image tag to ${GIT_COMMIT}"
     git push origin main
     ```
3. **Argo CD Takes Over (The CD Phase):**
   - Argo CD, running inside the EKS cluster, continuously monitors the GitOps repository.
   - It detects the new commit, marks the application as `OutOfSync`, and triggers an automated rolling or canary synchronization into the EKS cluster.
</details>

<details>
<summary><strong>↳ Follow-up: Have you actually worked hands-on with Argo CD, or not?</strong></summary>

**Answer:**
Yes, I have extensive hands-on operational experience with **Argo CD** in production:
- Provisioning and configuring the Argo CD control plane using the official Helm chart (`argo/argo-cd`).
- Managing multi-tenant environments using **`ApplicationSet`** controllers to dynamically generate deployment applications across multiple EKS clusters.
- Configuring **Sync Policies** (automated sync, self-healing, prune options).
- Setting up **Argo CD RBAC** and integrating Single Sign-On (SSO) via Okta OIDC.
- Implementing progressive canary delivery using **Argo Rollouts** integrated with Prometheus metric analysis templates.
</details>

<details>
<summary><strong>● You listed JFrog Artifactory as a tool you've used. What kind of artifacts did you store there—JAR files or Docker images?</strong></summary>

**Answer:**
We utilized JFrog Artifactory as our **Universal Artifact Repository Manager** for both application binaries and container images:

1. **JAR / WAR Files (Maven / Gradle Repositories):**
   - Stored compiled Java microservice artifacts (`.jar` files) tagged with semantic versioning.
   - Configured **Remote Repositories** caching public dependencies from Maven Central, speeding up builds and shielding our pipeline from external upstream outages.
2. **Docker / OCI Images:**
   - Managed multi-stage Docker repositories with an automated promotion pipeline:
     - `docker-dev-local`: Initial CI builds.
     - `docker-stage-local`: Promoted after passing QA and security scans.
     - `docker-prod-local`: Production-approved images.
3. **Helm Charts:**
   - Stored packaged Helm charts (`.tgz`) serving as the enterprise private chart catalog.
4. **Security Scanning (JFrog Xray):**
   - Integrated with **JFrog Xray** for deep recursive binary scanning, identifying vulnerabilities in third-party JAR dependencies and container base OS packages.
</details>

#### 【 DOCKER 】

<details>
<summary><strong>● You mentioned using multi-stage Docker builds. Can you give a specific example: what was the base image, what did the build stage do, and what made the final image stage smaller?</strong></summary>

**Answer:**
Here is a real-world example from our Spring Boot Java microservice pipeline:

```dockerfile
# ==============================================================================
# STAGE 1: Compilation & Packaging (Heavyweight Build Environment)
# ==============================================================================
FROM maven:3.9.6-eclipse-temurin-17 AS builder
WORKDIR /workspace

# Cache dependencies independently from source code
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy source code and build production JAR
COPY src ./src
RUN mvn clean package -DskipTests

# ==============================================================================
# STAGE 2: Hardened Production Runtime (Minimal Execution Environment)
# ==============================================================================
FROM eclipse-temurin:17-jre-alpine AS runner
WORKDIR /app

# Create non-root system user for security compliance
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy ONLY the compiled executable JAR from Stage 1
COPY --from=builder /workspace/target/*.jar /app/application.jar

USER appuser
EXPOSE 8080

ENTRYPOINT ["java", "-XX:+UseContainerSupport", "-XX:MaxRAMPercentage=75.0", "-jar", "/app/application.jar"]
```

**Detailed Technical Breakdown:**
- **Base Image in Build Stage:** `maven:3.9.6-eclipse-temurin-17` (~850 MB). It includes the full Java Development Kit (JDK), compiler (`javac`), Maven build engine, and Linux development utilities.
- **Build Stage Action:** Downloaded project dependencies, compiled Java source files into bytecode, and packaged them into an executable fat JAR (`application.jar` ~45 MB).
- **Final Runtime Base Image:** `eclipse-temurin:17-jre-alpine` (~170 MB). It contains only the stripped-down Java Runtime Environment (JRE) on a minimal Alpine Linux distribution.
- **Why the Final Image Stage is Drastically Smaller:**
  - The final image **completely discards the Maven installation, the JDK compiler, intermediate `.m2` repository caches, build plugins, and raw source files**.
  - Final image size dropped from **~1.2 GB down to ~215 MB**, shrinking storage costs, accelerating image pull times across EKS nodes, and significantly eliminating CVE vulnerabilities.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● You mentioned working with Docker containers and Kubernetes clusters. Were you personally administering the clusters, or were you just deploying applications to them?</strong></summary>

**Answer:**
I have operated at both tiers as a **Platform and SRE Lead**:

1. **Cluster Administration & Infrastructure (Day-2 Operations):**
   - Provisioning multi-AZ EKS clusters via Terraform.
   - Managing worker node lifecycles, AMI patching, and autoscaling using **Karpenter**.
   - Implementing cluster networking via AWS VPC CNI and Calico NetworkPolicies.
   - Deploying and maintaining platform add-ons: Ingress-NGINX, cert-manager, External Secrets Operator, and Prometheus Operator.
   - Executing EKS minor version upgrades and managing control plane security.
2. **Application Delivery & Developer Enablement:**
   - Authoring modular Helm charts for engineering squads.
   - Establishing Argo CD GitOps pipelines.
   - Configuring HPA autoscalers, PodDisruptionBudgets, and resource quotas.
</details>

<details>
<summary><strong>↳ Follow-up: Do you also maintain the EKS cluster and its nodes, or do you just write the code/manifests for it?</strong></summary>

**Answer:**
Yes, I actively maintain the live clusters and worker node fleets:
- **Node Fleet Maintenance:** Managing rolling node updates for security patching using `kubectl cordon` and `kubectl drain` while respecting PodDisruptionBudgets.
- **Capacity & Autoscaling Management:** Tuning Karpenter provisioners, optimizing spot vs on-demand node pools, and preventing subnet IP exhaustion.
- **Incident Response & On-Call:** Investigating cluster-wide outages, CoreDNS latency, and OOMKilled events as part of our 24/7 on-call rotation.
</details>

<details>
<summary><strong>● Tell me about a real production incident you were on call for—what broke, and how did you find the root cause?</strong></summary>

**Answer:**
**The Production Outage:**
During a high-volume marketing campaign, our primary customer API began throwing widespread **HTTP 504 Gateway Timeouts** across multiple microservices.

**Triage & Diagnostic Investigation:**
1. **Initial Layer Check:** Application Load Balancer and Ingress Controller metrics showed 504 Gateway Timeouts. However, application pod CPU and memory utilization looked completely normal (~35%).
2. **APM & Tracing Telemetry:** We inspected distributed traces in OpenTelemetry/Jaeger and discovered that internal service-to-service HTTP requests were hanging for 30+ seconds on **DNS lookup resolution**.
3. **Control Plane & CoreDNS Metrics:**
   - Inspected CoreDNS metrics in Prometheus: `coredns_dns_request_duration_seconds` had spiked dramatically.
   - CoreDNS logs revealed severe request drops, and `kubectl top pods -n kube-system` showed CoreDNS pods were hitting **100% CPU CFS throttling**.
4. **Root Cause Identification:**
   - A newly deployed microservice was making external HTTP calls in a tight loop without connection pooling or DNS caching.
   - Due to the default Linux `/etc/resolv.conf` `ndots:5` lookup behavior, every single external hostname lookup triggered 4 sequential search-domain queries within the cluster before querying upstream DNS, causing a massive query amplification storm (over 120,000 queries/second) that saturated CoreDNS.

**Remediation & Recovery:**
- **Immediate Mitigation:** Horizontally scaled CoreDNS deployment from 2 to 12 replicas and increased its CPU limits, immediately clearing the query backlog and restoring API latency to sub-50ms.
- **Permanent Architectural Fix:**
  1. Deployed **NodeLocal DNSCache** as a DaemonSet across all worker nodes. DNS queries are now cached locally on each node via a loopback IP, bypassing CoreDNS for 85% of queries.
  2. Guided the application team to implement HTTP client-level DNS caching.
</details>

#### 【 IAC 】

<details>
<summary><strong>● You mentioned using both Terraform and Ansible for AWS automation. Why use both tools, and what specifically was Terraform responsible for versus what Ansible was responsible for on the same AWS infrastructure?</strong></summary>

**Answer:**
We use both tools by maintaining a strict **Separation of Concerns** between **Infrastructure Orchestration** and **Configuration Management**:

```
[ TERRAFORM: Infrastructure Orchestration (Outside-the-OS) ]
  - VPCs, Subnets, Route Tables, Internet Gateways
  - IAM Roles, Policies, KMS Keys
  - Security Groups, Application Load Balancers
  - Amazon RDS PostgreSQL, S3 Buckets, EC2 Instances
                       |
                       v (Handoff: Dynamic Inventory via Tags)
[ ANSIBLE: Configuration Management (Inside-the-OS) ]
  - Operating System Hardening (CIS Benchmarks)
  - Managing /etc/ssh/sshd_config, users, PAM modules
  - Installing security agents (CrowdStrike, Datadog)
  - Applying Nginx templates & runtime configurations
```

- **Terraform's Responsibility:** Declaratively provisions the underlying cloud infrastructure (VPCs, EC2, RDS, IAM, S3). Terraform manages cloud resources through cloud provider APIs.
- **Ansible's Responsibility:** Connects to the provisioned EC2 instances over SSH/SSM to configure the operating system internals, apply security baselines, and deploy host configuration templates.
</details>

<details>
<summary><strong>↳ Follow-up: Why couldn't you accomplish everything using just one tool, either Terraform or Ansible alone? Why was it necessary to use both?</strong></summary>

**Answer:**
While both tools *can* technically perform overlapping tasks, using one tool for both introduces severe architectural compromises:

1. **Why Not Ansible for Cloud Infrastructure Provisioning?**
   - Ansible lacks a robust, centralized state file. Managing complex cloud dependency graphs (e.g., deleting a VPC after destroying subnets, NAT gateways, and ENIs) is brittle and frequently results in orphaned resources or failed cloud deployments.
2. **Why Not Terraform for In-Guest OS Configuration?**
   - Terraform is not a configuration management tool. Using `remote-exec` or giant `user_data` bash scripts inside Terraform is non-idempotent, difficult to debug, lacks error handling, and requires **destroying and recreating the EC2 instance** whenever you want to update a configuration file!
3. **The Best-of-Breed Synergy:**
   - Terraform excels at stateful cloud lifecycle orchestration.
   - Ansible excels at agentless, idempotent, in-guest software configuration.
</details>

<details>
<summary><strong>↳ Follow-up: Did you encounter any scaling issues while managing infrastructure provisioning and configuration with Terraform and Ansible?</strong></summary>

**Answer:**
Yes, at enterprise scale we encountered distinct bottlenecks with both:

1. **Terraform State Bloat & Cloud API Rate Limiting:**
   - *Problem:* A large monolithic state file tracking 800+ resources took over 20 minutes to run `terraform plan` and triggered AWS `ThrottlingException` API errors.
   - *Solution:* Decomposed the monolithic state into decoupled directory layers (`network/`, `data/`, `compute/`) using remote state data sources. Plan execution time dropped to < 45 seconds.
2. **Ansible SSH Concurrency & Performance Bottlenecks:**
   - *Problem:* Running playbooks sequentially across 250+ EC2 instances took over an hour.
   - *Solution:* Tuned `ansible.cfg` by increasing `forks = 50`, enabling SSH `pipelining = True`, and adopting the **Mitogen for Ansible** plugin, accelerating playbook execution by 5x.
</details>

<details>
<summary><strong>● Can you tell me about a time when a Terraform code change you made broke something, and how did you fix it?</strong></summary>

**Answer:**
**The Incident:**
While updating an AWS Launch Template managed by Terraform, I modified the `user_data` script to add a new monitoring agent.

**What Broke:**
Because `user_data` changes force an instance replacement in AWS, and our Terraform resource was missing the `lifecycle { create_before_destroy = true }` meta-argument, Terraform attempted to destroy the existing target group instances before launching the replacement instances, resulting in a **4-minute service degradation on an internal payment webhook**.

**Immediate Remediation & Long-Term Fix:**
1. **Immediate Action:** Rolled back the change immediately and restored the previous state version via S3 Bucket Versioning.
2. **Added `create_before_destroy`:**
   ```hcl
   lifecycle {
     create_before_destroy = true
   }
   ```
3. **Automated Rolling Instance Refresh:** Updated the Auto Scaling Group resource to use **`instance_refresh`** with dynamic health check monitoring:
   ```hcl
   instance_refresh {
     strategy = "Rolling"
     preferences {
       min_healthy_percentage = 100
       instance_warmup        = 300
     }
   }
   ```
   This guarantees that replacement instances are fully initialized and healthy before old instances are terminated.
</details>

#### 【 CLOUD 】

<details>
<summary><strong>● You mentioned optimizing infrastructure and reducing costs by eliminating unnecessary servers. Do you have any specific before-and-after numbers to quantify that cost reduction?</strong></summary>

**Answer:**
Yes. During a major FinOps optimization initiative across our three AWS accounts:

**Baseline Metrics (Before):**
- Total monthly cloud spend: **$52,000 / month**.
- Unattached EBS volumes: 68 volumes in `available` state costing ~$1,800/month.
- Development/QA compute running 24/7 with average CPU < 8%.

**Optimization Actions Executed:**
1. Cleaned up orphaned EBS volumes, obsolete snapshots older than 90 days, and unattached Elastic IPs.
2. Implemented **AWS Instance Scheduler** via EventBridge and Lambda to automatically stop all non-production EC2 instances on weeknights and weekends (saving 65% on non-prod compute).
3. Right-sized 30+ over-provisioned production instances using AWS Compute Optimizer telemetry.
4. Committed to a 3-year **Compute Savings Plan** for steady-state baseline production compute.

**Results Achieved (After):**
- Monthly spend dropped from **$52,000/month to $34,800/month**.
- Delivered a verified recurring **annual cost reduction of over $206,000 (~33% savings)** with zero impact on performance.
</details>

<details>
<summary><strong>● Your resume lists both AWS and Azure. Have you ever had the chance to deploy the same workload on both cloud platforms?</strong></summary>

**Answer:**
Yes. We deployed an enterprise notification and reporting service across both AWS and Azure:
- **On AWS:** Deployed on **Amazon EKS** with an Application Load Balancer, AWS VPC CNI, and Amazon Aurora PostgreSQL.
- **On Azure:** Deployed on **Azure Kubernetes Service (AKS)** with Azure Application Gateway Ingress Controller, Azure CNI, and Azure Database for PostgreSQL Flexible Server.
- **Portability Layer:** The underlying microservice Docker container and core Helm chart templates were 100% identical; only cloud-specific values files (`values-aws.yaml` vs `values-azure.yaml`) and ingress annotations were customized.
</details>

<details>
<summary><strong>↳ Follow-up: So is Azure used as a backup cloud in your environment, rather than a primary one?</strong></summary>

**Answer:**
**Clarification:** No, Azure was not used as a passive backup or DR failover for AWS.
- AWS serves as our primary cloud platform for core SaaS product hosting.
- Azure is utilized strategically for enterprise identity governance (**Microsoft Entra ID**), corporate data analytics (PowerBI), and dedicated private client deployments where enterprise enterprise agreements mandate data residency within Azure.
</details>

<details>
<summary><strong>● Do you have any experience working with Google Cloud Platform (GCP)?</strong></summary>

**Answer:**
Yes, I possess a strong foundational understanding of **Google Cloud Platform (GCP)**:
- Container Orchestration: **Google Kubernetes Engine (GKE)**, including GKE Autopilot and VPC-native clusters.
- Compute & Storage: Google Compute Engine (GCE), Google Cloud Storage (GCS).
- Identity & Governance: Cloud IAM, Service Accounts with Workload Identity.
- While my daily production depth is in AWS and Azure, cloud-native principles (IAM, VPC networking, managed Kubernetes, object storage) translate seamlessly to GCP.
</details>

#### 【 MONITORING 】

<details>
<summary><strong>● You mentioned leveraging Helm charts. Do you have experience with the Grafana monitoring tool?</strong></summary>

**Answer:**
Yes, extensive production experience:
- Deployed and operated Grafana at scale using the **`kube-prometheus-stack`** Helm chart.
- Designed comprehensive operational dashboards for the **Four Golden Signals** (Latency, Traffic, Errors, Saturation).
- Implemented **Grafana Unified Alerting** routing notifications to Slack and PagerDuty with custom Go alert templates.
- Automated dashboard provisioning as code using Kubernetes ConfigMaps with sidecar auto-reloading and Terraform (`grafana_dashboard`).
</details>

#### 【 SECURITY 】

<details>
<summary><strong>● When setting up Jenkins or AWS resources, how do you handle secrets management?</strong></summary>

**Answer:**
We enforce a strict **Zero Cleartext Secrets** policy across the delivery pipeline:

1. **In Jenkins Pipelines:**
   - Secrets are stored inside the encrypted **Jenkins Credentials Manager**.
   - Injected into pipeline stages using `withCredentials([string(...), usernamePassword(...)])`.
   - Jenkins automatically masks secret values in console logs with `****`.
2. **In AWS & Terraform:**
   - Secrets are managed in **AWS Secrets Manager** with automated KMS encryption and rotation.
   - We never hardcode passwords in `.tfvars` files or Git.
3. **In Kubernetes (External Secrets Operator - ESO):**
   - The **External Secrets Operator** synchronizes secrets directly from AWS Secrets Manager into Kubernetes `Secret` objects inside the cluster memory at runtime.
</details>

<details>
<summary><strong>↳ Follow-up: Do you know anything about security/cybersecurity concepts?</strong></summary>

**Answer:**
Yes. In modern cloud and DevOps engineering, security is integral to my daily work through **DevSecOps**:
- **Zero-Trust Architecture:** Principle of Least Privilege (PoLP), strict network segmentation (Calico NetworkPolicies), and mutual TLS (mTLS).
- **Shift-Left Security:** Automated SAST (SonarQube), SCA dependency analysis (Snyk/OWASP), and container image scanning (Trivy) enforced as pipeline quality gates.
- **Identity & Access Management:** Passwordless OIDC authentication, short-lived STS tokens, and Multi-Factor Authentication (MFA).
- **Data Protection:** Enforcing AES-256 / KMS encryption at rest across all disks/buckets and TLS 1.2+ in transit.
- **Compliance Standards:** CIS Benchmarks, SOC2 Type II, and PCI-DSS compliance baselines.
</details>

<details>
<summary><strong>● When you worked on giving AWS credentials to users, what security practices did you follow, and how did you provide credentials to them?</strong></summary>

**Answer:**
We strictly prohibit creating static IAM users with long-lived Access Keys (`AKIA...`) for human developers.

**Enterprise Security Practices Followed:**
1. **Federated Single Sign-On (AWS IAM Identity Center):**
   - Users authenticate using corporate credentials via **AWS IAM Identity Center** integrated with Okta / Azure AD with mandatory hardware MFA.
2. **Role-Based Access Control (RBAC):**
   - Users assume temporary, short-lived IAM roles via **AWS STS** (session duration 1–4 hours).
3. **Permission Sets & Least Privilege:**
   - Permissions are granted based on job function (e.g. `DeveloperReadOnly`, `DataEngineerAccess`). Production write access requires temporary just-in-time elevation with manager approval.
4. **Service Control Policies (SCPs):**
   - Organizational guardrails prevent users from modifying CloudTrail, disabling security logs, or launching instances outside authorized AWS regions.
</details>

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Pick one specific project you worked on at Informatica and describe what state it was in when you joined versus its current state.</strong></summary>

**Answer:**
**The Legacy State (When I Joined):**
- Infrastructure was deployed manually through the AWS Console, resulting in severe configuration drift.
- Deployments were executed via manual SSH scripts on standalone EC2 instances, taking over 3 hours and requiring scheduled weekend maintenance windows.
- Monitoring consisted of basic CloudWatch alarms, with no distributed tracing and frequent customer-reported outages.

**The Modernized State (Current Architecture):**
- 100% codified as **Infrastructure as Code (Terraform)** across multi-AZ VPCs and Amazon EKS.
- Fully automated **GitOps CI/CD pipeline** (GitHub Actions + Argo CD) delivering progressive canary rollouts with zero downtime.
- Centralized observability stack (**Prometheus, Grafana, OpenTelemetry**) providing sub-minute anomaly detection.
- Deployment frequency increased from **monthly to multiple releases daily**, with Change Failure Rate dropping to **< 2%**.
</details>

<details>
<summary><strong>● Your resume mentions breaking down monolithic applications into microservices. What was your specific role in that decomposition—were you doing the application-level work, or just the platform/infrastructure side?</strong></summary>

**Answer:**
My role was strictly on the **Cloud Platform, Infrastructure, and DevOps side**:
1. **Container Hosting Platform:** Designed and provisioned the high-availability Amazon EKS cluster foundation, networking, and security boundaries.
2. **Strangler Fig Routing Pattern:** Configured the AWS Application Load Balancer and API Gateway path-based routing rules to progressively peel off URI endpoints (e.g. `/api/v1/payments`) from the legacy monolith and route them to the new microservice.
3. **Developer "Golden Path" Templates:** Built standardized Helm charts and CI/CD pipeline templates so developers could spin up and deploy new microservices in minutes.
4. **Distributed Observability:** Implemented OpenTelemetry distributed tracing so requests spanning both the legacy monolith and new microservices could be traced end-to-end.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you tell me about yourself and your professional background?

● **Candidate Introduction:** In your first job as a software engineer, what was your actual day-to-day work like, in terms of writing application code versus doing infrastructure work?

<details>
<summary><strong>● You describe yourself as having extensive experience in CI/CD pipelines and DevOps. What would you say is your strongest contribution to date?</strong></summary>

**Answer:**
My strongest contribution was architecting and delivering an enterprise-wide **GitOps-driven Continuous Delivery Platform** for our core SaaS microservices:
- Transitioned 35+ services from fragile, manual scripts to automated GitOps with **Argo CD** and **Argo Rollouts**.
- Built automated canary validation with Prometheus error budget gates, reducing our Change Failure Rate from 18% to under 2%.
- Reduced average deployment lead time from **4 hours down to 12 minutes**, enabling engineering squads to ship features safely on-demand with zero customer downtime.
</details>

<details>
<summary><strong>↳ Follow-up: Regarding your strongest contribution, did you build it entirely from scratch, or did you take an existing setup and build upon it? Can you explain how it worked?</strong></summary>

**Answer:**
I built the modern GitOps platform **from scratch as a greenfield initiative** while orchestrating a phased, zero-downtime migration away from the legacy infrastructure:
1. Designed and deployed the new Amazon EKS cluster architecture using modular Terraform code.
2. Formulated standardized Helm base charts and reusable GitHub Actions CI workflows.
3. Deployed Argo CD inside the management cluster and established the GitOps manifest repository structure.
4. Migrated microservices one by one using DNS and load balancer traffic shifting, deprecating the old VM-based pipelines as each service transitioned.
</details>

<details>
<summary><strong>● What part of your current job do you find most interesting, and what part do you wish you did less of?</strong></summary>

**Answer:**
- **Most Interesting:** Designing platform architecture, solving complex distributed system reliability challenges, and creating automated developer self-service tooling ("Golden Paths") that dramatically improve developer productivity.
- **Wish I Did Less Of:** Manual operational toil and ad-hoc administrative requests (e.g. manually approving access requests or troubleshooting snowflake environments). This drives me to aggressively automate workflows through self-service portals, Terraform, and policy-as-code.
</details>

<details>
<summary><strong>↳ Follow-up: Is there anything about your current job that you don't like?</strong></summary>

**Answer:**
I find bureaucratic, manual Change Advisory Board (CAB) review processes frustrating when they delay low-risk, automated changes. I actively work to replace manual change gates with automated pipeline quality gates (SAST, unit testing, automated canary analysis), proving to leadership that automated guardrails provide higher reliability than manual review checklists.
</details>

<details>
<summary><strong>● Have you ever considered moving into cybersecurity, or are you more comfortable staying in DevOps?</strong></summary>

**Answer:**
I view **DevOps and Cybersecurity as inseparable disciplines**. I thrive in the intersection—**DevSecOps** and **Cloud Platform Security**. I enjoy the broad architectural ownership of building reliable, scalable systems while embedding security into every layer (container hardening, IAM zero trust, automated scanning). I intend to continue leading platform engineering with a heavy focus on DevSecOps.
</details>

<details>
<summary><strong>● As a junior engineer in your first year at Informatica, how much of the Terraform, Ansible, and Jenkins work were you actually owning, versus shadowing or just assisting others?</strong></summary>

**Answer:**
In my initial months, I primarily shadowed senior SREs, reviewing their Terraform pull requests and assisting with routine Jenkins maintenance and Ansible playbook execution for server patching. Within 6 months, as I demonstrated technical competence, I was granted full ownership of non-production Terraform modules and built automated CI/CD pipelines for secondary microservices, progressively growing into independent production ownership.
</details>

<details>
<summary><strong>● Across your three companies, you've used the same tools like Terraform, Ansible, Jenkins, AWS, and Docker. What was actually different about the work you did at each company?</strong></summary>

**Answer:**
While the tool names remained consistent, the **scale, architectural maturity, and problem complexity evolved drastically**:
1. **First Role (Accenture):** Focused on implementation and task-level execution—writing individual Dockerfiles, maintaining Jenkins jobs, and executing scripts written by seniors.
2. **Second Role (Informatica - First Stint):** Advanced to ownership—migrating applications from on-prem to AWS, writing custom reusable Terraform modules, and configuring multi-node Kubernetes clusters.
3. **Current Role (Senior Platform Engineer):** High-level architectural leadership—designing multi-account AWS Landing Zones, establishing enterprise GitOps standards with Argo CD, driving FinOps cost reduction, and setting security guardrails across the entire engineering organization.
</details>

<details>
<summary><strong>● Can you describe a tactical decision you got wrong and had to back out of, and what you learned from it?</strong></summary>

**Answer:**
**The Tactical Decision:**
Early in our Kubernetes adoption, I enforced strict, tight CPU limits on all microservice containers (e.g. `limits.cpu: 500m`), believing this would guarantee fair CPU sharing and prevent noisy-neighbor issues.

**What Went Wrong:**
In production, while average CPU utilization was only 30%, our p99 application response latency spiked from 80ms to over 3.5 seconds. Deep kernel profiling revealed that Linux **Completely Fair Scheduler (CFS) quota throttling** was violently throttling application threads during microscopic 100ms processing bursts.

**Backing Out & What I Learned:**
I immediately removed CPU limits across all non-batch workloads (while keeping strict memory limits intact) and tuned CPU `requests` accurately. Latency instantly returned to sub-100ms.
- *Core Learning:* CPU is a compressible resource; throttling causes severe latency spikes without saving money. Modern Kubernetes best practice is to set CPU requests accurately for scheduling and let CFS burst naturally, relying on HPA for scaling.
</details>

#### 【 OTHER 】

<details>
<summary><strong>● Your resume lists Python as a skill. Do you know Python?</strong></summary>

**Answer:**
Yes. I use Python regularly for DevOps automation:
- Developing cloud automation scripts using the AWS SDK (**`boto3`**).
- Authoring custom Kubernetes controllers using the **`kopf`** framework.
- Writing custom Prometheus metric exporters and REST API integrations.
- Data processing and JSON/YAML configuration manipulation scripts.
</details>

<details>
<summary><strong>● Is YAML one of your primary languages/skills that you work with?</strong></summary>

**Answer:**
Yes. In cloud-native engineering, YAML is the universal declarative standard. I work with YAML daily across Kubernetes manifests, Helm values hierarchies, GitHub Actions workflows, GitLab CI definitions, Ansible playbooks, and OpenAPI specifications, with deep knowledge of syntax nuances, multi-line string folding, anchors, and schema validation.
</details>

<details>
<summary><strong>● Do you have any knowledge of JavaScript?</strong></summary>

**Answer:**
Yes, I possess practical working knowledge of **JavaScript / Node.js**:
- Debugging and containerizing Node.js/Express backend applications.
- Managing `package.json` dependencies and debugging `npm` build failures in CI pipelines.
- Writing automated end-to-end API test scripts using Postman and Cypress.
</details>
</details>

<details open>
<summary><h3>Level 2</h3></summary>

*Date: 05-08-2026 09:16 PM*

#### 【 SYSTEM DESIGN 】

<details>
<summary><strong>● Can you walk me through how you would take an application (such as the interviewer's) and integrate it into your current environment?</strong></summary>

**Answer:**
I follow a structured, 6-phase **Application Onboarding & Production Readiness Framework**:

```
[ Phase 1: Architectural Discovery ] -> [ Phase 2: Containerization & Hardening ] -> [ Phase 3: CI Pipeline Onboarding ]
                                                                                               |
[ Phase 6: Production Cutover & Observability ] <- [ Phase 5: Ingress & Secrets ] <- [ Phase 4: GitOps & Helm Packaging ]
```

1. **Phase 1: Architectural Discovery & Requirements Gathering:**
   - Review application runtime dependencies (Java/Node/Go/Python), statefulness (stateless vs stateful database dependencies), network communication requirements, and throughput/latency SLAs.
2. **Phase 2: Containerization & Hardening:**
   - Author a hardened **multi-stage Dockerfile** using Distroless or Alpine base images.
   - Configure container to run as a non-root user (`USER 10001`), set up proper `SIGTERM` signal handling for graceful termination, and configure a `.dockerignore` file.
3. **Phase 3: CI Pipeline Integration (Golden Path):**
   - Connect the repository to our centralized CI pipeline (GitHub Actions / Jenkins).
   - Configure automated unit tests, SonarQube SAST, Trivy vulnerability scanning, and automated container build/push to Amazon ECR tagged with the Git commit SHA.
4. **Phase 4: Packaging via Helm & GitOps Onboarding:**
   - Package application manifests into a Helm chart defining `Deployment`, `Service`, `HPA`, and `PodDisruptionBudget`.
   - Configure robust `readinessProbe` and `livenessProbe` endpoints.
   - Register the application in **Argo CD** for automated continuous delivery into Dev and Staging namespaces.
5. **Phase 5: Ingress, DNS & Secrets Integration:**
   - Configure **AWS Load Balancer Controller** Ingress with TLS certificates managed automatically via ACM and Route 53.
   - Deploy an `ExternalSecret` manifest to securely inject database credentials and API keys from **AWS Secrets Manager** at runtime.
6. **Phase 6: Observability & Production Readiness Review (PRR):**
   - Configure Prometheus metric scraping via `ServiceMonitor`.
   - Import a standardized Grafana Golden Signals dashboard (Latency, Traffic, Errors, Saturation).
   - Configure alert routes to Slack and PagerDuty. Execute load testing and sign off on the Production Readiness Review checklist.
</details>

#### 【 BEHAVIORAL 】

● **Candidate Introduction:** Can you introduce yourself?

<details>
<summary><strong>● Can you explain a project that you have worked on?</strong></summary>

**Answer:**
**Project Overview: Enterprise Cloud Migration & Platform Modernization**
At my previous company, I led the platform migration of our core financial invoicing and billing platform from legacy on-premises VMware virtual machines to **Amazon EKS**:

- **The Challenge:** The legacy system suffered from slow deployment cycles (monthly manual releases), unmonitored server drift, and scaling limitations during month-end invoicing spikes.
- **My Role & Implementation:**
  1. Codified the multi-AZ cloud landing zone using **Terraform** (VPCs across 3 AZs, Amazon EKS, and Multi-AZ Aurora PostgreSQL).
  2. Containerized the microservices using hardened multi-stage Dockerfiles.
  3. Built automated GitOps deployment pipelines using **GitHub Actions and Argo CD**, implementing Canary rollouts via Argo Rollouts.
  4. Configured end-to-end observability using **Prometheus, Grafana, and OpenTelemetry**.
- **Business Impact Delivered:**
  - Deployment frequency increased from **monthly to on-demand (multiple times daily)**.
  - Production incident recovery time (MTTR) dropped by **65%**.
  - Reduced annual cloud infrastructure costs by **over $180,000** through automated autoscaling and compute right-sizing.
</details>

<details>
<summary><strong>● How comfortable are you with learning Python quickly?</strong></summary>

**Answer:**
I am very comfortable. I already write Python for systems automation, cloud infrastructure scripting with `boto3`, and Kubernetes custom controllers. Because I understand programming fundamentals, data structures, and asynchronous patterns, ramping up on advanced Python frameworks, FastAPI, or backend application libraries is a rapid and seamless process for me.
</details>

<details>
<summary><strong>● What interests you about cyber security?</strong></summary>

**Answer:**
What excites me most about cybersecurity is that it is an **active, evolving discipline that underpins modern cloud engineering**:
- In modern cloud environments, security can no longer be an afterthought managed by a separate team at the end of a release cycle; it must be embedded directly into platform architecture (**DevSecOps** and **Shift-Left Security**).
- I am passionate about designing architectures that are resilient by default—implementing zero-trust network policies, identity-based cryptographic authentication (SPIFFE/mTLS), automated supply-chain vulnerability scanning, and immutable infrastructure that eliminates attack vectors before they can be exploited.
</details>
</details>
</details>
